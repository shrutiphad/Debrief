"""
Tool: log_interaction  (mandatory tool #1)

Fills the "Interaction Details" form on the left of the Log Interaction screen
from the rep's plain-language description — this is the conversational,
AI-drives-the-form flow the task video requires: the rep never types into the
form, they describe the visit and this tool extracts the structured fields.

It does NOT write to the database. It *stages* a draft that the frontend renders
into the form; the rep reviews it (and can ask the agent to correct it via
`edit_interaction`) and then clicks "Log Interaction" to persist. The LLM is
used for the two things the brief calls out explicitly:

  1. Entity extraction — interaction type, products, samples, materials, dates,
     follow-up flag are extracted by the agent's LLM into this tool's arguments.
  2. Summarization + sentiment — a focused second pass turns the raw description
     into a clean Topics-Discussed summary and infers HCP sentiment.
"""
from datetime import date as date_type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import get_primary_llm
from app.agents.prompts import SENTIMENT_PROMPT, SUMMARY_EXTRACTION_PROMPT


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
    attendees: list[str] = Field(default_factory=list, description="Other people present besides the HCP, if mentioned.")
    raw_notes: str = Field(description="The rep's free-text description of what happened, verbatim.")
    products_discussed: list[str] = Field(default_factory=list, description="Product/brand names mentioned.")
    samples_dropped: list[str] = Field(default_factory=list, description="Sample products left with the HCP, if any.")
    materials_shared: list[str] = Field(default_factory=list, description="Marketing/clinical materials shared, if any.")
    outcomes: str | None = Field(default=None, description="Key outcomes or agreements reached, if any.")
    follow_up_required: bool = Field(default=False, description="True if the rep needs to take a next step.")
    follow_up_notes: str | None = Field(default=None, description="What the follow-up is, if follow_up_required is true.")


async def _summarize(raw_notes: str) -> str:
    try:
        llm = get_primary_llm()
        resp = await llm.ainvoke(
            [{"role": "system", "content": SUMMARY_EXTRACTION_PROMPT}, {"role": "user", "content": raw_notes}]
        )
        return resp.content.strip()
    except Exception:
        # Enrichment failing shouldn't block the form from being filled — fall back to the raw notes.
        return raw_notes


async def _sentiment(raw_notes: str) -> str:
    try:
        llm = get_primary_llm()
        resp = await llm.ainvoke(
            [{"role": "system", "content": SENTIMENT_PROMPT}, {"role": "user", "content": raw_notes}]
        )
        label = resp.content.strip().lower()
        return label if label in {"positive", "neutral", "negative"} else "neutral"
    except Exception:
        return "neutral"


def make_log_interaction_tool(db: AsyncSession) -> StructuredTool:
    # `db` is unused here (this tool stages a draft rather than persisting) but the
    # factory signature is kept uniform with the other DB-backed tools.
    async def _run(**kwargs) -> dict:
        payload = LogInteractionInput(**kwargs)

        summary, sentiment = await _summarize(payload.raw_notes), await _sentiment(payload.raw_notes)

        # The draft object mirrors the fields the left-hand form renders, so the
        # frontend can drop it straight into the form.
        draft = {
            "interaction_type": payload.interaction_type,
            "interaction_date": payload.interaction_date,
            "interaction_time": payload.interaction_time,
            "attendees": payload.attendees,
            "products_discussed": payload.products_discussed,
            "samples_dropped": payload.samples_dropped,
            "materials_shared": payload.materials_shared,
            "topics_discussed": summary,
            "outcomes": payload.outcomes,
            "sentiment": sentiment,
            "follow_up_required": payload.follow_up_required,
            "follow_up_notes": payload.follow_up_notes,
        }
        return {"status": "staged", "draft": draft}

    return StructuredTool.from_function(
        name="log_interaction",
        description=(
            "Fill the Interaction Details form from the rep's description of a visit. Extract the "
            "interaction type, date, products/samples/materials, and follow-up, and infer a summary "
            "and sentiment. This fills the form for the rep to review and save — it does not save itself."
        ),
        args_schema=LogInteractionInput,
        coroutine=_run,
    )
