"""GA4 Insight Explorer — UI component orchestration."""

import streamlit as st
from components.sidebar import render_sidebar
from components.hero import render_hero
from components.data_preview import render_data_preview
from components.summary import render_summary_section
from components.chat import render_chat_section
from utils.ga4_client import exchange_code, credentials_to_dict
from utils.error_boundary import render_error_card
from utils.onboarding import render_tour_step


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
        # Streamlit uses exceptions for control flow (st.stop, st.rerun); let those propagate
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
        # ── Onboarding tour (replaces hero when active) ──────────────────
        tour_step = st.session_state.get("tour_step", 0)
        if tour_step in (1, 2, 3):
            render_tour_step(tour_step)
            st.stop()

        render_hero()
        st.stop()

    render_data_preview()
    render_summary_section()

    st.divider()

    render_chat_section()

    # ── Footer ───────────────────────────────────────────────────────────
    st.divider()
    st.markdown(
        '<p style="text-align:center;color:#686880;font-size:0.75rem;">'
        "GA4 Insight Explorer · Data processed in-memory only · "
        '<a href="https://aistudio.google.com/apikey" style="color:#818cf8;">Gemini API Key</a> · '
        '<a href="https://console.cloud.google.com/apis/credentials" style="color:#818cf8;">GCP OAuth Setup</a>'
        "</p>",
        unsafe_allow_html=True,
    )


def _handle_oauth_callback() -> None:
    """Handle Google OAuth redirect (?code=...).

    Called at the very start of render_all(), before any UI renders.
    After exchanging the code for credentials, calls st.rerun() to
    clean the URL of query params and start a fresh render cycle with
    the authenticated state.
    """
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
        # Rerun immediately: strips ?code= from the browser URL and
        # starts a clean render cycle where the sidebar shows "✅ Connected".
        # Without this, the callback and page render share a cycle, and
        # the browser URL retains the single-use auth code on refresh.
        st.rerun()
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.session_state.ga4_auth_flow = None
        st.query_params.clear()
