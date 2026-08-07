"""ai_service unit tests (spec Task 7 / D4 / D11 / C2).

Deterministic-context assembly, identifier scrubbing (heuristic — NOT a
complete PII detector), metric-status caveats, the two-stage token guard
(local estimate → exact preflight → trim → typed context_too_large), and the
provider-error classifier (typed codes only — never raw exception text).
"""

from __future__ import annotations

import pandas as pd
import pytest

from api.schemas import ChatMessage, DatasetContext, DateRange
from api.services.ai_service import (
    ContextTooLargeError,
    TypedAiError,
    build_chat_prompt_payload,
    build_deterministic_context,
    build_summary_prompt_payload,
    classify_provider_error,
    estimate_tokens,
    ledger_sink,
    metric_status_caveats,
    scrub_identifiers,
    validate_chat_messages,
)
from api.stores.session_store import AppSession


# ── scrub_identifiers (D4) ─────────────────────────────────────────────────
def test_scrub_identifiers_drops_likely_columns() -> None:
    df = pd.DataFrame(
        {
            "email": ["a@b.c"],
            "user_id": [1],
            "sessions": [5],
            "users": [4],
        }
    )
    scrubbed, removed = scrub_identifiers(df)
    assert set(removed) == {"email", "user_id"}
    assert list(scrubbed.columns) == ["sessions", "users"]


def test_scrub_identifiers_keeps_legitimate_dimensions() -> None:
    # Business-entity and generic columns are NOT removed (over-removal guard):
    # `customer_id`, `account`, `member`, and a generic `id` stay.
    df = pd.DataFrame(
        {
            "customer_id": [1],
            "account": ["acme"],
            "member": [True],
            "id": [7],
            "sessions": [5],
        }
    )
    scrubbed, removed = scrub_identifiers(df)
    assert removed == []
    assert list(scrubbed.columns) == ["customer_id", "account", "member", "id", "sessions"]


def test_scrub_identifiers_is_noop_without_matches() -> None:
    df = pd.DataFrame({"sessions": [5], "users": [4]})
    scrubbed, removed = scrub_identifiers(df)
    assert removed == []
    assert scrubbed is df  # unchanged object — no wasteful copy


# ── build_deterministic_context (Task 7) ───────────────────────────────────
def _ctx() -> DatasetContext:
    return DatasetContext(
        source="upload",
        filename="sample.csv",
        row_count=3,
        date_range=DateRange(),
        columns=[],
    )


def test_deterministic_context_adds_identifier_warning() -> None:
    df = pd.DataFrame({"date": ["2026-01-01"], "email": ["a@b.c"], "sessions": [5]})
    ctx = _ctx()
    session = AppSession()
    result = build_deterministic_context(df, ctx, session)
    assert result.removed_columns == ["email"]
    codes = [w.code for w in ctx.warnings]
    assert "identifiers_removed_for_ai" in codes
    warning = next(w for w in ctx.warnings if w.code == "identifiers_removed_for_ai")
    assert warning.removed_columns == ["email"]


def test_deterministic_context_deduplicates_warning() -> None:
    df = pd.DataFrame({"email": ["a@b.c"], "sessions": [5]})
    ctx = _ctx()
    session = AppSession()
    build_deterministic_context(df, ctx, session)
    build_deterministic_context(df, ctx, session)  # second call must not duplicate
    codes = [w.code for w in ctx.warnings]
    assert codes.count("identifiers_removed_for_ai") == 1


def test_deterministic_context_never_keeps_full_frame() -> None:
    df = pd.DataFrame({"date": range(50), "sessions": range(50)})
    result = build_deterministic_context(df, _ctx(), AppSession())
    # prompt_df is a sampled, scrubbed frame — never the full raw frame.
    assert len(result.prompt_df) <= 5
    assert "date" not in result.prompt_df.columns or len(result.prompt_df) <= 5


# ── metric_status_caveats (measurement contract) ───────────────────────────
def test_metric_status_caveats_provisional_and_unavailable() -> None:
    ctx = _ctx()
    ctx.metrics = [
        {"id": "m1", "status": "provisional"},
        {"id": "m2", "status": "unavailable"},
        {"id": "m3", "status": "validated"},
    ]
    caveats = metric_status_caveats(ctx)
    assert any("m1 is provisional" in c for c in caveats)
    assert any("m2 is unavailable" in c for c in caveats)
    assert not any("m3" in c for c in caveats)


# ── validate_chat_messages (D12) ───────────────────────────────────────────
def test_validate_chat_messages_ok() -> None:
    validate_chat_messages([ChatMessage(role="user", content="hi")])


