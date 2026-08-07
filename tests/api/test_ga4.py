"""Phase 5 GA4 contract tests (spec phase-5-ga4-drive.md Task 6).

Covers the locked OAuth flow (PKCE S256, one-time state consumption,
transaction-cookie binding, session rotation, callback vocabulary) and the
first-pull contract: server-owned request builder, pagination **proven via
mocks** (≈90-row production reality — no high-cardinality dimension added),
quota recorded from successful responses only, and the locked typed error
taxonomy (quota exhaustion is non-retryable — no retry loop).
"""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from api.main import app

# Phase 5 OAuth callbacks 303-redirect to the React frontend — never follow
# them in contract tests (the browser handles the redirect, not the API).
client = TestClient(app, follow_redirects=False)

# Server-side-only fake credentials (built at runtime; never credential-shaped).
FAKE_CREDS = {
    "token": "test-access-token",
    "refresh_token": "test-refresh-token",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "test-client",
    "client_secret": "test-secret",
    "scopes": ["openid", "email", "profile", "https://www.googleapis.com/auth/analytics.readonly"],
    "expiry": None,
}

QUOTA = SimpleNamespace(
    tokens_per_day=SimpleNamespace(consumed=10, remaining=199990),
    tokens_per_hour=SimpleNamespace(consumed=5, remaining=39995),
    concurrent_requests=SimpleNamespace(consumed=1, remaining=9),
    server_errors_per_project_per_hour=SimpleNamespace(consumed=0, remaining=10),
)


def _row(idx: int) -> SimpleNamespace:
    """A single date-row with the five canonical metric values."""
    return SimpleNamespace(
        dimension_values=[SimpleNamespace(value=f"2026-05-{idx % 28 + 1:02d}")],
        metric_values=[SimpleNamespace(value=str((idx + 1) * 10)) for _ in range(5)],
    )


class FakeAsyncClient:
    """Mock BetaAnalyticsDataAsyncClient — pages by offset; optional error seq."""

    def __init__(
        self,
        page_rows: list[int],
        row_count: int,
        quota=QUOTA,
        error_seq: list | None = None,
    ) -> None:
        self.page_rows = list(page_rows)
        self.row_count = row_count
        self.quota = quota
        self.error_seq = list(error_seq or [])
        self.calls: list = []

    async def run_report(self, request, timeout=None):
        self.calls.append(request)
        if self.error_seq:
            error = self.error_seq.pop(0)
            if error is not None:
                raise error
        count = self.page_rows.pop(0) if self.page_rows else 0
        return SimpleNamespace(
            rows=[_row(i) for i in range(count)],
            row_count=self.row_count,
            property_quota=self.quota,
        )


def _begin_oauth(connection: str = "ga4", http_client: TestClient = client) -> str:
    """POST /ga4/connect → return the OAuth state from the authorization URL."""
    resp = http_client.post("/api/v1/ga4/connect", json={"connection": connection})
    assert resp.status_code == 200
    url = resp.json()["authorization_url"]
    query = parse_qs(urlparse(url).query)
    return query["state"][0]


def _complete_oauth(
    state: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    http_client: TestClient = client,
    exchange_result=FAKE_CREDS,
):
    """GET /ga4/callback with a mocked code exchange (TestClient jar holds cookies)."""
    if exchange_result is not None:
        monkeypatch.setattr(
            "api.routes.ga4.exchange_code",
            lambda **kwargs: dict(exchange_result),
        )
    return http_client.get(f"/api/v1/ga4/callback?code=test-code&state={state}")


def _connected_session(monkeypatch: pytest.MonkeyPatch, connection: str = "ga4") -> None:
    """Full mocked connect→callback flow; TestClient jar now holds the session."""
    state = _begin_oauth(connection)
    resp = _complete_oauth(state, monkeypatch)
    assert resp.status_code == 303
    assert "status=success" in resp.headers["location"]


# ── Connect ────────────────────────────────────────────────────────────────


