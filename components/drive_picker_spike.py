"""Phase 0: Google Picker transport spike (Option B — declared component).

Proves — in real browser conditions with a live Streamlit session — that a
selected Google Picker file ID can reach Python reliably, using Streamlit's
supported bidirectional component protocol.

Option A (components.html + hidden-input bridge) was **rejected** after the
srcdoc iframe origin proved incompatible with Google Picker's origin
requirements.  See ``plans/00-sprints/🔵 phase-0-debug-summary.md``.

This module is DELETED after the Phase 0 gate decision. It never downloads
files, creates DataContexts, logs identifiers, or persists state.

Branch: spike/drive-picker-transport
Parent spec: plans/00-sprints/🔵 phase-0-drive-picker-spike-spec.md
"""

from __future__ import annotations

import logging
import secrets

import streamlit as st

from components.drive_picker_component import drive_picker_transport
from utils.ga4_client import credentials_from_dict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scope / credential helpers
# ---------------------------------------------------------------------------


def _token_has_drive_scope() -> bool:
    """True if the current GA4 credentials include the drive.file scope."""
    creds_dict = st.session_state.get("ga4_creds")
    if not creds_dict:
        return False
    try:
        creds = credentials_from_dict(creds_dict)
        granted = set(creds.scopes or [])
        return "https://www.googleapis.com/auth/drive.file" in granted
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main render entry-point
# ---------------------------------------------------------------------------


def render_drive_picker_spike() -> None:
    """Phase 0 transport experiment.  Proves a Picker file ID reaches Python.

    Option B uses a **declared Streamlit component** with the supported
    ``Streamlit.setComponentValue()`` return channel.  The frontend is a
    tiny TypeScript bundle at ``drive_picker_component_frontend/build/``.

    Guards:
    * No OAuth credentials → "Connect Google Analytics first" message.
    * Token missing ``drive.file`` → "Reconnect Google" message.
    * Missing API key → setup instructions.

    Success indication (minimal):
        ✓ Picker transport verified
        The component stays visible with the verified status and a reset button.

    No file download.  No DataContext.  No ingestion.  No persistent state.
    """
    theme = st.session_state.get("theme", "dark")
    section_color = "#1f2937" if theme == "light" else "#f0f0f5"

    st.markdown(
        f'<p style="font-size:0.8rem;font-weight:600;color:{section_color};'
        f'margin-bottom:0.3rem;">🧪 Drive Picker Spike (Phase 0)</p>',
        unsafe_allow_html=True,
    )

    verified = st.session_state.get("_spike_success", False)

    # ── Guard: credentials ───────────────────────────────────────────────
    if st.session_state.ga4_creds is None:
        st.info("🔐 Connect or reconnect Google Analytics first to test Drive Picker.")
        return

    if not _token_has_drive_scope():
        st.warning(
            "🔐 Reconnect Google to enable Drive import.  "
            "Your current credentials do not include the `drive.file` scope."
        )
        return

    # ── Guard: API key ───────────────────────────────────────────────────
    api_key: str = st.secrets.get("GOOGLE_PICKER_API_KEY", "")
    if not api_key:
        st.warning(
            "🔑 Missing `GOOGLE_PICKER_API_KEY` in `.streamlit/secrets.toml`.  "
            "See `.streamlit/secrets.example.toml` for setup instructions."
        )
        return

    # ── Resolve OAuth token ──────────────────────────────────────────────
    try:
        creds = credentials_from_dict(st.session_state.ga4_creds)
        oauth_token: str = creds.token
    except Exception:
        st.error("Could not read OAuth token. Please reconnect Google.")
        return

    # ── Compact success + reset (rendered inline, component stays below) ──
    if verified:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(
                "✓ Picker transport verified — "
                "no file was downloaded, parsed, stored, or imported."
            )
        with col2:
            if st.button("🔄 Reset", key="_spike_reset_btn", use_container_width=True):
                st.session_state._spike_success = False
                st.session_state.pop("_phase0_request_id", None)
                st.rerun()

    # ── Server-generated request ID (prevents stale/replay events) ───────
    request_id: str = st.session_state.setdefault("_phase0_request_id", secrets.token_urlsafe(16))

    # ── Declared component (replaces the rejected hidden-input bridge) ───
    result = drive_picker_transport(
        oauth_token=oauth_token,
        developer_key=api_key,
        app_id=st.secrets.get("GOOGLE_CLOUD_PROJECT_NUMBER", ""),
        app_origin="http://localhost:8501",
        request_id=request_id,
        key="phase0_drive_picker_component",
    )

    # ── Validate return: must be exact sanitised event ───────────────────
    if (
        not verified
        and isinstance(result, dict)
        and result.get("kind") == "transport_verified"
        and result.get("requestId") == request_id
    ):
        st.session_state._spike_success = True
        st.rerun()
