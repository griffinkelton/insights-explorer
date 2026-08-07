"""Phase 5 wiring smoke — GA4/Drive affordances fail closed without credentials.

Drives the real stack (``uvicorn api.main:app`` + ``npm run dev``) exactly like
``test_frontend_flow.py``. With no Google credentials configured, the Phase 5
endpoints return the typed ``ga4_not_configured`` error and the UI must surface
it in the empty-state banner without console errors.

This is the **no-credential wiring gate**. The full 12-row Drive E2E matrix +
GA4 connect→pull→preview flow (spec Task 6) require the opt-in live smoke
(``E2E_REAL_GOOGLE=1``, owner-provided sandbox property/account — D4) and are
never run in default CI.
"""

import pytest

playwright_module = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright_module.sync_playwright

FRONTEND_URL = __import__("os").environ.get("FRONTEND_URL", "http://127.0.0.1:5173")


def test_phase5_wiring_smoke() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors: list[str] = []

        def _collect(msg) -> None:
            if msg.type != "error":
                return
            # The typed ga4_not_configured response is an intentional 503 — the
            # banner assertion proves it is that typed error, not a surprise
            # failure. Every other console error still fails the gate.
            if "Failed to load resource: the server responded with a status of 503" in msg.text:
                return
            errors.append(msg.text)

        page.on("console", _collect)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        try:
            page.goto(FRONTEND_URL, wait_until="networkidle")

            # Empty state + Phase 5 sidebar affordances (D5 placement).
            hero = page.get_by_role("heading", name="Explore your analytics data")
            hero.wait_for(state="visible")
            page.get_by_role("button", name="Import a file from Google Drive").wait_for(
                state="visible"
            )
            page.get_by_role("button", name="Connect Google Analytics").wait_for(state="visible")

            # GA4 connect with no credentials → typed ga4_not_configured banner.
            page.get_by_role("button", name="Connect Google Analytics").click()
            banner = page.get_by_test_id("error-banner")
            banner.wait_for(state="visible")
            assert "not configured" in banner.inner_text()

            # Dismiss restores the clean empty state.
            page.get_by_role("button", name="Dismiss error").click()
            banner.wait_for(state="hidden")

            # Import from Drive with no credentials → same fail-closed path.
            page.get_by_role("button", name="Import a file from Google Drive").click()
            banner.wait_for(state="visible")
            assert "not configured" in banner.inner_text()
        finally:
            browser.close()

        assert not errors, f"console errors during the flow: {errors[:5]}"
