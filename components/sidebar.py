"""Sidebar — file uploader, GA4 connect, privacy notice, navigation."""

import os
import pandas as pd
import streamlit as st
from utils.data_loader import load_file, validate_columns, get_dataset_stats, assess_data_quality
from utils.ga4_client import get_auth_url, credentials_from_dict, pull_ga4_report
from utils.session import clear_data

REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501")


def render_sidebar() -> None:
    """Render the full sidebar and return the uploaded file (if any)."""
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
        _render_footer()
        _render_learn_link()

    # Process uploaded file (after sidebar renders so errors show in main area)
    if uploaded_file is not None:
        _process_uploaded_file(uploaded_file)


def _render_logo() -> None:
    """Render the app logo and title in the sidebar."""
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
        <div style="width:38px;height:38px;border-radius:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                    display:flex;align-items:center;justify-content:center;font-size:1.2rem;">📊</div>
        <div>
            <div style="font-weight:700;font-size:1.1rem;color:#f0f0f5;line-height:1.3;">Insight Explorer</div>
            <div style="font-size:0.75rem;color:#9898b0;">GA4 Analytics + AI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_file_uploader():
    """Render the file uploader widget. Returns the uploaded file or None."""
    return st.file_uploader(
        "Upload GA4 Export",
        type=["csv", "xlsx"],
        help="De-identified Google Analytics 4 export file (CSV or XLSX).",
    )


def _render_ga4_connect() -> None:
    """Render the GA4 live connection: sign-in, property ID, pull data, disconnect."""
    st.markdown(
        '<p style="font-size:0.8rem;font-weight:600;color:#f0f0f5;margin-bottom:0.3rem;">'
        '🔗 Google Analytics 4 (Live)</p>',
        unsafe_allow_html=True,
    )

    if st.session_state.ga4_creds is None:
        # Not connected — show sign-in
        if st.button("🔐 Sign in with Google", use_container_width=True, type="primary"):
            auth_url, flow = get_auth_url(REDIRECT_URI)
            st.session_state.ga4_auth_flow = flow
            st.markdown(
                f'<meta http-equiv="refresh" content="0;url={auth_url}">'
                f'<p style="color:#9898b0;font-size:0.85rem;">Redirecting to Google...</p>'
                f'<p style="color:#686880;font-size:0.75rem;">'
                f'If not redirected, <a href="{auth_url}" style="color:#818cf8;">click here</a></p>',
                unsafe_allow_html=True,
            )
            st.stop()

        st.caption(
            "Connect live to your GA4 property. "
            "Requires a [GCP OAuth client](https://console.cloud.google.com/apis/credentials) "
            "with `http://localhost:8501` as an authorized redirect URI."
        )
    else:
        # Connected — show controls
        st.success("✅ Connected to Google")

        property_id = st.text_input(
            "GA4 Property ID",
            value=st.session_state.ga4_property_id,
            placeholder="e.g., 123456789",
            help="Numeric property ID from GA4 Admin > Property Settings",
        )
        st.session_state.ga4_property_id = property_id

        date_range = st.selectbox(
            "Date range",
            options=["7 days", "30 days", "90 days"],
            index=2,
            key="ga4_date_range",
            help="How far back to pull data from GA4.",
        )
        start_date_map = {"7 days": "7daysAgo", "30 days": "30daysAgo", "90 days": "90daysAgo"}
        start_date = start_date_map[date_range]

        col_pull, col_disc = st.columns(2)
        with col_pull:
            if st.button("📥 Pull Data", use_container_width=True, type="primary"):
                if not property_id:
                    st.error("Please enter your GA4 Property ID first.")
                else:
                    with st.spinner(f"Fetching {date_range} of data from Google Analytics..."):
                        try:
                            creds = credentials_from_dict(st.session_state.ga4_creds)
                            df = pull_ga4_report(creds, property_id, start_date=start_date)
                            if df.empty:
                                st.error("No data returned. Check your Property ID and date range.")
                            else:
                                missing = validate_columns(df)
                                if missing:
                                    st.warning(f"⚠️ Missing columns: {', '.join(missing)}")

                                st.session_state.df = df
                                st.session_state.missing_columns = missing
                                st.session_state.stats = get_dataset_stats(df)
                                st.session_state.stats["missing_columns"] = missing
                                st.session_state.quality_report = assess_data_quality(df, missing)
                                st.session_state.summary = None
                                st.session_state.chat_history = []
                                st.session_state.data_source = "ga4"
                                st.session_state.data_cleared = False
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to pull GA4 data: {e}")

        with col_disc:
            if st.button("✕ Disconnect", use_container_width=True):
                st.session_state.ga4_creds = None
                st.session_state.ga4_auth_flow = None
                st.session_state.ga4_property_id = ""
                if st.session_state.data_source == "ga4":
                    clear_data()
                st.rerun()


