"""Contract tests: POST /api/v1/upload (spec §12)."""

from __future__ import annotations

import io

import pandas as pd
from fastapi.testclient import TestClient

from api.config import get_settings
from api.main import app

client = TestClient(app)

LIMIT = get_settings().max_browser_upload_bytes


def _csv_bytes() -> bytes:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "page_path": ["/", "/about", "/contact"],
            "sessions": [10, 5, 2],
            "users": [8, 4, 2],
        }
    )
    return df.to_csv(index=False).encode()


def test_upload_csv_201_with_context() -> None:
    resp = client.post("/api/v1/upload", files={"file": ("sample.csv", _csv_bytes(), "text/csv")})
    assert resp.status_code == 201
    body = resp.json()
    dataset = body["dataset"]
    assert dataset["source"] == "upload"
    assert dataset["filename"] == "sample.csv"
    assert dataset["row_count"] == 3
    assert dataset["columns"]
    # date_range is present; start may be null because the Phase 1 adapter does
    # not infer dates on read (mirrors utils/data_loader.load_file) — Phase 2
    # decoupling decides date-typing policy.
    assert "date_range" in dataset


def test_upload_xlsx_201() -> None:
    buf = io.BytesIO()
    pd.DataFrame({"a": [1, 2]}).to_excel(buf, index=False)
    resp = client.post(
        "/api/v1/upload",
        files={
            "file": (
                "book.xlsx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 201


def test_upload_bad_suffix_415() -> None:
    resp = client.post("/api/v1/upload", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert resp.status_code == 415
    assert resp.json()["detail"] == "Upload a CSV, XLSX, or XLS file."


def test_upload_empty_400() -> None:
    resp = client.post("/api/v1/upload", files={"file": ("empty.csv", b"", "text/csv")})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Uploaded file is empty."


def test_upload_over_25mb_413() -> None:
    # Just over the locked cap — must reject during the bounded read.
    over = b"a" * (LIMIT + 1)
    resp = client.post("/api/v1/upload", files={"file": ("big.csv", over, "text/csv")})
    assert resp.status_code == 413
    assert (
        resp.json()["detail"]
        == "Uploaded file exceeds the 25 MB browser limit. Use a Drive import or a smaller file."
    )


def test_upload_at_cap_is_not_rejected_by_size_check() -> None:
    # Exactly at the cap passes the size gate: the check is `total > cap`, so
    # an exact-size payload must never be rejected with 413 (it may parse as a
    # single-column CSV, or fail parsing as 422 — never a size rejection).
    exact = b"a" * LIMIT
    resp = client.post("/api/v1/upload", files={"file": ("exact.csv", exact, "text/csv")})
    assert resp.status_code != 413
