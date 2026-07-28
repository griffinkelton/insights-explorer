# 🧩 Component Refactor — Phase 5 Implementation Plan

> **Roadmap ref:** IMPLEMENTATION_PLAN.md #20, ENHANCEMENTS.md #12
> **Effort:** High (3-5 days) | **Risk:** Medium (mechanical extraction, session state coupling)
> **Status:** ✅ Done (7 phases, 78-line orchestrator, 228 tests, 2026-07-28)

---

## 🎯 Goal

Split `app.py` (~400 lines) into a `components/` package with 6 focused modules. `app.py` becomes a thin orchestrator — page config, session state, and a single `components.render_all()` call. Every section of the UI gets its own file with its own tests.

---

## 🧠 Why Refactor Now

`app.py` has grown organically to ~500 lines. It now contains:

- Page config & CSS injection (lines 1-30)
- 14 session state key initializations (lines 41-59)
- API key validation banner (lines 62-72)
- OAuth callback handler (lines 76-90)
- `clear_data()` function (lines 93-101)
- Sidebar: logo, file uploader, GA4 connect, privacy notice, clear button (lines 104-200)
- File processing block (lines 203-240)
- `_render_main()`: header, hero, data preview, summary, chat (lines 245-328)
- `_render_hero()`: empty state cards (lines 331-375)
- Error boundary wrapper (lines 378-384)
- `_generate_summary()` callback (lines 387-395)
- `_generate_chart()` + `_find_column()` + `_find_date_column()` helpers (lines 398-480)
- Footer (lines 483-492)

None of these are individually complex. The problem is that they're all in one file, making it hard to:
- Find where a specific piece of UI lives
- Test individual sections in isolation
- Onboard new contributors
- Avoid merge conflicts when multiple features touch different sections

The refactor is mechanical — extract each section into a function in its own module. No behavior changes.

---

## 🏗️ Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Session state location | **All in `app.py` orchestrator** | Single source of truth for what state exists. Components read/write `st.session_state` directly. |
| State passing | **Direct `st.session_state` access** | Passing to every component creates verbose signatures that drift. Streamlit-idiomatic approach. |
| Callback functions | **Move to components, update references** | `on_click=clear_data` stays as reference; source function moves to relevant component. |
| Widget keys | **No changes; audit for collisions** | Existing keys already unique; new components get new keys. |
| `st.rerun()` / `st.stop()` | **No special handling** | Works identically regardless of which module calls it. |
| Extraction order | **Charts first, orchestrator last** | Lowest-risk → highest-risk. Each phase verified independently before next. |
| File processing | **Moves to `components/sidebar.py`** | `_process_uploaded_file()` is called at the bottom of `render_sidebar()`. Keeps the upload lifecycle contained in one module. |
| Mini-spec source | **Design decisions from component-refactor mini-spec** | Merged into this detailed plan to eliminate duplication. |

---

## 🗂️ Target Structure

### Before

```
app.py  (~400 lines)
```

### After

```
app.py  (~60 lines)                  # Page config, session state, orchestrator
components/
├── __init__.py      (~30 lines)     # render_all() — calls all components in order
├── sidebar.py       (~120 lines)    # Logo, uploader, GA4 connect, privacy, clear, nav
├── hero.py          (~60 lines)     # Empty state with feature cards + tour
├── data_preview.py  (~60 lines)     # Metrics row, preview table, filters
├── summary.py       (~50 lines)     # AI summary card + generate button
├── chat.py          (~120 lines)    # Chat history, chat input, export button
└── onboarding.py    (~80 lines)     # 3-step guided tour (if implemented)

utils/
├── charts.py        (~80 lines)     # _generate_chart(), _find_column(), _find_date_column()
├── ... (existing files unchanged)
```

### `app.py` — The Orchestrator

```python
"""GA4 Insight Explorer — Streamlit web app for analyzing GA4 export data with Gemini."""

import streamlit as st
from utils.styles import inject_custom_css
from utils.gemini_client import validate_api_key
from components import render_all


# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GA4 Insight Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────
inject_custom_css()

# ── Session state initialization ─────────────────────────────────────────
_defaults = {
    "df": None, "stats": None, "summary": None, "chat_history": [],
    "missing_columns": [], "data_cleared": False, "last_file_id": None,
    "ga4_creds": None, "ga4_property_id": "", "ga4_auth_flow": None,
    "data_source": None, "api_key_valid": None, "api_key_error": "",
    "last_api_call": 0.0, "api_call_count": 0,
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


# ── Render all UI (components handle their own logic) ─────────────────────
render_all()
```

