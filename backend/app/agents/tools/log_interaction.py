"""
Tool: log_interaction  (mandatory tool #1)

Fills the "Interaction Details" form on the left of the Log Interaction screen
from the rep's plain-language description — the conversational, AI-drives-the-form
flow the task video requires: the rep never types into the form, they describe the
visit and this tool extracts the structured fields.

It does NOT write to the database. It *stages* a draft that the frontend renders
into the form; the rep reviews it (and can ask the agent to correct it via
`edit_interaction`) then clicks "Log Interaction" to persist.

Entity extraction + summarization are done by the AGENT's own LLM as it fills in
this tool's arguments (products, samples, materials, a concise `summary`, and the
inferred `sentiment`). We deliberately do NOT make additional LLM calls inside the
tool — a single log turn already involves several model calls in the agent loop,
and piling on more made the whole pipeline flaky under Groq's free-tier limits.
Fewer calls = the form fills reliably every time.
"""
from datetime import date as date_type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

_VALID_SENTIMENT = {"positive", "neutral", "negative"}


class LogInteractionInput(BaseModel):
    interaction_type: str = Field(
        default="visit",
        description="One of: visit, call, email, conference, sample_drop.",
    )
    interaction_date: str = Field(
        default_factory=lambda: date_type.today().isoformat(),
        description="ISO date (YYYY-MM-DD) the interaction happened. Default to today if not stated.",
    )
    interaction_time: str | None = Field(default=None, description="Time of the interaction, HH:MM, if mentioned.")
    attendees: list[str] = Field(
        default_factory=list,
        description=(
            "Other people present BESIDES the HCP themselves (e.g. a clinic nurse, a colleague). "
            "Never put the HCP's own name here. Leave empty if only the HCP was present."
        ),
    )
    raw_notes: str = Field(description="The rep's free-text description of what happened, verbatim.")
    summary: str | None = Field(
        default=None,
        description=(
            "A concise 1-2 sentence professional summary of the interaction that YOU write from the "
            "rep's description. Plain text only — no preamble like 'Here is a summary'."
        ),
    )
    products_discussed: list[str] = Field(default_factory=list, description="Product/brand names mentioned.")
    samples_dropped: list[str] = Field(default_factory=list, description="Sample products left with the HCP, if any.")
    materials_shared: list[str] = Field(default_factory=list, description="Marketing/clinical materials shared, if any.")
    outcomes: str | None = Field(default=None, description="Key outcomes or agreements reached, if any.")
    sentiment: str | None = Field(
        default=None,
        description=(
            "The HCP's sentiment inferred from the rep's description: exactly 'positive', 'neutral', or "
            "'negative'. If the rep gives no signal of how the HCP reacted, use 'neutral'."
        ),
    )
    follow_up_required: bool = Field(default=False, description="True if the rep needs to take a next step.")
    follow_up_notes: str | None = Field(default=None, description="What the follow-up is, if follow_up_required is true.")


def make_log_interaction_tool(db: AsyncSession) -> StructuredTool:
    # `db` is unused (this tool stages a draft rather than persisting) but the
    # factory signature is kept uniform with the other DB-backed tools.
    async def _run(**kwargs) -> dict:
        payload = LogInteractionInput(**kwargs)

        sentiment = (payload.sentiment or "").strip().lower()
        if sentiment not in _VALID_SENTIMENT:
            sentiment = "neutral"

        # The draft mirrors the fields the left-hand form renders, so the frontend
        # can drop it straight in. No LLM calls here — the agent already did the work.
        draft = {
            "interaction_type": payload.interaction_type,
            "interaction_date": payload.interaction_date,
            "interaction_time": payload.interaction_time,
            "attendees": payload.attendees,
            "products_discussed": payload.products_discussed,
            "samples_dropped": payload.samples_dropped,
            "materials_shared": payload.materials_shared,
            "topics_discussed": (payload.summary or payload.raw_notes or "").strip(),
            "outcomes": payload.outcomes,
            "sentiment": sentiment,
            "follow_up_required": payload.follow_up_required,
            "follow_up_notes": payload.follow_up_notes,
        }
        return {"status": "staged", "draft": draft}

    return StructuredTool.from_function(
        name="log_interaction",
        description=(
            "Fill the Interaction Details form from the rep's description of a visit/call/interaction. "
            "Extract the type, date, products/samples/materials and follow-up, write a short summary, and "
            "infer the sentiment. Call this whenever the rep describes something that happened with the "
            "HCP. It fills the form for the rep to review and save — it does not save itself."
        ),
        args_schema=LogInteractionInput,
        coroutine=_run,
    )
