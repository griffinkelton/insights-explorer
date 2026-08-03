# Codebuff Prompt: Phase 3.3 Real-Drive E2E Tests (Functional #2-#4)

> Paste this whole prompt into Codebuff as a single task. This produces two
> NEW files only; it must not modify tests/test_drive_import_smoke.py or any
> other existing file.

## Context to give Codebuff

This repo (insights-explorer) already has a Playwright smoke suite at
`tests/test_drive_import_smoke.py`. That suite tests the Drive Picker UI
using an app-controlled test-mode seam (`DRIVE_PICKER_TEST_MODE=1` + query
param `?picker_seam=none|cancel|error|picked`) and NEVER touches Google's
real Picker or real OAuth -- it fakes the component's return value.

We now need a second, separate suite that runs against the REAL Google Drive
Picker with a real (disposable/test) Google account, to validate Functional
Matrix cases #2-#4 from RELEASE_CHECKLIST.md:
  2. Select CSV file via Picker -> file imported, preview renders
  3. Select XLSX file via Picker -> file imported, preview renders
  4. Select native Google Sheet via Picker -> exported as CSV, imported

Because this suite needs a real authenticated Google session, use
Playwright's `storageState` pattern: a one-time interactive login script
saves cookies/localStorage to disk, and the real E2E spec reuses that saved
state headlessly so no credentials are ever hardcoded or committed.

## Task 1 -- auth-setup.spec.ts

Create `tests/e2e/auth-setup.spec.ts` (TypeScript, `@playwright/test`):
- Run manually, locally, headed only -- never in CI.
- Launch a browser context pointed at the running Streamlit app (`BASE_URL`
  env var, default `http://localhost:8501`).
- Pause execution (e.g. `page.pause()`) so the developer can manually finish
  Google OAuth sign-in and Drive consent in the opened window.
- Poll for the authenticated sidebar state (the 'Import from Google Drive'
  button becoming visible), timeout ~120s to allow for manual login.
- On success, call `context.storageState({ path: 'tests/e2e/.auth/session.json' })`.
- Print a clear console message on success/failure.
- Add `tests/e2e/.auth/` to `.gitignore` -- never commit real session state.
- Top-of-file comment block: ONE-TIME, LOCAL-ONLY script; must never run in
  CI; the saved file holds live session cookies and must never be committed
  or shared.

## Task 2 -- test_drive_picker_e2e.spec.ts

Create `tests/e2e/test_drive_picker_e2e.spec.ts` (TypeScript, `@playwright/test`):
- Use `test.use({ storageState: 'tests/e2e/.auth/session.json' })` to reuse
  the saved real session.
- Skip gracefully with a clear message if the session file is missing, and/or
  gate the whole suite behind an explicit `E2E_REAL_DRIVE=1` env var, so
  CI and fresh clones never fail on this.
- Three tests matching Functional Matrix #2-#4:
  1. imports a real CSV file via Picker and renders a data preview
  2. imports a real XLSX file via Picker and renders a data preview
  3. imports a real native Google Sheet via Picker (exported as CSV) and
     renders a data preview
- Each test: open the app, click 'Import from Google Drive', wait for the
  Picker iframe. Driving Google's real Picker UI inside the cross-origin
  iframe is best-effort and unstable in Playwright, so prefer asserting on
  app-side post-import state instead: preview table visible, sane row/column
  count, and no raw filename displayed (per the Sensitive-Output Leakage
  checklist).
- Reference the three dummy fixtures only by type ("a small CSV file", "a
  small XLSX file", "a native Sheet") -- never hardcode real file IDs,
  filenames, or account emails. Read them from env vars instead:
  `E2E_CSV_FILE_NAME`, `E2E_XLSX_FILE_NAME`, `E2E_SHEET_FILE_NAME`.
- Add assertions for Sensitive-Output Leakage Check items L1/L5 from
  RELEASE_CHECKLIST.md: after import, page content must not contain the raw
  Drive file ID or the picked filename string.
- Use generous timeouts (Picker UI + real network round trip): 30-45s.

## Constraints for Codebuff

- Do not modify any existing file.
- Do not add new npm dependencies beyond `@playwright/test` -- check
  package.json first; if it's missing, flag that as a manual follow-up
  rather than editing package.json.
- Do not commit. Only write the two new files plus the `.gitignore` addition.
- Match the existing repo's docstring/comment style (see the header comment
  in tests/test_drive_import_smoke.py for tone and format).

## Open question before you commit to this in Codebuff

Before generating these files, decide: do you want me to first confirm how
the existing `test_drive_import_smoke.py` test-mode seam works in more
detail (so any shared helpers/conventions -- like `_wait_for_sidebar` or the
`iframe title="drive_picker_transport"` pattern -- are reused instead of
reinvented in the new real-Drive suite), or do you want to run this prompt
as-is and reconcile any duplication afterward?
