"""AI Summary section — summary card + generate button."""

from typing import Any
import pandas as pd
import streamlit as st
from utils.prompt_templates import build_summary_prompt
from utils.gemini_client import DEFAULT_MODEL, generate_response
from utils.session import streamlit_usage_sink


def render_summary_section() -> None:
    """Render the AI-generated summary card and generate button."""
    ctx = st.session_state.get("data_context")
    df = ctx.active_df if ctx else None
    stats = st.session_state.stats

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


def _generate_summary(df: pd.DataFrame, stats: dict[str, Any]) -> None:
    """Callback for the Generate Summary button.

    Includes quality_report from session state to give Gemini richer context
    about data issues (missing columns, outliers, gaps).
    """
    try:
        model = st.session_state.get("selected_model", DEFAULT_MODEL)
        summary_prompt = build_summary_prompt(
            df,
            stats,
            quality_report=st.session_state.get("quality_report"),
        )
        st.session_state.summary = generate_response(
            summary_prompt, model=model, request_type="summary", usage_sink=streamlit_usage_sink
        )
    except ValueError as e:
        st.error(f"🔑 Configuration error: {e}")
    except RuntimeError as e:
        st.error(f"⚠️ API error: {e}")
