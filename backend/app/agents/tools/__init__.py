from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.edit_interaction import make_edit_interaction_tool
from app.agents.tools.hcp_insights import make_hcp_insights_tool
from app.agents.tools.log_interaction import make_log_interaction_tool
from app.agents.tools.schedule_followup import make_schedule_followup_tool
from app.agents.tools.search_interactions import make_search_interactions_tool


def build_tools(db: AsyncSession, hcp_id: str | None = None) -> list:
    """Construct all 5 LangGraph tools bound to this request's DB session.

    `hcp_id` (the active HCP for this chat) lets schedule_followup attach a
    follow-up to that HCP's latest interaction without the agent guessing an id.
    """
    return [
        make_log_interaction_tool(db),
        make_edit_interaction_tool(db),
        make_search_interactions_tool(db),
        make_schedule_followup_tool(db, hcp_id),
        make_hcp_insights_tool(db),
    ]