**Design decision — session state in orchestrator:** All 14 session state keys are initialized in `app.py`, not scattered across components. This gives a single source of truth for what state exists. Components read/write `st.session_state` directly (Streamlit-idiomatic approach).

**Why not pass state as parameters:** Passing `st.session_state.df`, `st.session_state.stats`, etc. to every component function creates verbose signatures that change whenever state changes. Direct `st.session_state` access is simpler, more Streamlit-native, and avoids parameter-drift bugs.

### `components/__init__.py` — The Render Order

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
    """Render all UI sections in order. Wrapped in error boundary."""

    # Handle OAuth callback (must happen before any rendering)
    _handle_oauth_callback()

    # Sidebar (always rendered)
    render_sidebar()

    # Main content (with error boundary)
    try:
        _render_main_content()
    except Exception as e:
        if e.__class__.__module__.startswith("streamlit"):
            raise
        render_error_card(e, context="rendering the page")


def _render_main_content() -> None:
    """Main content area — hero, data preview, summary, chat."""

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
    """Handle Google OAuth redirect (code= param in URL)."""
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

### `components/sidebar.py` — Sidebar UI

Extract everything currently inside `with st.sidebar:` in `app.py` (lines 104-200):

```python
"""Sidebar — file uploader, GA4 connect, privacy notice, navigation."""

import streamlit as st
from utils.data_loader import load_file, validate_columns, get_dataset_stats
from utils.ga4_client import get_auth_url, credentials_from_dict, pull_ga4_report


def render_sidebar() -> None:
    """Render the full sidebar."""

    with st.sidebar:
        _render_logo()
        st.divider()
        uploaded_file = _render_file_uploader()
        st.divider()
        _render_ga4_connect()
        st.divider()
        _render_privacy_notice()
        _render_clear_button()
        _render_learn_link()
        _render_footer()

        # Process uploaded file (side effect)
        if uploaded_file is not None:
            _process_uploaded_file(uploaded_file)


def _render_logo() -> None:
    """Render the app logo and tagline."""
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
        <div style="width:38px;height:38px;border-radius:12px;
                    background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    display:flex;align-items:center;justify-content:center;
                    font-size:1.2rem;">📊</div>
        <div>
            <div style="font-weight:700;font-size:1.1rem;color:#f0f0f5;line-height:1.3;">
                Insight Explorer
            </div>
            <div style="font-size:0.75rem;color:#9898b0;">GA4 Analytics + AI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_file_uploader():
    """Render file uploader widget. Returns the uploaded file object."""
    return st.file_uploader(
        "Upload GA4 Export",
        type=["csv", "xlsx"],
        help="De-identified Google Analytics 4 export file (CSV or XLSX).",
    )


def _render_ga4_connect() -> None:
    """Render the GA4 live connection section (OAuth + property ID + pull)."""
    # ... (extract the GA4 connect block from app.py)


def _render_privacy_notice() -> None:
    """Render the privacy disclaimer card."""
    # ...


def _render_clear_button() -> None:
    """Render the Clear Data button (only when data is loaded)."""
    if st.session_state.df is not None:
        if st.button("🗑️ Clear Data", use_container_width=True, type="secondary"):
            _clear_data()
            st.rerun()


def _render_learn_link() -> None:
    """Render navigation link to the Learn page."""
    st.divider()
    st.page_link(
        "pages/learn.py",
        label="📚 Learn Python",
        icon="📚",
        help="Interactive tutorials on Streamlit, Pandas, Plotly, Gemini, and more",
    )


def _render_footer() -> None:
    """Render sidebar footer."""
    st.markdown(
        '<div style="font-size:0.72rem;color:#686880;">'
        'Built with ❤️ using Streamlit + Gemini</div>',
        unsafe_allow_html=True,
    )


def _clear_data() -> None:
    """Wipe all session state and uploaded file from memory."""
    st.session_state.df = None
    st.session_state.stats = None
    st.session_state.summary = None
    st.session_state.chat_history = []
    st.session_state.missing_columns = []
    st.session_state.data_cleared = True
    st.session_state.data_source = None


def _process_uploaded_file(uploaded_file) -> None:
    """Parse the uploaded file and populate session state."""
    # ... (extract the file processing block from app.py)
```

### `components/hero.py` — Empty State

Extract `_render_hero()` from `app.py` (lines 331-375):

