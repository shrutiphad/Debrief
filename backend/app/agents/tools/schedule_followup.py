"""
Tool: schedule_followup  (tool #4)

Creates a follow-up task tied to an interaction — e.g. "send the dosing
study PDF", "return with samples in 2 weeks". Keeping this a distinct tool
(rather than a field on log_interaction) lets the agent create follow-ups
mid-conversation, retroactively on old interactions, or several at once.
"""
from datetime import date as date_type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FollowUp, Interaction


class ScheduleFollowupInput(BaseModel):
    due_date: str = Field(description="ISO date YYYY-MM-DD the follow-up is due.")
    notes: str = Field(description="What needs to happen, e.g. 'Send elderly-dosing study PDF'.")
    interaction_id: str | None = Field(
        default=None,
        description=(
            "Optional. The interaction this follow-up relates to. If you don't have one, omit it — "
            "the follow-up attaches to this HCP's most recent interaction automatically."
        ),
    )


def make_schedule_followup_tool(db: AsyncSession, hcp_id: str | None = None) -> StructuredTool:
    async def _run(**kwargs) -> dict:
        payload = ScheduleFollowupInput(**kwargs)

        # 1) Use the id the agent gave, if it resolves. 2) Otherwise fall back to the active
        # HCP's most recent interaction — so the agent never has to guess an id (which used to
        # cause an error + a wasted recovery round-trip).
        interaction = None
        if payload.interaction_id:
            interaction = (
                await db.execute(select(Interaction).where(Interaction.id == payload.interaction_id))
            ).scalar_one_or_none()
        if interaction is None and hcp_id:
            interaction = (
                await db.execute(
                    select(Interaction)
                    .where(Interaction.hcp_id == hcp_id)
                    .order_by(Interaction.interaction_date.desc(), Interaction.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
        if interaction is None:
            return {
                "status": "error",
                "message": "No interaction to attach the follow-up to yet — log an interaction for this HCP first.",
            }

        follow_up = FollowUp(
            interaction_id=interaction.id,
            hcp_id=interaction.hcp_id,
            due_date=date_type.fromisoformat(payload.due_date),
            notes=payload.notes,
        )
        db.add(follow_up)

        interaction.follow_up_required = True
        interaction.follow_up_notes = payload.notes

        await db.commit()
        await db.refresh(follow_up)

        return {
            "follow_up_id": follow_up.id,
            "due_date": follow_up.due_date.isoformat(),
            "notes": follow_up.notes,
            "status": "scheduled",
        }

    return StructuredTool.from_function(
        name="schedule_followup",
        description=(
            "Create a follow-up task for the current HCP with a due date and what needs to happen. "
            "You don't need an interaction id — it attaches to the HCP's most recent interaction automatically."
        ),
        args_schema=ScheduleFollowupInput,
        coroutine=_run,
    )
