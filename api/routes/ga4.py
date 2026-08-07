"""Phase 5 GA4 OAuth + pull routes (spec phase-5-ga4-drive.md Task 1 + Task 3).

Flow (parked F4 §8, production-real per owner guidance 2026-08-06):

```
Browser → POST /api/v1/ga4/connect
  → FastAPI creates state + PKCE verifier, stores a 10-min transaction
  → sets an HttpOnly transaction cookie binding this browser
  → returns the Google authorization URL (S256)
Google → GET /api/v1/ga4/callback
  → consumes the transaction exactly once (no replay)
  → verifies the transaction cookie (compare_digest)
  → exchanges the code server-side with the stored verifier
  → stores encrypted tokens on the session (server-side only)
  → rotates the app session ID
  → 303 → /auth/{ga4|drive}/callback?status=success
```

Callback status vocabulary (locked): ``success`` · ``cancelled`` ·
``error&reason=<code>`` with reason in ``invalid_state | token_exchange_failed |
scope_denied``. Protocol violations (missing/expired/replayed state,
transaction-cookie mismatch) are typed 400s; OAuth *outcomes* (denied, exchange
failure, success) are 303 redirects into the React callback route.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from api.config import get_settings
from api.dependencies import (
    AppSession,
    enforce_same_origin_unsafe,
    get_or_create_session,
    set_session_cookie,
)
from api.schemas import Ga4ConnectResponse, Ga4StatusResponse, OAuthConnectRequest, UploadResponse
from api.services import ga4_service
from api.services.dataset_service import clear_dataset_state, make_context
from api.services.ga4_service import (
    DRIVE_SCOPES,
    GA4_SCOPES,
    Ga4ServiceError,
    build_contract_metrics,
    build_ga4_client,
    decrypt_tokens,
    encrypt_tokens,
    exchange_code,
    new_transaction_id,
    pull_ga4_report,
    revoke_tokens,
    rows_to_dataframe,
    state_key,
)
from api.stores.dataset_store import datasets
from api.stores.oauth_store import oauth_transactions

router = APIRouter(prefix="/api/v1", tags=["ga4"])

OAUTH_TXN_COOKIE = "insights_oauth_txn"
OAUTH_TXN_TTL_SECONDS = 600


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _typed_error(
    status_code: int, code: str, message: str, retryable: bool = False
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "retryable": retryable},
    )


def _redirect_callback(
    frontend_url: str, return_path: str, status: str, reason: str | None = None
) -> RedirectResponse:
    url = f"{frontend_url}{return_path}?status={status}"
    if reason:
        url += f"&reason={reason}"
    return RedirectResponse(url=url, status_code=303)


@router.post("/ga4/connect", response_model=Ga4ConnectResponse)
def connect_ga4(
    response: Response,
    request: Request,
    payload: OAuthConnectRequest | None = None,
    session: AppSession = Depends(get_or_create_session),
) -> Ga4ConnectResponse:
    settings = get_settings()
    if not settings.ga4_enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ga4_not_configured",
                "message": "Google connections are not configured.",
            },
        )
    enforce_same_origin_unsafe(request)

    connection = (payload.connection if payload else "ga4") or "ga4"
    if connection not in ("ga4", "drive"):
        raise _typed_error(422, "invalid_connection", "connection must be 'ga4' or 'drive'.")

    scopes = GA4_SCOPES if connection == "ga4" else DRIVE_SCOPES
    return_path = "/auth/ga4/callback" if connection == "ga4" else "/auth/drive/callback"

    try:
        authorization_url, state, code_verifier = ga4_service.build_authorization_url(
            scopes=scopes,
            redirect_uri=settings.ga4_redirect_uri,
        )
    except Exception:
        raise _typed_error(
            503, "ga4_provider_unavailable", "Could not start Google sign-in."
        ) from None

    transaction_id = new_transaction_id()
    record = {
        "transaction_id": transaction_id,
        "code_verifier": code_verifier,
        "redirect_uri": settings.ga4_redirect_uri,
        "created_at": _utcnow().isoformat(),
        "return_path": return_path,
        "connection": connection,
    }
    written = oauth_transactions.put(state_key(state), record, ttl_seconds=OAUTH_TXN_TTL_SECONDS)
    if not written:
        raise _typed_error(500, "state_collision", "Could not start Google sign-in. Try again.")

    # HttpOnly transaction cookie binds this browser to the transaction —
    # never exposed to JavaScript (Task 1 rules).
    response.set_cookie(
        key=OAUTH_TXN_COOKIE,
        value=transaction_id,
        httponly=True,
        secure=False,  # True behind HTTPS (Phase 6 __Host- prefix)
        samesite="lax",
        max_age=OAUTH_TXN_TTL_SECONDS,
        path="/",
    )
    return Ga4ConnectResponse(authorization_url=authorization_url)


@router.get("/ga4/callback")
def ga4_callback(
    request: Request,
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: AppSession = Depends(get_or_create_session),
) -> RedirectResponse:
    settings = get_settings()
    frontend_url = settings.frontend_url

    # Provider outcome (user denied / provider error) → 303 with vocabulary.
    # Google usually echoes `state` even on error — peek (do NOT consume) the
    # transaction to route the denial to the right connection's callback page.
    if error:
        return_path = "/auth/ga4/callback"
        if state:
            record = oauth_transactions.peek(state_key(state))
            if record:
                return_path = record.get("return_path", return_path)
        if error == "access_denied":
            return _redirect_callback(frontend_url, return_path, "cancelled")
        return _redirect_callback(frontend_url, return_path, "error", "scope_denied")

    if not state:
        raise _typed_error(400, "invalid_state", "OAuth state is missing.")

    # One-time consumption — replay or expiry lands here (Task 6 test).
    record = oauth_transactions.get_and_delete(state_key(state))
    if record is None:
        raise _typed_error(
            400, "invalid_state", "OAuth state is invalid, expired, or already used."
        )

    transaction_cookie = request.cookies.get(OAUTH_TXN_COOKIE)
    if not secrets.compare_digest(transaction_cookie or "", record.get("transaction_id", "")):
        raise _typed_error(
            400, "transaction_mismatch", "OAuth transaction does not match this browser session."
        )

    if not code:
        raise _typed_error(400, "invalid_state", "OAuth authorization code is missing.")

    connection = record.get("connection", "ga4")
    scopes = GA4_SCOPES if connection == "ga4" else DRIVE_SCOPES
    try:
        creds_dict = exchange_code(
            code=code,
            redirect_uri=record["redirect_uri"],
            code_verifier=record["code_verifier"],
            scopes=scopes,
        )
    except Exception:
        return _redirect_callback(
            frontend_url, "/auth/ga4/callback", "error", "token_exchange_failed"
        )

    # Grant-scope verification (consent-state model): the returned token must
    # include the connection's required scope — a degraded/combined grant is
    # never silently stored as feature-level consent.
    required_scope = (
        "https://www.googleapis.com/auth/analytics.readonly"
        if connection == "ga4"
        else "https://www.googleapis.com/auth/drive.file"
    )
    granted = set(creds_dict.get("scopes") or [])
    if required_scope not in granted:
        return _redirect_callback(
            frontend_url, record.get("return_path", "/auth/ga4/callback"), "error", "scope_denied"
        )

    blob = encrypt_tokens(creds_dict)
    if connection == "drive":
        session.drive_credentials = blob
    else:
        session.ga4_credentials = blob

    # Rotate the app session ID after OAuth completes (Task 1 rule) — the
    # pre-auth anonymous session must not keep carrying the connection. The
    # cookies must go on the RETURNED RedirectResponse: FastAPI discards the
    # injected ``response`` object's cookies when the route returns a Response.
    old_session_id = getattr(request.state, "session_id", None)
    new_session_id, new_session = _rotate_session(old_session_id, session)
    redirect = _redirect_callback(
        frontend_url, record.get("return_path", "/auth/ga4/callback"), "success"
    )
    set_session_cookie(redirect, new_session_id)
    redirect.delete_cookie(key=OAUTH_TXN_COOKIE, path="/")
    return redirect


def _rotate_session(old_session_id: str | None, session: AppSession) -> tuple[str, AppSession]:
    """Create a fresh session carrying the OAuth connection + active dataset.

    Provider tokens are stored on the *new* session; the old anonymous session
    is deleted. Dataset-derived state carries over so an existing upload or a
    GA4 pull is not lost mid-flow. The AI lock is intentionally NOT copied —
    the fresh session owns a new lock.
    """
    from api.stores.session_store import sessions

    new_session_id, new_session = sessions.create()
    new_session.dataset_id = session.dataset_id
    new_session.metadata = dict(session.metadata)
    new_session.usage_ledger = session.usage_ledger
    new_session.ga4_credentials = session.ga4_credentials
    new_session.drive_credentials = session.drive_credentials
    if old_session_id:
        sessions.delete(old_session_id)
    return new_session_id, new_session


@router.get("/ga4/status", response_model=Ga4StatusResponse)
def ga4_status(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> Ga4StatusResponse:
    return Ga4StatusResponse(connected=bool(session.ga4_credentials))


@router.post("/ga4/disconnect")
def ga4_disconnect(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> dict[str, str]:
    if session.ga4_credentials:
        try:
            revoke_tokens(decrypt_tokens(session.ga4_credentials))
        except Ga4ServiceError:
            pass  # already invalid — clearing the record is the meaningful action
    session.ga4_credentials = None
    return {"status": "disconnected"}


@router.post("/ga4/pull", response_model=UploadResponse)
async def pull_ga4(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> UploadResponse:
    """First pull — locked D3 fallback report → contract-provenanced DatasetContext.

    No client-supplied metrics, dimensions, or date ranges (Task 3: the
    browser payload is just ``POST /api/v1/ga4/pull``).
    """
    settings = get_settings()
    if not settings.ga4_enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ga4_not_configured",
                "message": "Google connections are not configured.",
            },
        )
    if not session.ga4_credentials:
        raise _typed_error(409, "ga4_connection_required", "Connect Google Analytics first.")
    property_id = settings.ga4_property_id
    if not property_id:
        raise _typed_error(404, "ga4_property_unavailable", "No GA4 property is configured.")

    try:
        creds_dict = decrypt_tokens(session.ga4_credentials)
        client = build_ga4_client(creds_dict)
        rows, provenance, _last_quota = await pull_ga4_report(client, property_id=property_id)
    except Exception as exc:
        # ``classify_ga4_error`` maps Ga4ServiceError + raw provider exceptions
        # (ResourceExhausted/ServiceUnavailable/DeadlineExceeded/...) to the
        # locked taxonomy (Task 3).
        classified = ga4_service.classify_ga4_error(exc)
        raise _typed_error(
            classified.status_code,
            classified.code,
            classified.message,
            retryable=classified.retryable,
        ) from exc

    dataframe = rows_to_dataframe(rows)
    if dataframe.empty:
        raise _typed_error(
            422, "ga4_empty_report", "The GA4 property returned no rows for the report period."
        )

    clear_dataset_state(session)
    context = make_context(
        dataframe,
        source="ga4",
        filename=f"ga4-{property_id}.csv",
    )
    context.metrics = build_contract_metrics()
    context.provenance = provenance

    stored = datasets.put(dataframe, context)
    session.dataset_id = stored.id
    return UploadResponse(dataset=context)
