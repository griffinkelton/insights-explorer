"""Shared session state management — extracted from app.py."""

import streamlit as st


def clear_data() -> None:
    """Wipe all analysis session state. Does not touch auth/GA4 credentials.

    Called from: sidebar.py (Clear Data button), sidebar.py (GA4 disconnect),
    and sidebar.py (file processing — new file replaces old data).
    """
    st.session_state.df = None
    st.session_state.stats = None
    st.session_state.summary = None
    st.session_state.quality_report = None
    st.session_state.chat_history = []
    st.session_state.missing_columns = []
    st.session_state.data_cleared = True
    st.session_state.data_source = None
