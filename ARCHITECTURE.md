# 🏗️ GA4 Insight Explorer — Architecture & Design

> Complete architecture, design decisions, and build log for the GA4 Insight Explorer.

---

## 📋 Purpose

A local, single-user Streamlit web app for analyzing de-identified Google Analytics 4 data using natural language via the Gemini API. It supports both **file upload** (CSV/XLSX) and **live GA4 connection** (OAuth + Analytics Data API).

---

## 🗂️ Project Structure

```
insights-explorer/
├── app.py                       # Main Streamlit entrypoint — UI, routing, callbacks
├── pages/
│   └── learn.py                 # Interactive Python tutorials (8 tabs)
├── utils/
│   ├── __init__.py
│   ├── data_loader.py           # CSV/XLSX parsing, column validation, stats
│   ├── gemini_client.py         # Gemini API wrapper (error handling, key validation, token tracking)
│   ├── ga4_client.py            # GA4 live connection (OAuth + Analytics Data API, PKCE state persistence)
│   ├── prompt_templates.py      # Prompt construction, sanitization, chart detection
│   └── styles.py                # Custom CSS theme (light/dark) + keyboard shortcut JS
├── components/
│   ├── __init__.py              # UI orchestrator + OAuth callback handler
│   ├── sidebar.py               # File upload, GA4 connect, model selector
│   ├── chat.py                  # Chat interface, streaming, chart rendering, export
│   ├── summary.py               # AI summary generation + display
│   ├── data_preview.py          # Data metrics, filters, quality scorecard
│   └── hero.py                  # Empty-state hero + onboarding
├── tests/
│   ├── conftest.py              # Pytest config — warning filters, global fixtures
│   ├── test_data_loader.py      # 20 tests — file parsing, validation, stats
│   ├── test_gemini_client.py    # 14 tests — API calls, error handling, key validation
│   ├── test_prompt_templates.py # 58 tests — prompts, sanitization, chart detection
│   ├── test_ga4_client.py       # 28 tests — OAuth flow, credentials, GA4 report pull, state persistence
│   ├── test_exports.py          # 8 tests — error classification, Excel/PDF export smoke tests
│   └── ...                      # 15 additional test modules + conftest.py (458 total, 0 warnings)
├── .streamlit/
│   └── config.toml              # Secure defaults (headless, XSRF, CORS)
├── assets/
│   ├── icon.svg                 # Master SVG icon
│   ├── favicon.ico              # Multi-res browser favicon
│   ├── og-image.png             # Social share preview
│   ├── site.webmanifest         # PWA manifest
│   └── icons/                   # 8 PNG sizes (16–512px)
├── scripts/
│   ├── smoke_test.sh            # Headless smoke test
│   └── generate_icons.py        # SVG → PNG/ICO/OG rasterizer
├── cloudbuild.yaml              # CI/CD — auto-run tests on every push (GCP Cloud Build)
├── .env.example                 # API key template + GA4 OAuth path
├── requirements.txt             # Python dependencies
├── .gitignore
├── BUGLOG.md                    # Structured bug log (10 bugs)
├── ORIGINAL_SPEC.md             # Initial spec + compliance checklist
├── IDEAS.md                     # 25 bonus ideas + 10 moonshots
├── DOCUMENTATION_INDEX.md       # Central docs index
├── plans/
│   ├── 00-meta/                 # Archived meta-planning (UNIFIED_PLAN, IMPLEMENTATION_PLAN, ENHANCEMENTS)
│   ├── 00-sprints/              # Archived sprint specs (all ✅)
│   ├── p1-p2/, p3-p4/, p5-p6/   # Archived phase completion docs (all ✅)
│   └── maintenance/             # Post-phase-6 maintenance (active)
│       ├── ✅ 2026-07-29-oauth-scope-remediation-spec.md
│       ├── 🔵 2026-07-29-drive-scope-remediation-plan.md
│       └── ✅ 2026-07-29-drive-export-model-selector-session.md
├── ARCHITECTURE.md              # This file
└── README.md                    # Setup guide + GA4 connection walkthrough
```

