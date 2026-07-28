"""GA4 Insight Explorer — Streamlit web app for analyzing GA4 export data with Gemini."""

import os
import time
from typing import Any
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_file, validate_columns, get_dataset_stats, assess_data_quality, filter_dataframe
from utils.gemini_client import generate_response, generate_response_stream, validate_api_key
from utils.prompt_templates import (
    build_summary_prompt,
    build_chat_prompt,
    detect_chart_request,
)
from utils.ga4_client import (
    get_auth_url,
    exchange_code,
    credentials_to_dict,
    credentials_from_dict,
    pull_ga4_report,
)
from utils.styles import inject_custom_css, inject_favicon_meta
from utils.error_boundary import render_error_card

# OAuth redirect URI — configurable via env var for non-localhost deployments
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501")

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GA4 Insight Explorer",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS, JS & favicon (extracted to utils/styles.py) ──────────────────
inject_custom_css()
inject_favicon_meta()

# ── Session state initialization ─────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None
if "stats" not in st.session_state:
    st.session_state.stats = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "missing_columns" not in st.session_state:
    st.session_state.missing_columns = []
if "data_cleared" not in st.session_state:
    st.session_state.data_cleared = False
if "last_file_id" not in st.session_state:
    st.session_state.last_file_id = None
# GA4 live connection state
if "ga4_creds" not in st.session_state:
    st.session_state.ga4_creds = None
if "ga4_property_id" not in st.session_state:
    st.session_state.ga4_property_id = ""
if "ga4_auth_flow" not in st.session_state:
    st.session_state.ga4_auth_flow = None
if "data_source" not in st.session_state:
    st.session_state.data_source = None  # "file" or "ga4"
if "quality_report" not in st.session_state:
    st.session_state.quality_report = None
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = None  # Tri-state: None=unchecked, True/False
# Rate limiting state
if "last_api_call" not in st.session_state:
    st.session_state.last_api_call = 0.0
if "api_call_count" not in st.session_state:
    st.session_state.api_call_count = 0
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = None


# ── API key validation on first run ──────────────────────────────────────────
if st.session_state.api_key_valid is None:
    is_valid, msg = validate_api_key()
    st.session_state.api_key_valid = is_valid
    if not is_valid:
        st.session_state.api_key_error = msg


# ── Handle OAuth callback (Google redirects back with ?code=...) ─────────────
if "code" in st.query_params and st.session_state.ga4_auth_flow is not None:
    try:
        creds = exchange_code(
            st.session_state.ga4_auth_flow,
            code=st.query_params["code"],
        )
        st.session_state.ga4_creds = credentials_to_dict(creds)
        st.session_state.ga4_auth_flow = None
        st.query_params.clear()
        st.success("✅ Connected to Google Analytics!")
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.session_state.ga4_auth_flow = None
        st.query_params.clear()


def clear_data() -> None:
    """Wipe all session state and uploaded file from memory."""
    st.session_state.df = None
    st.session_state.stats = None
    st.session_state.summary = None
    st.session_state.quality_report = None
    st.session_state.chat_history = []
    st.session_state.missing_columns = []
    st.session_state.data_cleared = True
    st.session_state.data_source = None


