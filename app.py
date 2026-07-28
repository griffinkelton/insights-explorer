"""GA4 Insight Explorer — Streamlit web app for analyzing GA4 export data with Gemini."""

import os
import streamlit as st
from utils.styles import inject_custom_css, inject_favicon_meta
from utils.gemini_client import validate_api_key
from components import render_all

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
inject_custom_css(theme=st.session_state.get("theme", "dark"))
inject_favicon_meta(theme=st.session_state.get("theme", "dark"))

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
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ── API key validation on first run ──────────────────────────────────────────
if st.session_state.api_key_valid is None:
    is_valid, msg = validate_api_key()
    st.session_state.api_key_valid = is_valid
    if not is_valid:
        st.session_state.api_key_error = msg

# ── API key banner (persistent, shows on every page if key is bad) ───────────
if st.session_state.api_key_valid is False:
    st.error(
        f"🔑 **Gemini API Key Issue** — "
        f"{st.session_state.get('api_key_error', 'Invalid key.')}"
    )
    st.caption(
        "[Get a free key → Google AI Studio](https://aistudio.google.com/apikey)"
    )

# ── Render all UI ────────────────────────────────────────────────────────────
render_all()