---

## 🔧 Design Decisions

### 1. Gemini SDK: `google-genai` (v2.x) over `google.generativeai` (deprecated)
**Decision:** Use the newer `google-genai` SDK (`genai.Client`) instead of the deprecated `google.generativeai`.
**Rationale:** The older SDK is deprecated and emits warnings. The new SDK supports the same models with a cleaner API (`client.models.generate_content()`).

### 2. OAuth Code Exchange: Direct `code=` parameter
**Decision:** Pass the authorization code directly via `flow.fetch_token(code=code)` instead of reconstructing the full callback URL.
**Rationale:** Reconstructing the URL from `st.query_params` is fragile — URL encoding can break, and Streamlit may inject its own params. Passing just the code avoids these issues.

### 3. Prompt Construction: Structured with Security Guardrails
**Decision:** Wrap user questions in `"""..."""` delimiters with a `⚠️ SECURITY` instruction telling Gemini to treat embedded text literally.
**Rationale:** Prevents prompt injection attacks where a user could embed instructions like "Ignore previous instructions and..." inside their question.

### 4. Chart Detection: Heuristic Keyword Matching (Not AI)
**Decision:** After Gemini responds, scan the response text for keywords ("over time", "top 5", etc.) to decide chart type. Use the **actual DataFrame** to generate charts — never AI-generated numbers.
**Rationale:** AI-suggested charts risk hallucination (wrong columns, fabricated data). Heuristic matching on real data is deterministic and safe.

### 5. Caching: `@st.cache_data` on Stable Functions
**Decision:** Cache `validate_columns`, `get_dataset_stats`, and `build_summary_prompt` with `@st.cache_data`. Do NOT cache `build_chat_prompt` or `generate_response`.
**Rationale:** Validation, stats, and summary prompts are deterministic for the same DataFrame. Chat prompts change on every message (unique user questions). API responses must never be cached (they depend on live model state).

### 6. Single-Quote Triple Delimiters for Code Blocks
**Decision:** Use `st.code('''...''')` (single-quote delimiters) instead of `st.code("""...""")` for code snippets in the learn page.
**Rationale:** Python's `"""` inside `"""..."""` prematurely closes the string. Single-quote delimiters avoid this collision since `"""` is common in Python code (docstrings, f-string delimiters).

### 7. Keyboard Shortcuts: JS Injection via `unsafe_allow_html`
**Decision:** Inject keyboard shortcut JavaScript (Cmd/Ctrl+K to focus chat) via `st.markdown(unsafe_allow_html=True)`.
**Rationale:** Streamlit has no native keyboard shortcut API. The JS approach is the standard workaround. Cmd+Enter (submit) was intentionally skipped — `dispatchEvent()` doesn't reliably trigger Streamlit's React event handlers.

### 8. CI/CD: Google Cloud Build
**Decision:** Use `cloudbuild.yaml` with GCP Cloud Build triggers on every push.
**Rationale:** The project already uses GCP for OAuth and GA4 API. Cloud Build integrates natively and has a generous free tier (120 build-minutes/day). The build installs deps in a venv and runs the full 171-test suite.

### 9. OAuth State Persistence: Filesystem-Based PKCE
**Decision:** Persist PKCE `code_verifier` and `redirect_uri` in temp JSON files keyed by the OAuth `state` parameter.
**Rationale:** Streamlit destroys `st.session_state` when Google redirects the browser away for OAuth consent. The filesystem bridge survives the redirect. Files are pruned after 10 minutes, restricted to `chmod(0o600)` (POSIX only), and deleted on one-time-use read.

