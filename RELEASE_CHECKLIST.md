# v0.3.0 Release Checklist

> **Release:** v0.3.0 — Drive Import
> **Date:** 2026-08-03
> **Release owner:** griffinkelton
> **Tests:** 672 pytest (unit/integration) + 14 Playwright smoke + 8 E2E real-Drive leakage + 7 error-path = 701 total

---

## Phase 1–3.2: Automated Gates

- [x] Phase 1: Server-side download (`download_drive_file`, `DriveImportError`, `PickerSelection` wrapper)
- [x] Phase 2: Provenance + atomic ingestion (prepare-then-commit, `_NamedBytesIO`, failure-preservation matrix)
- [x] Phase 3.0: Picker transport (declared component, request freshness, duplicate protection)
- [x] Phase 3.1: Picker UX (theme sync, button states, cancel/reset, filename sanitization)
- [x] Phase 3.2a: Platform Playwright smoke (app loads, sidebar visible, no credential leaks)
- [x] Phase 3.2b: Drive-import Playwright controlled-state (14 tests, test-mode seam)
- [x] CI: Dedicated Playwright job with explicit Chromium install
- [x] CI: Frontend typecheck + production build gate
- [x] CI: Credential guard (AIza/ya29/AQ. patterns)
- [x] README: Drive Import feature, scope, formats, privacy model, Picker setup
- [x] CHANGELOG: v0.3.0 section
- [x] Spec status updated
- [x] Error-path E1-E6: unit-test simulation (`tests/test_drive_import_errors.py` — 7 tests)
- [x] Sensitive-output L1-L5: automated leakage suite (`tests/e2e/test_drive_picker_e2e.py` — 8 tests)

---

## Test Suite Breakdown

| Suite | Count | Command | What It Covers |
|-------|-------|---------|----------------|
| Unit/Integration | 672 | `pytest tests/ --ignore=tests/test_drive_import_smoke.py --ignore=tests/e2e` | DataContext, GA4 client, Drive client, error paths, components, chat, charts, forecasting, session, all Python logic |
| Error-Path E1-E6 | 7 | `pytest tests/test_drive_import_errors.py -v` | `access_denied`, `not_found`, `unsupported_type`, `too_large`, `empty_file`, `download_failed` + success path |
| Playwright Smoke | 14 | `DRIVE_PICKER_TEST_MODE=1 pytest tests/test_drive_import_smoke.py -v` | App loads, sidebar visible, no credential leaks, import button visibility, on-demand render, cancel, error, theme sync, duplicate protection |
| E2E Real-Drive Leakage | 8 | `E2E_REAL_DRIVE=1 pytest tests/e2e/test_drive_picker_e2e.py -v` | L1-L5 sensitive-output checks (no Drive IDs, raw errors, OAuth tokens, API keys, Picker filenames in page source) |
| Frontend Typecheck + Build | — | `cd components/drive_picker_component_frontend && npm ci && npm run check && npm run build` | TypeScript compilation, Vite production build |

---

## How to Run — Complete Validation Sequence

Run these in order from the project root.  All should pass before signing off.

### 1. Python unit/integration suite
```bash
# All unit + integration tests (excludes Playwright smoke and E2E)
python -m pytest tests/ --ignore=tests/test_drive_import_smoke.py --ignore=tests/e2e -v
```

### 2. Drive error-path simulation (E1-E6)
```bash
# Simulates all 6 DriveImportError codes via dependency injection.
# No real Drive API, OAuth, or Playwright needed.
python -m pytest tests/test_drive_import_errors.py -v
```

### 3. Playwright controlled-state smoke (Phase 3.2b)
```bash
# Requires: playwright installed, Chromium available.
# Uses DRIVE_PICKER_TEST_MODE=1 to bypass OAuth + Picker secrets.
# Covers: button visibility, on-demand render, cancel, error, theme,
#         duplicate protection, import section visibility.
DRIVE_PICKER_TEST_MODE=1 python -m pytest tests/test_drive_import_smoke.py -v
```

### 4. Frontend typecheck + production build
```bash
# Ensures the Picker component TypeScript compiles and builds cleanly.
cd components/drive_picker_component_frontend
npm ci
npm run check
npm run build
cd ../..
```

### 5. Credential guard scan
```bash
# Scans all tracked files for AIza/ya29/AQ. credential-shaped strings.
# Must return exit code 0 (clean).
python scripts/check_credentials.py
```

### 6. E2E real-Drive leakage (Phase 3.3 L1-L5) — one-time setup required first
```bash
# ── One-time setup (interactive, requires real Google account) ──
# Place dummy CSV, XLSX, and native Google Sheets files in your Drive.
# Then save a Playwright auth session:
E2E_REAL_DRIVE=1 python tests/e2e/auth_setup.py

# ── Set env vars with your test file display names ──
export E2E_CSV_FILE_NAME="dummy-ga4-export-messy"
export E2E_XLSX_FILE_NAME="dummy-ga4-export"
export E2E_SHEET_FILE_NAME="dummy-ga4-export-sheets"

# ── Run leakage tests ──
E2E_REAL_DRIVE=1 python -m pytest tests/e2e/test_drive_picker_e2e.py -v
```

