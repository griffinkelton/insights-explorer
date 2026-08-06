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


@pytest.fixture(autouse=True)
def _reset_stores():
    """The in-memory stores are module-level singletons shared across tests;
    reset them so each contract test starts clean."""
    from api.stores.dataset_store import datasets
    from api.stores.session_store import sessions

    sessions._sessions.clear()  # type: ignore[attr-defined]
    datasets._items.clear()  # type: ignore[attr-defined]
    yield
