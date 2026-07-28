"""Google Drive client — file listing, download, and DataFrame loading."""

from io import BytesIO
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# Limits — imported from data_loader for consistency
from utils.data_loader import MAX_FILE_SIZE_MB, MAX_ROWS


def _build_drive_service(credentials: Credentials):
    """Build an authorized Drive v3 service client. Refreshes tokens if expired."""
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return build("drive", "v3", credentials=credentials)


def list_drive_files(
    credentials: Credentials,
    mime_types: list[str],
    page_size: int = 50,
) -> list[dict[str, str]]:
    """List files in the user's Drive matching given MIME types.

    Args:
        credentials: OAuth credentials from st.session_state.ga4_creds.
        mime_types: e.g., ["text/csv", "application/vnd.google-apps.spreadsheet"].
        page_size: Max files to return.

    Returns:
        [{"id": "...", "name": "...", "mime_type": "..."}, ...]
    """
    service = _build_drive_service(credentials)
    query = " or ".join(f"mimeType='{mt}'" for mt in mime_types)
    try:
        results = (
            service.files()
            .list(
                q=f"({query}) and trashed = false",
                pageSize=page_size,
                fields="files(id, name, mimeType)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
    except HttpError as e:
        raise RuntimeError(f"Drive API error listing files: {e}") from e

    return [
        {
            "id": f["id"],
            "name": f["name"],
            "mime_type": f["mimeType"],
        }
        for f in results.get("files", [])
    ]


def download_drive_file(
    credentials: Credentials,
    file_id: str,
    mime_type: str,
) -> BytesIO:
    """Download a Drive file as CSV bytes.

    - text/csv: direct download.
    - application/vnd.google-apps.spreadsheet: export as CSV via Drive export API.
    """
    service = _build_drive_service(credentials)

    try:
        if mime_type == "application/vnd.google-apps.spreadsheet":
            request = service.files().export_media(
                fileId=file_id, mimeType="text/csv",
            )
        else:
            request = service.files().get_media(fileId=file_id)

        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buffer.seek(0)
        return buffer
    except HttpError as e:
        raise RuntimeError(f"Drive API error downloading file: {e}") from e


def load_drive_file_as_df(
    credentials: Credentials,
    file_id: str,
    mime_type: str,
) -> tuple[pd.DataFrame | None, str | None]:
    """Download a Drive file and load it as a pandas DataFrame.

    Enforces same limits as load_file(): MAX_FILE_SIZE_MB (100MB), MAX_ROWS (50k).
    Returns (df, None) on success or (None, error_message) on failure.
    Matches the signature of load_file() in utils/data_loader.py.
    """
    try:
        buffer = download_drive_file(credentials, file_id, mime_type)

        # Enforce file size limit
        buffer.seek(0, 2)  # Seek to end
        file_size = buffer.tell()
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            return None, (
                f"File too large ({file_size / 1024 / 1024:.1f} MB). "
                f"Maximum is {MAX_FILE_SIZE_MB} MB."
            )
        buffer.seek(0)

        df = pd.read_csv(buffer)
        if df.empty:
            return None, "The selected file is empty."

        # Enforce row limit
        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)

        return df, None
    except RuntimeError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Failed to load Drive file: {e}"