def test_connect_returns_authorization_url_with_pkce(oauth_settings) -> None:
    resp = client.post("/api/v1/ga4/connect", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert "authorization_url" in body
    query = parse_qs(urlparse(body["authorization_url"]).query)
    assert query["state"]  # cryptographically random state
    assert query["code_challenge"]  # PKCE S256 — never plain
    assert query["code_challenge_method"] == ["S256"]
    # HttpOnly transaction cookie binds the browser to the transaction.
    cookie = resp.cookies.get("insights_oauth_txn")
    assert cookie


def test_connect_not_configured_503() -> None:
    # No oauth_settings fixture → default settings (ga4_enabled=False).
    resp = client.post("/api/v1/ga4/connect", json={})
    assert resp.status_code == 503
    assert resp.json()["detail"]["code"] == "ga4_not_configured"


def test_connect_invalid_connection_422(oauth_settings) -> None:
    resp = client.post("/api/v1/ga4/connect", json={"connection": "sheets"})
    assert resp.status_code == 422


def test_connect_rejects_foreign_origin(oauth_settings) -> None:
    resp = client.post(
        "/api/v1/ga4/connect",
        json={},
        headers={"Origin": "https://evil.example"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "csrf_origin_rejected"


# ── Callback ───────────────────────────────────────────────────────────────


def test_callback_missing_state_400(oauth_settings) -> None:
    resp = client.get("/api/v1/ga4/callback?code=test-code")
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "invalid_state"


def test_callback_unknown_state_400(oauth_settings) -> None:
    resp = client.get("/api/v1/ga4/callback?code=test-code&state=unknown-state-value")
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "invalid_state"


def test_callback_replay_consumed_state_400(oauth_settings, monkeypatch) -> None:
    state = _begin_oauth()
    assert _complete_oauth(state, monkeypatch).status_code == 303
    # Second callback with the SAME state — one-time consumption, no replay.
    resp = _complete_oauth(state, monkeypatch)
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "invalid_state"


def test_callback_transaction_cookie_mismatch_400(oauth_settings, monkeypatch) -> None:
    # Connect on one client (txn cookie lands there); callback on a fresh
    # client (no matching transaction cookie) → mismatch.
    other = TestClient(app)
    state = _begin_oauth(http_client=other)
    resp = _complete_oauth(state, monkeypatch, http_client=client)
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "transaction_mismatch"


def test_callback_success_rotates_session(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    status = client.get("/api/v1/ga4/status")
    assert status.status_code == 200
    assert status.json() == {"connected": True}


def test_callback_exchange_failure_token_exchange_failed(oauth_settings, monkeypatch) -> None:
    state = _begin_oauth()

    def _boom(**kwargs):
        raise RuntimeError("provider exchange failed")

    monkeypatch.setattr("api.routes.ga4.exchange_code", _boom)
    resp = client.get(f"/api/v1/ga4/callback?code=test-code&state={state}")
    assert resp.status_code == 303
    assert "status=error" in resp.headers["location"]
    assert "reason=token_exchange_failed" in resp.headers["location"]


def test_callback_cancelled_on_provider_denied(oauth_settings) -> None:
    resp = client.get("/api/v1/ga4/callback?error=access_denied")
    assert resp.status_code == 303
    assert "status=cancelled" in resp.headers["location"]


def test_callback_drive_denial_redirects_to_drive_callback(oauth_settings) -> None:
    # A denied drive.file consent routes to the Drive callback page (return_path
    # resolved from the transaction without consuming it).
    state = _begin_oauth("drive")
    resp = client.get(f"/api/v1/ga4/callback?error=access_denied&state={state}")
    assert resp.status_code == 303
    assert "/auth/drive/callback" in resp.headers["location"]
    assert "status=cancelled" in resp.headers["location"]


def test_callback_scope_verification_denied(oauth_settings, monkeypatch) -> None:
    # A grant missing the required analytics.readonly scope is never stored as
    # GA4 consent (consent-state model — degraded grants don't blur consent).
    state = _begin_oauth("ga4")
    monkeypatch.setattr(
        "api.routes.ga4.exchange_code",
        lambda **kwargs: {
            **FAKE_CREDS,
            "scopes": ["https://www.googleapis.com/auth/drive.file"],
        },
    )
    resp = client.get(f"/api/v1/ga4/callback?code=test-code&state={state}")
    assert resp.status_code == 303
    assert "status=error" in resp.headers["location"]
    assert "reason=scope_denied" in resp.headers["location"]
    assert client.get("/api/v1/ga4/status").json() == {"connected": False}


def test_connect_same_origin_host_match_allowed(oauth_settings) -> None:
    # Same-origin deploy: the browser's Origin equals the request Host — passes
    # even when the CORS allowlist is empty.
    resp = client.post(
        "/api/v1/ga4/connect",
        json={},
        headers={"Origin": "http://testserver", "Host": "testserver"},
    )
    assert resp.status_code == 200


# ── Status / disconnect ────────────────────────────────────────────────────


def test_status_reflects_connection_lifecycle(oauth_settings, monkeypatch) -> None:
    assert client.get("/api/v1/ga4/status").json() == {"connected": False}
    _connected_session(monkeypatch)
    assert client.get("/api/v1/ga4/status").json() == {"connected": True}
    resp = client.post("/api/v1/ga4/disconnect")
    assert resp.status_code == 200
    assert client.get("/api/v1/ga4/status").json() == {"connected": False}


def test_disconnect_revokes_tokens(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    revoked = []

    monkeypatch.setattr(
        "api.routes.ga4.revoke_tokens",
        lambda creds: revoked.append(creds),
    )
    client.post("/api/v1/ga4/disconnect")
    assert revoked  # best-effort revoke attempted before clearing


# ── Pull ───────────────────────────────────────────────────────────────────


def test_pull_requires_connection_409(oauth_settings) -> None:
    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "ga4_connection_required"


def test_pull_success_single_page(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    fake = FakeAsyncClient(page_rows=[90], row_count=90)
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)

    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 200
    dataset = resp.json()["dataset"]
    assert dataset["source"] == "ga4"
    assert dataset["row_count"] == 90
    assert dataset["filename"] == "ga4-123456789.csv"
    # Server-owned request builder: no client-supplied metrics/dimensions.
    request = fake.calls[0]
    assert request.offset == 0
    assert request.limit == 10_000
    assert request.return_property_quota is True
    assert [m.name for m in request.metrics] == [
        "sessions",
        "totalUsers",
        "engagedSessions",
        "engagementRate",
        "bounceRate",
    ]
    # Contract provenance on metrics: provisional rows + unavailable rows 3-5.
    statuses = {m["id"]: m["validation_status"] for m in dataset["metrics"]}
    assert statuses["sessions"] == "provisional"
    assert statuses["questionnaire_start_count"] == "unavailable"
    assert statuses["questionnaire_completion_rate"] == "unavailable"
    assert statuses["post_questionnaire_action_rate"] == "unavailable"
    # Provenance: page_count/row_count/quota_observed present; no tokens.
    provenance = dataset["provenance"]
    assert provenance["page_count"] == 1
    assert provenance["row_count"] == 90
    assert provenance["quota_observed"] is True
    assert provenance["quota"]["tokens_per_day"]["remaining"] == 199990
    # Provider tokens / raw OAuth metadata never enter provenance.
    assert "refresh_token" not in str(provenance)
    assert "test-access-token" not in str(provenance)


def test_pull_pagination_multipage(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    fake = FakeAsyncClient(page_rows=[10_000, 10_000, 1], row_count=20_001)
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)

    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 200
    assert resp.json()["dataset"]["row_count"] == 20_001
    # Offset progression: 0 → 10,000 → 20,000; no duplicate rows.
    assert [r.offset for r in fake.calls] == [0, 10_000, 20_000]
    assert fake.calls[1].offset == 10_000  # second request offset = first page rows
    assert resp.json()["dataset"]["provenance"]["page_count"] == 3


def test_pull_empty_report_422(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    fake = FakeAsyncClient(page_rows=[0], row_count=0)
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)
    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "ga4_empty_report"


def test_pull_quota_exhausted_no_retry_loop(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    from google.api_core.exceptions import ResourceExhausted

    fake = FakeAsyncClient(
        page_rows=[],
        row_count=0,
        error_seq=[ResourceExhausted("quota")],
    )
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)
    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "ga4_quota_exhausted"
    assert resp.json()["detail"]["retryable"] is False
    assert len(fake.calls) == 1  # NO retry on quota exhaustion


def test_pull_provider_unavailable_one_retry_then_success(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    from google.api_core.exceptions import ServiceUnavailable

    fake = FakeAsyncClient(
        page_rows=[90],
        row_count=90,
        error_seq=[ServiceUnavailable("down")],
    )
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)
    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 200
    assert len(fake.calls) == 2  # exactly one pre-response retry


def test_pull_provider_unavailable_after_retry_503(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    from google.api_core.exceptions import ServiceUnavailable

    fake = FakeAsyncClient(
        page_rows=[],
        row_count=0,
        error_seq=[ServiceUnavailable("down"), ServiceUnavailable("down")],
    )
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)
    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 503
    assert resp.json()["detail"]["code"] == "ga4_provider_unavailable"
    assert resp.json()["detail"]["retryable"] is True


def test_pull_timeout_504(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    from google.api_core.exceptions import DeadlineExceeded

    fake = FakeAsyncClient(page_rows=[], row_count=0, error_seq=[DeadlineExceeded("slow")])
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)
    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 504
    assert resp.json()["detail"]["code"] == "ga4_timeout"


def test_pull_access_denied_403(oauth_settings, monkeypatch) -> None:
    _connected_session(monkeypatch)
    from google.api_core.exceptions import PermissionDenied

    fake = FakeAsyncClient(page_rows=[], row_count=0, error_seq=[PermissionDenied("nope")])
    monkeypatch.setattr("api.routes.ga4.build_ga4_client", lambda creds: fake)
    resp = client.post("/api/v1/ga4/pull")
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "ga4_access_denied"
