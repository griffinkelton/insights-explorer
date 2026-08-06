"""
STREAMLIT-ONLY MODULE.

This module is part of the legacy Streamlit presentation layer.
FastAPI services and framework-neutral utils must not import it.

Migration owner: Phase 6 retirement.
"""

import streamlit as st

from utils.gemini_client import UsageEvent


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


def streamlit_usage_sink(event: UsageEvent) -> None:
    """STREAMLIT-ONLY sink — preserves pre-refactor session accounting.

    Phase 2 (spec Task 5): the shared Gemini client emits UsageEvents; the
    Streamlit layer owns the session-state accumulation. Net behavior is
    identical to the pre-refactor _track_usage writes.
    """
    for key, value in [
        ("total_input_tokens", event.input_tokens),
        ("total_output_tokens", event.output_tokens),
        ("total_thought_tokens", event.thoughts_token_count),
        ("total_cached_tokens", event.cached_token_count),
        ("total_tokens_used", event.total_token_count),  # provider total (review fix)
    ]:
        if key not in st.session_state:
            st.session_state[key] = 0
        st.session_state[key] += value
    if event.success:  # review fix: only successful requests count (errors may
        # emit usage events later; they must not inflate the success counter)
        if "api_success_count" not in st.session_state:
            st.session_state.api_success_count = 0
        st.session_state.api_success_count += 1
    history = st.session_state.get("chat_history", [])
    if history and "usage" not in history[-1]:
        history[-1]["usage"] = {
            "prompt_tokens": event.input_tokens,
            "output_tokens": event.output_tokens,
            "thought_tokens": event.thoughts_token_count,
            "cached_tokens": event.cached_token_count,
            "tool_tokens": event.tool_use_token_count,
            "total_tokens": event.total_token_count,
        }
