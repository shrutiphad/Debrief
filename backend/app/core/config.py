"""
Centralized application settings.

All configuration is sourced from environment variables (see .env.example).
Nothing sensitive is hard-coded — the Groq API key in particular must be
supplied by whoever runs the service, per the assignment's instruction to
"create a new API token" for gemma2-9b-it / llama-3.3-70b-versatile.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "AVIOAI CRM — HCP Interaction Module"
    ENV: str = "development"
    API_V1_PREFIX: str = "/api"

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Database ---
    # Postgres by default (per spec: MySQL/PostgreSQL). Falls back to a local
    # SQLite file automatically if DATABASE_URL is left unset, so the API can
    # boot for a quick smoke test without Docker/Postgres running.
    DATABASE_URL: str = "sqlite+aiosqlite:///./avioai_dev.db"

    # --- Groq / LLMs ---
    # Mandatory per the task brief.
    GROQ_API_KEY: str = ""
    PRIMARY_MODEL: str = "gemma2-9b-it"            # required model
    CONTEXT_MODEL: str = "llama-3.3-70b-versatile"  # used for longer-context reasoning
    LLM_TEMPERATURE: float = 0.2

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
