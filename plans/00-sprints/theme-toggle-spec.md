# 🌓 Theme Toggle — Implementation Spec

> **Source plan:** [plans/p3-p4/🔵 THEME_TOGGLE.md](../p3-p4/🔵 THEME_TOGGLE.md)
> **Status:** ✅ Done (4 phases, 231 tests, 2026-07-28)
> **Effort:** 2-3 days (reduced from 3-5 due to component refactor) | **Risk:** Medium
> **Based on:** 3 rounds of user interviews (2026-07-28), component refactor already complete

---

## 🎯 Goal

Add a sidebar toggle that switches between dark mode (current, default) and light mode. Persist in `st.session_state` only (session-scoped). Apply via CSS custom properties already defined in `utils/styles.py` + a small JS snippet for the `data-theme` attribute.

---

## 🏗️ Design Decisions (from 3 interview rounds)

| Decision | Choice | Rationale |
|---|---|---|
| Syntax token colors | **Background only** | Swap code block background + border in light mode. Syntax token colors stay as-is (dark syntax colors on white background are legible — many VS Code light themes do this). Full 15-token syntax override is an **optional Phase 4 polish** if testing shows readability issues. Don't pre-commit to it. |
| Theme default | **Always dark** | Simpler — no JS detection of `prefers-color-scheme`. User toggles manually. |
| Toggle location | **Bottom of sidebar** | After learn link, before Built with ❤️ footer. Grouped logically: `📚 Learn Python → ───── → ☀️ Light Mode → ───── → Built with ❤️`. This is where theme toggles live in every analytics tool (Grafana, Metabase, Notion, Linear). |
| Persistence | **Session only** | `st.session_state.theme` only. Resets to dark on browser refresh. Simplest. |
| Learn page CSS | **Same function + delete standalone CSS** | `pages/learn.py` calls the same `inject_custom_css(theme)` as main app. **Delete the learn page's standalone CSS block** — it currently has its own `st.markdown(css)` call. Replace with a single `inject_custom_css(theme=...)` call. One CSS source of truth. |
| Plotly cache-busting | **Append theme to key** | `key=f"chart_{i}_{theme}"`. When theme changes, old iframes invalidate, new ones render with correct template. |
| Hero gradient | **Darker for light** | Light mode: `#6366f1 → #4f46e5 → #3730a3`. Better contrast on white background. |
| Chart theme passing | **Accept `theme` param** | `generate_chart(df, config, response, question, theme='dark')`. Utilities (`utils/`) should accept params for testability. Components (`components/`) can use `st.session_state` directly — that's the Streamlit-idiomatic boundary established by the component refactor. |
| Scope | **2-3 days** | Component refactor simplified wiring. CSS testing remains the bottleneck. |

---

## 🔑 Key Insight: CSS Variables Already Exist

`utils/styles.py` already defines CSS custom properties in a `:root` block:

```css
:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: #12121a;
    --bg-card: #1a1a26;
    --bg-elevated: #222233;
    --text-primary: #f0f0f5;
    --text-secondary: #9898b0;
    --text-muted: #686880;
    --accent: #6366f1;
    --accent-hover: #818cf8;
    --accent-soft: rgba(99, 102, 241, 0.12);
    --success: #34d399;
    --warning: #fbbf24;
    --danger: #f87171;
    --border: rgba(255, 255, 255, 0.06);
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-xl: 24px;
}
```

The original plan's "Phase 5a: CSS variable extraction" is already done. The CSS is already referencing `var(--bg-primary)`, `var(--accent)`, etc. This spec starts at "Phase 5b: Add light theme variables."

---

## 🗂️ Files Changed (Post-Component-Refactor)

| File | Lines | Change |
|---|---|---|
| `utils/styles.py` | ~240 → ~300 | Add `[data-theme="light"]` block, add `theme` param to `inject_custom_css()`, add JS snippet for `data-theme` attribute |
| `components/sidebar.py` | 247 → ~265 | Add theme toggle button at bottom (after learn link, before footer) |
| `utils/charts.py` | 105 → ~115 | `generate_chart()` accepts `theme` param, uses for template + font color |
| `components/chat.py` | 137 → ~140 | Pass `theme` to chart calls, append to `st.plotly_chart` keys |
| `components/__init__.py` | 80 → ~82 | Pass theme to `inject_custom_css(theme=...)` |
| `app.py` | 78 → ~81 | Initialize `st.session_state.theme = "dark"` |
| `pages/learn.py` | ~300 → ~301 | Call `inject_custom_css(theme=...)` instead of theme-less version |

**Zero new files.** This is a smaller change than any previous sprint.

