# Test-Layer Inventory
## Which of the 742 tests transfer to the FastAPI + React stack (and which don't)

**Date:** 2026-08-05
**Method:** `pytest tests/ --collect-only -q` on 2026-08-05 → **782 collected** = 742 unit + 32 smoke (`test_drive_import_smoke.py`) + 8 e2e (`tests/e2e/`). Each unit-test file below was classified by what it exercises: `utils/` (framework-free logic) vs `components/` + `app.py` + `pages/` (Streamlit UI layer).
**Purpose:** substantiate the plan's claim that "the 742-test count won't transfer one-to-one" (plan risk row) and give Phase 6 a concrete retirement/rewrite checklist. Maps onto the Batch 3 four-layer test matrix (Python unit · FastAPI contract · React unit/component · Playwright E2E).

> Bottom line: **452 of 742 (61%) transfer as-is** (utils-facing); **290 (39%) are Streamlit-layer** and must be rewritten as API-contract / React component tests or retired with the UI. Plus 32 Playwright smoke + 8 E2E stay as E2E.

## 1. Keep — utils-facing Python tests (452 tests, 61%)

These exercise framework-free logic and transfer unchanged to the FastAPI backend. No rewrite needed beyond import-path stability.

| File | Count | Notes |
|---|---|---|
| `test_data_context.py` | 112 | DataContext state machine — the core domain object |
| `test_prompt_templates.py` | 61 | Prompt assembly (keep server-side; the whisperer's hardcoded prompts must NOT replace these — Batch 3) |
| `test_forecasting.py` | 31 | Pure forecasting math |
| `test_ga4_client.py` | 27 | GA4 client (OAuth + reports) — keep, verify against live client at Phase 5 |
| `test_static_analysis.py` | 25 | Tooling/structure checks — keep; drop the Streamlit-coupled cases (session_state/theme strings) |
| `test_funnels.py` | 24 | Funnel math — scope to template funnels at Phase 3 (plan amendment) |
| `test_commands.py` | 22 | Chat command parsing → becomes server-side `/api/chat` command handling |
| `test_drive_client.py` | 21 | Drive download guards + error taxonomy (the 100 MB `MAX_DRIVE_IMPORT_BYTES` guard lives here) |
| `test_data_loader.py` | 20 | CSV/XLSX parsing — keep; the API upload adapter wraps this (F4 §6) |
| `test_custom_metrics.py` | 20 | Metric DSL |
| `test_data_quality.py` | 18 | Quality scorecard → `GET /api/data/quality` |
| `test_charts.py` | 18 | Chart data shaping → `GET /api/data/charts` |
| `test_credential_guard.py` | 15 | Security gate — keep + extend to FastAPI env vars |
| `test_gemini_client.py` | 14 | Gemini client → `/api/chat`; prune the shut-down `gemini-2.0-flash` cases (round-3, §3.10 item 7) |
| `test_exports.py` | 8 | Export logic → `POST /api/export` |
| `test_token_safety.py` | 6 | Secret-redaction guarantees — keep (applies to the API boundary) |
| `test_drive_import_errors.py` | 7 | Drive error taxonomy |
| `test_session.py` | 3 | Session-state defaults → replaced by FastAPI session tests (F4 §4), keep the logic |

**Sum: 452**

## 2. Rewrite or retire — Streamlit-layer tests (290 tests, 39%)

These target `components/`, `app.py`, or `pages/`. They don't transfer as-is; each has a mapped destination in the new stack.

| File | Count | Destination |
|---|---|---|
| `test_styles.py` | 68 | **Retire with the Streamlit presentation layer** (`utils/styles.py` is Streamlit-only per plan Phase 2). Design-token checks, if wanted, become React/CSS storybook checks |
| `test_sidebar.py` | 45 | **API-contract** (sidebar is the Drive/GA4/upload entry surface → the endpoints) + React component tests |
| `test_learn_page.py` | 43 | **React component + Playwright E2E** (Learn page renders in the SPA) |
| `test_onboarding.py` | 29 | **React component + Playwright** (onboarding tour) |
| `test_scenarios.py` | 27 | **Playwright E2E** (user-flow scenarios: upload → preview → chat → export) |
| `test_drive_picker_component.py` | 19 | **React component tests** (native Picker component, Phase 5) + MSW |
| `test_app.py` | 16 | **API-contract + smoke** (app wiring → endpoint wiring) |
| `test_error_boundary.py` | 9 | **React component tests** (error states) |
| `test_data_preview.py` | 9 | **API-contract** (`GET /api/data/preview`) + React |
| `test_hero.py` | 7 | **React component tests** (empty-state hero) |
| `test_components_init.py` | 7 | **Keep as an import-structure check** (components package integrity) |
| `test_chat.py` | 6 | **React chat tests with MSW** (streaming via `getReader()`, not `EventSource` — §3.10 item 4) |
| `test_summary.py` | 5 | **API-contract** (`mode: "summary"` chat) + React |

**Sum: 290**

## 3. Stay as E2E (40 tests)

| File | Count | Role |
|---|---|---|
| `test_drive_import_smoke.py` | 32 | Playwright smoke — keep, extend for the new stack |
| `tests/e2e/` (auth-state + leakage) | 8 | Playwright E2E — keep the no-secret-leakage guarantees for the API/React UI |

## 4. Phase 6 checklist (from this inventory)

- [ ] `test_*` files in §1 → move under `tests/api/` or keep as `tests/utils/` — **zero rewrite required**, run against the same Python code via FastAPI.
- [ ] §2 files → one-by-one: API-contract tests for the endpoint each component drove; React component tests for the UI; Playwright E2E for the flows. `test_styles.py` retires outright.
- [ ] Keep the credential/security files (`test_credential_guard.py`, `test_token_safety.py`) green in both eras — they guard the API boundary now.
- [ ] Track the count delta in the CHANGELOG: 742 unit → (452 kept + new API-contract/React suites). Do not claim "742 tests still pass post-migration" — that number is a pre-migration baseline.

---

*Cross-refs: plan Phase 6 (retire Streamlit tests) + risk row · Batch 3 four-layer matrix · F4 §12 test strategy · `../README.md`.*