```python
"""Hero / empty state — shown when no data is loaded."""

import streamlit as st


def render_hero() -> None:
    """Render the hero section with feature cards."""
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        # ... (existing hero HTML — gradient title, feature cards)

    st.divider()
    st.markdown(
        '<p style="text-align:center;color:#686880;font-size:0.85rem;">'
        '📂 Upload a file in the sidebar to get started</p>',
        unsafe_allow_html=True,
    )
```

### `components/data_preview.py` — Metrics & Preview

Extract the metrics row + expander from `_render_main()`:

```python
"""Data preview — metrics row, preview table, optional filters."""

import streamlit as st


def render_data_preview() -> None:
    """Render the 4-column metrics row and preview table expander."""
    stats = st.session_state.stats
    if stats is None:
        return

    st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Total Rows", f"{stats['row_count']:,}")
    with col2:
        st.metric("📊 Columns", stats["column_count"])
    with col3:
        st.metric("📅 From", stats.get("date_range_start", "—"))
    with col4:
        st.metric("📅 To", stats.get("date_range_end", "—"))

    with st.expander("🔍 Preview Table (first 10 rows)", expanded=False):
        df = st.session_state.df
        st.dataframe(df.head(10), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
```

### `components/summary.py` — AI Summary Card

Extract the summary section + generate button from `_render_main()`:

```python
"""AI Summary section — summary card + generate button."""

import streamlit as st
import pandas as pd
from typing import Any
from utils.prompt_templates import build_summary_prompt
from utils.gemini_client import generate_response


def render_summary_section() -> None:
    """Render the AI-generated summary card and generate button."""
    st.markdown("### 🤖 AI-Generated Summary")

    summary_col1, summary_col2 = st.columns([3, 1])
    with summary_col1:
        if st.session_state.summary:
            with st.container(border=True):
                st.markdown(st.session_state.summary)
        else:
            st.info("Click **Generate Summary** to analyze your dataset with AI.")

    with summary_col2:
        if st.button("✨ Generate Summary", type="primary", use_container_width=True):
            _handle_generate_summary()


def _handle_generate_summary() -> None:
    """Callback for the Generate Summary button."""
    df = st.session_state.df
    stats = st.session_state.stats

    with st.spinner("🤖 Analyzing your dataset with Gemini..."):
        try:
            summary_prompt = build_summary_prompt(df, stats)
            st.session_state.summary = generate_response(summary_prompt)
        except ValueError as e:
            st.error(f"🔑 Configuration error: {e}")
        except RuntimeError as e:
            st.error(f"⚠️ API error: {e}")
    st.rerun()
```

### `components/chat.py` — Chat Interface

Extract the chat section from `_render_main()`:

```python
"""Chat interface — message history, chat input, export button."""

import streamlit as st
import pandas as pd
from utils.prompt_templates import build_chat_prompt, detect_chart_request
from utils.gemini_client import generate_response


def render_chat_section() -> None:
    """Render the full chat interface."""
    st.markdown(
        '<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;">'
        '<h3 style="margin:0;">💬 Ask Questions</h3>'
        '<span class="kb-shortcut">⌘K</span> '
        '<span style="color:#686880;font-size:0.7rem;">focus chat</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    _render_chat_history()
    _render_chat_input()
    _render_export_button()


def _render_chat_history() -> None:
    """Render past Q&A messages."""
    for i, entry in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.markdown(entry["question"])
        with st.chat_message("assistant"):
            if entry.get("response"):
                st.markdown(entry["response"])
            if entry.get("chart") and entry["chart"].get("fig"):
                with st.container(border=True):
                    st.plotly_chart(
                        entry["chart"]["fig"],
                        use_container_width=True,
                        key=f"chart_{i}",
                    )


def _render_chat_input() -> None:
    """Render chat input and handle new messages."""
    if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
        st.session_state.chat_history.append(
            {"question": prompt, "response": None, "chart": None}
        )
        _process_chat_message(st.session_state.chat_history[-1])
        st.rerun()


def _process_chat_message(entry: dict) -> None:
    """Send a chat message to Gemini and store the response."""
    df = st.session_state.df
    stats = st.session_state.stats

    with st.spinner("Thinking..."):
        try:
            chat_prompt = build_chat_prompt(entry["question"], df, stats)
            response = generate_response(chat_prompt)

            chart_config = detect_chart_request(response)
            chart_data = None
            if chart_config:
                chart_data = _generate_chart(df, chart_config, response, entry["question"])

            entry["response"] = response
            entry["chart"] = chart_data

        except ValueError as e:
            entry["response"] = f"🔑 Configuration error: {e}"
        except RuntimeError as e:
            entry["response"] = f"⚠️ API error: {e}"


def _render_export_button() -> None:
    """Render export button (when chat history is non-empty)."""
    # ...
```

