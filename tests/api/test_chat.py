"""Contract tests: POST /api/v1/chat SSE streaming (spec Task 6 / C5 / C6).

Covers the settled wire format (``event: text/usage/done/error`` + optional
``event: warning``), terminal sequences, the bounded ai_lock queue-wait
(``ai_busy``), failure accounting (``UsageEvent(success=False)`` before the
typed error event), and per-session ledger effects.
"""

from __future__ import annotations

import json

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
            "page_path": ["/", "/about", "/contact"],
            "sessions": [10, 5, 2],
            "users": [8, 4, 2],
        }
    )
    return df.to_csv(index=False).encode()


def _upload(c: TestClient) -> None:
    resp = c.post("/api/v1/upload", files={"file": ("sample.csv", _csv_bytes(), "text/csv")})
    assert resp.status_code == 201


class _FakeSettings:
    """Settings surface the chat route reads (monkeypatched per test)."""

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

    fake = _FakeSettings()
    monkeypatch.setattr(chat_route, "get_settings", lambda: fake)
    return fake


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event = "message"
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: ") :]
            elif line.startswith("data: "):
                data_lines.append(line[len("data: ") :])
        events.append((event, json.loads("".join(data_lines))))
    return events


def test_chat_requires_dataset() -> None:
    fresh = TestClient(app)
    resp = fresh.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert resp.status_code == 409
    assert "No active dataset" in resp.json()["detail"]


def test_chat_503_without_ai_key() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 503
    assert "AI features unavailable" in resp.json()["detail"]


def test_chat_503_when_disabled(ai_settings) -> None:
    ai_settings.gemini_data_policy = "disabled"
    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 503
    assert "disabled" in resp.json()["detail"]


def test_chat_rejects_oversized_history(ai_settings) -> None:
    c = TestClient(app)
    _upload(c)
    big = "x" * 4_000
    payload = {"messages": [{"role": "user", "content": big} for _ in range(7)]}
    resp = c.post("/api/v1/chat", json=payload)
    assert resp.status_code == 422
    assert "24,000-character" in resp.json()["detail"]


def test_chat_rejects_bad_role(ai_settings) -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post(
        "/api/v1/chat",
        json={"messages": [{"role": "system", "content": "hi"}]},
    )
    assert resp.status_code == 422


def test_chat_streams_text_then_done(ai_settings, monkeypatch) -> None:
    import api.routes.chat as chat_route

    async def fake_stream(prompt, **kwargs):
        yield "Hello "
        yield "world"

    monkeypatch.setattr(chat_route, "generate_response_stream_async", fake_stream)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    text_events = [(e, d) for e, d in events if e == "text"]
    assert [d["content"] for e, d in text_events] == ["Hello ", "world"]
    # Terminal sequence: last event is `done` (C5).
    assert events[-1][0] == "done"
    assert events[-1][1] == {"type": "done"}
    assert all(e != "error" for e, _ in events)


def test_chat_emits_usage_event_on_success(ai_settings, monkeypatch) -> None:
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
    assert usage["success_count"] == 1
    assert usage["failure_count"] == 0
    assert usage["input_tokens"] == 10
    assert usage["output_tokens"] == 5
    assert usage["total_tokens"] == 15
    assert usage["by_request_type"] == {"chat": 1}
    assert usage["by_model"] == {"gemini-2.5-flash": 1}


def test_chat_failure_emits_failure_event_then_typed_error(ai_settings, monkeypatch) -> None:
    import api.routes.chat as chat_route

    async def failing_stream(prompt, **kwargs):
        raise RuntimeError("429 RESOURCE_EXHAUSTED")
        yield  # pragma: no cover

    monkeypatch.setattr(chat_route, "generate_response_stream_async", failing_stream)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 200  # SSE transport succeeds; typed error inside

    events = _parse_sse(resp.text)
    error_events = [(e, d) for e, d in events if e == "error"]
    assert len(error_events) == 1
    _, err = error_events[0]
    assert err["type"] == "error"
    assert err["code"] == "rate_limited"
    assert err["retryable"] is True
    assert "429" not in err["message"] and "RESOURCE_EXHAUSTED" not in err["message"]
    # Terminal sequence: error → done (C5).
    assert events[-1][0] == "done"

    usage = c.get("/api/v1/ai/usage").json()
    assert usage["failure_count"] == 1
    assert usage["success_count"] == 0
    assert usage["request_count"] == 1


def test_chat_ai_busy_on_queue_wait_timeout(ai_settings, monkeypatch) -> None:
    import asyncio

    import api.routes.chat as chat_route

    async def fake_wait_for(awaitable, timeout):  # simulate bounded queue-wait expiry
        awaitable.close()  # drop the pending lock-acquire coroutine cleanly
        raise asyncio.TimeoutError()

    monkeypatch.setattr(chat_route.asyncio, "wait_for", fake_wait_for)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    errors = [(e, d) for e, d in events if e == "error"]
    assert len(errors) == 1
    assert errors[0][1]["code"] == "ai_busy"
    assert errors[0][1]["retryable"] is True
    assert events[-1][0] == "done"

    # ai_busy is a failure — ledger records it.
    usage = c.get("/api/v1/ai/usage").json()
    assert usage["failure_count"] == 1


def test_chat_warning_event_when_identifiers_removed(ai_settings, monkeypatch) -> None:
    import api.routes.chat as chat_route

    async def fake_stream(prompt, **kwargs):
        yield "answer"

    monkeypatch.setattr(chat_route, "generate_response_stream_async", fake_stream)

    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "email": ["a@b.c"],
            "sessions": [5],
        }
    )
    c = TestClient(app)
    resp = c.post(
        "/api/v1/upload", files={"file": ("pii.csv", df.to_csv(index=False).encode(), "text/csv")}
    )
    assert resp.status_code == 201

    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "analyze"}]})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    warnings = [(e, d) for e, d in events if e == "warning"]
    assert len(warnings) == 1
    assert warnings[0][1]["code"] == "identifiers_removed_for_ai"
    assert warnings[0][1]["removed_columns"] == ["email"]

    usage = c.get("/api/v1/ai/usage").json()
    assert usage["identifiers_removed"] == 1


def test_chat_context_too_large_typed_error(ai_settings, monkeypatch) -> None:
    import api.routes.chat as chat_route
    from api.services.ai_service import ContextTooLargeError

    async def never_called(prompt, **kwargs):  # pragma: no cover
        yield "should not run"

    monkeypatch.setattr(chat_route, "generate_response_stream_async", never_called)

    # Force the deterministic-minimum-exceeds-budget path regardless of data.
    def _too_large(**kw):
        raise ContextTooLargeError(100)

    monkeypatch.setattr(chat_route, "build_chat_prompt_payload", _too_large)

    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    errors = [(e, d) for e, d in events if e == "error"]
    assert errors[0][1]["code"] == "context_too_large"
    assert errors[0][1]["retryable"] is False
    assert events[-1][0] == "done"
