# 🌓 Light/Dark Theme Toggle — Phase 5 Implementation Plan

> **Roadmap ref:** IMPLEMENTATION_PLAN.md #18, ENHANCEMENTS.md #6
> **Effort:** High (3-5 days) | **Risk:** High (many CSS overrides to test)
> **Status:** 🔲 Planned — no code written

---

## 🎯 Goal

Add a sidebar toggle that switches between dark mode (current) and light mode. Persist the preference in `st.session_state` and apply it via CSS custom properties + a small JS snippet.

---

## 🧠 Why This Is Hard

Streamlit's dark theme is deeply embedded. Every component — sidebar, buttons, metrics, expanders, dataframes, chat, alerts, file uploader, spinners — has dark-mode-specific styling injected by Streamlit's runtime. We're already overriding many of these in `utils/styles.py` with `!important` rules targeting `data-testid` attributes. Adding a light mode means duplicating all those overrides with inverted colors, scoped to a `[data-theme="light"]` selector.

Compounding factors:
- Streamlit ships its own CSS after ours, so our overrides need high specificity
- Plotly charts have their own `template="plotly_dark"` — must swap to `template="plotly_light"` at render time
- The syntax-highlighted code blocks in the `/learn` page have hardcoded dark backgrounds that need light-mode variants
- `st.chat_message` bubbles have Streamlit-default styling that differs between themes

---

## 🗂️ Files & Changes

### 1. `utils/styles.py` — CSS Architecture Refactor

**Current state:** ~200 lines of dark-only CSS in a single `st.markdown(unsafe_allow_html=True)` call.

**Target state:** CSS custom properties (variables) scoped to `[data-theme]`, plus a theme-aware injection function.

#### Step 1: Extract color values into CSS custom properties

Move all hardcoded color values into a `:root, [data-theme="dark"]` block:

```css
:root, [data-theme="dark"] {
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
    --border-light: rgba(255, 255, 255, 0.12);
    --shadow: rgba(0, 0, 0, 0.3);
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-xl: 24px;
}
```

Then reference these variables everywhere instead of hardcoded colors. For example:
```css
/* Before */
.stApp { background: #0a0a0f; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #6366f1, #8b5cf6); }

/* After */
.stApp { background: var(--bg-primary); }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, var(--accent), #8b5cf6); }
```