def _render_privacy_notice() -> None:
    """Render the privacy disclaimer card."""
    st.markdown("""
    <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);
                border-radius:12px;padding:0.9rem 1rem;margin:0.5rem 0;">
        <div style="font-size:0.78rem;color:#9898b0;line-height:1.5;">
            🔒 <b>Privacy</b><br>Data is processed in-memory only and is not stored or used to train any model.
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_clear_button() -> None:
    """Render the Clear Data button. Only shown when data is loaded.

    FIX (BUG-005): Uses `if st.button` pattern instead of `on_click=clear_data`
    to comply with the anti-pattern guard.
    """
    if st.session_state.df is not None:
        if st.button(
            "🗑️ Clear Data",
            use_container_width=True,
            type="secondary",
        ):
            clear_data()
            st.rerun()


def _render_api_counter() -> None:
    """Render API call counter (only when calls have been made)."""
    if st.session_state.api_call_count > 0:
        st.caption(f"🔢 API calls this session: {st.session_state.api_call_count}")


def _render_footer() -> None:
    """Render the sidebar footer."""
    st.divider()
    st.markdown(
        '<div style="font-size:0.72rem;color:#686880;">Built with ❤️ using Streamlit + Gemini</div>',
        unsafe_allow_html=True,
    )


def _render_learn_link() -> None:
    """Render the navigation link to the Learn page."""
    st.divider()
    st.page_link(
        "pages/learn.py",
        label="📚 Learn Python",
        icon="📚",
        help="Interactive tutorials on Streamlit, Pandas, Plotly, Gemini, and more",
    )


def _process_uploaded_file(uploaded_file) -> None:
    """Parse uploaded file and populate session state."""
    file_id = f"{uploaded_file.name}-{uploaded_file.size}"
    is_new_file = file_id != st.session_state.last_file_id
    should_process = (st.session_state.df is None and not st.session_state.data_cleared) or is_new_file

    if not should_process:
        return

    if is_new_file and st.session_state.df is not None:
        clear_data()
        st.session_state.data_cleared = False

    df, error, warning = load_file(uploaded_file)

    if error:
        st.error(f"❌ {error}")
        st.session_state.last_file_id = file_id
    else:
        if warning:
            st.warning(f"⚠️ {warning}")
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"📥 Download truncated data ({len(df):,} rows)",
                data=csv_data,
                file_name=f"truncated_{uploaded_file.name}",
                mime="text/csv",
            )
        missing = validate_columns(df)
        if missing:
            st.warning(
                f"⚠️ Missing expected columns: {', '.join(missing)}. "
                "Some features may be limited."
            )

        date_cols = [c for c in df.columns if "date" in c.lower()]
        if date_cols:
            try:
                df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors="coerce")
            except Exception:
                pass

        st.session_state.df = df
        st.session_state.missing_columns = missing
        st.session_state.stats = get_dataset_stats(df)
        st.session_state.stats["missing_columns"] = missing
        st.session_state.quality_report = assess_data_quality(df, missing)
        st.session_state.data_cleared = False
        st.session_state.last_file_id = file_id
