"""Ephemeral OAuth transaction store (Phase 5, spec phase-5-ga4-drive.md Task 1).

In-memory, single-process, TTL-bounded (10-minute), **one-time consumption**
(get-and-delete) — the Phase 6 Redis swap keeps the same interface (GETDEL /
Lua get-and-delete) so routes never change. Records are keyed by
``ie:oauth:state:<sha256(state)>`` and carry ``{ transaction_id, code_verifier,
redirect_uri, created_at, return_path, connection }``.

The browser is bound to a transaction via an HttpOnly cookie; the store itself
never holds client data beyond the ephemeral PKCE/state record.
"""

from __future__ import annotations

import time
from threading import RLock

OAUTH_STATE_TTL_SECONDS = 600  # 10-minute TTL (spec Task 1: "State TTL ≈ 10 minutes")


class OAuthTransactionStore:
    """TTL-bounded, NX-write, atomic get-and-delete record store.

    Local-first implementation (master-plan principle 9): fine for single
    process; replaced by Redis in Phase 6 without changing the interface.
    """

    def __init__(self) -> None:
        self._records: dict[str, dict] = {}
        self._lock = RLock()

    def put(self, key: str, record: dict, ttl_seconds: int = OAUTH_STATE_TTL_SECONDS) -> bool:
        """NX semantics — never overwrite an existing (live) record.

        Returns True when written, False when the key is already present.
        """
        with self._lock:
            if key in self._records:
                return False
            stored = dict(record)
            stored["expires_at"] = time.monotonic() + ttl_seconds
            self._records[key] = stored
            return True

    def get_and_delete(self, key: str) -> dict | None:
        """Atomic one-time consumption — equivalent to Redis ``GETDEL``.

        Returns the record, or None when missing **or expired** (expired keys
        are dropped lazily here; the TTL is the primary cleanup system).
        """
        with self._lock:
            record = self._records.get(key)
            if record is None:
                return None
            del self._records[key]
            if record.get("expires_at", 0) < time.monotonic():
                return None
            return record

    def peek(self, key: str) -> dict | None:
        """Non-consuming read (no expiry pruning) — used on the OAuth error path
        to resolve the connection's ``return_path`` without burning the state.
        """
        with self._lock:
            record = self._records.get(key)
            return dict(record) if record is not None else None

    # ── Public test-only helpers (same pattern as session_store) ──────────
    def clear_for_test(self) -> None:
        with self._lock:
            self._records.clear()

    def count_for_test(self) -> int:
        with self._lock:
            return len(self._records)


oauth_transactions = OAuthTransactionStore()
