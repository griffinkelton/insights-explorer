"""Declared Streamlit component for v0.3.0 Drive import (Picker transport).

This is the Option-B component selected by Phase 0 — the replacement for
the rejected :func:`components.html` hidden-input bridge. It uses
Streamlit's supported bidirectional component protocol: Python supplies
arguments (oauth_token, dev_key, app_id, app_origin, request_id),
and the frontend returns one validated selection via
``Streamlit.setComponentValue()``.

The wrapper owns **schema validation**: it returns only allowlisted
shapes — ``PickerSelection`` (``kind: "picked"`` + ``requestId`` +
``fileId``) or ``CancelSelection`` (``kind: "cancel"`` + ``requestId``,
Workstream C PR 3/C1) — or ``None``. It never returns raw component
values, Picker metadata, tokens, or error text. The sidebar owns request
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
    """A validated file-selection payload the wrapper may return.

    ``kind`` is fixed to ``"picked"``; ``requestId`` is the server-side
    current-request token; ``fileId`` is the opaque Drive file ID.
    """

    kind: Literal["picked"]
    requestId: str
    fileId: str


class CancelSelection(TypedDict):
    """A validated cancel payload the wrapper may return (Workstream C/C1).

    Emitted by the component's Cancel button and on Picker-CANCEL. Carries
    only ``kind`` + ``requestId`` — never filename, MIME, URL, token, or
    raw callback data (A+C spec §5.4).
    """

    kind: Literal["cancel"]
    requestId: str


def drive_picker_transport(
    *,
    oauth_token: str,
    dev_key: str,
    app_id: str,
    app_origin: str,
    request_id: str,
    theme: str = "dark",
    key: str,
) -> PickerSelection | CancelSelection | None:
    """Render the declared component; return a validated payload or ``None``.

    The wrapper validates the raw component result and returns only
    allowlisted shapes: a ``PickerSelection`` (``picked`` + non-empty
    ``fileId``) or a ``CancelSelection`` (``cancel`` + non-empty
    ``requestId``) — ``None`` for ``None``, strings, lists, malformed
    dicts, unknown ``kind``, or missing/invalid required fields. It never
    returns Picker filenames, MIME types, URLs, raw callback objects,
    tokens, keys, or raw error text.
    """
    value = _component(
        oauthToken=oauth_token,
        developerKey=dev_key,
        appId=app_id,
        appOrigin=app_origin,
        requestId=request_id,
        theme=theme,
        key=key,
        default=None,
    )
    if (
        isinstance(value, dict)
        and value.get("kind") == "cancel"
        and isinstance(value.get("requestId"), str)
        and value["requestId"].strip()
    ):
        return {"kind": "cancel", "requestId": value["requestId"]}
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
