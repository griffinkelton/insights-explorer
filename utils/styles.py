"""Custom CSS, JS, and favicon injection for the GA4 Insight Explorer UI."""

import streamlit as st


def inject_favicon_meta(theme: str = "dark") -> None:
    """Inject favicon, Apple Touch Icon, and Open Graph meta tags into the page head.

    Args:
        theme: "dark" (default) or "light". Controls the theme-color meta tag.

    Call this once per page after st.set_page_config().

    Note: The HTML <link> tags here will 404 in local dev mode
    (streamlit run) because Streamlit doesn't serve arbitrary static
    files — only st.set_page_config(page_icon=...) works locally via
    base64 encoding. The HTML tags activate in production behind
    nginx, Cloud Run, or any proper static file server.
    """
    theme_color = "#0a0a0f" if theme == "dark" else "#ffffff"
    st.markdown(
        f"""
    <!-- Favicon (standard + retina) -->
    <link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/icon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/icon-16x16.png">
    <link rel="shortcut icon" href="/assets/favicon.ico">

    <!-- Apple Touch Icon (iOS home screen) -->
    <link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/icon-180x180.png">

    <!-- Android / PWA -->
    <link rel="manifest" href="/assets/site.webmanifest">
    <meta name="theme-color" content="{theme_color}">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

    <!-- Open Graph / Social Share -->
    <meta property="og:title" content="GA4 Insight Explorer">
    <meta property="og:description" content="Analyze GA4 data with natural language — powered by Gemini AI">
    <meta property="og:image" content="/assets/og-image.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    """,
        unsafe_allow_html=True,
    )


