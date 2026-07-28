# 📂 Google Drive File Picker — Implementation Spec

> **Source:** User request (2026-07-28)
> **Status:** 🔵 Planned — awaiting implementation
> **Effort:** Small (1-2 hours) | **Risk:** Low
> **Based on:** Verified against current `utils/ga4_client.py`, `utils/data_loader.py`, `components/sidebar.py`, `requirements.txt`, `app.py`

---

## 🎯 Goal

When a user is authenticated with Google (via the existing "Sign in with Google" OAuth flow), add a Drive file picker in the sidebar. Users select a CSV or Google Sheet from their Drive, and the data loads into `st.session_state.df` exactly as if uploaded via `st.file_uploader`. Zero new UI for authentication — it piggybacks on the existing GA4 OAuth flow.

---

## 🏗️ Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| OAuth scope | **Add `drive.readonly` to existing `SCOPES`** | One OAuth flow, one credential, both GA4 + Drive access. `prompt="consent"` already forces re-consent for new scopes. |
| Drive API client | **`googleapiclient.discovery.build("drive", "v3")`** | Standard Google Drive v3 REST API. Already a transitive dependency of `google-analytics-data`. |
| File types | **CSV + Google Sheets** | `text/csv` for raw CSV, `application/vnd.google-apps.spreadsheet` for Sheets (exported as CSV). |
| File list caching | **`st.session_state.drive_files_cache`** | Prevents re-fetching the file list on every Streamlit rerun. Cleared on disconnect. |
| Data loading | **Parallel path, not replacement** | `load_drive_file_as_df()` matches `load_file()` signature `(df | None, error | None)`. Separate from file upload path. |
| UI placement | **Between GA4 connect and privacy notice** | Only visible when `ga4_creds is not None`. Logically grouped with Google-connected features. |
| Error handling | **`if st.button → try/except → st.error`** | Follows BUG-005 pattern. No `on_click` callbacks for network operations. |

---

## 📁 Files Changed

| File | Change | Lines |
|---|---|---|
| `utils/ga4_client.py` | Add `drive.readonly` to `SCOPES` list | +1 |
| `utils/drive_client.py` | **NEW**: `list_drive_files()`, `download_drive_file()`, `load_drive_file_as_df()` | ~80 |
| `components/sidebar.py` | Add `_render_drive_picker()` + call in `render_sidebar()` | ~55 |
| `app.py` | Add `drive_files_cache` to session state | +3 |
| `requirements.txt` | Add `google-api-python-client>=2.0.0` | +1 |
| `tests/test_drive_client.py` | **NEW**: 3 tests | ~40 |
| **Total** | **6 files changed, 2 new** | **~180 lines** |

---

## 📐 Detailed Changes

### 1. `utils/ga4_client.py` — expand OAuth scope

```python
# Before:
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

# After:
SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/drive.readonly",  # Drive file picker
]
```

Existing users will see a re-consent screen asking for Drive access. The `prompt="consent"` in `get_auth_url()` already forces this — no code change needed for the re-consent flow itself.

### 2. `utils/drive_client.py` — new file

```python
"""Google Drive client — file listing, download, and DataFrame loading."""

from io import BytesIO
from typing import Any
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError


def _build_drive_service(credentials: Credentials):
    """Build an authorized Drive v3 service client."""
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
    query = " or ".join(
        f"mimeType='{mt}'" for mt in mime_types
    )
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
            # Google Sheets — export as CSV
            request = service.files().export_media(
                fileId=file_id,
                mimeType="text/csv",
            )
        else:
            # CSV — direct download
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

    Returns (df, None) on success or (None, error_message) on failure.
    Matches the signature of load_file() in utils/data_loader.py.
    """
    try:
        buffer = download_drive_file(credentials, file_id, mime_type)
        df = pd.read_csv(buffer)
        if df.empty:
            return None, "The selected file is empty."
        return df, None
    except RuntimeError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Failed to load Drive file: {e}"
```

### 3. `components/sidebar.py` — Drive file picker UI

#### 3a: Add import

```python
from utils.drive_client import list_drive_files, load_drive_file_as_df
```

#### 3b: Add `_render_drive_picker()` function

```python
def _render_drive_picker() -> None:
    """Render the Google Drive file picker (only when authenticated)."""
    if st.session_state.ga4_creds is None:
        return

    st.divider()
    st.markdown("**📂 Google Drive**")

    creds = credentials_from_dict(st.session_state.ga4_creds)

    # Cache the file list to avoid re-fetching on every rerun
    if st.session_state.get("drive_files_cache") is None:
        with st.spinner("Loading Drive files..."):
            try:
                files = list_drive_files(
                    creds,
                    ["text/csv", "application/vnd.google-apps.spreadsheet"],
                )
                st.session_state.drive_files_cache = files
            except Exception as e:
                st.error(f"Drive error: {e}")
                return

    files = st.session_state.drive_files_cache

    if not files:
        st.caption("No CSV files or Google Sheets found in your Drive.")
        return

    # File selector
    file_names = [f["name"] for f in files]
    selected_name = st.selectbox(
        "Select a file",
        options=file_names,
        key="drive_file_select",
    )

    # Find the selected file's metadata
    selected_file = next(f for f in files if f["name"] == selected_name)

    # Load button
    if st.button("📥 Load from Drive", use_container_width=True):
        with st.spinner(f"Loading {selected_name}..."):
            df, error = load_drive_file_as_df(
                creds,
                selected_file["id"],
                selected_file["mime_type"],
            )

        if error:
            st.error(error)
        else:
            # Same session state population as _process_uploaded_file()
            missing = validate_columns(df)
            if missing:
                st.warning(
                    f"⚠️ Missing expected columns: {', '.join(missing)}. "
                    "Some features may be limited."
                )

            date_cols = [c for c in df.columns if "date" in c.lower()]
            if date_cols:
                try:
                    df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors="coerce")
                except Exception:
                    pass

            st.session_state.df = df
            st.session_state.missing_columns = missing
            st.session_state.stats = get_dataset_stats(df)
            st.session_state.stats["missing_columns"] = missing
            st.session_state.quality_report = assess_data_quality(df, missing)
            st.session_state.summary = None
            st.session_state.chat_history = []
            st.session_state.data_source = "drive"
            st.session_state.data_cleared = False
            st.rerun()
```

