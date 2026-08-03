"""ONE-TIME, LOCAL-ONLY: save a real Google OAuth session for E2E tests.

Run this interactively from the project root:

    E2E_REAL_DRIVE=1 python tests/e2e/auth_setup.py

It launches a headed Chromium browser pointed at the running Streamlit app
(default ``http://localhost:8501``).  You manually sign into Google and
complete OAuth + Drive consent.  Once the sidebar shows the Drive Import
button, the script saves cookies/localStorage to
``tests/e2e/.auth/session.json`` and exits.

IMPORTANT:
- NEVER run this in CI.
- NEVER commit ``tests/e2e/.auth/session.json``.
- The saved file contains live session cookies equivalent to your password.
- If the session expires, re-run this script to refresh it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Guard: only import Playwright when this script is run directly ──────
try:
    from playwright.sync_api import sync_playwright  # noqa: I202
except ImportError:
    print(
        "playwright is not installed. Run: pip install playwright && python -m playwright install chromium"
    )
    sys.exit(1)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")
SESSION_PATH = Path(__file__).resolve().parent / ".auth" / "session.json"
LOGIN_TIMEOUT_MS = 120_000  # generous: you need time to click through Google OAuth


def _wait_for_import_button(page, timeout_ms: int = LOGIN_TIMEOUT_MS) -> None:
    """Poll until the Drive Import button appears in the sidebar."""
    print("⏳ Waiting for Google OAuth sign-in + Drive Import button...")

    import time

    deadline = time.monotonic() + (timeout_ms / 1000)
    while time.monotonic() < deadline:
        try:
            sidebar = page.locator('[data-testid="stSidebar"]')
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            if btn.is_visible():
                print("✅ Drive Import button visible — authentication successful.")
                return
        except Exception:
            pass
        time.sleep(1)

    raise TimeoutError(
        f"Drive Import button did not appear within {timeout_ms // 1000}s. "
        "Did you complete Google OAuth sign-in and Drive consent?"
    )


def main() -> None:
    """Run the one-time interactive auth setup."""

    # ── Pre-flight checks ──────────────────────────────────────────────
    if not os.getenv("E2E_REAL_DRIVE"):
        print("❌ Set E2E_REAL_DRIVE=1 to confirm you want to create a real session.")
        sys.exit(1)

    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"🌐 Opening {BASE_URL} in headed Chromium...")
    print("   Sign into Google when the OAuth redirect appears.")
    print("   Once the sidebar shows 'Import from Google Drive', the script finishes.\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # Navigate to the app — Streamlit may trigger an OAuth redirect.
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)

        # Hand control to you: complete Google sign-in in the browser window.
        print("🔐 Complete Google OAuth in the browser window that opened.")
        print("   The script will detect the Drive Import button automatically.\n")
        page.pause()

        # After you resume (click "Resume" in Playwright Inspector or close it),
        # wait for the authenticated sidebar state.
        _wait_for_import_button(page)

        # Save the authenticated session for reuse by the E2E test suite.
        context.storage_state(path=str(SESSION_PATH))
        print(f"\n💾 Session saved to {SESSION_PATH}")

        browser.close()

    print("\n🎉 Done. You can now run:")
    print("   E2E_REAL_DRIVE=1 python -m pytest tests/e2e/test_drive_picker_e2e.py -v")
    print(f"\n⚠️  The file {SESSION_PATH} contains LIVE session cookies.")
    print("   Never commit it. It is already gitignored.")


if __name__ == "__main__":
    main()
