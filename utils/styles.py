"""Custom CSS, JS, and favicon injection for the GA4 Insight Explorer UI.

v0.2.0 refactor:
    - Monolithic f-string replaced by 5 CSS + 1 JS named constants.
    - Focus-visible styles use semantic --focus-ring-* variables (never red).
    - build_theme_css() assembles constants; only the validated theme value
      is interpolated.
"""

import streamlit as st

# ── Valid theme names ────────────────────────────────────────────────────────
VALID_THEMES = {"dark", "light"}

# ═══════════════════════════════════════════════════════════════════════════════
# CSS Constants
# ═══════════════════════════════════════════════════════════════════════════════

BASE_TOKENS_CSS = """
    /* ── System font stack (no external Google Fonts dependency) ── */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        color: var(--text-primary);
        -webkit-font-smoothing: antialiased;
    }

    /* ── CSS variables — dark theme (default) ── */
    :root {
        --bg-primary: #0e0e16;
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
        /* Focus ring — aliased from accent, never red/destructive */
        --focus-ring-color: var(--accent);
        --focus-ring-soft: var(--accent-soft);
        --focus-ring-width: 2px;
        --focus-ring-offset: 2px;
    }
"""

LIGHT_THEME_CSS = """
    /* ── Light theme variable overrides ── */
    [data-theme="light"] {
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
        /* Light-mode semantic tokens (B2a consolidation — no raw hexes at
           usage sites; only these definitions may hold literal values) */
        --hover: #e5e7eb;
        --code-bg: #f5f5fa;
        --code-inline-bg: #f3f4f6;
        --scroll-thumb: #d1d5db;
        --scroll-thumb-hover: #9ca3af;
    }

    /* ── Light theme: App background ── */
    [data-theme="light"] .stApp {
        background: var(--bg-primary) !important;
    }
    [data-theme="light"] .main .block-container {
        background: var(--bg-primary) !important;
    }

    /* ── Light theme: Sidebar ── */
    [data-theme="light"] [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-theme="light"] [data-testid="stSidebar"] .stMarkdown h1 {
        color: var(--text-primary) !important;
    }
    [data-theme="light"] [data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-secondary) !important;
    }

    /* ── Light theme: Text colors ── */
    [data-theme="light"] h1, [data-theme="light"] h2, [data-theme="light"] h3 {
        color: var(--text-primary) !important;
    }
    /* Blanket p/span/div rule removed (B2e): it could override intended
       muted text app-wide. Scoped to .stMarkdown containers — children
       inherit; paragraphs stay secondary via the rule below. */
    [data-theme="light"] .stMarkdown {
        color: var(--text-primary);
    }
    [data-theme="light"] .stMarkdown p {
        color: var(--text-secondary) !important;
    }
    [data-theme="light"] .stCaption {
        color: var(--text-muted) !important;
    }

    /* ── Light theme: Buttons ── */
    [data-theme="light"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
    }
    [data-theme="light"] .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
        transform: translateY(-1px);
    }
    [data-theme="light"] .stButton > button[kind="secondary"] {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    [data-theme="light"] .stButton > button[kind="secondary"]:hover {
        background: var(--hover) !important;
        border-color: rgba(0, 0, 0, 0.15) !important;
    }
    /* ── Light theme: Metrics ── */
    [data-theme="light"] [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    [data-theme="light"] [data-testid="stMetric"]:hover {
        border-color: rgba(79, 70, 229, 0.3);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    [data-theme="light"] [data-testid="stMetric"] label {
        color: var(--text-muted) !important;
    }
    [data-theme="light"] [data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
    }
    [data-theme="light"] [data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        color: var(--text-secondary) !important;
    }

    /* ── Light theme: Expanders ── */
    [data-theme="light"] .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }
    [data-theme="light"] .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
    }

    /* ── Light theme: DataFrames ── */
    [data-theme="light"] [data-testid="stDataFrame"] th {
        background: var(--bg-elevated) !important;
        color: var(--text-secondary) !important;
    }
    [data-theme="light"] [data-testid="stDataFrame"] td {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
    }
    [data-theme="light"] [data-testid="stDataFrame"] tr:hover td {
        background: var(--bg-elevated) !important;
    }

    /* ── Light theme: Chat messages ── */
    [data-theme="light"] [data-testid="stChatMessage"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
    }
    [data-theme="light"] [data-testid="stChatMessage"] p {
        color: var(--text-primary) !important;
    }
    [data-theme="light"] [data-testid="stChatMessage"] .stMarkdown p {
        color: var(--text-primary) !important;
    }

    /* ── Light theme: Chat input ── */
    [data-theme="light"] [data-testid="stChatInput"] textarea {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }
    [data-theme="light"] [data-testid="stChatInput"] textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft);
    }
    [data-theme="light"] [data-testid="stChatInput"] textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* ── Light theme: Alerts ── */
    [data-theme="light"] div[data-testid="stAlert"][kind="info"] {
        background: rgba(79, 70, 229, 0.06) !important;
        color: var(--text-primary) !important;
    }
    [data-theme="light"] div[data-testid="stAlert"][kind="warning"] {
        background: rgba(217, 119, 6, 0.06) !important;
        color: var(--text-primary) !important;
    }
    [data-theme="light"] div[data-testid="stAlert"][kind="error"] {
        background: rgba(220, 38, 38, 0.06) !important;
        color: var(--text-primary) !important;
    }
    [data-theme="light"] div[data-testid="stAlert"][kind="success"] {
        background: rgba(5, 150, 105, 0.06) !important;
        color: var(--text-primary) !important;
    }

    /* ── Light theme: File uploader ── */
    [data-theme="light"] [data-testid="stFileUploader"] section {
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
    }
    [data-theme="light"] [data-testid="stFileUploader"] section:hover {
        border-color: rgba(79, 70, 229, 0.3) !important;
        background: rgba(79, 70, 229, 0.02) !important;
    }

    /* ── Light theme: Select boxes and inputs ── */
    [data-theme="light"] .stSelectbox [data-baseweb="select"] {
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
    }
    [data-theme="light"] .stTextInput input {
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
    }
    [data-theme="light"] .stTextInput input::placeholder {
        color: var(--text-muted) !important;
    }
    [data-theme="light"] .stTextArea textarea {
        background: var(--bg-card) !important;
        border-color: var(--border) !important;
        color: var(--text-primary) !important;
    }

    /* ── Light theme: Tabs ── */
    [data-theme="light"] .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
    }
    [data-theme="light"] .stTabs [aria-selected="true"] {
        background: rgba(79, 70, 229, 0.1) !important;
        color: var(--accent) !important;
    }
    [data-theme="light"] .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-elevated) !important;
    }

    /* ── Light theme: Dividers ── */
    [data-theme="light"] hr {
        border-color: var(--border) !important;
    }

    /* ── Light theme: Header gradient ── */
    [data-theme="light"] h1 {
        background: linear-gradient(135deg, #6366f1, #4f46e5, #3730a3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ── Light theme: Hero title gradient (A1) — darker indigo on white ──
       The background shorthand resets background-clip to border-box, so
       the clip + fill MUST be re-declared after it (same pattern as the
       [data-theme="light"] h1 rule) or the gradient paints a full box
       behind invisible text. */
    [data-theme="light"] .hero-title {
        background: linear-gradient(135deg, #6366f1, #4f46e5, #3730a3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ── Light theme: Metric hover shadow ── */
    [data-theme="light"] [data-testid="stMetric"]:hover {
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
    }

    /* ── Light theme: Secondary button hover ── */
    [data-theme="light"] .stButton > button[kind="secondary"]:hover {
        background: var(--hover) !important;
    }

    /* ── Light theme: Code blocks ── */
    [data-theme="light"] .stCode,
    [data-theme="light"] .stCodeBlock {
        background: var(--code-bg) !important;
        border-color: rgba(0, 0, 0, 0.08) !important;
    }
    [data-theme="light"] code {
        background: var(--code-inline-bg) !important;
        color: var(--text-primary) !important;
    }

    /* ── Light theme: Scrollbar ── */
    [data-theme="light"] ::-webkit-scrollbar-thumb {
        background: var(--scroll-thumb);
    }
    [data-theme="light"] ::-webkit-scrollbar-thumb:hover {
        background: var(--scroll-thumb-hover);
    }

    /* ── Light theme: Tooltips ── */
    [data-theme="light"] .stTooltip {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }

    /* ── Light theme: Learn page cards ── */
    [data-theme="light"] .concept-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
    }
    [data-theme="light"] .concept-card h4 {
        color: var(--text-primary);
    }
    [data-theme="light"] .concept-card p {
        color: var(--text-secondary);
    }
    [data-theme="light"] .concept-card:hover {
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    }

    /* ── Light theme: Tip box ── */
    [data-theme="light"] .tip-box {
        background: rgba(217, 119, 6, 0.05);
        border-color: rgba(217, 119, 6, 0.15);
        color: var(--text-primary);
    }

    /* ── Light theme: Dialog (B6) ── */
    [data-theme="light"] [data-testid="stDialog"] section[role="dialog"] {
        background: var(--bg-card);
        color: var(--text-primary);
        border: 1px solid var(--border);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.15);
    }
    [data-theme="light"] [data-testid="stDialog"] h2 {
        color: var(--text-primary) !important;
    }
    [data-theme="light"] [data-testid="stDialog"] .stMarkdown p,
    [data-theme="light"] [data-testid="stDialog"] .stCaption {
        color: var(--text-secondary) !important;
    }
    [data-theme="light"] [data-testid="stDialog"] button[aria-label="Close"] {
        color: var(--text-secondary) !important;
    }
    [data-theme="light"] [data-testid="stDialog"] button[aria-label="Close"]:hover {
        color: var(--text-primary) !important;
    }
"""

