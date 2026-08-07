"""Phase 3 AI service (spec phase-3-ai-analysis.md Task 7).

Boundary: ``dataset_service`` owns ingestion/context/Clear Data; ``ai_service``
owns AI-specific concerns — deterministic-context assembly, identifier
scrubbing (retention-policy §8), metric-status caveats (measurement
contract), token budgeting (D11), usage-ledger sink wiring (D5/D13), and
provider-error classification (C2). Gemini never calculates — deterministic
utils assemble authoritative context; Gemini explains and prioritizes.

Privacy boundary: nothing here retains prompt text, sample rows, user
messages, or model output — the ledger stores counts and safe diagnostics
only (estimated_prompt_tokens, context_trimmed, identifiers_removed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from utils.data_loader import get_dataset_stats, smart_sample
from utils.gemini_client import UsageEvent, UsageSink, count_tokens
from utils.prompt_templates import build_chat_prompt, build_summary_prompt

from api.schemas import ChatMessage, DatasetContext, DatasetWarning
from api.services.quality_service import build_quality_report
from api.stores.session_store import AppSession, UsageLedger

# ── Identifier scrub (heuristic — NOT a complete PII detector, D4) ─────────
IDENTIFIER_PATTERNS = (
    "email",
    "e-mail",
    "user_id",
    "userid",
    "name",
    "first_name",
    "last_name",
    "phone",
    "mobile",
    "address",
    "zip",
    "ip",
    "device_id",
    "session_id",
    "uid",
    "ssn",
    "dob",
    "birth",
)


def scrub_identifiers(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return (scrubbed_df, removed_columns).

    Drop identifier-like columns from prompt-bound samples (retention-policy
    §8). Best-effort name-pattern matching — a column that fails a pattern
    test is NOT automatically safe, and unknown columns are NOT automatically
    removed. Business-entity columns (customer/account/member/...) and a
    generic ``id`` are deliberately excluded to avoid over-removal.
    """
    removed = [c for c in df.columns if any(p in str(c).lower() for p in IDENTIFIER_PATTERNS)]
    return (df.drop(columns=removed) if removed else df), removed


# ── Layer-1 request validation (D12) ───────────────────────────────────────
def validate_chat_messages(messages: list[ChatMessage]) -> None:
    """Layer-1 chat request validation (D12).

    Roles (user|assistant), per-message length (≤4,000 chars) and message
    count (≤20) are enforced by the schema; this adds the 24,000 total-character
    ceiling that spans the whole request. Raises ValueError → route maps to 422
    with a static message — never echoes user content.
    """
    total = sum(len(m.content) for m in messages)
    if total > 24_000:
        raise ValueError("Chat history exceeds the 24,000-character request limit.")


# ── Metric-status caveats (canonical: ga4-measurement-contract) ────────────
def metric_status_caveats(ctx: DatasetContext) -> list[str]:
    """Provisional → directional-only; unavailable → never numeric evidence."""
    caveats: list[str] = []
    for m in ctx.metrics:
        status = m.get("status", "validated")
        ident = m.get("id", m.get("name", "?"))
        if status == "provisional":
            caveats.append(f"{ident} is provisional — directional only")
        elif status == "unavailable":
            caveats.append(f"{ident} is unavailable — blocked capability only")
    return caveats


# ── Deterministic context ───────────────────────────────────────────────────
@dataclass(frozen=True)
class DeterministicContext:
    prompt_df: pd.DataFrame  # identifier-scrubbed sample — never the full raw frame
    stats: dict[str, Any]
    quality: Any  # QualityReport | None
    metric_caveats: list[str]
    removed_columns: list[str] = field(default_factory=list)


