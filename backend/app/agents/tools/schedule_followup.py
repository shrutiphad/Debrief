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
    interaction_id: str = Field(description="The interaction this follow-up relates to.")
    due_date: str = Field(description="ISO date YYYY-MM-DD the follow-up is due.")
    notes: str = Field(description="What needs to happen, e.g. 'Send elderly-dosing study PDF'.")


def make_schedule_followup_tool(db: AsyncSession) -> StructuredTool:
    async def _run(**kwargs) -> dict:
        payload = ScheduleFollowupInput(**kwargs)

        result = await db.execute(select(Interaction).where(Interaction.id == payload.interaction_id))
        interaction = result.scalar_one_or_none()
        if interaction is None:
            return {"status": "error", "message": f"No interaction found with id {payload.interaction_id}"}

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
        description="Create a follow-up task tied to a logged interaction, with a due date and what needs to happen.",
        args_schema=ScheduleFollowupInput,
        coroutine=_run,
    )
