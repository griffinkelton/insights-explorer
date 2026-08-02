"""Phase 3.2: Playwright smoke test for Drive Import — app-controlled surfaces only.

Phase 3.2a (platform smoke): app loads, sidebar visible, no credential leaks.
Phase 3.2b (drive-import controlled-state): import-button visibility, on-demand
component rendering, ready/cancel/error UI, theme sync, duplicate protection.

No-secret boundary: these tests never interact with Google's Picker,
never use real OAuth tokens or API keys, and never select real Drive
files.  In test mode (DRIVE_PICKER_TEST_MODE=1), the sidebar bypasses
OAuth checks and uses dummy secrets; a query-param seam
(?picker_seam=none|cancel|error|picked) controls the fake return value.

Requires: ``playwright`` (dev dependency) + ``python -m playwright install chromium``

CI gate: when invoked via the dedicated ``playwright`` CI job, this file
must NOT skip — it must prove the browser environment exists.  When
running under ordinary local ``pytest`` without Playwright installed, a
module-level skip is acceptable.
"""

import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest

try:
    from playwright.sync_api import Page, sync_playwright

    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

# ── Skip policy ────────────────────────────────────────────────────────
_IN_CI = os.getenv("CI", "") == "true" or os.getenv("GITHUB_ACTIONS", "") == "true"

if not _HAS_PLAYWRIGHT and not _IN_CI:
    pytest.skip("playwright not installed", allow_module_level=True)
elif not _HAS_PLAYWRIGHT and _IN_CI:
    raise ImportError(
        "Playwright is required in CI but not importable. "
        "Ensure the CI job runs 'python -m playwright install --with-deps chromium'."
    )


BASE_PORT = 18599
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTUP_TIMEOUT = 45
SIDEBAR_WAIT = 20_000  # ms — generous for Streamlit WebSocket initial render
IFRAME_WAIT = 5_000  # ms — wait for component iframe to appear after click


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_streamlit(port: int, *, test_mode: bool = False) -> subprocess.Popen:
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    if test_mode:
        env["DRIVE_PICKER_TEST_MODE"] = "1"

    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(PROJECT_ROOT / "app.py")],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Streamlit exited early with code {proc.returncode}")
        try:
            import urllib.request

            urllib.request.urlopen(f"http://localhost:{port}/_stcore/health", timeout=2)
            return proc
        except Exception:
            time.sleep(0.5)
    proc.terminate()
    raise TimeoutError(f"Streamlit did not start within {STARTUP_TIMEOUT}s")


