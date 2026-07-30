"""Custom CSS, JS, and favicon injection for the GA4 Insight Explorer UI."""

import streamlit as st

# Allowed theme values — validate before interpolation into HTML/CSS/JS templates.
VALID_THEMES = {"dark", "light"}


def inject_favicon_meta(theme: str = "dark") -> None:
    """Inject favicon, Apple Touch Icon, and Open Graph meta tags into the page head.

    Args:
        theme: "dark" (default) or "light". Controls the theme-color meta tag.
            Raises ValueError for unknown theme values.

    Call this once per page after st.set_page_config().

    Note: The HTML <link> tags here will 404 in local dev mode
    (streamlit run) because Streamlit doesn't serve arbitrary static
    files — only st.set_page_config(page_icon=...) works locally via
    base64 encoding. The HTML tags activate in production behind
    nginx, Cloud Run, or any proper static file server.
    """
    if theme not in VALID_THEMES:
        raise ValueError(f"Unknown theme '{theme}'. Valid themes: {sorted(VALID_THEMES)}")
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
            Raises ValueError for unknown theme values.
    """
    if theme not in VALID_THEMES:
        raise ValueError(f"Unknown theme '{theme}'. Valid themes: {sorted(VALID_THEMES)}")
    st.markdown(
        f"""<div id="theme-data" data-theme="{theme}" style="display:none;"></div>
