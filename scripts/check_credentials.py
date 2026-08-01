#!/usr/bin/env python3
"""Pre-commit guard: reject credential-shaped strings in staged files.

Catches real Google API keys (``AIza...``) and Google OAuth access tokens
(``ya29...``) before they reach git history — a regression guard for the
IDEAS #29 credential-rotation incident.

Deliberate non-matches (kept safe by minimum-length requirements):
  - ``ya29.abc123``  — test fixture in tests/test_ga4_client.py (payload too short)
  - ``AIza...``      — doc placeholder in phase-0 spike spec (dots, too short)

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

# Real Google OAuth access tokens: "ya29." + long base64url payload.
# The test fixture "ya29.abc123" never matches (payload too short).
GOOGLE_OAUTH_TOKEN = re.compile(r"ya29\.[0-9A-Za-z_-]{10,}")

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Google API key", GOOGLE_API_KEY),
    ("Google OAuth access token", GOOGLE_OAUTH_TOKEN),
)

# Directories/suffixes never scanned (the guard itself, lockfiles, binaries).
SKIP_PARTS = {".git", "node_modules", "venv", "build", "docs/_build"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc", ".lock"}


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
    if failures:
        print(
            "\nCredential-shaped strings found in staged files. "
            "Remove them or replace with placeholders before committing."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
