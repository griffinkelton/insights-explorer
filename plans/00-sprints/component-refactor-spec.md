# 🧩 Component Refactor — Implementation Spec

> **Source plan:** [plans/p5-p6/✅ COMPONENT_REFACTOR.md](../p5-p6/✅ COMPONENT_REFACTOR.md)
> **Status:** ✅ Done (7 phases, 228 tests, 2026-07-28)
> **Effort:** 3–5 days | **Risk:** Medium
> **Based on:** 5 rounds of user interviews (2026-07-28)

---

## 🎯 Goal

Split `app.py` (currently **809 lines**) into a `components/` package with 6 focused modules plus `utils/session.py` for shared state management. `app.py` becomes a ~60-line orchestrator. Zero behavior changes.

---

## 🏗️ Design Decisions (from interviews)

| Decision | Choice | Rationale |
|---|---|---|
| File processing location | **sidebar.py** | Depends on `uploaded_file` widget — keep coupling local |
| `clear_data()` location | **`utils/session.py`** (new) | Shared by sidebar.py and __init__.py. Avoids circular deps. User's design choice. |
| `on_click` anti-pattern | **Fix during refactor** | Replace `on_click=clear_data` with `if st.button` + `st.rerun()`. Per BUGLOG.md Pattern 2. |
| `_stream_chat_response()` | **Move as-is + document side effects** | Mutates `st.session_state.chat_history[-1]` in place during streaming. Document this in docstring for future testability refactor. |
| Widget keys | **Audit only** | List all existing keys, verify no collisions. No `_key()` abstraction layer. |
| `onboarding.py` | **Skip entirely** | Tour isn't implemented. Don't create placeholder files. Add later when feature is built. |
| Extraction order | **Charts → Hero → Data Preview → Summary → Chat → Sidebar → Orchestrator** | Lowest-risk to highest-risk. Sidebar stays last (largest, most complex). |
| Footer | **`__init__.py`** | Renders after all components in `_render_main_content()`. |
| Lazy import (report_exporter) | **Keep lazy, add comment** | `kaleido` vendors Chromium and may not be installed. Lazy import isolates ImportError to export click, not every page load. |
| `_generate_summary()` | **Match actual code** | Include `quality_report` parameter — that's what the real code does. |
| `_render_data_filters()` | **`data_preview.py`** | Filters are part of data preview flow. One file for all data display. |
| Commit strategy | **One per phase (7 commits)** | Each independently verifiable. Easier bisect. History tells the story. |
| Testing | **5-test pattern per file** | AST parse + smoke import + BUG-005 gate + BUG-008 gate + function existence. Extends existing CI patterns to new files. |
| Refactor timing | **Before theme toggle** | Theme is 95% CSS in `styles.py`. Refactoring first means theme applies to clean component files. |

---

## 🗂️ Target Architecture

### Before

```
app.py  (809 lines)
```

### After

```
app.py  (~70 lines)                   # Page config, session state, orchestrator
components/
├── __init__.py      (~65 lines)      # render_all(), OAuth callback, error boundary, footer
├── sidebar.py       (~240 lines)     # Logo, uploader, file processing, GA4 connect, privacy, clear, nav
├── hero.py          (~75 lines)      # Empty state with feature cards
├── data_preview.py  (~140 lines)     # Metrics, preview table, quality scorecard, filters
├── summary.py       (~45 lines)      # AI summary card + generate button
└── chat.py          (~200 lines)     # Chat history, chat input, streaming, chart rendering, export
utils/
├── session.py       (~25 lines)      # clear_data() — shared state reset
├── charts.py        (~100 lines)     # generate_chart(), find_column(), find_date_column()
└── ... (existing files unchanged)
```

### What Stays in `app.py`

```python
"""GA4 Insight Explorer — Streamlit web app."""

import os
import streamlit as st
from utils.styles import inject_custom_css, inject_favicon_meta
from utils.gemini_client import validate_api_key
from components import render_all

REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501")

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GA4 Insight Explorer",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS, JS & favicon ─────────────────────────────────────────────
inject_custom_css()
inject_favicon_meta()

# ── Session state initialization (all 16 keys) ───────────────────────────
_defaults = {
    "df": None, "stats": None, "summary": None, "chat_history": [],
    "missing_columns": [], "data_cleared": False, "last_file_id": None,
    "ga4_creds": None, "ga4_property_id": "", "ga4_auth_flow": None,
    "data_source": None, "quality_report": None, "api_key_valid": None,
    "api_key_error": "", "last_api_call": 0.0, "api_call_count": 0,
    "filtered_df": None,
}
for key, default in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── API key validation ───────────────────────────────────────────────────
if st.session_state.api_key_valid is None:
    is_valid, msg = validate_api_key()
    st.session_state.api_key_valid = is_valid
    if not is_valid:
        st.session_state.api_key_error = msg

if st.session_state.api_key_valid is False:
    st.error(
        f"🔑 **Gemini API Key Issue** — "
        f"{st.session_state.get('api_key_error', 'Invalid key.')}"
    )
    st.caption(
        "[Get a free key → Google AI Studio](https://aistudio.google.com/apikey)"
    )

# ── Render all UI ────────────────────────────────────────────────────────
render_all()
```