def build_deterministic_context(
    df: pd.DataFrame,
    ctx: DatasetContext,
    session: AppSession,
) -> DeterministicContext:
    """Assemble the deterministic context for AI prompts (spec Task 7).

    Reuses Phase 1 services (``get_dataset_stats``, ``build_quality_report``),
    scrubs identifiers from a small sample (retention-policy §8), and attaches
    the ``identifiers_removed_for_ai`` warning to the stored context once
    (deduplicated). ``session`` is reserved for Phase 4/5 filter/metric state.
    """
    stats = get_dataset_stats(df)
    quality = build_quality_report(df)
    scrubbed, removed = scrub_identifiers(smart_sample(df, max_rows=5))
    caveats = metric_status_caveats(ctx)
    if removed:
        warning = DatasetWarning(
            code="identifiers_removed_for_ai",
            message="Potential identifier columns were removed before AI analysis.",
            removed_columns=removed,
        )
        if not any(w.code == warning.code for w in ctx.warnings):
            ctx.warnings.append(warning)
    return DeterministicContext(scrubbed, stats, quality, caveats, removed)


# ── Token budgeting (D11 — two-stage guard) ────────────────────────────────
class ContextTooLargeError(Exception):
    """Deterministic minimum context exceeds the token budget (typed, C2)."""

    def __init__(self, budget: int) -> None:
        super().__init__("context_too_large")
        self.budget = budget


