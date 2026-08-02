"""Structural tests for the credential-shaped-string pre-commit guard.

Covers scripts/check_credentials.py behavior and its registration in
.pre-commit-config.yaml + the CI workflow. Regression guard for the
IDEAS #29 credential-rotation incident.

NOTE: Fake keys/tokens here are built via runtime concatenation so no source
line contains a contiguous credential-shaped string — otherwise the guard
would flag its own test file when CI scans the repo.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "check_credentials.py"

# Built at runtime — never a contiguous string in this source file.
FAKE_KEY = "AIza" + "Sy" + "Dg1234567890AbCdEfGhIjKlMnOpQrStUv"
FAKE_AI_STUDIO_KEY = "AQ." + ("z" * 40)
FAKE_TOKEN = "ya29." + ("x" * 40)


def _load_guard():
    """Load scripts/check_credentials.py as a module (not a package)."""
    spec = importlib.util.spec_from_file_location("check_credentials", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_credentials"] = module
    spec.loader.exec_module(module)
    return module


class TestScanText:
    """Direct unit tests of scan_text() — no filesystem access."""

    def _guard(self):
        return _load_guard()

    def test_flags_real_google_api_key(self):
        guard = self._guard()
        # 39-char AIza key — matches the real format
        hits = guard.scan_text(f'GOOGLE_PICKER_API_KEY = "{FAKE_KEY}"')
        assert hits
        assert "Google API key" in hits[0][1]

    def test_flags_short_api_key_still_catches_30plus(self):
        guard = self._guard()
        # 30-char suffix after AIza still matches the {30,} pattern
        hits = guard.scan_text("AIza" + ("A" * 30))
        assert hits

    def test_allows_doc_placeholder_aiZa_dots(self):
        guard = self._guard()
        # "AIza..." placeholder must NOT be flagged
        hits = guard.scan_text('GOOGLE_PICKER_API_KEY = "AIza..."')
        assert not hits

    def test_flags_real_ya29_token(self):
        guard = self._guard()
        hits = guard.scan_text(f"oauth_token={FAKE_TOKEN}")
        assert hits
        assert "Google OAuth access token" in hits[0][1]

    def test_allows_test_fixture_ya29_abc123(self):
        guard = self._guard()
        # tests/test_ga4_client.py fixture — payload too short to match
        hits = guard.scan_text('"token": "ya29.abc123"')
        assert not hits

    def test_flags_real_ai_studio_key(self):
        guard = self._guard()
        hits = guard.scan_text(f'GEMINI_API_KEY = "{FAKE_AI_STUDIO_KEY}"')
        assert hits
        assert "Google AI Studio API key" in hits[0][1]

    def test_allows_doc_placeholder_aq_dots(self):
        guard = self._guard()
        # "AQ...." placeholder must NOT be flagged
        hits = guard.scan_text('GEMINI_API_KEY = "AQ...."')
        assert not hits

    def test_allows_identifier_oauth_token_equal(self):
        guard = self._guard()
        # Code identifier `oauth_token=oauth_token` — no credential value
        hits = guard.scan_text("_picker_iframe_html(oauth_token=oauth_token, api_key=api_key)")
        assert not hits

    def test_redacts_long_match(self):
        guard = self._guard()
        hits = guard.scan_text("AIza" + ("B" * 35))
        assert hits
        # Redacted form never contains the full value
        assert ("B" * 35) not in hits[0][2]


class TestHookRegistration:
    """Guard is wired into pre-commit and CI."""

    def test_hook_registered_in_precommit_config(self):
        config = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text()
        assert "check-credentials" in config
        assert "python scripts/check_credentials.py" in config
        assert "types: [text]" in config

    def test_ci_workflow_runs_guard(self):
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "test.yml").read_text()
        assert "check_credentials.py" in workflow
        assert "git ls-files" in workflow

    def test_script_exists(self):
        assert SCRIPT_PATH.exists()


class TestMainBehavior:
    """End-to-end main() behavior on real files."""

    def _guard(self):
        return _load_guard()

    def test_main_passes_on_clean_text(self, tmp_path):
        guard = self._guard()
        clean = tmp_path / "clean.txt"
        clean.write_text("nothing sensitive here\n", encoding="utf-8")
        assert guard.main(["check_credentials.py", str(clean)]) == 0

    def test_main_fails_on_credential(self, tmp_path):
        guard = self._guard()
        leaky = tmp_path / "leaky.txt"
        leaky.write_text(f'key = "{FAKE_KEY}"\n', encoding="utf-8")
        assert guard.main(["check_credentials.py", str(leaky)]) == 1

    def test_main_skips_ignored_suffixes(self, tmp_path):
        guard = self._guard()
        binary = tmp_path / "blob.png"
        binary.write_bytes(FAKE_KEY.encode())
        assert guard.main(["check_credentials.py", str(binary)]) == 0