### `utils/session.py` (NEW)

```python
"""Shared session state management — extracted from app.py."""

import streamlit as st


def clear_data() -> None:
    """Wipe all session state and uploaded file from memory.

    Called from: sidebar.py (Clear Data button), __init__.py (GA4 disconnect),
    and sidebar.py (file processing — new file replaces old).
    """
    st.session_state.df = None
    st.session_state.stats = None
    st.session_state.summary = None
    st.session_state.quality_report = None
    st.session_state.chat_history = []
    st.session_state.missing_columns = []
    st.session_state.data_cleared = True
    st.session_state.data_source = None
```

### `utils/charts.py` (NEW)

```python
"""Chart generation helpers — extracted from app.py."""

from typing import Any
import pandas as pd
import plotly.express as px


def generate_chart(
    df: pd.DataFrame,
    chart_config: dict[str, str],
    gemini_response: str,
    user_question: str,
) -> dict[str, Any] | None:
    """Generate a Plotly chart. Returns {"fig": Figure, "type": str} or None."""
    # ... (existing _generate_chart from app.py lines 669-741)


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Case-insensitive column lookup by candidate names."""
    # ... (existing _find_column from app.py lines 742-748)


def find_date_column(df: pd.DataFrame) -> str | None:
    """Find the best date column in the DataFrame."""
    # ... (existing _find_date_column from app.py lines 750-758)
```

### `components/__init__.py`

```python
"""GA4 Insight Explorer — UI component orchestration."""

import streamlit as st
from components.sidebar import render_sidebar
from components.hero import render_hero
from components.data_preview import render_data_preview
from components.summary import render_summary_section
from components.chat import render_chat_section
from utils.ga4_client import exchange_code, credentials_to_dict
from utils.error_boundary import render_error_card


def render_all() -> None:
    """Render all UI sections in order. Called once from app.py."""

    # Handle OAuth callback (must happen before any rendering)
    _handle_oauth_callback()

    # Sidebar always renders
    render_sidebar()

    # Main content with error boundary
    try:
        _render_main_content()
    except Exception as e:
        if e.__class__.__module__.startswith("streamlit"):
            raise
        render_error_card(e, context="rendering the page")


def _render_main_content() -> None:
    """Main content area — hero, data preview, summary, chat, footer."""

    st.markdown(
        '<h1 style="margin-bottom:0.3rem;">GA4 Insight Explorer</h1>',
        unsafe_allow_html=True,
    )
    st.caption("Ask questions about your analytics data — powered by Gemini AI.")

    if st.session_state.df is None:
        render_hero()
        st.stop()

    render_data_preview()
    render_summary_section()
    render_chat_section()

    # Footer
    st.divider()
    st.markdown(
        '<p style="text-align:center;color:#686880;font-size:0.75rem;">'
        'GA4 Insight Explorer · Data processed in-memory only · '
        '<a href="https://aistudio.google.com/apikey" style="color:#818cf8;">Gemini API Key</a> · '
        '<a href="https://console.cloud.google.com/apis/credentials" style="color:#818cf8;">GCP OAuth Setup</a>'
        '</p>',
        unsafe_allow_html=True,
    )


def _handle_oauth_callback() -> None:
    """Handle Google OAuth redirect (?code=...)."""
    if "code" not in st.query_params or st.session_state.ga4_auth_flow is None:
        return
    try:
        creds = exchange_code(
            st.session_state.ga4_auth_flow,
            code=st.query_params["code"],
        )
        st.session_state.ga4_creds = credentials_to_dict(creds)
        st.session_state.ga4_auth_flow = None
        st.query_params.clear()
        st.success("✅ Connected to Google Analytics!")
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.session_state.ga4_auth_flow = None
        st.query_params.clear()
```

### `components/sidebar.py`

