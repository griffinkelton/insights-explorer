"""Contract tests: session cookie, expiry modes, runtime secret validation.

Review fix 2026-08-06 (D): tests use only the **public** store surface
(create/get/delete + clear_for_test/count_for_test) and the signed-cookie
transport. No private ``_sessions``/``_items`` dict access — the tests stay
valid if the in-memory stores are swapped for a shared store later.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from api.config import Settings, validate_session_secret
from api.dependencies import SESSION_COOKIE, _verify_session_id
from api.main import app
from api.stores.dataset_store import datasets
from api.stores.session_store import AppSession, sessions, utcnow

client = TestClient(app)


def _session_id_from(client: TestClient) -> str:
    """Decode the signed session cookie from the client's cookie jar (public
    transport). Reads the jar, not the response, because reusing an existing
    session does NOT re-send Set-Cookie."""
    cookie = client.cookies.get(SESSION_COOKIE)
    assert cookie, "client jar has no session cookie"
    sid = _verify_session_id(cookie)
    assert sid, "cookie did not verify"
    return sid


def _only_session_after(client: TestClient, resp) -> tuple[str, AppSession]:
    """Return (session_id, session) for the single live session after a request."""
    sid = _session_id_from(client)
    session = sessions.get(sid)
    assert session is not None
    assert sessions.count_for_test() == 1, "expected exactly one live session"
    return sid, session


def test_cookie_set_and_correlates() -> None:
    c = TestClient(app)
    first = c.get("/api/v1/data/context")
    assert first.status_code == 409  # no dataset yet
    assert first.headers.get("set-cookie", "").lower().find("httponly") != -1
    sid = _session_id_from(c)
    assert sid
    # Same client reuses the cookie: the second request must NOT mint a new
    # session (the store still holds exactly one).
    second = c.get("/api/v1/data/context")
    assert second.status_code == 409
    assert sessions.count_for_test() == 1
    assert _session_id_from(c) == sid


def test_tampered_cookie_gets_fresh_session() -> None:
    c = TestClient(app)
    assert c.get("/api/v1/data/context").status_code == 409
    cookie = c.cookies.get(SESSION_COOKIE)
    assert cookie
    tampered = cookie[:-1] + ("X" if cookie[-1] != "X" else "Y")
    c.cookies.set(SESSION_COOKIE, tampered)
    resp = c.get("/api/v1/data/context")
    assert resp.status_code == 409  # no 500
    # Assert on the Set-Cookie header: httpx's cookie jar raises
    # CookieConflict when a manually-set cookie and the response cookie share
    # a name, so response-cookie access is unreliable here.
    set_cookie = resp.headers.get("set-cookie", "")
    assert SESSION_COOKIE in set_cookie
    new_value = set_cookie.split(";", 1)[0].split("=", 1)[1]
    assert new_value != tampered
    # The tampered cookie did not verify, so a fresh session was minted.
    assert _verify_session_id(tampered) is None
    assert sessions.count_for_test() == 2  # original + fresh


def test_idle_expiry_discards_session_and_state() -> None:
    c = TestClient(app)
    upload = c.post(
        "/api/v1/upload",
        files={"file": ("sample.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert upload.status_code == 201
    session_id, session = _only_session_after(c, upload)
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
    assert sessions.count_for_test() == 1


def test_absolute_expiry_discards_session_and_state() -> None:
    c = TestClient(app)
    upload = c.post(
        "/api/v1/upload",
        files={"file": ("sample.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert upload.status_code == 201
    session_id, session = _only_session_after(c, upload)
    dataset_id = session.dataset_id
    assert dataset_id
    # Backdate past the 12 h absolute window.
    session.created_at = utcnow() - timedelta(hours=13)
    session.last_accessed_at = session.created_at
    resp = c.get("/api/v1/data/context")
    assert resp.status_code == 409
    assert sessions.get(session_id) is None
    assert datasets.get(dataset_id) is None


def test_store_test_helpers_reset_state() -> None:
    """clear_for_test empties both stores between/within suites (review fix D)."""
    sessions.clear_for_test()
    datasets.clear_for_test()
    assert sessions.count_for_test() == 0
    assert datasets.count_for_test() == 0
    sessions.create()
    assert sessions.count_for_test() == 1
    sessions.clear_for_test()
    assert sessions.count_for_test() == 0


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
