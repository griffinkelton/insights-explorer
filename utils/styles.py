"""Custom CSS and JS injection for the GA4 Insight Explorer UI."""

import streamlit as st


def inject_custom_css() -> None:
    """Inject the app's custom CSS theme and keyboard shortcut JS."""
    st.markdown(
        """
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

    /* ── Keyboard shortcut hint ── */
    .kb-shortcut {
        display: inline-block;
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 5px;
        padding: 2px 7px;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        font-family: 'Inter', monospace;
    }
</style>

<!-- Keyboard shortcuts JS -->
<script>
(function() {
    document.addEventListener('keydown', function(e) {
        const isMac = /Mac/i.test(navigator.userAgentData?.platform || navigator.platform || '');
        const mod = isMac ? e.metaKey : e.ctrlKey;

        // Cmd/Ctrl + K → focus chat input
        if (mod && e.key === 'k') {
            e.preventDefault();
            const chatInput = document.querySelector('[data-testid="stChatInput"] textarea');
            if (chatInput) { chatInput.focus(); }
        }
    });
})();
</script>
""",
        unsafe_allow_html=True,
    )
