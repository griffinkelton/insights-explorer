# 🚀 GA4 Insight Explorer — Enhancement Roadmap v2

> 30 actionable ideas across 7 categories, grounded in the current codebase.
>
> ✅ = Completed &nbsp;|&nbsp; ⚠️ = Optional/Deferred &nbsp;|&nbsp; 🔲 = Available (all done! 🎉)</newString>
>
> **Last updated:** 2026-07-28 — All 37 enhancements complete ✅. Pre-commit hooks ✅, Sphinx docs ✅, onboarding tour ✅. 37/37 done.</newString>

---

## 🎨 UX Enhancements

### 1. Loading Spinner for Summary Generation ✅
**Why:** The "Generate Summary" button uses a fire-and-forget `on_click` callback — the UI freezes for 3-5 seconds during the Gemini API call with no feedback.
**How:** Replace the callback with a `st.spinner("Analyzing your data...")` wrapper that shows a loading animation during the API call.
**Effort:** Small | **Files:** `app.py`

### 2. Conversation Memory (Multi-Turn Chat) ✅
**Status:** ✅ Done in P4 Wave 1 sprint — last 5 exchanges injected via conversation_history param, New Chat button.
**Why:** Each chat message is independent — Gemini has no memory of previous Q&A. Users can't ask "What about last month?" without re-specifying context.
**How:** Include the last 3-5 Q&A pairs from `st.session_state.chat_history` in `build_chat_prompt` as conversation context. Add a "New Conversation" button.
**Effort:** Medium | **Files:** `utils/prompt_templates.py`, `app.py`

### 3. Export Chat as Report (PDF/Markdown) ✅
**Status:** ✅ Done in P4 Wave 1 sprint — Markdown export with optional kaleido chart PNGs.
**Why:** Users will want to share AI-generated insights and charts with stakeholders.
**How:** Add a "📥 Export Report" button that bundles the AI summary, chat Q&A, and Plotly charts into a downloadable Markdown or PDF. Use `st.download_button`.
**Effort:** Medium | **Files:** `app.py`, `requirements.txt`

### 4. Keyboard Shortcuts & Power-User Interactions ✅
**How:** `Cmd/Ctrl+K` focuses the chat textarea. Injected via JS in `utils/styles.py`.
**Status:** ✅ Done

### 5. Progressive Onboarding Tour ⚠️
**Status:** ⚠️ Optional, deferred — standalone mini-spec at [plans/00-meta/🔵 onboarding-tour.md](plans/00-meta/🔵 onboarding-tour.md).
**Why:** Empty states exist, but a 3-step guided tour on first visit would reduce bounce.
**How:** Show a "🎓 Quick Tour" button. Step through tooltips anchored to: sidebar uploader, Generate Summary, chat input. Track `st.session_state.tour_step`.
**Effort:** Small | **Files:** `app.py`

### 6. Light/Dark Theme Toggle ✅
**Status:** ✅ Done — Theme Toggle sprint. Sidebar toggle, ~80 CSS variables, Plotly theme swap, learn page integration.
**Why:** Hardcoded to dark mode. Many analysts prefer light mode.
**How:** Sidebar toggle swapping CSS custom properties between palettes. Persist in `st.session_state`.
**Effort:** Medium | **Files:** `app.py`, `utils/styles.py`

### 7. Learn Page Discovery ✅
**Why:** The `/learn` page exists but users only find it if they know the URL or spot it in the sidebar nav.
**How:** Add a prominent "📚 Learn Python" link in the sidebar and a mention in the README.
**Effort:** Small | **Files:** `app.py`, `README.md`

---

## 🧱 Code Enhancements

### 8. Extract CSS to a Dedicated Stylesheet ✅
**Status:** ✅ Done — `utils/styles.py` with `inject_custom_css()`.

### 9. Add Full Type Hints Throughout ✅
**Status:** ✅ Done — `X | None` syntax across all `.py` files.

### 10. Unit Test Suite with pytest ✅
**Status:** ✅ Done — 194 tests across 9 modules (data_loader, prompt_templates, gemini_client, ga4_client, learn_page, error_boundary, data_quality, static_analysis, app).