COMPONENT_CSS = """
    .stApp {
        background: var(--bg-primary);
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

    /* ── Hero / empty state (interstitial PR-L3, A1) ──
       Token-based: surfaces resolve correctly in both themes. The hero
       title gradient is the only raw-hex value; light-mode override in
       LIGHT_THEME_CSS provides the darker indigo gradient for white bg. */
    .hero-section {
        text-align: center;
        padding: 3rem 2rem;
    }
    .hero-emoji {
        font-size: 4rem;
        margin-bottom: 1rem;
        filter: drop-shadow(0 8px 24px rgba(99, 102, 241, 0.3));
    }
    .hero-title {
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #c4b5fd, #818cf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    .hero-cards {
        display: flex;
        gap: 1.5rem;
        justify-content: center;
        flex-wrap: wrap;
    }
    .hero-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        min-width: 140px;
    }
    .hero-card-icon {
        font-size: 1.6rem;
        margin-bottom: 0.3rem;
    }
    .hero-card-title {
        font-weight: 600;
        font-size: 0.85rem;
        color: var(--text-primary);
    }
    .hero-card-caption {
        font-size: 0.72rem;
        color: var(--text-muted);
    }
    .hero-hint {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.85rem;
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

    /* ── Privacy card (interstitial PR-L2, B2d) ──
       Replaces the inline theme-branched rgba from the sidebar; tokens
       resolve correctly in both themes. */
    .privacy-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin: 0.5rem 0;
    }
    .privacy-card-text {
        font-size: 0.78rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }

    /* ── Dialog (Drive Picker — interstitial PR 2, B6) ──
       Streamlit's st.dialog Paper carries no [theme] config defaults, so
       the surface is themed explicitly here. The X button uses
       currentColor — override it or it disappears on dark cards. */
    [data-testid="stDialog"] section[role="dialog"] {
        background: var(--bg-card);
        color: var(--text-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.5);
    }
    [data-testid="stDialog"] h2 {
        color: var(--text-primary) !important;
    }
    [data-testid="stDialog"] .stMarkdown p,
    [data-testid="stDialog"] .stCaption {
        color: var(--text-secondary) !important;
    }
    [data-testid="stDialog"] button[aria-label="Close"] {
        color: var(--text-secondary) !important;
    }
    [data-testid="stDialog"] button[aria-label="Close"]:hover {
        color: var(--text-primary) !important;
    }

    /* ── Column type badges ── */
    .col-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        margin: 0 4px 4px 0;
        font-weight: 600;
    }
    .col-date { background: rgba(99, 102, 241, 0.12); color: var(--accent-hover); }
    .col-numeric { background: rgba(52, 211, 153, 0.12); color: var(--success); }
    .col-category { background: rgba(251, 191, 36, 0.12); color: var(--warning); }
    .col-text { background: rgba(152, 152, 176, 0.12); color: var(--text-muted); }
"""

