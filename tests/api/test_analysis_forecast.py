"""Contract tests: POST /api/v1/analysis/forecast (spec Task 9).

Deterministic server-side projection — NO Gemini, no AI quota, no ai_lock.
"""

from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _csv_bytes() -> bytes:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [f"2026-01-{d:02d}" for d in range(1, 11)]  # 10 days — ≥7 required
            ),
            "sessions": [10, 12, 11, 14, 15, 14, 16, 17, 16, 18],
            "users": [8, 9, 8, 10, 11, 10, 12, 13, 12, 14],
        }
    )
    return df.to_csv(index=False).encode()


def _upload(c: TestClient) -> None:
    resp = c.post("/api/v1/upload", files={"file": ("sample.csv", _csv_bytes(), "text/csv")})
    assert resp.status_code == 201


def test_forecast_requires_dataset() -> None:
    fresh = TestClient(app)
    resp = fresh.post("/api/v1/analysis/forecast", json={"metric_col": "sessions"})
    assert resp.status_code == 409


def test_forecast_auto_detects_date_column() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post(
        "/api/v1/analysis/forecast",
        json={"metric_col": "sessions", "periods": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["insufficient_data"] is False
    assert len(body["forecast_points"]) == 5
    assert body["metric_col"] == "sessions"
    assert body["periods"] == 5
    assert body["summary"]
    point = body["forecast_points"][0]
    assert set(point) == {"date", "value", "lower", "upper"}


def test_forecast_explicit_date_col() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post(
        "/api/v1/analysis/forecast",
        json={"date_col": "date", "metric_col": "users", "periods": 3},
    )
    assert resp.status_code == 200
    assert len(resp.json()["forecast_points"]) == 3


def test_forecast_unknown_metric_422() -> None:
    c = TestClient(app)
    _upload(c)
    resp = c.post("/api/v1/analysis/forecast", json={"metric_col": "nope"})
    assert resp.status_code == 422


def test_forecast_insufficient_data_flag() -> None:
    df = pd.DataFrame({"date": ["2026-01-01"], "sessions": [5]})
    c = TestClient(app)
    resp = c.post(
        "/api/v1/upload",
        files={"file": ("one-row.csv", df.to_csv(index=False).encode(), "text/csv")},
    )
    assert resp.status_code == 201
    resp = c.post("/api/v1/analysis/forecast", json={"metric_col": "sessions"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["insufficient_data"] is True
    assert body["forecast_points"] == []
