# Remediation Plan Prompt — GA4 Insight Explorer

**Purpose:** Prompt for Freebuff `/plan` to remediate uncommitted session changes before commit/push.

---

## Context

The uncommitted changes from the last session (OAuth persistence, Drive write-back, model selector, token tracking, export formats, light mode CSS) need a remediation pass before commit/push. Code review surfaced 2 critical issues, 1 security hardening item, and 2 quality gaps. Plan the fixes in priority order, smallest safe diff first.

---

## Critical — fix before anything else

### 1. OAuth scope over-privileged

`utils/ga4_client.py` currently requests the full `https://www.googleapis.com/auth/drive` scope, which grants read/write access to the user's entire Drive.

**Fix:** Change to `https://www.googleapis.com/auth/drive.file` — this restricts access to files the app creates or files the user explicitly picks via the file picker, and covers 100% of the current write-back use case (`write_drive_file`, `create_google_sheet`, `write_dataframe_to_drive`).

**Verify:** Confirm the Drive picker flow (existing file reads) still works under `drive.file` — it should, since it uses the picker pattern. If arbitrary existing-file reads outside the picker are required anywhere, flag that as a separate scope decision rather than silently reverting to broad `drive`.

### 2. ReportLab import contradiction

`utils/report_exporter.py`'s PDF export was described as having a "lazy import with graceful degradation" but is also flagged as crashing at module-level import if ReportLab isn't installed. These are inconsistent.

**Fix:** Audit the actual import statement. If it's module-level, move it inside `build_pdf_report()` matching the existing `HAS_OPENPYXL` guard pattern used for the Excel exporter. The app must not crash on `import report_exporter` in environments without ReportLab installed.

---

## Security hardening

### 3. OAuth state file permissions

`save_oauth_state()` in `utils/ga4_client.py` writes `code_verifier` to temp JSON files.

**Fix:** Add `os.chmod(path, 0o600)` immediately after write so the file isn't world-readable on shared/multi-user systems.

**Verify:** Confirm `state` is generated via a cryptographically secure random source (not predictable), since it now doubles as a lookup key for sensitive material on disk.

---

## Quality gaps — add before commit

### 4. Missing test coverage

Six new functions have zero tests:

- `write_drive_file` (drive_client.py)
- `write_dataframe_to_drive` (drive_client.py)
- `create_google_sheet` (drive_client.py)
- `build_excel_report` (report_exporter.py)
- `build_pdf_report` (report_exporter.py)
- `analyze_file_with_gemini` (gemini_client.py)

**Fix:** Add smoke tests minimum:
- Valid input doesn't raise
- Invalid/missing credentials returns a handled error, not a crash
- Lazy-import guards work when the optional dependency is absent (mock `HAS_OPENPYXL`/`HAS_REPORTLAB` as `False` and confirm graceful fallback)

### 5. Duplicated API error handling

`generate_response()`, `generate_response_stream()`, and `analyze_file_with_gemini()` in `gemini_client.py` likely repeat the same try/except, rate-limit, and token-tracking scaffolding three times.

**Fix:** Extract a shared `_call_api_with_model()` helper if the duplication is confirmed.

---

## Process constraint

Do not bundle all fixes into one commit. Sequence as:

1. Scope fix + confirm existing OAuth tests still pass
2. ReportLab import fix
3. File permissions
4. New tests
5. Refactor duplication if time permits

Each step should be independently verifiable before moving to the next.
