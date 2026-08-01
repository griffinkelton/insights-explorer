"""Declared Streamlit component for the Phase 0 Google Picker transport spike.

This is the Option-B replacement for the rejected
:func:`components.html` hidden-input bridge.  It uses Streamlit's
supported bidirectional component protocol: Python supplies arguments
(oauth_token, developer_key, app_id, app_origin, request_id), and the
frontend returns one sanitised event via ``Streamlit.setComponentValue()``.

Branch: spike/drive-picker-transport
Parent spec: plans/00-sprints/🔵 phase-0-drive-picker-spike-spec.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "drive_picker_component_frontend" / "build"

_component = components.declare_component(
    "drive_picker_transport",
    path=str(_FRONTEND_DIR),
)


def drive_picker_transport(
    *,
    oauth_token: str,
    developer_key: str,
    app_id: str,
    app_origin: str,
    request_id: str,
    key: str,
) -> dict[str, Any] | None:
    """Render the Picker transport component; return its sanitised event or ``None``.

    The frontend is only allowed to return:

    .. code-block:: json

        {"kind": "transport_verified", "requestId": "<current>"}

    The caller must validate ``kind`` and ``requestId`` before acting on
    the return value.  No file ID, filename, MIME type, OAuth token,
    API key, or raw error text is ever returned.
    """
    value = _component(
        oauthToken=oauth_token,
        developerKey=developer_key,
        appId=app_id,
        appOrigin=app_origin,
        requestId=request_id,
        key=key,
        default=None,
    )
    return value if isinstance(value, dict) else None
