"""
Groq-backed LLM clients.

Per the task brief, `gemma2-9b-it` is the mandatory model and drives the
LangGraph agent's tool-routing loop. `llama-3.3-70b-versatile` is used
wherever the brief says "for context" — i.e. tasks that benefit from a
larger context window and stronger multi-step reasoning:

  * summarizing long / rambling free-text or chat-derived notes
  * `hcp_insights`, which reasons over an HCP's *entire* interaction
    history to produce a relationship read + recommended next action

If, at review time, `gemma2-9b-it` does not accept `bind_tools` on a given
Groq API version, set AGENT_MODEL=context in the environment (see
.env.example) to route the agent loop through llama-3.3-70b-versatile
instead — the rest of the graph is model-agnostic.
"""
from functools import lru_cache

from langchain_groq import ChatGroq

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_primary_llm() -> ChatGroq:
    """gemma2-9b-it — mandatory model, drives the agent's routing/tool-call loop."""
    return ChatGroq(
        model=settings.PRIMARY_MODEL,
        api_key=settings.GROQ_API_KEY or "missing-key",
        temperature=settings.LLM_TEMPERATURE,
    )


@lru_cache
def get_context_llm() -> ChatGroq:
    """llama-3.3-70b-versatile — long-context reasoning & summarization."""
    return ChatGroq(
        model=settings.CONTEXT_MODEL,
        api_key=settings.GROQ_API_KEY or "missing-key",
        temperature=settings.LLM_TEMPERATURE,
    )


def agent_llm() -> ChatGroq:
    import os

    return get_context_llm() if os.getenv("AGENT_MODEL") == "context" else get_primary_llm()
