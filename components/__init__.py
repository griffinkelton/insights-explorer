"""GA4 Insight Explorer — UI component orchestration."""

import logging

import streamlit as st

from components.chat import render_chat_section
from components.data_preview import render_data_preview
from components.hero import render_hero
from components.sidebar import render_sidebar
from components.summary import render_summary_section
from utils.error_boundary import render_error_card
from utils.ga4_client import credentials_to_dict, exchange_code
from components.onboarding_tour import render_onboarding_tour

logger = logging.getLogger(__name__)


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

    # Drive Picker overlay — renders at full width in main area (not cramped sidebar)
    _render_drive_picker_overlay()

    st.markdown(
        '<h1 style="margin-bottom:0.3rem;">GA4 Insight Explorer</h1>',
        unsafe_allow_html=True,
    )
    st.caption("Ask questions about your analytics data — powered by Gemini AI.")

    if st.session_state.data_context is None:
        # ── Onboarding tour (frontend-owned, localStorage-persisted) ──
        render_onboarding_tour()

        render_hero()

    render_data_preview()
    render_summary_section()

    st.divider()

    render_chat_section()

    # ── Footer ───────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "GA4 Insight Explorer · Data processed in session · AI calls sent to Gemini API · "
        "Exports via [Google Sheets & Drive](https://developers.google.com/sheets/api) · "
        "[Gemini API Key](https://aistudio.google.com/apikey)"
    )


def _render_drive_picker_overlay() -> None:
    """Render the Google Drive Picker in the main content area (full width).

    The sidebar's _render_drive_picker() stores config in session state
    when the user clicks "Import from Google Drive". This function picks
    it up, renders the Picker iframe at full width, and processes the
    selection on return.
    """
    import os

    from components.sidebar import _ingest_drive_file
    from components.drive_picker_component import drive_picker_transport
    from utils.drive_client import download_drive_file
    from utils.ga4_client import credentials_from_dict

    if not st.session_state.get("drive_picker_active"):
        return
    if not st.session_state.get("drive_picker_request_id"):
        return

    oauth_token = st.session_state.get("_drive_picker_oauth_token", "")
    dev_key = st.session_state.get("_drive_picker_dev_key", "")
    app_id = st.session_state.get("_drive_picker_app_id", "")
    app_origin = st.session_state.get("_drive_picker_app_origin", "")
    request_id = st.session_state["drive_picker_request_id"]

    if not oauth_token or not dev_key:
        return

    # ── Full-width Picker container ──
    st.markdown(
        '<div style="margin: 1rem 0 0.5rem 0; font-weight: 600; font-size: 0.95rem;">'
        "📂 Select a file from Google Drive</div>",
        unsafe_allow_html=True,
    )
    st.caption("Choose a CSV, XLSX, or Google Sheets file to import.")

    _DRIVE_PICKER_TEST_MODE = os.getenv("DRIVE_PICKER_TEST_MODE", "") == "1"

    if _DRIVE_PICKER_TEST_MODE:
        seam = st.query_params.get("picker_seam", "")
        if seam == "picked":
            selection = {
                "kind": "picked",
                "requestId": request_id,
                "fileId": "test-file-id-123",
            }
        elif seam in ("cancel", "error"):
            selection = None
        else:
            selection = drive_picker_transport(
                oauth_token=oauth_token,
                dev_key=dev_key,
                app_id=app_id,
                app_origin=app_origin,
                request_id=request_id,
                theme=st.session_state.get("theme", "dark"),
                key=f"drive_picker_{request_id}",
            )
    else:
        selection = drive_picker_transport(
            oauth_token=oauth_token,
            dev_key=dev_key,
            app_id=app_id,
            app_origin=app_origin,
            request_id=request_id,
            theme=st.session_state.get("theme", "dark"),
            key=f"drive_picker_{request_id}",
        )

    # ── Process selection ──
    if selection is not None:
        if selection["requestId"] != request_id:
            return  # Stale selection from a previous render.

        if _DRIVE_PICKER_TEST_MODE:
            st.session_state.drive_picker_active = False
            st.session_state._drive_picker_oauth_token = ""
            st.rerun()
        else:
            creds_dict = st.session_state.ga4_creds
            creds = credentials_from_dict(creds_dict)
            ok = _ingest_drive_file(download_drive_file, creds, selection["fileId"])
            if not ok:
                return  # Error is already displayed; keep picker active.
            st.session_state.drive_picker_active = False
            st.session_state._drive_picker_oauth_token = ""
            st.rerun()

    # ── Cancel button ──
    col_cancel, _ = st.columns([1, 3])
    with col_cancel:
        if st.button("✕ Cancel", key="drive_picker_cancel_main"):
            st.session_state.drive_picker_active = False
            st.session_state.drive_picker_request_id = ""
            st.session_state._drive_picker_oauth_token = ""
            st.rerun()


def _handle_oauth_callback() -> None:
    """Handle Google OAuth redirect (?code=...&state=...).

    Called at the very start of render_all(), before any UI renders.
    After exchanging the code for credentials, calls st.rerun() to
    clean the URL of query params and start a fresh render cycle with
    the authenticated state.
    """
    if "code" not in st.query_params:
        return
    try:
        from components.sidebar import REDIRECT_URI

        creds = exchange_code(
            code=st.query_params["code"],
            redirect_uri=REDIRECT_URI,
            state=st.query_params.get("state"),
        )
        st.session_state.ga4_creds = credentials_to_dict(creds)
        st.query_params.clear()
        # Rerun immediately: strips ?code= from the browser URL and
        # starts a clean render cycle where the sidebar shows "✅ Connected".
        # Without this, the callback and page render share a cycle, and
        # the browser URL retains the single-use auth code on refresh.
        st.rerun()
    except Exception:
        st.error("Authentication failed. Please sign in again.")
        logger.warning("OAuth callback error", exc_info=True)
        st.query_params.clear()
