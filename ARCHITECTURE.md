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
│   ├── gemini_client.py         # Gemini API wrapper (error handling, key validation)
│   ├── ga4_client.py            # GA4 live connection (OAuth + Analytics Data API)
│   ├── prompt_templates.py      # Prompt construction, sanitization, chart detection
│   └── styles.py                # Custom CSS theme + keyboard shortcut JS
├── tests/
│   ├── test_data_loader.py      # 20 tests — file parsing, validation, stats
│   ├── test_gemini_client.py    # 14 tests — API calls, error handling, key validation
│   ├── test_prompt_templates.py # 58 tests — prompts, sanitization, chart detection
│   ├── test_ga4_client.py       # 18 tests — OAuth flow, credentials, GA4 report pull
│   └── test_learn_page.py       # 19 tests — learn page structure, content, tabs
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
├── BUGLOG.md                    # Structured bug log
├── ORIGINAL_SPEC.md             # Initial spec + compliance checklist
├── IDEAS.md                     # 25 bonus ideas + 10 moonshots
├── DOCUMENTATION_INDEX.md       # Central docs index
├── ENHANCEMENTS.md              # 37-item enhancement roadmap
├── IMPLEMENTATION_PLAN.md       # 21-item execution blueprint
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
**Rationale:** The project already uses GCP for OAuth and GA4 API. Cloud Build integrates natively and has a generous free tier (120 build-minutes/day). The build installs deps in a venv and runs the full 129-test suite.

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
| **Data privacy** | All in-memory only; no disk, database, or model training |
| **XSRF** | `enableXsrfProtection = true` in `.streamlit/config.toml` |
| **CORS** | `enableCORS = false` — localhost only |
| **Error details** | `showErrorDetails = false` — prevents source leakage |
| **File upload** | Capped at 200 MB via `maxUploadSize` |
| **OAuth secrets** | `client_secrets.json` in `.gitignore`; read from env-configurable path |

---

## 🧪 Test Suite

| Module | Tests | Coverage |
|---|---|---|
| `test_data_loader.py` | 20 | `load_file` (6), `validate_columns` (8), `get_dataset_stats` (6) |
| `test_prompt_templates.py` | 58 | `build_summary_prompt` (9), `build_chat_prompt` (11), `_sanitize_question` (18), `detect_chart_request` (20) |
| `test_gemini_client.py` | 14 | `generate_response` (8), `validate_api_key` (6) |
| `test_ga4_client.py` | 18 | `credentials_to_dict/from_dict` (3), `get_auth_url`/`exchange_code` (5), `pull_ga4_report` (10) |
| `test_learn_page.py` | 19 | Structural parsing, 8 tabs, content checks, back-to-app button |
| **Total** | **129** | All util modules + learn page covered |

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
| `google-auth-oauthlib` | ≥1.0 | OAuth 2.0 flow |
| `pytest` | ≥8.0 | Testing framework |
| `cairosvg` | ≥2.7 | SVG-to-PNG rasterization (icon generation script) |
| `pillow` (Pillow) | ≥10.0 | Image manipulation (ICO generation, OG image) |

---

## 📝 Build Log (Today)

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

---

## 📖 Further Reading

- [README.md](README.md) — Setup guide, features, quick start
- [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) — The initial project prompt + compliance checklist
- [ENHANCEMENTS.md](ENHANCEMENTS.md) — 37-item enhancement roadmap
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — 21-item execution blueprint with sprint plan
- [IDEAS.md](IDEAS.md) — 25 bonus enhancements + 10 moonshot ideas
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central index of all documentation
- [BUGLOG.md](BUGLOG.md) — Structured bug log with root causes, fixes, and learnings