### 7. Full clean-checkout validation
```bash
# From a clean clone (no cached session state):
python -m pytest tests/ --ignore=tests/test_drive_import_smoke.py --ignore=tests/e2e -v
DRIVE_PICKER_TEST_MODE=1 python -m pytest tests/test_drive_import_smoke.py -v
python scripts/check_credentials.py
cd components/drive_picker_component_frontend && npm ci && npm run check && npm run build
```

---

## Phase 3.3: Manual Cross-Browser Matrix

> **Execute after automated gates are green.** Record date, environment, browser version, pass/fail, tester, and any exception.
>
> **Already automated (no manual verification needed for these):**
> - L1-L5 Sensitive-output leakage (covered by E2E suite — 8 tests)
> - E1-E6 Error-path user-safe messages (covered by error-path suite — 7 tests)
> - Button visibility, on-demand render, cancel/error/theme/duplicate states (covered by smoke suite — 14 tests)

### Environment Matrix

| # | OS | Browser | Date | Version | Result | Tester | Notes |
|---|---|---|---|---|---|---|---|
| 1 | macOS | Chrome | 2026-08-03 | — | ✅ | griffinkelton | Functional #1-#8 all pass |
| 2 | macOS | Safari | | | ⬜ | | |
| 3 | macOS | Firefox | | | ⬜ | | |
| 4 | Windows | Chrome | | | ⬜ | | |
| 5 | Windows | Firefox | | | ⬜ | | |

### Functional Matrix (per environment)

| # | Test Case | Expected Result | Chrome/macOS | Safari/macOS | Firefox/macOS | Chrome/Win | Firefox/Win |
|---|---|---|---|---|---|---|---|
| 1 | GA4 sign-in → Drive Import section visible | Section header + button appear | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 | Select CSV file via Picker | File imported, data preview renders | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3 | Select XLSX file via Picker | File imported, data preview renders | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 4 | Select native Google Sheets via Picker | First sheet exported as CSV, imported | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 5 | Cancel Picker without selecting | No import, button resets | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 6 | Second import after completed import | New file replaces prior data | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 7 | Theme switch during active Picker flow | Picker iframe receives updated theme | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |
| 8 | Theme switch (reverse) during active Picker flow | Picker iframe receives updated theme | ✅ | ⬜ | ⬜ | ⬜ | ⬜ |

### Error-Path Matrix (per environment)

> **E1-E6 user-safe messages verified by automated unit tests (`tests/test_drive_import_errors.py`).**
> Manual verification confirms the full end-to-end flow from Picker through download to error display.

| # | Error Case | Expected Behavior | Automated | Chrome/macOS | Safari/macOS | Firefox/macOS | Chrome/Win | Firefox/Win |
|---|---|---|---|---|---|---|---|---|
| E1 | Access denied (file not shared) | User-safe error, no raw API text | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E2 | File not found (deleted after Picker) | User-safe error, no raw API text | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E3 | Unsupported type (non-CSV/XLSX/Sheets) | User-safe error, no raw API text | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E4 | Oversized file (>100 MB) | User-safe error, no raw API text | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E5 | Empty file (0 bytes) | User-safe error, no raw API text | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E6 | Generic download failure (network/500) | User-safe error, no raw API text | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

### Sensitive-Output Leakage Check (per environment)

> **L1-L5 verified by automated E2E suite (`tests/e2e/test_drive_picker_e2e.py`).**
> Manual spot-check confirms no regression in real browser rendering.

| # | Check | Automated | Chrome/macOS | Safari/macOS | Firefox/macOS | Chrome/Win | Firefox/Win |
|---|---|---|---|---|---|---|---|
| L1 | No Drive file IDs in page/UI/log output | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L2 | No raw Google error messages in page/UI | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L3 | No OAuth tokens (ya29...) in page/UI | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L4 | No API keys (AIza...) in page/UI | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L5 | No selected-file names from Picker in page/UI | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

---

## Phase 4: Release Closeout

- [ ] Manual browser matrix — Chrome/macOS: ✅ (Functional #1-#8), other envs: deferred
- [ ] Clean checkout: full validation sequence (Section 7 above) — all green
- [ ] Frontend: `npm ci && npm run check && npm run build` — clean
- [ ] Credential guard: `python scripts/check_credentials.py` — clean
- [x] CHANGELOG v0.3.0 entry finalized with final commit hash + test baseline
- [x] Spec status updated to "✅ Complete"
- [ ] Git tag `v0.3.0` created and pushed

### Deferred to v0.3.0→v0.4.0 interstitial
- [ ] Picker sidebar width fix
- [ ] Light mode design polish
- [ ] Cross-browser manual matrix (Safari, Firefox, Windows)

---

## Sign-off

- [ ] Release owner approval: _____________ (date: ______)
- [ ] Manual matrix reviewer: _____________ (date: ______)

---

*Each checkbox requires linked evidence: a test result, PR, commit, or review note. Do not mark complete merely because code was changed.*
