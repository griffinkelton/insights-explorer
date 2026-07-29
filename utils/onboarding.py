"""Onboarding tour — 3-step guided walkthrough for first-time users."""

import streamlit as st

TOUR_STEPS = [
    {
        "icon": "📂",
        "title": "Upload your data",
        "body": (
            "👈 Upload a CSV or XLSX file in the sidebar, "
            "or connect live via Google sign‑in."
        ),
    },
    {
        "icon": "✨",
        "title": "Generate an AI summary",
        "body": (
            "Click **Generate Summary** to get an instant overview "
            "of your dataset — date range, top pages, anomalies."
        ),
    },
    {
        "icon": "💬",
        "title": "Ask questions",
        "body": (
            "Type natural language questions in the chat box. "
            'Try: *"Which pages have the highest drop-off?"*'
        ),
    },
]


def render_tour_step(step: int) -> None:
    """Render the current onboarding tour step card.

    Args:
        step: 1-based step number (1, 2, or 3).
    """
    s = TOUR_STEPS[step - 1]

    # Center the tour card like the hero section
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        with st.container(border=True):
            col_icon, col_content = st.columns([0.15, 0.85])
            with col_icon:
                st.markdown(
                    f"<div style='font-size:3rem;text-align:center;'>{s['icon']}</div>",
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