Extract everything inside `with st.sidebar:` (lines 121-267) **plus** the file processing block (lines 270-316). This is ~200 lines total.

```python
"""Sidebar — file uploader, GA4 connect, privacy notice, navigation."""

import streamlit as st
import pandas as pd
from utils.data_loader import load_file, validate_columns, get_dataset_stats, assess_data_quality
from utils.ga4_client import get_auth_url, credentials_from_dict, pull_ga4_report
from utils.session import clear_data


def render_sidebar() -> None:
    """Render the full sidebar and handle file processing."""
    with st.sidebar:
        _render_logo()
        st.divider()
        uploaded_file = _render_file_uploader()
        st.divider()
        _render_ga4_connect()
        st.divider()
        _render_privacy_notice()
        _render_clear_button()
        _render_api_counter()
        _render_footer()
        _render_learn_link()

    # Process uploaded file (after sidebar renders so errors show in main area)
    if uploaded_file is not None:
        _process_uploaded_file(uploaded_file)


def _render_logo() -> None: ...

def _render_file_uploader():
    """Returns the file_uploader widget's return value."""
    return st.file_uploader(
        "Upload GA4 Export",
        type=["csv", "xlsx"],
        help="De-identified Google Analytics 4 export file (CSV or XLSX).",
    )


def _render_ga4_connect() -> None:
    """GA4 live connection: sign-in button, property ID, pull data, disconnect."""
    # ... (lines 146-231 of current app.py)


def _render_privacy_notice() -> None:
    """Privacy disclaimer card."""
    # ... (lines 235-244 of current app.py)


def _render_clear_button() -> None:
    """Clear Data button. Only shown when data is loaded."""
    if st.session_state.df is not None:
        # FIX: Replace on_click=clear_data with if st.button pattern (BUGLOG Pattern 2)
        if st.button(
            "🗑️ Clear Data",
            use_container_width=True,
            type="secondary",
        ):
            clear_data()
            st.rerun()


def _render_api_counter() -> None:
    """API call counter (only when calls have been made)."""
    if st.session_state.api_call_count > 0:
        st.caption(f"🔢 API calls this session: {st.session_state.api_call_count}")


def _render_footer() -> None:
    """Sidebar footer."""
    st.divider()
    st.markdown(
        '<div style="font-size:0.72rem;color:#686880;">'
        'Built with ❤️ using Streamlit + Gemini</div>',
        unsafe_allow_html=True,
    )


def _render_learn_link() -> None:
    """Navigation link to Learn page."""
    st.divider()
    st.page_link(
        "pages/learn.py",
        label="📚 Learn Python",
        icon="📚",
        help="Interactive tutorials on Streamlit, Pandas, Plotly, Gemini, and more",
    )


def _process_uploaded_file(uploaded_file) -> None:
    """Parse uploaded file and populate session state.

    Extracted from app.py lines 270-316.
    """
    # ... (existing file processing logic)
```

### `components/hero.py`

Extract `_render_hero()` (lines 533-590). Stateless — reads no widget state.

### `components/data_preview.py`

Extract metrics row, preview table, quality scorecard, **and** data filters (lines 337-367 + 616-668 for scorecard + 471-532 for filters). ~140 lines.

```python
"""Data preview — metrics, preview table, quality scorecard, filters."""

import streamlit as st
from utils.charts import find_date_column
from utils.data_loader import filter_dataframe


def render_data_preview() -> None:
    """Render metrics row, preview table, quality card, and filter expander."""
    # ... metrics row (lines 339-352)
    # ... quality scorecard (lines 358-359)
    # ... filter expander with _render_data_filters()
```

### `components/summary.py`

Extract summary section + `_generate_summary()` callback. ~45 lines.

```python
"""AI Summary section — summary card + generate button."""

import streamlit as st
from typing import Any
import pandas as pd
from utils.prompt_templates import build_summary_prompt
from utils.gemini_client import generate_response


def render_summary_section() -> None:
    """Render the AI-generated summary card and generate button."""
    # ... (lines 361-393 of current app.py)


def _generate_summary(df: pd.DataFrame, stats: dict[str, Any]) -> None:
    """Callback for Generate Summary button."""
    # Match ACTUAL code — include quality_report parameter
    try:
        summary_prompt = build_summary_prompt(
            df, stats,
            quality_report=st.session_state.get("quality_report"),
        )
        st.session_state.summary = generate_response(summary_prompt)
    except ValueError as e:
        st.error(f"🔑 Configuration error: {e}")
    except RuntimeError as e:
        st.error(f"⚠️ API error: {e}")
```