LEARN_PAGE_CSS = """
    /* ── Learn page: concept cards ── */
    .concept-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem 1.6rem;
        margin: 0.6rem 0;
        transition: all 0.2s ease;
    }
    .concept-card:hover {
        border-color: rgba(99, 102, 241, 0.25);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        transform: translateY(-2px);
    }
    .concept-card .icon {
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    .concept-card h4 {
        margin: 0 0 0.3rem 0;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .concept-card p {
        color: var(--text-secondary);
        font-size: 0.82rem;
        line-height: 1.5;
        margin: 0;
    }

    /* ── Learn page: section divider ── */
    .section-divider {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 2.5rem 0 1.5rem 0;
    }
    .section-divider .line {
        flex: 1;
        height: 1px;
        background: var(--border);
    }
    .section-divider .label {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        white-space: nowrap;
    }

    /* ── Learn page: file path badge ── */
    .file-badge {
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
    }

    /* ── Learn page: tip box ── */
    .tip-box {
        background: rgba(251, 191, 36, 0.06);
        border: 1px solid rgba(251, 191, 36, 0.12);
        border-left: 3px solid var(--warning);
        border-radius: 0 10px 10px 0;
        padding: 0.8rem 1.1rem;
        margin: 1rem 0;
        font-size: 0.82rem;
        color: var(--text-primary);
    }
    .tip-box strong {
        color: var(--warning);
    }
"""