### 10. Scope Migration Banner: Self-Correcting Re-Auth Flow
**Decision:** Detect stale cached credentials (old broad `drive` scope) via `needs_scope_migration()` using `issubset()`. Show a persistent sidebar warning with a "Reconnect Google Account" button that revokes the old grant server-side before clearing local state.
**Rationale:** Future-proof — any scope change automatically flags stale credentials. Self-correcting: banner disappears once user re-authenticates with new scopes. Server-side revocation ensures the old over-privileged token is dead, not just discarded.

### 11. Shared Error Classification: HTTP Status Code-Based
**Decision:** Use a pure function `_classify_api_error()` that classifies Gemini exceptions by HTTP status code (429/403/500) into emoji-prefixed user-facing messages.
**Rationale:** HTTP status codes are a stable taxonomy — `"429" in str(e)` won't break when Google changes error message text. Emoji prefixes make errors visually parseable. Non-streaming callers `raise RuntimeError(msg) from e`; streaming callers `yield msg; return` to avoid generator exception issues.

### 12. Flash-Only Model Constraint
**Decision:** Restrict `AVAILABLE_MODELS` to free-tier Flash models only (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`). Pro models removed.
**Rationale:** The app is designed for the free tier. Including Pro models creates a footgun — a user selects Pro, gets a billing error, and has no clear path back. The selector should only offer what's guaranteed to work without payment.

---

## 🔄 Data Flow

```
                    ┌──────────────────┐
                    │   User Uploads   │
                    │   CSV / XLSX     │
                    └────────┬─────────┘
                             │
              ┌──────────────▼──────────────┐
              │     data_loader.load_file   │
              │  (parse, validate columns)  │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │  data_loader.get_dataset_   │
              │  stats (row count, dates,   │
              │  column list) [CACHED]      │
              └──────────────┬──────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
│ Generate Summary│ │  Chat Input   │ │ Auto-Chart Gen   │
│ (one-click)     │ │  (per Q&A)    │ │ (post-response)  │
└────────┬────────┘ └───────┬───────┘ └────────┬─────────┘
         │                  │                   │
         ▼                  ▼                   ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
│ build_summary_  │ │ build_chat_   │ │ detect_chart_    │
│ prompt [CACHED] │ │ prompt        │ │ request          │
└────────┬────────┘ └───────┬───────┘ │ (keyword scan)   │
         │                  │         └────────┬─────────┘
         ▼                  ▼                  │
┌──────────────────────────────────────┐       │
│     gemini_client.generate_response  │       │
│     (temperature=0.3, max 2048 tok)  │       │
└──────────────────┬───────────────────┘       │
                   │                           │
                   ▼                           ▼
         ┌─────────────────┐        ┌──────────────────┐
         │  Display in UI  │        │ Plotly chart from │
         │  (markdown card)│        │ actual DataFrame  │
         └─────────────────┘        └──────────────────┘
```

---

## 🔒 Security Model

| Layer | Implementation |
|---|---|
| **API key** | Never hardcoded; read from `.env` via `python-dotenv` |
| **Prompt injection** | `_sanitize_question()` strips code blocks/backticks; triple-quote delimiters + `⚠️ SECURITY` guardrail |
| **Key validation** | `validate_api_key()` runs on startup; persistent error banner if invalid |
| **Data privacy** | Processed in active session; AI calls sent to Gemini API; exports via Google Sheets & Drive |
| **XSRF** | `enableXsrfProtection = true` in `.streamlit/config.toml` |
| **CORS** | `enableCORS = false` — localhost only |
| **Error details** | `showErrorDetails = false` — prevents source leakage |
| **File upload** | Capped at 200 MB via `maxUploadSize` |
| **OAuth secrets** | `client_secrets.json` in `.gitignore`; read from env-configurable path |
| **OAuth scope** | `analytics.readonly` for GA4 data pulls + `drive.file` for user-initiated exports only |
| **Token revocation** | `_revoke_token()` calls Google's `/revoke` endpoint on scope migration, invalidating the old broad-scope grant server-side |
| **OAuth state files** | `chmod(0o600)` on state JSON files (POSIX) — prevents other users on shared systems from reading `code_verifier` |
| **Model access** | `AVAILABLE_MODELS` restricted to free-tier Flash models — no paid-model footgun |
| **Export escaping** | `sanitize.py`: formula injection prevention for Excel/Sheets + PDF XML escaping |
| **Error redaction** | Production mode (`SHOW_DEBUG_DETAILS=false`) hides tracebacks; UUID error IDs shown instead |

---

## 🧪 Test Suite

| Module | Tests | Coverage |
|---|---|---|
| `test_data_loader.py` | 20 | `load_file` (6), `validate_columns` (8), `get_dataset_stats` (6) |
| `test_prompt_templates.py` | 58 | `build_summary_prompt` (9), `build_chat_prompt` (11), `_sanitize_question` (18), `detect_chart_request` (20) |
| `test_gemini_client.py` | 14 | `generate_response` (8), `validate_api_key` (6) |
| `test_ga4_client.py` | 28 | `credentials_to_dict/from_dict` (3), `get_auth_url`/`exchange_code` (7), `pull_ga4_report` (10), `TestOAuthStateStore` (8) |
| `test_exports.py` | 8 | `TestClassifyApiError` (4), `TestExcelExport` (2), `TestPdfExport` (2) |
| `test_learn_page.py` | 19 | Structural parsing, 8 tabs, content checks, back-to-app button |
| `test_error_boundary.py` | 14 | `render_error_card` — 5 exception types, context, stack traces |
| `test_data_quality.py` | 18 | `assess_data_quality` — completeness, duplicates, outliers, grades A–F |
| `test_static_analysis.py` | 12 | All 6 BUGLOG patterns CI-gated: def-before-call, file I/O guard, Streamlit exception guard, on_click anti-pattern, drive.readonly gate, silent except:pass scanner |
| `test_app.py` | 20 | Structural tests for app.py — syntax, imports, structure, session state (#13) |
| _15 additional modules_ | _319_ | `test_chat`, `test_charts`, `test_sidebar`, `test_summary`, `test_forecasting`, `test_funnels`, `test_commands`, `test_drive_client`, `test_custom_metrics`, `test_onboarding`, `test_components_init`, `test_session`, `test_scenarios`, `test_styles`, `test_data_context` |
| **Total** | **458** | All util modules + components + pages + error boundary + data quality + static analysis + scenarios + app structure + data context (0 warnings) |

Mocks used: `unittest.mock.patch` for Gemini API (`_get_client`), GA4 Data API (`BetaAnalyticsDataClient`), OAuth Flow, and token refresh (`Request`).

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥1.28 | UI framework |
| `google-genai` | ≥1.0 | Gemini API (new SDK) |
| `pandas` | ≥2.0 | Data manipulation |
| `plotly` | ≥5.17 | Interactive charts |
| `python-dotenv` | ≥1.0 | Env var management |
| `openpyxl` | ≥3.1 | XLSX file support |
| `google-analytics-data` | ≥0.18 | GA4 Data API |
| `google-api-python-client` | ≥2.0 | Drive API client (file picker, Sheets) |
| `google-auth-oauthlib` | ≥1.0 | OAuth 2.0 flow |
| `requests` | (transitive) | HTTP client — used directly by `_revoke_token()` for Google's OAuth revocation endpoint |
| `reportlab` | (optional) | PDF report generation — lazy-imported with `HAS_REPORTLAB` guard |
| `pytest` | ≥8.0 | Testing framework |
| `cairosvg` | ≥2.7 | SVG-to-PNG rasterization (icon generation script) |
| `pillow` (Pillow) | ≥10.0 | Image manipulation (ICO generation, OG image) |

---

## 📝 Build Log (2026-07-29)

| # | Change | Type |
|---|---|---|
| 1 | Migrated from `google.generativeai` (deprecated) to `google-genai` SDK | Migration |
| 2 | Added GA4 live connection: OAuth sign-in + Analytics Data API | Feature |
| 3 | Added date range selector (7/30/90 days) for GA4 data pull | Feature |
| 4 | Implemented keyboard shortcuts: Cmd/Ctrl+K to focus chat | Feature |
| 5 | Implemented API key validation on startup with persistent error banner | Feature |
| 6 | Implemented prompt injection hardening: `_sanitize_question()` | Security |
| 7 | Extracted CSS to `utils/styles.py` (#6 from roadmap) | Refactor |
| 8 | Added type hints to all functions across the codebase (#7) | Refactor |
| 9 | Added `@st.cache_data` to `validate_columns`, `get_dataset_stats`, `build_summary_prompt` (#10) | Performance |
| 10 | Created `/learn` page — 8 interactive Python tutorials | Feature |
| 11 | Added `.streamlit/config.toml` with secure defaults (#15) | Security |
| 12 | Added `cloudbuild.yaml` for CI/CD — auto-run tests on push | CI/CD |
| 13 | Added 18 tests for `_sanitize_question()` (prompt injection coverage) | Testing |
| 14 | Added 14 tests for `gemini_client.py` (mocked Gemini API) | Testing |
| 15 | Added 18 tests for `ga4_client.py` (OAuth + Analytics Data API) | Testing |
| 16 | Added `pytest` to `requirements.txt` and documented in README | Docs |
| 17 | Added comprehensive GA4 live connection setup guide to README | Docs |
| 18 | Created smoke test: verified app boots, key banner, Cmd+K shortcut | Testing |
| 19 | Test suite: 0 → 110 tests across 4 test modules | Testing |
| 20 | Added `utils/error_boundary.py` — global error boundary (#13) | Feature |
| 21 | Added 19 structural tests for `pages/learn.py` | Testing |
| 22 | Added `scripts/smoke_test.sh` — headless smoke test | CI/CD |
| 23 | Added Back to App button on `/learn` via `st.page_link` | Feature |
| 24 | Rewrote `ENHANCEMENTS.md` v2 — 37 enhancements across 7 categories | Docs |
| 25 | Added `IMPLEMENTATION_PLAN.md` — 21-item execution blueprint | Docs |
| 26 | Added `IDEAS.md` — 25 bonus enhancements + 10 moonshots | Docs |
| 27 | Added `ORIGINAL_SPEC.md` — initial prompt + compliance checklist | Docs |
| 28 | Added `DOCUMENTATION_INDEX.md` — central doc index | Docs |
| 29 | Added `plans/` directory — Phase 5 detailed plans + bonus plans | Docs |
| 30 | Implemented P1: App Icon — custom SVG, 8 PNG sizes, ICO, PWA manifest, OG image, favicon meta tags | Feature |
| 31 | Fixed privacy disclaimer wording to match ORIGINAL_SPEC.md requirement #15 verbatim | Fix |
| 32 | Added BUGLOG.md cross-references to DOCUMENTATION_INDEX.md, README.md, and ARCHITECTURE.md | Docs |
| 33 | Docs consistency sweep — updated test counts (110→129), project structures, build log | Docs |
| 34 | Implemented P2: Data Quality Scorecard — A-F grading, styled card, 18 tests | Feature |
| 35 | Added 14 unit tests for `utils/error_boundary.py` — `render_error_card()` | Testing |
| 36 | BUG-008: Full `except Exception` audit — 11 instances across 5 files, 9 safe, 2 documented risks | Audit |
| 37 | Added `tests/test_static_analysis.py` — def-before-call AST linter + file I/O guard (BUGLOG Patterns 3 & 4 gated) | Testing |
| 38 | Fixed BUG-005: replaced `on_click=lambda` with `if st.button` + `st.spinner()` for summary generation | Fix |
| 39 | Added Pattern 1 linter: Streamlit exception guard check (BUG-001 CI gate) | Testing |
| 40 | Added Pattern 2 linter: `on_click` anti-pattern detection (BUG-005 CI gate) | Testing |
| 41 | P1-P3 sprint: #4 file size/row limits (100MB, 50k rows) + download truncated slice | Feature |
| 42 | P1-P3 sprint: #5 rate limiting (2-sec debounce + API call counter) | Feature |
| 43 | P1-P3 sprint: #1 learn page sidebar link (`st.page_link`) | Feature |
| 44 | P1-P3 sprint: OAuth redirect configurability (`OAUTH_REDIRECT_URI` env var) | Feature |
| 45 | P1-P3 sprint: #2 learn page test count updated (92 → 171) | Fix |
| 46 | P1-P3 sprint: #10 pytest-cov coverage reporting | Infra |
| 47 | P1-P3 sprint: #11 split dev dependencies (requirements/base.txt + dev.txt) | Infra |
| 48 | P1-P3 sprint: #12 per-module test badges in README | Docs |
| 49 | P1-P3 sprint: #13 app.py structural test (20 tests) | Testing |
| 50 | P1-P3 sprint: #14 GitHub Actions CI | CI/CD |
| 51 | P1-P3 sprint: #9 free-tier limits documented in README | Docs |
| 52 | P1-P3 sprint: cross-reference sweep across 12 MD files | Docs |
| 53 | P4 Wave 1 + Streaming: #19 streaming (st.write_stream, generate_response_stream) | Feature |
| 54 | P4 Wave 1 + Streaming: #15 column picker & date filters (filter_dataframe, _render_data_filters) | Feature |
| 55 | P4 Wave 1 + Streaming: #16 conversation memory (last 5 exchanges in build_chat_prompt, New Chat button) | Feature |
| 56 | P4 Wave 1 + Streaming: #17 export chat as Markdown report (report_exporter.py, kaleido) | Feature |
| 57-63 | OAuth security hardening: scope reduction (drive→analytics.readonly+drive.file), PKCE state persistence with chmod hardening, scope migration banner with server-side token revocation, shared error classification (_classify_api_error), thought/cached token tracking, 8 smoke tests (test_exports.py), dead code cleanup (ga4_auth_flow, Pro model), BUG-009 & BUG-010, file reorganization (plans/maintenance/) | Remediation |

---

## 📖 Further Reading

- [README.md](README.md) — Setup guide, features, quick start
- [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) — The initial project prompt + compliance checklist
- [ENHANCEMENTS.md](plans/00-meta/ENHANCEMENTS.md) — 37-item enhancement roadmap
- [IMPLEMENTATION_PLAN.md](plans/00-meta/IMPLEMENTATION_PLAN.md) — 21-item execution blueprint with sprint plan
- [IDEAS.md](IDEAS.md) — 25 bonus enhancements + 10 moonshot ideas
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central index of all documentation
- [BUGLOG.md](BUGLOG.md) — Structured bug log with root causes, fixes, and learnings (10 bugs)
- [plans/00-meta/✅ UNIFIED_PLAN.md](plans/00-meta/✅ UNIFIED_PLAN.md) — Master execution plan (6 phase plans + 5 derived sprint plans)
- [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) — OAuth security hardening & code quality remediation spec
- [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md) — P1–P3 sprint spec ✅
- [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md) — Sprint completion tracker
- [plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md](plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md) — Active sprint (#15–17, #19)
- [plans/00-meta/✅ P4-future-plan.md](plans/00-meta/✅ P4-future-plan.md) — Future-phase plan
- [plans/00-meta/✅ P4-deferred-plan.md](plans/00-meta/✅ P4-deferred-plan.md) — Deferred items (Batches C–F)
- [plans/p5-p6/✅ COMPONENT_REFACTOR.md](plans/p5-p6/✅ COMPONENT_REFACTOR.md) — #20 component refactor mini-spec
- [CHANGELOG.md](CHANGELOG.md) — Unified change history