### `utils/charts.py` — Chart Helpers

Extract from `app.py`:

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
    """Generate a Plotly chart based on detected chart config.
    
    Returns {"fig": go.Figure, "type": "line"|"bar"} or None.
    """
    # ... (existing _generate_chart logic from app.py)


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find a column matching one of the candidate names (case-insensitive)."""
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        if candidate in df_cols_lower:
            return df_cols_lower[candidate]
    return None


def find_date_column(df: pd.DataFrame) -> str | None:
    """Find the best date column in the DataFrame."""
    date_candidates = ["date", "day", "date_time", "timestamp"]
    col = find_column(df, date_candidates)
    if col:
        return col
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None
```

---

## 🔍 Edge Cases & Gotchas

| Issue | Handling |
|---|---|
| **Widget key collisions** | Each component uses unique `key=` values. Audit all existing keys before extraction. Add a `_key(prefix)` helper that generates {component}_{id} keys to prevent collisions. |
| **`st.rerun()` scope** | `st.rerun()` works the same regardless of which module calls it. No special handling needed. |
| **`st.stop()` scope** | Same — `st.stop()` stops execution of the current script run, regardless of which module calls it. |
| **Import ordering** | `from utils.charts import find_date_column` in `components/data_preview.py` — all imports must work. The `components/` package has no circular deps since it imports from `utils/` and `st`, never from `app.py`. |
| **Callback functions** | The `on_click=_clear_data` pattern uses function references. When the function moves to a different module, the reference must be updated. Example: `on_click=sidebar._clear_data` → import and call directly, or keep callbacks as local functions. |
| **Session state key changes** | All 14 keys remain unchanged. Components access them directly via `st.session_state`. |
| **OAuth flow** | The flow object (`st.session_state.ga4_auth_flow`) is a `Flow` instance that can't be pickled. It stays in session state, accessed from `components/sidebar.py` and the OAuth callback handler in `__init__.py`. |

---

## 🧪 Test Impact

- **New structural tests for each component:** `test_sidebar.py`, `test_hero.py`, `test_data_preview.py`, `test_summary.py`, `test_chat.py` — AST parsing, import checks, section existence. ~25 new tests total.
- **New test for `utils/charts.py`:** `test_charts.py` — verifies `generate_chart`, `find_column`, `find_date_column`. ~8 tests.
- **Update `test_app.py`:** The existing structural test for `app.py` must be updated to match the new ~60-line orchestrator. Verify imports, session state init, `render_all()` call.
- **All existing tests continue to pass** — they test `utils/` modules, which are not being refactored.

---

## 📐 Implementation Order

1. **Phase 5a (charts.py):** Extract `_generate_chart`, `_find_column`, `_find_date_column` to `utils/charts.py`. This is the lowest-risk extraction — pure functions with no Streamlit widgets. Write tests. Verify all existing tests pass. Commit.
2. **Phase 5b (hero.py):** Extract `_render_hero()`. Stateless — reads no widget state, renders static HTML. Commit.
3. **Phase 5c (data_preview.py):** Extract metrics row + preview table. Reads `st.session_state.stats` and `st.session_state.df`. Commit.
4. **Phase 5d (summary.py):** Extract summary card + generate button. Contains the API call logic. Commit.
5. **Phase 5e (chat.py):** Extract chat interface. Most complex component — chat history, chat input, chart rendering, export button. Commit.
6. **Phase 5f (sidebar.py):** Extract the entire sidebar. Last and largest extraction. Contains file uploader, GA4 connect, OAuth flow. Commit.
7. **Phase 5g (orchestrator):** Rewrite `app.py` as the thin orchestrator. `components/__init__.py` ties it all together. Final commit.

---

## 💭 Why This Matters

This is an investment in development velocity. After the refactor:
- Adding a new sidebar widget touches `components/sidebar.py` (~120 lines), not `app.py` (~400 lines)
- Testing a component in isolation means parsing ~60 lines of AST, not ~400
- Two developers can work on `chat.py` and `summary.py` simultaneously without merge conflicts
- The component structure is self-documenting — the file tree _is_ the UI structure

The refactor adds zero user-facing features. But every feature after this point takes half the time to implement.

---

*Plan created from review of `app.py` (~400 lines), `utils/` directory structure, and Streamlit's multi-module component patterns.*
