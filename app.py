"""GA4 Insight Explorer — Streamlit web app for analyzing GA4 export data with Gemini."""

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_file, validate_columns, get_dataset_stats
from utils.gemini_client import generate_response
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

# OAuth redirect URI — must match what's registered in GCP Console
REDIRECT_URI = "http://localhost:8501"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GA4 Insight Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import Inter font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global resets & theme ── */
    :root {
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
        --radius-sm: 8px;
        --radius-md: 14px;
        --radius-lg: 20px;
        --radius-xl: 24px;
    }

    .stApp {
        background: var(--bg-primary);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary);
        -webkit-font-smoothing: antialiased;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1 {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    [data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-secondary) !important;
        font-size: 0.85rem;
    }

    /* ── Headers ── */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
    }
    h1 {
        font-size: 2rem !important;
        background: linear-gradient(135deg, #c4b5fd, #818cf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    h2 {
        font-size: 1.35rem !important;
        color: var(--text-primary) !important;
    }
    h3 {
        font-size: 1.15rem !important;
        color: var(--text-primary) !important;
        margin-bottom: 0rem !important;
    }

    /* ── Cards ── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        /* Nested containers get card styling when used for cards */
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s ease !important;
        border: none !important;
        letter-spacing: -0.01em;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 28px rgba(99, 102, 241, 0.45);
        transform: translateY(-1px);
    }
    .stButton > button[kind="secondary"] {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #2a2a3a !important;
        border-color: rgba(255,255,255,0.12) !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.2rem 1.4rem !important;
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(99, 102, 241, 0.25);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }
    [data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    [data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    .streamlit-expanderHeader:hover {
        border-color: rgba(99, 102, 241, 0.25) !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
    }

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {
        border-radius: var(--radius-md) !important;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] table {
        font-size: 0.85rem;
    }
    [data-testid="stDataFrame"] th {
        background: var(--bg-elevated) !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        border-radius: var(--radius-lg) !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 0.6rem !important;
    }
    [data-testid="stChatMessage"][data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        /* Assistant messages */
    }

    /* ── Chat input ── */
    [data-testid="stChatInput"] textarea {
        border-radius: var(--radius-xl) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        font-size: 0.92rem !important;
        padding: 0.9rem 1.2rem !important;
        transition: all 0.2s ease;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft);
    }

    /* ── Dividers ── */
    hr {
        border-color: var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Info/Warning/Error boxes ── */
    div[data-testid="stAlert"] {
        border-radius: var(--radius-md) !important;
        border: none !important;
        font-size: 0.88rem;
    }
    div[data-testid="stAlert"][kind="info"] {
        background: rgba(99, 102, 241, 0.08) !important;
        border-left: 3px solid var(--accent) !important;
    }
    div[data-testid="stAlert"][kind="warning"] {
        background: rgba(251, 191, 36, 0.08) !important;
        border-left: 3px solid var(--warning) !important;
    }
    div[data-testid="stAlert"][kind="error"] {
        background: rgba(248, 113, 113, 0.08) !important;
        border-left: 3px solid var(--danger) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] section {
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius-lg) !important;
        background: var(--bg-card) !important;
        transition: all 0.2s ease;
        padding: 1.5rem !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(99, 102, 241, 0.3) !important;
        background: rgba(99, 102, 241, 0.03) !important;
    }
    [data-testid="stFileUploader"] small {
        color: var(--text-muted) !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-color: var(--accent) !important;
    }

    /* ── Plotly charts ── */
    .js-plotly-plot {
        border-radius: var(--radius-lg) !important;
        overflow: hidden;
    }

    /* ── Smooth fade-in (scoped to hero and main content only) ── */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .hero-section, [data-testid="stMetric"] {
        animation: fadeIn 0.5s ease-out;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 20px; }
    ::-webkit-scrollbar-thumb:hover { background: #333344; }

    /* ── Tooltip ── */
    .stTooltip {
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

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


def clear_data():
    """Wipe all session state and uploaded file from memory."""
    st.session_state.df = None
    st.session_state.stats = None
    st.session_state.summary = None
    st.session_state.chat_history = []
    st.session_state.missing_columns = []
    st.session_state.data_cleared = True
    st.session_state.data_source = None


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
            # Redirect user to Google OAuth consent screen
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

        col_pull, col_disc = st.columns(2)
        with col_pull:
            if st.button("📥 Pull Data", use_container_width=True, type="primary"):
                if not property_id:
                    st.error("Please enter your GA4 Property ID first.")
                else:
                    with st.spinner("Fetching data from Google Analytics..."):
                        try:
                            creds = credentials_from_dict(st.session_state.ga4_creds)
                            df = pull_ga4_report(creds, property_id)
                            if df.empty:
                                st.error("No data returned. Check your Property ID and date range.")
                            else:
                                # Parse dates and validate columns
                                missing = validate_columns(df)
                                if missing:
                                    st.warning(f"⚠️ Missing columns: {', '.join(missing)}")

                                st.session_state.df = df
                                st.session_state.missing_columns = missing
                                st.session_state.stats = get_dataset_stats(df)
                                st.session_state.stats["missing_columns"] = missing
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

    # Privacy disclaimer — clean card style
    st.markdown("""
    <div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.12);
                border-radius:12px;padding:0.9rem 1rem;margin:0.5rem 0;">
        <div style="font-size:0.78rem;color:#9898b0;line-height:1.5;">
            🔒 <b>Privacy</b><br>All data stays in-memory.<br>Nothing is stored or sent to train models.
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

    st.divider()
    st.markdown(
        '<div style="font-size:0.72rem;color:#686880;">Built with ❤️ using Streamlit + Gemini</div>',
        unsafe_allow_html=True,
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

        df, error = load_file(uploaded_file)

        if error:
            st.error(f"❌ {error}")
            st.session_state.last_file_id = file_id
        else:
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
            st.session_state.data_cleared = False
            st.session_state.last_file_id = file_id

# ── Main content area ────────────────────────────────────────────────────────
st.markdown('<h1 style="margin-bottom:0.3rem;">GA4 Insight Explorer</h1>', unsafe_allow_html=True)
st.caption("Ask questions about your analytics data — powered by Gemini AI.")

if st.session_state.df is None:
    # ── Empty state — hero section ──
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
    st.stop()

# ── Data preview ─────────────────────────────────────────────────────────────
df = st.session_state.df
stats = st.session_state.stats

st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📋 Total Rows", f"{stats['row_count']:,}")
with col2:
    st.metric("📊 Columns", stats["column_count"])
with col3:
    st.metric("📅 From", stats.get("date_range_start", "—"))
with col4:
    st.metric("📅 To", stats.get("date_range_end", "—"))

with st.expander("🔍 Preview Table (first 10 rows)", expanded=False):
    st.dataframe(df.head(10), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── AI Summary ───────────────────────────────────────────────────────────────
st.markdown("### 🤖 AI-Generated Summary")

summary_col1, summary_col2 = st.columns([3, 1])
with summary_col1:
    if st.session_state.summary:
        with st.container(border=True):
            st.markdown(st.session_state.summary)
    else:
        st.info("Click **Generate Summary** to analyze your dataset with AI.")

with summary_col2:
    st.button(
        "✨ Generate Summary",
        type="primary",
        use_container_width=True,
        key="gen_summary_btn",
        on_click=lambda: _generate_summary(df, stats),
    )

st.divider()

# ── Chat interface ───────────────────────────────────────────────────────────
st.markdown("### 💬 Ask Questions")

# Display chat history
for i, entry in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.markdown(entry["question"])

    with st.chat_message("assistant"):
        st.markdown(entry["response"])
        if entry.get("chart") and entry["chart"].get("fig"):
            with st.container(border=True):
                st.plotly_chart(entry["chart"]["fig"], use_container_width=True, key=f"chart_{i}")

# Chat input
if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
    st.session_state.chat_history.append({
        "question": prompt,
        "response": None,
        "chart": None,
    })

    with st.spinner("Thinking..."):
        try:
            chat_prompt = build_chat_prompt(prompt, df, stats)
            response = generate_response(chat_prompt)

            chart_config = detect_chart_request(response)
            chart_data = None
            if chart_config:
                chart_data = _generate_chart(df, chart_config, prompt, response)

            st.session_state.chat_history[-1]["response"] = response
            st.session_state.chat_history[-1]["chart"] = chart_data

        except ValueError as e:
            st.session_state.chat_history[-1]["response"] = f"🔑 Configuration error: {e}"
        except RuntimeError as e:
            st.session_state.chat_history[-1]["response"] = f"⚠️ API error: {e}"

    st.rerun()


# ── Summary generation callback ──────────────────────────────────────────────
def _generate_summary(df, stats):
    """Callback for the Generate Summary button."""
    try:
        summary_prompt = build_summary_prompt(df, stats)
        st.session_state.summary = generate_response(summary_prompt)
    except ValueError as e:
        st.error(f"🔑 Configuration error: {e}")
    except RuntimeError as e:
        st.error(f"⚠️ API error: {e}")


# ── Chart generation helpers ─────────────────────────────────────────────────
def _generate_chart(df, chart_config, gemini_response, user_question):
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


def _find_column(df, candidates):
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        if candidate in df_cols_lower:
            return df_cols_lower[candidate]
    return None


def _find_date_column(df):
    date_candidates = ["date", "day", "date_time", "timestamp"]
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in date_candidates:
        if candidate in df_cols_lower:
            return df_cols_lower[candidate]
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None


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
