#!/usr/bin/env python3
"""Pre-commit guard: reject credential-shaped strings in staged files.

Catches real Google API keys (``AIza...``), Google AI Studio API keys
(``AQ....``), and Google OAuth access tokens (``ya29...``) before they
reach git history — a regression guard for the IDEAS #29 credential-
rotation incident.

Phase 1 addition (master-plan §11-D, spec phase-1-upload-slice.md §1):
the FastAPI env-var **allowlist** (names only). Three checks:

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

# ── Phase 1: FastAPI env-var allowlist (names only — master-plan §11-D) ──
ALLOWLISTED_ENV_VARS = frozenset(
    {
        "API_SESSION_SECRET",
        "API_CORS_ORIGINS",
        "FRONTEND_URL",
        "MAX_BROWSER_UPLOAD_BYTES",
        "MAX_INGEST_BYTES",
    }
)
# Non-placeholder fails ANYWHERE, including .env.example.
SECRET_ENV_VARS = frozenset({"API_SESSION_SECRET"})
# Concrete safe defaults OK inside .env.example; fail in committed real env files.
SAFE_CONFIG_ENV_VARS = frozenset(ALLOWLISTED_ENV_VARS - SECRET_ENV_VARS)

ENV_EXAMPLE_NAME = ".env.example"
ENV_ASSIGNMENT = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$")
PLACEHOLDER_VALUE = re.compile(r"^(<[^>]*>|your_[a-z0-9_]+_here|replace-with-.*|\.\.\.)$")
ENV_FILE_NAMES = {".env", "docker-compose.yml", "docker-compose.yaml", "cloudbuild.yaml"}
WORKFLOW_DIR = ".github/workflows"


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
    """Real env/config files the value scan applies to (excludes .env.example)."""
    name = path.name
    if name == ENV_EXAMPLE_NAME:
        return False
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        return True
    if name in ENV_FILE_NAMES:
        return True
    if len(path.parts) >= 2 and path.parts[:2] == (".github", "workflows"):
        return True
    return False


def check_env_example(text: str) -> list[str]:
    """Presence of every allowlisted name + placeholder-only secret."""
    errors: list[str] = []
    assignments = parse_assignments(text)
    for name in sorted(ALLOWLISTED_ENV_VARS):
        if name not in assignments:
            errors.append(f"missing {name} in {ENV_EXAMPLE_NAME}")
    if "API_SESSION_SECRET" in assignments:
        secret = assignments["API_SESSION_SECRET"]
        if not PLACEHOLDER_VALUE.match(secret):
            errors.append(
                "API_SESSION_SECRET in .env.example must be a placeholder "
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
    if failures:
        print(
            "\nCredential-shaped strings or committed env values found. "
            "Remove them or replace with placeholders before committing."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
