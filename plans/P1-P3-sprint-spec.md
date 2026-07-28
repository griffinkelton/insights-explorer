# 📋 P1–P3 Sprint Spec — GA4 Insight Explorer

> **What:** Execution spec for the next sprint batch of enhancements.
> **Scope:** IMPLEMENTATION_PLAN.md items #1–14 (P1 Quick Wins + P2 UX Polish + P3 Code Quality), plus OAuth redirect configurability. #7 is already done. #8 is ⚠️ Optional — see [onboarding-tour.md](onboarding-tour.md). #6 is skipped.
> **Status:** 🔴 Spec complete — awaiting implementation.
> **Based on:** IMPLEMENTATION_PLAN.md, ENHANCEMENTS.md, user interview (3 rounds, July 28, 2026) + follow-up analysis. #8 tour implementation extracted to [onboarding-tour.md](onboarding-tour.md).
> **Test baseline:** 171 tests passing across 8 modules.

---

## 🧭 What This Sprint Covers

After auditing the current codebase against IMPLEMENTATION_PLAN.md P1–P3, here's what's done vs pending:

### ✅ Already Done (skip these)

| Item | What | Evidence |
|------|------|----------|
| **#7** | Loading spinner for summary button | `st.spinner` wrapping `_generate_summary()` in `app.py` line ~250 |
| **—** | Test count in README | Already says 171 tests (verified by `pytest tests/ -q`) |

### ❌ Still Pending (these are in the sprint)

_Batch 1 — Safety (prevent crashes, protect quotas):_

| # | What | Why first |
|---|---|---|
| **#4** | File size & row limits (+ download truncated slice) | Prevents OOM crashes from large uploads |
| **#5** | Rate limiting on chat | Protects Gemini API quota from rapid-fire usage |

_Batch 2 — Quick Wins (fast, no dependencies):_

| # | What | Why second |
|---|---|---|
| **#1** | Learn link in sidebar | Makes `/learn` discoverable |
| **NEW-A** | OAuth redirect configurability | Enables deployment beyond localhost |

_Batch 3 — Docs (reflect code state after code changes):_

| # | What | Why third |
|---|---|---|
| **#2** | Update learn page test count | Still says "92 unit tests" (actual: 171) |
| **#3** | Update docs (ARCHITECTURE, ENHANCEMENTS) | Stale build log and progress counts |
| **#9** | Learn link in README | Documents how to access `/learn` |