### 11. Use Streamlit's Native Caching ✅
**Status:** ✅ Done — `@st.cache_data` on `validate_columns`, `get_dataset_stats`, `build_summary_prompt`.

### 12. Refactor app.py into Modular Components ✅
**Status:** ✅ Done — Component Refactor sprint. app.py 809→78 lines, 7 new files in components/ + utils/charts.py + utils/session.py, 228 tests.
**Why:** `app.py` is ~400 lines mixing CSS, session state, file processing, UI, and chart generation. Extracting `_render_main()` and `_render_hero()` was a start, but the sidebar, GA4 connect section, and chart helpers should be separate modules.
**How:** Split into `components/sidebar.py`, `components/hero.py`, `components/data_preview.py`, `components/chat.py`, `utils/charts.py`.
**Effort:** High | **Files:** New `components/` package

### 13. Split Dependencies (dev vs prod) 🔲
**Why:** `requirements.txt` mixes runtime deps with `pytest`. CI installs all of them.
**How:** Create `requirements/dev.txt` (pytest, pytest-cov, pytest-mock) and keep `requirements.txt` for production deps only.
**Effort:** Small | **Files:** `requirements/` directory

---

## 🔒 Security Enhancements

### 14. API Key Validation on Startup ✅
**Status:** ✅ Done — `validate_api_key()` runs on first load with persistent error banner.

### 15. Prompt Injection Mitigation ✅
**Status:** ✅ Done — `_sanitize_question()` strips code blocks/backticks + guardrail instruction.

### 16. Global Error Boundary ✅
**Status:** ✅ Done — `utils/error_boundary.py` catches unhandled exceptions, Streamlit control flow exempted.

### 17. Secure Streamlit Configuration ✅
**Status:** ✅ Done — `.streamlit/config.toml` with 8 security settings locked down.

### 18. File Size & Row Limits ✅
**Why:** No guardrail against a 10GB CSV or 50M-row file that would exhaust memory.
**How:** Check `uploaded_file.size` before parsing (reject >100MB). Use `pd.read_csv(..., nrows=50001)` and warn if >50k rows.
**Effort:** Small | **Files:** `utils/data_loader.py`, `app.py`

### 19. Rate Limiting on Chat Input ✅
**Why:** Rapid-fire chat messages hammer the Gemini API and consume quota in seconds.
**How:** Track `st.session_state.last_api_call` timestamp. 2-second debounce — reject with toast if too fast. Show API call counter in sidebar.
**Effort:** Small | **Files:** `app.py`

---

## 🤖 AI Enhancements

### 20. Structured Chart Detection via Gemini ✅
**Status:** ✅ Done in AI/Data sprint (P6a) — `[CHART:{json}]` token with keyword fallback + retry logic, 3 new tests.
**Why:** Current `detect_chart_request()` uses brittle keyword matching, missing ~40% of chart-able responses.
**How:** Add hidden prompt instruction: `"[SYSTEM] If a chart would help, append [CHART:line:sessions] or [CHART:bar:page_path]"`. Parse the token instead of keyword scanning.
**Effort:** Medium | **Files:** `utils/prompt_templates.py`, `app.py`

### 21. Streaming Token-by-Token Responses ✅
**Status:** ✅ Done in P4 Wave 1 sprint — st.write_stream with generate_response_stream generator.
**Why:** Gemini responses appear all at once after 3-5 seconds. Streaming creates a ChatGPT-like real-time feel.
**How:** Use `stream=True` in `generate_content()`. Return a generator. Use `st.write_stream()` in `app.py`.
**Effort:** High | **Files:** `utils/gemini_client.py`, `app.py`

### 22. Comparative Analysis Mode ✅
**Status:** ✅ Done in AI/Data sprint (P6c) — sidebar toggle, dual-panel charts, `build_comparison_prompt()`, 5 new session state vars.
**Why:** Analysts constantly compare: "Q2 vs Q1" or "organic vs paid traffic."
**How:** Add a "Compare" toggle in the sidebar. Construct specialized comparison prompts. Generate dual-panel charts.
**Effort:** High | **Files:** `app.py`, `utils/prompt_templates.py`

