"""Phase 5 Drive contract tests (spec phase-5-ga4-drive.md Task 6).

Picker-first path: JIT picker-token (no-store, one active request id) → server-
authoritative download (only ``file_id`` is trusted) → unified ingestion.
Covered: request_id one-shot binding (stale/duplicate can never replace the
active dataset), metadata authority, trashed/canDownload, MIME + suffix
allowlist, declared + actual-byte caps, Google-native rejection, cancellation
cleanup, temp-artifact hygiene, and the **no-upload boundary**.
"""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services import drive_service

# Phase 5 OAuth callbacks 303-redirect to the React frontend — never follow
# them in contract tests (the browser handles the redirect, not the API).
client = TestClient(app, follow_redirects=False)

FAKE_CREDS = {
    "token": "test-access-token",
    "refresh_token": "test-refresh-token",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "test-client",
    "client_secret": "test-secret",
    "scopes": ["https://www.googleapis.com/auth/drive.file"],
    "expiry": None,
}

CSV_CONTENT = b"date,sessions,totalUsers\n2026-01-01,10,8\n2026-01-02,12,9\n"

SUCCESS_META = {
    "id": "drive-file-1",
    "name": "sessions.csv",
    "mimeType": "text/csv",
    "size": str(len(CSV_CONTENT)),
    "md5Checksum": "abc",
    "trashed": False,
    "capabilities": {"canDownload": True},
}


class FakeDriveService:
    def __init__(self, metadata: dict, content: bytes = CSV_CONTENT) -> None:
        self._files = SimpleNamespace(
            get=lambda fileId, fields: SimpleNamespace(execute=lambda: dict(metadata)),
            get_media=lambda fileId: SimpleNamespace(_content=content),
        )

    def files(self):
        return self._files


class FakeMediaDownloader:
    """Stand-in for MediaIoBaseDownload: writes content once, then done."""

    def __init__(self, fd, request, chunksize=262144) -> None:
        self.fd = fd
        self.request = request
        self._sent = False

    def next_chunk(self):
        if not self._sent:
            self._sent = True
            self.fd.write(self.request._content)
            return (None, False)
        return (None, True)


@pytest.fixture(autouse=True)
def _fake_google(monkeypatch):
    """Point the route's client builder + downloader at fakes (no network)."""
    monkeypatch.setattr(drive_service, "MediaIoBaseDownload", FakeMediaDownloader)
    monkeypatch.setattr(
        "api.services.drive_service.get_valid_access_token",
        lambda creds: ("test-access-token", "2026-08-06T12:00:00Z"),
    )


