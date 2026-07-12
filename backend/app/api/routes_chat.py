import os

from fastapi import APIRouter, Depends
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_graph
from app.core.config import get_settings
from app.db.database import get_db
from app.db.schemas import ChatMessageIn, ChatMessageOut, ToolTrace

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()


def _extract_trace(new_messages: list) -> list[ToolTrace]:
    """Pair each tool_call the agent made with its ToolMessage result so the
    frontend's Agent Activity panel can show what actually ran, in order."""
    calls_by_id = {}
    for m in new_messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for call in m.tool_calls:
                calls_by_id[call["id"]] = {"tool": call["name"], "input": call["args"]}

    trace = []
    for m in new_messages:
        if isinstance(m, ToolMessage):
            call = calls_by_id.get(m.tool_call_id, {"tool": m.name, "input": {}})
            try:
                import json

                output = json.loads(m.content) if isinstance(m.content, str) else m.content
            except Exception:
                output = {"raw": str(m.content)}
            status = "error" if isinstance(output, dict) and output.get("status") == "error" else "success"
            trace.append(ToolTrace(tool=call["tool"], input=call["input"], output=output, status=status))
    return trace


@router.post("", response_model=ChatMessageOut)
async def chat(payload: ChatMessageIn, db: AsyncSession = Depends(get_db)):
    if not settings.GROQ_API_KEY:
        return ChatMessageOut(
            session_id=payload.session_id,
            reply=(
                "GROQ_API_KEY is not set on the backend. Add it to backend/.env "
                "(see .env.example) and restart the server to enable the AI agent."
            ),
            tool_trace=[],
            model_used="none",
        )

    graph = build_graph(db, payload.hcp_id)
    config = {"configurable": {"thread_id": payload.session_id}}

    context_prefix = f"[Active HCP context: hcp_id={payload.hcp_id}] " if payload.hcp_id else ""
    try:
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=context_prefix + payload.message)],
                "hcp_id": payload.hcp_id,
                "session_id": payload.session_id,
            },
            config=config,
        )
    except Exception as exc:
        return ChatMessageOut(
            session_id=payload.session_id,
            reply=(
                f"The agent couldn't reach the Groq API ({exc.__class__.__name__}). "
                "Check GROQ_API_KEY and network access from the backend, then try again."
            ),
            tool_trace=[],
            model_used="error",
        )

    all_messages = result["messages"]
    # Messages produced in *this* turn = everything after the last prior AI final reply.
    # Simplest robust approach: walk back from the end to the human message we just sent.
    turn_start = max(i for i, m in enumerate(all_messages) if isinstance(m, HumanMessage))
    new_messages = all_messages[turn_start + 1 :]

    final_reply = next((m.content for m in reversed(new_messages) if isinstance(m, AIMessage) and m.content), "")
    trace = _extract_trace(new_messages)

    return ChatMessageOut(
        session_id=payload.session_id,
        reply=final_reply or "Done.",
        tool_trace=trace,
        model_used=os.getenv("AGENT_MODEL", "primary"),
    )
