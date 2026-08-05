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

        # A1 (interstitial PR-L3): all colors moved to the .hero-* class set
        # in utils/styles.py (token-based, theme-correct in both modes) —
        # no inline theme colors remain in this component.
        st.markdown(
            """
        <div class="hero-section">
            <div class="hero-emoji">📊</div>
            <h2 class="hero-title">Explore Your Analytics</h2>
            <p class="hero-subtitle">
                <strong>Upload a GA4 export</strong> (CSV or XLSX) or<br>
                <strong>connect live</strong> via Google sign-in<br>
                and ask natural language questions about your data.
            </p>
            <div class="hero-cards">
                <div class="hero-card">
                    <div class="hero-card-icon">🔗</div>
                    <div class="hero-card-title">Live Connect</div>
                    <div class="hero-card-caption">Direct GA4 API</div>
                </div>
                <div class="hero-card">
                    <div class="hero-card-icon">🤖</div>
                    <div class="hero-card-title">AI Summary</div>
                    <div class="hero-card-caption">Instant insights</div>
                </div>
                <div class="hero-card">
                    <div class="hero-card-icon">💬</div>
                    <div class="hero-card-title">Chat</div>
                    <div class="hero-card-caption">Natural language Q&A</div>
                </div>
                <div class="hero-card">
                    <div class="hero-card-icon">📈</div>
                    <div class="hero-card-title">Auto-Charts</div>
                    <div class="hero-card-caption">Visualize on the fly</div>
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
        '<p class="hero-hint">📂 Upload a file in the sidebar to get started</p>',
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
        # The hero renders AFTER the sidebar's dialog gate
        # (_maybe_show_drive_picker_dialog) has already run this pass, so
        # the fresh drive_picker_active flag alone would not open the
        # dialog until some later interaction. Rerun immediately so the
        # dialog appears right away (the sidebar button needs no rerun —
        # its gate runs later in the same pass).
        st.rerun()
    st.caption("Pick a CSV, XLSX, or Google Sheets file from your Drive")
