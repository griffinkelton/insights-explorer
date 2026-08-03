"""Phase 3.3 E2E fixtures: real Google session reuse + env-var gating.

ONE-TIME SETUP (run interactively, locally, NEVER in CI):
    E2E_REAL_DRIVE=1 python tests/e2e/auth_setup.py

This launches a headed browser so you can sign into Google manually.
On success it writes ``tests/e2e/.auth/session.json``.  That file holds
live session cookies; it must never be committed or shared.

CI / automated runs consume the saved session:
    E2E_REAL_DRIVE=1 python -m pytest tests/e2e/test_drive_picker_e2e.py -v
"""

import os
from pathlib import Path

import pytest

_SESSION_PATH = Path(__file__).resolve().parent / ".auth" / "session.json"


def _is_opted_in() -> bool:
    """Real-Drive E2E tests are gated behind E2E_REAL_DRIVE=1.

    Without it, the entire module skips — CI and fresh clones never fail.
    """
    return os.getenv("E2E_REAL_DRIVE", "") == "1"


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover
    """Register the e2e marker so pytest doesn't warn."""
    config.addinivalue_line("markers", "e2e_real_drive: real Google Drive Picker E2E test")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:  # pragma: no cover
    """Skip all real-Drive tests unless E2E_REAL_DRIVE=1."""
    if _is_opted_in():
        return
    skip_reason = (
        "E2E_REAL_DRIVE=1 not set — real-Drive E2E tests require an "
        "interactive OAuth session (run auth_setup.py first)."
    )
    for item in items:
        if "e2e_real_drive" in item.keywords:
            item.add_marker(pytest.mark.skip(reason=skip_reason))