def inject_custom_css(theme: str = "dark") -> None:
    """Inject the app's custom CSS theme and keyboard shortcut JS.

    Args:
        theme: "dark" (default) or "light". Sets data-theme on the
            document element via a hidden div + JS snippet.
    """
    st.markdown(
        f"""<div id="theme-data" data-theme="{theme}" style="display:none;"></div>
<style>
    /* ── Import Inter font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global resets & dark theme (default) ── */
    :root {{
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
    }}

    /* ── Light theme overrides ── */
    [data-theme="light"] {{
        --bg-primary: #ffffff;
        --bg-secondary: #f5f5fa;
        --bg-card: #ffffff;
        --bg-elevated: #f0f0f5;
        --text-primary: #1a1a2e;
        --text-secondary: #686880;
        --text-muted: #9898b0;
        --accent: #4f46e5;
        --accent-hover: #6366f1;
        --accent-soft: rgba(79, 70, 229, 0.08);
        --success: #059669;
        --warning: #d97706;
        --danger: #dc2626;
        --border: rgba(0, 0, 0, 0.08);
    }}

    .stApp {{
        background: var(--bg-primary);
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-primary);
        -webkit-font-smoothing: antialiased;
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }}
    [data-testid="stSidebar"] .stMarkdown h1 {{
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }}
    [data-testid="stSidebar"] .stMarkdown p {{
        color: var(--text-secondary) !important;
        font-size: 0.85rem;
    }}

    /* ── Headers ── */
    h1, h2, h3 {{
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
    }}
    h1 {{
        font-size: 2rem !important;
        background: linear-gradient(135deg, #c4b5fd, #818cf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    [data-theme="light"] h1 {{
        background: linear-gradient(135deg, #6366f1, #4f46e5, #3730a3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    h2 {{
        font-size: 1.35rem !important;
        color: var(--text-primary) !important;
    }}
    h3 {{
        font-size: 1.15rem !important;
        color: var(--text-primary) !important;
        margin-bottom: 0rem !important;
    }}

    /* ── Buttons ── */
    .stButton > button {{
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 1.4rem !important;
        transition: all 0.2s ease !important;
        border: none !important;
        letter-spacing: -0.01em;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 6px 28px rgba(99, 102, 241, 0.45);
        transform: translateY(-1px);
    }}
    .stButton > button[kind="secondary"] {{
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }}
    .stButton > button[kind="secondary"]:hover {{
        background: #2a2a3a !important;
        border-color: rgba(255,255,255,0.12) !important;
    }}
    [data-theme="light"] .stButton > button[kind="secondary"]:hover {{
        background: #e0e0eb !important;
    }}

    /* ── Metrics ── */
    [data-testid="stMetric"] {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.2rem 1.4rem !important;
        transition: all 0.2s ease;
    }}
    [data-testid="stMetric"]:hover {{
        border-color: rgba(99, 102, 241, 0.25);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }}
    [data-theme="light"] [data-testid="stMetric"]:hover {{
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
    }}
    [data-testid="stMetric"] label {{
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    [data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }}

    /* ── Expanders ── */
    .streamlit-expanderHeader {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }}
    .streamlit-expanderHeader:hover {{
        border-color: rgba(99, 102, 241, 0.25) !important;
    }}
    .streamlit-expanderContent {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
    }}

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {{
        border-radius: var(--radius-md) !important;
        overflow: hidden;
    }}
    [data-testid="stDataFrame"] table {{
        font-size: 0.85rem;
    }}
    [data-testid="stDataFrame"] th {{
        background: var(--bg-elevated) !important;
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {{
        border-radius: var(--radius-lg) !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 0.6rem !important;
    }}

    /* ── Chat input ── */
    [data-testid="stChatInput"] textarea {{
        border-radius: var(--radius-xl) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        font-size: 0.92rem !important;
        padding: 0.9rem 1.2rem !important;
        transition: all 0.2s ease;
    }}
    [data-testid="stChatInput"] textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft);
    }}

    /* ── Dividers ── */
    hr {{
        border-color: var(--border) !important;
        margin: 1.5rem 0 !important;
    }}

    /* ── Info/Warning/Error boxes ── */
    div[data-testid="stAlert"] {{
        border-radius: var(--radius-md) !important;
        border: none !important;
        font-size: 0.88rem;
    }}
    div[data-testid="stAlert"][kind="info"] {{
        background: rgba(99, 102, 241, 0.08) !important;
        border-left: 3px solid var(--accent) !important;
    }}
    div[data-testid="stAlert"][kind="warning"] {{
        background: rgba(251, 191, 36, 0.08) !important;
        border-left: 3px solid var(--warning) !important;
    }}
    div[data-testid="stAlert"][kind="error"] {{
        background: rgba(248, 113, 113, 0.08) !important;
        border-left: 3px solid var(--danger) !important;
    }}

    /* ── File uploader ── */
    [data-testid="stFileUploader"] section {{
        border: 2px dashed var(--border) !important;
        border-radius: var(--radius-lg) !important;
        background: var(--bg-card) !important;
        transition: all 0.2s ease;
        padding: 1.5rem !important;
    }}
    [data-testid="stFileUploader"] section:hover {{
        border-color: rgba(99, 102, 241, 0.3) !important;
        background: rgba(99, 102, 241, 0.03) !important;
    }}
    [data-testid="stFileUploader"] small {{
        color: var(--text-muted) !important;
    }}

    /* ── Code blocks (light mode background swap) ── */
    [data-theme="light"] .stCode,
    [data-theme="light"] .stCodeBlock {{
        background: #f5f5fa !important;
        border-color: rgba(0, 0, 0, 0.08) !important;
    }}

    /* ── Spinner ── */
    .stSpinner > div {{
        border-color: var(--accent) !important;
    }}

    /* ── Plotly charts ── */
    .js-plotly-plot {{
        border-radius: var(--radius-lg) !important;
        overflow: hidden;
    }}

    /* ── Smooth fade-in (scoped to hero and main content only) ── */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(12px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .hero-section, [data-testid="stMetric"] {{
        animation: fadeIn 0.5s ease-out;
    }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--bg-elevated); border-radius: 20px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #333344; }}

    /* ── Tooltip ── */
    .stTooltip {{
        font-size: 0.8rem;
    }}

    /* ── Keyboard shortcut hint ── */
    .kb-shortcut {{
        display: inline-block;
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 5px;
        padding: 2px 7px;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        font-family: 'Inter', monospace;
    }}

    /* ── Column type badges ── */
    .col-badge {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        margin: 0 4px 4px 0;
        font-weight: 600;
    }}
    .col-date {{ background: rgba(99, 102, 241, 0.12); color: var(--accent-hover); }}
    .col-numeric {{ background: rgba(52, 211, 153, 0.12); color: var(--success); }}
    .col-category {{ background: rgba(251, 191, 36, 0.12); color: var(--warning); }}
    .col-text {{ background: rgba(152, 152, 176, 0.12); color: var(--text-muted); }}

    /* ── Learn page: concept cards ── */
    .concept-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem 1.6rem;
        margin: 0.6rem 0;
        transition: all 0.2s ease;
    }}
    .concept-card:hover {{
        border-color: rgba(99, 102, 241, 0.25);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        transform: translateY(-2px);
    }}
    [data-theme="light"] .concept-card:hover {{
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    }}
    .concept-card .icon {{
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }}
    .concept-card h4 {{
        margin: 0 0 0.3rem 0;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-primary);
    }}
    .concept-card p {{
        color: var(--text-secondary);
        font-size: 0.82rem;
        line-height: 1.5;
        margin: 0;
    }}

    /* ── Learn page: section divider ── */
    .section-divider {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 2.5rem 0 1.5rem 0;
    }}
    .section-divider .line {{
        flex: 1;
        height: 1px;
        background: var(--border);
    }}
    .section-divider .label {{
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        white-space: nowrap;
    }}

    /* ── Learn page: file path badge ── */
    .file-badge {{
        display: inline-block;
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 6px;
        padding: 1px 8px;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--accent-hover);
        font-family: 'SF Mono', 'Fira Code', monospace;
        margin-left: 0.5rem;
    }}

    /* ── Learn page: tip box ── */
    .tip-box {{
        background: rgba(251, 191, 36, 0.06);
        border: 1px solid rgba(251, 191, 36, 0.12);
        border-left: 3px solid var(--warning);
        border-radius: 0 10px 10px 0;
        padding: 0.8rem 1.1rem;
        margin: 1rem 0;
        font-size: 0.82rem;
        color: var(--text-primary);
    }}
    .tip-box strong {{
        color: var(--warning);
    }}

    /* ── Learn page: tabs customization ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.3rem;
        background: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    .stTabs [aria-selected="true"] {{
        background: rgba(99, 102, 241, 0.12) !important;
    }}
</style>

<!-- Keyboard shortcuts + theme sync JS -->
<script>
(function() {{
    // ── Theme sync ──
    const themeEl = document.getElementById('theme-data');
    if (themeEl) {{
        document.documentElement.setAttribute('data-theme', themeEl.dataset.theme);
    }}

    // ── Keyboard shortcuts ──
    document.addEventListener('keydown', function(e) {{
        const isMac = /Mac/i.test(navigator.userAgentData?.platform || navigator.platform || '');
        const mod = isMac ? e.metaKey : e.ctrlKey;

        // Cmd/Ctrl + K → focus chat input
        if (mod && e.key === 'k') {{
            e.preventDefault();
            const chatInput = document.querySelector('[data-testid="stChatInput"] textarea');
            if (chatInput) {{ chatInput.focus(); }}
        }}
    }});
}})();
</script>
""",
        unsafe_allow_html=True,
    )
