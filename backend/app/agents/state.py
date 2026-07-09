from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state threaded through every node in the graph.

    `messages` is the running conversation (human / AI / tool messages),
    reduced with LangGraph's `add_messages` so each node only returns the
    *new* messages it produced, not the whole history.

    `hcp_id` / `session_id` carry request context so tools can act on the
    right HCP and record edits against the right conversation thread.
    """

    messages: Annotated[list, add_messages]
    hcp_id: str | None
    session_id: str
