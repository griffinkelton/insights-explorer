"""Phase 3.3: Real-Drive E2E tests — requires explicit opt-in (E2E_REAL_DRIVE=1).

These tests use Playwright's storageState pattern to reuse a real Google OAuth
session.  The session is created once interactively (auth_setup.py) and must
never be committed.  See docs/codebuff-prompt-e2e-drive-picker.md for the
full specification.
"""