def estimate_tokens(text: str) -> int:
    """Cheap local estimate (chars ÷ 4) — model-approximate, never exact."""
    return max(1, len(text) // 4)


def _trim_history(history: list[dict], max_chars: int) -> list[dict]:
    """Token-budgeted sliding window — newest → oldest until the char ceiling.

    Preserves the newest user message (already outside ``history`` at the call
    site); drops oldest assistant turns before older user turns; never trims
    deterministic caveats/provenance (they live in the fixed context).
    """
    total = 0
    selected: list[dict] = []
    for msg in reversed(history):
        size = len(msg["content"])
        if selected and total + size > max_chars:
            continue
        selected.append(msg)
        total += size
    return list(reversed(selected))


def build_chat_prompt_payload(
    *,
    user_question: str,
    history: list[dict],
    context: DeterministicContext,
    max_context_tokens: int,
    reserved_output_tokens: int,
    max_context_chars: int,
    model: str = "gemini-2.5-flash",
) -> tuple[str, bool, int]:
    """Assemble + budget the chat prompt. Returns (prompt, trimmed, estimated).

    3-branch flow (D11): estimate < 80% → stream now · 80–100% → exact
    ``countTokens`` preflight · over budget → trim (drop history first), then
    reject with ``ContextTooLargeError`` if the minimum compliant context
    still exceeds the budget.
    """
    budget = max_context_tokens - reserved_output_tokens
    history = _trim_history(history, max_context_chars)

    def _build(hist: list[dict]) -> str:
        return build_chat_prompt(
            user_question=user_question,
            df=context.prompt_df,
            stats=context.stats,
            conversation_history=hist,
        )

    prompt = _build(history)
    estimated = estimate_tokens(prompt)
    trimmed = False

    if estimated >= int(budget * 0.8) and estimated < budget:
        # Near-limit band: exact countTokens preflight (free but separately
        # rate-limited — D11). Degrades to the local estimate on failure.
        try:
            exact = count_tokens(prompt, model=model)
        except Exception:
            exact = estimated
        if exact > budget:
            trimmed = True
            prompt = _build([])  # drop history first — deterministic trim order
            estimated = estimate_tokens(prompt)

    if estimated > budget:
        trimmed = True
        prompt = _build([])
        estimated = estimate_tokens(prompt)

    if estimated > budget:
        raise ContextTooLargeError(budget)

    return prompt, trimmed, estimated


def build_summary_prompt_payload(
    *,
    context: DeterministicContext,
    max_context_tokens: int,
    reserved_output_tokens: int,
) -> tuple[str, bool, int]:
    """Assemble + budget the summary prompt (non-streaming, spec Task 8)."""
    budget = max_context_tokens - reserved_output_tokens
    prompt = build_summary_prompt(
        context.prompt_df,
        context.stats,
        quality_report=context.quality,
    )
    estimated = estimate_tokens(prompt)
    if estimated > budget:
        raise ContextTooLargeError(budget)
    return prompt, False, estimated


# ── Usage-ledger sink (D5/D13) ─────────────────────────────────────────────
def accumulate_latency(ledger: UsageLedger) -> None:
    """Add the last request's TTFT/TTLT to the ledger's safe cumulative sums.

    Shared by the chat (SSE) and analysis (summary) routes so the two paths
    cannot drift. Observability only — no per-request retention (D13).
    """
    if ledger.request_started_at and ledger.provider_first_token_at:
        ledger.ttft_cum_ms += int(
            (ledger.provider_first_token_at - ledger.request_started_at).total_seconds() * 1000
        )
    if ledger.request_started_at and ledger.provider_completed_at:
        ledger.ttlt_cum_ms += int(
            (ledger.provider_completed_at - ledger.request_started_at).total_seconds() * 1000
        )


def ledger_sink(ledger: UsageLedger) -> UsageSink:
    """Bind Phase 2 ``UsageEvent`` emission to the per-session ledger.

    All mutation happens inside the per-session ``ai_lock`` critical section
    (C6) — single-writer, deterministic counts. Counts only (D13).
    """

    def sink(event: UsageEvent) -> None:
        ledger.request_count += 1
        ledger.input_tokens += event.input_tokens
        ledger.output_tokens += event.output_tokens
        ledger.thought_tokens += event.thoughts_token_count
        ledger.cached_tokens += event.cached_token_count
        ledger.tool_tokens += event.tool_use_token_count
        ledger.total_tokens += event.total_token_count
        if event.success:
            ledger.success_count += 1
        else:
            ledger.failure_count += 1
        ledger.by_request_type[event.request_type] = (
            ledger.by_request_type.get(event.request_type, 0) + 1
        )
        ledger.by_model[event.model] = ledger.by_model.get(event.model, 0) + 1

    return sink


# ── Provider-error classification (C2 — never raw exception text) ──────────
@dataclass(frozen=True)
class TypedAiError:
    code: str
    message: str
    retryable: bool = False
    retry_after_seconds: int | None = None

    def public_payload(self) -> dict:
        """SSE wire shape (spec Task 6): type/code/retryable/message always;
        retry_after_seconds only when known. Never includes raw exception text."""
        payload: dict = {
            "type": "error",
            "code": self.code,
            "retryable": self.retryable,
            "message": self.message,
        }
        if self.retry_after_seconds is not None:
            payload["retry_after_seconds"] = self.retry_after_seconds
        return payload


def classify_provider_error(exc: Exception) -> TypedAiError:
    """Map provider/runtime exceptions to approved code/message pairs.

    Never includes raw exception text, prompt content, rows, or keys (C2).
    ``error_class`` (for the ledger) is the exception type name.
    """
    if isinstance(exc, ContextTooLargeError):
        return TypedAiError(
            code="context_too_large",
            message="The analysis context is too large. Narrow filters or reduce the dataset scope.",
        )
    if isinstance(exc, TimeoutError):
        return TypedAiError(
            code="timeout",
            message="AI request timed out. Try again shortly.",
            retryable=True,
        )
    msg = str(exc).lower()
    if "429" in str(exc) or "rate" in msg:
        return TypedAiError(
            code="rate_limited",
            message="AI capacity is temporarily limited. Try again shortly.",
            retryable=True,
        )
    if "quota" in msg or "resource_exhausted" in msg:
        return TypedAiError(
            code="quota_exhausted",
            message="AI quota is exhausted for this project. Try again later or use a configured paid deployment.",
        )
    if "api key" in msg or "unauthorized" in msg or "permission" in msg:
        return TypedAiError(
            code="provider_unavailable",
            message="AI service authentication failed. Check the configured API key.",
        )
    return TypedAiError(
        code="provider_unavailable",
        message="AI service is temporarily unavailable. Try again shortly.",
        retryable=True,
    )


# Re-exported for routes/tests convenience (keeps one error home).
__all__ = [
    "ContextTooLargeError",
    "DeterministicContext",
    "TypedAiError",
    "accumulate_latency",
    "build_chat_prompt_payload",
    "build_deterministic_context",
    "build_summary_prompt_payload",
    "classify_provider_error",
    "estimate_tokens",
    "ledger_sink",
    "metric_status_caveats",
    "scrub_identifiers",
    "validate_chat_messages",
]