# ── API key banner (persistent, shows on every page if key is bad) ──────────
if st.session_state.api_key_valid is False:
    st.error(
        f"🔑 **Gemini API Key Issue** — {st.session_state.get('api_key_error', 'Invalid key.')}"
    )
    st.caption("[Get a free key → Google AI Studio](https://aistudio.google.com/apikey)")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
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

    st.divider()

    uploaded_file = st.file_uploader(
        "Upload GA4 Export",
        type=["csv", "xlsx"],
        help="De-identified Google Analytics 4 export file (CSV or XLSX).",
    )

    st.divider()

    # ── GA4 Live Connection section ──
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

    st.divider()

    # Privacy disclaimer
    st.markdown("""
    <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);
                border-radius:12px;padding:0.9rem 1rem;margin:0.5rem 0;">
        <div style="font-size:0.78rem;color:#9898b0;line-height:1.5;">
            🔒 <b>Privacy</b><br>Data is processed in-memory only and is not stored or used to train any model.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.df is not None:
        st.button(
            "🗑️ Clear Data",
            on_click=clear_data,
            use_container_width=True,
            type="secondary",
        )

    if st.session_state.api_call_count > 0:
        st.caption(f"🔢 API calls this session: {st.session_state.api_call_count}")

    st.divider()
    st.markdown(
        '<div style="font-size:0.72rem;color:#686880;">Built with ❤️ using Streamlit + Gemini</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.page_link(
        "pages/learn.py",
        label="📚 Learn Python",
        icon="📚",
        help="Interactive tutorials on Streamlit, Pandas, Plotly, Gemini, and more",
    )

# ── File processing ──────────────────────────────────────────────────────────
if uploaded_file is not None:
    file_id = f"{uploaded_file.name}-{uploaded_file.size}"
    is_new_file = file_id != st.session_state.last_file_id
    should_process = (st.session_state.df is None and not st.session_state.data_cleared) or is_new_file

    if should_process:
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

# ═══════════════════════════════════════════════════════════════════════════════
# Main content rendering
# ═══════════════════════════════════════════════════════════════════════════════

def _render_main() -> None:
    """Render all main content: header, hero/data-preview, summary, chat."""

    st.markdown('<h1 style="margin-bottom:0.3rem;">GA4 Insight Explorer</h1>', unsafe_allow_html=True)
    st.caption("Ask questions about your analytics data — powered by Gemini AI.")

    if st.session_state.df is None:
        _render_hero()
        st.stop()

    df = st.session_state.df
    stats = st.session_state.stats

    # Use filtered data for metrics/preview if available
    display_df = st.session_state.filtered_df if st.session_state.filtered_df is not None else df

    # ── Data preview ─────────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Total Rows", f"{len(display_df):,}")
    with col2:
        st.metric("📊 Columns", len(display_df.columns))
    with col3:
        st.metric("📅 From", stats.get("date_range_start", "—"))
    with col4:
        st.metric("📅 To", stats.get("date_range_end", "—"))

    with st.expander("🔍 Preview Table (first 10 rows)", expanded=False):
        st.dataframe(display_df.head(10), use_container_width=True)

    # ── Data quality scorecard ───────────────────────────────────────────
    if st.session_state.get("quality_report"):
        _render_quality_scorecard(st.session_state.quality_report)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Data filters ─────────────────────────────────────────────────────────
    if st.session_state.df is not None:
        with st.expander("🔍 Filter Data", expanded=False):
            _render_data_filters(df)

    # ── AI Summary ───────────────────────────────────────────────────────────
    st.markdown("### 🤖 AI-Generated Summary")

    summary_col1, summary_col2 = st.columns([3, 1])
    with summary_col1:
        if st.session_state.summary:
            with st.container(border=True):
                st.markdown(st.session_state.summary)
        else:
            st.info("Click **Generate Summary** to analyze your dataset with AI.")

    with summary_col2:
        if st.button(
            "✨ Generate Summary",
            type="primary",
            use_container_width=True,
            key="gen_summary_btn",
        ):
            with st.spinner("🤖 Analyzing your dataset with Gemini..."):
                _generate_summary(df, stats)
            st.rerun()

    st.divider()

    # ── Chat interface ───────────────────────────────────────────────────────
    col_chat_header, col_new_chat = st.columns([4, 1])
    with col_chat_header:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;">'
            '<h3 style="margin:0;">💬 Ask Questions</h3>'
            '<span class="kb-shortcut">⌘K</span> <span style="color:#686880;font-size:0.7rem;">focus chat</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col_new_chat:
        if st.button(
            "🆕 New Chat",
            use_container_width=True,
            help="Clear chat history but keep your data",
        ):
            st.session_state.chat_history = []
            st.rerun()

    for i, entry in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.markdown(entry["question"])

        with st.chat_message("assistant"):
            if entry["response"] == "":
                # ── Stream new message ────────────────────────────────────
                _stream_chat_response(entry, df, i)
            else:
                # ── Render historical message ─────────────────────────────
                st.markdown(entry["response"])
                if entry.get("chart") and entry["chart"].get("fig"):
                    with st.container(border=True):
                        st.plotly_chart(
                            entry["chart"]["fig"],
                            use_container_width=True,
                            key=f"chart_{i}",
                        )

    # Chat input
    if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
        # Rate limiting guard
        now = time.time()
        if now - st.session_state.last_api_call < 2.0:
            st.warning("⏳ Please wait a moment between questions...")
            st.stop()
        st.session_state.last_api_call = now
        st.session_state.api_call_count += 1

        st.session_state.chat_history.append({
            "question": prompt,
            "response": "",
            "chart": None,
        })
        st.rerun()

    # ── Export button ────────────────────────────────────────────────────
    if any(
        e.get("response") and e["response"] != ""
        for e in st.session_state.chat_history
    ):
        st.divider()
        if st.button("📥 Export Report", use_container_width=True):
            from utils.report_exporter import build_markdown_report

            report = build_markdown_report(
                summary=st.session_state.summary,
                chat_history=st.session_state.chat_history,
                stats=st.session_state.stats or {},
                data_source=st.session_state.data_source,
            )
            st.download_button(
                label="⬇️ Download Markdown Report",
                data=report,
                file_name=f"ga4_insight_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )
            st.caption(
                "⚠️ Charts missing from the report? "
                "Install kaleido: `pip install kaleido`"
            )


def _render_data_filters(df: pd.DataFrame) -> None:
    """Render column picker and date range filter controls."""
    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1])

    date_col = _find_date_column(df)
    all_columns = df.columns.tolist()
    dates = None
    min_date = None
    max_date = None

    with col_filter1:
        selected_columns = st.multiselect(
            "Columns to include",
            options=all_columns,
            default=all_columns,
            key="filter_columns",
        )

    with col_filter2:
        start_date = None
        end_date = None
        if date_col:
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if not dates.empty:
                min_date = dates.min().date()
                max_date = dates.max().date()
                date_range = st.date_input(
                    "Date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="filter_dates",
                )
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date = str(date_range[0])
                    end_date = str(date_range[1])

    with col_filter3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.session_state.filter_columns = all_columns
            if date_col and not dates.empty:
                st.session_state.filter_dates = (min_date, max_date)
            st.rerun()

    # Apply filters and store result
    filtered_df = filter_dataframe(
        df,
        date_col=date_col,
        start_date=start_date,
        end_date=end_date,
        selected_columns=selected_columns,
    )

    if filtered_df.empty:
        st.warning("⚠️ No rows match your filters. Try a wider date range or select more columns.")
        st.session_state.filtered_df = None
    else:
        st.session_state.filtered_df = filtered_df
        st.caption(f"Showing {len(filtered_df):,} of {len(df):,} rows")


def _render_hero() -> None:
    """Render the hero / empty state when no data is loaded."""
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("""
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
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown(
        '<p style="text-align:center;color:#686880;font-size:0.85rem;">'
        '📂 Upload a file in the sidebar to get started</p>',
        unsafe_allow_html=True,
    )


# ── Global error boundary ────────────────────────────────────────────────────

try:
    _render_main()
except Exception as e:
    # Streamlit uses exceptions for control flow (st.stop, st.rerun); let those propagate
    if e.__class__.__module__.startswith("streamlit"):
        raise
    render_error_card(e, context="rendering the page")


# ── Summary generation callback ──────────────────────────────────────────────

def _generate_summary(df: pd.DataFrame, stats: dict[str, Any]) -> None:
    """Callback for the Generate Summary button."""
    try:
        summary_prompt = build_summary_prompt(df, stats, quality_report=st.session_state.get("quality_report"))
        st.session_state.summary = generate_response(summary_prompt)
    except ValueError as e:
        st.error(f"🔑 Configuration error: {e}")
    except RuntimeError as e:
        st.error(f"⚠️ API error: {e}")


# ── Chart generation helpers ─────────────────────────────────────────────────

def _render_quality_scorecard(report) -> None:
    """Render the data quality scorecard as a styled A-F grade card."""
    grade_colors = {
        "A": "#34d399",
        "B": "#818cf8",
        "C": "#fbbf24",
        "D": "#f59e0b",
        "F": "#f87171",
    }
    color = grade_colors.get(report.grade, "#686880")

    with st.container(border=True):
        col_grade, col_stats = st.columns([0.2, 0.8])

        with col_grade:
            st.markdown(
                f'<div style="text-align:center;padding:1rem 0;">'
                f'<div style="font-size:3.5rem;font-weight:800;color:{color};'
                f'line-height:1;">{report.grade}</div>'
                f'<div style="font-size:0.7rem;color:#686880;text-transform:uppercase;'
                f'letter-spacing:0.08em;">Data Quality</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_stats:
            parts = [
                f"**{report.completeness_pct}%** completeness",
                f"**{report.column_count}** columns",
                f"**{report.duplicate_count:,}** duplicates",
            ]
            if report.outlier_count:
                parts.append(f"**{report.outlier_count}** outliers")
            st.markdown(" · ".join(parts))

            if report.date_range_days is not None:
                st.markdown(
                    f"📅 **{report.date_range_days}** days of data "
                    f"({report.date_gaps} missing days)"
                )

            if report.missing_columns:
                st.caption(
                    f"Missing expected columns: {', '.join(report.missing_columns)}"
                )

            for warning in report.warnings:
                st.warning(warning, icon="⚠️")

            if not report.warnings:
                st.success("No significant data quality issues detected.", icon="✅")


def _generate_chart(
    df: pd.DataFrame,
    chart_config: dict[str, str],
    gemini_response: str,
    user_question: str,
) -> dict[str, Any] | None:
    chart_type = chart_config.get("chart_type", "bar")
    try:
        date_col = _find_date_column(df)

        if chart_type == "line" and date_col:
            sessions_col = _find_column(df, ["sessions"])
            if sessions_col:
                daily = df.groupby(date_col)[sessions_col].sum().reset_index().sort_values(date_col)
                fig = px.line(
                    daily, x=date_col, y=sessions_col,
                    title="Sessions Over Time", markers=True,
                    template="plotly_dark",
                    color_discrete_sequence=["#818cf8"],
                )
                fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
                fig.update_layout(
                    xaxis_title="Date", yaxis_title="Sessions",
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9898b0", size=12),
                    margin=dict(l=20, r=20, t=40, b=20),
                    hovermode="x unified",
                )
                return {"fig": fig, "type": "line"}

        if chart_type in ("bar", "ranking"):
            page_col = _find_column(df, ["page_path", "page", "path", "url", "landing_page"])
            sessions_col = _find_column(df, ["sessions"])
            if page_col and sessions_col:
                top = df.groupby(page_col)[sessions_col].sum().nlargest(10).reset_index()
                fig = px.bar(
                    top, x=sessions_col, y=page_col, orientation="h",
                    title=f"Top Pages by {sessions_col.replace('_', ' ').title()}",
                    template="plotly_dark",
                    color_discrete_sequence=["#818cf8"],
                    text_auto=".1s",
                )
                fig.update_traces(textposition="outside", textfont=dict(color="#9898b0", size=11))
                fig.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9898b0", size=12),
                    margin=dict(l=20, r=40, t=40, b=20),
                )
                return {"fig": fig, "type": "bar"}

        # Fallback
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        if numeric_cols and categorical_cols:
            cat_col, num_col = categorical_cols[0], numeric_cols[0]
            agg = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()
            fig = px.bar(
                agg, x=num_col, y=cat_col, orientation="h",
                title=f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                template="plotly_dark",
                color_discrete_sequence=["#818cf8"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9898b0", size=12),
            )
            return {"fig": fig, "type": "bar"}
    except Exception:
        pass
    return None


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        if candidate in df_cols_lower:
            return df_cols_lower[candidate]
    return None


def _find_date_column(df: pd.DataFrame) -> str | None:
    date_candidates = ["date", "day", "date_time", "timestamp"]
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in date_candidates:
        if candidate in df_cols_lower:
            return df_cols_lower[candidate]
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None


def _stream_chat_response(entry: dict[str, Any], df: pd.DataFrame, i: int) -> None:
    """Stream a Gemini response with st.write_stream, then detect and render chart.

    Called from _render_main() when a chat_history entry has response=="".
    Updates entry["response"] and entry["chart"] in place.
    """
    chat_prompt = build_chat_prompt(
        entry["question"],
        df,
        st.session_state.stats,
        conversation_history=st.session_state.chat_history[:-1],
    )

    try:
        full_text = st.write_stream(generate_response_stream(chat_prompt))
        entry["response"] = full_text

        # Detect and render chart from the full response
        chart_config = detect_chart_request(full_text)
        if chart_config:
            chart_data = _generate_chart(df, chart_config, full_text, entry["question"])
            if chart_data:
                entry["chart"] = chart_data
                with st.container(border=True):
                    st.plotly_chart(
                        chart_data["fig"],
                        use_container_width=True,
                        key=f"chart_{i}",
                    )

    except ValueError as e:
        entry["response"] = f"🔑 Configuration error: {e}"
    except RuntimeError as e:
        entry["response"] = f"⚠️ API error: {e}"
    except Exception as e:
        entry["response"] = f"⚠️ An unexpected error occurred: {e}"


# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    '<p style="text-align:center;color:#686880;font-size:0.75rem;">'
    'GA4 Insight Explorer · Data processed in-memory only · '
    '<a href="https://aistudio.google.com/apikey" style="color:#818cf8;">Gemini API Key</a> · '
    '<a href="https://console.cloud.google.com/apis/credentials" style="color:#818cf8;">GCP OAuth Setup</a>'
    '</p>',
    unsafe_allow_html=True,
)