#### Step 2: Add light theme variable overrides

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
    --border-light: rgba(0, 0, 0, 0.14);
    --shadow: rgba(0, 0, 0, 0.06);
}
```

**Approach to picking light theme colors:** Take each dark variable, convert to HSL, flip the lightness (swap ~5-10% with ~90-95%), adjust saturation. The accent stays similar (it's brand color). Success/warning/danger get slightly darker variants for better contrast on white.

#### Step 3: JS snippet for theme sync

Add a small script that initializes the `data-theme` attribute from `st.session_state`:

```html
<script>
(function() {
    // Read theme from Streamlit session state (set via st.markdown injection)
    const theme = window.parent.document.querySelector('[data-testid="stMarkdownContainer"]')
        ?.getAttribute('data-streamlit-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', theme);
})();
</script>
```

Actually, a cleaner approach: inject the theme into a hidden div from Python, then read it in JS:

```python
# In inject_custom_css(theme: str = "dark"):
st.markdown(f'<div id="theme-data" data-theme="{theme}" style="display:none;"></div>', unsafe_allow_html=True)
```

```javascript
const themeEl = document.getElementById('theme-data');
if (themeEl) {
    document.documentElement.setAttribute('data-theme', themeEl.dataset.theme);
}
```

#### Step 4: Theme-aware gradient for the h1 title

The h1 gradient uses hardcoded colors:
```css
h1 {
    background: linear-gradient(135deg, #c4b5fd, #818cf8, #6366f1);
}
```

In light mode, these purple shades are too bright. Use CSS custom properties for the gradient stops, or use a separate rule:

```css
[data-theme="light"] h1 {
    background: linear-gradient(135deg, #6366f1, #4f46e5, #3730a3);
}
```

### 2. `app.py` — Theme State & Toggle

#### Session state
```python
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
```

#### Sidebar toggle (near the bottom of the sidebar)
```python
st.divider()
st.markdown("### 🎨 Appearance")

current_theme = st.session_state.theme
new_theme = "light" if current_theme == "dark" else "dark"
theme_label = "☀️ Light Mode" if current_theme == "dark" else "🌙 Dark Mode"

if st.button(theme_label, use_container_width=True, key="theme_toggle"):
    st.session_state.theme = new_theme
    st.rerun()
```

#### Pass theme to CSS injection
```python
# Was: inject_custom_css()
# Now: inject_custom_css(theme=st.session_state.theme)
```

### 3. `app.py` — Plotly Theme Swapping

Every `px.line()` and `px.bar()` call uses `template="plotly_dark"`. Must change to use the session theme:

```python
PLOTLY_TEMPLATE = "plotly_dark" if st.session_state.theme == "dark" else "plotly_light"

# In chart generation:
fig = px.line(..., template=PLOTLY_TEMPLATE, ...)
```

Also adjust font colors and plot background based on theme:

```python
font_color = "#9898b0" if st.session_state.theme == "dark" else "#4b5563"
plot_bg = "rgba(0,0,0,0)" if st.session_state.theme == "dark" else "rgba(255,255,255,0)"
```

### 4. `pages/learn.py` — Learn Page Theme Support

The learn page has its own CSS block. It needs the same variable approach:

```css
.concept-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    /* ... */
}
.concept-card:hover {
    border-color: var(--accent-soft);
    box-shadow: 0 8px 32px var(--shadow);
}
```

And the code blocks currently use dark backgrounds:
```css
/* Hardcoded dark — must become theme-aware */
.stCode {
    background: var(--bg-card) !important;
}
```

---

## 🔍 Edge Cases

| Edge Case | Handling |
|---|---|
| **Theme flash on load** | The JS snippet must run before the first paint. Inject it at the top of `inject_custom_css()`, not at the bottom. Use `defer` or inline `<script>` without `defer`. |
| **Plotly charts still dark after toggle** | `st.plotly_chart` caches the figure object. After theme toggle, `st.rerun()` regenerates all charts with the new template. But the Plotly iframe may retain the old CSS. Solution: add a cache-buster key to `st.plotly_chart(key=f"chart_{i}_{theme}")`. |
| **Streamlit's own theme overrides** | Streamlit's `[theme]` config in `.streamlit/config.toml` takes precedence over custom CSS for some elements. We're not using Streamlit's built-in theme system — our CSS is injected via `st.markdown(unsafe_allow_html=True)`, which runs after Streamlit's CSS. We need `!important` on critical rules. |
| **Browser default theme preference** | The user's OS/browser might have `prefers-color-scheme: dark`. We could detect this and default to the OS preference. But simpler to default to dark (current behavior) and let the user toggle. |
| **Learn page code syntax highlighting** | Streamlit's `st.code()` uses a dark syntax theme. Light mode code blocks need a light syntax theme. This requires overriding the `.stCode` CSS for every syntax token color. ~15 rules. |
| **Alert/notification boxes** | `st.info`, `st.warning`, `st.error` have Streamlit-default backgrounds. Our overrides use `rgba(99,102,241,0.08)` which works in both themes. May need slight adjustments for light mode readability. |
| **Mobile/responsive** | The theme toggle is in the sidebar, which collapses on mobile. Users can still toggle from the hamburger menu. No special handling needed. |

---

## 🧪 Test Impact

- **Visual smoke test:** Toggle the theme on every page (main, learn) and verify all components render correctly. Checklist: sidebar, hero, metrics, expander, chat bubbles, chat input, file uploader, alert boxes, Plotly charts, dataframes, buttons, footer, spinner.
- **No unit test for CSS.** Structural test for `inject_custom_css()` accepting a `theme` parameter.
- **Learn page test:** Verify `.stCode` blocks use theme variables.

---

## 📐 Implementation Order

1. **Phase 5a (CSS variable extraction):** Convert all hardcoded colors in `styles.py` to CSS custom properties. No new functionality — just a refactor. Verify dark mode still looks identical. Commit.
2. **Phase 5b (Light theme variables):** Add `[data-theme="light"]` block with inverted colors. Toggle manually by editing the HTML in devtools. Iterate on colors until light mode looks polished. Commit.
3. **Phase 5c (JS + Python toggle):** Add the JS snippet, session state, sidebar button, and `inject_custom_css(theme=...)` parameter. Full toggle working. Commit.
4. **Phase 5d (Plotly + learn page):** Update chart templates and learn page CSS for theme awareness. Commit.
5. **Phase 5e (Edge case polish):** Flash fix, Plotly cache-busting, syntax highlighting, alert box tweaks. Commit.

---

## 💭 Why This Matters

A theme toggle is the #1 most-requested UI feature in analytics tools. Many analysts work in bright offices and prefer light mode; developers prefer dark mode. Supporting both signals that this is a serious tool, not a prototype. The CSS variable architecture also makes future theming (brand colors, accessibility modes) trivial — change the variables, not 200 lines of CSS.

---

*Plan created from deep review of `utils/styles.py` (200+ lines of CSS), `app.py` (Plotly chart templates), `pages/learn.py` (code block styling).*