def _stop_streamlit(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def streamlit_server():
    port = _find_free_port()
    proc = _start_streamlit(port, test_mode=False)
    try:
        yield f"http://localhost:{port}"
    finally:
        _stop_streamlit(proc)


@pytest.fixture(scope="module")
def streamlit_server_test_mode():
    port = _find_free_port()
    proc = _start_streamlit(port, test_mode=True)
    try:
        yield f"http://localhost:{port}"
    finally:
        _stop_streamlit(proc)


# ── Helpers ─────────────────────────────────────────────────────────────


@contextmanager
def _page(server_url: str) -> Generator[Page, None, None]:
    """Yield a headless Chromium page pointed at *server_url*."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(server_url, wait_until="networkidle", timeout=30_000)
        _wait_for_sidebar(page)
        yield page
        browser.close()


def _wait_for_sidebar(page: Page) -> None:
    """Wait for Streamlit sidebar user-content to have rendered children."""
    page.locator('[data-testid="stSidebar"]').wait_for(state="visible", timeout=10_000)
    page.wait_for_function(
        """() => {
            const el = document.querySelector('[data-testid="stSidebarUserContent"]');
            if (!el) return false;
            const block = el.querySelector('[data-testid="stVerticalBlock"]');
            return block && block.children.length > 0;
        }""",
        timeout=SIDEBAR_WAIT,
    )


def _click_import(page: Page) -> None:
    """Click the Import button, then wait for the iframe to appear."""
    sidebar = page.locator('[data-testid="stSidebar"]')
    btn = sidebar.get_by_role("button", name="Import from Google Drive")
    btn.click()
    page.wait_for_timeout(IFRAME_WAIT)


def _picker_iframes(page: Page) -> list:
    """Return all iframes whose title contains 'drive_picker_transport'."""
    return [
        f
        for f in page.locator("iframe").all()
        if f.get_attribute("title") and "drive_picker_transport" in (f.get_attribute("title") or "")
    ]


# ══════════════════════════════════════════════════════════════════════════
# Phase 3.2a: Platform smoke (no test mode)
# ══════════════════════════════════════════════════════════════════════════


class TestPlatformSmoke:
    """App loads, sidebar visible, no credential-shaped strings in page source."""

    def test_app_loads_without_crash(self, streamlit_server):
        with _page(streamlit_server) as page:
            assert page.url.startswith(streamlit_server)

    def test_sidebar_is_present(self, streamlit_server):
        with _page(streamlit_server) as page:
            assert page.locator('[data-testid="stSidebar"]').is_visible()

    def test_no_credential_leak_in_page_source(self, streamlit_server):
        with _page(streamlit_server) as page:
            html = page.content()
            assert "AIza" not in html, "Possible API key leak in page source"
            assert "ya29" not in html, "Possible OAuth token leak in page source"
            assert "AQ." not in html, "Possible AI Studio key leak in page source"


# ══════════════════════════════════════════════════════════════════════════
# Phase 3.2b: Drive Import controlled-state (test mode)
# ══════════════════════════════════════════════════════════════════════════


class TestDriveImportVisibility:
    """Import button visibility and section rendering."""

    def test_import_button_visible_in_test_mode(self, streamlit_server_test_mode):
        with _page(streamlit_server_test_mode) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            btn.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            assert btn.is_visible(), "Import button not visible in test mode"

    def test_import_section_hidden_without_auth(self, streamlit_server):
        with _page(streamlit_server) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            assert (
                "Google Drive Import" not in sidebar.inner_text()
            ), "Drive Import section should be hidden when not authenticated"


class TestDriveImportOnDemandRender:
    """Component renders only when the user activates it."""

    def test_picker_iframe_not_visible_initially(self, streamlit_server_test_mode):
        with _page(streamlit_server_test_mode) as page:
            assert (
                len(_picker_iframes(page)) == 0
            ), "Picker iframe should not exist before activation"

    def test_picker_iframe_appears_after_click(self, streamlit_server_test_mode):
        with _page(streamlit_server_test_mode) as page:
            _click_import(page)
            assert len(_picker_iframes(page)) > 0, "Expected a Picker iframe after activation"


class TestDriveImportCancelState:
    """Cancel seam: import button resets and Picker iframe is gone."""

    def test_cancel_seam_resets_import_button(self, streamlit_server_test_mode):
        url = f"{streamlit_server_test_mode}?picker_seam=cancel"
        with _page(url) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            _click_import(page)
            # After cancel, the button should reappear and be enabled.
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            btn.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            assert btn.is_visible(), "Import button should be visible after cancel"
            assert btn.is_enabled(), "Import button should be enabled after cancel"

    def test_cancel_seam_removes_picker_iframe(self, streamlit_server_test_mode):
        url = f"{streamlit_server_test_mode}?picker_seam=cancel"
        with _page(url) as page:
            _click_import(page)
            # The Picker iframe should be gone after cancel is processed.
            page.wait_for_timeout(2000)
            assert len(_picker_iframes(page)) == 0, "Picker iframe should be removed after cancel"


class TestDriveImportErrorState:
    """Error seam: component returns None (error), import button resets."""

    def test_error_seam_resets_button(self, streamlit_server_test_mode):
        url = f"{streamlit_server_test_mode}?picker_seam=error"
        with _page(url) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            _click_import(page)
            # After error, the button should reappear.
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            btn.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            assert btn.is_visible(), "Import button should be visible after error"


class TestDriveImportThemeSync:
    """Theme propagation: the Picker iframe body has data-theme set."""

    def test_theme_propagates_to_iframe_body(self, streamlit_server_test_mode):
        with _page(streamlit_server_test_mode) as page:
            _click_import(page)
            picker_frames = _picker_iframes(page)
            assert len(picker_frames) >= 1, "Expected at least one Picker iframe for theme check"
            # The component loads its own HTML; the body should have data-theme.
            body = picker_frames[0].content_frame.locator("body")
            theme = body.get_attribute("data-theme")
            assert theme in (
                "dark",
                "light",
            ), f"Expected body[data-theme] to be 'dark' or 'light', got {theme!r}"


class TestDriveImportDuplicateProtection:
    """Duplicate activation: two rapid clicks do not double-activate."""

    def test_rapid_double_click_produces_one_iframe(self, streamlit_server_test_mode):
        with _page(streamlit_server_test_mode) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            # Click twice in rapid succession.
            btn.click()
            btn.click()
            page.wait_for_timeout(IFRAME_WAIT)
            # There should be exactly one Picker iframe, not two.
            picker_frames = _picker_iframes(page)
            assert (
                len(picker_frames) == 1
            ), f"Expected 1 Picker iframe after double-click, got {len(picker_frames)}"


class TestDriveImportPickedSeam:
    """Query-param seam: ?picker_seam=picked simulates file selection."""

    def test_picked_seam_clears_active_state(self, streamlit_server_test_mode):
        url = f"{streamlit_server_test_mode}?picker_seam=picked"
        with _page(url) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            _click_import(page)
            # After a "picked" seam, the picker is deactivated and the
            # import button reappears.
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            btn.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            assert btn.is_visible(), "Import button should reappear after seam-pick completes"


class TestDriveImportNoCredentialLeakTestMode:
    """Even in test mode, no credential-shaped strings leak."""

    def test_no_credential_leak_in_test_mode(self, streamlit_server_test_mode):
        with _page(streamlit_server_test_mode) as page:
            html = page.content()
            assert "AIza" not in html, "Possible API key leak in test mode"
            assert "ya29" not in html, "Possible OAuth token leak in test mode"
            assert "AQ." not in html, "Possible AI Studio key leak in test mode"
