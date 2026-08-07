"""Phase 5 Drive service (spec phase-5-ga4-drive.md Task 2 + Task 4).

Ports ``utils/drive_client.py::download_drive_file`` **behavior** (server-side
trust boundary) with the Task 0/2 refinements locked for the migration API:

- ``file_id`` is the ONLY authority input — client filename/MIME/size ignored.
- Server re-fetches metadata (``trashed``, ``capabilities.canDownload``).
- MIME/suffix allowlist enforced server-side; Google-native → typed
  ``workspace_export_required`` (no automatic export in Phase 5).
- **Declared + actual-byte** size enforcement against ``MAX_INGEST_BYTES``.
- Disk-backed ``NamedTemporaryFile`` (256 KiB chunks) — raw content never
  occupies process RAM before pandas parses.
- **No Drive uploads in Phase 5** — download-and-ingest only.

``request_id`` binds the selection to the active server/session picker request
(one at a time; stale/duplicate → typed non-retryable error; consumed on
successful download so a second selection can never replace the active dataset).
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from api.services.ga4_service import (
    Ga4ServiceError,
    credentials_from_dict,
    decrypt_tokens,
    get_valid_access_token,
)

ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}
GOOGLE_WORKSPACE_MIME_PREFIX = "application/vnd.google-apps."
DOWNLOAD_CHUNK_BYTES = 256 * 1024  # 256 KiB chunks (Task 2)
PICKER_REQUEST_TTL_SECONDS = 600  # 10-minute picker request lifetime

# Drive error taxonomy → HTTP status (typed; Task 2).
DRIVE_ERROR_STATUS = {
    "unsupported_type": 415,
    "too_large": 413,
    "empty_file": 400,
    "not_found": 404,
    "access_denied": 403,
    "download_failed": 502,
    "file_not_available": 410,
    "download_not_allowed": 403,
    "workspace_export_required": 422,
    "stale_picker_request": 409,
    "drive_connection_required": 409,
    "drive_reconnect_required": 401,
}


class DriveImportError(Exception):
    """Public, typed Drive-import failure — the UI/tests branch on ``.code``.

    Never attaches raw Google error payloads, file IDs, or request URLs.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DriveDownloadArtifact:
    path: Path
    filename: str
    size_bytes: int


def sanitize_drive_filename(name: str) -> str:
    """Basename only — never trust a raw Drive/client name for paths."""
    return Path(name or "import").name or "import"


def _classify_drive_http_error(exc: HttpError) -> DriveImportError:
    """Map Drive API HttpErrors to fixed public codes (never raw payloads)."""
    status = getattr(exc.resp, "status", None)
    if status == 404:
        return DriveImportError("not_found", "File not found or access denied.")
    if status == 403:
        return DriveImportError(
            "access_denied",
            "Access denied. Reconnect Google Drive and try again.",
        )
    return DriveImportError("download_failed", "Could not download the file. Please try again.")


