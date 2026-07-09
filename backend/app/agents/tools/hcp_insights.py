"""
Tool: hcp_insights  (tool #5)

The one tool that deliberately uses CONTEXT_MODEL (llama-3.3-70b-versatile) —
this is the "for context" use case the brief calls out. It pulls an HCP's
*entire* interaction history (which can run long for a
well-covered prescriber) and asks a larger-context model to produce a
relationship read: engagement trend, sentiment trajectory, and a
recommended next best action. This is what a rep would pull up right
before walking into a visit.
"""
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import get_context_llm
from app.agents.prompts import INSIGHTS_PROMPT
from app.db.models import HCP, Interaction


class HCPInsightsInput(BaseModel):
    hcp_id: str = Field(description="The HCP to generate a relationship briefing for.")


def make_hcp_insights_tool(db: AsyncSession) -> StructuredTool:
    async def _run(**kwargs) -> dict:
        payload = HCPInsightsInput(**kwargs)

        hcp = (await db.execute(select(HCP).where(HCP.id == payload.hcp_id))).scalar_one_or_none()
        if hcp is None:
            return {"status": "error", "message": f"No HCP found with id {payload.hcp_id}"}

        rows = (
            (
                await db.execute(
                    select(Interaction)
                    .where(Interaction.hcp_id == payload.hcp_id)
                    .order_by(Interaction.interaction_date.asc())
                )
            )
            .scalars()
            .all()
        )

        if not rows:
            return {
                "hcp_id": hcp.id,
                "hcp_name": hcp.name,
                "briefing": "No interactions logged yet for this HCP — this would be a first touchpoint.",
            }

        history_text = "\n".join(
            f"- {r.interaction_date.isoformat()} ({r.interaction_type}, sentiment: {r.sentiment or 'n/a'}): "
            f"{r.summary or r.topics_discussed or 'no summary'} "
            f"[products: {', '.join(r.products_discussed) or 'none'}]"
            for r in rows
        )

        llm = get_context_llm()
        try:
            resp = await llm.ainvoke(
                [
                    {"role": "system", "content": INSIGHTS_PROMPT},
                    {"role": "user", "content": f"HCP: {hcp.name} ({hcp.specialty or 'specialty unknown'})\n\nHistory:\n{history_text}"},
                ]
            )
            briefing = resp.content.strip()
        except Exception as exc:
            briefing = f"Could not reach the insights model right now ({exc.__class__.__name__}). Raw history is available below."

        return {
            "hcp_id": hcp.id,
            "hcp_name": hcp.name,
            "interaction_count": len(rows),
            "briefing": briefing,
        }

    return StructuredTool.from_function(
        name="hcp_insights",
        description=(
            "Generate a relationship briefing for an HCP — engagement trend, sentiment trajectory, "
            "and recommended next best action — from their full interaction history."
        ),
        args_schema=HCPInsightsInput,
        coroutine=_run,
    )
