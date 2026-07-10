"""
Groq-backed LLM clients.

`PRIMARY_MODEL` (llama-3.3-70b-versatile) drives the LangGraph agent's
tool-routing loop — a 70B model is used here because reliable structured
tool-calling across a 5-tool ReAct loop needs stronger instruction-following
than a small model can give. `CONTEXT_MODEL` is used for longer-context
reasoning / summarization tasks such as `hcp_insights`.

Both clients are configured with automatic retries and a request timeout so
transient Groq rate-limit (429) / timeout blips are retried with backoff
rather than surfacing to the rep as a hard failure. Set AGENT_MODEL=context
to route the agent loop through CONTEXT_MODEL instead.
"""
from functools import lru_cache

from langchain_groq import ChatGroq

from app.core.config import get_settings

settings = get_settings()

# Robustness knobs shared by both clients. langchain-groq retries 429s / 5xx /
# timeouts with exponential backoff up to max_retries before raising.
_MAX_RETRIES = 3
_REQUEST_TIMEOUT = 30.0  # seconds per attempt
# Cap output length. Agent replies are short confirmations and tool-call args, and
# insights briefings are <90 words — capping tokens keeps each call well under the
# free-tier tokens-per-minute (TPM) ceiling so we don't get rate-limited mid-turn.
_MAX_TOKENS = 512


@lru_cache
def get_primary_llm() -> ChatGroq:
    """PRIMARY_MODEL — drives the agent's routing/tool-call loop."""
    return ChatGroq(
        model=settings.PRIMARY_MODEL,
        api_key=settings.GROQ_API_KEY or "missing-key",
        temperature=settings.LLM_TEMPERATURE,
        max_retries=_MAX_RETRIES,
        request_timeout=_REQUEST_TIMEOUT,
        max_tokens=_MAX_TOKENS,
    )


@lru_cache
def get_context_llm() -> ChatGroq:
    """CONTEXT_MODEL — long-context reasoning & summarization."""
    return ChatGroq(
        model=settings.CONTEXT_MODEL,
        api_key=settings.GROQ_API_KEY or "missing-key",
        temperature=settings.LLM_TEMPERATURE,
        max_retries=_MAX_RETRIES,
        request_timeout=_REQUEST_TIMEOUT,
        max_tokens=_MAX_TOKENS,
    )


def agent_llm() -> ChatGroq:
    import os

    return get_context_llm() if os.getenv("AGENT_MODEL") == "context" else get_primary_llm()
