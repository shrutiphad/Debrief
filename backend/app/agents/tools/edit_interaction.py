"""
Tool: edit_interaction  (mandatory tool #2)

Updates the Interaction Details form the rep is reviewing, before it's saved.
This is the video's second mandatory flow: the form is filled, the rep spots a
mistake ("actually the sentiment was negative, and it was a call not a visit"),
and instead of clicking the form they tell the agent — this tool returns ONLY
the changed fields as a patch, and the frontend merges it into the current
draft so every other field is left exactly as it was.

Like `log_interaction`, this stages changes into the form rather than writing to
the database; persistence happens when the rep clicks "Log Interaction".
"""
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession


class EditInteractionInput(BaseModel):
    interaction_type: str | None = Field(default=None, description="One of: visit, call, email, conference, sample_drop.")
    interaction_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    interaction_time: str | None = None
    attendees: list[str] | None = None
    products_discussed: list[str] | None = None
    samples_dropped: list[str] | None = None
    materials_shared: list[str] | None = None
    topics_discussed: str | None = None
    outcomes: str | None = None
    sentiment: str | None = Field(default=None, description="positive, neutral, or negative.")
    follow_up_required: bool | None = None
    follow_up_notes: str | None = None
    edit_reason: str = Field(description="Short reason for the edit, taken from what the rep said.")


def make_edit_interaction_tool(db: AsyncSession) -> StructuredTool:
    # `db` is unused (this tool patches the in-progress form draft, not a saved row).
    async def _run(**kwargs) -> dict:
        payload = EditInteractionInput(**kwargs)

        # Only the fields the rep actually asked to change — everything else is left
        # untouched when the frontend merges this into the current draft.
        patch = payload.model_dump(exclude={"edit_reason"}, exclude_none=True)

        return {
            "status": "edited" if patch else "no_changes",
            "patch": patch,
            "fields_changed": list(patch.keys()),
            "edit_reason": payload.edit_reason,
        }

    return StructuredTool.from_function(
        name="edit_interaction",
        description=(
            "Update fields on the Interaction Details form the rep is reviewing. Pass ONLY the fields "
            "that changed — everything else stays as it is. Use this whenever the rep corrects or adds "
            "to what you already put in the form."
        ),
        args_schema=EditInteractionInput,
        coroutine=_run,
    )
