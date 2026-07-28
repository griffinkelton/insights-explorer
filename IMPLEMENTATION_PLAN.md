# 📋 GA4 Insight Explorer — Implementation Plan

> Complete 21-item implementation blueprint with context, reasoning, risk assessments, and execution strategy.
>
> **Status:** 🔴 Awaiting review — no code has been written yet.
>
> **Numbering note:** This document uses its own item numbering (#1-21) for the 21 planned tasks. References to ENHANCEMENTS.md use the roadmap's numbering (e.g., "ENHANCEMENTS.md #13"). The two numbering schemes are independent.

---

## 🧭 Why This Plan Exists

After building the GA4 Insight Explorer from scratch — the app, 129 tests, GA4 live connection, `/learn` page, CI/CD, security hardening, and a 37-item enhancement roadmap — we reached a natural inflection point. The question became: *what's next, and in what order?*

This document answers that question. It takes the 21 highest-priority items from the [ENHANCEMENTS.md](ENHANCEMENTS.md) roadmap and provides a detailed, file-by-file implementation plan for each one. Every item includes:

- **Exact files** to touch
- **Exact changes** to make (with code-level precision)
- **Edge cases** to handle
- **Risk assessment** (Near Zero / Low / Medium / High)
- **Test impact** (what new tests, if any)
- **Dependencies** on other items

The plan is organized into five priority tiers, each with a specific rationale for *why* that tier comes before the next.

---

## 🏗️ Design Philosophy (Guidelines for All Items)

Before diving into individual items, here are the principles that guided every decision:

1. **Backward compatibility first.** No item should break existing functionality. Every change is additive or a drop-in replacement.
2. **Test before commit.** Every code change must pass `python -m pytest tests/ -q`. New features get new tests.
3. **Minimal diff, maximal impact.** Prefer surgical changes. One well-placed `st.page_link()` is better than 50 lines of custom navigation code.
4. **Fail closed.** Security and error handling always default to the safer option. File too large? Reject. API key invalid? Persistent banner.
5. **Streamlit-native.** Use Streamlit's built-in APIs (`st.page_link`, `st.spinner`, `st.cache_data`, `st.chat_message`) rather than custom workarounds. The app should feel like a Streamlit app, not a React app shoehorned into Python.

---

## 📊 Tier Rationale

| Tier | Name | Rationale |
|---|---|---|
| 🔴 **Priority 1** | Quick Wins | All under 30 min each. No dependencies between them. Can be done in any order. High visibility-to-effort ratio — the learn page link and accurate docs make the app feel "complete" immediately. |
| 🟡 **Priority 2** | UX Polish | Slightly more involved (30-60 min each). The loading spinner is the single highest-impact UX fix remaining. The onboarding tour removes the "cold start" problem. |
| 🟢 **Priority 3** | Code Quality & Docs | Infrastructure improvements. `pytest-cov`, dev dependencies, GitHub Actions — these make future development faster and more confident. The app.py structural test fills the last gap in test coverage. |
| 🔵 **Priority 4** | Medium Features | User-facing features that change behavior. Column picker and conversation memory are the two most-requested capabilities. Export chat gives users something to share. |
| ⚪ **Priority 5** | Larger Investments | Each 1-3 days of work. These are transformative (streaming, theming, component refactor) but don't block anything above them. Do them when you have a free afternoon. |

---

## 🔴 Priority 1 — Quick Wins (6 items)

Estimated total time: **~2 hours** (all 6 can be done in parallel by different people)

---

### #1: Add "Learn" link to sidebar

**Files:** `app.py`

**Change:** In the sidebar block (around line 105, after the "Built with ❤️" footer line and before the closing of `with st.sidebar:`), add:

```python
st.divider()
st.page_link("pages/learn.py", label="📚 Learn Python", icon="📚",
             help="Interactive tutorials on Streamlit, Pandas, Plotly, Gemini, and more")
```

**Why this approach:** `st.page_link` is Streamlit's native cross-page navigation API (added in 1.31). It renders a clickable button that navigates to another page within the same multi-page app. Unlike a raw HTML link, it:
- Works regardless of hostname (no hardcoded `localhost:8501`)
- Respects Streamlit's base URL if deployed
- Renders consistently with Streamlit's component styling

**Edge cases:** None. `st.page_link` handles the case where the target page doesn't exist (shows an error) and works even when the app isn't deployed locally.

**Risk:** Near zero. One function call in an existing block.

**Test impact:** `test_learn_page.py` doesn't test `app.py`, so no test changes needed. The structural test (#13) would verify this link exists after that test is written.

**Dependencies:** None.

---

### #2: Update learn page test count (92 → 129)

**Files:** `pages/learn.py`

**Change:** In the Testing tab (`tab8`), around line ~620:

1. Replace `"92 unit tests"` with `"129 unit tests"`
2. Update the test file tree shown in the tab to include:
   ```
   tests/
   ├── test_data_loader.py
   ├── test_prompt_templates.py
   ├── test_gemini_client.py
   ├── test_ga4_client.py       ← new
   └── test_learn_page.py       ← new
   ```

**Why now:** The learn page is a teaching tool. An outdated test count undermines its credibility as a living, accurate codebase walkthrough.

**Edge cases:** The stale content test in `test_learn_page.py` uses a `>= 92` floor check — 129 passes that check, so no test failure. However, it's cleaner to bump the floor to `>= 129` so it catches regressions.

**Also update:** `tests/test_learn_page.py` → `test_test_count_in_testing_tab_is_current` — change `>= 92` to `>= 129`.

**Risk:** Near zero. Two string replacements, one number bump.

**Test impact:** One assertion change in `test_learn_page.py`.

**Dependencies:** None, but #3 (doc updates) should come after this for accurate counts.

---

### #3: Update docs (ENHANCEMENTS.md, ARCHITECTURE.md, README.md)

**Files:** `ENHANCEMENTS.md`, `ARCHITECTURE.md`, `README.md`

**Why:** Three doc files are stale. The v2 rewrite of `ENHANCEMENTS.md` mostly caught up, but the build log in `ARCHITECTURE.md` and the test count badge in `README.md` haven't been updated in several commits.

**Changes:**

#### ENHANCEMENTS.md
- Verify the progress summary table says "15 / 37 done" (it's accurate after the v2 rewrite)
- Verify #13 error boundary and #16 global error boundary are both marked ✅ (they should be — the v2 rewrite caught both)
- If any item was completed but not marked, mark it

#### ARCHITECTURE.md — Build Log
Add these entries after #19:

| # | Change | Type |
|---|---|---|
| 20 | Added `utils/error_boundary.py` — global error boundary (#13) | Feature |
| 21 | Added 19 structural tests for `pages/learn.py` | Testing |
| 22 | Added `scripts/smoke_test.sh` — headless smoke test | CI/CD |
| 23 | Added "← Back to App" button (`st.page_link`) on `/learn` | Feature |
| 24 | Rewrote `ENHANCEMENTS.md` v2 — 37 enhancements across 7 categories | Docs |

#### ARCHITECTURE.md — Test Suite Table
Update from:
```
| Total | 110 | All util modules covered |
```
To:
```
| test_learn_page.py | 19 | Syntax, structure, tab content, stale detection |
| Total | 129 | All util modules + learn page covered |
```

#### README.md
- Badge: `110 passed` → `129 passed`
- Test count mention: "110 tests covering..." → "129 tests covering..."
- Project structure: add `test_learn_page.py` to the `tests/` directory listing

**Risk:** Medium. Three files, multiple changes each. Easy to miss a number or have an inconsistency between files. The fix is to run `python -m pytest tests/ -q` after all edits to confirm the actual test count matches what the docs say.

**Test impact:** None (docs only).

**Dependencies:** Should be done after #2 (learn page test count update) to avoid propagating stale numbers.

---

### #4: File size/row limits (#13 from roadmap)

**Files:** `utils/data_loader.py`, `app.py`

**Why now:** Currently, a 10 GB CSV or 50-million-row file will crash the app with a memory error. This is a defensive guardrail — it prevents the most catastrophic failure mode before it happens.

**Changes:**

#### `utils/data_loader.py`
Add constants at the top:
```python
MAX_FILE_SIZE_MB = 100
MAX_ROWS = 50_000
```

In `load_file()`, read the file into bytes once (avoids consuming the buffer before pandas reads it), then check size:
```python
from io import BytesIO

# Read file into bytes ONCE — avoids buffer consumption issues with pd.read_csv/read_excel
file_bytes = file.read()
file_size = len(file_bytes)
if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
    return None, f"File too large ({file_size / 1024 / 1024:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB."

# Parse from bytes, not from file object
if filename.endswith(".csv"):
    df = pd.read_csv(BytesIO(file_bytes))
elif filename.endswith(".xlsx"):
    df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
```

After successful parse, check row count:
```python
if len(df) > MAX_ROWS:
    warning = (
        f"Dataset has {len(df):,} rows — showing first {MAX_ROWS:,} for performance. "
        "Consider exporting a smaller date range from GA4."
    )
    df = df.head(MAX_ROWS)
    return df, None, warning  # New: third return value for warnings
```

**Design decision — truncate vs reject:** If someone has 200k rows, showing them 50k with a warning is more useful than showing nothing. The warning makes the truncation transparent. Rejection would be the "failsafe" choice (safest for memory) but the worst UX.

**Return type change:** Currently `tuple[DataFrame | None, str | None]`. This becomes `tuple[DataFrame | None, str | None, str | None]` — adding an optional warning string. This is a breaking change to the function signature, but all callers in `app.py` use unpacking:

```python
# Before
df, error = load_file(uploaded_file)

# After
df, error, warning = load_file(uploaded_file)
```

#### `app.py`
In the file processing block, handle the warning:
```python
df, error, warning = load_file(uploaded_file)

if error:
    st.error(f"❌ {error}")
else:
    if warning:
        st.warning(f"⚠️ {warning}")
    # ... rest of processing
```

**Edge cases:**
- **Truncation + date parsing:** If rows are truncated, the date range in `get_dataset_stats` may be narrower than the full dataset. The warning already covers this.
- **Empty CSV with large file size:** The size check happens before parsing — it would reject. In practice, empty CSVs are small.
- **`BytesIO` import:** Add `from io import BytesIO` to `data_loader.py` imports.

**Risk:** Low. Added before existing logic, fails closed. The return type change is a minor refactor but all callers are in the same codebase and updated simultaneously.

**Test impact:** Add to `test_data_loader.py`:
- `test_rejects_oversized_file()` — mock a 200 MB file, assert error message
- `test_truncates_large_dataset()` — create a 60k-row DataFrame, assert warning and truncation
- `test_small_file_passes_size_check()` — normal flow still works
- **⚠️ Also update all 6 existing `load_file()` tests** — they unpack two values (`df, error`), must now unpack three (`df, error, warning`). The return type change from `tuple[DataFrame | None, str | None]` to `tuple[DataFrame | None, str | None, str | None]` is a breaking change to every existing test.

**Dependencies:** None.

---

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify the app boots with file size limits active.

### #5: Rate limiting on chat (#14 from roadmap)

**Files:** `app.py`

**Why now:** Rapid-fire chat messages hammer the Gemini API and can burn through a free API quota in seconds. A 2-second debounce costs nothing to implement and prevents the most common quota-exhaustion scenario.

**Changes:**

#### Session state initialization (around line 41)
Add:
```python
if "last_api_call" not in st.session_state:
    st.session_state.last_api_call = 0.0
if "api_call_count" not in st.session_state:
    st.session_state.api_call_count = 0
```

#### Chat input handler (`_render_main()`, in the `if prompt := st.chat_input(...)` block)
Add a guard clause before the API call:
```python
import time

if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
    # Rate limiting guard
    now = time.time()
    if now - st.session_state.last_api_call < 2.0:
        st.warning("⏳ Please wait a moment between questions...")
        st.stop()
    st.session_state.last_api_call = now
    st.session_state.api_call_count += 1

    # ... rest of chat handling (append to history, spinner, API call)
```

#### Sidebar (near the "Clear Data" button or privacy notice)
Add a subtle usage counter:
```python
if st.session_state.api_call_count > 0:
    st.caption(f"🔢 API calls this session: {st.session_state.api_call_count}")
```

**Why `st.warning` instead of `st.toast`:** `st.toast` was added in Streamlit 1.35 (September 2024). Our `requirements.txt` says `>=1.28`. Using `st.warning` is universally compatible. If we bump to `streamlit>=1.44` (see #6), we could switch to `st.toast` for a less intrusive notification.

**Edge cases:**
- **Very first message:** `last_api_call` is 0.0, so `now - 0.0 > 2.0` is always true. First message always passes.
- **Session state reset on rerun:** `last_api_call` persists because it's in `st.session_state`. The `st.stop()` prevents the API call but the warning appears on the next rerun.
- **Clock skew:** N/A — `time.time()` is monotonic enough for a 2-second check.

**Risk:** Low. A guard clause before the API call. The worst case is a false-positive rate limit (user waits 2.1 seconds but it feels like 2). The counter is informational, not a hard limit.

**Test impact:** Difficult to unit test time-based logic directly. Best tested via the smoke test (send two rapid messages, verify the second is rejected). The API call counter can be verified by inspecting `st.session_state.api_call_count` in the smoke test log.

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify the app boots with rate limiting active.

**Dependencies:** None.

---

### #6: Add `.streamlit/pages.toml`

**Files:** New `.streamlit/pages.toml`

**Change:** Create the file with:
```toml
[[pages]]
path = "pages/learn.py"
name = "📚 Learn Python"
icon = "📚"
```

**Why:** Streamlit auto-generates sidebar navigation from the `pages/` directory, using the filename ("learn") as the display name. This is functional but unpolished. `pages.toml` lets us customize the display name and icon without changing the filename.

**Version compatibility:** `pages.toml` was added in Streamlit 1.44. Our `requirements.txt` says `>=1.28`. **Keep `>=1.28`** — do NOT bump. On Streamlit < 1.44, `pages.toml` is silently ignored and the sidebar shows "learn" instead of "📚 Learn Python" — a harmless fallback that doesn't break anyone's install. On >=1.44, it shows the polished name.

**Edge cases:**
- **Incorrect path:** If `pages/learn.py` doesn't exist, Streamlit shows an error. Not a concern since the file exists and is tested.
- **Multiple pages:** If we add more pages later, each gets its own `[[pages]]` block.
- **File not found:** If `pages.toml` is missing, Streamlit falls back to filename-based naming. No crash.

**Risk:** Low. The file is optional — if it fails to parse or the Streamlit version is <1.44, it's silently ignored. No version bump needed.

**Test impact:** None. `test_learn_page.py` doesn't test the sidebar navigation. The `st.page_link` in #1 still references `"pages/learn.py"` regardless of the display name.

**Dependencies:** None directly, but pairs nicely with #1 (sidebar link).

---

## 🟡 Priority 2 — UX Polish (3 items)

Estimated total time: **~2.5 hours**

---

### #7: Loading state for summary button

**Files:** `app.py`

**Why now:** This is the single highest-impact UX fix remaining. Currently, the "✨ Generate Summary" button uses `on_click` callback mode — the UI freezes for 3-5 seconds during the Gemini API call with zero feedback. Users think the app crashed. A `st.spinner` wrapper tells them *something is happening*.

**Current code (the problem):**

```python
st.button(
    "✨ Generate Summary",
    type="primary",
    use_container_width=True,
    key="gen_summary_btn",
    on_click=lambda: _generate_summary(df, stats),
)
```

The `on_click` callback runs `_generate_summary()` synchronously inside Streamlit's event loop, blocking all UI updates until the API call returns. No spinner, no progress, just a frozen page.

**New code (the fix):**

```python
if st.button("✨ Generate Summary", type="primary", use_container_width=True, key="gen_summary_btn"):
    with st.spinner("🤖 Analyzing your dataset with Gemini..."):
        _generate_summary(df, stats)
    st.rerun()
```

**Why this works:** The `st.spinner` context manager wraps the API call. Streamlit renders the spinner *before* executing the block, then clears it *after* the block completes. The `st.rerun()` forces a refresh so the summary (now in `st.session_state.summary`) appears immediately rather than on the next user interaction.

**The `_generate_summary()` callback stays the same:**

```python
def _generate_summary(df: pd.DataFrame, stats: dict[str, Any]) -> None:
    try:
        summary_prompt = build_summary_prompt(df, stats)
        st.session_state.summary = generate_response(summary_prompt)
    except ValueError as e:
        st.error(f"🔑 Configuration error: {e}")
    except RuntimeError as e:
        st.error(f"⚠️ API error: {e}")
```

**Edge cases:**
- **Error during API call:** `st.error()` inside `st.spinner` still works — the error appears after the spinner closes. The error persists across reruns (same behavior as before).
- **Double-click:** If the user clicks twice rapidly, the second click starts a new spinner. Streamlit's widget state management prevents duplicate execution by default.

**Risk:** Low. Just wrapping existing logic. The `on_click` callback approach was the original bug — this is the standard Streamlit pattern for async operations.

**Test impact:** No unit test needed (it's a Streamlit widget behavior, not logic). Smoke test: verify the spinner text appears in the page source when the button is clicked.

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify the app boots and the Generate Summary button still works.

**Dependencies:** None.

---

### #8: Onboarding tour (#5 from roadmap)

**Files:** `app.py` (or new `utils/onboarding.py` if the state machine is complex enough)

**Why now:** The empty state (hero page) is beautiful but passive. A first-time user sees "Upload a file in the sidebar" and might not know to also try the AI summary or chat. A 3-step guided tour reduces time-to-value from "figure it out" to ~30 seconds.

**Changes:**

#### Session state (around line 41)
```python
if "tour_step" not in st.session_state:
    st.session_state.tour_step = 0  # 0 = not started, 1-3 = steps, 4 = done
```

#### Hero area (`_render_hero()`)
Add a tour start button when no data is loaded:
```python
if st.session_state.tour_step == 0:
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("🎓 Quick Tour", type="secondary", use_container_width=True):
            st.session_state.tour_step = 1
            st.rerun()
```

#### Tour steps (render before hero content when `tour_step` is 1-3)

Create a tour card that overlays the main content area:

```python
def _render_tour_step(step: int) -> None:
    """Render the current onboarding tour step."""
    steps = [
        {
            "icon": "📂",
            "title": "Upload your data",
            "body": "👈 Upload a CSV or XLSX file in the sidebar, "
                    "or connect live via Google sign-in.",
        },
        {
            "icon": "✨",
            "title": "Generate an AI summary",
            "body": "Click **Generate Summary** to get an instant overview "
                    "of your dataset — date range, top pages, anomalies.",
        },
        {
            "icon": "💬",
            "title": "Ask questions",
            "body": "Type natural language questions in the chat box. "
                    "Try: *\"Which pages have the highest drop-off?\"*",
        },
    ]
    s = steps[step - 1]

    with st.container(border=True):
        col_icon, col_content = st.columns([0.15, 0.85])
        with col_icon:
            st.markdown(f"<div style='font-size:3rem;'>{s['icon']}</div>", unsafe_allow_html=True)
        with col_content:
            st.markdown(f"### Step {step}/3: {s['title']}")
            st.markdown(s["body"])
            st.progress(step / 3)

        col_back, col_skip, col_next = st.columns([1, 1, 1])
        with col_back:
            if step > 1:
                if st.button("← Back", key=f"tour_back_{step}"):
                    st.session_state.tour_step = step - 1
                    st.rerun()
        with col_skip:
            if st.button("Skip Tour", key=f"tour_skip_{step}"):
                st.session_state.tour_step = 4
                st.rerun()
        with col_next:
            label = "Finish ✅" if step == 3 else "Next →"
            if st.button(label, key=f"tour_next_{step}", type="primary"):
                st.session_state.tour_step = step + 1 if step < 3 else 4
                st.rerun()
```

#### Tour auto-dismiss
If the user uploads data while the tour is active, auto-complete the tour:
```python
# In the file processing block
if uploaded_file is not None and st.session_state.tour_step in (1, 2, 3):
    st.session_state.tour_step = 4
```

**Edge cases:**
- **User uploads data mid-tour:** Tour auto-dismisses (see above). The data takes priority.
- **User reloads the page:** Session state resets, tour restarts. This is correct behavior — the tour is per-session.
- **Tour + GA4 connect:** If the user connects GA4 during the tour, the tour auto-dismisses (same as file upload).
- **Tour on mobile:** The tour card uses full-width containers, which work on narrow viewports.

**Risk:** Medium. Adds non-trivial UI state management. The tour is rendered in the main content area, which means it needs to coexist with the hero/empty state. The auto-dismiss logic must be careful not to interfere with normal data loading.

**Could be extracted:** If the tour logic exceeds ~60 lines, extract to `utils/onboarding.py` with a `render_tour(step: int) -> None` function.

**Test impact:** Smoke test (verify tour renders, advance through steps, dismiss on upload). If extracted to a utility, add 3-4 unit tests for the state machine.

**Dependencies:** Touches `_render_hero()` and the file processing block — same areas as #1 and #7. Should be done after those are stable.

---

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify the app boots and the tour renders correctly.

### #9: Add "Learn" link to README

**Files:** `README.md`

**Why now:** The README mentions `/learn` in the project structure but never tells users how to access it. Two sentences fix this.

**Changes:**

#### In the "📚 Learn Page" section
Add before the topic list:

```markdown
### How to access

Start the app (`streamlit run app.py`), then either:
- Click **📚 Learn Python** in the sidebar, or
- Navigate to [http://localhost:8501/learn](http://localhost:8501/learn)

> ⚠️ The app must be running locally for the link to work.
```

#### In the "🚀 Quick Start" section
Add as step 6:

```markdown
### 6. Explore the learn page

Open [http://localhost:8501/learn](http://localhost:8501/learn) (while the app is running)
for interactive Python tutorials covering every library and pattern used in the app.
```

**Risk:** Near zero. Documentation only.

**Dependencies:** Done after #1 (sidebar link) so the README instructions match reality.

---

## 🟢 Priority 3 — Code Quality & Docs (5 items)

Estimated total time: **~2 hours**

---

### #10: Add pytest-cov coverage reporting

**Files:** `requirements.txt` (or `requirements/dev.txt` if #11 is done first), `README.md`, `cloudbuild.yaml`

**Why now:** 129 tests exist but we have no visibility into what's actually covered. `pytest-cov` adds `--cov` flags that show per-module coverage percentages. This takes 5 minutes to install and configure and gives immediate insight into coverage gaps.

**Changes:**

#### Dependency
```
pytest-cov>=4.0
```

#### README.md — test command update
```bash
# From:
python -m pytest tests/

# To:
python -m pytest tests/ --cov=utils --cov=pages --cov-report=term -v
```

#### cloudbuild.yaml — test step update
```yaml
echo "=== Running tests with coverage ==="
python -m pytest tests/ -v --tb=short --cov=utils --cov=pages --cov-report=term
```

**Edge cases:**
- **`--cov=pages` flag:** The pages directory has a single file (`learn.py`). If `--cov=pages` doesn't find it, use `--cov=pages/learn.py` explicitly.
- **Coverage of `app.py`:** We don't include `--cov=app` because `app.py` can't be imported without Streamlit's runtime. The structural test (#13) verifies app.py's AST.

**Risk:** Near zero. Adding a dev-only dependency and CLI flags.

**Dependencies:** Can be done independently, but pairs naturally with #11 (dev dependencies split).

---

### #11: Split dev dependencies

**Files:** New `requirements/` directory, `cloudbuild.yaml`, `README.md`

**Why now:** `requirements.txt` mixes runtime deps (streamlit, pandas) with dev deps (pytest). In production (e.g., Cloud Run deployment), you don't need pytest. Splitting them is a 10-minute cleanup that prevents unnecessary packages in deployment.

**Changes:**

#### Directory structure
```
requirements/
├── base.txt        # Runtime deps only
└── dev.txt         # Dev deps (includes base.txt)
```

#### `requirements/base.txt`
```
streamlit>=1.28.0
google-genai>=1.0.0
pandas>=2.0.0
plotly>=5.17.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
google-analytics-data>=0.18.0
google-auth-oauthlib>=1.0.0
```

#### `requirements/dev.txt`
```
-r base.txt
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.12.0
```

#### `cloudbuild.yaml` — update install step
```yaml
pip install -r requirements/dev.txt --progress-bar off
```

#### README.md — update install instructions
```bash
# For development (includes tests):
pip install -r requirements/dev.txt

# For production (runtime only):
pip install -r requirements/base.txt
```

#### Root `requirements.txt`
Keep as a copy of `base.txt` for backward compatibility. Users who cloned earlier won't have their `pip install -r requirements.txt` break. Add a comment at the top:
```
# Runtime dependencies only. For development, use requirements/dev.txt.
```

**Why keep `requirements.txt` at root:** GitHub dependency scanners, `pip freeze` tools, and some deployment platforms look for `requirements.txt` in the project root by default. Removing it would break those integrations.

**Edge cases:**
- **Existing users:** `pip install -r requirements.txt` still works (it's a copy of base.txt).
- **New contributors:** The README guides them to `requirements/dev.txt`.

**Risk:** Low. Additive change. The root `requirements.txt` stays for backward compatibility.

**Dependencies:** #10 (pytest-cov) can go into this split — add `pytest-cov` to `dev.txt` instead of root `requirements.txt`.

---

### #12: Per-module test badges in README

**Files:** `README.md`

**Why now:** The README says "110 tests" (stale — we have 129) in a single badge. A per-module table gives contributors a clear picture of where the test coverage lives.

**Changes:**

Replace the single badge:
```markdown
<img src="https://img.shields.io/badge/tests-110%20passed-success?logo=pytest" alt="110 tests">
```

With:
```markdown
<img src="https://img.shields.io/badge/tests-129%20passed-success?logo=pytest" alt="129 tests">
```

Add a test breakdown table in the "🧪 Test Suite" section (or create one if it doesn't exist):

```markdown
### Test breakdown

| Module | Tests | Covers |
|---|---|---|
| `test_data_loader.py` | 20 | `load_file`, `validate_columns`, `get_dataset_stats` |
| `test_prompt_templates.py` | 58 | `build_summary_prompt`, `build_chat_prompt`, `_sanitize_question`, `detect_chart_request` |
| `test_gemini_client.py` | 14 | `generate_response`, `validate_api_key` |
| `test_ga4_client.py` | 18 | `get_auth_url`, `exchange_code`, credentials serialization, `pull_ga4_report` |
| `test_learn_page.py` | 19 | Syntax, structure, tab content, stale detection |
| **Total** | **129** | All 5 util modules + learn page |
```

**Risk:** Near zero. Documentation only. Must keep counts in sync — the `test_test_count_in_testing_tab_is_current` test in `test_learn_page.py` catches regressions on the learn page count, and `python -m pytest tests/ -q` gives the actual count for verification.

**Dependencies:** Done after #3 (doc updates) so counts are consistent everywhere.

---

### #13: Add app.py structural test

**Files:** New `tests/test_app.py`

**Why now:** Every Python file in the project has structural tests except `app.py` — the most important file. A structural test verifies the file parses, imports the right modules, has all expected sections, and correctly wraps the main content in the error boundary. It doesn't run the app (Streamlit apps can't be imported like normal modules).

**Approach:** Parse `app.py` with `ast` (like `test_learn_page.py` does), then verify:

```python
"""Structural tests for app.py — AST parsing only, no Streamlit runtime."""

import ast
import re
import pytest

APP = "app.py"

def _read_source() -> str:
    with open(APP) as f:
        return f.read()

def _parse_ast() -> ast.Module:
    return ast.parse(_read_source(), filename=APP)


class TestAppSyntax:
    """Verify the file parses without syntax errors."""

    def test_parses_without_syntax_error(self):
        tree = _parse_ast()
        assert isinstance(tree, ast.Module)


class TestAppImports:
    """Verify all expected utility modules are imported."""

    def test_imports_data_loader(self):
        source = _read_source()
        assert "from utils.data_loader import" in source

    def test_imports_gemini_client(self):
        source = _read_source()
        assert "from utils.gemini_client import" in source

    def test_imports_prompt_templates(self):
        source = _read_source()
        assert "from utils.prompt_templates import" in source

    def test_imports_ga4_client(self):
        source = _read_source()
        assert "from utils.ga4_client import" in source

    def test_imports_styles(self):
        source = _read_source()
        assert "from utils.styles import" in source

    def test_imports_error_boundary(self):
        source = _read_source()
        assert "from utils.error_boundary import" in source


class TestAppStructure:
    """Verify key sections and patterns exist."""

    def test_has_page_config(self):
        source = _read_source()
        assert "st.set_page_config" in source
        assert "GA4 Insight Explorer" in source

    def test_has_sidebar(self):
        source = _read_source()
        assert "with st.sidebar:" in source

    def test_has_file_uploader(self):
        source = _read_source()
        assert "st.file_uploader" in source

    def test_has_clear_data_function(self):
        source = _read_source()
        assert "def clear_data()" in source

    def test_has_chat_input(self):
        source = _read_source()
        assert "st.chat_input" in source

    def test_has_error_boundary_wrapper(self):
        """The main content must be wrapped in try/except with render_error_card."""
        source = _read_source()
        assert "try:" in source
        assert "_render_main()" in source
        assert "render_error_card" in source

    def test_has_footer(self):
        source = _read_source()
        assert "GA4 Insight Explorer" in source
        assert "Data processed in-memory only" in source

    @pytest.mark.skip(reason="Requires #1 (sidebar learn link) to be implemented first")
    def test_has_learn_page_link(self):
        """If #1 is implemented, the learn page link should exist."""
        source = _read_source()
        assert 'st.page_link("pages/learn.py"' in source or \
               "st.page_link('pages/learn.py'" in source


class TestAppSessionState:
    """Verify all expected session state keys are initialized."""

    def test_df_initialized(self):
        source = _read_source()
        assert '"df"' in source

    def test_chat_history_initialized(self):
        source = _read_source()
        assert '"chat_history"' in source

    def test_api_key_valid_initialized(self):
        source = _read_source()
        assert '"api_key_valid"' in source

    def test_ga4_credentials_initialized(self):
        source = _read_source()
        assert '"ga4_creds"' in source

    def test_data_source_initialized(self):
        source = _read_source()
        assert '"data_source"' in source
```

**Edge cases:**
- **Do NOT `import app`:** Streamlit scripts have side effects at import time (widget creation, page config). Importing them in a test context will fail or corrupt the test runner's state. AST parsing is the safe approach.
- **String search fragility:** `assert "st.chat_input" in source` is fragile — it would pass even if `st.chat_input` is in a comment. But it's good enough for a structural smoke test.

**Risk:** Low. No runtime testing, just AST and string checks. The tests will catch: syntax errors, missing imports after a refactor, accidentally removed sections.

**Test count:** ~18 new tests.

**Dependencies:** If #1 (learn page link) is done, the `test_has_learn_page_link` test verifies it. If #1 isn't done yet, that test can be skipped or marked as expected failure.

---

### #14: Add GitHub Actions CI

**Files:** New `.github/workflows/test.yml`

**Why now:** Cloud Build (`cloudbuild.yaml`) requires a GCP project. GitHub Actions is free, built into the repo, and requires zero setup. It's a 5-minute addition that gives a second CI pipeline (and works for contributors who don't have GCP access).

**Change:**

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

#### README.md — add CI badges
```markdown
<img src="https://github.com/griffinkelton/insights-explorer/actions/workflows/test.yml/badge.svg" alt="GitHub Actions">
<img src="https://img.shields.io/badge/CI-Cloud%20Build-blue?logo=googlecloud" alt="Cloud Build">
```

**Why both Cloud Build and GitHub Actions:** Cloud Build is already configured and working. GitHub Actions is a free, zero-setup alternative. Both can coexist — they run on different triggers. Contributors who fork the repo on GitHub get Actions for free without configuring GCP.

**Edge cases:**
- **No `.env` file in CI:** Our tests mock all API calls (`unittest.mock.patch`). The `dotenv.load_dotenv()` call in `gemini_client.py` silently fails in CI (no `.env` file exists), which is fine because tests mock `_get_client()` before any real API call.
- **Branch protection:** Once the Actions workflow exists, enable branch protection on `main` to require passing tests before merge.

**Risk:** Near zero. Standard GitHub Actions boilerplate. The workflow file is inert until pushed to GitHub.

**Dependencies:** None.

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify the app boots and chat input still works.

---

## 🔵 Priority 4 — Medium Features (3 items)

Estimated total time: **~5 hours**

---

### #15: Column picker & date filters (#3 from roadmap)

**Files:** `app.py`, `utils/data_loader.py`

**Why now:** Users often want to focus on subsets of data — specific date ranges, certain columns. Currently, the entire DataFrame is sent to Gemini and used for charts. A filter layer lets users narrow their analysis without re-uploading.

**Changes:**

#### `utils/data_loader.py` — new helper
```python
def filter_dataframe(
    df: pd.DataFrame,
    date_col: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    selected_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Apply date range and column filters to a DataFrame.

    Returns a filtered copy — never mutates the original.
    If no filters are provided, returns the original DataFrame.
    """
    filtered = df.copy()

    if date_col and date_col in filtered.columns:
        filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
        if start_date:
            filtered = filtered[filtered[date_col] >= pd.Timestamp(start_date)]
        if end_date:
            filtered = filtered[filtered[date_col] <= pd.Timestamp(end_date)]

    if selected_columns:
        valid_cols = [c for c in selected_columns if c in filtered.columns]
        if valid_cols:
            filtered = filtered[valid_cols]

    return filtered
```

#### `app.py` — filter controls (between data preview and AI summary)

```python
# ── Data filters ─────────────────────────────────────────────────────────
if st.session_state.df is not None:
    st.markdown("### 🔍 Filter Data")

    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1])

    with col_filter1:
        all_columns = st.session_state.df.columns.tolist()
        selected_columns = st.multiselect(
            "Columns to include",
            options=all_columns,
            default=all_columns,
            key="filter_columns",
        )

    with col_filter2:
        date_col = _find_date_column(st.session_state.df)
        if date_col:
            min_date = st.session_state.df[date_col].min()
            max_date = st.session_state.df[date_col].max()
            date_range = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="filter_dates",
            )

    with col_filter3:
        st.markdown("<br>", unsafe_allow_html=True)  # Align with other controls
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.session_state.filter_columns = all_columns
            if date_col:
                st.session_state.filter_dates = (min_date, max_date)
            st.rerun()

    # Apply filters to create filtered_df
    filtered_df = filter_dataframe(
        st.session_state.df,
        date_col=date_col,
        start_date=str(date_range[0]) if date_range else None,
        end_date=str(date_range[1]) if date_range else None,
        selected_columns=selected_columns,
    )
    st.session_state.filtered_df = filtered_df
    st.caption(f"Showing {len(filtered_df):,} of {len(st.session_state.df):,} rows")
```

All downstream consumers (summary, chat, charts) use `st.session_state.filtered_df` instead of `st.session_state.df`. The full `st.session_state.df` is preserved as the source of truth for filter resets.

**Downstream consumer checklist** — every reference to `st.session_state.df` that must switch to `filtered_df`:

| Consumer | Before | After |
|---|---|---|
| Data preview table | `st.dataframe(df.head(10))` | `st.dataframe(filtered_df.head(10))` |
| Summary prompt | `build_summary_prompt(df, stats)` | `build_summary_prompt(filtered_df, filtered_stats)` — recompute stats for filtered data |
| Chat prompt | `build_chat_prompt(prompt, df, stats)` | `build_chat_prompt(prompt, filtered_df, filtered_stats)` |
| Chart generation | `_generate_chart(df, ...)` | `_generate_chart(filtered_df, ...)` |
| Metrics row | `stats['row_count']` | `len(filtered_df)` — must use filtered stats, not full df stats |
| AI Summary display | `st.session_state.summary` | Re-generate summary from filtered_df when filters change |

Missing any consumer creates a silent bug where charts/prompts use unfiltered data while the UI shows filtered data.

**Edge cases:**
- **Empty filtered dataset:** Show `st.warning("No rows match your filters. Try a wider date range.")` and don't crash.
- **Date column with mixed formats:** `pd.to_datetime(..., errors="coerce")` handles this — unparseable values become NaT and are excluded from filtering.
- **All columns deselected:** If `selected_columns` is empty, show a warning rather than an empty DataFrame.
- **Filter state persistence:** Store filter values in `st.session_state` so they survive reruns. The "Reset Filters" button clears them.

**Risk:** Medium. Touches the core data flow. Every consumer of `st.session_state.df` must be updated to use `filtered_df`. Missing one creates a subtle bug where the summary/chart uses unfiltered data.

**Test impact:** 4-5 new tests in `test_data_loader.py`:
- `test_filter_dataframe_by_date_range`
- `test_filter_dataframe_by_columns`
- `test_filter_dataframe_empty_result`
- `test_filter_dataframe_no_filters_returns_original`

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify filters don't crash the app.

**Dependencies:** None directly, but touches the same areas as #7 (loading state) and should be done after that is stable.

---

### #16: Multi-turn conversation memory (#17 from roadmap)

**Files:** `utils/prompt_templates.py`, `app.py`

**Why now:** Currently, every chat message is independent — Gemini has no memory of previous Q&A. Users can't ask "What about last month?" without re-specifying context. Adding the last 3-5 exchanges to the prompt gives Gemini context for follow-up questions.

**Changes:**

#### `utils/prompt_templates.py` — modified signature
```python
def build_chat_prompt(
    user_question: str,
    df: pd.DataFrame,
    stats: dict[str, Any],
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
```

And in the prompt construction, after the sample data and before the user question:
```python
# If we have conversation history, include it
if conversation_history:
    history_entries = conversation_history[-5:]  # Last 5 exchanges
    history_str = "\n".join(
        f"User: {h['question']}\n"
        f"Assistant: {h.get('response', '')[:500]}"  # Truncate long responses
        for h in history_entries
        if h.get("response")  # Only include answered questions
    )
    if history_str.strip():
        prompt += (
            f"\n\nCONVERSATION HISTORY (for context only — answer the "
            f"current question, not these):\n{history_str}\n"
        )
```

**Why the "answer the current question" instruction:** Without it, Gemini sometimes continues answering the previous question instead of the new one. The guard clause makes it explicit.

#### `app.py` — pass history
In `_render_main()`, in the chat input handler:
```python
chat_prompt = build_chat_prompt(
    prompt,
    df,
    stats,
    conversation_history=st.session_state.chat_history,  # <-- new
)
```

#### `app.py` — "New Conversation" button
Add between the chat header and the chat history:
```python
col_chat_header, col_new_chat = st.columns([4, 1])
with col_new_chat:
    if st.button("🆕 New Chat", use_container_width=True, 
                 help="Clear chat history but keep your data"):
        st.session_state.chat_history = []
        st.rerun()
```

**Edge cases:**
- **Very long conversations (50+ Q&A):** Only include last 5 exchanges. Each response truncated to 500 chars. This keeps the prompt well within Gemini's context window.
- **First message:** `conversation_history` is empty → no history block appended. Works the same as before.
- **Failed responses (None):** If `entry["response"]` is None (error during API call), skip that entry from the history block.
- **Memory across data changes:** If the user clears data and uploads a new file, they get a new conversation automatically (chat history is wiped by `clear_data()`).

**Risk:** Medium. Changes prompt construction, which is the most sensitive part of the app. Must ensure:
1. The history doesn't confuse Gemini about which data is current
2. The "answer the current question" guard clause works
3. Token count stays within limits

**Test impact:** 3-4 new tests in `test_prompt_templates.py`:
- `test_build_chat_prompt_includes_history`
- `test_build_chat_prompt_truncates_long_history`
- `test_build_chat_prompt_handles_empty_history`
- `test_build_chat_prompt_history_not_included_for_first_message`

**Dependencies:** None.

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify chat still works with conversation history.

---

### #17: Export chat as report (#2 from roadmap)

**Files:** `app.py`, new `utils/report_exporter.py`

**Why now:** Users will want to share AI-generated insights and charts with stakeholders. A download button that bundles the AI summary, chat Q&A, and charts into a Markdown file is the simplest export format — it renders on GitHub, in VS Code, and in any Markdown viewer.

**Changes:**

#### `utils/report_exporter.py` (new)
```python
"""Report exporter — builds downloadable Markdown reports from chat sessions."""

from typing import Any
import base64
from io import BytesIO
import pandas as pd
import plotly.graph_objects as go


def build_markdown_report(
    summary: str | None,
    chat_history: list[dict[str, Any]],
    stats: dict[str, Any],
    data_source: str | None = None,
) -> str:
    """Build a Markdown report from the current session.

    Args:
        summary: AI-generated summary text (or None)
        chat_history: List of {"question": ..., "response": ..., "chart": ...}
        stats: Dataset statistics dict
        data_source: "file" or "ga4" (or None)
    """
    lines = []

    # Title
    lines.append("# 📊 GA4 Insight Explorer — Report")
    lines.append("")
    lines.append(f"*Generated on {pd.Timestamp.now().strftime('%Y-%m-%d at %H:%M')}*")
    lines.append(f"*Data source: {data_source or 'Unknown'}*")
    lines.append("")

    # Stats
    lines.append("## 📋 Dataset Overview")
    lines.append("")
    lines.append(f"- **Rows:** {stats.get('row_count', 'N/A'):,}")
    lines.append(f"- **Columns:** {stats.get('column_count', 'N/A')}")
    lines.append(f"- **Date range:** {stats.get('date_range_start', 'N/A')} → {stats.get('date_range_end', 'N/A')}")
    lines.append("")

    # AI Summary
    if summary:
        lines.append("## 🤖 AI-Generated Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Chat history
    if chat_history:
        lines.append("## 💬 Q&A")
        lines.append("")
        for i, entry in enumerate(chat_history, 1):
            if entry.get("response"):
                lines.append(f"### Q{i}: {entry['question']}")
                lines.append("")
                lines.append(entry["response"])
                lines.append("")
                if entry.get("chart") and entry["chart"].get("fig"):
                    chart_png = _chart_to_base64(entry["chart"]["fig"])
                    if chart_png:
                        lines.append(f"![Chart for Q{i}]({chart_png})")
                        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by [GA4 Insight Explorer](https://github.com/griffinkelton/insights-explorer)*")

    return "\n".join(lines)


def _chart_to_base64(fig: go.Figure) -> str | None:
    """Convert a Plotly figure to a base64 PNG string for Markdown embedding.

    Requires kaleido: pip install kaleido
    """
    try:
        img_bytes = fig.to_image(format="png", scale=2)
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None  # Silently skip if kaleido isn't installed
```

#### `app.py` — export button
In the chat area, after the chat history rendering:
```python
if st.session_state.chat_history:
    st.divider()
    if st.button("📥 Export Report", use_container_width=True):
        from utils.report_exporter import build_markdown_report

        report = build_markdown_report(
            summary=st.session_state.summary,
            chat_history=st.session_state.chat_history,
            stats=st.session_state.stats or {},
            data_source=st.session_state.data_source,
        )
        st.download_button(
            label="⬇️ Download Markdown Report",
            data=report,
            file_name=f"ga4_insight_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
        )
        st.caption(
            "⚠️ Charts missing from the report? "
            "Install kaleido: `pip install kaleido`"
        )
```

#### `requirements.txt` (or `requirements/dev.txt`)
Add:
```
kaleido>=0.2.1
```

**Why Markdown not PDF:** Markdown is simpler — no external renderer needed. It renders on GitHub (where most data reports live), in VS Code, and in dozens of free viewers. PDF requires `weasyprint` or `fpdf` which add significant complexity and dependency weight.

**Why `kaleido` for chart export:** Plotly's `fig.to_image()` requires either `kaleido` (cross-platform, `pip install kaleido`) or `orca` (deprecated, requires a separate system install). `kaleido` is the official replacement.

**Edge cases:**
- **`kaleido` not installed:** `_chart_to_base64` catches the error and returns `None` — charts are skipped. A `st.caption` warning is shown below the download button so the user knows why charts are missing and how to fix it.
- **Very long chat history (100+ Q&A):** The entire history is included. Markdown files have no practical size limit for text. For extreme cases, add a `max_entries=50` parameter.
- **No charts in session:** The export still works — just skips the chart embedding.
- **No AI summary:** The "🤖 AI-Generated Summary" section is omitted if `summary` is None.

**Risk:** Medium. Requires a new dependency (`kaleido`). Chart export can be slow for complex figures (2-5 seconds per chart). The `_chart_to_base64` function runs synchronously — for sessions with many charts, the export button click could take 10+ seconds.

**Test impact:** 2-3 new tests in `test_report_exporter.py`:
- `test_builds_report_with_summary_and_chat`
- `test_builds_report_without_charts`
- `test_builds_report_handles_empty_state`

**Dependencies:** None.

**Post-implementation:** Run `bash scripts/smoke_test.sh` to verify the app boots and the export button renders.

---

## ⚪ Priority 5 — Larger Investments (4 items)

Estimated total time: **5-10 days** (one person, sequential)

---

### #18: Light/dark theme toggle (#1 from roadmap)

**Files:** `utils/styles.py`, `app.py`

**Approach:** Use CSS custom properties with `[data-theme]` attribute selectors. A toggle in the sidebar sets `st.session_state.theme`. A small JS snippet syncs `document.documentElement.dataset.theme` with the session state.

**Scope:** ~80 CSS variable overrides for light theme:
- `--bg-primary: #ffffff`
- `--bg-secondary: #f5f5fa`
- `--bg-card: #ffffff`
- `--text-primary: #1a1a2e`
- `--text-secondary: #686880`
- `--accent: #6366f1`
- `--border: rgba(0, 0, 0, 0.08)`
- etc. for all ~40 CSS variables currently defined

**Complexity:** Streamlit's component styling is deeply embedded (`data-testid` selectors, `!important` rules). The light theme overrides must be tested against every component: sidebar, buttons, metrics, expanders, dataframes, chat messages, alerts, file uploader, spinners, Plotly charts.

**Risk:** High effort for polish. CSS alone is 100+ lines of overrides. The result is a genuinely impressive feature but requires careful testing across all components.

**Test impact:** Smoke test (visual inspection). No automated test for CSS correctness.

---

### #19: Streaming token-by-token responses (#18 from roadmap)

**Files:** `utils/gemini_client.py`, `app.py`

**Approach:** Add `generate_response_stream(prompt)` generator in `gemini_client.py`:
```python
def generate_response_stream(prompt: str, model: str = DEFAULT_MODEL):
    """Stream response tokens one at a time."""
    response = _get_client().models.generate_content_stream(
        model=model,
        contents=prompt,
        config={...},
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text
```

In `app.py`, use `st.write_stream()`:
```python
with st.chat_message("assistant"):
    response_text = st.write_stream(generate_response_stream(chat_prompt))
    # After stream completes, detect chart from full response_text
    chart_config = detect_chart_request(response_text)
    if chart_config:
        chart_data = _generate_chart(df, chart_config, response_text, prompt)
        st.plotly_chart(chart_data["fig"], use_container_width=True)
```

**Why this is complex:** The current architecture calls `generate_response` → gets full text → calls `detect_chart_request` on the full text → renders chat + chart. With streaming, chart detection must happen *after* the stream completes, which requires restructuring the chat response flow:
1. Render the streaming text with `st.write_stream`
2. Collect the full text from `st.write_stream`'s return value
3. Run chart detection on the full text
4. Render the chart below the streamed text

**Risk:** High. Fundamentally changes the response rendering pipeline. Must handle error states during streaming (connection drops mid-response). The `st.write_stream` API is relatively new (Streamlit 1.37+).

**Test impact:** Mock `generate_content_stream` in `test_gemini_client.py` — 2-3 new tests.

---

### #20: Refactor app.py into components/ (#9 from roadmap)

**Files:** New `components/` package with `sidebar.py`, `hero.py`, `data_preview.py`, `chat.py`. New `utils/charts.py`.

**Approach:** Extract each section into a function in its own module. `app.py` becomes a thin orchestrator. Before:

```
app.py (~400 lines)
├── Page config + CSS injection
├── Session state initialization (14 keys)
├── API key validation + banner
├── OAuth callback handler
├── clear_data() function
├── Sidebar (file uploader, GA4 connect, privacy, clear button)   ← extract
├── File processing block
├── _render_main() (header, hero, data preview, summary, chat)     ← extract sub-sections
├── _render_hero()                                                  ← extract
├── Error boundary wrapper
├── _generate_summary() callback
├── _generate_chart() + _find_column() + _find_date_column()        ← extract to utils/charts.py
└── Footer
```

After:

```
app.py (~120 lines)
├── Page config + CSS injection
├── Session state initialization (14 keys)
├── API key validation + banner
├── OAuth callback handler
├── Error boundary wrapper → components.render_all()

components/
├── __init__.py          # render_all() orchestrator
├── sidebar.py           # render_sidebar() — uploader, GA4 connect, learn link
├── hero.py              # render_hero() — empty state
├── data_preview.py      # render_data_preview() — metrics, table, filters
├── chat.py              # render_chat() — chat history, input, export button
└── summary.py           # render_summary() — AI summary + generate button

utils/
├── charts.py            # generate_chart(), find_column(), find_date_column()
└── ... (existing files)
```

**Complexity:** Session state references are tightly coupled to `app.py`. Each extracted component must either:
1. Accept session state values as function parameters (clean but verbose), or
2. Access `st.session_state` directly from the component module (works because Streamlit shares `st.session_state` globally)

Option 2 is simpler and more Streamlit-idiomatic. All components import `streamlit as st` and read/write `st.session_state` directly — same as they do in `app.py`.

**Risk:** Medium. Mechanical extraction, but session state coupling makes it tedious. The risk is breaking something subtle — like a widget key collision or a callback that references a function that moved modules.

**Test impact:** Each component gets a structural test (AST parse + section checks). The existing `test_app.py` (#13) validates the orchestrator.

---

### #21: Remaining AI & data processing enhancements

This item is a catch-all for the remaining ENHANCEMENTS.md items not individually planned above. Each would be a separate implementation task.

| Roadmap # | Enhancement | Effort | What it does |
|---|---|---|---|
| #20 | Structured chart detection via Gemini | Medium | Replace keyword heuristics with `[CHART:line:sessions]` tokens in Gemini responses — more accurate, fewer false negatives |
| #23 | Gemini-suggested chart mapping | Medium | Ask Gemini to output JSON: `{"chart_type": "bar", "x": "device", "y": "users"}` — parse with `json.loads` and map dynamically to Plotly |
| #22 | Comparative analysis mode | High | "Compare Q2 vs Q1" or "organic vs paid traffic" — dual-panel prompts and charts |
| #25 | Automatic column type detection | Medium | Detect: date-like columns, numeric metrics, string columns with <50 unique values (dimensions). Show as "detected dimensions/metrics" in data preview |
| #26 | Statistical anomaly detection | Medium | Rolling Z-score: flag dates where a metric deviates >2 std from the 7-day rolling mean. Red markers on charts |
| #27 | Intelligent sampling | Small | For >10k rows: stratified sampling. For >100k rows: only aggregate stats in prompts, never raw rows |

Each of these is described in detail in [ENHANCEMENTS.md](ENHANCEMENTS.md) with the "Why" and "How." They should be planned individually before implementation.

---

## 📈 Execution Strategy

### Phase dependencies

```
Phase 1 (parallel safe, ~1 hr total):
  #1  Add Learn link to sidebar        ─┐
  #2  Update learn page test count      ├─ No dependencies
  #6  Add .streamlit/pages.toml        ─┘
  #3  Update docs (ENHANCEMENTS, ARCH)  ── Depends on #2 for accurate counts
  #9  Add Learn link to README          ── No dependency (but better after #1)

Phase 2 (~2.5 hrs total):
  #4  File size/row limits              ─┐
  #5  Rate limiting on chat             ├─ All independent
  #13 Add app.py structural test       ─┘
  #10 Add pytest-cov                    ─┐
  #11 Split dev dependencies            ├─ #10 goes into #11's dev.txt
  #12 Per-module test badges            ─┘

Phase 3 (sequential, ~2.5 hrs):
  #7  Loading state for summary         ── Standalone (touches app.py)
  #14 GitHub Actions CI                 ── Standalone (new file only)
  #8  Onboarding tour                   ── Touches same app.py area as #1/#7

Phase 4 (larger, one at a time, ~5 hrs):
  #15 Column picker & date filters      ── Touches data flow
  #16 Multi-turn conversation memory   ── Touches prompt construction
  #17 Export chat as report             ── Standalone (new module)

Phase 5 (future, 5-10 days):
  #18-#21                               ── Each 1-3 days
```

### Recommended sprint plan

| Sprint | Items | Outcome |
|---|---|---|
| **Sprint 1** (2 hours) | #1, #2, #6, #3, #9 | Sidebar learn link, accurate docs, polished nav |
| **Sprint 2** (2.5 hours) | #4, #5, #10, #11, #12, #13 | Safety guardrails, coverage reporting, full structural tests |
| **Sprint 3** (3 hours) | #7, #14, #8 | Loading spinner, GitHub Actions, onboarding tour |
| **Sprint 4** (5 hours) | #15, #16, #17 | Column filters, conversation memory, chat export |
| **Sprint 5+** (as needed) | #18-21 | Theming, streaming, refactor, advanced AI features |

---

## 📊 Progress Tracking

| # | Item | Priority | Status |
|---|---|---|---|
| 1 | Learn link to sidebar | 🔴 P1 | 🔲 Planned |
| 2 | Update learn page test count | 🔴 P1 | 🔲 Planned |
| 3 | Update docs (ENHANCEMENTS, ARCHITECTURE, README) | 🔴 P1 | 🔲 Planned |
| 4 | File size/row limits | 🔴 P1 | 🔲 Planned |
| 5 | Rate limiting on chat | 🔴 P1 | 🔲 Planned |
| 6 | `.streamlit/pages.toml` | 🔴 P1 | 🔲 Planned |
| 7 | Loading state for summary | 🟡 P2 | 🔲 Planned |
| 8 | Onboarding tour | 🟡 P2 | 🔲 Planned |
| 9 | Learn link to README | 🟡 P2 | 🔲 Planned |
| 10 | pytest-cov coverage | 🟢 P3 | 🔲 Planned |
| 11 | Split dev dependencies | 🟢 P3 | 🔲 Planned |
| 12 | Per-module test badges | 🟢 P3 | 🔲 Planned |
| 13 | app.py structural test | 🟢 P3 | 🔲 Planned |
| 14 | GitHub Actions CI | 🟢 P3 | 🔲 Planned |
| 15 | Column picker & date filters | 🔵 P4 | 🔲 Planned |
| 16 | Multi-turn conversation memory | 🔵 P4 | 🔲 Planned |
| 17 | Export chat as report | 🔵 P4 | 🔲 Planned |
| 18 | Light/dark theme toggle | ⚪ P5 | 🔲 Planned |
| 19 | Streaming responses | ⚪ P5 | 🔲 Planned |
| 20 | Refactor app.py into components | ⚪ P5 | 🔲 Planned |
| 21 | Remaining AI & data enhancements | ⚪ P5 | 🔲 Planned |

---

*Plan created from deep review of the codebase. No code has been written — this is a review-for-approval document. All 21 items are traceable to specific items in ENHANCEMENTS.md.*
