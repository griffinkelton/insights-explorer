"""Google Drive client — write-only exports (Sheets, CSV, Drive upload).

Drive browsing (list_drive_files, download_drive_file, load_drive_file_as_df)
was removed in v0.1.0 to enforce least-privilege: only drive.file scope is
requested; the app cannot list or read arbitrary Drive files.
"""

from io import BytesIO
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

from utils.sanitize import safe_spreadsheet_value


def _build_drive_service(credentials: Credentials):
    """Build an authorized Drive v3 service client. Refreshes tokens if expired."""
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return build("drive", "v3", credentials=credentials)


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