def download_drive_to_tempfile(
    drive_service,
    *,
    file_id: str,
    max_bytes: int,
    should_cancel=None,
) -> DriveDownloadArtifact:
    """Server-authoritative metadata + bounded disk-backed download (Task 2).

    ``should_cancel`` (optional zero-arg callable) is polled every chunk so a
    cancelled/abandoned request aborts the worker thread promptly and the
    temp artifact self-cleans — no orphaned client data after a client
    disconnect or timeout.
    """
    try:
        metadata = (
            drive_service.files()
            .get(
                fileId=file_id,
                fields="id,name,mimeType,size,md5Checksum,trashed,capabilities(canDownload)",
            )
            .execute()
        )
    except HttpError as exc:
        raise _classify_drive_http_error(exc) from exc

    if metadata.get("trashed"):
        raise DriveImportError(
            "file_not_available", "The selected Drive file is no longer available."
        )
    if not metadata.get("capabilities", {}).get("canDownload"):
        raise DriveImportError(
            "download_not_allowed", "The selected Drive file cannot be downloaded."
        )

    mime_type = metadata.get("mimeType", "")
    if mime_type.startswith(GOOGLE_WORKSPACE_MIME_PREFIX):
        # No automatic Sheets/Docs export in Phase 5 — a later export contract
        # (allowlisted export MIME, row/size behavior, typed errors) governs it.
        raise DriveImportError(
            "workspace_export_required",
            "This Google Workspace file requires an approved export format.",
        )
    if mime_type not in ALLOWED_MIME_TYPES:
        raise DriveImportError("unsupported_type", "Only CSV and Excel files can be imported.")

    filename = sanitize_drive_filename(metadata.get("name", "import"))
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise DriveImportError("unsupported_type", "Only CSV and Excel files can be imported.")

    # Declared-size preflight (fast path; never the only control).
    declared_size = metadata.get("size")
    if declared_size is not None and int(declared_size) > max_bytes:
        raise DriveImportError(
            "too_large", "The selected Drive file exceeds the import size limit."
        )

    temp = NamedTemporaryFile(
        mode="w+b",
        suffix=suffix,
        prefix="insights-drive-",
        delete=False,
    )
    temp_path = Path(temp.name)
    bytes_written = 0
    try:
        request = drive_service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(temp, request, chunksize=DOWNLOAD_CHUNK_BYTES)
        done = False
        while not done:
            if should_cancel is not None and should_cancel():
                raise DriveImportError("download_failed", "The download was cancelled.")
            _, done = downloader.next_chunk()
            # Actual-byte counter — covers absent/untrusted metadata and any
            # future export path; abort immediately at the hard limit.
            bytes_written = temp.tell()
            if bytes_written > max_bytes:
                raise DriveImportError(
                    "too_large", "The selected Drive file exceeds the import size limit."
                )
        temp.flush()
        if bytes_written == 0:
            raise DriveImportError("empty_file", "The selected Drive file is empty.")
        return DriveDownloadArtifact(path=temp_path, filename=filename, size_bytes=bytes_written)
    except Exception:
        temp.close()
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        if not temp.closed:
            temp.close()


def build_drive_service(creds_dict: dict):
    """Build an authorized Drive v3 client (synchronous — worker-thread bound)."""
    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=credentials_from_dict(creds_dict))


def get_fresh_access_token(session) -> tuple[str, str | None]:
    """Return (token, expires_at) for the session's Drive connection.

    Raises typed errors for a missing or reconnect-required connection.
    """
    if not session.drive_credentials:
        raise DriveImportError("drive_connection_required", "Connect Google Drive first.")
    try:
        creds_dict = decrypt_tokens(session.drive_credentials)
        token, expires_at = get_valid_access_token(creds_dict)
    except Ga4ServiceError as exc:
        raise DriveImportError("drive_reconnect_required", exc.message) from exc
    if not token:
        raise DriveImportError("drive_reconnect_required", "Reconnect Google Drive.")
    return token, expires_at


# ── Picker request one-shot binding (Task 4) ───────────────────────────────
def create_picker_request(session) -> str:
    """Create the single active picker request id for this session."""
    request_id = secrets.token_urlsafe(16)
    session.metadata["picker_request_id"] = request_id
    session.metadata["picker_request_expires_at"] = time.time() + PICKER_REQUEST_TTL_SECONDS
    return request_id


def validate_picker_request(session, request_id: str) -> None:
    """Stale/duplicate/expired picker requests → typed non-retryable error.

    A second selection can never replace the active dataset (Task 4).
    """
    active = session.metadata.get("picker_request_id")
    expires_at = session.metadata.get("picker_request_expires_at", 0)
    if not active or active != request_id or time.time() > float(expires_at):
        raise DriveImportError(
            "stale_picker_request",
            "This file selection has expired. Open the picker again.",
        )


def consume_picker_request(session) -> None:
    """One-shot consumption after a successful download."""
    session.metadata.pop("picker_request_id", None)
    session.metadata.pop("picker_request_expires_at", None)
