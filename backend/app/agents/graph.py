"""
The LangGraph agent graph.

This is a classic ReAct-style loop built explicitly with StateGraph (rather
than the `create_react_agent` shortcut) so the orchestration is visible and
explainable node-by-node:

        ┌────────────┐   tool_calls present   ┌───────────┐
   ───▶ │   agent    │ ─────────────────────▶ │   tools   │
        │ (gemma2-9b │                         │ (ToolNode)│
        │  -it, LLM) │ ◀───────────────────── │           │
        └─────┬──────┘      tool results        └───────────┘
              │
              │ no tool_calls
              ▼
             END

* `agent` — the LLM (bound to all 5 tools) reads the conversation so far and
  either calls a tool or produces a final reply to the rep.
* `tools` — executes whichever tool(s) the LLM asked for and appends the
  results as ToolMessages, then hands control back to `agent` so it can
  react to what it learned (e.g. call `search_interactions`, then
  `log_interaction` with richer context).

A `MemorySaver` checkpointer keys conversation state by `session_id`, so a
rep's chat has continuity ("no, make it Tuesday not Wednesday") within a
session without the frontend having to resend full history.
"""
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import agent_llm
from app.agents.prompts import AGENT_SYSTEM_PROMPT
from app.agents.state import AgentState
from app.agents.tools import build_tools

# One process-lifetime checkpointer shared across requests, threads separated by session_id.
_checkpointer = MemorySaver()


def _should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else "end"


def build_graph(db: AsyncSession):
    """Compile a fresh graph bound to this request's DB session and tool set."""
    tools = build_tools(db)
    llm_with_tools = agent_llm().bind_tools(tools)

    async def agent_node(state: AgentState) -> dict:
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT), *messages]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=_checkpointer)
