"""Google Drive client — write-only exports + v0.3.0 Drive import download.

Export paths (Sheets, CSV, Drive upload) were kept in v0.1.0 under the
least-privilege ``drive.file`` scope. ``download_drive_file`` (v0.3.0)
re-adds a *single-file* read path: the user explicitly selects one file
via the Picker, and the server fetches authoritative metadata and
streams that one file within a bounded in-memory buffer. The app never
lists or scans the user's Drive.
"""

import io
import logging
from io import BytesIO
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

from utils.sanitize import safe_spreadsheet_value

logger = logging.getLogger(__name__)


class DriveImportError(RuntimeError):
    """Public, typed error for Drive-import failures.

    The UI and tests branch on ``.code``, not on message text. Codes are
    stable and document the full error taxonomy for Phase 2+3 UX mapping.

    Never attach raw Google error payloads, file IDs, or request URLs.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# Supported MIME types for Drive import (server-authoritative allowlist).
# Google Sheets is exported server-side as CSV (first sheet only).
DRIVE_IMPORT_MIME_TYPES = {
    "text/csv": ".csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.google-apps.spreadsheet": ".csv",
}

MAX_DRIVE_IMPORT_BYTES = 100 * 1024 * 1024  # 100 MB

GOOGLE_SHEETS_EXPORT_MIME = "text/csv"


def _build_drive_service(credentials: Credentials):
    """Build an authorized Drive v3 service client. Refreshes tokens if expired."""
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return build("drive", "v3", credentials=credentials)


class _BoundedBytesIO(io.BytesIO):
    """BytesIO that rejects writes exceeding MAX_DRIVE_IMPORT_BYTES.

    Rejects the chunk before it is retained in the in-memory output
    buffer, preventing unbounded accumulation from a large Google Sheets
    export that lacks a metadata size.
    """

    def write(self, data: bytes) -> int:
        if self.tell() + len(data) > MAX_DRIVE_IMPORT_BYTES:
            raise DriveImportError("too_large", "The selected file exceeds the 100 MB limit.")
        return super().write(data)


def download_drive_file(
    credentials: Credentials,
    file_id: str,
) -> tuple[bytes, str]:
    """Download a single file from Google Drive for import.

    Server-side metadata is authoritative — the ``file_id`` is an opaque
    token from the Picker; name, MIME type, and size are fetched from the
    Drive API, never from client-provided values.

    Size validation uses 3 layers:
    1. Metadata preflight — reject if 'size' field > 100 MB (fast).
    2. Streamed byte cap — hard-abort the download/export stream if
       accumulated bytes exceed 100 MB (catches Sheets with no preflight).
    3. Final check — verify len(bytes) <= 100 MB before returning.

    Google Sheets behavior: exports only the **first sheet** as CSV.

    Args:
        credentials: Valid OAuth credentials (with drive.file scope).
        file_id: Google Drive file ID from the Picker.

    Returns:
        Tuple of (file_bytes, normalized_filename).
        - Google Sheets: filename gets '.csv' extension if not already present.
        - CSV/XLSX: filename used as-is from server metadata.

    Raises:
        DriveImportError: With fixed codes — ``unsupported_type``,
            ``too_large``, ``empty_file``, ``not_found``,
            ``access_denied``, or ``download_failed``.
    """
    service = _build_drive_service(credentials)

    try:
        # 1. Server metadata is authoritative (never trust Picker name/MIME).
        metadata = service.files().get(fileId=file_id, fields="name,mimeType,size").execute()
    except HttpError as e:
        _raise_classified_drive_error(e)

    name = metadata.get("name", "")
    mime_type = metadata.get("mimeType", "")
    size = metadata.get("size")

    # MIME allowlist — reject anything not importable.
    if mime_type not in DRIVE_IMPORT_MIME_TYPES:
        logger.warning("Drive import rejected: category=unsupported_mime")
        raise DriveImportError(
            "unsupported_type",
            "This file type cannot be imported. Use CSV, XLSX, or Google Sheets.",
        )

    # Layer 1: metadata preflight (fast path for CSV/XLSX).
    if size is not None and int(size) > MAX_DRIVE_IMPORT_BYTES:
        logger.warning("Drive import rejected: category=file_too_large")
        raise DriveImportError("too_large", "The selected file exceeds the 100 MB limit.")

    # Layer 2: streamed byte cap with bounded in-memory writer.
    buffer = _BoundedBytesIO()
    try:
        if mime_type == "application/vnd.google-apps.spreadsheet":
            request = service.files().export_media(
                fileId=file_id, mimeType=GOOGLE_SHEETS_EXPORT_MIME
            )
        else:
            request = service.files().get_media(fileId=file_id)

        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    except HttpError as e:
        _raise_classified_drive_error(e)

    file_bytes = buffer.getvalue()

    # Layer 3: final byte check (safety net).
    if len(file_bytes) > MAX_DRIVE_IMPORT_BYTES:
        logger.warning("Drive import rejected: category=file_too_large")
        raise DriveImportError("too_large", "The selected file exceeds the 100 MB limit.")

    # Zero-byte rejection.
    if not file_bytes:
        logger.warning("Drive import rejected: category=empty_file")
        raise DriveImportError("empty_file", "The selected file is empty.")

    # Google Sheets: first sheet only; avoid a double '.csv' extension.
    if mime_type == "application/vnd.google-apps.spreadsheet":
        if name.lower().endswith(".csv"):
            final_name = name
        else:
            final_name = f"{name}.csv"
    else:
        final_name = name

    return file_bytes, final_name


def _raise_classified_drive_error(error: HttpError) -> None:
    """Raise a DriveImportError for a Drive API HttpError.

    Never exposes raw API error text, request URLs, file IDs, or token
    fragments. Logs only an allowlisted error category — never
    ``exc_info=True`` (tracebacks can reproduce the raw HttpError payload
    including request URLs and file IDs).
    """
    status = getattr(error.resp, "status", None)
    if status == 404:
        logger.warning("Drive download failed: category=not_found")
        raise DriveImportError(
            "not_found",
            "File not found or access denied. Check that you have permission.",
        )
    if status == 403:
        logger.warning("Drive download failed: category=access_denied")
        raise DriveImportError(
            "access_denied",
            "Access denied. Try reconnecting your Google account.",
        )
    logger.warning("Drive download failed: category=download_failed")
    raise DriveImportError(
        "download_failed",
        "Could not download the file. Please try again.",
    )


def _build_sheets_service(credentials: Credentials):
    """Build an authorized Google Sheets API v4 service client."""
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return build("sheets", "v4", credentials=credentials)


def write_drive_file(
    credentials: Credentials,
    filename: str,
    content: str | bytes,
    mime_type: str = "text/plain",
    folder_id: str | None = None,
) -> str:
    """Create and upload a file to the user's Google Drive."""
    service = _build_drive_service(credentials)

    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    else:
        content_bytes = content

    file_metadata = {"name": filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(
        BytesIO(content_bytes),
        mimetype=mime_type,
        resumable=False,
    )

    try:
        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink",
            )
            .execute()
        )
        return file.get("id")
    except HttpError as e:
        raise RuntimeError(f"Drive API error uploading file: {e}") from e


