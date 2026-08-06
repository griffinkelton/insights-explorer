"""Contract tests: session cookie, expiry modes, runtime secret validation."""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from api.config import Settings, validate_session_secret
from api.dependencies import SESSION_COOKIE
from api.main import app
from api.stores.dataset_store import datasets
from api.stores.session_store import AppSession, sessions, utcnow

client = TestClient(app)


def _only_session() -> tuple[str, AppSession]:
    """The single live in-memory session (dev store is a dict)."""
    entries = list(sessions._sessions.items())  # type: ignore[attr-defined]
    assert len(entries) == 1
    return entries[0]


def _cookie_from(resp) -> str | None:
    return resp.cookies.get(SESSION_COOKIE)


def test_cookie_set_and_correlates() -> None:
    c = TestClient(app)
    first = c.get("/api/v1/data/context")
    assert first.status_code == 409  # no dataset yet
    cookie = _cookie_from(first)
    assert cookie
    assert first.headers.get("set-cookie", "").lower().find("httponly") != -1
    # Same client reuses the cookie: the second request must NOT mint a new
    # session (the store still holds exactly one).
    second = c.get("/api/v1/data/context")
    assert second.status_code == 409
    assert len(sessions._sessions) == 1  # type: ignore[attr-defined]


def test_tampered_cookie_gets_fresh_session() -> None:
    c = TestClient(app)
    c.get("/api/v1/data/context")
    cookie = c.cookies.get(SESSION_COOKIE)
    assert cookie
    tampered = cookie[:-1] + ("X" if cookie[-1] != "X" else "Y")
    c.cookies.set(SESSION_COOKIE, tampered)
    resp = c.get("/api/v1/data/context")
    assert resp.status_code == 409  # no 500
    new_cookie = resp.cookies.get(SESSION_COOKIE)
    assert new_cookie and new_cookie != tampered


def test_idle_expiry_discards_session_and_state() -> None:
    c = TestClient(app)
    upload = c.post(
        "/api/v1/upload",
        files={"file": ("sample.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert upload.status_code == 201
    session_id, session = _only_session()
    dataset_id = session.dataset_id
    assert dataset_id
    # Backdate past the 2 h idle window (and inside the 12 h absolute window).
    session.last_accessed_at = utcnow() - timedelta(hours=3)
    resp = c.get("/api/v1/data/context")
    assert resp.status_code == 409
    # Old session and its dataset are gone; nothing is silently preserved.
    assert sessions.get(session_id) is None
    assert datasets.get(dataset_id) is None
    # A fresh session was issued (store now holds exactly one new entry).
    assert len(sessions._sessions) == 1  # type: ignore[attr-defined]


def test_absolute_expiry_discards_session_and_state() -> None:
    c = TestClient(app)
    upload = c.post(
        "/api/v1/upload",
        files={"file": ("sample.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert upload.status_code == 201
    session_id, session = _only_session()
    dataset_id = session.dataset_id
    assert dataset_id
    # Backdate past the 12 h absolute window.
    session.created_at = utcnow() - timedelta(hours=13)
    session.last_accessed_at = session.created_at
    resp = c.get("/api/v1/data/context")
    assert resp.status_code == 409
    assert sessions.get(session_id) is None
    assert datasets.get(dataset_id) is None


def test_validate_session_secret_rejects_placeholder_outside_test() -> None:
    with pytest.raises(ValueError, match="placeholder"):
        validate_session_secret("replace-with-a-long-random-value", "development")
    with pytest.raises(ValueError, match="placeholder"):
        validate_session_secret("", "development")
    with pytest.raises(ValueError, match="placeholder"):
        validate_session_secret("your_secret_here", "development")


def test_validate_session_secret_allows_test_and_real() -> None:
    assert (
        validate_session_secret("replace-with-a-long-random-value", "test")
        == "replace-with-a-long-random-value"
    )
    assert (
        validate_session_secret("a-real-secret-value-123", "development")
        == "a-real-secret-value-123"
    )


def test_settings_require_non_placeholder_secret(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("API_SESSION_SECRET", "replace-with-a-long-random-value")
    with pytest.raises(ValueError, match="placeholder"):
        Settings()
