"""FastAPI application settings (Phase 1 vertical slice + Phase 3 AI).

Reads the allowlist-validated environment variables (master-plan §11-D,
data-retention-policy §7.2). ``API_SESSION_SECRET`` is required and must be
a real secret at runtime — placeholder values copied from ``.env.example``
are rejected at startup outside an explicit test environment.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import ValidationInfo, field_validator, model_validator
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

    # ── Phase 3 — AI / Gemini runtime (spec phase-3-ai-analysis.md §2; env
    #    names allowlist-validated, canonical table data-retention-policy §7.2) ──
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"  # GEMINI_MODEL — env-configurable, 2.5 fallback (D1)
    # Corrected C3: Literal-validated at startup — an invalid value is a
    # Pydantic validation error, never silent fall-through.
    gemini_data_policy: Literal["local_free", "client_paid", "disabled"] = "local_free"
    ai_max_context_tokens: int = 24_000  # AI_MAX_CONTEXT_TOKENS — total context budget (C4)
    ai_reserved_output_tokens: int = (
        4_096  # AI_RESERVED_OUTPUT_TOKENS — provider max_output_tokens (C4)
    )
    ai_max_context_chars: int = 96_000  # AI_MAX_CONTEXT_CHARS — deterministic-trim ceiling
    ai_first_token_timeout_seconds: int = 30  # AI_FIRST_TOKEN_TIMEOUT_SECONDS (D10)
    ai_generate_timeout_seconds: int = 60  # AI_GENERATE_TIMEOUT_SECONDS (D10)
    ai_stream_timeout_seconds: int = 120  # AI_STREAM_TIMEOUT_SECONDS (D10)
    ai_queue_wait_seconds: int = 30  # AI_QUEUE_WAIT_SECONDS — bounded ai_lock queue wait (C6)

    # ── Phase 5 — GA4 + Drive OAuth (spec phase-5-ga4-drive.md Task 1/2) ──
    # Same OAuth client serves both flows with separate, incremental scopes
    # (D2). GA4_ENABLED/DRIVE_ENABLED fail fast at startup when the required
    # client configuration is missing — never an undefined runtime state.
    ga4_enabled: bool = False
    ga4_client_id: str | None = None
    ga4_client_secret: str | None = None
    ga4_redirect_uri: str | None = None
    ga4_property_id: str | None = None  # server-resolved property; Admin-API auto-lookup deferred
    drive_enabled: bool = False
    google_cloud_project_number: str | None = None  # Picker setAppId (Task 4)
    drive_download_timeout_seconds: int = 300  # whole-download cap (Task 2: timeouts)

    @model_validator(mode="after")
    def _validate_oauth_config(self) -> "Settings":
        """Fail fast when an enabled Google flow lacks its required config."""
        oauth_enabled = self.ga4_enabled or self.drive_enabled
        if oauth_enabled and not (
            self.ga4_client_id and self.ga4_client_secret and self.ga4_redirect_uri
        ):
            raise ValueError(
                "GA4_ENABLED/DRIVE_ENABLED requires GA4_CLIENT_ID, GA4_CLIENT_SECRET "
                "and GA4_REDIRECT_URI to be configured."
            )
        if self.drive_enabled and not self.google_cloud_project_number:
            raise ValueError(
                "DRIVE_ENABLED requires GOOGLE_CLOUD_PROJECT_NUMBER (Picker setAppId)."
            )
        return self

    @field_validator("api_session_secret")
    @classmethod
    def _validate_secret(cls, value: str, info: ValidationInfo) -> str:
        return validate_session_secret(value, info.data.get("environment", "development"))

    @property
    def cors_origins(self) -> list[str]:
        return [v.strip() for v in self.api_cors_origins.split(",") if v.strip()]

    @property
    def has_ai(self) -> bool:
        """True when a Gemini API key is configured (the app boots without AI)."""
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
