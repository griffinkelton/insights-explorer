"""Contract tests: GET /api/v1/ai/usage (spec Task 11).

Per-session counts only (D13) — no budgets enforced in Phase 3. Clear Data
resets the ledger with the rest of the dataset-derived state (D5).
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
            "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
            "sessions": [10, 5],
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
    ai_first_token_timeout_seconds = 30
    ai_stream_timeout_seconds = 120


@pytest.fixture
def ai_settings(monkeypatch):
    import api.routes.chat as chat_route

    monkeypatch.setattr(chat_route, "get_settings", lambda: _FakeSettings())
    return _FakeSettings()


def test_usage_zero_state() -> None:
    resp = client.get("/api/v1/ai/usage")
    assert resp.status_code == 200
    body = resp.json()
    assert body["request_count"] == 0
    assert body["success_count"] == 0
    assert body["failure_count"] == 0
    assert body["avg_ttft_ms"] is None
    assert body["avg_ttlt_ms"] is None
    assert body["by_request_type"] == {}
    assert body["by_model"] == {}


def test_usage_after_chat_then_clear_resets(ai_settings, monkeypatch) -> None:
    import api.routes.chat as chat_route

    async def fake_stream(prompt, *, usage_sink=None, **kwargs):
        yield "ok"
        if usage_sink is not None:
            usage_sink(
                UsageEvent(
                    model="gemini-2.5-flash",
                    request_type="chat",
                    input_tokens=10,
                    output_tokens=5,
                    total_token_count=15,
                    success=True,
                )
            )

    monkeypatch.setattr(chat_route, "generate_response_stream_async", fake_stream)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 200

    usage = c.get("/api/v1/ai/usage").json()
    assert usage["request_count"] == 1
    assert usage["total_tokens"] == 15
    assert usage["avg_ttft_ms"] is not None  # latency aggregates computed

    # Clear Data resets dataset-derived state INCLUDING the usage ledger (D5).
    clear = c.post("/api/v1/data/clear")
    assert clear.status_code == 200
    usage = c.get("/api/v1/ai/usage").json()
    assert usage["request_count"] == 0
    assert usage["success_count"] == 0
    assert usage["total_tokens"] == 0
    assert usage["avg_ttft_ms"] is None
