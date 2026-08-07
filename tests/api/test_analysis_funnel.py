"""Contract tests: POST /api/v1/analysis/funnel (spec Task 9).

Deterministic page-path aggregation — NO Gemini, no AI quota, no ai_lock.
"""

from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _csv_bytes() -> bytes:
    df = pd.DataFrame(
        {
            "page_path": ["/home", "/product", "/cart", "/checkout", "/home"],
            "sessions": [10, 5, 3, 2, 8],
            "users": [8, 4, 2, 1, 6],
        }
    )
    return df.to_csv(index=False).encode()


def _upload(c: TestClient) -> None:
    resp = c.post("/api/v1/upload", files={"file": ("sample.csv", _csv_bytes(), "text/csv")})
    assert resp.status_code == 201


def test_funnel_requires_dataset() -> None:
    fresh = TestClient(app)
    resp = fresh.post(
        "/api/v1/analysis/funnel",
        json={"metric_col": "sessions", "steps": ["/home", "/product"]},
    )
    assert resp.status_code == 409


def test_funnel_auto_detects_page_column() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post(
        "/api/v1/analysis/funnel",
        json={"metric_col": "sessions", "steps": ["/home", "/product", "/cart"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["steps"] == ["/home", "/product", "/cart"]
    assert len(body["values"]) == 3
    assert body["values"][0] > body["values"][1]  # 18 > 5 — dropoff ordering


def test_funnel_explicit_page_col() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post(
        "/api/v1/analysis/funnel",
        json={
            "page_col": "page_path",
            "metric_col": "users",
            "steps": ["/home", "/checkout"],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["steps"] == ["/home", "/checkout"]


def test_funnel_unknown_metric_422() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post(
        "/api/v1/analysis/funnel",
        json={"metric_col": "nope", "steps": ["/home", "/product"]},
    )
    assert resp.status_code == 422


def test_funnel_missing_page_column_422() -> None:
    df = pd.DataFrame({"sessions": [10, 5]})
    c = TestClient(app)
    resp = c.post(
        "/api/v1/upload",
        files={"file": ("nopage.csv", df.to_csv(index=False).encode(), "text/csv")},
    )
    assert resp.status_code == 201
    resp = c.post(
        "/api/v1/analysis/funnel",
        json={"metric_col": "sessions", "steps": ["/home", "/product"]},
    )
    assert resp.status_code == 422
    assert "page" in resp.json()["detail"].lower()