### `components/chat.py`

Extract full chat interface including streaming. ~200 lines. Most complex component.

```python
"""Chat interface — message history, chat input, streaming, chart rendering, export."""

import time
import streamlit as st
import pandas as pd
from typing import Any
from utils.prompt_templates import build_chat_prompt, detect_chart_request
from utils.gemini_client import generate_response_stream
from utils.charts import generate_chart


def render_chat_section() -> None:
    """Render the full chat interface."""
    # Chat header + New Chat button (lines 375-394)
    _render_chat_header()

    # Render all messages (lines 396-424)
    for i, entry in enumerate(st.session_state.chat_history):
        _render_chat_message(entry, i)

    # Chat input (lines 426-440)
    _render_chat_input()

    # Export button (lines 442-465)
    _render_export_button()


def _render_chat_header() -> None:
    """Chat heading + New Chat button."""
    # ... (lines 375-394)


def _render_chat_message(entry: dict[str, Any], i: int) -> None:
    """Render a single chat message. Streams if response is empty."""
    with st.chat_message("user"):
        st.markdown(entry["question"])
    with st.chat_message("assistant"):
        if entry["response"] == "":
            _stream_chat_response(entry, st.session_state.df, i)
        else:
            st.markdown(entry["response"])
            if entry.get("chart") and entry["chart"].get("fig"):
                with st.container(border=True):
                    st.plotly_chart(
                        entry["chart"]["fig"],
                        use_container_width=True,
                        key=f"chart_{i}",
                    )


def _render_chat_input() -> None:
    """Chat input with rate limiting guard."""
    if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
        now = time.time()
        if now - st.session_state.last_api_call < 2.0:
            st.warning("⏳ Please wait a moment between questions...")
            st.stop()
        st.session_state.last_api_call = now
        st.session_state.api_call_count += 1
        st.session_state.chat_history.append({
            "question": prompt, "response": "", "chart": None,
        })
        st.rerun()


def _stream_chat_response(entry: dict[str, Any], df: pd.DataFrame, i: int) -> None:
    """Stream Gemini response and detect chart.

    ⚠️ SIDE EFFECT: Mutates `entry["response"]` and `entry["chart"]` in place
    on `st.session_state.chat_history[-1]` during streaming. After the refactor,
    a follow-up commit should make this function accept parameters and return
    values for full testability.
    """
    # ... (existing code from app.py lines 762-797)


def _render_export_button() -> None:
    """Export button — only when chat has non-empty responses."""
    if any(
        e.get("response") and e["response"] != ""
        for e in st.session_state.chat_history
    ):
        st.divider()
        if st.button("📥 Export Report", use_container_width=True):
            # Lazy import — kaleido may not be installed; error handled below
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

---

## 📐 7-Phase Extraction Plan

Each phase: extract → tests → verify 194 pass → commit. **7 commits total.**

### Phase 1: `utils/charts.py` + `utils/session.py` (Lowest risk)

Extract pure functions with no Streamlit widgets:
- `_generate_chart()` → `utils/charts.py` as `generate_chart()`
- `_find_column()` → `utils/charts.py` as `find_column()`
- `_find_date_column()` → `utils/charts.py` as `find_date_column()`
- `clear_data()` → `utils/session.py` (deduplicated from app.py root and sidebar)

**Imports needed in app.py:** `from utils.charts import generate_chart, find_column, find_date_column`, `from utils.session import clear_data`

**Tests:** `test_charts.py` (~8 tests), `test_session.py` (~3 tests)

### Phase 2: `components/hero.py`

Extract `_render_hero()`. Stateless — static HTML, no widgets.

**Imports needed in app.py:** `from components.hero import render_hero`

**Tests:** `test_hero.py` (~4 tests)

### Phase 3: `components/data_preview.py`

Extract metrics row, preview table, quality scorecard, and data filters.
Reads `st.session_state.stats`, `st.session_state.df`, `st.session_state.quality_report`, `st.session_state.filtered_df`.

**Imports needed in app.py:** `from components.data_preview import render_data_preview`

**Tests:** `test_data_preview.py` (~5 tests)

### Phase 4: `components/summary.py`

Extract summary card + `_generate_summary()` callback. Contains API call via `generate_response()`.

**Imports needed in app.py:** `from components.summary import render_summary_section`

**Tests:** `test_summary.py` (~5 tests)

### Phase 5: `components/chat.py` (Most complex)

Extract full chat interface: history, input, streaming, chart rendering, export. Contains `st.chat_input`, `st.chat_message`, `st.plotly_chart`, `st.write_stream`.

**Imports needed in app.py:** `from components.chat import render_chat_section`

**Tests:** `test_chat.py` (~6 tests)

### Phase 6: `components/sidebar.py` (Largest)

Extract sidebar + file processing (~200 lines). Contains `st.file_uploader`, GA4 OAuth flow, `on_click` → `if st.button` fix.

**Imports needed in app.py:** `from components.sidebar import render_sidebar`

**Tests:** `test_sidebar.py` (~6 tests)

### Phase 7: `components/__init__.py` + Rewrite `app.py`

Tie together. `render_all()` orchestrates order. OAuth callback moves here. `app.py` becomes ~70 lines.

**Tests:** `test_components_init.py` (~5 tests), update `test_app.py` to match new orchestrator.

---

## 🔍 Widget Key Audit

Audit before Phase 1 to prevent collisions. Current keys found in app.py:

| Key | Component | Purpose |
|---|---|---|
| `gen_summary_btn` | summary.py | Generate Summary button |
| `filter_columns` | data_preview.py | Column multiselect |
| `filter_dates` | data_preview.py | Date range picker |
| `ga4_date_range` | sidebar.py | GA4 date range selectbox |

All keys are already unique. No collisions expected across components.

---

## 🧪 Test Impact Summary

Each new component file gets a **5-test pattern** that extends existing CI gates from BUGLOG:

| # | Test | Catches |
|---|---|---|
| 1 | **AST parses cleanly** | Syntax errors introduced during extraction |
| 2 | **Module imports without error** | Undefined names, circular imports, missing dependencies (BUG-002 class) |
| 3 | **Primary render function exists and is callable** | Accidental renames during extraction |
| 4 | **No `on_click` callbacks with slow functions** | Extends BUG-005 CI gate (`test_static_analysis.py`) to new component files |
| 5 | **No `except Exception: pass` without a comment** | Extends BUG-008 audit pattern to new component files |

Tests 4 and 5 are free — `test_static_analysis.py` already has the patterns; just add the new file paths to the scan scope.

| Module | New Tests | Type |
|---|---|---|
| `test_charts.py` | ~8 | Unit: generate_chart, find_column, find_date_column |
| `test_session.py` | ~3 | Unit: clear_data resets all keys |
| `test_hero.py` | ~5 | 5-test pattern |
| `test_data_preview.py` | ~5 | 5-test pattern |
| `test_summary.py` | ~5 | 5-test pattern |
| `test_chat.py` | ~5 | 5-test pattern |
| `test_sidebar.py` | ~5 | 5-test pattern |
| `test_components_init.py` | ~5 | 5-test pattern |
| `test_static_analysis.py` | Updated | Extend BUG-005/BUG-008 scan scope to `components/` directory |
| `test_app.py` | Updated | Match new ~70-line orchestrator |
| **Total new** | **~46** | |

**Post-refactor expected: 194 → ~240 tests.**

All existing tests continue to pass — they test `utils/` modules which are not refactored.

---

## 🔀 Edge Cases

| Issue | Handling |
|---|---|
| `on_click=clear_data` pattern | Replaced with `if st.button` + `st.rerun()` in sidebar.py. Fixes BUGLOG Pattern 2. |
| GA4 disconnect calls clear_data() | Disconnect is in sidebar.py. Import `clear_data` from `utils.session` and call. |
| File processing references uploaded_file | `uploaded_file` returned from `_render_file_uploader()` in sidebar.py. Processing stays in same module. |
| `_stream_chat_response` modifies `entry` in place | Kept as-is. Docstring explicitly documents the side effect for future refactoring. Follow-up commit will make it parameter-accepting for testability. |
| OAuth flow object unpicklable | Stays in `st.session_state` (same as today). Accessed from sidebar.py and __init__.py. |
| Lazy import of report_exporter | Kept lazy inside button callback. Avoids import on every page load. |
| Widget key collisions | All 4 keys audited — no collisions. No new keys added. |

---

## 🚫 Out of Scope

- **`onboarding.py`** — tour doesn't exist yet. Skip entirely.
- **Theme toggle** — separate sprint, runs after this refactor.
- **`_key()` helper** — audit is sufficient. No abstraction layer.
- **`inject_favicon_meta()` in learn.py** — separate concern, not part of this refactor.

---

*Spec derived from 5 interview rounds (2026-07-28), the original [p5-p6/✅ COMPONENT_REFACTOR.md](../p5-p6/✅ COMPONENT_REFACTOR.md), and analysis of the current 809-line app.py.*
