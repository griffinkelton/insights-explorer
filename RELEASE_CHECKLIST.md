# v0.3.0 Release Checklist

> **Release:** v0.3.0 — Drive Import
> **Date:** TBD (pending manual matrix)
> **Release owner:** griffinkelton
> **Tests:** 663 (pytest, non-smoke) + 14 Playwright smoke

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

---

## Phase 3.3: Manual Cross-Browser Matrix

> **Execute after automated gates are green.** Record date, environment, browser version, pass/fail, tester, and any exception.

### Environment Matrix

| # | OS | Browser | Date | Version | Result | Tester | Notes |
|---|---|---|---|---|---|---|---|
| 1 | macOS | Chrome | | | ⬜ | | |
| 2 | macOS | Safari | | | ⬜ | | |
| 3 | macOS | Firefox | | | ⬜ | | |
| 4 | Windows | Chrome | | | ⬜ | | |
| 5 | Windows | Firefox | | | ⬜ | | |

### Functional Matrix (per environment)

| # | Test Case | Expected Result | Chrome/macOS | Safari/macOS | Firefox/macOS | Chrome/Win | Firefox/Win |
|---|---|---|---|---|---|---|---|
| 1 | GA4 sign-in → Drive Import section visible | Section header + button appear | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 2 | Select CSV file via Picker | File imported, data preview renders | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 3 | Select XLSX file via Picker | File imported, data preview renders | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 4 | Select native Google Sheets via Picker | First sheet exported as CSV, imported | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 5 | Cancel Picker without selecting | No import, button resets to "Import from Google Drive" | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 6 | Second import after completed import | New file replaces prior data, no stale state | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 7 | Theme switch (dark→light) during active Picker flow | Picker iframe receives updated theme | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| 8 | Theme switch (light→dark) during active Picker flow | Picker iframe receives updated theme | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

### Error-Path Matrix (per environment)

| # | Error Case | Expected Behavior | Chrome/macOS | Safari/macOS | Firefox/macOS | Chrome/Win | Firefox/Win |
|---|---|---|---|---|---|---|---|
| E1 | Access denied (file not shared) | User-safe error, no raw API text | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E2 | File not found (deleted after Picker) | User-safe error, no raw API text | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E3 | Unsupported type (non-CSV/XLSX/Sheets) | User-safe error, no raw API text | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E4 | Oversized file (>100 MB) | User-safe error, no raw API text | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E5 | Empty file (0 bytes) | User-safe error, no raw API text | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E6 | Generic download failure (network/500) | User-safe error, no raw API text | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

### Sensitive-Output Leakage Check (per environment)

| # | Check | Chrome/macOS | Safari/macOS | Firefox/macOS | Chrome/Win | Firefox/Win |
|---|---|---|---|---|---|---|
| L1 | No Drive file IDs in page/UI/log output | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L2 | No raw Google error messages in page/UI | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L3 | No OAuth tokens (ya29...) in page/UI | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L4 | No API keys (AIza...) in page/UI | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| L5 | No selected-file names from Picker in page/UI | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

---

## Phase 4: Release Closeout

- [ ] Manual browser matrix complete (all 5 environments, all test cases pass)
- [ ] Error-path matrix complete (all 6 error cases produce user-safe messages)
- [ ] Sensitive-output leakage check complete (no Drive IDs, raw errors, tokens, keys, or Picker filenames)
- [ ] CHANGELOG v0.3.0 entry finalized with commit hashes
- [ ] Spec status updated to "✅ Complete"
- [ ] README test count updated to final baseline
- [ ] Clean checkout: `pytest tests/ --ignore=tests/test_drive_import_smoke.py -v` — all pass
- [ ] Clean checkout: Playwright job green in CI
- [ ] Frontend: `npm ci && npm run check && npm run build` — clean
- [ ] Credential guard: `git ls-files -z | xargs -0 python scripts/check_credentials.py` — clean
- [ ] Git tag `v0.3.0` created

---

## Sign-off

- [ ] Release owner approval: _____________ (date: ______)
- [ ] Manual matrix reviewer: _____________ (date: ______)

---

*Each checkbox requires linked evidence: a test result, PR, commit, or review note. Do not mark complete merely because code was changed.*
