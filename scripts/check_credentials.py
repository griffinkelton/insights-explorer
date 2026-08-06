#!/usr/bin/env python3
"""Pre-commit guard: reject credential-shaped strings in staged files.

Catches real Google API keys (``AIza...``), Google AI Studio API keys
(``AQ....``), and Google OAuth access tokens (``ya29...``) before they
reach git history — a regression guard for the IDEAS #29 credential-
rotation incident.

Phase 1 + Phase 3 addition (master-plan §11-D; specs phase-1-upload-slice.md
§1 and phase-3-ai-analysis.md settings block; canonical env table in
policies/data-retention-policy.md §7.2): the env-var **allowlist** (names
only). Three checks:

  1. **Presence** — every allowlisted name appears as ``NAME=`` in
     ``.env.example``.
  2. **Secret value** — ``API_SESSION_SECRET=<non-placeholder>`` fails
     *anywhere*, including ``.env.example``.
  3. **Config value** — a ``SAFE_CONFIG_ENV_VARS`` name with a
     non-placeholder value in a committed real env file (``.env``,
     ``.env.*``, ``*.env``, docker-compose, ``cloudbuild.yaml``, GitHub
     workflows) fails. ``.env.example`` may keep concrete safe config
     defaults (dev origin, byte limits) — it is checked for presence,
     not placeholder-ness.

Phase 1 review correction (2026-08-06): YAML env syntax. GitHub Actions
(``.github/workflows/*.yml``) and Cloud Build (``cloudbuild.yaml``) commonly
write env settings as ``NAME: value`` (colon syntax), which a dotenv-only
parser cannot see. ``check_yaml_env_file()`` parses tracked YAML deployment
config with ``yaml.safe_load()`` and walks the tree for allowlisted keys.
Approved values: placeholders, GitHub ``${{ secrets.NAME }}`` references,
and Cloud secret-manager references (``projects/.../secrets/...``). Literal
secret or config values in committed deployment config fail.

Phase 3 addition (2026-08-06): the AI/Gemini env vars joined the allowlist —
``GEMINI_API_KEY`` (secret-bearing, placeholder-only like
``API_SESSION_SECRET``), plus ``GEMINI_MODEL``, ``GEMINI_DATA_POLICY`` and
the six AI_* token/timeout vars (safe config: concrete defaults allowed in
``.env.example``, never in committed real env files). Tier mode is explicit
via ``GEMINI_DATA_POLICY`` — never inferred from the key value.

Deliberate non-matches (kept safe by minimum-length requirements):
  - ``ya29.abc123``  — test fixture in tests/test_ga4_client.py (payload too short)
  - ``AIza...``      — doc placeholder in phase-0 spike spec (dots, too short)
  - ``AQ....``       — doc placeholder (dots, too short)

Usage (via pre-commit): receives staged filenames as argv. Also accepts
tracked-file lists piped from ``git ls-files -z | xargs -0`` for CI.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml  # PyYAML — pinned in requirements/dev.txt; pulled by pandas in prod envs

# Real Google API keys: "AIza" + 35 base64url chars (39 total).
# The doc placeholder "AIza..." never matches (dots, too short).
GOOGLE_API_KEY = re.compile(r"AIza[0-9A-Za-z_-]{30,}")

# Real Google AI Studio API keys: "AQ." + long base64url payload.
# The doc placeholder "AQ...." never matches (dots, too short).
GOOGLE_AI_STUDIO_KEY = re.compile(r"AQ\.[0-9A-Za-z_-]{30,}")

# Real Google OAuth access tokens: "ya29." + long base64url payload.
# The test fixture "ya29.abc123" never matches (payload too short).
GOOGLE_OAUTH_TOKEN = re.compile(r"ya29\.[0-9A-Za-z_-]{10,}")

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Google API key", GOOGLE_API_KEY),
    ("Google AI Studio API key", GOOGLE_AI_STUDIO_KEY),
    ("Google OAuth access token", GOOGLE_OAUTH_TOKEN),
)

# Directories/suffixes never scanned (the guard itself, lockfiles, binaries).
SKIP_PARTS = {".git", "node_modules", "venv", "build", "docs/_build"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc", ".lock"}

# ── Env-var allowlist (names only — master-plan §11-D; data-retention-policy §7.2) ──
ALLOWLISTED_ENV_VARS = frozenset(
    {
        # Phase 1 — FastAPI backend
        "API_SESSION_SECRET",
        "API_CORS_ORIGINS",
        "FRONTEND_URL",
        "MAX_BROWSER_UPLOAD_BYTES",
        "MAX_INGEST_BYTES",
        # Phase 3 — AI / Gemini runtime (spec phase-3-ai-analysis.md settings)
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_DATA_POLICY",
        "AI_MAX_CONTEXT_TOKENS",
        "AI_RESERVED_OUTPUT_TOKENS",
        "AI_MAX_CONTEXT_CHARS",
        "AI_FIRST_TOKEN_TIMEOUT_SECONDS",
        "AI_GENERATE_TIMEOUT_SECONDS",
        "AI_STREAM_TIMEOUT_SECONDS",
    }
)
# Non-placeholder fails ANYWHERE, including .env.example.
SECRET_ENV_VARS = frozenset({"API_SESSION_SECRET", "GEMINI_API_KEY"})
# Concrete safe defaults OK inside .env.example; fail in committed real env files.
SAFE_CONFIG_ENV_VARS = frozenset(ALLOWLISTED_ENV_VARS - SECRET_ENV_VARS)

ENV_EXAMPLE_NAME = ".env.example"
ENV_ASSIGNMENT = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$")
PLACEHOLDER_VALUE = re.compile(r"^(<[^>]*>|your_[a-z0-9_]+_here|replace-with-.*|\.\.\.)$")
ENV_FILE_NAMES = {".env", "docker-compose.yml", "docker-compose.yaml", "cloudbuild.yaml"}
WORKFLOW_DIR = ".github/workflows"

# Approved non-literal YAML values for allowlisted keys (review fix 2026-08-06):
# GitHub Actions ``${{ secrets.NAME }}`` and Cloud secret-manager refs.
YAML_SECRET_REFERENCE = re.compile(r"^\$\{\{\s*secrets\.[A-Z0-9_]+\s*\}\}$")
CLOUD_SECRET_REFERENCE = re.compile(r"^projects/[^/]+/secrets/[^/]+/versions/[^/]+$")

# YAML suffixes that get the tree-walking value check (in addition to the
# dotenv parser, which simply finds nothing in colon-syntax files).
YAML_SUFFIXES = {".yml", ".yaml"}


def scan_text(text: str) -> list[tuple[int, str, str]]:
    """Return [(line_no, pattern_name, redacted_match)] for a text blob."""
    hits: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for name, pattern in PATTERNS:
            match = pattern.search(line)
            if match:
                value = match.group(0)
                redacted = f"{value[:6]}…" if len(value) > 6 else value
                hits.append((lineno, name, redacted))
                break  # one hit per line is enough
    return hits


# ── Phase 1: env-file value scan helpers ─────────────────────────────────


def _strip_inline_comment(value: str) -> str:
    """Drop a trailing `` # comment`` from a dotenv assignment value."""
    return re.sub(r"\s+#.*$", "", value).strip()


