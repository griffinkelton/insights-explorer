"""Phase 3.2: Playwright smoke test for Drive Import — app-controlled surfaces only.

No-secret boundary: these tests never interact with Google's Picker,
never use real OAuth tokens or API keys, and never select real Drive
files. They verify only the app's own UI renders correctly and that no
credential-shaped strings leak into the page source.

Requires: ``playwright`` (dev dependency) + ``python -m playwright install chromium``
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    pytest.skip("playwright not installed", allow_module_level=True)


BASE_PORT = 18599
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STARTUP_TIMEOUT = 30  # seconds


def _find_free_port() -> int:
    """Return an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_streamlit(port: int) -> subprocess.Popen:
    """Start a headless Streamlit server on *port*."""
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(PROJECT_ROOT / "app.py")],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Poll /healthz until Streamlit is ready (or timeout).
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
    """Terminate the Streamlit server process."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="module")
def streamlit_server():
    """Module fixture: starts Streamlit on a free port, yields URL, then stops it."""
    port = _find_free_port()
    proc = _start_streamlit(port)
    try:
        yield f"http://localhost:{port}"
    finally:
        _stop_streamlit(proc)


class TestDriveImportSmoke:
    """App-controlled-surface smoke tests — no Google interaction."""

    def test_app_loads_without_crash(self, streamlit_server):
        """App serves a 200 response."""
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            resp = page.goto(streamlit_server, wait_until="domcontentloaded", timeout=30_000)
            assert resp is not None
            assert resp.ok, f"Expected 2xx, got {resp.status}"
            browser.close()

    def test_sidebar_is_present(self, streamlit_server):
        """Sidebar element exists and is visible."""
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(streamlit_server, wait_until="networkidle", timeout=30_000)

            sidebar = page.locator('[data-testid="stSidebar"]')
            sidebar.wait_for(state="visible", timeout=10_000)
            assert sidebar.is_visible()
            browser.close()

    def test_no_credential_leak_in_page_source(self, streamlit_server):
        """No API-key or OAuth-token shapes in the rendered page source."""
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(streamlit_server, wait_until="networkidle", timeout=30_000)

            html = page.content()
            # Google API key shape: AIza... (≥30 chars after prefix)
            assert "AIza" not in html, "Possible API key leak in page source"
            # Google OAuth access token shape: ya29...
            assert "ya29" not in html, "Possible OAuth token leak in page source"
            # AI Studio key shape: AQ....
            assert "AQ." not in html, "Possible AI Studio key leak in page source"
            browser.close()
