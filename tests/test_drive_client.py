"""Tests for utils/drive_client.py — export-only in v0.1.0.

Drive browsing functions (list_drive_files, download_drive_file,
load_drive_file_as_df) were removed in PR 2 to enforce least-privilege
(drive.file scope only, no drive.readonly).
"""

from unittest.mock import patch, MagicMock
from utils.drive_client import write_drive_file, write_dataframe_to_drive


class TestWriteDriveFile:
    def test_returns_file_id(self):
        """write_drive_file should return a file ID on success."""
        mock_creds = MagicMock()
        mock_service = MagicMock()
        mock_service.files().create().execute.return_value = {
            "id": "file123",
            "name": "test.csv",
        }

        with patch("utils.drive_client.build", return_value=mock_service):
            result = write_drive_file(
                mock_creds, "test.csv", "col1,col2\n1,2", mime_type="text/csv"
            )
            assert result == "file123"

    def test_refreshes_expired_token(self):
        """Should refresh expired tokens before building the service."""
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh123"
        mock_service = MagicMock()
        mock_service.files().create().execute.return_value = {"id": "ok"}

        with patch("utils.drive_client.build", return_value=mock_service):
            write_drive_file(mock_creds, "test.csv", "data", mime_type="text/csv")
            mock_creds.refresh.assert_called_once()


class TestWriteDataFrameToDrive:
    def test_calls_write_drive_file(self):
        """write_dataframe_to_drive should delegate to write_drive_file."""
        import pandas as pd

        mock_creds = MagicMock()
        df = pd.DataFrame({"col": ["a", "b"]})

        with patch("utils.drive_client.write_drive_file", return_value="id123") as mock_write:
            result = write_dataframe_to_drive(mock_creds, "export.csv", df)
            assert result == "id123"
            mock_write.assert_called_once()