def parse_assignments(text: str) -> dict[str, str]:
    """Return {NAME: value} for ``NAME=value`` lines in an env-like file."""
    assignments: dict[str, str] = {}
    for line in text.splitlines():
        match = ENV_ASSIGNMENT.match(line)
        if match:
            assignments[match.group(1)] = _strip_inline_comment(match.group(2))
    return assignments


def _is_env_like(path: Path) -> bool:
    """Real env/config files the value scan applies to (excludes .env.example).

    Uses ``Path`` components (works for relative and absolute paths alike —
    review fix 2026-08-06)."""
    name = path.name
    if name == ENV_EXAMPLE_NAME:
        return False
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        return True
    if name in ENV_FILE_NAMES:
        return True
    parts = path.parts
    if any(
        parts[i] == ".github" and i + 1 < len(parts) and parts[i + 1] == "workflows"
        for i in range(len(parts))
    ):
        return True
    return False


def check_env_example(text: str) -> list[str]:
    """Presence of every allowlisted name + placeholder-only secret."""
    errors: list[str] = []
    assignments = parse_assignments(text)
    for name in sorted(ALLOWLISTED_ENV_VARS):
        if name not in assignments:
            errors.append(f"missing {name} in {ENV_EXAMPLE_NAME}")
    for name in sorted(SECRET_ENV_VARS):
        if name in assignments:
            value = assignments[name]
            if not PLACEHOLDER_VALUE.match(value):
                errors.append(
                    f"{name} in {ENV_EXAMPLE_NAME} must be a placeholder "
                    "(empty or real values are rejected)"
                )
    return errors