def write_dataframe_to_drive(
    credentials: Credentials,
    filename: str,
    df: pd.DataFrame,
    folder_id: str | None = None,
) -> str:
    """Export a DataFrame as CSV and upload to Google Drive."""
    # Apply formula-escaping to all cell values before CSV export
    sanitized = df.map(safe_spreadsheet_value)
    csv_content = sanitized.to_csv(index=False)
    return write_drive_file(
        credentials,
        filename=filename,
        content=csv_content,
        mime_type="text/csv",
        folder_id=folder_id,
    )


def create_google_sheet(
    credentials: Credentials,
    title: str,
    df: pd.DataFrame | None = None,
    summary: str | None = None,
    chat_history: list[dict] | None = None,
) -> tuple[str, str]:
    """Create a new Google Sheet with analysis results.

    Creates a spreadsheet with Dashboard, Data, and Q&A tabs.

    Returns:
        Tuple of (spreadsheet_id, spreadsheet_url).

    Raises:
        RuntimeError: If the Sheets API returns an error.
    """
    sheets_service = _build_sheets_service(credentials)

    # Create the spreadsheet with initial sheet
    spreadsheet = (
        sheets_service.spreadsheets().create(body={"properties": {"title": title}}).execute()
    )
    spreadsheet_id = spreadsheet["spreadsheetId"]

    # Rename the default sheet to "Dashboard" and add Data + Q&A sheets
    requests_body = [
        {
            "updateSheetProperties": {
                "properties": {"sheetId": 0, "title": "Dashboard"},
                "fields": "title",
            }
        },
        {"addSheet": {"properties": {"title": "Data"}}},
        {"addSheet": {"properties": {"title": "Q&A"}}},
    ]
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests_body},
    ).execute()

    # ── Populate Dashboard ──
    dashboard_values = [
        [safe_spreadsheet_value("📊 GA4 Insight Explorer — Report")],
        [""],
        ["Generated:", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
        ["Data Source:", "GA4 Insight Explorer"],
        [""],
        ["📋 Dataset Overview"],
        ["Total Rows:", len(df) if df is not None else 0],
        ["Columns:", len(df.columns) if df is not None else 0],
    ]
    if summary:
        dashboard_values.append([""])
        dashboard_values.append([safe_spreadsheet_value("🤖 AI Summary")])
        for line in summary.split("\n")[:15]:
            if line.strip():
                dashboard_values.append([safe_spreadsheet_value(line[:100])])

    # ── Populate Data ──
    data_values = []
    if df is not None and not df.empty:
        data_values.append([safe_spreadsheet_value(str(col)) for col in df.columns])
        for _, row in df.head(1000).iterrows():
            data_values.append([safe_spreadsheet_value(str(v)) if pd.notna(v) else "" for v in row])

    # ── Populate Q&A ──
    qa_values = [["Question", "AI Response"]]
    for entry in chat_history or []:
        if entry.get("response") and entry["response"] != "":
            qa_values.append(
                [
                    safe_spreadsheet_value(entry["question"][:200]),
                    safe_spreadsheet_value(entry["response"][:500]),
                ]
            )

    # Batch write all three sheets
    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "RAW",
            "data": [
                {"range": "Dashboard!A1", "values": dashboard_values},
                {"range": "Data!A1", "values": data_values},
                {"range": "Q&A!A1", "values": qa_values},
            ],
        },
    ).execute()

    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    return spreadsheet_id, spreadsheet_url