**One file structurally changed:** The learn page currently has its own standalone CSS block (`st.markdown(css)`). That block is **deleted** and replaced with a single `inject_custom_css(theme=...)` call — the same function the main app uses. The CSS variable architecture (`var(--bg-card)`, `var(--border)`, etc.) means the learn page's concept cards and code blocks get light mode for free once the variables swap.

---

## 📐 Implementation Plan (4 Phases)

### Phase 1: CSS Light Theme + Theme Param (utils/styles.py)

Add the light theme variable overrides and update `inject_custom_css()` to accept a `theme` parameter.

#### 1a: Add `[data-theme="light"]` block

Insert after the existing `:root` block (before `.stApp`):

```css
[data-theme="light"] {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5fa;
    --bg-card: #ffffff;
    --bg-elevated: #f0f0f5;
    --text-primary: #1a1a2e;
    --text-secondary: #686880;
    --text-muted: #9898b0;
    --accent: #4f46e5;
    --accent-hover: #6366f1;
    --accent-soft: rgba(79, 70, 229, 0.08);
    --success: #059669;
    --warning: #d97706;
    --danger: #dc2626;
    --border: rgba(0, 0, 0, 0.08);
}
```

#### 1b: Add light theme h1 gradient override

```css
[data-theme="light"] h1 {
    background: linear-gradient(135deg, #6366f1, #4f46e5, #3730a3);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
```

#### 1c: Light mode button hover fix

The secondary button hover uses a hardcoded `#2a2a3a`:

```css
/* Before */
.stButton > button[kind="secondary"]:hover {
    background: #2a2a3a !important;
}

/* After — use a variable or override per theme */
[data-theme="light"] .stButton > button[kind="secondary"]:hover {
    background: #e0e0eb !important;
}
```

#### 1d: Light mode code block background

```css
[data-theme="light"] .stCode, 
[data-theme="light"] .stCodeBlock {
    background: #f5f5fa !important;
    border-color: rgba(0, 0, 0, 0.08) !important;
}
```

#### 1e: Light mode metric hover shadow

```css
[data-theme="light"] [data-testid="stMetric"]:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
}
```

#### 1f: Light mode chat input focus

```css
[data-theme="light"] [data-testid="stChatInput"] textarea:focus {
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
}
```

#### 1g: Update `inject_custom_css()` signature

```python
def inject_custom_css(theme: str = "dark") -> None:
    """Inject the app's custom CSS theme and keyboard shortcut JS.

    Args:
        theme: "dark" (default) or "light". Sets data-theme on document.
    """
```

At the top of the CSS block, inject a hidden div with the theme:

```python
st.markdown(f'<div id="theme-data" data-theme="{theme}" style="display:none;"></div>', unsafe_allow_html=True)
```

Add a JS snippet that reads the hidden div and sets `data-theme` on the document:

```javascript
<script>
(function() {
    const themeEl = document.getElementById('theme-data');
    if (themeEl) {
        document.documentElement.setAttribute('data-theme', themeEl.dataset.theme);
    }
})();
</script>
```

#### 1h: Learn page `theme-color` meta tag

The `inject_favicon_meta()` hardcodes `<meta name="theme-color" content="#0a0a0f">`. Make it theme-aware:

```python
def inject_favicon_meta(theme: str = "dark") -> None:
    theme_color = "#0a0a0f" if theme == "dark" else "#ffffff"
    # ... use {theme_color} in the meta tag
```

---

### Phase 2: Session State + Toggle Button + Wiring

#### 2a: Session state initialization (`app.py`)

```python
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
```

#### 2b: Pass theme to `inject_custom_css()` (`app.py`)

```python
inject_custom_css(theme=st.session_state.theme)
inject_favicon_meta(theme=st.session_state.theme)
```

#### 2c: Toggle button (`components/sidebar.py`)

Add at the bottom of `render_sidebar()`, right after `_render_learn_link()` and before `_render_footer()`:

```python
def _render_theme_toggle() -> None:
    """Render the theme toggle button at the bottom of the sidebar."""
    current = st.session_state.theme
    new_theme = "light" if current == "dark" else "dark"
    label = "☀️ Light Mode" if current == "dark" else "🌙 Dark Mode"
    
    st.divider()
    if st.button(label, use_container_width=True, key="theme_toggle"):
        st.session_state.theme = new_theme
        st.rerun()
```

Update `render_sidebar()` to call it:

```python
def render_sidebar() -> None:
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
        _render_learn_link()
        _render_theme_toggle()    # ← NEW
        _render_footer()
    
    if uploaded_file is not None:
        _process_uploaded_file(uploaded_file)
```

#### 2d: Pass theme to `inject_custom_css()` in learn page (`pages/learn.py`)

