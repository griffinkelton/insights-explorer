"""Tests for utils/drive_client.py — export + v0.3.0 Drive import download."""

import io
from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError

from utils.drive_client import (
    MAX_DRIVE_IMPORT_BYTES,
    DriveImportError,
    download_drive_file,
    write_dataframe_to_drive,
    write_drive_file,
)

SHEETS_MIME = "application/vnd.google-apps.spreadsheet"
CSV_MIME = "text/csv"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class _FakeDownloader:
    """MediaIoBaseDownload stand-in that writes chunks into the buffer."""

    def __init__(self, buffer, request, chunks=None):
        self.buffer = buffer
        self.chunks = chunks if chunks is not None else [b"a,b\n1,2"]

    def next_chunk(self):
        if self.chunks:
            self.buffer.write(self.chunks.pop(0))
            return (None, False)
        return (None, True)


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


class TestDownloadDriveFile:
    """v0.3.0 Phase 1 — download_drive_file() (spec §1.3)."""

    def _service(self, metadata):
        service = MagicMock()
        service.files().get().execute.return_value = metadata
        return service

    def _download(self, metadata, chunks=None, creds=None):
        """Run download_drive_file with a stubbed service + downloader."""
        service = self._service(metadata)

        def _factory(buffer, request):
            return _FakeDownloader(buffer, request, chunks=chunks)

        with patch("utils.drive_client.build", return_value=service), patch(
            "utils.drive_client.MediaIoBaseDownload", side_effect=_factory
        ):
            return download_drive_file(creds or MagicMock(), "file123")

    # ── Media paths ───────────────────────────────────────────────────────

    def test_download_csv(self):
        """CSV uses files.get_media and returns server metadata name."""
        service = self._service({"name": "data.csv", "mimeType": CSV_MIME, "size": 100})

        def _factory(buffer, request):
            return _FakeDownloader(buffer, request)

        with patch("utils.drive_client.build", return_value=service), patch(
            "utils.drive_client.MediaIoBaseDownload", side_effect=_factory
        ):
            file_bytes, name = download_drive_file(MagicMock(), "file123")

        service.files().get_media.assert_called_once_with(fileId="file123")
        assert name == "data.csv"
        assert file_bytes == b"a,b\n1,2"

    def test_download_xlsx(self):
        """XLSX uses files.get_media."""
        file_bytes, name = self._download({"name": "data.xlsx", "mimeType": XLSX_MIME, "size": 100})
        assert name == "data.xlsx"
        assert file_bytes == b"a,b\n1,2"

    def test_download_google_sheet_exports_as_csv(self):
        """Google Sheets uses files.export_media(mimeType='text/csv')."""
        service = self._service({"name": "Report", "mimeType": SHEETS_MIME, "size": None})

        def _factory(buffer, request):
            return _FakeDownloader(buffer, request)

        with patch("utils.drive_client.build", return_value=service), patch(
            "utils.drive_client.MediaIoBaseDownload", side_effect=_factory
        ):
            file_bytes, name = download_drive_file(MagicMock(), "file123")

        service.files().export_media.assert_called_once_with(fileId="file123", mimeType="text/csv")
        assert name == "Report.csv"
        assert file_bytes == b"a,b\n1,2"

    def test_google_sheet_filename_appends_csv(self):
        """'My Report' Sheets -> 'My Report.csv'."""
        _, name = self._download({"name": "My Report", "mimeType": SHEETS_MIME, "size": None})
        assert name == "My Report.csv"

    def test_google_sheet_filename_no_double_csv(self):
        """'report.csv' Sheets -> 'report.csv' (not '.csv.csv')."""
        _, name = self._download({"name": "report.csv", "mimeType": SHEETS_MIME, "size": None})
        assert name == "report.csv"

    # ── Size validation (3 layers) ────────────────────────────────────────

    def test_layer1_too_large_metadata(self):
        """Layer 1: metadata size > 100 MB raises DriveImportError(code='too_large')."""
        with pytest.raises(DriveImportError, match="100 MB") as exc_info:
            self._download(
                {"name": "big.csv", "mimeType": CSV_MIME, "size": MAX_DRIVE_IMPORT_BYTES + 1}
            )
        assert exc_info.value.code == "too_large"

    def test_layer2_too_large_streamed(self):
        """Layer 2: export stream exceeding cap aborts via bounded writer (code='too_large')."""
        with patch("utils.drive_client.MAX_DRIVE_IMPORT_BYTES", 100):
            with pytest.raises(DriveImportError, match="100 MB") as exc_info:
                self._download(
                    {"name": "Report", "mimeType": SHEETS_MIME, "size": None},
                    chunks=[b"x" * 100, b"y" * 100],
                )
            assert exc_info.value.code == "too_large"

    def test_layer3_final_byte_check(self):
        """Layer 3: final len() check rejects oversized bytes (safety net, code='too_large').

        Uses an unbounded writer so the streamed cap doesn't fire first —
        proving the final check is an independent guard.
        """
        with patch("utils.drive_client.MAX_DRIVE_IMPORT_BYTES", 100), patch(
            "utils.drive_client._BoundedBytesIO", io.BytesIO
        ):
            with pytest.raises(DriveImportError, match="100 MB") as exc_info:
                self._download(
                    {"name": "big.csv", "mimeType": CSV_MIME, "size": None},
                    chunks=[b"x" * 200],
                )
            assert exc_info.value.code == "too_large"

    # ── MIME allowlist + empty files ──────────────────────────────────────

    def test_rejects_unsupported_mime_type(self):
        """application/pdf is not in the import allowlist (code='unsupported_type')."""
        with pytest.raises(DriveImportError, match="cannot be imported") as exc_info:
            self._download({"name": "doc.pdf", "mimeType": "application/pdf", "size": 10})
        assert exc_info.value.code == "unsupported_type"

    def test_rejects_zero_byte_file(self):
        """An empty download raises DriveImportError(code='empty_file')."""
        with pytest.raises(DriveImportError, match="empty") as exc_info:
            self._download({"name": "empty.csv", "mimeType": CSV_MIME, "size": 0}, chunks=[])
        assert exc_info.value.code == "empty_file"

    # ── Server metadata authority ─────────────────────────────────────────

    def test_fetches_server_metadata_not_client_values(self):
        """files.get is called with fileId+fields; server name wins."""
        service = self._service({"name": "server-name.xlsx", "mimeType": XLSX_MIME, "size": 100})

        def _factory(buffer, request):
            return _FakeDownloader(buffer, request)

        with patch("utils.drive_client.build", return_value=service), patch(
            "utils.drive_client.MediaIoBaseDownload", side_effect=_factory
        ):
            file_bytes, name = download_drive_file(MagicMock(), "file123")

        # The _service() helper's own ``get().execute`` chain records one call;
        # assert_any_call proves the download path issued the server-metadata
        # request with the correct kwargs (name/mimeType/size authority).
        service.files().get.assert_any_call(fileId="file123", fields="name,mimeType,size")
        assert name == "server-name.xlsx"

    # ── Error classification ──────────────────────────────────────────────

    def test_handles_404_error(self):
        """Drive 404 -> DriveImportError(code='not_found'), no raw API text."""
        service = MagicMock()
        service.files().get().execute.side_effect = HttpError(MagicMock(status=404), b"not found")
        with patch("utils.drive_client.build", return_value=service):
            with pytest.raises(DriveImportError, match="permission") as exc_info:
                download_drive_file(MagicMock(), "file123")
        assert exc_info.value.code == "not_found"

    def test_handles_403_error(self):
        """Drive 403 -> DriveImportError(code='access_denied'), suggests reconnect."""
        service = MagicMock()
        service.files().get().execute.side_effect = HttpError(MagicMock(status=403), b"forbidden")
        with patch("utils.drive_client.build", return_value=service):
            with pytest.raises(DriveImportError, match="reconnect") as exc_info:
                download_drive_file(MagicMock(), "file123")
        assert exc_info.value.code == "access_denied"

    def test_handles_generic_http_error(self):
        """Drive 500 -> DriveImportError(code='download_failed')."""
        service = MagicMock()
        service.files().get().execute.side_effect = HttpError(
            MagicMock(status=500), b"server error"
        )
        with patch("utils.drive_client.build", return_value=service):
            with pytest.raises(DriveImportError, match="try again") as exc_info:
                download_drive_file(MagicMock(), "file123")
        assert exc_info.value.code == "download_failed"

    def test_service_build_failure_maps_to_download_failed(self):
        """Credentials-refresh or service-construction failure → download_failed."""
        with patch(
            "utils.drive_client._build_drive_service",
            side_effect=ConnectionError("network unreachable"),
        ):
            with pytest.raises(DriveImportError, match="try again") as exc_info:
                download_drive_file(MagicMock(), "file123")
        assert exc_info.value.code == "download_failed"

    def test_non_http_downloader_failure_maps_to_download_failed(self):
        """Non-HttpError download transport failure → download_failed (from None)."""
        service = self._service({"name": "data.csv", "mimeType": CSV_MIME, "size": 100})

        def _failing_factory(buffer, request):
            raise OSError("connection reset")

        with patch("utils.drive_client.build", return_value=service), patch(
            "utils.drive_client.MediaIoBaseDownload", side_effect=_failing_factory
        ):
            with pytest.raises(DriveImportError, match="try again") as exc_info:
                download_drive_file(MagicMock(), "file123")
        assert exc_info.value.code == "download_failed"
        # Verify from None — the __cause__ must not be the OSError.
        assert exc_info.value.__cause__ is None

    # ── Credentials + behavior ────────────────────────────────────────────

    def test_refreshes_expired_credentials(self):
        """Expired credentials with a refresh token are refreshed."""
        creds = MagicMock()
        creds.expired = True
        creds.refresh_token = "rt"
        self._download({"name": "data.csv", "mimeType": CSV_MIME, "size": 100}, creds=creds)
        creds.refresh.assert_called_once()

    def test_google_sheets_single_sheet_behavior(self):
        """Docstring documents first-sheet-only Google Sheets behavior."""
        assert "first sheet" in download_drive_file.__doc__.lower()
