# 🎓 Onboarding Tour — Mini-Spec

> **What:** A 3-step guided tour for first-time users of the GA4 Insight Explorer.
> **Status:** ⚠️ Optional — deferred until P1–P3 sprint is complete and stable.
> **Effort:** ~60 min | **Risk:** Medium | **Files:** `app.py`
> **Depends on:** #1 (Learn link in sidebar) must be implemented first.
> **Referenced by:** [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md) (Batch 4), [P4 future plan](📋 P4-future-plan.md)

---

## 🧭 Why This Exists

The empty state (hero page) is beautiful but passive. A first-time user sees "Upload a file in the sidebar" and might not know to also try the AI summary or chat. A 3-step guided tour reduces time-to-value from "figure it out" to ~30 seconds.

This was originally item #8 in IMPLEMENTATION_PLAN.md and was marked ⚠️ Optional in the P1-P3 sprint spec because:
- It has "Medium" risk — adds non-trivial UI state management
- It touches multiple `app.py` areas (`_render_hero()`, `_render_main()`, file processing block, GA4 pull handler)
- It depends on #1 (sidebar learn link) being stable

---

## 🏗️ Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Persistence | **Per-session only** | Resets on page reload — matches the "prototype" nature; no JS complexity |
| Rendering | **Card in main content area** | Overlays the hero/empty state; no tooltip anchoring needed |
| Dismissal | **Auto-dismiss on data load** | Data takes priority — tour auto-completes when user uploads a file or connects GA4 |
| Extraction threshold | **Inline in app.py unless >60 lines** | Extracted to `utils/onboarding.py` only if the state machine grows complex |

---

## 📐 Implementation

### Session State

Add near existing session state initialization in `app.py`:

```python
if "tour_step" not in st.session_state:
    st.session_state.tour_step = 0  # 0 = not started, 1-3 = steps, 4 = done
```

### Tour Start Button

In `_render_hero()`, add when no data is loaded:

```python
if st.session_state.tour_step == 0:
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("🎓 Quick Tour", type="secondary", use_container_width=True):
            st.session_state.tour_step = 1
            st.rerun()
```

### Tour Card

New function `_render_tour_step(step: int)`:

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
                   'Try: *"Which pages have the highest drop-off?"*',
        },
    ]
    s = steps[step - 1]

    with st.container(border=True):
        col_icon, col_content = st.columns([0.15, 0.85])
        with col_icon:
            st.markdown(
                f"<div style='font-size:3rem;'>{s['icon']}</div>",
                unsafe_allow_html=True,
            )
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

### Rendering Logic

In `_render_main()`, before the hero check:

```python
if st.session_state.tour_step in (1, 2, 3) and st.session_state.df is None:
    _render_tour_step(st.session_state.tour_step)
    st.stop()
```

### Auto-Dismiss

In both the **file processing block** and the **GA4 pull handler**:

```python
if st.session_state.tour_step in (1, 2, 3):
    st.session_state.tour_step = 4
```

---

## 🔀 Edge Cases

| Scenario | Behavior |
|---|---|
| User uploads data mid-tour | Tour auto-dismisses — data takes priority |
| User connects GA4 mid-tour | Same auto-dismiss as file upload |
| User reloads the page | Session state resets, tour restarts from step 0 |
| User clicks "Skip Tour" | Tour dismissed permanently for this session |
| Tour on mobile / narrow viewport | Full-width containers work without adjustment |
| Tour + empty state coexistence | Tour renders instead of hero; hero renders when tour done |

---

## 🧪 Test Impact

No unit tests needed (UI state machine, not logic). Smoke test covers:
- Tour renders when "🎓 Quick Tour" button is clicked
- Advance through all 3 steps with Next/Back navigation
- "Skip Tour" dismisses and shows hero
- Tour auto-dismisses on file upload or GA4 connect

If the tour logic exceeds ~60 lines at implementation time, extract to `utils/onboarding.py` and add 3–4 unit tests for the state machine.

---

## 📖 Related Docs

- [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md) — Current sprint (references this as Batch 4 Optional)
- [P4 future plan](📋 P4-future-plan.md) — Future-phase items beyond P1–P3
- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — Original item #8