```python
inject_custom_css(theme=st.session_state.get("theme", "dark"))
inject_favicon_meta(theme=st.session_state.get("theme", "dark"))
```

---

### Phase 3: Plotly Charts + Chart Theme Param

#### 3a: Update `generate_chart()` to accept theme (`utils/charts.py`)

```python
def generate_chart(
    df: pd.DataFrame,
    chart_config: dict[str, str],
    gemini_response: str,
    user_question: str,
    theme: str = "dark",
) -> dict[str, Any] | None:
    """Generate a Plotly chart. Uses theme-aware template and font colors."""
    template = "plotly_dark" if theme == "dark" else "plotly_light"
    font_color = "#9898b0" if theme == "dark" else "#4b5563"
    
    # ... use template=template, font=dict(color=font_color) throughout
```

Update all `template="plotly_dark"` → `template=template` and all `font=dict(color="#9898b0", ...)` → `font=dict(color=font_color, ...)`.

#### 3b: Pass theme from chat (`components/chat.py`)

```python
def render_chat_section() -> None:
    theme = st.session_state.get("theme", "dark")
    # ... pass theme to chart keys and generate_chart calls
```

Update `_stream_chat_response()`:

```python
def _stream_chat_response(entry, df, i):
    theme = st.session_state.get("theme", "dark")
    # ...
    chart_data = generate_chart(df, chart_config, full_text, entry["question"], theme=theme)
    # ...
    st.plotly_chart(
        chart_data["fig"],
        use_container_width=True,
        key=f"chart_{i}_{theme}",  # ← theme-tagged key for cache-busting
    )
```

Also update historical chart rendering:

```python
# In _render_chat_message loop:
st.plotly_chart(
    entry["chart"]["fig"],
    use_container_width=True,
    key=f"chart_{i}_{st.session_state.get('theme', 'dark')}",
)
```

---

### Phase 4: Polish + Edge Cases

| Edge Case | Handling |
|---|---|
| **Theme flash on load** | The JS snippet runs inline (no defer). It reads the hidden `#theme-data` div and sets `data-theme` before the first CSS paint. |
| **Plotly theme mismatch** | Cache-busted keys (`chart_0_dark` vs `chart_0_light`) ensure each theme gets its own Plotly iframe. Old ones are garbage-collected by Streamlit. |
| **Learn page theme** | `st.session_state.theme` is shared across pages. Toggling on main page persists when navigating to learn page (and vice versa). |
| **Streamlit's own theme** | We're not using Streamlit's built-in `[theme]` config. Our CSS is injected via `st.markdown(unsafe_allow_html=True)` after Streamlit's CSS, so our rules take precedence. |
| **Alert boxes in light mode** | The `rgba()` backgrounds for info/warning/error use the accent color with low opacity — these work in both themes with the variable swap. No additional overrides needed. |
| **Mobile sidebar** | Sidebar collapses on mobile (hamburger menu). Users can still access the toggle via the hamburger. No special handling needed. |
| **GA4 redirect** | `st.stop()` during OAuth redirect short-circuits CSS injection for that one render — same behavior as today. On rerun after callback, theme applies normally. |

---

## 🧪 Test Impact

| Module | Change | Tests |
|---|---|---|
| `test_charts.py` | Updated | Add `theme` param to `generate_chart` calls. Verify dark/light template/font swapping. ~3 tests. |
| `test_sidebar.py` | Updated | Verify `_render_theme_toggle()` function exists. ~1 test. |
| All other tests | Unchanged | Component structure and test patterns already validated by refactor. |

**Post-theme expected: 228 → ~231 tests.**

---

## 📊 What Stays the Same

- All `utils/` modules except `styles.py` and `charts.py` — no changes
- `components/hero.py` — gradient handled via CSS, no Python changes
- `components/data_preview.py` — no changes (all styling via CSS variables)
- `components/summary.py` — no changes
- All test files except `test_charts.py` and `test_sidebar.py` — no changes

---

## 🚫 Out of Scope

- **OS/browser theme detection** — always defaults to dark (per interview round 1)
- **localStorage persistence** — session-only (per interview round 2)
- **Full syntax token light theme** — background/border only, syntax colors stay. Full 15-token override is an optional Phase 4 polish if readability testing shows it's needed (per interview round 1).
- **Streamlit native theme system** — sticking with custom CSS injection
- **Per-component theme awareness** — only charts, CSS, and sidebar button need explicit theme handling

---

*Spec derived from 3 interview rounds (2026-07-28), the original [p3-p4/🔵 THEME_TOGGLE.md](../p3-p4/🔵 THEME_TOGGLE.md), the post-refactor component structure, and analysis of `utils/styles.py` (already has CSS variables).*
