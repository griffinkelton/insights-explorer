"""Phase 5 Drive routes (spec phase-5-ga4-drive.md Task 2 + Task 4).

Picker-first path (D1):

```
POST /api/v1/drive/picker-token  → JIT access token + app_id + request_id (no-store)
Google Picker (browser, memory-only token)
POST /api/v1/drive/download { request_id, file_id } → server download → ingest
```

Trust boundary (Task 2): only ``file_id`` carries metadata/download authority;
``request_id`` must match the active server/session picker request (stale or
duplicate → typed non-retryable error, one-shot consumed on success). The
browser never receives a refresh token, client secret, or connection record —
and the picker token is **never revoked on close** (revocation can invalidate
the underlying grant). Download-and-ingest only: no upload endpoints exist.
"""

from __future__ import annotations

import asyncio
import threading

import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.config import get_settings
from api.dependencies import (
    AppSession,
    enforce_same_origin_unsafe,
    get_or_create_session,
)
from api.schemas import (
    DriveDownloadRequest,
    DrivePickerTokenResponse,
    DriveStatusResponse,
    UploadResponse,
)
from api.services import drive_service
from api.services.dataset_service import (
    UploadError,
    clear_dataset_state,
    make_context,
    parse_uploaded_file,
)
from api.services.drive_service import (
    DRIVE_ERROR_STATUS,
    DriveImportError,
    build_drive_service,
    consume_picker_request,
    create_picker_request,
    download_drive_to_tempfile,
    get_fresh_access_token,
    validate_picker_request,
)
from api.services.ga4_service import Ga4ServiceError
from api.stores.dataset_store import datasets

router = APIRouter(prefix="/api/v1", tags=["drive"])


def _typed_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _drive_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DriveImportError):
        return _typed_error(
            DRIVE_ERROR_STATUS.get(exc.code, 502),
            exc.code,
            exc.message,
        )
    return _typed_error(502, "download_failed", "Could not download the file. Please try again.")


@router.get("/drive/status", response_model=DriveStatusResponse)
def drive_status(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> DriveStatusResponse:
    return DriveStatusResponse(configured=bool(session.drive_credentials))


@router.post("/drive/picker-token", response_model=DrivePickerTokenResponse)
def drive_picker_token(
    response: Response,
    request: Request,
    session: AppSession = Depends(get_or_create_session),
) -> DrivePickerTokenResponse:
    """Just-in-time Picker bootstrap — browser-memory-only token (Task 4)."""
    settings = get_settings()
    if not settings.drive_enabled:
        raise HTTPException(
            status_code=503,
            detail={"code": "drive_not_configured", "message": "Drive import is not configured."},
        )
    enforce_same_origin_unsafe(request)

    try:
        token, expires_at = get_fresh_access_token(session)
    except DriveImportError as exc:
        raise _drive_error(exc) from exc

    request_id = create_picker_request(session)

    # The token is a short-lived credential for the Picker iframe only — no
    # caching anywhere (backend or browser).
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return DrivePickerTokenResponse(
        access_token=token,
        expires_at=expires_at,
        app_id=settings.google_cloud_project_number,
        request_id=request_id,
    )


@router.post("/drive/download", response_model=UploadResponse, status_code=201)
async def drive_download(
    payload: DriveDownloadRequest,
    request: Request,
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> UploadResponse:
    """Server-authoritative Drive download → unified ingestion pipeline.

    Preserves the old dataset on every failure (replace only on success);
    deletes the temp artifact deterministically in ``finally``; aborts the
    worker thread on timeout or client disconnect (cancel event polled per
    chunk) so no temp file is ever orphaned.
    """
    settings = get_settings()
    if not settings.drive_enabled:
        raise HTTPException(
            status_code=503,
            detail={"code": "drive_not_configured", "message": "Drive import is not configured."},
        )
    if not session.drive_credentials:
        raise _typed_error(409, "drive_connection_required", "Connect Google Drive first.")
    enforce_same_origin_unsafe(request)  # unsafe POST — Origin must match (Task 4)

    try:
        validate_picker_request(session, payload.request_id)
        creds_dict = drive_service.decrypt_tokens(session.drive_credentials)
    except DriveImportError as exc:
        raise _drive_error(exc) from exc
    except Ga4ServiceError as exc:
        raise _typed_error(401, "drive_reconnect_required", exc.message) from exc

    service = build_drive_service(creds_dict)
    artifact = None
    cancel_event = threading.Event()
    try:
        # anyio 4.x run_sync does not forward kwargs — bind via lambda. The
        # whole-download timeout caps the worker thread (Task 2: timeouts);
        # the cancel event lets a timed-out/cancelled request abort the thread
        # at the next chunk so it self-cleans its temp file.
        artifact = await asyncio.wait_for(
            anyio.to_thread.run_sync(
                lambda: download_drive_to_tempfile(
                    service,
                    file_id=payload.file_id,
                    max_bytes=settings.max_ingest_bytes,
                    should_cancel=cancel_event.is_set,
                )
            ),
            timeout=settings.drive_download_timeout_seconds,
        )
        content = artifact.path.read_bytes()
        dataframe, warning = parse_uploaded_file(artifact.filename, content)
    except asyncio.TimeoutError:
        cancel_event.set()
        raise _typed_error(504, "drive_timeout", "The Drive download took too long.") from None
    except (DriveImportError, UploadError, ValueError) as exc:
        cancel_event.set()
        if isinstance(exc, DriveImportError):
            raise _drive_error(exc) from exc
        if isinstance(exc, UploadError):
            raise _typed_error(exc.status_code, "drive_parse_failed", exc.detail) from exc
        raise _typed_error(
            422, "drive_parse_failed", "Could not parse the downloaded file."
        ) from exc
    finally:
        cancel_event.set()  # abandoned threads abort + self-clean at next chunk
        if artifact is not None:
            artifact.path.unlink(missing_ok=True)

    # Success only: clear derived state, replace the dataset, consume the
    # one-shot picker request (a second selection can never replace it).
    clear_dataset_state(session)
    context = make_context(
        dataframe,
        source="drive",
        filename=artifact.filename,
        warnings=[warning] if warning else [],
    )
    stored = datasets.put(dataframe, context)
    session.dataset_id = stored.id
    consume_picker_request(session)
    return UploadResponse(dataset=context)
