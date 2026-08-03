"""Phase 3.3 Error-Path simulation — E1 through E6.

Tests inject a fake downloader into ``_ingest_drive_file`` to simulate
each ``DriveImportError`` code and verify the correct user-facing
``st.error`` message is produced.  No real Drive API, no OAuth, no
Playwright required.

These cover the 6 error-path rows in RELEASE_CHECKLIST.md:
    E1 — access_denied
    E2 — not_found
    E3 — unsupported_type
    E4 — too_large
    E5 — empty_file
    E6 — download_failed
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from google.oauth2.credentials import Credentials

from components.sidebar import _ingest_drive_file
from utils.drive_client import DriveImportError

# ── Full user-facing messages (verbatim from drive_client.py) ──────────
# These are what st.error displays to the user.  We assert substring
# matches so minor wording tweaks don't break the tests.

ERROR_MESSAGES: dict[str, str] = {
    "access_denied": (
        "Access denied. Check the 🔍 Drive Import Diagnostics in the sidebar. "
        "Common causes: (1) Drive API not enabled in GCP, "
        "(2) Picker API key and OAuth client are in different GCP projects, "
        "(3) OAuth token missing the drive.file scope — try reconnecting."
    ),
    "not_found": ("File not found or access denied. Check that you have permission."),
    "unsupported_type": ("This file type cannot be imported. Use CSV, XLSX, or Google Sheets."),
    "too_large": ("The selected file exceeds the 100 MB limit."),
    "empty_file": ("The selected file is empty."),
    "download_failed": ("Could not download the file. Please try again."),
}


def _fake_credentials() -> Credentials:
    """Return a minimal Credentials object (no real tokens required)."""
    return Credentials(token="test-token")


def _downloader_that_raises(code: str) -> MagicMock:
    """Return a mock downloader that raises DriveImportError(code, message)."""
    msg = ERROR_MESSAGES[code]
    downloader = MagicMock()
    downloader.side_effect = DriveImportError(code, msg)
    return downloader


def _downloader_that_succeeds() -> MagicMock:
    """Return a mock downloader that returns fixture bytes + display name."""
    downloader = MagicMock()
    downloader.return_value = (b"date,sessions\n2024-01-01,100", "test.csv")
    return downloader


# ══════════════════════════════════════════════════════════════════════
# E1–E6: Error-path simulation
# ══════════════════════════════════════════════════════════════════════


class TestDriveImportErrorPaths:
    """Simulate each of the 6 error codes via dependency injection.

    Every test mocks ``st.error`` so we can assert the exact user-facing
    message without needing a running Streamlit server.
    """

    @patch("components.sidebar.st")
    def test_e1_access_denied_shows_user_safe_error(self, mock_st):
        """E1: access_denied → st.error with user-safe message, returns False."""
        creds = _fake_credentials()
        downloader = _downloader_that_raises("access_denied")

        result = _ingest_drive_file(downloader, creds, "test-file-id")

        assert result is False
        mock_st.error.assert_called_once()
        call_arg = mock_st.error.call_args[0][0]
        assert "Access denied" in call_arg
        assert "Drive API not enabled" in call_arg
        # Must NOT leak raw API error, file ID, or token.
        assert "test-file-id" not in call_arg
        assert "ya29" not in call_arg.lower()
        assert "AIza" not in call_arg

    @patch("components.sidebar.st")
    def test_e2_not_found_shows_user_safe_error(self, mock_st):
        """E2: not_found → st.error with 'not found', returns False."""
        creds = _fake_credentials()
        downloader = _downloader_that_raises("not_found")

        result = _ingest_drive_file(downloader, creds, "test-file-id")

        assert result is False
        mock_st.error.assert_called_once()
        call_arg = mock_st.error.call_args[0][0]
        assert "not found" in call_arg.lower()
        assert "permission" in call_arg.lower()
        assert "test-file-id" not in call_arg

    @patch("components.sidebar.st")
    def test_e3_unsupported_type_shows_user_safe_error(self, mock_st):
        """E3: unsupported_type → st.error with 'cannot be imported', returns False."""
        creds = _fake_credentials()
        downloader = _downloader_that_raises("unsupported_type")

        result = _ingest_drive_file(downloader, creds, "test-file-id")

        assert result is False
        mock_st.error.assert_called_once()
        call_arg = mock_st.error.call_args[0][0]
        assert "cannot be imported" in call_arg.lower()
        assert "CSV" in call_arg
        assert "XLSX" in call_arg
        assert "test-file-id" not in call_arg

    @patch("components.sidebar.st")
    def test_e4_too_large_shows_user_safe_error(self, mock_st):
        """E4: too_large → st.error with '100 MB', returns False."""
        creds = _fake_credentials()
        downloader = _downloader_that_raises("too_large")

        result = _ingest_drive_file(downloader, creds, "test-file-id")

        assert result is False
        mock_st.error.assert_called_once()
        call_arg = mock_st.error.call_args[0][0]
        assert "100 MB" in call_arg
        assert "test-file-id" not in call_arg

    @patch("components.sidebar.st")
    def test_e5_empty_file_shows_user_safe_error(self, mock_st):
        """E5: empty_file → st.error with 'empty', returns False."""
        creds = _fake_credentials()
        downloader = _downloader_that_raises("empty_file")

        result = _ingest_drive_file(downloader, creds, "test-file-id")

        assert result is False
        mock_st.error.assert_called_once()
        call_arg = mock_st.error.call_args[0][0]
        assert "empty" in call_arg.lower()
        assert "test-file-id" not in call_arg

    @patch("components.sidebar.st")
    def test_e6_download_failed_shows_user_safe_error(self, mock_st):
        """E6: download_failed → st.error with 'try again', returns False."""
        creds = _fake_credentials()
        downloader = _downloader_that_raises("download_failed")

        result = _ingest_drive_file(downloader, creds, "test-file-id")

        assert result is False
        mock_st.error.assert_called_once()
        call_arg = mock_st.error.call_args[0][0]
        assert "try again" in call_arg.lower()
        assert "test-file-id" not in call_arg

    @patch("components.sidebar.st")
    def test_success_path_returns_true(self, mock_st):
        """Non-error path: successful download → returns True, no st.error."""
        creds = _fake_credentials()
        downloader = _downloader_that_succeeds()

        result = _ingest_drive_file(downloader, creds, "test-file-id")

        assert result is True
        mock_st.error.assert_not_called()