def check_env_file(text: str) -> list[str]:
    """Committed real env files: no secret value, no non-placeholder config value."""
    errors: list[str] = []
    for name, value in parse_assignments(text).items():
        if name not in ALLOWLISTED_ENV_VARS:
            continue
        if PLACEHOLDER_VALUE.match(value):
            continue
        if name in SECRET_ENV_VARS:
            errors.append(f"{name} carries a real value — use deployment secrets instead")
        else:
            errors.append(
                f"{name} carries a committed value — environment-specific "
                "production values must not be committed"
            )
    return errors


def _yaml_scalar(value: Any) -> str:
    """Normalize a YAML scalar (str/int/bool/None) to a string for value checks."""
    if value is None:
        return ""
    return str(value)


def _yaml_value_allowed(value: str) -> bool:
    """Placeholders and approved secret references pass; literal values fail."""
    stripped = value.strip()
    if PLACEHOLDER_VALUE.match(stripped):
        return True
    if YAML_SECRET_REFERENCE.match(stripped):
        return True
    if CLOUD_SECRET_REFERENCE.match(stripped):
        return True
    return False


def _walk_allowlisted(node: Any, errors: list[str], where: str) -> None:
    """Recursively walk YAML mappings/lists for allowlisted keys."""
    if isinstance(node, dict):
        for key, value in node.items():
            key_name = str(key)
            if key_name in ALLOWLISTED_ENV_VARS:
                val = _yaml_scalar(value)
                if not _yaml_value_allowed(val):
                    if key_name in SECRET_ENV_VARS:
                        errors.append(
                            f"{where}: {key_name} carries a real value — use "
                            f"${{{{ secrets.{key_name} }}}} or a secret-manager reference"
                        )
                    else:
                        errors.append(
                            f"{where}: {key_name} carries a committed value — use a "
                            "placeholder or an approved secret reference"
                        )
            _walk_allowlisted(value, errors, where)
    elif isinstance(node, list):
        for item in node:
            _walk_allowlisted(item, errors, where)


def check_yaml_env_file(text: str, where: str = "yaml") -> list[str]:
    """YAML-aware env-value check for deployment config (review fix 2026-08-06).

    Parses with ``yaml.safe_load()`` and walks the tree for allowlisted keys.
    Unparseable YAML is skipped here — ``scan_text`` still covers credential
    shapes in the raw text, and a malformed workflow is a CI failure anyway.
    """
    errors: list[str] = []
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return errors
    if data is None:
        return errors
    _walk_allowlisted(data, errors, where)
    return errors


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv[1:]]
    failures = 0
    for path in files:
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, name, redacted in scan_text(text):
            print(f"{path}:{lineno}: {name} (credential-shaped: {redacted})")
            failures += 1
        if path.name == ENV_EXAMPLE_NAME:
            for err in check_env_example(text):
                print(f"{path}: {err}")
                failures += 1
        elif _is_env_like(path):
            for err in check_env_file(text):
                print(f"{path}: {err}")
                failures += 1
            # YAML deployment config also gets the tree-walking check (review fix).
            if path.suffix.lower() in YAML_SUFFIXES:
                for err in check_yaml_env_file(text, where=str(path)):
                    print(f"{path}: {err}")
                    failures += 1
    if failures:
        print(
            "\nCredential-shaped strings or committed env values found. "
            "Remove them or replace with placeholders before committing."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