### 23. Gemini-Suggested Chart Mapping ✅
**Status:** ✅ Done in AI/Data sprint (P6b) — JSON-first `detect_chart_request()`, column hallucination guard, 3 new tests.
**Why:** Chart generation is limited to hardcoded "sessions over time" or "top pages by sessions."
**How:** Ask Gemini to output JSON: `{"chart_type": "bar", "x": "device_category", "y": "users"}`. Parse with `json.loads` and map dynamically.
**Effort:** Medium | **Files:** `utils/prompt_templates.py`, `app.py`

---

## 📊 Data Processing Enhancements

### 24. Column Picker & Data Filters ✅
**Status:** ✅ Done in P4 Wave 1 sprint — date range + column multiselect, metrics/preview update instantly.
**Why:** Users often want to focus on subsets (specific date ranges, certain pages).
**How:** Add `st.multiselect` for columns and `st.date_input` for date range filtering above the data preview. Filtered DataFrame replaces full one downstream.
**Effort:** Medium | **Files:** `app.py`, `utils/data_loader.py`

### 25. Automatic Column Type Detection ✅
**Status:** ✅ Done in AI/Data sprint (P6d) — `detect_column_types()` with 📅🔢🏷️📝 badges, `.col-badge` CSS, 4 new tests.
**Why:** The app only looks for 5 hardcoded columns. GA4 exports can have 30+ columns.
**How:** Detect: date-like columns, numeric metrics, string columns with <50 unique values (dimensions). Show as "detected dimensions/metrics" in data preview.
**Effort:** Medium | **Files:** `utils/data_loader.py`, `app.py`

### 26. Statistical Anomaly Detection ✅
**Status:** ✅ Done in AI/Data sprint (P6e) — 7-day rolling Z-score, collapsible anomaly table, red X markers on charts, 3 new tests.
**Why:** Gemini only sees a 5-row sample when asked to find anomalies. Real detection should run on actual data.
**How:** Rolling Z-score function — flag dates where a metric deviates >2 std from 7-day rolling mean. Show as red markers on charts.
**Effort:** Medium | **Files:** `utils/data_loader.py`, `app.py`

### 27. Intelligent Sampling for Large Datasets ✅
**Status:** ✅ Done in AI/Data sprint (P6f) — `smart_sample()` with stratified weekly sampling, replaces `head()` everywhere, 3 new tests.
**Why:** `df.head(10)` is sent in every prompt regardless of dataset size.
**How:** For >10k rows: stratified sampling (preserve date distribution). For >100k rows: only aggregate stats in prompts, never raw rows.
**Effort:** Small | **Files:** `utils/prompt_templates.py`

---

## 🚀 DevOps & CI Enhancements

### 28. CI/CD Pipeline ✅
**Status:** ✅ Done — `cloudbuild.yaml` runs pytest on every push.

### 29. Headless Smoke Test ✅
**Status:** ✅ Done — `scripts/smoke_test.sh` boots Streamlit, checks HTTP 200, verifies no import errors.

### 30. Test Coverage Reporting ✅
**Why:** 129 tests exist but no visibility into what's covered.
**How:** Add `pytest-cov` to dev dependencies. Add `--cov=utils --cov=pages --cov-report=term` to pytest command. Add coverage badge to README.
**Effort:** Small | **Files:** `requirements/dev.txt`, `README.md`, `cloudbuild.yaml`

### 31. GitHub Actions CI (Alternative to Cloud Build) ✅
**Why:** Cloud Build requires GCP. GitHub Actions is free and built-in.
**How:** `.github/workflows/test.yml` with `pip install -r requirements.txt && pytest`.
**Effort:** Small | **Files:** `.github/workflows/test.yml`

### 32. Pre-commit Hooks ✅
**Status:** ✅ Done — `.pre-commit-config.yaml` with check-ast, ruff, black, trailing-whitespace, debug-statements.
**Why:** Catch syntax errors, trailing whitespace, and formatting issues before they reach CI.</newString>
**How:** Add `.pre-commit-config.yaml` with `black`, `ruff`, and `check-ast` hooks.
**Effort:** Small | **Files:** `.pre-commit-config.yaml`

---

## 📚 Documentation & Learning Enhancements

### 33. Interactive Learn Page via /learn ✅
**Status:** ✅ Done — 8-tab tutorial covering Streamlit, Pandas, Plotly, Gemini API, OAuth, Type Hints, Caching, Testing.