def _connect_drive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mocked drive.file OAuth flow; TestClient jar holds the session."""
    resp = client.post("/api/v1/ga4/connect", json={"connection": "drive"})
    assert resp.status_code == 200
    state = parse_qs(urlparse(resp.json()["authorization_url"]).query)["state"][0]
    monkeypatch.setattr(
        "api.routes.ga4.exchange_code",
        lambda **kwargs: dict(FAKE_CREDS),
    )
    resp = client.get(f"/api/v1/ga4/callback?code=test-code&state={state}")
    assert resp.status_code == 303
    assert "status=success" in resp.headers["location"]


def _pick_request_id(monkeypatch: pytest.MonkeyPatch, metadata=None, content=CSV_CONTENT) -> str:
    """Establish a drive connection + one active picker request."""
    monkeypatch.setattr(
        "api.routes.drive.build_drive_service",
        lambda creds: FakeDriveService(metadata or SUCCESS_META, content),
    )
    resp = client.post("/api/v1/drive/picker-token")
    assert resp.status_code == 200
    return resp.json()["request_id"]


# ── Status / picker-token ──────────────────────────────────────────────────


def test_status_not_configured(oauth_settings) -> None:
    assert client.get("/api/v1/drive/status").json() == {"configured": False}


def test_status_after_connect(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    assert client.get("/api/v1/drive/status").json() == {"configured": True}


def test_picker_token_requires_connection_409(oauth_settings) -> None:
    resp = client.post("/api/v1/drive/picker-token")
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "drive_connection_required"


def test_picker_token_jit_no_store_headers(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    resp = client.post("/api/v1/drive/picker-token")
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"] == "test-access-token"
    assert body["expires_at"] == "2026-08-06T12:00:00Z"
    assert body["app_id"] == "123456789012"  # Cloud project number (setAppId)
    assert body["request_id"]
    assert resp.headers["cache-control"] == "no-store"
    assert resp.headers["pragma"] == "no-cache"


def test_picker_token_origin_rejected(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    resp = client.post(
        "/api/v1/drive/picker-token",
        headers={"Origin": "https://evil.example"},
    )
    assert resp.status_code == 403


# ── Download — request_id one-shot binding ─────────────────────────────────


def test_download_requires_active_picker_request(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    resp = client.post(
        "/api/v1/drive/download",
        json={"request_id": "never-issued", "file_id": "f1"},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "stale_picker_request"


def test_download_success(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    request_id = _pick_request_id(monkeypatch)
    resp = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-1"},
    )
    assert resp.status_code == 201
    dataset = resp.json()["dataset"]
    assert dataset["source"] == "drive"
    assert dataset["filename"] == "sessions.csv"  # server-fetched, client ignored
    assert dataset["row_count"] == 2


def test_download_ignores_client_metadata(oauth_settings, monkeypatch) -> None:
    """Forged filename/MIME/size never reaches ingestion — server metadata wins."""
    _connect_drive(monkeypatch)
    request_id = _pick_request_id(monkeypatch)
    resp = client.post(
        "/api/v1/drive/download",
        json={
            "request_id": request_id,
            "file_id": "drive-file-1",
            "filename": "evil.exe",
            "mime_type": "application/x-msdownload",
            "size_bytes": 999999999,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["dataset"]["filename"] == "sessions.csv"


def test_download_duplicate_request_id_cannot_replace_dataset(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    request_id = _pick_request_id(monkeypatch)
    first = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-1"},
    )
    assert first.status_code == 201
    first_filename = first.json()["dataset"]["filename"]
    # Second selection with the SAME (now consumed) request id → typed error;
    # the active dataset is preserved.
    second = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-2"},
    )
    assert second.status_code == 409
    assert second.json()["detail"]["code"] == "stale_picker_request"
    assert client.get("/api/v1/data/context").json()["filename"] == first_filename


def test_download_parse_failure_preserves_dataset(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    # First: a valid import becomes the active dataset.
    request_id = _pick_request_id(monkeypatch)
    assert (
        client.post(
            "/api/v1/drive/download",
            json={"request_id": request_id, "file_id": "drive-file-1"},
        ).status_code
        == 201
    )
    # Second: a connection with unparseable CSV (ragged columns) fails; the
    # old dataset stays active.
    request_id = _pick_request_id(monkeypatch, content=b"a,b\n1\n2,3\n4,5,6\n")
    resp = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-2"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "drive_parse_failed"
    assert client.get("/api/v1/data/context").json()["filename"] == "sessions.csv"


def test_download_cancellation_cleanup(oauth_settings, monkeypatch) -> None:
    """Transfer aborted (too_large) → temp artifact deleted, old dataset active."""
    _connect_drive(monkeypatch)
    request_id = _pick_request_id(monkeypatch, content=CSV_CONTENT)
    # A successful import becomes the baseline dataset (consumes the request).
    first = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-1"},
    )
    assert first.status_code == 201

    created: list[str] = []
    real_ntf = drive_service.NamedTemporaryFile

    def tracking(*args, **kwargs):
        temp = real_ntf(*args, **kwargs)
        created.append(temp.name)
        return temp

    monkeypatch.setattr(drive_service, "NamedTemporaryFile", tracking)
    request_id = _pick_request_id(monkeypatch, content=b"x" * 4096)

    # Abort mid-transfer via the actual-byte counter (tiny max_ingest_bytes).
    settings = oauth_settings
    original = settings.max_ingest_bytes
    settings.max_ingest_bytes = 10
    try:
        resp = client.post(
            "/api/v1/drive/download",
            json={"request_id": request_id, "file_id": "drive-file-2"},
        )
    finally:
        settings.max_ingest_bytes = original
    assert resp.status_code == 413
    assert resp.json()["detail"]["code"] == "too_large"
    # No orphaned temp artifacts.
    import os

    for path in created:
        assert not os.path.exists(path)
    # Prior dataset remains active.
    assert client.get("/api/v1/data/context").json()["filename"] == "sessions.csv"


# ── Download — metadata authority / caps ───────────────────────────────────


@pytest.mark.parametrize(
    ("meta", "expected_status", "expected_code"),
    [
        ({**SUCCESS_META, "trashed": True}, 410, "file_not_available"),
        (
            {**SUCCESS_META, "capabilities": {"canDownload": False}},
            403,
            "download_not_allowed",
        ),
        (
            {**SUCCESS_META, "mimeType": "application/vnd.google-apps.spreadsheet"},
            422,
            "workspace_export_required",
        ),
        ({**SUCCESS_META, "mimeType": "application/pdf"}, 415, "unsupported_type"),
        ({**SUCCESS_META, "name": "notes.txt", "mimeType": "text/csv"}, 415, "unsupported_type"),
        ({**SUCCESS_META, "size": str(200 * 1024 * 1024)}, 413, "too_large"),
    ],
)
def test_download_typed_rejections(
    oauth_settings, monkeypatch, meta, expected_status, expected_code
) -> None:
    _connect_drive(monkeypatch)
    request_id = _pick_request_id(monkeypatch, metadata=meta)
    resp = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-1"},
    )
    assert resp.status_code == expected_status
    assert resp.json()["detail"]["code"] == expected_code


def test_download_empty_file_400(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    request_id = _pick_request_id(monkeypatch, content=b"")
    resp = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-1"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "empty_file"


def test_download_temp_artifact_deleted_after_success(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    created: list[str] = []
    real_ntf = drive_service.NamedTemporaryFile

    def tracking(*args, **kwargs):
        temp = real_ntf(*args, **kwargs)
        created.append(temp.name)
        return temp

    monkeypatch.setattr(drive_service, "NamedTemporaryFile", tracking)
    request_id = _pick_request_id(monkeypatch)
    assert (
        client.post(
            "/api/v1/drive/download",
            json={"request_id": request_id, "file_id": "drive-file-1"},
        ).status_code
        == 201
    )
    import os

    for path in created:
        assert not os.path.exists(path)


# ── No-upload boundary (Phase 5 is download-and-ingest only) ───────────────


def test_download_should_cancel_aborts_and_self_cleans(monkeypatch) -> None:
    """A cancelled/abandoned transfer aborts at the next chunk and the temp
    artifact self-cleans — no orphaned client data (review fix: cancellation)."""
    import os

    created: list[str] = []
    real_ntf = drive_service.NamedTemporaryFile

    def tracking(*args, **kwargs):
        temp = real_ntf(*args, **kwargs)
        created.append(temp.name)
        return temp

    monkeypatch.setattr(drive_service, "NamedTemporaryFile", tracking)
    service = FakeDriveService(SUCCESS_META, b"x" * 100)

    with pytest.raises(drive_service.DriveImportError) as excinfo:
        drive_service.download_drive_to_tempfile(
            service,
            file_id="f",
            max_bytes=10_000,
            should_cancel=lambda: True,
        )
    assert excinfo.value.code == "download_failed"
    for path in created:
        assert not os.path.exists(path)


def test_download_origin_rejected(oauth_settings, monkeypatch) -> None:
    # drive/download is an unsafe POST — foreign Origin is rejected (Task 4).
    _connect_drive(monkeypatch)
    request_id = _pick_request_id(monkeypatch)
    resp = client.post(
        "/api/v1/drive/download",
        json={"request_id": request_id, "file_id": "drive-file-1"},
        headers={"Origin": "https://evil.example"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "csrf_origin_rejected"


def test_no_drive_upload_endpoints(oauth_settings) -> None:
    for path in ("/api/v1/drive/upload", "/api/v1/drive/export", "/api/v1/drive/files"):
        assert client.post(path, json={}).status_code == 404


# ── Clear Data retains OAuth connection ────────────────────────────────────


def test_clear_data_retains_oauth_connections(oauth_settings, monkeypatch) -> None:
    _connect_drive(monkeypatch)
    # Also establish a GA4 connection (D2 — two separate consents).
    resp = client.post("/api/v1/ga4/connect", json={"connection": "ga4"})
    state = parse_qs(urlparse(resp.json()["authorization_url"]).query)["state"][0]
    monkeypatch.setattr(
        "api.routes.ga4.exchange_code",
        lambda **kwargs: {
            **FAKE_CREDS,
            "scopes": ["https://www.googleapis.com/auth/analytics.readonly"],
        },
    )
    assert client.get(f"/api/v1/ga4/callback?code=test-code&state={state}").status_code == 303

    request_id = _pick_request_id(monkeypatch)
    assert (
        client.post(
            "/api/v1/drive/download",
            json={"request_id": request_id, "file_id": "drive-file-1"},
        ).status_code
        == 201
    )

    resp = client.post("/api/v1/data/clear")
    assert resp.status_code == 200
    # Dataset-derived state cleared…
    assert client.get("/api/v1/data/context").status_code == 409
    # …OAuth connections retained (retention policy: connection retained).
    assert client.get("/api/v1/ga4/status").json() == {"connected": True}
    assert client.get("/api/v1/drive/status").json() == {"configured": True}
