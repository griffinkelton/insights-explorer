# 📝 Changelog — GA4 Insight Explorer

> All notable changes to this project, tracked with commit hashes, dates, and links to related documentation.
>
> Repo: [github.com/griffinkelton/insights-explorer](https://github.com/griffinkelton/insights-explorer)

---

---

### Theme Toggle Executed — 4 phases, light/dark mode, 231 tests

**Date:** 2026-07-28 | **Status:** ✅ Done

| Phase | What | Files |
|---|---|---|
| 1 | Light theme CSS variables + theme param for `inject_custom_css()` | `utils/styles.py` |
| 2 | Session state + toggle button + wiring | `app.py`, `components/sidebar.py`, `components/__init__.py` |
| 3 | Theme-aware chart generation + Plotly cache-busting | `utils/charts.py`, `components/chat.py` |
| 4 | Learn page: delete standalone CSS, use `inject_custom_css()` | `pages/learn.py`, `utils/styles.py` |

**Key decisions (9 from 3 interview rounds):**
- Syntax tokens: background-only (dark colors on white = legible)
- Default: always dark (no `prefers-color-scheme` detection)
- Toggle: bottom of sidebar (learn link → theme → footer)
- Persistence: session-only (`st.session_state`)
- Learn page: same CSS function, standalone block deleted
- Plotly: theme-tagged cache keys (`chart_0_dark` / `chart_0_light`)
- Charts: `generate_chart()` accepts `theme` param for testability
- Hero gradient: darker purples in light mode for contrast
- Learn page styles: concept cards/tips/tabs use CSS variables

**Related:** [plans/p3-p4/✅ THEME_TOGGLE.md](plans/p3-p4/✅ THEME_TOGGLE.md), [plans/00-sprints/✅ theme-toggle-spec.md](plans/00-sprints/✅ theme-toggle-spec.md)

---

### Component Refactor Executed — 7 phases, app.py 809→78 lines, 228 tests

**Date:** 2026-07-28 | **Status:** ✅ Done

| Phase | What | Files |
|---|---|---|
| 1 | Extracted `utils/charts.py` + `utils/session.py` | `utils/charts.py` (new), `utils/session.py` (new), `app.py` |
| 2 | Extracted `components/hero.py` — empty state | `components/hero.py` (new) |
| 3 | Extracted `components/data_preview.py` — metrics, filters, quality | `components/data_preview.py` (new) |
| 4 | Extracted `components/summary.py` — AI summary | `components/summary.py` (new) |
| 5 | Extracted `components/chat.py` — chat, streaming, export | `components/chat.py` (new) |
| 6 | Extracted `components/sidebar.py` — sidebar + file processing | `components/sidebar.py` (new) |
| 7 | Created `components/__init__.py` orchestrator, rewrote `app.py` | `components/__init__.py` (new), `app.py` (rewritten) |

**Key decisions:**
- `clear_data()` lives in `utils/session.py` (shared by sidebar + orchestrator)
- BUG-005 fixed: `on_click=clear_data` → `if st.button` + `st.rerun()` pattern
- `_stream_chat_response` moved as-is with in-place mutation docstring
- Footer moved to `components/__init__.py`
- Widget key audit: all 4 keys unique, no collisions
- Test coverage: 194 → 228 (34 new tests across 8 modules)

**Related:** [plans/p5-p6/✅ COMPONENT_REFACTOR.md](plans/p5-p6/✅ COMPONENT_REFACTOR.md), [plans/00-sprints/✅ component-refactor-spec.md](plans/00-sprints/✅ component-refactor-spec.md)

---

### P4 Wave 1 + Streaming Sprint Executed — 4/4 items, 194 tests

**Date:** 2026-07-28 | **Status:** ✅ Done

| Item | What | Files |
|---|---|---|
| #19 | Streaming token-by-token responses (st.write_stream, generate_response_stream) | `utils/gemini_client.py`, `app.py` |
| #15 | Column picker & date filters (filter_dataframe, _render_data_filters) | `utils/data_loader.py`, `app.py` |
| #16 | Conversation memory (last 5 exchanges, New Chat button) | `utils/prompt_templates.py`, `app.py` |
| #17 | Export chat as Markdown report (report_exporter.py, kaleido) | `utils/report_exporter.py` (new), `app.py`, `requirements.txt` |

**Related:** [plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md](plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md), [plans/00-meta/📋 P4-future-plan.md](plans/00-meta/📋 P4-future-plan.md)

---

### P1–P3 Sprint Executed — 12 items implemented across 5 batches

**Date:** 2026-07-28 | **Tests:** 171 → 194

| Batch | Items | Status |
|---|---|---|
| Batch 1 (Safety) | #4 file limits + download slice, #5 rate limiting | ✅ |
| Batch 2 (Quick Wins) | #1 learn sidebar link, NEW-A OAuth redirect config | ✅ |
| Batch 3 (Docs) | #2 test count update, #3 doc updates, #9 README learn link | ✅ |
| Batch 4 (UX) | #8 onboarding tour | ⚠️ Deferred |
| Batch 5 (Infra) | #10 pytest-cov, #11 dev deps split, #12 test badges, #13 app.py structural test (20 tests), #14 GitHub Actions CI | ✅ |

**Key changes:**
- `utils/data_loader.py`: Added 100MB/50k-row limits, BytesIO parsing, 3-tuple return with warning
- `app.py`: Rate limiting (2-sec debounce + counter), learn sidebar link, OAuth env config, 3-tuple unpacking
- New `tests/test_app.py`: 20 structural tests (syntax, imports, structure, session state)
- New `.github/workflows/test.yml`: GitHub Actions CI pipeline
- New `requirements/base.txt` + `requirements/dev.txt`: Dev/prod dependency split
- `README.md`: Test breakdown table, GitHub Actions badge, learn page access, free-tier limits
- `ENHANCEMENTS.md` + `ARCHITECTURE.md`: Progress counts updated (15→22/37 done)

**Related:** [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md), [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md)

| Change | Commit | Related Docs |
|---|---|---|
| **P1–P3 sprint executed — 12 items implemented across 5 batches** | `83aef98` | [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md), [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md) |

---

## 2026-07-28 — Static Analysis & Anti-Pattern Fixes

### Added Patterns 1 & 2 linters + fix BUG-005 on_click anti-pattern + docs sweep

**Commit:** [`7404961`](https://github.com/griffinkelton/insights-explorer/commit/7404961)

| Change | Type | Related Docs |
|---|---|---|
| Added Pattern 1 linter: Streamlit exception guard check (BUG-001 CI gate) | Testing | [BUGLOG.md](BUGLOG.md) |
| Added Pattern 2 linter: `on_click` anti-pattern detection (BUG-005 CI gate) | Testing | [BUGLOG.md](BUGLOG.md) |
| Fixed BUG-005: replaced `on_click=lambda` with `if st.button` + `st.spinner()` for summary generation | Fix | [BUGLOG.md](BUGLOG.md) |
| Docs consistency sweep | Docs | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |

---

### Docs consistency sweep: P2 completion + 166 test counts + build log + BUGLOG gating

**Commit:** [`4286c3d`](https://github.com/griffinkelton/insights-explorer/commit/4286c3d)

| Change | Type | Related Docs |
|---|---|---|
| Updated test counts (110 → 129 → 166) across all docs | Docs | [ARCHITECTURE.md](ARCHITECTURE.md), [README.md](README.md) |
| Added P2 Data Quality Scorecard completion entries to build log | Docs | [ARCHITECTURE.md](ARCHITECTURE.md) |
| BUGLOG patterns CI-gated in `test_static_analysis.py` | Testing | [BUGLOG.md](BUGLOG.md) |

---

### Add synthetic tests for def-before-call linter + FileIO fragility docs

**Commit:** [`4946e2a`](https://github.com/griffinkelton/insights-explorer/commit/4946e2a)

| Change | Type | Related Docs |
|---|---|---|
| Added def-before-call AST linter tests | Testing | [BUGLOG.md](BUGLOG.md) |
| Documented FileIO fragility in test contexts | Docs | [BUGLOG.md](BUGLOG.md) |

---

## 2026-07-28 — P2: Data Quality Scorecard

### Implement P2: Data Quality Scorecard — A-F grading, styled card, prompt integration

**Commit:** [`9842065`](https://github.com/griffinkelton/insights-explorer/commit/9842065)

| Change | Type | Related Docs |
|---|---|---|
| Added `DataQualityReport` dataclass + `assess_data_quality()` to `utils/data_loader.py` | Feature | [plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md](plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md) |
| Added `render_quality_scorecard()` to `app.py` — styled A-F grade card | Feature | [plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md](plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md) |
| Added quality section to `build_summary_prompt()` | Feature | [utils/prompt_templates.py](utils/prompt_templates.py) |
| 18 new tests in `test_data_quality.py` | Testing | [tests/test_data_quality.py](tests/test_data_quality.py) |

---

### Mark ORIGINAL_SPEC.md #15 as fully compliant — privacy wording matches spec verbatim

**Commit:** [`fe1fbac`](https://github.com/griffinkelton/insights-explorer/commit/fe1fbac)

| Change | Type | Related Docs |
|---|---|---|
| Fixed privacy disclaimer wording to match original spec exactly | Fix | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |

---

## 2026-07-28 — Error Boundary & BUG-008 Audit

### Add 14 unit tests for utils/error_boundary.py — render_error_card()

**Commit:** [`dd266d6`](https://github.com/griffinkelton/insights-explorer/commit/dd266d6)

| Change | Type | Related Docs |
|---|---|---|
| 14 tests covering 5 exception types, context rendering, stack trace display | Testing | [tests/test_error_boundary.py](tests/test_error_boundary.py) |

---

### BUG-008: Full except Exception audit — 11 instances across 5 files

**Commit:** [`0cc5278`](https://github.com/griffinkelton/insights-explorer/commit/0cc5278)

| Change | Type | Related Docs |
|---|---|---|
| 11 `except Exception` instances audited — 9 safe, 2 documented risks | Audit | [BUGLOG.md](BUGLOG.md) |

---

### Cross-reference audit: add missing BUGLOG.md links to 6 docs

**Commit:** [`863a940`](https://github.com/griffinkelton/insights-explorer/commit/863a940)

| Change | Type | Related Docs |
|---|---|---|
| BUGLOG.md cross-references added to README, ARCHITECTURE, and 4 other docs | Docs | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |

---

### Docs consistency sweep: P1 completion + stale counts + project structure updates

**Commit:** [`67509c3`](https://github.com/griffinkelton/insights-explorer/commit/67509c3)

| Change | Type | Related Docs |
|---|---|---|
| P1 App Icon completion documented across all docs | Docs | [ARCHITECTURE.md](ARCHITECTURE.md), [plans/p1-p2/✅ APP_ICON.md](plans/p1-p2/✅ APP_ICON.md) |
| Stale test counts updated across files | Docs | [README.md](README.md) |

---

### Add BUGLOG.md to DOCUMENTATION_INDEX.md + cross-refs in README and ARCHITECTURE

**Commit:** [`1f45885`](https://github.com/griffinkelton/insights-explorer/commit/1f45885)

| Change | Type | Related Docs |
|---|---|---|
| BUGLOG.md added to documentation index and cross-referenced | Docs | [BUGLOG.md](BUGLOG.md) |

---

### Fix privacy disclaimer wording to match original spec exactly

**Commit:** [`a846780`](https://github.com/griffinkelton/insights-explorer/commit/a846780)

| Change | Type | Related Docs |
|---|---|---|
| Privacy disclaimer now verbatim matches ORIGINAL_SPEC.md #15 | Fix | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |

---

## 2026-07-27 — P1: App Icon & Favicon

### Implement P1: App Icon & Favicon

**Commit:** [`25ca2df`](https://github.com/griffinkelton/insights-explorer/commit/25ca2df)

| Change | Type | Related Docs |
|---|---|---|
| Custom SVG icon + 8 PNG sizes + ICO + PWA manifest + OG image | Feature | [plans/p1-p2/✅ APP_ICON.md](plans/p1-p2/✅ APP_ICON.md) |
| `inject_favicon_meta()` added to `utils/styles.py` | Feature | [utils/styles.py](utils/styles.py) |
| Page configs updated to use custom favicon | Feature | [app.py](app.py), [pages/learn.py](pages/learn.py) |

---

### Apply 7 reviewer fixes to 📋 UNIFIED_PLAN.md + ✅ APP_ICON.md forward-reference fix

**Commit:** [`aad1190`](https://github.com/griffinkelton/insights-explorer/commit/aad1190)

| Change | Type | Related Docs |
|---|---|---|
| 7 review fixes applied to 📋 UNIFIED_PLAN.md | Docs | [plans/00-meta/📋 UNIFIED_PLAN.md](plans/00-meta/📋 UNIFIED_PLAN.md) |

---

## 2026-07-27 — Documentation Foundation

### Add BUGLOG.md — structured bug log with 7 documented bugs

**Commit:** [`ae21220`](https://github.com/griffinkelton/insights-explorer/commit/ae21220)

| Change | Type | Related Docs |
|---|---|---|
| 7 bugs documented with root causes, fixes, learnings, and patterns | Docs | [BUGLOG.md](BUGLOG.md) |

---

### Add app icon plan, bonus idea plan, doc index, cross-references, and fix IMPL plan issues

**Commit:** [`940ebdd`](https://github.com/griffinkelton/insights-explorer/commit/940ebdd)

| Change | Type | Related Docs |
|---|---|---|
| ✅ APP_ICON.md, ✅ BONUS_DATA_QUALITY_SCORECARD.md, DOCUMENTATION_INDEX.md created | Docs | [plans/](plans/) |
| Cross-references and IMPLEMENTATION_PLAN fixes | Docs | [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) |

---

### Add ORIGINAL_SPEC.md — preserve the initial project spec as historical reference

**Commit:** [`6fad5c3`](https://github.com/griffinkelton/insights-explorer/commit/6fad5c3)

| Change | Type | Related Docs |
|---|---|---|
| 26-item compliance checklist + evolution beyond spec documented | Docs | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |

---

### Add Phase 5+ detailed plans + IDEAS.md (25 enhancements + 10 moonshots)

**Commit:** [`c96b0fb`](https://github.com/griffinkelton/insights-explorer/commit/c96b0fb)

| Change | Type | Related Docs |
|---|---|---|
| 4 Phase 5 detailed plans (theme toggle, streaming, component refactor, AI/data) | Docs | [plans/p3-p4/ and plans/p5-p6/](plans/p3-p4/ and plans/p5-p6/) |
| IDEAS.md with 25 bonus enhancements + 10 moonshot ideas | Docs | [IDEAS.md](IDEAS.md) |

---

### Add IMPLEMENTATION_PLAN.md — detailed 21-item execution blueprint

**Commit:** [`585527d`](https://github.com/griffinkelton/insights-explorer/commit/585527d)

| Change | Type | Related Docs |
|---|---|---|
| 21-item plan with file-level precision, risk assessments, sprint plan | Docs | [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) |

---

### Rewrite ENHANCEMENTS.md v2 — 37 enhancements across 7 categories

**Commit:** [`7e964a9`](https://github.com/griffinkelton/insights-explorer/commit/7e964a9)

| Change | Type | Related Docs |
|---|---|---|
| Complete v2 rewrite with progress summary and related docs | Docs | [ENHANCEMENTS.md](ENHANCEMENTS.md) |

---

## 2026-07-26 — Learn Page, Testing, CI/CD

### Add '← Back to App' button to /learn page via st.page_link("app.py")

**Commit:** [`7abfdd7`](https://github.com/griffinkelton/insights-explorer/commit/7abfdd7)

| Change | Type | Related Docs |
|---|---|---|
| Cross-page navigation from learn page back to main app | Feature | [pages/learn.py](pages/learn.py) |

---

### Add 19 structural tests for the /learn page (test_learn_page.py)

**Commit:** [`a66e94d`](https://github.com/griffinkelton/insights-explorer/commit/a66e94d)

| Change | Type | Related Docs |
|---|---|---|
| Structural tests: syntax, imports, 8 tabs, content checks, stale detection | Testing | [tests/test_learn_page.py](tests/test_learn_page.py) |

---

### Add headless smoke test script (scripts/smoke_test.sh)

**Commit:** [`aecbce2`](https://github.com/griffinkelton/insights-explorer/commit/aecbce2)

| Change | Type | Related Docs |
|---|---|---|
| Headless boot verification: HTTP 200, no import errors | CI/CD | [scripts/smoke_test.sh](scripts/smoke_test.sh) |

---

### Add global error boundary (#13) — friendly error cards instead of red tracebacks

**Commit:** [`4fc85c9`](https://github.com/griffinkelton/insights-explorer/commit/4fc85c9)

| Change | Type | Related Docs |
|---|---|---|
| `utils/error_boundary.py` with `render_error_card()` | Feature | [utils/error_boundary.py](utils/error_boundary.py) |

---

## 2026-07-26 — Architecture & Test Suite Expansion

### Add ARCHITECTURE.md + update README and ENHANCEMENTS for completed roadmap items

**Commit:** [`af0eb03`](https://github.com/griffinkelton/insights-explorer/commit/af0eb03)

| Change | Type | Related Docs |
|---|---|---|
| Full architecture doc with design decisions, data flow, security model, build log | Docs | [ARCHITECTURE.md](ARCHITECTURE.md) |

---

### Add 18 unit tests for ga4_client module — completes the test suite

**Commit:** [`a8b518e`](https://github.com/griffinkelton/insights-explorer/commit/a8b518e)

| Change | Type | Related Docs |
|---|---|---|
| OAuth flow, credentials serialization, GA4 report pull tests | Testing | [tests/test_ga4_client.py](tests/test_ga4_client.py) |

---

### Add cloudbuild.yaml for CI/CD — auto-run pytest on every push via Google Cloud Build

**Commit:** [`ebb62e6`](https://github.com/griffinkelton/insights-explorer/commit/ebb62e6)

| Change | Type | Related Docs |
|---|---|---|
| GCP Cloud Build pipeline — install deps + run 171-test suite on every push | CI/CD | [cloudbuild.yaml](cloudbuild.yaml) |

---

### Add .streamlit/config.toml with secure defaults (#15 security enhancement)

**Commit:** [`4128741`](https://github.com/griffinkelton/insights-explorer/commit/4128741)

| Change | Type | Related Docs |
|---|---|---|
| Headless mode, XSRF protection, CORS disabled, 200MB upload cap | Security | [.streamlit/config.toml](.streamlit/config.toml) |

---

### Add /learn page — interactive Python & code walkthrough for the app

**Commit:** [`5ba31c5`](https://github.com/griffinkelton/insights-explorer/commit/5ba31c5)

| Change | Type | Related Docs |
|---|---|---|
| 8-tab tutorial: Streamlit, Pandas, Plotly, Gemini API, OAuth, Type Hints, Caching, Testing | Feature | [pages/learn.py](pages/learn.py) |

---

## 2026-07-26 — Security & Testing Foundations

### Add 18 unit tests for _sanitize_question() — prompt injection sanitizer

**Commit:** [`ceb7b87`](https://github.com/griffinkelton/insights-explorer/commit/ceb7b87)

| Change | Type | Related Docs |
|---|---|---|
| Prompt injection coverage: code blocks, backticks, whitespace, delimiters | Testing | [tests/test_prompt_templates.py](tests/test_prompt_templates.py) |

---

### Add Streamlit caching (#10): @st.cache_data on 3 functions

**Commit:** [`b569a79`](https://github.com/griffinkelton/insights-explorer/commit/b569a79)

| Change | Type | Related Docs |
|---|---|---|
| `@st.cache_data` on `validate_columns`, `get_dataset_stats`, `build_summary_prompt` | Performance | [utils/data_loader.py](utils/data_loader.py), [utils/prompt_templates.py](utils/prompt_templates.py) |

---

### Add comprehensive GA4 live connection setup guide to README

**Commit:** [`6426c00`](https://github.com/griffinkelton/insights-explorer/commit/6426c00)

| Change | Type | Related Docs |
|---|---|---|
| Step-by-step OAuth setup with ASCII diagrams and troubleshooting table | Docs | [README.md](README.md) |

---

### Add pytest to requirements.txt and document test command in README

**Commit:** [`358e0b7`](https://github.com/griffinkelton/insights-explorer/commit/358e0b7)

| Change | Type | Related Docs |
|---|---|---|
| Testing infrastructure: pytest dependency + README test command | Docs | [README.md](README.md), [requirements.txt](requirements.txt) |

---

### Add 14 unit tests for gemini_client module — mocked Gemini API

**Commit:** [`89d7a87`](https://github.com/griffinkelton/insights-explorer/commit/89d7a87)

| Change | Type | Related Docs |
|---|---|---|
| `generate_response` and `validate_api_key` tests with mocked API | Testing | [tests/test_gemini_client.py](tests/test_gemini_client.py) |

---

### Refactor: extract CSS to utils/styles.py (#6) and add type hints throughout (#7)

**Commit:** [`35661b4`](https://github.com/griffinkelton/insights-explorer/commit/35661b4)

| Change | Type | Related Docs |
|---|---|---|
| 200+ lines of custom CSS extracted to `utils/styles.py` | Refactor | [utils/styles.py](utils/styles.py) |
| `X \| None` type hints across all modules | Refactor | All `.py` files |

---

## 2026-07-25 — Initial Features

### Implement top 3 quick-wins: keyboard shortcuts, API key validation, prompt injection hardening

**Commit:** [`92869b5`](https://github.com/griffinkelton/insights-explorer/commit/92869b5)

| Change | Type | Related Docs |
|---|---|---|
| Cmd/Ctrl+K keyboard shortcut for chat focus | Feature | [utils/styles.py](utils/styles.py) |
| `validate_api_key()` on startup with persistent error banner | Feature | [utils/gemini_client.py](utils/gemini_client.py) |
| `_sanitize_question()` — prompt injection hardening | Security | [utils/prompt_templates.py](utils/prompt_templates.py) |

---

### Add GA4 live connection via OAuth Sign-in with Google and Analytics Data API

**Commit:** [`0288992`](https://github.com/griffinkelton/insights-explorer/commit/0288992)

| Change | Type | Related Docs |
|---|---|---|
| OAuth 2.0 flow + Google Analytics Data API integration | Feature | [utils/ga4_client.py](utils/ga4_client.py) |
| Google Sign-in button, property ID input, 7/30/90 day pull presets | Feature | [app.py](app.py) |

---

### Migrate from deprecated google.generativeai to google.genai SDK (v2.14.0)

**Commit:** [`8476b8f`](https://github.com/griffinkelton/insights-explorer/commit/8476b8f)

| Change | Type | Related Docs |
|---|---|---|
| SDK migration: `google.generativeai` → `google-genai` (`genai.Client`) | Migration | [utils/gemini_client.py](utils/gemini_client.py) |

---

## 2026-07-25 — Testing & Roadmap Foundation

### Add comprehensive pytest unit tests for data_loader and prompt_templates (59 tests)

**Commit:** [`f26e591`](https://github.com/griffinkelton/insights-explorer/commit/f26e591)

| Change | Type | Related Docs |
|---|---|---|
| 59 tests: data loading, validation, stats, prompt construction, chart detection | Testing | [tests/test_data_loader.py](tests/test_data_loader.py), [tests/test_prompt_templates.py](tests/test_prompt_templates.py) |

---

### Add comprehensive enhancement roadmap: 25 ideas across UX, code, security, AI, and data processing

**Commit:** [`5c92a83`](https://github.com/griffinkelton/insights-explorer/commit/5c92a83)

| Change | Type | Related Docs |
|---|---|---|
| Initial ENHANCEMENTS.md — 25 ideas across 5 categories | Docs | [ENHANCEMENTS.md](ENHANCEMENTS.md) |

---

## 2026-07-25 — Initial Commit

### Initial commit: GA4 Insight Explorer

**Commit:** [`c5177cc`](https://github.com/griffinkelton/insights-explorer/commit/c5177cc)

| Change | Type | Related Docs |
|---|---|---|
| Streamlit app with Gemini AI for analyzing GA4 export data | Feature | [app.py](app.py), [utils/](utils/) |
| CSV/XLSX upload, AI summary, chat interface, auto-chart generation | Feature | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |
| Privacy-first: in-memory only, clear data button, privacy disclaimer | Feature | [README.md](README.md) |

---

## 📊 Summary

| Metric | Value |
|---|---|
| Total commits tracked | 43 |
| Date range | July 25–28, 2026 |
| Features shipped | GA4 Insight Explorer core, GA4 live OAuth, keyboard shortcuts, API key validation, prompt injection hardening, error boundary, learn page, data quality scorecard, app icon/favicon |
| Tests | 0 → 228 across 17 modules |
| CI/CD | Cloud Build + smoke test |
| Documentation | 18 MD files totaling 100+ KB |
| Plans | 21-item IMPLEMENTATION_PLAN + 6 UNIFIED plans + 3 derived sprint plans |

---

## 📖 Related Docs

- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central index of all project docs
- [plans/00-meta/📋 UNIFIED_PLAN.md](plans/00-meta/📋 UNIFIED_PLAN.md) — Master execution plan
- [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md) — Current sprint spec
- [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md) — Sprint completion tracker
- [plans/00-meta/📋 P4-future-plan.md](plans/00-meta/📋 P4-future-plan.md) — Future-phase plan

---

---

### v1.5.0 — Google Drive File Picker (2026-07-28)
- **NEW**: `utils/drive_client.py` — list, download, and load Drive CSV/Sheets as DataFrames
- **NEW**: `tests/test_drive_client.py` — 4 tests (list, export, token refresh, bad file)
- **CHANGED**: `utils/ga4_client.py` — added `drive.readonly` OAuth scope
- **CHANGED**: `components/sidebar.py` — `_render_drive_picker()` with file ID-based selectbox, 🔄 refresh button, BUG-005 compliant
- **CHANGED**: `components/sidebar.py` — extracted `_populate_data_state()` shared helper (eliminates triplicated 8-line blocks across upload/GA4/Drive paths)
- **CHANGED**: `app.py` — added `drive_files_cache` session state
- **CHANGED**: `requirements.txt` — added `google-api-python-client>=2.0.0`
- **CHANGED**: `tests/test_sidebar.py` — structural test for `_render_drive_picker()`
- 236 tests (was 231) | Bug fix: upload path now correctly sets `data_source` + clears `summary`/`chat_history` on reload

---

### v1.6.0 — AI & Data Processing Enhancements (2026-07-28)
- **21d**: Column type detection — `detect_column_types()` + colored badges (📅🔢🏷️📝) in data preview
- **21f**: Smart sampling — `smart_sample()` with stratified weekly sampling, replaces `head()` everywhere
- **21a+b**: Chart JSON detection — `[CHART:{json}]` token in prompts, JSON-first `detect_chart_request()` with keyword fallback + retry logic
- **21e**: Anomaly detection — 7-day rolling Z-score, collapsible anomaly table, red X markers on charts
- **21c**: Comparative mode — sidebar toggle, dual-panel charts, `build_comparison_prompt()`
- **CHANGED**: `utils/charts.py` — imports `find_date_column` from `utils/data_loader` (canonical source)
- **CHANGED**: `utils/prompt_templates.py` — chart instruction in chat prompt, JSON + keyword hybrid detection
- **CHANGED**: `components/chat.py` — CHART token stripping (post-detection), retry Gemini call, compare mode dual charts
- **CHANGED**: `components/sidebar.py` — `_render_compare_controls()` between Clear Data and API counter
- **CHANGED**: `app.py` — 5 compare mode session state variables
- **CHANGED**: `utils/styles.py` — `.col-badge` CSS for type badges
- 239 tests (was 236) | +3 JSON chart detection tests, updated 15 keyword tests with `method` tag

---

*This changelog will be updated as each batch from the P1-P3 sprint is completed. Each completed item will be marked with its commit hash, date, files changed, and test impact.*