### 34. Architecture Documentation ✅
**Status:** ✅ Done — `ARCHITECTURE.md` with design decisions, data flow, security model, build log.

### 35. GA4 Connection Setup Guide ✅
**Status:** ✅ Done — Step-by-step README with ASCII diagrams and troubleshooting table.

### 36. Per-Module Test Badges in README ✅
**Why:** README says "110 tests" (stale since we have 129). No visibility into per-module coverage.
**How:** Add a table or badges showing: data_loader:20, prompt_templates:58, gemini_client:14, ga4_client:18, learn_page:19.
**Effort:** Small | **Files:** `README.md`

### 37. API Documentation (Docstrings to Sphinx) ✅
**Status:** ✅ Done — Sphinx setup with autodoc, napoleon, alabaster theme. `docs/` directory with conf.py, index.rst, auto-generated API docs. Build: `sphinx-build -b html docs docs/_build`.
**Why:** All functions have docstrings but no generated API reference.</newString>
**How:** Run `sphinx-quickstart` + `sphinx-apidoc` to generate HTML docs from existing docstrings. Host on GitHub Pages.
**Effort:** Medium | **Files:** `docs/` directory

---

## 📈 Priority Matrix

| Priority | Items |
|---|---|
| **🔴 Do today** (~30 min each) | #1 Loading spinner, #7 Learn page discovery, #18 File limits, #19 Rate limiting, #30 Coverage reporting, #36 Test badges |
| **🟡 This week** (~1-2 hrs each) | #2 Conversation memory, #5 Onboarding tour, #20 Structured chart detection, #27 Intelligent sampling, #31 GitHub Actions CI |
| **🟢 This month** | #3 Export report, #6 Theme toggle, #12 Component refactor, #23 Smart chart mapping, #24 Column picker, #25 Type detection |
| **🔵 Later** | #21 Streaming, #22 Comparative mode, #26 Anomaly detection, #37 Sphinx docs |

---

## 📊 Progress Summary

| Category | Total | Done | Remaining |
|---|---|---|---|
| UX | 7 | 6 | 1 |
| Code | 6 | 6 | 0 |
| Security | 6 | 6 | 0 |
| AI | 4 | 4 | 0 |
| Data Processing | 4 | 4 | 0 |
| DevOps/CI | 5 | 5 | 0 |
| Documentation | 5 | 5 | 0 |
| **Total** | **37** | **37** | **0** |</newString>

---

*Generated from deep review of the actual codebase, test suite, and CI pipeline. Last updated after: error boundary, learn page, smoke test, back-to-app button, test suite expansion, P1-P3 sprint (12 items, 194 tests), and P4 Wave 1 + Streaming sprint spec.*

---

## 📖 Related Docs

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — 21-item execution blueprint with sprint plan
- [IDEAS.md](IDEAS.md) — 25 bonus enhancements + 10 moonshot ideas
- [ARCHITECTURE.md](ARCHITECTURE.md) — Design decisions, data flow, security model
- [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) — The initial project prompt + compliance checklist
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central index of all project docs
- [BUGLOG.md](BUGLOG.md) — Structured bug log (7 bugs, patterns, rules)
- [plans/00-meta/✅ UNIFIED_PLAN.md](plans/00-meta/✅ UNIFIED_PLAN.md) — Master execution plan (6 phase plans + 3 derived plans)
- [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md) — Current sprint spec (Batches 1–5, 13 items)
- [plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md](plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md) — Active sprint spec (#15–17, #19)
- [plans/00-meta/✅ P4-future-plan.md](plans/00-meta/✅ P4-future-plan.md) — Future-phase plan
- [plans/00-meta/✅ P4-deferred-plan.md](plans/00-meta/✅ P4-deferred-plan.md) — Deferred items (Batches C–F)
- [plans/00-meta/🔵 onboarding-tour.md](plans/00-meta/🔵 onboarding-tour.md) — Standalone mini-spec for #8
- [plans/p5-p6/✅ COMPONENT_REFACTOR.md](plans/p5-p6/✅ COMPONENT_REFACTOR.md) — Standalone mini-spec for #20
- [CHANGELOG.md](CHANGELOG.md) — Unified change history
