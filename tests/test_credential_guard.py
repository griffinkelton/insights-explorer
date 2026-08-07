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


class TestEnvAllowlist:
    """Phase 1 allowlist checks: parse_assignments / check_env_example / check_env_file."""

    def _guard(self):
        return _load_guard()

    def test_parse_assignments_strips_inline_comment(self):
        guard = self._guard()
        parsed = guard.parse_assignments(
            "API_SESSION_SECRET=replace-with-a-long-random-value   # python -c ...\n"
            "FRONTEND_URL=http://localhost:5173\n"
        )
        assert parsed["API_SESSION_SECRET"] == "replace-with-a-long-random-value"
        assert parsed["FRONTEND_URL"] == "http://localhost:5173"

    def test_check_env_example_presence_lists_missing_names(self):
        guard = self._guard()
        errors = guard.check_env_example(
            "API_SESSION_SECRET=replace-with-a-long-random-value\n"
            "FRONTEND_URL=http://localhost:5173\n"
        )
        joined = "\n".join(errors)
        assert "API_CORS_ORIGINS" in joined
        assert "MAX_BROWSER_UPLOAD_BYTES" in joined
        assert "MAX_INGEST_BYTES" in joined
        assert "GEMINI_MODEL" in joined
        assert "AI_MAX_CONTEXT_TOKENS" in joined

    def test_check_env_example_rejects_real_or_empty_secret(self):
        guard = self._guard()
        real = guard.check_env_example(
            "API_SESSION_SECRET=not-a-placeholder\n"
            "FRONTEND_URL=x\n"
            "API_CORS_ORIGINS=x\n"
            "MAX_BROWSER_UPLOAD_BYTES=x\n"
            "MAX_INGEST_BYTES=x\n"
        )
        assert real  # placeholder error present
        empty = guard.check_env_example(
            "API_SESSION_SECRET=\n"
            "FRONTEND_URL=x\n"
            "API_CORS_ORIGINS=x\n"
            "MAX_BROWSER_UPLOAD_BYTES=x\n"
            "MAX_INGEST_BYTES=x\n"
        )
        assert empty  # empty value is treated as a real value

    def test_check_env_file_config_defaults_fail_in_real_env_file(self):
        guard = self._guard()
        errors = guard.check_env_file(
            "FRONTEND_URL=http://localhost:5173\n" "MAX_BROWSER_UPLOAD_BYTES=26214400\n"
        )
        assert any("FRONTEND_URL" in e for e in errors)

    def test_check_env_file_secret_placeholder_passes(self):
        guard = self._guard()
        errors = guard.check_env_file("API_SESSION_SECRET=replace-with-x\n")
        assert errors == []

    def test_check_env_example_full_with_ai_vars_passes(self):
        guard = self._guard()
        errors = guard.check_env_example(
            "API_SESSION_SECRET=replace-with-a-long-random-value\n"
            "API_CORS_ORIGINS=http://localhost:5173\n"
            "FRONTEND_URL=http://localhost:5173\n"
            "MAX_BROWSER_UPLOAD_BYTES=26214400\n"
            "MAX_INGEST_BYTES=104857600\n"
            "GEMINI_API_KEY=your_api_key_here\n"
            "GEMINI_MODEL=gemini-2.5-flash\n"
            "GEMINI_DATA_POLICY=local_free\n"
            "AI_MAX_CONTEXT_TOKENS=24000\n"
            "AI_RESERVED_OUTPUT_TOKENS=4096\n"
            "AI_MAX_CONTEXT_CHARS=96000\n"
            "AI_FIRST_TOKEN_TIMEOUT_SECONDS=30\n"
            "AI_GENERATE_TIMEOUT_SECONDS=60\n"
            "AI_STREAM_TIMEOUT_SECONDS=120\n"
            "AI_QUEUE_WAIT_SECONDS=30\n"
            "GA4_CLIENT_ID=your_ga4_client_id_here\n"
            "GA4_CLIENT_SECRET=your_ga4_client_secret_here\n"
            "GA4_REDIRECT_URI=http://localhost:8000/api/v1/ga4/callback\n"
            "GA4_ENABLED=false\n"
            "GA4_PROPERTY_ID=123456789\n"
            "DRIVE_ENABLED=false\n"
            "GOOGLE_CLOUD_PROJECT_NUMBER=123456789012\n"
            "DRIVE_DOWNLOAD_TIMEOUT_SECONDS=300\n"
        )
        assert errors == []

    def test_phase5_oauth_names_allowlisted(self):
        guard = self._guard()
        for name in (
            "GA4_CLIENT_ID",
            "GA4_CLIENT_SECRET",
            "GA4_REDIRECT_URI",
            "GA4_ENABLED",
            "GA4_PROPERTY_ID",
            "DRIVE_ENABLED",
            "GOOGLE_CLOUD_PROJECT_NUMBER",
        ):
            assert name in guard.ALLOWLISTED_ENV_VARS, name
        # GA4_CLIENT_SECRET is secret-bearing — placeholder-only like the others.
        assert "GA4_CLIENT_SECRET" in guard.SECRET_ENV_VARS
        # .env.example must carry every allowlisted name.
        text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
        assert "GA4_CLIENT_SECRET=your_ga4_client_secret_here" in text
        assert "GOOGLE_CLOUD_PROJECT_NUMBER=123456789012" in text

    def test_check_env_example_rejects_real_gemini_api_key(self):
        guard = self._guard()
        errors = guard.check_env_example(
            "API_SESSION_SECRET=replace-with-a-long-random-value\n"
            "API_CORS_ORIGINS=x\n"
            "FRONTEND_URL=x\n"
            "MAX_BROWSER_UPLOAD_BYTES=x\n"
            "MAX_INGEST_BYTES=x\n"
            "GEMINI_API_KEY=not-a-placeholder-key\n"
            "GEMINI_MODEL=gemini-2.5-flash\n"
            "GEMINI_DATA_POLICY=local_free\n"
            "AI_MAX_CONTEXT_TOKENS=24000\n"
            "AI_RESERVED_OUTPUT_TOKENS=4096\n"
            "AI_MAX_CONTEXT_CHARS=96000\n"
            "AI_FIRST_TOKEN_TIMEOUT_SECONDS=30\n"
            "AI_GENERATE_TIMEOUT_SECONDS=60\n"
            "AI_STREAM_TIMEOUT_SECONDS=120\n"
            "AI_QUEUE_WAIT_SECONDS=30\n"
        )
        assert any("GEMINI_API_KEY" in e for e in errors)

    def test_check_env_file_gemini_api_key_real_fails(self):
        guard = self._guard()
        errors = guard.check_env_file("GEMINI_API_KEY=not-a-placeholder-key\n")
        assert any("GEMINI_API_KEY" in e for e in errors)

    def test_check_env_file_gemini_api_key_placeholder_passes(self):
        guard = self._guard()
        errors = guard.check_env_file("GEMINI_API_KEY=your_api_key_here\n")
        assert errors == []

    def test_check_env_file_ai_config_value_fails_in_real_env(self):
        guard = self._guard()
        errors = guard.check_env_file(
            "GEMINI_MODEL=gemini-2.5-flash\n"
            "GEMINI_DATA_POLICY=local_free\n"
            "AI_MAX_CONTEXT_TOKENS=24000\n"
        )
        assert any("GEMINI_MODEL" in e for e in errors)
        assert any("GEMINI_DATA_POLICY" in e for e in errors)
        assert any("AI_MAX_CONTEXT_TOKENS" in e for e in errors)

    def test_repo_env_example_passes_check_env_example(self):
        guard = self._guard()
        text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
        assert guard.check_env_example(text) == []

    def test_is_env_like_excludes_env_example(self):
        guard = self._guard()
        assert not guard._is_env_like(Path(".env.example"))
        assert guard._is_env_like(Path(".env"))
        assert guard._is_env_like(Path(".env.local"))
        assert guard._is_env_like(Path("prod.env"))
        assert guard._is_env_like(Path("cloudbuild.yaml"))
        assert guard._is_env_like(Path(".github/workflows/test.yml"))
        assert not guard._is_env_like(Path("migration/specs/phase-1-upload-slice.md"))


