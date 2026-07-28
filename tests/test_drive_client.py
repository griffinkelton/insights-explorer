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

    def test_refreshes_expired_token(self):
        """Should refresh expired tokens before building the service."""
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh123"
        mock_service = MagicMock()

        with patch("utils.drive_client.build", return_value=mock_service):
            with patch("utils.drive_client.MediaIoBaseDownload") as mock_download:
                mock_download.return_value.next_chunk.return_value = (None, True)
                download_drive_file(mock_creds, "file123", "text/csv")
                mock_creds.refresh.assert_called_once()


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