<style>
    /* ── System font stack (no external Google Fonts dependency) ── */
    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        color: var(--text-primary);
        -webkit-font-smoothing: antialiased;
    }}

    /* ── Global resets & dark theme (default) ── */
    :root {{
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
        --bg-secondary: #f8f9fa;
        --bg-card: #ffffff;
        --bg-elevated: #f0f1f3;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --text-muted: #9ca3af;
        --accent: #4f46e5;
        --accent-hover: #6366f1;
        --accent-soft: rgba(79, 70, 229, 0.08);
        --success: #059669;
        --warning: #d97706;
        --danger: #dc2626;
        --border: rgba(0, 0, 0, 0.1);
    }}

    /* ── Light theme: App background ── */
    [data-theme="light"] .stApp {{
        background: var(--bg-primary) !important;
    }}
    [data-theme="light"] .main .block-container {{
        background: var(--bg-primary) !important;
    }}

    /* ── Light theme: Sidebar ── */
    [data-theme="light"] [data-testid="stSidebar"] {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }}
    [data-theme="light"] [data-testid="stSidebar"] .stMarkdown h1 {{
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] [data-testid="stSidebar"] .stMarkdown p {{
        color: var(--text-secondary) !important;
    }}

    /* ── Light theme: Text colors ── */
    [data-theme="light"] h1, [data-theme="light"] h2, [data-theme="light"] h3 {{
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] p, [data-theme="light"] span, [data-theme="light"] div {{
        color: var(--text-primary);
    }}
    [data-theme="light"] .stMarkdown p {{
        color: var(--text-secondary) !important;
    }}
    [data-theme="light"] .stCaption {{
        color: var(--text-muted) !important;
    }}

    /* ── Light theme: Buttons ── */
    [data-theme="light"] .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
    }}
    [data-theme="light"] .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
        transform: translateY(-1px);
    }}
    [data-theme="light"] .stButton > button[kind="secondary"] {{
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }}
    [data-theme="light"] .stButton > button[kind="secondary"]:hover {{
        background: #e5e7eb !important;
        border-color: rgba(0, 0, 0, 0.15) !important;
    }}

    /* ── Light theme: Metrics ── */
    [data-theme="light"] [data-testid="stMetric"] {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}
    [data-theme="light"] [data-testid="stMetric"]:hover {{
        border-color: rgba(79, 70, 229, 0.3);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }}
    [data-theme="light"] [data-testid="stMetric"] label {{
        color: var(--text-muted) !important;
    }}
    [data-theme="light"] [data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] [data-testid="stMetric"] div[data-testid="stMetricDelta"] {{
        color: var(--text-secondary) !important;
    }}

    /* ── Light theme: Expanders ── */
    [data-theme="light"] .streamlit-expanderHeader {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] .streamlit-expanderContent {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
    }}

    /* ── Light theme: DataFrames ── */
    [data-theme="light"] [data-testid="stDataFrame"] th {{
        background: var(--bg-elevated) !important;
        color: var(--text-secondary) !important;
    }}
    [data-theme="light"] [data-testid="stDataFrame"] td {{
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
    }}
    [data-theme="light"] [data-testid="stDataFrame"] tr:hover td {{
        background: var(--bg-elevated) !important;
    }}

    /* ── Light theme: Chat messages ── */
    [data-theme="light"] [data-testid="stChatMessage"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
    }}
    [data-theme="light"] [data-testid="stChatMessage"] p {{
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] [data-testid="stChatMessage"] .stMarkdown p {{
        color: var(--text-primary) !important;
    }}

    /* ── Light theme: Chat input ── */
    [data-theme="light"] [data-testid="stChatInput"] textarea {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] [data-testid="stChatInput"] textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft);
    }}
    [data-theme="light"] [data-testid="stChatInput"] textarea::placeholder {{
        color: var(--text-muted) !important;
    }}

    /* ── Light theme: Alerts ── */
    [data-theme="light"] div[data-testid="stAlert"][kind="info"] {{
        background: rgba(79, 70, 229, 0.06) !important;
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] div[data-testid="stAlert"][kind="warning"] {{
        background: rgba(217, 119, 6, 0.06) !important;
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] div[data-testid="stAlert"][kind="error"] {{
        background: rgba(220, 38, 38, 0.06) !important;
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] div[data-testid="stAlert"][kind="success"] {{
        background: rgba(5, 150, 105, 0.06) !important;
        color: var(--text-primary) !important;
    }}

    /* ── Light theme: File uploader ── */
    [data-theme="light"] [data-testid="stFileUploader"] section {{
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
    }}
    [data-theme="light"] [data-testid="stFileUploader"] section:hover {{
        border-color: rgba(79, 70, 229, 0.3) !important;
        background: rgba(79, 70, 229, 0.02) !important;
    }}

    /* ── Light theme: Select boxes and inputs ── */
    [data-theme="light"] .stSelectbox [data-baseweb="select"] {{
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] .stTextInput input {{
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
    }}
    [data-theme="light"] .stTextInput input::placeholder {{
        color: var(--text-muted) !important;
    }}
    [data-theme="light"] .stTextArea textarea {{
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
    }}

    /* ── Light theme: Tabs ── */
    [data-theme="light"] .stTabs [data-baseweb="tab"] {{
        color: var(--text-secondary) !important;
    }}
    [data-theme="light"] .stTabs [aria-selected="true"] {{
        background: rgba(79, 70, 229, 0.1) !important;
        color: var(--accent) !important;
    }}
    [data-theme="light"] .stTabs [data-baseweb="tab-list"] {{
        background: var(--bg-elevated) !important;
    }}

    /* ── Light theme: Dividers ── */
    [data-theme="light"] hr {{
        border-color: var(--border) !important;
    }}

    /* ── Light theme: Code blocks ── */
    [data-theme="light"] .stCode,
    [data-theme="light"] .stCodeBlock {{
        background: #f3f4f6 !important;
        border-color: var(--border) !important;
    }}
    [data-theme="light"] code {{
        background: #f3f4f6 !important;
        color: var(--text-primary) !important;
    }}

    /* ── Light theme: Scrollbar ── */
    [data-theme="light"] ::-webkit-scrollbar-thumb {{
        background: #d1d5db;
    }}
    [data-theme="light"] ::-webkit-scrollbar-thumb:hover {{
        background: #9ca3af;
    }}

    /* ── Light theme: Tooltips ── */
    [data-theme="light"] .stTooltip {{
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }}

    /* ── Light theme: Concept cards ── */
    [data-theme="light"] .concept-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
    }}
    [data-theme="light"] .concept-card h4 {{
        color: var(--text-primary);
    }}
    [data-theme="light"] .concept-card p {{
        color: var(--text-secondary);
    }}

    /* ── Light theme: Tip box ── */
    [data-theme="light"] .tip-box {{
        background: rgba(217, 119, 6, 0.05);
        border-color: rgba(217, 119, 6, 0.15);
        color: var(--text-primary);
    }}

    .stApp {{
        background: var(--bg-primary);
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

    /* ── Reduced motion support ── */
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
        }}
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
        // Guard against duplicate listener installation
        if (window.__ga4ExplorerShortcutInstalled) return;
        window.__ga4ExplorerShortcutInstalled = true;
        const isMac = /Mac/i.test(navigator.userAgentData?.platform || navigator.platform || '');
        const mod = isMac ? e.metaKey : e.ctrlKey;

        // Cmd/Ctrl + K → focus chat input
        if (mod && e.key === 'k') {{
            e.preventDefault();
            const chatInput = document.querySelector('[data-testid="stChatInput"] textarea');
            if (chatInput) {{ chatInput.focus(); }}
        }}
    }});
</script>
""",
        unsafe_allow_html=True,
    )
