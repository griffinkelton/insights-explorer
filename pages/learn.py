"""Learn — interactive walkthrough of the GA4 Insight Explorer architecture and concepts.

Refactored for v0.2.0: 8 learner-journey sections replace the old technology-centric
tab layout.  Each section follows a progressive pattern:
    plain-English concept → real app example → small annotated excerpt → try it → check
"""

import streamlit as st

from utils.styles import inject_custom_css, inject_favicon_meta

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Learn · GA4 Insight Explorer",
    page_icon="assets/favicon.ico",
)

# ── Theme-aware CSS + favicon ─────────────────────────────────────────────────
inject_custom_css(theme=st.session_state.get("theme", "dark"))
inject_favicon_meta(theme=st.session_state.get("theme", "dark"))

# ── Hero ─────────────────────────────────────────────────────────────────────
_theme = st.session_state.get("theme", "dark")
_hero_color = "#6b7280" if _theme == "light" else "#9898b0"
st.markdown(
    f"""
<div style="text-align:center;padding:2rem 1rem 1.5rem 1rem;">
    <div style="font-size:3.5rem;margin-bottom:0.5rem;">📚</div>
    <h1 style="font-size:2.2rem;margin-bottom:0.3rem;">
        Learn How Insight Explorer Works
    </h1>
    <p style="color:{_hero_color};font-size:1rem;max-width:700px;margin:0 auto;line-height:1.6;">
        A guided tour through the app's architecture — from uploading data to
        asking AI questions, with privacy principles at every step.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Back to app ──────────────────────────────────────────────────────────────
st.page_link(
    "app.py",
    label="← Back to App",
    icon="🏠",
    help="Return to the GA4 Insight Explorer",
)

# ── Tabs: 8-section learner's journey ────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    [
        "🚀 Start here",
        "📊 Follow the data",
        "📈 Explore & analyze",
        "🤖 Ask AI well",
        "🔐 Privacy & safety",
        "🐍 Build it in Python",
        "🧩 Guided challenges",
        "🗺️ Where next",
    ]
)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. START HERE
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 🚀 Start here — what you can do in 60 seconds")

    st.markdown(
        """
    The **GA4 Insight Explorer** is a local assistant for your analytics data.
    You can do four things in any session:

    1. **Upload** a CSV or XLSX export from GA4 — or connect live via Google sign‑in
    2. **Inspect** your data with filters, custom metrics, and quality checks
    3. **Analyze** with AI‑generated summaries, charts, forecasts, and funnel views
    4. **Export** results to Google Sheets when you find something worth sharing
    """
    )

    st.markdown("### The interface at a glance")
    st.code(
        """# The app is a single Streamlit script with a sidebar + main area.
#
#   ┌─────────── Sidebar ───────────┐  ┌──── Main area ────────────────────┐
#   │  📂 Upload file               │  │  📊 Data preview (table + stats)  │
#   │  🔗 Connect GA4 live          │  │  ✨ Generate AI summary           │
#   │  🔍 Filter Data               │  │  💬 Chat with your data           │
#   │  ➕ Custom metrics            │  │  📈 Charts, forecast, funnels    │
#   │  🗑️  Clear data               │  │  📋 Export to Google Sheets      │
#   └────────────────────────────────┘  └──────────────────────────────────┘""",
        language="text",
    )

    st.markdown("### Try it now")
    st.markdown(
        """
    1. Go back to the app (🏠 button above)
    2. Upload a GA4 CSV export in the sidebar
    3. Click **Generate Summary** to see an AI overview of your data
    """
    )

    st.markdown(
        '<div class="tip-box"><strong>💡 Key insight:</strong> Streamlit reruns '
        "your entire Python script on every interaction (button click, text input, "
        "etc.). That's why the app uses <code>st.session_state</code> to persist "
        "data across reruns and <code>@st.cache_data</code> to skip expensive "
        "recomputation.</div>",
        unsafe_allow_html=True,
    )

    st.caption("See also: `app.py` (entrypoint), `components/sidebar.py` (upload & GA4 connect)")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. FOLLOW THE DATA
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## 📊 Follow the data — the `DataContext` lifecycle")

    st.markdown(
        """
    Understanding how data flows through the app is the key to getting reliable
    results.  The app uses a **three-layer model** called `DataContext`:

    | Layer | What it holds | When it changes |
    |---|---|---|
    | `raw_df` | The original uploaded or GA4-pulled data | Never — it's the immutable ground truth |
    | `base_df` | The unfiltered analytical dataset (includes custom metrics) | When you add or remove custom metrics |
    | `active_df` | The currently analyzed view (filtered `base_df`) | When you apply, change, or clear filters |

    This design ensures that clearing filters always restores your full
    analytical base — custom metrics survive. And every transformation
    produces a new `DataContext` so there's no accidental mutation.
    """
    )

    st.markdown("### How data gets loaded")
    st.code(
        """# utils/data_loader.py — simplified
import pandas as pd

def load_file(file):
    filename = file.name.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(file)
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        return None, "Unsupported file type."
    if df.empty:
        return None, "The uploaded file is empty."
    return df, None""",
        language="python",
    )

    st.markdown("### Creating a DataContext")
    st.code(
        """from utils.data_context import create_context_from_upload

# The factory uses SHA-256 of the raw file bytes for identity.
# Same file → same ID.  Different file → different ID.
ctx = create_context_from_upload(
    df,
    file_bytes,           # raw uploaded bytes
    display_name="Q3_report.csv",
)
# ctx.source_id = "file:a1b2c3d4e5f6..."
# ctx.version   = 0
# ctx.raw_df    = original data (never modified)
# ctx.base_df   = copy of original
# ctx.active_df = same as base (no filters yet)""",
        language="python",
    )

    st.markdown("### Filters and custom metrics")
    st.markdown(
        """
    - **Filters** (date range, column subset) produce a new `DataContext` with
      `active_df` set to the filtered rows.  The filter is always computed from
      `base_df` — never from a previously filtered `active_df` — so changing a
      date range doesn't accidentally compound.
    - **Custom metrics** (e.g. `sessions / users`) rebuild `base_df` from
      `raw_df` and clear any active filters, because a filter on old columns
      may not make sense against the new derived column.
    """
    )

    st.markdown(
        '<div class="tip-box"><strong>💡 Key insight:</strong> '
        "The three-layer model prevents a common bug: adding a metric while "
        "a date filter is active would discard rows outside that date range "
        "from the new base.  By rebuilding from <code>raw_df</code>, every "
        "row is preserved.</div>",
        unsafe_allow_html=True,
    )

    st.caption(
        "See also: `utils/data_context.py` (the full DataContext module), `tests/test_data_context.py`"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 3. EXPLORE & ANALYZE
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## 📈 Explore & analyze — charts, forecasting, and funnels")

    st.markdown(
        """
    Every chart and analysis in this app is built from the **actual DataFrame**
    — never from AI‑generated numbers.  The three main analysis tools are:
    """
    )

    st.markdown("### 1. Interactive charts")
    st.code(
        """import plotly.express as px

# Group sessions by date
daily = df.groupby(date_col)["sessions"].sum().reset_index()
fig = px.line(daily, x=date_col, y="sessions",
              title="Sessions Over Time")
st.plotly_chart(fig, use_container_width=True)""",
        language="python",
    )

    st.markdown("### 2. Linear trend projection (forecasting)")
    st.markdown(
        """
    The forecasting tool fits a **linear regression** to your time series and
    projects forward by a configurable number of periods.  It shows confidence
    bands, slope, and R².  This is a simple extrapolation — not a probabilistic
    model — so treat it as a directional signal, not a precise prediction.
    """
    )

    st.markdown("### 3. Page-path funnel analysis")
    st.code(
        """# utils/funnels.py — simplified
def build_funnel(df, path_col, metric_col, steps):
    \"\"\"Aggregate a page-path funnel.\"\"\"
    funnel = []
    for step_paths in steps:
        mask = df[path_col].isin(step_paths)
        total = df.loc[mask, metric_col].sum()
        funnel.append({"step": step_paths, metric_col: total})
    return funnel""",
        language="python",
    )

    st.markdown("### Quality checks")
    st.markdown(
        """
    When data is loaded, the app runs automatic quality checks:
    - Column presence (case‑insensitive matching against expected columns)
    - Date parsing (handles multiple date formats)
    - Numeric column detection for stats
    - Missing value flags
    - Anomaly detection (z‑score outliers)

    A quality report card is displayed above the data preview.
    """
    )

    st.markdown(
        '<div class="tip-box"><strong>💡 Key insight:</strong> '
        'Pandas <code>pd.to_datetime(..., errors="coerce")</code> turns '
        "unparseable dates into <code>NaT</code> instead of crashing.  Always "
        "use it when reading user‑uploaded data.</div>",
        unsafe_allow_html=True,
    )

    st.caption(
        "See also: `utils/charts.py`, `utils/forecasting.py`, `utils/funnels.py`, `components/data_preview.py`"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 4. ASK AI WELL
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 🤖 Ask AI well — what Gemini sees and how to get good answers")

    st.markdown(
        """
    The app sends a **structured prompt** to Gemini that includes:

    - A description of your dataset (row count, columns, date range)
    - Statistical summary (describe() output for numeric columns)
    - Quality report findings
    - Your question
    - Optional: chart suggestions (opt‑in)
    """
    )

    st.markdown("### Model selection")
    st.markdown(
        """
    You can choose your Gemini model from the sidebar.  The free tier supports
    `gemini-2.5-flash` (default) and other flash variants.  Different models
    have different speed, quality, and quota characteristics — pick the one
    that fits your task.
    """
    )

    st.markdown("### Prompt construction (simplified)")
    st.code(
        """# utils/prompt_templates.py — simplified
def build_chat_prompt(df, stats, quality, user_question):
    prompt = f\"\"\"
You are an analytics assistant.
Dataset: {len(df)} rows, {list(df.columns)}
Statistics:
{stats}
Quality notes: {quality}
---
Question: {user_question}
\"\"\"
    return prompt""",
        language="python",
    )

    st.markdown("### Usage visibility")
    st.markdown(
        """
    After each response, the chat UI shows the **provider‑reported token counts**:
    input tokens, output tokens, thought tokens, and total.  No percentages,
    gauges, or "approaching limit" warnings — just the raw numbers.
    When usage metadata is unavailable, the UI shows
    *"Usage unavailable for this request"* rather than fabricating an estimate.
    """
    )

    st.markdown(
        '<div class="tip-box"><strong>💡 Key insight:</strong> '
        "Streaming responses display token‑by‑token as they arrive, but usage "
        "metadata only appears at the end.  If the stream fails mid‑response, "
        "the error is shown in context without losing the conversation history."
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption(
        "See also: `utils/gemini_client.py`, `utils/prompt_templates.py`, `SECURITY.md` (AI data handling)"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 5. PRIVACY & SAFETY
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("## 🔐 Privacy & safety — how your data is protected")

    st.markdown(
        """
    The v0.1.0 hardening release established a strong security baseline.
    Every design decision below is documented and tested.
    """
    )

    st.markdown("### Session‑only processing")
    st.markdown(
        """
    - All uploaded data lives **only in `st.session_state`** — no server‑side
      database, no persistent files, no caching to disk.
    - **`DataContext`** is the single owner of loaded, filtered, and
      custom‑metric state.  There is no ambiguity about which DataFrame is
      current.
    - Clearing data from the sidebar immediately removes the `DataContext`
      and all derived analysis state from the session.
    """
    )

    st.markdown("### Gemini disclosure")
    st.markdown(
        """
    - The app **always** sends your data's statistical summary (not raw rows)
      to the Gemini API.
    - AI features are **opt‑in for chart suggestions** — you control whether
      charts are generated automatically.
    - When confidential Evidence dashboard data is integrated in the future,
      AI analysis will be disabled by default for those sources.
    """
    )

    st.markdown("### OAuth & scopes")
    st.markdown(
        """
    - GA4: `analytics.readonly` scope — the app can read your GA4 data but
      cannot modify properties, create accounts, or manage users.
    - Google Drive: `drive.file` scope — the most restrictive Drive scope.
      The app can only access files it creates (exports).  It cannot list or
      read your existing Drive files.
    - OAuth state is **session‑only** and never persisted to disk.
    - An AST‑based static guard rejects any reintroduction of broader scopes
      in production code.
    """
    )

    st.markdown("### Export safety")
    st.markdown(
        """
    - Exports to Google Sheets happen only on **explicit user action**
      (clicking an export button).
    - PDF exports sanitize spreadsheet values and text fields before embedding.
    - A static analysis test enforces the `drive.file` scope requirement.
    """
    )

    st.markdown("### Error redaction")
    st.markdown(
        """
    Errors shown in the UI never expose raw file paths, stack traces, API keys,
    OAuth tokens, or internal state.  The `error_boundary` component wraps all
    rendering and strips sensitive information automatically.
    """
    )

    st.markdown(
        '<div class="tip-box"><strong>🔐 Reminder:</strong> '
        "The app is designed as a local assistant.  Never host it on a public "
        "server without additional authentication, rate limiting, and a proper "
        "secret‑management solution.</div>",
        unsafe_allow_html=True,
    )

    st.caption(
        "See also: `SECURITY.md` (full security model), `utils/error_boundary.py`, `utils/ga4_client.py`"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 6. BUILD IT IN PYTHON
# ═══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("## 🐍 Build it in Python — one complete end‑to‑end change")

    st.markdown(
        """
    The best way to understand the app is to **make a small change and test it**.
    Here's a guided walkthrough of adding a new data quality check.
    """
    )

    st.markdown("### Step 1: Add the check function")
    st.code(
        """# In utils/data_loader.py
def detect_duplicate_rows(df):
    \"\"\"Return the number of fully duplicated rows.\"\"\"
    return int(df.duplicated().sum())""",
        language="python",
    )

    st.markdown("### Step 2: Integrate it into the quality report")
    st.markdown(
        "Find where the quality report dict is built (in `_run_quality_checks`) "
        "and add a `duplicate_rows` key using your new function."
    )

    st.markdown("### Step 3: Write a test")
    st.code(
        """# In tests/test_data_loader.py
def test_duplicate_detection():
    from utils.data_loader import detect_duplicate_rows
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    assert detect_duplicate_rows(df) == 1""",
        language="python",
    )

    st.markdown("### Step 4: Run the test suite")
    st.code(
        """$ python -m pytest tests/test_data_loader.py -q
.                                                          [100%]
1 passed""",
        language="bash",
    )

    st.markdown("### Step 5: Check yourself")
    st.markdown(
        """
    Run the full suite to make sure nothing is broken:

    ```bash
    $ python -m pytest tests/ -q
    ... all tests passed
    ```

    If the suite passes, your change is safe.  This is the same workflow used
    for every feature in the app.
    """
    )

    st.caption("See also: `tests/` (test suite), `ARCHITECTURE.md` (module map)")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. GUIDED CHALLENGES
# ═══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown("## 🧩 Guided challenges — test your understanding")

    st.markdown(
        """
    Each challenge asks you to make a small code change and verify the result.
    Solutions are in the linked test files — try them yourself first!
    """
    )

    st.markdown("### 🟢 Beginner: Add a new custom metric formula")
    st.markdown(
        """
    **Task:** Make the custom metric `Engagement per User` use
    `engaged_sessions / users` instead of `sessions / users`.

    - Find the metric definition in `components/sidebar.py`
    - Change the formula
    - Run `python -m pytest tests/test_custom_metrics.py` to verify
    """
    )

    st.markdown("### 🟡 Intermediate: Add a column to the quality report")
    st.markdown(
        """
    **Task:** Add a `zero_sessions` flag to the quality report that counts
    rows where `sessions == 0`.

    - Add a helper in `utils/data_loader.py`
    - Add the key to the quality report dict
    - Write a test in `tests/test_data_quality.py`
    - Run the full suite
    """
    )

    st.markdown("### 🔴 Advanced: Thread the `truncated` flag through the AI prompt")
    st.markdown(
        """
    **Task:** When GA4 data hits the 500,000‑row cap, the summary prompt should
    include a note: *"This dataset was truncated at 500,000 rows."*

    - `DataContext.truncated` is already set by the GA4 pull path
    - Update `build_summary_prompt()` in `utils/prompt_templates.py` to read
      the `truncated` flag from the `DataContext`
    - Write a test showing the truncated message appears when the flag is
      `True`
    - Run `python -m pytest tests/ -q`
    """
    )

    st.caption("See also: `tests/` for challenge solutions embedded in test assertions")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. WHERE NEXT
# ═══════════════════════════════════════════════════════════════════════════════
with tab8:
    st.markdown("## 🗺️ Where next — resources and roadmap")

    st.markdown("### Project docs")
    st.markdown(
        """
    | Document | What it covers |
    |---|---|
    | `README.md` | Quick‑start guide, features, getting your API key |
    | `ARCHITECTURE.md` | Module map, data flow, design rationale |
    | `SECURITY.md` | Complete security model, scope justification, threat model |
    | `DOCUMENTATION_INDEX.md` | Index of every doc, plan, and spec in the repo |
    | `CHANGELOG.md` | Release history with test counts and key changes |
    | `IDEAS.md` | Feature backlog and future concepts |
    """
    )

    st.markdown("### Current plan")
    st.markdown(
        """
    - **[🔵 v0.2.0 plan](https://github.com/griffinkelton/insights-explorer/blob/main/plans/%F0%9F%94%B5%20v0.2.0-plan.md)**
      — architecture, accessibility, documentation, and UX improvements.
    - **[🔵 v0.2.0 implementation spec](https://github.com/griffinkelton/insights-explorer/blob/main/plans/00-sprints/%F0%9F%94%B5%20v0.2.0-implementation-spec.md)**
      — detailed design decisions and acceptance criteria.
    - **[🔵 v0.2.0 release checklist](https://github.com/griffinkelton/insights-explorer/blob/main/plans/audit/%F0%9F%94%B5%20v0.2.0-release-checklist.md)**
      — binary gates for the v0.2.0 release.
    """
    )

    st.markdown("### Test suite")
    st.markdown(
        """
    The project has over 500 tests across 27+ test modules.  Run them with:

    ```bash
    $ python -m pytest tests/ -q
    ```

    Coverage report:

    ```bash
    $ python -m pytest tests/ --cov=utils --cov=components --cov=pages --cov-report=term-missing
    ```
    """
    )

    st.markdown("### Contributing")
    st.markdown(
        """
    1. Create a branch from `main`
    2. Make your change and write tests
    3. Run `python -m pytest tests/ -q` — all tests must pass
    4. Run `pre-commit run --all-files` — linting must be clean
    5. Open a PR against `main`

    The `.github/workflows/test.yml` CI workflow runs the full test suite on
    every push.
    """
    )

    st.markdown(
        '<div class="tip-box"><strong>🎯 Ready?</strong> '
        "Go back to the app and try uploading your own GA4 data.  Every line "
        "of code is a lesson — and the test suite has your back.</div>",
        unsafe_allow_html=True,
    )

    st.caption("See also: `BUGLOG.md`, `RELEASE_CHECKLIST.md`, `.github/workflows/test.yml`")

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Learn page — content reflects v0.2.0 architecture.  "
    "Code excerpts are simplified for teaching; see source files for the full implementation."
)
