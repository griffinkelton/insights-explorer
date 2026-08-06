"""Session store: protocol + thread-safe in-memory implementation.

Expiry policy (approved — master-plan §5, data-retention-policy §5):
idle 2 h since ``last_accessed_at``, absolute 12 h since ``created_at``,
effective lifetime is whichever happens first. Stores stay dumb — expiry is
enforced by ``api/dependencies.py``, which deletes the expired session and
its dataset.

Phase 3 (spec Task 3): per-session AI usage lives on ``AppSession.usage_ledger``
(counts only — no cap in Phase 3, D13) and AI requests are serialized per
session via ``ai_lock`` (C6 — bounded queue-wait, settled Option A).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Protocol
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class UsageLedger:
    """Per-session, server-owned Gemini usage (Phase 3, spec Task 3).

    Reset by Clear Data; never contains prompt content or raw rows. Records
    counts only (D13) — budgets stay a §17 hosted-beta gate. Safe diagnostic
    dimensions are set by ``ai_service`` at prompt-assembly time, never
    derived from prompt text.
    """

    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    thought_tokens: int = 0
    cached_tokens: int = 0
    tool_tokens: int = 0
    # Safe diagnostics (ai_service):
    estimated_prompt_tokens: int = 0
    context_trimmed: int = 0
    identifiers_removed: int = 0
    # Latency observability — safe cumulative aggregates (no per-request retention):
    ttft_cum_ms: int = 0  # sum of time-to-first-token across requests
    ttlt_cum_ms: int = 0  # sum of time-to-last-token across requests
    request_started_at: datetime | None = None
    provider_first_token_at: datetime | None = None
    provider_completed_at: datetime | None = None
    by_request_type: dict[str, int] = field(default_factory=dict)
    by_model: dict[str, int] = field(default_factory=dict)


@dataclass
class AppSession:
    dataset_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)  # absolute-expiry anchor
    last_accessed_at: datetime = field(default_factory=utcnow)  # idle-expiry anchor
    ga4_credentials: dict | None = None
    oauth_state: str | None = None
    code_verifier: str | None = None  # PKCE — used Phase 5
    metadata: dict = field(default_factory=dict)
    usage_ledger: UsageLedger = field(default_factory=UsageLedger)  # Phase 3 (D5)
    ai_lock: asyncio.Lock = field(default_factory=asyncio.Lock)  # Phase 3 (C6)


class SessionStore(Protocol):
    """Stores stay dumb — expiry is enforced by api/dependencies.py,
    which deletes the expired session and its dataset."""

    def create(self) -> tuple[str, AppSession]: ...
    def get(self, session_id: str) -> AppSession | None: ...
    def delete(self, session_id: str) -> None: ...


class InMemorySessionStore:
    """Local dev implementation — replace with a shared ephemeral store
    (Redis/Valkey) before the hosted beta; interfaces keep routes unchanged."""

    def __init__(self) -> None:
        self._sessions: dict[str, AppSession] = {}
        self._lock = RLock()

    def create(self) -> tuple[str, AppSession]:
        session_id = uuid4().hex
        session = AppSession()
        with self._lock:
            self._sessions[session_id] = session
        return session_id, session

    def get(self, session_id: str) -> AppSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    # ── Public test-only helpers (review fix 2026-08-06) — contract tests must
    # not reach into ``_sessions`` private dicts; stable surface for a future
    # shared-store swap. ────────────────────────────────────────────────────
    def clear_for_test(self) -> None:
        """Empty the store. Test-only; not part of the runtime contract."""
        with self._lock:
            self._sessions.clear()

    def count_for_test(self) -> int:
        """Number of live sessions. Test-only; not part of the runtime contract."""
        with self._lock:
            return len(self._sessions)


sessions = InMemorySessionStore()
