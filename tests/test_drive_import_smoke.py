"""Phase 3.2: Playwright smoke test for Drive Import — app-controlled surfaces only.

Phase 3.2a (platform smoke): app loads, sidebar visible, no credential leaks.
Phase 3.2b (drive-import controlled-state): import-button visibility, on-demand
component rendering, ready/cancel/error UI, theme sync, duplicate protection.
Phase 3.2c (dialog acceptance — interstitial PR 2): the Picker renders
inside st.dialog per plans/00-sprints/🔵 interstitial-ui-polish-spec.md
§5.6. These five tests were added before the PR 2 code (2026-08-03) and
went permanent with it: dialog-open, close-on-cancel, close-on-picked,
theme-in-dialog (F3), and error-stays-open (D5).
Phase 3.2d (app-level theme-sync regression): the sidebar theme toggle
must set html[data-theme] in the top-level document so the
[data-theme="light"] override block actually engages. Guards the
st.html(unsafe_allow_javascript=True) fix in utils/styles.py (Streamlit
strips <script> from st.html payloads by default).

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
import re
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest

try:
    from playwright.sync_api import Page, expect, sync_playwright

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

    # Guard against parent-env bleed: if the test suite was invoked with
    # DRIVE_PICKER_TEST_MODE=1 in the shell (the documented way to run this
    # module), os.environ.copy() would inherit it into a non-test-mode
    # server, silently enabling the test seam and defeating the
    # unauthenticated-state assertions below.  Explicitly strip it unless
    # this server is supposed to run in test mode.
    if test_mode:
        env["DRIVE_PICKER_TEST_MODE"] = "1"
    else:
        env.pop("DRIVE_PICKER_TEST_MODE", None)

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
            btn_count = sidebar.get_by_role("button", name="Import from Google Drive").count()
            assert btn_count == 0, "Import button should be hidden when not authenticated"
            assert (
                "Google Drive Import" not in sidebar.inner_text()
            ), "Drive Import section should not render when not authenticated"


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
        """Error seam: the sidebar Import button stays present and enabled.

        D5 keeps the dialog open on error, so this asserts button presence
        (Playwright visibility ignores backdrop occlusion) while
        ``test_error_state_keeps_dialog_open`` owns the in-dialog contract.
        """
        url = f"{streamlit_server_test_mode}?picker_seam=error"
        with _page(url) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            _click_import(page)
            # After error, the button should still be present and enabled.
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            btn.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            assert btn.is_visible(), "Import button should be present after error"
            assert btn.is_enabled(), "Import button should be enabled after error"


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
            # Click twice in rapid succession. The second click is forced:
            # once the dialog opens (PR 2), its full-viewport backdrop
            # covers the sidebar button — force bypasses the occlusion
            # actionability check so we can still prove no double-activation.
            btn.click()
            btn.click(force=True)
            page.wait_for_timeout(IFRAME_WAIT)
            # Exactly one dialog and one Picker iframe, not two of either.
            assert (
                page.locator('[data-testid="stDialog"]').count() == 1
            ), "Expected exactly one dialog after double-click"
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


class TestAppLevelThemeSync:
    """Theme-sync root-cause regression: the app-level toggle flips
    html[data-theme] so the [data-theme="light"] CSS rules engage.

    Before the fix, st.html() silently dropped THEME_SYNC_JS (Streamlit
    ignores <script> unless unsafe_allow_javascript=True), so data-theme
    never reached <html> and every [data-theme="light"] override stayed
    inert — only the preemptive page background flipped.
    """

    def test_toggle_flips_html_data_theme(self, streamlit_server_test_mode):
        with _page(streamlit_server_test_mode) as page:
            # The sync script must have run by the time the sidebar renders.
            page.locator("html[data-theme]").wait_for(state="attached", timeout=SIDEBAR_WAIT)
            initial = page.locator("html").get_attribute("data-theme")
            assert initial in ("dark", "light"), f"Unexpected initial data-theme {initial!r}"
            toggle = page.locator('[data-testid="stSidebar"]').get_by_role(
                "button", name=re.compile("Light Mode|Dark Mode")
            )
            toggle.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            toggle.click()
            expected = "light" if initial == "dark" else "dark"
            expect(page.locator("html")).to_have_attribute("data-theme", expected, timeout=10_000)


# ══════════════════════════════════════════════════════════════════════════
# Phase 3.2c: Dialog acceptance tests (interstitial PR 2 — spec §5.6)
# Added 2026-08-03 before the PR 2 code landed; permanent since PR 2.
# ══════════════════════════════════════════════════════════════════════════


class TestDriveImportDialogClose:
    """Cancel/picked seams leave no dialog open.

    Real guards for the dialog-close contract: the cancel seam simulates
    Picker cancel, the picked seam simulates a successful selection —
    both must leave no dialog behind and reset the sidebar button.
    """

    def test_dialog_closes_on_cancel_seam(self, streamlit_server_test_mode):
        url = f"{streamlit_server_test_mode}?picker_seam=cancel"
        with _page(url) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            _click_import(page)
            page.wait_for_timeout(2000)
            assert (
                page.locator('[data-testid="stDialog"]').count() == 0
            ), "Dialog should be closed after cancel seam"
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            btn.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            assert btn.is_visible(), "Import button should be visible after cancel"
            assert btn.is_enabled(), "Import button should be enabled after cancel"

    def test_dialog_closes_after_picked_seam(self, streamlit_server_test_mode):
        url = f"{streamlit_server_test_mode}?picker_seam=picked"
        with _page(url) as page:
            sidebar = page.locator('[data-testid="stSidebar"]')
            _click_import(page)
            page.wait_for_timeout(2000)
            assert (
                page.locator('[data-testid="stDialog"]').count() == 0
            ), "Dialog should be closed after picked seam (success path)"
            btn = sidebar.get_by_role("button", name="Import from Google Drive")
            btn.wait_for(state="visible", timeout=SIDEBAR_WAIT)
            assert btn.is_visible(), "Import button should be visible after import"
            assert btn.is_enabled(), "Import button should be enabled after import"


class TestDriveImportDialog:
    """Dialog behaviors implemented by PR 2 (previously strict-xfail).

    Permanent acceptance tests: the dialog opens on Import click with the
    Picker iframe inside; the in-dialog theme control (F3) flips the
    iframe's data-theme without closing the dialog; the error seam renders
    st.error inside the dialog and keeps it open for retry (D5).
    """

    def test_dialog_opens_on_click(self, streamlit_server_test_mode):
        """stDialog appears after clicking Import, with the Picker iframe inside."""
        with _page(streamlit_server_test_mode) as page:
            _click_import(page)
            dlg = page.locator('[data-testid="stDialog"]')
            dlg.wait_for(state="visible", timeout=15_000)
            assert dlg.is_visible(), "Expected st.dialog to open after clicking Import"
            inside = dlg.locator('iframe[title*="drive_picker_transport"]')
            inside.wait_for(state="attached", timeout=10_000)
            assert inside.count() == 1, "Expected exactly one Picker iframe inside the dialog"

    def test_theme_propagates_to_dialog_component(self, streamlit_server_test_mode):
        """In-dialog theme control flips iframe data-theme without closing the dialog (F3)."""
        with _page(streamlit_server_test_mode) as page:
            _click_import(page)
            dlg = page.locator('[data-testid="stDialog"]')
            dlg.wait_for(state="visible", timeout=15_000)
            body0 = dlg.frame_locator('iframe[title*="drive_picker_transport"]').locator("body")
            body0.wait_for(state="attached", timeout=10_000)
            theme0 = body0.get_attribute("data-theme")
            assert theme0 in ("dark", "light"), f"Unexpected initial theme {theme0!r}"
            # F3 decision: the in-dialog theme control (a button named
            # *Light Mode*/*Dark Mode* inside the dialog, reusing
            # _render_theme_toggle logic). The sidebar toggle is
            # backdrop-blocked while the dialog is open.
            toggle = dlg.get_by_role("button", name=re.compile("Light Mode|Dark Mode"))
            toggle.wait_for(state="visible", timeout=10_000)
            toggle.click()
            # Pattern (b): the full rerun must keep the dialog open.
            dlg.wait_for(state="visible", timeout=15_000)
            assert dlg.is_visible(), "Dialog closed after theme toggle — pattern (b) broken"
            # Poll for the iframe theme flip instead of a fixed sleep —
            # robust on slow CI once this test goes permanent post-PR-2.
            expected = "light" if theme0 == "dark" else "dark"
            body1 = dlg.frame_locator('iframe[title*="drive_picker_transport"]').locator("body")
            expect(body1).to_have_attribute("data-theme", expected, timeout=10_000)

    def test_error_state_keeps_dialog_open(self, streamlit_server_test_mode):
        """Error seam: st.error renders inside the dialog and the dialog stays open (D5)."""
        url = f"{streamlit_server_test_mode}?picker_seam=error"
        with _page(url) as page:
            _click_import(page)
            dlg = page.locator('[data-testid="stDialog"]')
            dlg.wait_for(state="visible", timeout=15_000)
            # D5: failed import renders st.error inside the dialog and keeps
            # it open for retry — verified via the stAlert surface.
            alert = dlg.locator('[data-testid="stAlert"]')
            alert.wait_for(state="visible", timeout=10_000)
            assert alert.is_visible(), "Expected st.error inside the dialog after failed import"
            assert dlg.is_visible(), "Dialog should stay open on error (retry in place)"
