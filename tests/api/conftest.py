"""FastAPI contract-test fixtures (spec §12).

``api.config.get_settings`` is lru-cached and ``api.dependencies`` builds a
serializer at import time, so the environment must be deterministic *before*
any ``api.*`` module is imported. ``conftest.py`` is imported by pytest ahead
of the test modules — force the test environment and a real (non-placeholder)
session secret here.
"""

from __future__ import annotations

import os

import pytest

os.environ["ENVIRONMENT"] = "test"
# Built at runtime — never a contiguous placeholder prefix; the runtime
# validator bypasses in test mode anyway, and a real value keeps signing sane.
os.environ["API_SESSION_SECRET"] = "test-" + ("a" * 40)
# Explicitly blank: the dev .env may carry a real GEMINI_API_KEY, but the
# "AI unavailable" 503 contract tests need the keyless default. Env vars take
# precedence over the .env file in pydantic-settings, so this forces
# Settings.has_ai == False for the whole API suite.
os.environ["GEMINI_API_KEY"] = ""


@pytest.fixture(autouse=True)
def _reset_stores():
    """The in-memory stores are module-level singletons shared across tests;
    reset them so each contract test starts clean."""
    from api.stores.dataset_store import datasets
    from api.stores.session_store import sessions

    # Public test-only helpers (review fix D, 2026-08-06) — no private-dict
    # access, so the fixture survives a future shared-store swap.
    sessions.clear_for_test()
    datasets.clear_for_test()
    yield
