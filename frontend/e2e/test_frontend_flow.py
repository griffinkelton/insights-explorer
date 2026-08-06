"""Phase 4 Task 9 — first-slice Playwright user-flow gate.

Serves the real stack: ``uvicorn api.main:app --port 8000`` + ``npm run dev``
(frontend at 5173, ``/api`` proxied to 8000), then drives the upload →
preview → quality → Clear Data flow with cookie-aware requests (the session
cookie set by FastAPI must round-trip through the proxied origin).

Uses ``sync_playwright`` directly (no pytest-playwright plugin). Run via the
dedicated CI job or locally with the two dev processes up.
"""

import csv
import os
import pathlib
import tempfile

import pytest

playwright_module = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_module.sync_playwright

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173")


def _sample_csv() -> pathlib.Path:
    """Deterministic small CSV with a date column + metrics (parses cleanly)."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", prefix="ie-flow-", delete=False)
    rows = [
        {"date": f"2026-01-{i + 1:02d}", "sessions": 100 + i, "channel": "organic"}
        for i in range(10)
    ]
    writer = csv.DictWriter(f, fieldnames=["date", "sessions", "channel"])
    writer.writeheader()
    writer.writerows(rows)
    f.close()
    return pathlib.Path(f.name)


def test_first_slice_flow() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors: list[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        try:
            page.goto(FRONTEND_URL, wait_until="networkidle")

            # Empty state renders the upload affordance.
            hero = page.get_by_role("heading", name="Explore your analytics data")
            hero.wait_for(state="visible")

            # Upload through the hidden file input.
            with page.expect_file_chooser() as chooser_info:
                page.get_by_label("Upload a CSV, XLSX, or XLS file").click()
            chooser_info.value.set_files(str(_sample_csv()))

            # Preview + quality hydrate from the API.
            page.get_by_text("Data preview", exact=True).wait_for(state="visible")
            page.get_by_text("Data quality", exact=True).wait_for(state="visible")
            page.get_by_text("sessions", exact=True).first.wait_for(state="visible")

            # AI panel is mounted once a dataset is ready (Wave 4B).
            page.get_by_text("Ask about your data", exact=True).wait_for(state="visible")

            # Clear Data returns to the empty state.
            page.get_by_role("button", name="Clear Data").click()
            page.get_by_role("heading", name="Explore your analytics data").wait_for(
                state="visible"
            )
            page.get_by_text("Data preview", exact=True).wait_for(state="hidden")
        finally:
            browser.close()

        # No console errors unless expected (Task 9 assert 3).
        assert not errors, f"console errors during the flow: {errors[:5]}"
