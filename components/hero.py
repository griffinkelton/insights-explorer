"""Hero / empty-state component — shown when no data is loaded."""

import streamlit as st


def render_hero() -> None:
    """Render the hero / empty state when no data is loaded."""
    st.markdown("")

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        # ── Replay tour (always visible — localStorage is authoritative) ──
        if st.button(
            "🔄 Replay tour",
            type="secondary",
            use_container_width=True,
            help="Take the guided tour again",
            key="replay_tour_btn",
        ):
            st.session_state["_tour_replay_requested"] = True
            st.rerun()
        st.markdown("")

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

        # ── Drive Import entry point (interstitial PR 2, D6) ──
        # Below the feature-card grid so it reads as a third import path
        # alongside Upload (sidebar) and Connect GA4, not a floating CTA.
        _render_drive_import_card()

    st.divider()
    st.markdown(
        '<p style="text-align:center;color:#686880;font-size:0.85rem;">'
        "📂 Upload a file in the sidebar to get started</p>",
        unsafe_allow_html=True,
    )


def _render_drive_import_card() -> None:
    """Drive Import entry point in the empty-state hero (interstitial PR 2, D6).

    Shown only when Drive import is actually available (test mode, or
    authenticated with Picker secrets configured). Sets the same flags as
    the sidebar button — the dialog opens via the shared
    ``_maybe_show_drive_picker_dialog()`` gate on the next run.
    """
    from components.sidebar import activate_drive_picker, drive_import_ready

    if not drive_import_ready():
        return
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    if st.button(
        "📂 Import from Google Drive",
        use_container_width=True,
        type="primary",
        key="hero_drive_import",
    ):
        activate_drive_picker()
    st.caption("Pick a CSV, XLSX, or Google Sheets file from your Drive")
