from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import get_primary_llm
from app.agents.prompts import SENTIMENT_PROMPT, SUMMARY_EXTRACTION_PROMPT
from app.db.database import get_db
from app.db.models import FollowUp, Interaction
from app.db.schemas import FollowUpOut, InteractionCreate, InteractionOut, InteractionUpdate

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("", response_model=list[InteractionOut])
async def list_interactions(hcp_id: str | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Interaction).order_by(Interaction.interaction_date.desc())
    if hcp_id:
        stmt = stmt.where(Interaction.hcp_id == hcp_id)
    return (await db.execute(stmt)).scalars().all()


@router.get("/{interaction_id}", response_model=InteractionOut)
async def get_interaction(interaction_id: str, db: AsyncSession = Depends(get_db)):
    interaction = await db.get(Interaction, interaction_id)
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return interaction


@router.post("", response_model=InteractionOut, status_code=201)
async def create_interaction(payload: InteractionCreate, db: AsyncSession = Depends(get_db)):
    """
    Structured-form submission path. Even here, the LLM is used (per the
    brief's 'potentially using the LLM for summarization' note) to turn
    whatever the rep typed into Topics Discussed into a clean summary and
    a sentiment label — the same enrichment the chat path gets via the
    log_interaction LangGraph tool, so both entry modes produce consistent
    CRM records.
    """
    data = payload.model_dump()
    notes = data.get("topics_discussed") or ""
    manual_sentiment = data.pop("sentiment", None)
    summary, sentiment = None, manual_sentiment

    if notes.strip():
        try:
            llm = get_primary_llm()
            summary_resp = await llm.ainvoke(
                [{"role": "system", "content": SUMMARY_EXTRACTION_PROMPT}, {"role": "user", "content": notes}]
            )
            summary = summary_resp.content.strip()
            if not manual_sentiment:
                sentiment_resp = await llm.ainvoke(
                    [{"role": "system", "content": SENTIMENT_PROMPT}, {"role": "user", "content": notes}]
                )
                label = sentiment_resp.content.strip().lower()
                sentiment = label if label in {"positive", "neutral", "negative"} else "neutral"
        except Exception as exc:
            # Don't let an LLM/provider hiccup block a rep from saving their log — the record is
            # still saved with the raw notes; summary/sentiment simply stay empty for this entry.
            import logging

            logging.getLogger(__name__).warning("LLM enrichment failed, saving without it: %s", exc)

    interaction = Interaction(**data, summary=summary, sentiment=sentiment)
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    return interaction


@router.patch("/{interaction_id}", response_model=InteractionOut)
async def update_interaction(interaction_id: str, payload: InteractionUpdate, db: AsyncSession = Depends(get_db)):
    interaction = await db.get(Interaction, interaction_id)
    if not interaction:
        raise HTTPException(404, "Interaction not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(interaction, field, value)

    await db.commit()
    await db.refresh(interaction)
    return interaction


@router.delete("/{interaction_id}", status_code=204)
async def delete_interaction(interaction_id: str, db: AsyncSession = Depends(get_db)):
    interaction = await db.get(Interaction, interaction_id)
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    await db.delete(interaction)
    await db.commit()


@router.get("/{interaction_id}/follow-ups", response_model=list[FollowUpOut])
async def list_followups_for_interaction(interaction_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(FollowUp).where(FollowUp.interaction_id == interaction_id)
    return (await db.execute(stmt)).scalars().all()
