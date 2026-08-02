"""Declared Streamlit component for v0.3.0 Drive import (Picker transport).

This is the Option-B component selected by Phase 0 — the replacement for
the rejected :func:`components.html` hidden-input bridge. It uses
Streamlit's supported bidirectional component protocol: Python supplies
arguments (oauth_token, developer_key, app_id, app_origin, request_id),
and the frontend returns one validated selection via
``Streamlit.setComponentValue()``.

The wrapper owns **schema validation**: it returns only an allowlisted
``PickerSelection`` shape or ``None`` — never raw component values,
Picker metadata, tokens, or error text. The sidebar owns request
freshness (``requestId`` equality).

Parent specs: plans/00-sprints/🔵 v0.3.0-drive-import-spec.md (§3.3),
plans/00-sprints/✅ phase-0-drive-picker-spike-spec.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "drive_picker_component_frontend" / "build"

_component = components.declare_component(
    "drive_picker_transport",
    path=str(_FRONTEND_DIR),
)


class PickerSelection(TypedDict):
    """The only payload the wrapper will return to the sidebar.

    ``kind`` is fixed to ``"picked"``; ``requestId`` is the server-side
    current-request token; ``fileId`` is the opaque Drive file ID.
    """

    kind: Literal["picked"]
    requestId: str
    fileId: str


def drive_picker_transport(
    *,
    oauth_token: str,
    developer_key: str,
    app_id: str,
    app_origin: str,
    request_id: str,
    theme: str = "dark",
    key: str,
) -> PickerSelection | None:
    """Render the declared component; return a validated selection or ``None``.

    The wrapper validates the raw component result and returns only an
    allowlisted ``PickerSelection`` shape or ``None`` — ``None`` for
    ``None``, strings, lists, malformed dicts, wrong ``kind``, or
    ``picked`` without a non-empty ``fileId``. The wrapper returns only
    the minimum allowlisted selection payload to the sidebar. It never
    returns Picker filenames, MIME types, URLs, raw callback objects,
    tokens, keys, or raw error text.
    """
    value = _component(
        oauthToken=oauth_token,
        developerKey=developer_key,
        appId=app_id,
        appOrigin=app_origin,
        requestId=request_id,
        theme=theme,
        key=key,
        default=None,
    )
    if (
        isinstance(value, dict)
        and value.get("kind") == "picked"
        and isinstance(value.get("requestId"), str)
        and isinstance(value.get("fileId"), str)
        and value["fileId"]
    ):
        return {
            "kind": "picked",
            "requestId": value["requestId"],
            "fileId": value["fileId"],
        }
    return None
