from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools.edit_interaction import make_edit_interaction_tool
from app.agents.tools.hcp_insights import make_hcp_insights_tool
from app.agents.tools.log_interaction import make_log_interaction_tool
from app.agents.tools.schedule_followup import make_schedule_followup_tool
from app.agents.tools.search_interactions import make_search_interactions_tool


def build_tools(db: AsyncSession) -> list:
    """Construct all 5 LangGraph tools bound to this request's DB session."""
    return [
        make_log_interaction_tool(db),
        make_edit_interaction_tool(db),
        make_search_interactions_tool(db),
        make_schedule_followup_tool(db),
        make_hcp_insights_tool(db),
    ]