_Batch 4 — UX Polish (⚠️ #8 Optional):_

| # | What | Why fourth |
|---|---|---|
| **#8** ⚠️ | Onboarding tour | Guides first-time users in ~30 seconds — optional; defer to next spec if velocity is tight |

_Batch 5 — Infra (enables better future work):_

| # | What | Why last |
|---|---|---|
| **#10** | pytest-cov coverage reporting | Visibility into what's actually covered |
| **#11** | Split dev dependencies | Clean separation of runtime vs dev deps |
| **#12** | Per-module test badges in README | Shows where the 171 tests live |
| **#13** | app.py structural test | Closes last gap — every .py file gets structural tests |
| **#14** | GitHub Actions CI | Free second CI pipeline (no GCP required) |

### ⏭️ Skipped

| # | What | Reason |
|---|---|---|
| **#6** | .streamlit/pages.toml | User chose to skip — `st.page_link` (#1) provides navigation without version-compat concerns |

---

## 🏗️ Design Decisions (from Interview)

| Decision | Choice | Rationale |
|---|---|---|
| File limit behavior | **Truncate with warning + download button** | Most useful UX. "A GA4 user who exports 80k rows didn't do anything wrong — rejecting is punishing." |
| Rate limiting | **2-second debounce + API call counter** | Simple, effective, prevents quota exhaustion without hard caps |
| OAuth redirect | **Environment variable (`OAUTH_REDIRECT_URI`)** with fallback to `localhost:8501` | Matches existing `.env` pattern; no CLI args needed |
| Onboarding tour persistence | **Per-session only** | Resets on reload — matches "prototype" nature; no JS complexity |
| Priority order | **Highest impact first (5 batches)** | Safety (#4,#5) → Quick Wins (#1,NEW-A) → Docs (#2,#3,#9) → UX (#8 optional) → Infra (#10–14). "This avoids shipping a polished sidebar link before the app can handle a 500MB upload crash." |
| Test count to use | **171** | Verified via `pytest tests/ -q` — 171 passed |

---

## 📐 Detailed Implementation

---

### #4: File Size & Row Limits (+ Download Truncated Slice)

**Risk:** Low | **Effort:** ~45 min (expanded from original 30 min due to download button) | **Files:** `utils/data_loader.py`, `app.py`

> **Note:** The download-truncated-slice button (originally listed as NEW-B) is folded into this item as a sub-feature. "It's not scope creep — it's the natural completion of the truncation UX."

#### Changes

**`utils/data_loader.py`:**

1. Add constants:
   ```python
   MAX_FILE_SIZE_MB = 100
   MAX_ROWS = 50_000
   ```

2. Modify `load_file()` — read into bytes ONCE, check size before parsing:
   ```python
   from io import BytesIO

   def load_file(file: Any) -> tuple[pd.DataFrame | None, str | None, str | None]:
       """Load a CSV or XLSX file into a DataFrame.

       Returns (df, error_message, warning_message). If successful, error_message is None.
       Warning is set when data is truncated due to size limits.
       """
       filename = file.name.lower()

       # Read file into bytes ONCE — avoids buffer consumption issues
       file_bytes = file.read()
       file_size = len(file_bytes)

       # Size check
       if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
           return None, (
               f"File too large ({file_size / 1024 / 1024:.1f} MB). "
               f"Maximum is {MAX_FILE_SIZE_MB} MB."
           ), None

       try:
           if filename.endswith(".csv"):
               df = pd.read_csv(BytesIO(file_bytes))
           elif filename.endswith(".xlsx"):
               df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
           else:
               return None, f"Unsupported file type: {file.name}. Please upload a CSV or XLSX file.", None
       except Exception as e:
           return None, f"Failed to parse file: {str(e)}", None

       if df.empty:
           return None, "The uploaded file is empty.", None

       # Row count check
       warning = None
       if len(df) > MAX_ROWS:
           warning = (
               f"Dataset has {len(df):,} rows — showing first {MAX_ROWS:,} for performance. "
               "Consider exporting a narrower date range from GA4."
           )
           df = df.head(MAX_ROWS)

       return df, None, warning
   ```

3. **Breaking change:** Return type changes from `tuple[DataFrame | None, str | None]` to `tuple[DataFrame | None, str | None, str | None]`.

**`app.py`:**

4. Update the file processing block to unpack three values:
   ```python
   df, error, warning = load_file(uploaded_file)

   if error:
       st.error(f"❌ {error}")
       st.session_state.last_file_id = file_id
   else:
       if warning:
           st.warning(f"⚠️ {warning}")
           # BONUS: Download button for the truncated slice
           csv = df.to_csv(index=False).encode("utf-8")
           st.download_button(
               label=f"📥 Download truncated data ({len(df):,} rows)",
               data=csv,
               file_name=f"truncated_{uploaded_file.name}",
               mime="text/csv",
           )
       # ... rest of processing unchanged
   ```

#### Edge Cases
- **Empty CSV with large file size:** Size check happens before parsing — would reject (but empty CSVs are tiny in practice).
- **Truncation + date parsing:** The date range in `get_dataset_stats` may be narrower than full dataset. The warning covers this.
- **`BytesIO` import:** Add `from io import BytesIO` to `data_loader.py` imports.

#### Test Impact
Add to `tests/test_data_loader.py`:
- `test_rejects_oversized_file()` — mock 200MB file, assert error
- `test_truncates_large_dataset()` — 60k-row DataFrame, assert warning + 50k result
- `test_small_file_passes_size_check()` — normal flow still works
- Update all existing `load_file()` tests to unpack `(df, error, warning)` instead of `(df, error)`

**⚠️ Also check:** `test_static_analysis.py` references the old pattern `"file_bytes = file.read(); df = pd.read_csv(BytesIO(file_bytes))"` — update to match the new implementation.

---

### #5: Rate Limiting on Chat

**Risk:** Low | **Effort:** ~20 min | **Files:** `app.py`

#### Changes

1. Add session state init (near existing session state block):
   ```python
   if "last_api_call" not in st.session_state:
       st.session_state.last_api_call = 0.0
   if "api_call_count" not in st.session_state:
       st.session_state.api_call_count = 0
   ```

2. Add guard clause in chat input handler (before the API call):
   ```python
   if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
       import time

       # Rate limiting guard
       now = time.time()
       if now - st.session_state.last_api_call < 2.0:
           st.warning("⏳ Please wait a moment between questions...")
           st.stop()
       st.session_state.last_api_call = now
       st.session_state.api_call_count += 1

       # ... rest of chat handling
   ```

3. Add API call counter to sidebar (near the "Clear Data" button):
   ```python
   if st.session_state.api_call_count > 0:
       st.caption(f"🔢 API calls this session: {st.session_state.api_call_count}")
   ```

#### Edge Cases
- **First message:** `last_api_call` is 0.0 → `now - 0.0 > 2.0` always true. First message always passes.
- **Clock skew:** N/A — `time.time()` is monotonic enough for a 2-second check.
- **Session state persistence:** `last_api_call` survives reruns because it's in `st.session_state`.

#### Test Impact
Difficult to unit test time-based logic directly. Best tested via smoke test: send two rapid messages, verify second is rejected. The API call counter can be verified in `st.session_state` by the smoke test.

---

### #1: Learn Link in Sidebar

**Risk:** Near zero | **Effort:** ~5 min | **Files:** `app.py`

#### Change
In the sidebar block, after the "Built with ❤️" footer line and before the closing of `with st.sidebar:`, add:

```python
st.divider()
st.page_link(
    "pages/learn.py",
    label="📚 Learn Python",
    icon="📚",
    help="Interactive tutorials on Streamlit, Pandas, Plotly, Gemini, and more",
)
```

#### Edge Cases
None. `st.page_link` handles non-existent target pages gracefully and works regardless of hostname.

#### Test Impact
Covered by `test_app.py` structural test (#13) once written. No standalone test needed.

---

### #8: Onboarding Tour ⚠️ Optional — see [onboarding-tour.md](onboarding-tour.md)

**Risk:** Medium | **Effort:** ~60 min | **Files:** `app.py`

> **⚠️ Optional — full implementation extracted to [onboarding-tour.md](onboarding-tour.md).** Pick it up after P1–P3 batches 1–3 are stable. Summary: 3-step guided tour (upload → summary → chat), per-session state machine, auto-dismisses on data load. Touch points: `_render_hero()`, `_render_main()`, file processing block, GA4 pull handler.

---

### #9: Learn Link in README

**Risk:** Near zero | **Effort:** ~10 min | **Files:** `README.md`

#### Changes

1. **In the "📚 Learn Page" section**, add before the topic list:
   ```markdown
   ### How to access

   Start the app (`streamlit run app.py`), then either:
   - Click **📚 Learn Python** in the sidebar, or
   - Navigate to [http://localhost:8501/learn](http://localhost:8501/learn)

   > ⚠️ The app must be running locally for the link to work.
   ```

2. **In the "🚀 Quick Start" section**, add as a new step:
   ```markdown
   ### 6. Explore the learn page

   Open [http://localhost:8501/learn](http://localhost:8501/learn) (while the app is running)
   for interactive Python tutorials covering every library and pattern used in the app.
   ```

---

### #2: Update Learn Page Test Count

**Risk:** Near zero | **Effort:** ~10 min | **Files:** `pages/learn.py`, `tests/test_learn_page.py`

#### Changes

**`pages/learn.py`** (Testing tab, ~line 749):

1. Replace `"92 unit tests"` with `"171 unit tests"`
2. Update the test file tree to match current reality:
   ```
   tests/
   ├── test_data_loader.py
   ├── test_prompt_templates.py
   ├── test_gemini_client.py
   ├── test_ga4_client.py
   ├── test_learn_page.py
   ├── test_error_boundary.py      ← new
   ├── test_data_quality.py         ← new
   └── test_static_analysis.py      ← new
   ```

**`tests/test_learn_page.py`:**

3. In `test_test_count_in_testing_tab_is_current`, change `>= 92` to `>= 171`.

---

### #3: Update Docs (ENHANCEMENTS, ARCHITECTURE)

**Risk:** Medium | **Effort:** ~30 min | **Files:** `ENHANCEMENTS.md`, `ARCHITECTURE.md`

#### Changes

**`ENHANCEMENTS.md` — Progress Summary:**

Update the progress table. Current: "15/37 done". Items completed since last update:
- #4 Keyboard shortcuts
- #8 CSS extraction  
- #9 Type hints
- #10 Test suite
- #11 Streamlit caching
- #14 API key validation
- #15 Prompt injection
- #16 Error boundary
- #17 Secure config
- #28 CI/CD
- #29 Smoke test
- #33 Learn page
- #34 Architecture docs
- #35 GA4 setup guide

Plus the P2 data quality scorecard and app icon. Verify final count by cross-referencing the actual code.

Update the Progress Summary table at the bottom with accurate counts.

**`ARCHITECTURE.md` — Build Log:**

Add these entries to the build log table:

| # | Change | Type |
|---|---|---|
| 25 | Added `utils/error_boundary.py` — global error boundary (#16) | Feature |
| 26 | Added 19 structural tests for `pages/learn.py` | Testing |
| 27 | Added `scripts/smoke_test.sh` — headless smoke test | CI/CD |
| 28 | Added "← Back to App" button on `/learn` | Feature |
| 29 | Rewrote `ENHANCEMENTS.md` v2 — 37 enhancements across 7 categories | Docs |
| 30 | Added PWA icon set — SVG, 8 PNG sizes, favicon, OG image | Assets |
| 31 | Added data quality scorecard — A-F grading, styled card, prompt integration | Feature |
| 32 | Added `test_error_boundary.py` — 14 unit tests for `render_error_card()` | Testing |
| 33 | Added `test_data_quality.py` — 18 tests for grade calculation and edge cases | Testing |
| 34 | Added `test_static_analysis.py` — linting guards (Patterns 1 & 2) | Testing |

**`ARCHITECTURE.md` — Test Suite Table:**

Update to reflect current 8-module, 171-test suite. Add rows for `test_error_boundary.py`, `test_data_quality.py`, `test_static_analysis.py`.

---

### #10: pytest-cov Coverage Reporting

**Risk:** Near zero | **Effort:** ~10 min | **Files:** `requirements.txt` (or `requirements/dev.txt` if #11 done)

#### Changes

1. **Add dependency:**
   ```
   pytest-cov>=4.0
   ```

2. **Update README test command:**
   ```bash
   python -m pytest tests/ --cov=utils --cov=pages --cov-report=term -v
   ```

3. **Update `cloudbuild.yaml` test step:**
   ```yaml
   python -m pytest tests/ -v --tb=short --cov=utils --cov=pages --cov-report=term
   ```

#### Note
If #11 (dev deps split) is done first, put `pytest-cov` in `requirements/dev.txt` instead.

---

### #11: Split Dev Dependencies

**Risk:** Low | **Effort:** ~20 min | **Files:** New `requirements/` directory, `requirements.txt`, `cloudbuild.yaml`, `README.md`

#### Changes

1. **Create `requirements/base.txt`:**
   ```
   streamlit>=1.28.0
   google-genai>=1.0.0
   pandas>=2.0.0
   plotly>=5.17.0
   python-dotenv>=1.0.0
   openpyxl>=3.1.0
   google-analytics-data>=0.18.0
   google-auth-oauthlib>=1.0.0
   kaleido>=0.2.1
   ```

2. **Create `requirements/dev.txt`:**
   ```
   -r base.txt
   pytest>=8.0.0
   pytest-cov>=4.0.0
   pytest-mock>=3.12.0
   ```

3. **Update `cloudbuild.yaml` install step:**
   ```yaml
   pip install -r requirements/dev.txt --progress-bar off
   ```

4. **Update README install instructions:**
   - Development: `pip install -r requirements/dev.txt`
   - Production: `pip install -r requirements/base.txt`

5. **Keep root `requirements.txt`** as a copy of `base.txt` for backward compatibility. Add comment:
   ```
   # Runtime dependencies only. For development, use requirements/dev.txt.
   ```

#### Design Decision
Keep root `requirements.txt` — GitHub dependency scanners, `pip freeze` tools, and deployment platforms look for it by default.

---

### #12: Per-Module Test Badges in README

**Risk:** Near zero | **Effort:** ~15 min | **Files:** `README.md`

#### Changes

1. **Verify badge already says 171** (confirmed: `tests-171%20passed-success`).

2. **Add a test breakdown table** in the "🧪 Test Suite" section (or create it):

```markdown
### Test breakdown

| Module | Tests | Covers |
|---|---|---|
| `test_prompt_templates.py` | ~60 | `build_summary_prompt`, `build_chat_prompt`, `_sanitize_question`, `detect_chart_request` |
| `test_data_loader.py` | ~22 | `load_file`, `validate_columns`, `get_dataset_stats` |
| `test_ga4_client.py` | ~18 | `get_auth_url`, `exchange_code`, credentials serialization, `pull_ga4_report` |
| `test_data_quality.py` | ~18 | Grade calculation, edge cases, `assess_data_quality` |
| `test_learn_page.py` | ~19 | Syntax, structure, tab content, stale detection |
| `test_gemini_client.py` | ~14 | `generate_response`, `validate_api_key` |
| `test_error_boundary.py` | ~14 | `render_error_card` rendering scenarios |
| `test_static_analysis.py` | ~6 | Linting guards (Patterns 1 & 2) |
| **Total** | **171** | All util modules + pages + static analysis |
```

> Use `python -m pytest tests/ -v --tb=no --co -q` to get exact per-module counts at implementation time.

---

### #13: app.py Structural Test

**Risk:** Low | **Effort:** ~30 min | **Files:** New `tests/test_app.py`

#### Approach

Parse `app.py` with `ast` (same pattern as `test_learn_page.py`). Do NOT import `app.py` — Streamlit scripts have side effects at import time.

#### Test Classes

1. **TestAppSyntax** — file parses without syntax errors
2. **TestAppImports** — all 6 util modules imported + `pandas`, `streamlit`, `plotly.express`
3. **TestAppStructure** — has page config, sidebar, file uploader, `clear_data()`, chat input, error boundary wrapper, footer
4. **TestAppSessionState** — all expected keys initialized: `df`, `chat_history`, `api_key_valid`, `ga4_creds`, `data_source`, `summary`, etc.

Include an optional `test_has_learn_page_link` that verifies the `st.page_link("pages/learn.py"` call exists after #1 is implemented.

Expected: ~18 new tests.

#### Edge Cases
- **String search fragility:** `assert "st.chat_input" in source` passes even if it's in a comment. Good enough for structural smoke tests.
- **No Streamlit runtime:** AST parsing only — no widget creation or API calls.

---

### #14: GitHub Actions CI

**Risk:** Near zero | **Effort:** ~10 min | **Files:** New `.github/workflows/test.yml`, `README.md`

#### Change

**`.github/workflows/test.yml`:**
```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python -m pytest tests/ -v --tb=short
```

**`README.md`** — add badge alongside existing badges:
```markdown
<img src="https://github.com/griffinkelton/insights-explorer/actions/workflows/test.yml/badge.svg" alt="GitHub Actions">
```

#### Why Both CI Pipelines
Cloud Build (existing) requires GCP. GitHub Actions is free, built-in, and works for contributors who don't have GCP access.

---

### NEW-A: OAuth Redirect Configurability (Batch 2)

**Risk:** Low | **Effort:** ~15 min | **Files:** `app.py`, `.env.example`

#### Change

**`app.py`:**
```python
import os

REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501")
```

**`.env.example`** — add:
```
# Optional: customize OAuth redirect URI for non-localhost deployments
# OAUTH_REDIRECT_URI=http://localhost:8501
```

#### Edge Cases
- **No env var set:** Falls back to `localhost:8501` — backward compatible.
- **Deployed on Streamlit Cloud:** User sets `OAUTH_REDIRECT_URI=https://myapp.streamlit.app` in Streamlit secrets.
- **Trailing slash:** OAuth redirect URIs are exact-match. The env var is used as-is — user is responsible for matching their GCP Console setting exactly.

---

## 📊 Execution Plan

```
Batch 1 — Safety (~1 hr):
  #4  File size & row limits (+ download truncated slice)
  #5  Rate limiting on chat
  → Run tests: python -m pytest tests/ -q
  → Run smoke test: bash scripts/smoke_test.sh

Batch 2 — Quick Wins (~20 min):
  #1    Learn link in sidebar
  NEW-A OAuth redirect configurability
  → Run smoke test: bash scripts/smoke_test.sh

Batch 3 — Docs (~1 hr):
  #2  Update learn page test count
  #3  Update docs (ENHANCEMENTS, ARCHITECTURE)
  #9  Learn link in README
  → Run tests: python -m pytest tests/ -q

Batch 4 — UX (~1 hr, ⚠️ Optional):
  #8  Onboarding tour
  → Run smoke test: bash scripts/smoke_test.sh

Batch 5 — Infra (~2 hrs):
  #10  pytest-cov coverage
  #11  Split dev dependencies
  #12  Per-module test badges
  #13  app.py structural test (~18 tests)
  #14  GitHub Actions CI
  → Run tests: python -m pytest tests/ -q
  → Run smoke test: bash scripts/smoke_test.sh
```

**Total estimated time: ~5.5 hours** (or ~4.5 hours if #8 is deferred)

> **Why this order:** "This avoids the 'P1 quick wins first' trap where you ship a polished sidebar link before the app can handle a 500MB upload crash." Safety guards ship first, then fast wins, then docs (which should reflect code state after code changes), then UX polish, then infrastructure last (enables better future work).

---

## 🧪 Test Impact Summary

| Item | New Tests | Updated Tests |
|------|-----------|---------------|
| #4 File limits | +3 | ~6 existing `load_file()` tests updated |
| #5 Rate limiting | 0 (smoke test only) | 0 |
| #1 Learn sidebar link | 0 (covered by #13) | 0 |
| #8 Onboarding tour ⚠️ | 0 (smoke test only) | 0 |
| #9 Learn in README | 0 | 0 |
| #2 Learn page count | 0 | 1 assertion changed |
| #3 Doc updates | 0 | 0 |
| #10 pytest-cov | 0 | 0 |
| #11 Dev deps split | 0 | 0 |
| #12 Test badges | 0 | 0 |
| #13 app.py structural test | ~18 | 0 |
| #14 GitHub Actions | 0 | 0 |
| NEW-A OAuth redirect | 0 | 0 |
| **Total** | **~21** | **~7** |

**Post-implementation expected test count: ~192 tests.**

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| `load_file()` return type change breaks callers | Only caller is `app.py` — updated simultaneously |
| Tour state machine complexity > expected | Extract to `utils/onboarding.py` if > 60 lines |
| Doc count inconsistencies across files | Run `pytest tests/ -q` after all edits to verify actual count |
| CI test failure on GitHub Actions | Our tests mock all API calls — no `.env` needed in CI |
| `BytesIO` import not in `data_loader.py` | Explicitly listed in implementation notes |

---

## 📖 Related Docs

- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — Source plan with detailed per-item breakdowns
- [ENHANCEMENTS.md](../ENHANCEMENTS.md) — 37-item enhancement roadmap
- [UNIFIED_PLAN.md](UNIFIED_PLAN.md) — Master execution plan (P1-P6 phase plans)
- [ARCHITECTURE.md](../ARCHITECTURE.md) — Design decisions, data flow, security model
- [BUGLOG.md](../BUGLOG.md) — Structured bug log with patterns and rules
- [onboarding-tour.md](onboarding-tour.md) — Standalone mini-spec for #8 (deferred until post-P1-P3)