#### 3c: Update `render_sidebar()` to call it

Insert `_render_drive_picker()` between `_render_ga4_connect()` and `_render_privacy_notice()`:

```python
    _render_ga4_connect()
    _render_drive_picker()        # ← Drive picker (only when authenticated)
    st.divider()
    _render_privacy_notice()
```

#### 3d: Clear Drive cache on disconnect

In `_render_ga4_connect()`, when disconnecting, also clear the cache:

```python
if st.button("✕ Disconnect", use_container_width=True):
    st.session_state.ga4_creds = None
    st.session_state.ga4_auth_flow = None
    st.session_state.ga4_property_id = ""
    st.session_state.drive_files_cache = None  # ← Clear Drive cache
    if st.session_state.data_source == "ga4":
        clear_data()
    st.rerun()
```

### 4. `app.py` — session state

Add after the existing session state block:

```python
if "drive_files_cache" not in st.session_state:
    st.session_state.drive_files_cache = None
```

### 5. `requirements.txt` — add dependency

```
google-api-python-client>=2.0.0
```

This is already a transitive dependency of `google-analytics-data` but should be explicit since `utils/drive_client.py` imports `googleapiclient` directly.

### 6. `tests/test_drive_client.py` — new file

```python
"""Tests for utils/drive_client.py."""

from unittest.mock import patch, MagicMock
from io import BytesIO
from utils.drive_client import list_drive_files, download_drive_file, load_drive_file_as_df


class TestListDriveFiles:
    def test_returns_list_of_dicts(self):
        """list_drive_files should return a list of file dicts."""
        mock_creds = MagicMock()
        mock_service = MagicMock()
        mock_service.files().list().execute.return_value = {
            "files": [
                {"id": "abc123", "name": "report.csv", "mimeType": "text/csv"},
            ]
        }

        with patch("utils.drive_client.build", return_value=mock_service):
            result = list_drive_files(mock_creds, ["text/csv"])
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "abc123"
            assert result[0]["name"] == "report.csv"


class TestDownloadDriveFile:
    def test_exports_sheets_as_csv(self):
        """Google Sheets should use the export_media endpoint."""
        mock_creds = MagicMock()
        mock_service = MagicMock()

        with patch("utils.drive_client.build", return_value=mock_service):
            with patch("utils.drive_client.MediaIoBaseDownload") as mock_download:
                mock_download.return_value.next_chunk.return_value = (None, True)
                result = download_drive_file(
                    mock_creds, "sheet123", "application/vnd.google-apps.spreadsheet"
                )
                mock_service.files().export_media.assert_called_once_with(
                    fileId="sheet123", mimeType="text/csv"
                )
                assert isinstance(result, BytesIO)


class TestLoadDriveFileAsDF:
    def test_returns_error_on_bad_file(self):
        """load_drive_file_as_df should return (None, error_str) on failure."""
        mock_creds = MagicMock()

        with patch(
            "utils.drive_client.download_drive_file",
            side_effect=RuntimeError("Drive API error"),
        ):
            df, error = load_drive_file_as_df(mock_creds, "bad_id", "text/csv")
            assert df is None
            assert error is not None
            assert "Drive API error" in error
```

---

## 🔍 Edge Cases

| Case | Handling |
|---|---|
| User not authenticated | `_render_drive_picker()` returns immediately. No Drive section visible. |
| Empty Drive | `st.caption("No CSV files or Google Sheets found...")` |
| Drive API error | `st.error(f"Drive error: {e}")`, file list stays cached |
| Large file download | `MediaIoBaseDownload` streams in chunks. No memory issues for reasonable files. |
| Disconnect clears cache | `drive_files_cache = None` on disconnect. Next auth re-fetches. |
| Re-authentication (new scopes) | `prompt="consent"` forces re-consent. User sees new "Drive access" permission screen. |
| `google-api-python-client` not installed | Import error in `utils/drive_client.py`. Only triggered when Drive section renders. Surround import in `_render_drive_picker()` with try/except? No — import at module level. If missing, the app boot fails with a clear ImportError. Add to requirements.txt to prevent this. |

---

## 🚫 Out of Scope

- Folder browsing / navigation — flat file list only
- Uploading files to Drive
- Drive file picker for non-CSV formats (PDF, images)
- Paging beyond 50 files
- `google-api-python-client` version pinning — `>=2.0.0` is sufficient

---

## 🧪 Test Impact

| Module | Change | Tests |
|---|---|---|
| `test_drive_client.py` | **NEW** | 3 tests: list_drive_files returns list, download_drive_file exports Sheets, load_drive_file_as_df returns error |
| All existing tests | Unchanged | No imports changed in tested modules |

**Post-Drive expected: 231 → ~234 tests.**
