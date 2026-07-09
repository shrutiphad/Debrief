"""
Tool: edit_interaction  (mandatory tool #2)

Patches a previously logged interaction. Reps rarely get everything right in
one pass ("actually add that she asked about pediatric dosing", "wrong date,
it was Tuesday") — this tool applies a partial update and keeps an audit
trail (`edit_history`) of every change, which the frontend surfaces on the
interaction detail view for compliance traceability.
"""
from datetime import date as date_type, datetime

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Interaction


class EditInteractionInput(BaseModel):
    interaction_id: str = Field(description="Id of the interaction to modify.")
    interaction_type: str | None = None
    interaction_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    interaction_time: str | None = None
    attendees: list[str] | None = None
    products_discussed: list[str] | None = None
    samples_dropped: list[str] | None = None
    materials_shared: list[str] | None = None
    topics_discussed: str | None = None
    outcomes: str | None = None
    sentiment: str | None = Field(default=None, description="Manual override: positive, neutral, or negative.")
    follow_up_required: bool | None = None
    follow_up_notes: str | None = None
    edit_reason: str = Field(description="Short reason for the edit, taken from what the rep said.")


def make_edit_interaction_tool(db: AsyncSession) -> StructuredTool:
    async def _run(**kwargs) -> dict:
        payload = EditInteractionInput(**kwargs)

        result = await db.execute(select(Interaction).where(Interaction.id == payload.interaction_id))
        interaction = result.scalar_one_or_none()
        if interaction is None:
            return {"status": "error", "message": f"No interaction found with id {payload.interaction_id}"}

        changed_fields = {}
        patch = payload.model_dump(exclude={"interaction_id", "edit_reason"}, exclude_none=True)
        for field, value in patch.items():
            if field == "interaction_date":
                value = date_type.fromisoformat(value)
            old_value = getattr(interaction, field)
            if old_value != value:
                changed_fields[field] = {"from": str(old_value), "to": str(value)}
                setattr(interaction, field, value)

        if changed_fields:
            history = list(interaction.edit_history or [])
            history.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": payload.edit_reason,
                    "changes": changed_fields,
                }
            )
            interaction.edit_history = history
            await db.commit()
            await db.refresh(interaction)

        return {
            "interaction_id": interaction.id,
            "fields_changed": list(changed_fields.keys()),
            "status": "updated" if changed_fields else "no_changes",
        }

    return StructuredTool.from_function(
        name="edit_interaction",
        description="Patch fields on an already-logged interaction. Only pass the fields that changed.",
        args_schema=EditInteractionInput,
        coroutine=_run,
    )
