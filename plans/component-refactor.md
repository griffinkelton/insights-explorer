# 🧩 Component Refactor — Mini-Spec

> **What:** Split `app.py` (~500 lines) into a thin orchestrator + 6 focused component modules. Addresses the "single-file orchestration" weakness from the repo assessment.
> **Status:** 🔵 Deferred — awaiting P4 Wave 1 + Streaming + Theme Toggle completion before execution.
> **Effort:** 3–5 days | **Risk:** Medium (mechanical extraction, session state coupling)
> **Files:** New `components/` package (6 files), new `utils/charts.py`, rewritten `app.py` (~60 lines)
> **Depends on:** P4 Wave 1 (#15–17, #19) + Theme Toggle (#18) must be stable first.
> **Referenced by:** [P4-deferred-plan.md](P4-deferred-plan.md) (Batch D), [P4-future-plan.md](P4-future-plan.md) (Wave 2b)
> **Detailed plan:** [phase5/COMPONENT_REFACTOR.md](phase5/COMPONENT_REFACTOR.md) — full 7-phase extraction guide with code samples.

---

## 🧭 Why This Exists

`app.py` has grown organically to ~500 lines. It now contains:

| Section | Lines | What |
|---|---|---|
| Page config & CSS | 1–37 | `set_page_config`, `inject_custom_css`, `inject_favicon_meta` |
| Session state init | 40–72 | 14 keys (`df`, `stats`, `summary`, `chat_history`, etc.) |
| API key validation | 75–84 | Startup check + persistent error banner |
| OAuth callback | 87–100 | Google redirect handler (`?code=...`) |
| `clear_data()` | 103–112 | State reset function |
| Sidebar | 115–218 | Logo, uploader, GA4 connect, privacy, clear, API counter, footer, nav |
| File processing | 221–270 | Parse uploaded file, validate, store state |
| `_render_main()` | 275–370 | Header, hero/data-preview/metrics, quality card, summary, chat |
| `_render_hero()` | 373–418 | Empty state with feature cards |
| `_render_quality_scorecard()` | 421–465 | A-F grade card |
| `_render_main()` error boundary | 468–473 | Global try/except |
| `_generate_summary()` | 476–485 | Summary callback |
| `_generate_chart()` + helpers | 488–545 | Chart generation + `_find_column` + `_find_date_column` |
| Footer | 548–556 | Bottom bar with links |

None of these are individually complex. The problem is they're all in one file, making it hard to find specific UI, test sections in isolation, or avoid merge conflicts.

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
| File processing | **Stays in `app.py` orchestrator** | Touches file upload widget state; tightly coupled to uploader in sidebar. Simplest to keep inline. |

---

## 📐 Target Architecture

### Before

```
app.py  (~500 lines)
```

### After

```
app.py  (~60 lines)                  # Page config, session state, error boundary → components.render_all()
components/
├── __init__.py      (~30 lines)     # render_all() — calls all components in order
├── sidebar.py       (~140 lines)    # Logo, uploader, GA4 connect, privacy, clear, API counter, footer, nav
├── hero.py          (~60 lines)     # Empty state with feature cards
├── data_preview.py  (~80 lines)     # Metrics row, preview table, quality scorecard
├── summary.py       (~50 lines)     # AI summary card + generate button
└── chat.py          (~140 lines)    # Chat history, chat input, rate limiting, chart rendering
utils/
└── charts.py        (~80 lines)     # _generate_chart(), _find_column(), _find_date_column()
```

### What Stays in `app.py`

```python
"""GA4 Insight Explorer — Streamlit web app for analyzing GA4 export data with Gemini."""

import streamlit as st
from utils.styles import inject_custom_css, inject_favicon_meta
from utils.gemini_client import validate_api_key
from components import render_all

# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(...)

# ── Custom CSS, JS & favicon ─────────────────────────────────────────────
inject_custom_css()
inject_favicon_meta()

# ── Session state initialization (all 14 keys) ──────────────────────────
_defaults = { "df": None, "stats": None, ... }
for key, default in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── API key validation ───────────────────────────────────────────────────
if st.session_state.api_key_valid is None:
    is_valid, msg = validate_api_key()
    ...

if not st.session_state.api_key_valid:
    st.error(...)

# ── Render all UI ────────────────────────────────────────────────────────
render_all()
```

### What Moves Where

| From `app.py` | To | Lines |
|---|---|---|
| `_generate_chart()`, `_find_column()`, `_find_date_column()` | `utils/charts.py` | ~80 |
| `_render_hero()` | `components/hero.py` | ~60 |
| Metrics row, preview table, quality card | `components/data_preview.py` | ~80 |
| Summary card + `_generate_summary()` | `components/summary.py` | ~50 |
| Chat history, chat input, rate limiting | `components/chat.py` | ~140 |
| Sidebar (logo, uploader, GA4, privacy, clear, counter, footer, nav) | `components/sidebar.py` | ~140 |
| OAuth callback + error boundary + `_render_main()` | `components/__init__.py` | ~50 |
| File processing block | **Stays in `app.py`** | ~50 |

---

## 📋 7-Phase Extraction Plan

Each phase: extract one section → verify 194 tests pass → commit. No behavior changes.

### Phase 1: `utils/charts.py` (Lowest Risk)

Extract `_generate_chart()`, `_find_column()`, `_find_date_column()`. Pure functions with no Streamlit widgets — lowest risk.

```python
# utils/charts.py
from typing import Any
import pandas as pd
import plotly.express as px

def generate_chart(df, chart_config, gemini_response, user_question) -> dict[str, Any] | None: ...
def find_column(df, candidates) -> str | None: ...
def find_date_column(df) -> str | None: ...
```

Update `app.py` to import from `utils.charts` instead of defining locally.

### Phase 2: `components/hero.py`

Extract `_render_hero()`. Stateless — reads no widget state, renders static HTML.

### Phase 3: `components/data_preview.py`

Extract metrics row + preview table + quality scorecard. Reads `st.session_state.stats`, `st.session_state.df`, `st.session_state.quality_report`.

### Phase 4: `components/summary.py`

Extract summary card + `_generate_summary()`. Contains the API call logic — the first component with side effects.

### Phase 5: `components/chat.py`

Extract full chat interface. Most complex component: chat history, chat input, rate limiting guard, chart rendering. Contains `st.chat_input`, `st.chat_message`, `st.plotly_chart`.

### Phase 6: `components/sidebar.py`

Extract the entire sidebar. Largest extraction: logo, file uploader, GA4 connect (OAuth flow), privacy notice, clear button, API counter, footer, learn link.

### Phase 7: `components/__init__.py` + Rewrite `app.py`

Tie it all together. `render_all()` orchestrates component order. `app.py` becomes the thin ~60-line orchestrator.

---

## 🔀 Edge Cases & Gotchas

| Issue | Handling |
|---|---|
| **Widget key collisions** | All existing keys already unique. New components use descriptive prefixes (`sidebar_`, `chat_`, `preview_`). Audit with `grep -n "key="` before extraction. |
| **`st.rerun()` scope** | Works identically from any module. No special handling. |
| **`st.stop()` scope** | Same — stops current script run regardless of calling module. |
| **Callback function references** | `on_click=clear_data` — `clear_data()` stays in `app.py`. All existing callbacks valid. |
| **OAuth flow object** | `st.session_state.ga4_auth_flow` is a `Flow` instance (unpicklable). Stays in session state, accessed from `components/sidebar.py` and `components/__init__.py`. |
| **File processing block** | Stays in `app.py` because it references `uploaded_file` (sidebar widget). Simplest to keep inline than to pass as parameter. |
| **Import ordering** | `components/` imports from `utils/` only, never from `app.py`. No circular dependencies. |
| **Existing test imports** | `test_app.py` checks `app.py` AST. Must update after Phase 7 to match new ~60-line orchestrator. |

---

## 🧪 Test Impact

| Module | New Tests | What |
|---|---|---|
| `tests/test_charts.py` | ~8 | `generate_chart()`, `find_column()`, `find_date_column()` |
| `tests/test_hero.py` | ~3 | AST check: import, function exists, function called from `render_all` |
| `tests/test_data_preview.py` | ~3 | AST check: import, function exists, renders metrics + preview |
| `tests/test_summary.py` | ~4 | AST check + callback logic + error handling |
| `tests/test_chat.py` | ~5 | AST check + chat input + rate limiting path + chart rendering |
| `tests/test_sidebar.py` | ~5 | AST check + uploader + GA4 connect paths |
| `tests/test_components_init.py` | ~4 | `render_all()` imports, call order, OAuth callback, error boundary |
| `tests/test_app.py` | Update | Match new ~60-line orchestrator: imports, session state init, `render_all()` call |

**Test growth: 194 → ~226 (+32 tests).**

All existing 194 tests continue to pass — they test `utils/` modules which are not being refactored.

---

## ⚠️ Critical Ordering

This refactor must run **after** these features are stable:

```
✅ P1–P3 sprint (done)
🔵 P4 Wave 1: #15 Column picker, #16 Conversation memory, #17 Export
🔵 P4 Wave 1: #19 Streaming responses
🔲 Theme Toggle (#18)                        ← Must be stable first
🔲 Component Refactor (#20)                   ← THIS — runs LAST
```

From the analysis: *"Refactoring while streaming and theming are still changing means every feature change requires updating both the original code AND the extracted component."*

The right trigger: streaming is shipped and stable, theming is shipped and stable, then look at the final `app.py` and extract from that.

---

## 💭 Why This Matters

This is an investment in development velocity. After the refactor:

- Adding a sidebar widget touches `components/sidebar.py` (~140 lines), not `app.py` (~500 lines)
- Testing a component means parsing ~60–140 lines of AST per module, not ~500
- Two developers can work on `chat.py` and `summary.py` simultaneously without merge conflicts
- The file tree _is_ the UI structure — self-documenting architecture
- Directly addresses the repo assessment's top weakness: "Single-file orchestration"

The refactor adds zero user-facing features. But every feature after this point takes half the time to implement.

---

## 📖 Related Docs

- [phase5/COMPONENT_REFACTOR.md](phase5/COMPONENT_REFACTOR.md) — Full implementation guide with code samples for all 7 phases
- [P4-deferred-plan.md](P4-deferred-plan.md) — This is Batch D in the deferred plan
- [P4-future-plan.md](P4-future-plan.md) — Original future-phase plan (Wave 2b)
- [P4-wave1-streaming-sprint-spec.md](P4-wave1-streaming-sprint-spec.md) — Current sprint (must complete first)
- [onboarding-tour.md](onboarding-tour.md) — Same mini-spec pattern for #8
- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — Original item #20
