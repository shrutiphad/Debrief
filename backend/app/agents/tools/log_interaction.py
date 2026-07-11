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
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

_VALID_SENTIMENT = {"positive", "neutral", "negative"}


class LogInteractionInput(BaseModel):
    interaction_type: str = Field(
        default="visit",
        description="One of: visit, call, email, conference, sample_drop.",
    )
    interaction_date: str | None = Field(
        default=None,
        description=(
            "ISO date YYYY-MM-DD ONLY if the rep explicitly says when it happened (e.g. 'yesterday', "
            "'last Tuesday'). Otherwise omit — today's date is filled in automatically at the moment of logging."
        ),
    )
    interaction_time: str | None = Field(default=None, description="HH:MM if the rep states one; else omit (current time is filled automatically).")
    attendees: list[str] = Field(default_factory=list, description="Others present besides the HCP (e.g. a nurse). Never the HCP themselves.")
    raw_notes: str = Field(description="The rep's description of what happened, verbatim.")
    summary: str | None = Field(default=None, description="Your concise 1-2 sentence summary. Plain text, no preamble.")
    products_discussed: list[str] = Field(default_factory=list, description="Product/brand names mentioned.")
    samples_dropped: list[str] = Field(default_factory=list, description="Sample products left with the HCP.")
    materials_shared: list[str] = Field(default_factory=list, description="Materials/decks shared.")
    outcomes: str | None = Field(default=None, description="Key outcomes or agreements, if any.")
    sentiment: str | None = Field(default=None, description="positive, neutral, or negative — inferred from the description.")
    follow_up_required: bool = Field(default=False, description="True if a next step is needed.")
    follow_up_notes: str | None = Field(default=None, description="What the follow-up is, if follow_up_required.")


def make_log_interaction_tool(db: AsyncSession) -> StructuredTool:
    # `db` is unused (this tool stages a draft rather than persisting) but the
    # factory signature is kept uniform with the other DB-backed tools.
    async def _run(**kwargs) -> dict:
        payload = LogInteractionInput(**kwargs)

        sentiment = (payload.sentiment or "").strip().lower()
        if sentiment not in _VALID_SENTIMENT:
            sentiment = "neutral"

        # Only pass through a date/time the rep actually stated. When absent we send null and let
        # the frontend stamp the *browser-local* current date/time at the moment of logging — the
        # server runs in UTC, so doing it here would log a date/time off from the rep's real local day.
        interaction_time = (payload.interaction_time or "").strip() or None
        interaction_date = (payload.interaction_date or "").strip() or None

        # The draft mirrors the fields the left-hand form renders, so the frontend
        # can drop it straight in. No LLM calls here — the agent already did the work.
        draft = {
            "interaction_type": payload.interaction_type,
            "interaction_date": interaction_date,
            "interaction_time": interaction_time,
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
