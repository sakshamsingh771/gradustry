import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Gradustry API"
    ENV: str = "development"

    # Default to local SQLite so the project runs with zero external setup.
    # For a production-like run, set DATABASE_URL to a Postgres DSN, e.g.:
    # postgresql+psycopg2://gradustry:gradustry@localhost:5432/gradustry
    DATABASE_URL: str = "sqlite:///./gradustry.db"

    JWT_SECRET: str = "dev-secret-change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h, fine for hackathon demo

    # Accepts a JSON array string (e.g. '["http://a.com","http://b.com"]'),
    # a comma-separated string (e.g. "http://a.com,http://b.com"), or a
    # single origin string. Kept as raw str here (NOT List[str]) because
    # pydantic-settings auto-JSON-decodes complex-typed env values *before*
    # any validator runs, which crashes on a plain (non-JSON) origin string
    # like "http://localhost:5173". Parsed into a list via the
    # `cors_origins` property below instead.
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- AI provider (optional) ---
    # If AI_API_KEY is unset, AI_PROVIDER is "none", or any call fails/times out,
    # every AI feature transparently falls back to its deterministic algorithm.
    AI_PROVIDER: str = "none"  # "gemini" | "openai" | "none"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gemini-2.0-flash"
    AI_TIMEOUT_SECONDS: float = 12.0
    AI_MAX_RETRIES: int = 2

    GITHUB_TOKEN: str = ""  # optional, raises GitHub API rate limits

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Normalize CORS_ORIGINS (raw env str) into List[str] on access.

        Accepts a JSON array string, a comma-separated string, or a single
        origin string.
        """
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return ["http://localhost:5173"]

        # Try JSON array first, e.g. '["http://a.com","http://b.com"]'
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]

        # Fall back to comma-separated or single-value string
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
