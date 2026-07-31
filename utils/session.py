"""Shared session state management — extracted from app.py."""

import streamlit as st


def clear_data() -> None:
    """Wipe all analysis session state. Does not touch auth/GA4 credentials.

    Called from: sidebar.py (Clear Data button), sidebar.py (GA4 disconnect),
    and sidebar.py (file processing — new file replaces old data).

    v0.2.0 Phase 1 Step 4: DataContext is the sole owner of loaded, filtered,
    and custom-metric state. Legacy data keys (df, filtered_df, custom_metrics_df,
    filters_active) are retired.
    """
    st.session_state.data_context = None
    st.session_state.stats = None
    st.session_state.summary = None
    st.session_state.quality_report = None
    st.session_state.chat_history = []
    st.session_state.missing_columns = []
    st.session_state.data_cleared = True
    st.session_state.data_source = None
    st.session_state.last_file_id = None
    # Reset tour so Quick Tour button reappears on empty state

    # Reset custom metrics so stale derived columns don't persist
    st.session_state.custom_metrics = {}
    # Purge stale forecast keys to prevent session state bloat
    for key in list(st.session_state.keys()):
        if key.startswith("forecast_"):
            del st.session_state[key]
    # Reset funnel state so stale steps don't persist across data loads
    st.session_state.funnel_steps = []
    st.session_state.funnel_data = None
