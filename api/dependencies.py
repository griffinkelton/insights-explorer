"""FastAPI dependencies: signed-cookie session + dataset guard.

Cookie → session (spec §7). The cookie value is **signed with itsdangerous**
(so ``API_SESSION_SECRET`` is required and used — never dead config), and
expiry is **enforced server-side** (``min(2 h idle, 12 h absolute)``, session
store §policy; ``__Host-`` prefix in production). On expiry the session and
its dataset are deleted — old dataset state is never silently preserved.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Cookie, Depends, HTTPException, Request, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from api.config import get_settings
from api.stores.dataset_store import datasets
from api.stores.session_store import AppSession, sessions

SESSION_COOKIE = "insights_session"
SESSION_IDLE_SECONDS = 2 * 60 * 60  # 2 h idle (approved session policy)
SESSION_ABSOLUTE_SECONDS = 12 * 60 * 60  # 12 h absolute (approved session policy)
SESSION_SALT = "insights-session"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_serializer = URLSafeTimedSerializer(get_settings().api_session_secret, salt=SESSION_SALT)


def _sign_session_id(session_id: str) -> str:
    """Sign the session id so clients cannot forge or tamper with it."""
    return _serializer.dumps(session_id)


def _verify_session_id(cookie_value: str) -> str | None:
    """Return the session id, or None if the cookie is tampered/expired."""
    try:
        return _serializer.loads(cookie_value, max_age=SESSION_ABSOLUTE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None


def _is_expired(session: AppSession) -> bool:
    now = _utcnow()
    idle_expired = (now - session.last_accessed_at).total_seconds() > SESSION_IDLE_SECONDS
    absolute_expired = (now - session.created_at).total_seconds() > SESSION_ABSOLUTE_SECONDS
    return idle_expired or absolute_expired


def _discard_session(session_id: str, session: AppSession) -> None:
    """Delete an expired session and its dataset — never preserve old state."""
    if session.dataset_id:
        datasets.remove(session.dataset_id)
    sessions.delete(session_id)


def set_session_cookie(response: Response, session_id: str) -> None:
    """Set the signed session cookie on a response (Phase 5 session rotation)."""
    response.set_cookie(
        key=SESSION_COOKIE,
        value=_sign_session_id(session_id),
        httponly=True,
        secure=False,  # True behind HTTPS; Phase 6 adds the __Host- prefix
        samesite="lax",
        max_age=SESSION_ABSOLUTE_SECONDS,
        path="/",
    )


def get_or_create_session(
    request: Request,
    response: Response,
    insights_session: str | None = Cookie(default=None),
) -> AppSession:
    session_id = _verify_session_id(insights_session) if insights_session else None
    session = sessions.get(session_id) if session_id else None

    if session:
        if _is_expired(session):
            _discard_session(session_id, session)
        else:
            session.last_accessed_at = _utcnow()  # refresh idle anchor
            request.state.session_id = session_id  # Phase 5 — session rotation
            return session

    session_id, session = sessions.create()
    request.state.session_id = session_id  # Phase 5 — session rotation
    set_session_cookie(response, session_id)
    # FastAPI discards dependency-set cookies when the endpoint raises an
    # HTTPException — replay it in api/main.py's exception handler so the
    # session cookie survives 409/410 responses too.
    request.state.pending_session_cookie = response.headers.get("set-cookie")
    return session


def enforce_same_origin_unsafe(request: Request) -> None:
    """CSRF guard for unsafe methods (POST/PUT/PATCH/DELETE) — Phase 5 Task 4.

    Browser ``Origin`` must match either an allowlisted CORS origin (dev Vite
    origin) **or the request's own Host** (same-origin production deploy, where
    ``API_CORS_ORIGINS=""`` leaves the CORS allowlist empty but the browser
    still sends an Origin header on POST). Non-browser clients (curl, contract
    tests) carry no Origin and are not blocked.
    """
    from urllib.parse import urlparse

    settings = get_settings()
    origin = request.headers.get("origin")
    if not origin:
        return
    allowed = {o.rstrip("/") for o in settings.cors_origins}
    if origin.rstrip("/") in allowed:
        return
    # Same-origin deploy: compare the Origin authority against the Host header.
    host = request.headers.get("host", "")
    origin_netloc = urlparse(origin).netloc
    if host and origin_netloc and host == origin_netloc:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "csrf_origin_rejected", "message": "Request origin is not allowed."},
    )


def require_dataset(session: AppSession = Depends(get_or_create_session)) -> AppSession:
    """Dependency for routes that need an active dataset (Phase 3 AI routes).

    Resolves the session via ``get_or_create_session`` (sub-dependency) so the
    signed cookie is created/refreshed on every request, then enforces the
    dataset guard — 409 when none is active.
    """
    if not session or not session.dataset_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active dataset. Upload a file or connect GA4 first.",
        )
    return session
