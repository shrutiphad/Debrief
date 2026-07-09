"""
Tool: search_interactions  (tool #3)

Lets the agent pull an HCP's interaction history into context before logging
a new one, resolving an edit ("the visit last week"), or answering a rep's
question ("what did we last discuss with Dr. Mehta?").
"""
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Interaction


class SearchInteractionsInput(BaseModel):
    hcp_id: str | None = Field(default=None, description="Restrict search to this HCP, if known.")
    keyword: str | None = Field(default=None, description="Free-text keyword to match against notes/summary/products.")
    limit: int = Field(default=5, description="Max number of results, most recent first.")


def make_search_interactions_tool(db: AsyncSession) -> StructuredTool:
    async def _run(**kwargs) -> dict:
        payload = SearchInteractionsInput(**kwargs)

        stmt = select(Interaction).order_by(Interaction.interaction_date.desc()).limit(payload.limit)
        if payload.hcp_id:
            stmt = stmt.where(Interaction.hcp_id == payload.hcp_id)
        if payload.keyword:
            like = f"%{payload.keyword}%"
            stmt = stmt.where(
                or_(Interaction.summary.ilike(like), Interaction.topics_discussed.ilike(like), Interaction.raw_notes.ilike(like))
            )

        rows = (await db.execute(stmt)).scalars().all()
        return {
            "count": len(rows),
            "interactions": [
                {
                    "id": r.id,
                    "date": r.interaction_date.isoformat(),
                    "type": r.interaction_type,
                    "summary": r.summary,
                    "sentiment": r.sentiment,
                    "products_discussed": r.products_discussed,
                    "follow_up_required": r.follow_up_required,
                }
                for r in rows
            ],
        }

    return StructuredTool.from_function(
        name="search_interactions",
        description="Search past logged interactions, optionally filtered by HCP and/or keyword.",
        args_schema=SearchInteractionsInput,
        coroutine=_run,
    )