ACCESSIBILITY_CSS = """
    /* ── Reduced motion support ── */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
        }
    }

    /* ── Focus-visible ring ──
       Uses accent-derived variables (never red/destructive).  Applied to all
       interactive elements: links, buttons, inputs, textareas, selects,
       expanders, tabs, and custom controls.
       Never suppressed with outline: none unless an equally visible
       replacement is applied. */
    :focus-visible {
        outline: var(--focus-ring-width) solid var(--focus-ring-color);
        outline-offset: var(--focus-ring-offset);
    }
"""

# ═══════════════════════════════════════════════════════════════════════════════
# JS Constants
# ═══════════════════════════════════════════════════════════════════════════════

THEME_SYNC_JS = """
    // ── Theme sync: apply theme directly (avoids duplicate-ID bug from st.rerun) ──
    (function applyTheme() {
        const attr = 'data-theme';
        const root = document.documentElement;
        // Read from the *last* #theme-data element (Streamlit appends, doesn't replace)
        const all = document.querySelectorAll('#theme-data');
        const el = all[all.length - 1];
        if (el && el.dataset.theme) {
            root.setAttribute(attr, el.dataset.theme);
        }
    })();
"""

# ═══════════════════════════════════════════════════════════════════════════════
# Assembly
# ═══════════════════════════════════════════════════════════════════════════════


def build_theme_css(theme: str) -> str:
    """Assemble CSS + JS constants for the given theme.

    Only the validated theme value is interpolated — no other dynamic content
    enters the generated HTML/CSS/JS output.

    Args:
        theme: \"dark\" or \"light\". Raises ValueError for unknown values.
    """
    if theme not in VALID_THEMES:
        raise ValueError(f"Unknown theme '{theme}'. Valid themes: {sorted(VALID_THEMES)}")
    bg_color = "#0e0e16" if theme == "dark" else "#ffffff"
    theme_div = f'<div id="theme-data" data-theme="{theme}" style="display:none;"></div>'
    # Preemptive style prevents white flash (FOUC) before CSS variables load.
    preemptive = (
        f"<style>"
        f"html{{background:{bg_color}!important}}"
        f"body{{background:{bg_color}!important}}"
        f".stApp{{background:{bg_color}!important}}"
        f"</style>"
    )
    return (
        f"{preemptive}\n"
        f"{theme_div}\n"
        f"<style>\n"
        f"{BASE_TOKENS_CSS}\n"
        f"{LIGHT_THEME_CSS}\n"
        f"{COMPONENT_CSS}\n"
        f"{LEARN_PAGE_CSS}\n"
        f"{ACCESSIBILITY_CSS}\n"
        f"</style>\n"
        f"<script>\n"
        f"{THEME_SYNC_JS}\n"
        f"</script>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Public injection functions (backward-compatible signatures)
# ═══════════════════════════════════════════════════════════════════════════════


def inject_favicon_meta(theme: str = "dark") -> None:
    """Inject favicon, Apple Touch Icon, and Open Graph meta tags into the page head.

    Args:
        theme: \"dark\" (default) or \"light\". Controls the theme-color meta tag.
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
    <meta property="og:description" content="Analyze GA4 data with natural language -- powered by Gemini AI">
    <meta property="og:image" content="/assets/og-image.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    """,
        unsafe_allow_html=True,
    )


def inject_custom_css(theme: str = "dark") -> None:
    """Inject the app's custom CSS theme and theme-sync JS.

    Uses ``st.html()`` (Streamlit 1.33+; the ``unsafe_allow_javascript``
    flag needs >=1.52 — verified against the streamlit GitHub tags) so the
    theme is fully replaced on every render.
    ``st.markdown(unsafe_allow_html=True)`` can silently skip replacement
    on ``st.rerun()`` when the container position matches.

    ``unsafe_allow_javascript=True`` is REQUIRED: ``st.html`` ignores
    inline ``<script>`` tags by default, so without it ``THEME_SYNC_JS``
    never executes and ``data-theme`` never reaches ``<html>`` — leaving
    every ``[data-theme="light"]`` rule inert (only the preemptive
    ``html/body/.stApp`` background flipped on toggle).

    Security: the payload is ``build_theme_css(theme)`` — static
    app-owned constants with only the validated theme value interpolated;
    no user input ever reaches this HTML.

    Args:
        theme: "dark" (default) or "light". Sets data-theme on the
            document element via a hidden div + JS snippet.
            Raises ValueError for unknown theme values.
    """
    st.html(build_theme_css(theme), unsafe_allow_javascript=True)
