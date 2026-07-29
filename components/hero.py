"""Hero / empty-state component — shown when no data is loaded."""

import streamlit as st


def render_hero() -> None:
    """Render the hero / empty state when no data is loaded."""
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        # ── Quick Tour button ────────────────────────────────────────────
        if st.session_state.get("tour_step", 0) == 0:
            col_tour, _ = st.columns([1.5, 1])
            with col_tour:
                if st.button(
                    "🎓 Quick Tour",
                    type="secondary",
                    use_container_width=True,
                    help="Take a 3-step guided tour of the app",
                ):
                    st.session_state.tour_step = 1
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
        <div style="text-align:center;padding:3rem 2rem;">
            <div style="font-size:4rem;margin-bottom:1rem;filter:drop-shadow(0 8px 24px rgba(99,102,241,0.3));">
                📊
            </div>
            <h2 style="margin-bottom:0.5rem;background:linear-gradient(135deg,#c4b5fd,#818cf8,#6366f1);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Explore Your Analytics
            </h2>
            <p style="color:#9898b0;font-size:1rem;line-height:1.6;margin-bottom:2rem;">
                <strong>Upload a GA4 export</strong> (CSV or XLSX) or<br>
                <strong>connect live</strong> via Google sign-in<br>
                and ask natural language questions about your data.
            </p>
            <div style="display:flex;gap:1.5rem;justify-content:center;flex-wrap:wrap;">
                <div style="background:#1a1a26;border:1px solid rgba(255,255,255,0.06);
                            border-radius:16px;padding:1.2rem 1.4rem;text-align:center;min-width:140px;">
                    <div style="font-size:1.6rem;margin-bottom:0.3rem;">🔗</div>
                    <div style="font-weight:600;font-size:0.85rem;color:#f0f0f5;">Live Connect</div>
                    <div style="font-size:0.72rem;color:#686880;">Direct GA4 API</div>
                </div>
                <div style="background:#1a1a26;border:1px solid rgba(255,255,255,0.06);
                            border-radius:16px;padding:1.2rem 1.4rem;text-align:center;min-width:140px;">
                    <div style="font-size:1.6rem;margin-bottom:0.3rem;">🤖</div>
                    <div style="font-weight:600;font-size:0.85rem;color:#f0f0f5;">AI Summary</div>
                    <div style="font-size:0.72rem;color:#686880;">Instant insights</div>
                </div>
                <div style="background:#1a1a26;border:1px solid rgba(255,255,255,0.06);
                            border-radius:16px;padding:1.2rem 1.4rem;text-align:center;min-width:140px;">
                    <div style="font-size:1.6rem;margin-bottom:0.3rem;">💬</div>
                    <div style="font-weight:600;font-size:0.85rem;color:#f0f0f5;">Chat</div>
                    <div style="font-size:0.72rem;color:#686880;">Natural language Q&A</div>
                </div>
                <div style="background:#1a1a26;border:1px solid rgba(255,255,255,0.06);
                            border-radius:16px;padding:1.2rem 1.4rem;text-align:center;min-width:140px;">
                    <div style="font-size:1.6rem;margin-bottom:0.3rem;">📈</div>
                    <div style="font-weight:600;font-size:0.85rem;color:#f0f0f5;">Auto-Charts</div>
                    <div style="font-size:0.72rem;color:#686880;">Visualize on the fly</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(
        '<p style="text-align:center;color:#686880;font-size:0.85rem;">'
        "📂 Upload a file in the sidebar to get started</p>",
        unsafe_allow_html=True,
    )
