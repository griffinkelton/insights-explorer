"""Session store: protocol + thread-safe in-memory implementation.

Expiry policy (approved — master-plan §5, data-retention-policy §5):
idle 2 h since ``last_accessed_at``, absolute 12 h since ``created_at``,
effective lifetime is whichever happens first. Stores stay dumb — expiry is
enforced by ``api/dependencies.py``, which deletes the expired session and
its dataset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Protocol
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AppSession:
    dataset_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)  # absolute-expiry anchor
    last_accessed_at: datetime = field(default_factory=utcnow)  # idle-expiry anchor
    ga4_credentials: dict | None = None
    oauth_state: str | None = None
    code_verifier: str | None = None  # PKCE — used Phase 5
    metadata: dict = field(default_factory=dict)


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


sessions = InMemorySessionStore()
