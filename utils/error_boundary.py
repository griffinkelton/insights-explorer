"""Global error boundary — renders friendly error cards instead of tracebacks."""

import traceback
import streamlit as st


def render_error_card(error: Exception, context: str = "") -> None:
    """Display a user-friendly error card with optional technical details.

    Args:
        error: The exception that was raised.
        context: Optional description of what was happening (e.g., "loading file").
    """
    error_type = type(error).__name__

    st.error(
        f"### 😣 Something went wrong"
        + (f" while {context}" if context else "")
        + f"\n\n**{error_type}:** {error}"
    )

    with st.expander("🔧 Technical Details", expanded=False):
        st.markdown("#### Stack Trace")
        st.code(traceback.format_exc(), language="python")
        st.caption(
            "If this persists, check your configuration or "
            "[open an issue](https://github.com/griffinkelton/insights-explorer/issues)."
        )
