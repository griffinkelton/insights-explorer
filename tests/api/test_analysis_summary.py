"""Contract tests: POST /api/v1/analysis/summary (spec Task 8).

Non-streaming Gemini narrative — same guards, typed-error policy (C2), and
failure accounting as chat, plus per-request UsageSummary deltas.
"""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app
from utils.gemini_client import UsageEvent

client = TestClient(app)


def _csv_bytes() -> bytes:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "sessions": [10, 5, 2],
        }
    )
    return df.to_csv(index=False).encode()


def _upload(c: TestClient) -> None:
    resp = c.post("/api/v1/upload", files={"file": ("sample.csv", _csv_bytes(), "text/csv")})
    assert resp.status_code == 201


class _FakeSettings:
    has_ai = True
    gemini_data_policy = "local_free"
    gemini_model = "gemini-2.5-flash"
    ai_queue_wait_seconds = 30
    ai_max_context_tokens = 24_000
    ai_reserved_output_tokens = 4_096
    ai_max_context_chars = 96_000
    ai_generate_timeout_seconds = 60


@pytest.fixture
def ai_settings(monkeypatch):
    import api.routes.analysis as analysis_route

    fake = _FakeSettings()
    monkeypatch.setattr(analysis_route, "get_settings", lambda: fake)
    return fake


def test_summary_requires_dataset() -> None:
    fresh = TestClient(app)
    resp = fresh.post("/api/v1/analysis/summary", json={"mode": "summary"})
    assert resp.status_code == 409


def test_summary_503_without_ai_key() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/analysis/summary", json={"mode": "summary"})
    assert resp.status_code == 503


def test_summary_503_when_disabled(ai_settings) -> None:
    ai_settings.gemini_data_policy = "disabled"
    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/analysis/summary", json={"mode": "summary"})
    assert resp.status_code == 503


def test_summary_success_with_usage_delta(ai_settings, monkeypatch) -> None:
    import api.routes.analysis as analysis_route

    def fake_generate(prompt, *, usage_sink=None, **kwargs):
        if usage_sink is not None:
            usage_sink(
                UsageEvent(
                    model="gemini-2.5-flash",
                    request_type="summary",
                    input_tokens=20,
                    output_tokens=8,
                    total_token_count=28,
                    success=True,
                )
            )
        return "This dataset shows a declining session trend."

    monkeypatch.setattr(analysis_route, "generate_response", fake_generate)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/analysis/summary", json={"mode": "summary"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "gemini-2.5-flash"
    assert "declining" in body["summary"]
    assert body["usage"] == {
        "input_tokens": 20,
        "output_tokens": 8,
        "thoughts_token_count": 0,
        "total_token_count": 28,
    }

    usage = c.get("/api/v1/ai/usage").json()
    assert usage["request_count"] == 1
    assert usage["success_count"] == 1
    assert usage["input_tokens"] == 20


def test_summary_failure_typed_error_and_ledger(ai_settings, monkeypatch) -> None:
    import api.routes.analysis as analysis_route

    def failing_generate(prompt, **kwargs):
        raise RuntimeError("quota exceeded for the project")

    monkeypatch.setattr(analysis_route, "generate_response", failing_generate)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/analysis/summary", json={"mode": "summary"})
    assert resp.status_code == 429  # quota_exhausted → 429
    body = resp.json()
    assert "quota" in body["detail"].lower()
    assert "quota exceeded for the project" not in body["detail"]  # C2 — no raw text

    usage = c.get("/api/v1/ai/usage").json()
    assert usage["failure_count"] == 1
    assert usage["success_count"] == 0


def test_summary_context_too_large_422(ai_settings, monkeypatch) -> None:
    import api.routes.analysis as analysis_route
    from api.services.ai_service import ContextTooLargeError

    def too_large(**kwargs):
        raise ContextTooLargeError(100)

    monkeypatch.setattr(analysis_route, "build_summary_prompt_payload", too_large)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/analysis/summary", json={"mode": "summary"})
    assert resp.status_code == 422
    assert "too large" in resp.json()["detail"].lower()