class TestYamlEnvAllowlist:
    """YAML-aware env-value scan for deployment config (review fix A, 2026-08-06).

    GitHub Actions / Cloud Build write ``NAME: value`` (colon syntax) which the
    dotenv parser cannot see; check_yaml_env_file() parses YAML and walks the
    tree for allowlisted keys.
    """

    def _guard(self):
        return _load_guard()

    def test_yaml_literal_secret_value_fails(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "steps:\n"
            "  - name: test\n"
            "    env:\n"
            "      API_SESSION_SECRET: some-real-secret-value\n"
        )
        assert any("API_SESSION_SECRET" in e for e in errors)

    def test_yaml_literal_config_value_fails(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "steps:\n"
            "  - name: test\n"
            "    env:\n"
            "      FRONTEND_URL: https://production.example.com\n"
        )
        assert any("FRONTEND_URL" in e for e in errors)

    def test_yaml_github_actions_secret_expression_passes(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "steps:\n"
            "  - name: test\n"
            "    env:\n"
            '      API_SESSION_SECRET: "${{ secrets.API_SESSION_SECRET }}"\n'
        )
        assert errors == []

    def test_yaml_cloud_secret_manager_reference_passes(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "availableSecrets:\n"
            "  secretManager:\n"
            "    - versionName: projects/my-proj/secrets/API_SESSION_SECRET/versions/latest\n"
        )
        assert errors == []

    def test_yaml_placeholder_passes(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "env:\n" "  API_SESSION_SECRET: replace-with-a-long-random-value\n"
        )
        assert errors == []

    def test_yaml_gemini_api_key_literal_fails(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "steps:\n" "  - name: test\n" "    env:\n" "      GEMINI_API_KEY: some-real-key-value\n"
        )
        assert any("GEMINI_API_KEY" in e for e in errors)

    def test_yaml_gemini_api_key_secrets_expression_passes(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "steps:\n"
            "  - name: test\n"
            "    env:\n"
            '      GEMINI_API_KEY: "${{ secrets.GEMINI_API_KEY }}"\n'
        )
        assert errors == []

    def test_yaml_gemini_model_literal_fails_in_deployment_config(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file("env:\n  GEMINI_MODEL: gemini-3.5-flash\n")
        assert any("GEMINI_MODEL" in e for e in errors)

    def test_yaml_numeric_config_value_fails_in_deployment_config(self):
        # YAML int scalars are normalized via _yaml_scalar() and must be
        # flagged like string values — deployment config cannot hardcode
        # allowlisted AI values either.
        guard = self._guard()
        errors = guard.check_yaml_env_file(
            "env:\n  AI_MAX_CONTEXT_TOKENS: 24000\n  AI_STREAM_TIMEOUT_SECONDS: 120\n"
        )
        assert any("AI_MAX_CONTEXT_TOKENS" in e for e in errors)
        assert any("AI_STREAM_TIMEOUT_SECONDS" in e for e in errors)

    def test_yaml_concrete_config_value_fails_in_deployment_config(self):
        # Per policy, a committed deployment YAML may not carry a concrete
        # config value either (only .env.example may). Review fix A matrix.
        guard = self._guard()
        errors = guard.check_yaml_env_file("env:\n" "  FRONTEND_URL: http://localhost:5173\n")
        assert any("FRONTEND_URL" in e for e in errors)

    def test_yaml_nested_workflow_literal_fails_via_main(self, tmp_path):
        guard = self._guard()
        workflow = tmp_path / ".github" / "workflows" / "deploy.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            "jobs:\n" "  deploy:\n" "    env:\n" "      API_SESSION_SECRET: leaked-value\n",
            encoding="utf-8",
        )
        assert guard.main(["check_credentials.py", str(workflow)]) == 1

    def test_yaml_secret_expression_passes_via_main(self, tmp_path):
        guard = self._guard()
        workflow = tmp_path / "cloudbuild.yaml"
        workflow.write_text(
            "steps:\n"
            "  - name: test\n"
            "    env:\n"
            '      API_SESSION_SECRET: "${{ secrets.API_SESSION_SECRET }}"\n',
            encoding="utf-8",
        )
        assert guard.main(["check_credentials.py", str(workflow)]) == 0

    def test_yaml_unparseable_skipped_not_crash(self):
        guard = self._guard()
        errors = guard.check_yaml_env_file("not: [valid: yaml: [")
        assert errors == []


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

    def test_main_env_example_presence_fails_when_name_missing(self, tmp_path):
        guard = self._guard()
        env_example = tmp_path / ".env.example"
        env_example.write_text(
            "API_SESSION_SECRET=replace-with-a-long-random-value\n"
            "API_CORS_ORIGINS=http://localhost:5173\n"
            "FRONTEND_URL=http://localhost:5173\n"
            "MAX_BROWSER_UPLOAD_BYTES=26214400\n",
            encoding="utf-8",
        )
        assert guard.main(["check_credentials.py", str(env_example)]) == 1

    def test_main_env_example_secret_real_value_fails(self, tmp_path):
        guard = self._guard()
        env_example = tmp_path / ".env.example"
        env_example.write_text(
            "API_SESSION_SECRET=some-real-looking-secret-value\n"
            "API_CORS_ORIGINS=http://localhost:5173\n"
            "FRONTEND_URL=http://localhost:5173\n"
            "MAX_BROWSER_UPLOAD_BYTES=26214400\n"
            "MAX_INGEST_BYTES=104857600\n",
            encoding="utf-8",
        )
        assert guard.main(["check_credentials.py", str(env_example)]) == 1

    def test_main_committed_config_value_in_env_file_fails(self, tmp_path):
        guard = self._guard()
        env_file = tmp_path / "cloudbuild.yaml"
        env_file.write_text(
            "FRONTEND_URL=https://production.example.com\n",
            encoding="utf-8",
        )
        assert guard.main(["check_credentials.py", str(env_file)]) == 1

    def test_main_env_example_with_safe_config_defaults_passes(self, tmp_path):
        guard = self._guard()
        env_example = tmp_path / ".env.example"
        env_example.write_text(
            "API_SESSION_SECRET=replace-with-a-long-random-value\n"
            "API_CORS_ORIGINS=http://localhost:5173\n"
            "FRONTEND_URL=http://localhost:5173\n"
            "MAX_BROWSER_UPLOAD_BYTES=26214400\n"
            "MAX_INGEST_BYTES=104857600\n"
            "GEMINI_API_KEY=your_api_key_here\n"
            "GEMINI_MODEL=gemini-2.5-flash\n"
            "GEMINI_DATA_POLICY=local_free\n"
            "AI_MAX_CONTEXT_TOKENS=24000\n"
            "AI_RESERVED_OUTPUT_TOKENS=4096\n"
            "AI_MAX_CONTEXT_CHARS=96000\n"
            "AI_FIRST_TOKEN_TIMEOUT_SECONDS=30\n"
            "AI_GENERATE_TIMEOUT_SECONDS=60\n"
            "AI_STREAM_TIMEOUT_SECONDS=120\n"
            "AI_QUEUE_WAIT_SECONDS=30\n"
            "GA4_CLIENT_ID=your_ga4_client_id_here\n"
            "GA4_CLIENT_SECRET=your_ga4_client_secret_here\n"
            "GA4_REDIRECT_URI=http://localhost:8000/api/v1/ga4/callback\n"
            "GA4_ENABLED=false\n"
            "GA4_PROPERTY_ID=123456789\n"
            "DRIVE_ENABLED=false\n"
            "GOOGLE_CLOUD_PROJECT_NUMBER=123456789012\n"
            "DRIVE_DOWNLOAD_TIMEOUT_SECONDS=300\n",
            encoding="utf-8",
        )
        assert guard.main(["check_credentials.py", str(env_example)]) == 0

    def test_main_docs_prose_is_not_value_scanned(self, tmp_path):
        guard = self._guard()
        prose = tmp_path / "spec.md"
        prose.write_text(
            "MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024 (locked)\n"
            "API_SESSION_SECRET = replace-with-...\n",
            encoding="utf-8",
        )
        # Not an env-like file: no value scan; no credential-shaped match.
        assert guard.main(["check_credentials.py", str(prose)]) == 0
