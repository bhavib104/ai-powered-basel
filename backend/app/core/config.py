"""Application configuration.

All settings are read from environment variables, optionally loaded from a
local ``.env`` file (see ``.env.example``).  Nothing secret is hard-coded.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings.

    Field names map to upper-case environment variables (``api_v1_prefix`` ->
    ``API_V1_PREFIX``).  Unknown variables in the environment are ignored so
    that unrelated tooling never breaks startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -------------------------------------------------------
    app_name: str = "AI-Powered Basel Regulatory Risk Intelligence Platform"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    log_format: str = Field(default="text", description="'text' or 'json'")
    api_v1_prefix: str = "/api/v1"

    # --- Database ----------------------------------------------------------
    # Default is a local SQLite file.  Swapping to PostgreSQL later means
    # changing this one value (the ORM/engine layer stays the same).
    database_url: str = "sqlite:///./data/basel.db"

    # --- CORS --------------------------------------------------------------
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # --- AI / LLM ----------------------------------------------------------
    # provider: "ollama" (local, free) | "openai" (optional) | "mock" (no creds)
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # --- Embeddings (local) ------------------------------------------------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Retrieval ---------------------------------------------------------
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.25

    # --- AI tool safety bounds --------------------------------------------
    ai_max_tool_calls: int = 8
    ai_tool_timeout_seconds: int = 20

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (read once per process)."""
    return Settings()
