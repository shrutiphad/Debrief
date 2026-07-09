"""
Tool: log_interaction  (mandatory tool #1)

Creates a new Interaction record for an HCP. This is the primary entry point
for the conversational side of the Log Interaction screen: the rep describes
what happened in plain language, and this tool is responsible for turning
that into a structured row — using the LLM for two things the brief calls
out explicitly:

  1. Summarization — a clean 1-3 sentence professional summary of raw_notes.
  2. Entity extraction — the *arguments to this tool itself* (products,
     samples, materials, follow-up flag) are entities the agent's LLM
     extracts from the rep's free text before ever calling this function.
     The tool then does a second, focused extraction pass for sentiment.
"""
from datetime import date as date_type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import get_primary_llm
from app.agents.prompts import SENTIMENT_PROMPT, SUMMARY_EXTRACTION_PROMPT
from app.db.models import Interaction


class LogInteractionInput(BaseModel):
    hcp_id: str = Field(description="The internal id of the HCP this interaction is with.")
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
        # Enrichment failing shouldn't block the log from being saved — fall back to the raw notes.
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
    async def _run(**kwargs) -> dict:
        payload = LogInteractionInput(**kwargs)

        summary, sentiment = await _summarize(payload.raw_notes), await _sentiment(payload.raw_notes)

        interaction = Interaction(
            hcp_id=payload.hcp_id,
            interaction_type=payload.interaction_type,
            channel="chat",
            interaction_date=date_type.fromisoformat(payload.interaction_date),
            interaction_time=payload.interaction_time,
            attendees=payload.attendees,
            products_discussed=payload.products_discussed,
            samples_dropped=payload.samples_dropped,
            materials_shared=payload.materials_shared,
            topics_discussed=summary,
            outcomes=payload.outcomes,
            raw_notes=payload.raw_notes,
            summary=summary,
            sentiment=sentiment,
            follow_up_required=payload.follow_up_required,
            follow_up_notes=payload.follow_up_notes,
        )
        db.add(interaction)
        await db.commit()
        await db.refresh(interaction)

        return {
            "interaction_id": interaction.id,
            "hcp_id": interaction.hcp_id,
            "summary": summary,
            "sentiment": sentiment,
            "follow_up_required": interaction.follow_up_required,
        }

    return StructuredTool.from_function(
        name="log_interaction",
        description=(
            "Log a new HCP interaction. Call this once you know which HCP, what happened, "
            "and have extracted products/samples/materials/follow-up from the rep's message."
        ),
        args_schema=LogInteractionInput,
        coroutine=_run,
    )
