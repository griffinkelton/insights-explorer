"""Global error boundary — renders friendly error cards instead of tracebacks."""

import logging
import os
import traceback
import uuid

import streamlit as st

SHOW_DEBUG_DETAILS = os.getenv("SHOW_DEBUG_DETAILS", "").lower() == "true"
logger = logging.getLogger(__name__)


def render_error_card(error: Exception, context: str = "") -> None:
    """Display a user-friendly error card with optional technical details.

    In production (SHOW_DEBUG_DETAILS=false), only a generic message and
    error reference ID are shown. Full tracebacks are logged server-side.

    Args:
        error: The exception that was raised.
        context: Optional description of what was happening (e.g., "loading file").
    """
    error_id = uuid.uuid4().hex[:8]
    logger.exception("Error %s while %s", error_id, context or "rendering")

    if SHOW_DEBUG_DETAILS:
        error_type = type(error).__name__
        st.error(
            "### 😣 Something went wrong"
            + (f" while {context}" if context else "")
            + f"\n\n**{error_type}:** {error}\n\nRef: `{error_id}`"
        )
        with st.expander("🔧 Technical Details", expanded=False):
            st.markdown("#### Stack Trace")
            st.code(traceback.format_exc(), language="python")
            st.caption(
                "If this persists, check your configuration or "
                "[open an issue](https://github.com/griffinkelton/insights-explorer/issues)."
            )
    else:
        st.error(
            "### 😣 Something went wrong"
            + (f" while {context}" if context else "")
            + f"\n\nPlease try again. If the problem persists, reference error ID `{error_id}`."
        )
