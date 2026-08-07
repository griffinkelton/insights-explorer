"""Phase 5 settings tests (spec phase-5-ga4-drive.md Task 1 — settings validation).

``GA4_ENABLED`` / ``DRIVE_ENABLED`` fail fast at startup when the required
Google client configuration is missing — never an undefined runtime state
(mirrors Phase 3's ``GEMINI_DATA_POLICY`` Literal behavior).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.config import Settings

SECRET = "test-" + ("a" * 40)


def test_ga4_enabled_requires_client_config() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="test", api_session_secret=SECRET, ga4_enabled=True)


def test_drive_enabled_requires_project_number() -> None:
    # Client config present but the Picker project number missing.
    with pytest.raises(ValidationError):
        Settings(
            environment="test",
            api_session_secret=SECRET,
            ga4_enabled=True,
            ga4_client_id="x",
            ga4_client_secret="x",
            ga4_redirect_uri="http://localhost:8000/api/v1/ga4/callback",
            drive_enabled=True,
        )


def test_oauth_config_happy_path() -> None:
    settings = Settings(
        environment="test",
        api_session_secret=SECRET,
        ga4_enabled=True,
        ga4_client_id="x",
        ga4_client_secret="x",
        ga4_redirect_uri="http://localhost:8000/api/v1/ga4/callback",
        ga4_property_id="123456789",
        drive_enabled=True,
        google_cloud_project_number="123456789012",
    )
    assert settings.ga4_property_id == "123456789"
    assert settings.google_cloud_project_number == "123456789012"


def test_disabled_flows_need_no_config() -> None:
    settings = Settings(
        environment="test",
        api_session_secret=SECRET,
        ga4_enabled=False,
        drive_enabled=False,
    )
    assert settings.ga4_enabled is False
    assert settings.drive_enabled is False
