"""FastAPI application settings (Phase 1 vertical slice).

Reads the five allowlist-validated environment variables (master-plan §11-D).
``API_SESSION_SECRET`` is required and must be a real secret at runtime —
placeholder values copied from ``.env.example`` are rejected at startup
outside an explicit test environment.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_PREFIXES = ("replace-with-", "your_", "<")


def validate_session_secret(value: str, environment: str) -> str:
    """Reject empty/placeholder secrets outside an explicit test environment —
    copying ``.env.example`` to ``.env`` without editing must fail at startup."""
    if environment == "test":
        return value
    if not value or value == "..." or value.startswith(PLACEHOLDER_PREFIXES):
        raise ValueError(
            "API_SESSION_SECRET must be a real deployment/local secret, "
            "not an .env.example placeholder."
        )
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_cors_origins: str = "http://localhost:5173"  # Vite dev origin; "" = same-origin deploy
    api_session_secret: str  # REQUIRED — no default (guard-allowlisted)
    frontend_url: str = "http://localhost:5173"
    max_browser_upload_bytes: int = 25 * 1024 * 1024  # MAX_BROWSER_UPLOAD_BYTES (locked)
    max_ingest_bytes: int = 100 * 1024 * 1024  # MAX_INGEST_BYTES — Drive/server-side only

    @field_validator("api_session_secret")
    @classmethod
    def _validate_secret(cls, value: str, info: ValidationInfo) -> str:
        return validate_session_secret(value, info.data.get("environment", "development"))

    @property
    def cors_origins(self) -> list[str]:
        return [v.strip() for v in self.api_cors_origins.split(",") if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