def test_validate_chat_messages_rejects_total_ceiling() -> None:
    big = "x" * 4_000
    messages = [ChatMessage(role="user", content=big) for _ in range(7)]  # 28k chars
    with pytest.raises(ValueError, match="24,000-character"):
        validate_chat_messages(messages)


# ── estimate_tokens (D11 — chars ÷ 4 heuristic) ────────────────────────────
def test_estimate_tokens_heuristic() -> None:
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("") == 1  # floor of 1 — never zero
    assert estimate_tokens("a" * 100) == 25


# ── build_chat_prompt_payload budget (D11) ─────────────────────────────────
def test_chat_payload_budget_ok() -> None:
    df = pd.DataFrame({"sessions": [1, 2, 3]})
    result = build_chat_prompt_payload(
        user_question="What is happening?",
        history=[],
        context=build_deterministic_context(df, _ctx(), AppSession()),
        max_context_tokens=24_000,
        reserved_output_tokens=4_096,
        max_context_chars=96_000,
    )
    prompt, trimmed, estimated = result
    assert isinstance(prompt, str) and prompt
    assert trimmed is False
    assert estimated > 0


def test_chat_payload_rejects_when_minimum_exceeds_budget() -> None:
    df = pd.DataFrame({"sessions": [1, 2, 3]})
    context = build_deterministic_context(df, _ctx(), AppSession())
    with pytest.raises(ContextTooLargeError):
        build_chat_prompt_payload(
            user_question="What is happening?",
            history=[],
            context=context,
            max_context_tokens=50,  # absurdly small — deterministic minimum exceeds
            reserved_output_tokens=10,
            max_context_chars=96_000,
        )


# ── build_summary_prompt_payload (Task 8) ──────────────────────────────────
def test_summary_payload_ok() -> None:
    df = pd.DataFrame({"date": ["2026-01-01"], "sessions": [1]})
    context = build_deterministic_context(df, _ctx(), AppSession())
    prompt, trimmed, estimated = build_summary_prompt_payload(
        context=context,
        max_context_tokens=24_000,
        reserved_output_tokens=4_096,
    )
    assert prompt and trimmed is False and estimated > 0


# ── classify_provider_error (C2 — typed codes, never raw text) ─────────────
def test_classify_provider_error_typed_codes() -> None:
    assert isinstance(classify_provider_error(ContextTooLargeError(100)), TypedAiError)
    assert classify_provider_error(ContextTooLargeError(100)).code == "context_too_large"
    assert classify_provider_error(TimeoutError("timed out")).code == "timeout"
    assert classify_provider_error(TimeoutError()).retryable is True

    rate = classify_provider_error(RuntimeError("429 RESOURCE_EXHAUSTED"))
    assert rate.code == "rate_limited"
    assert rate.retryable is True

    quota = classify_provider_error(RuntimeError("quota exceeded"))
    assert quota.code == "quota_exhausted"
    assert quota.retryable is False

    auth = classify_provider_error(RuntimeError("API key invalid"))
    assert auth.code == "provider_unavailable"

    generic = classify_provider_error(RuntimeError("boom"))
    assert generic.code == "provider_unavailable"
    assert generic.retryable is True


def test_classify_provider_error_never_leaks_message() -> None:
    # The message in str(exc) must never appear in the public payload.
    err = classify_provider_error(RuntimeError("SUPER-SECRET-INTERNAL"))
    assert "SUPER-SECRET-INTERNAL" not in err.public_payload()["message"]


# ── ledger_sink (D5/D13 — counts only) ─────────────────────────────────────
def test_ledger_sink_counts_and_partitions() -> None:
    from utils.gemini_client import UsageEvent

    session = AppSession()
    sink = ledger_sink(session.usage_ledger)
    sink(
        UsageEvent(
            model="gemini-2.5-flash",
            request_type="chat",
            input_tokens=10,
            output_tokens=5,
            total_token_count=15,
            success=True,
        )
    )
    sink(
        UsageEvent(
            model="gemini-2.5-flash",
            request_type="chat",
            total_token_count=0,
            success=False,
            sanitized_error_class="RuntimeError",
        )
    )
    ledger = session.usage_ledger
    assert ledger.request_count == 2
    assert ledger.success_count == 1
    assert ledger.failure_count == 1
    assert ledger.input_tokens == 10
    assert ledger.by_request_type == {"chat": 2}
    assert ledger.by_model == {"gemini-2.5-flash": 2}
