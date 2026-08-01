"""Phase 0: Google Picker transport spike.

Proves — in real browser conditions with a live Streamlit session — that a
selected Google Picker file ID can reach Python reliably.

This module is DELETED after the Phase 0 gate decision. It never downloads
files, creates DataContexts, logs identifiers, or persists state.

Branch: spike/drive-picker-transport
Parent spec: plans/00-sprints/🔵 phase-0-drive-picker-spike-spec.md
"""

from __future__ import annotations

import json
import logging

import streamlit as st
import streamlit.components.v1 as components

from utils.ga4_client import credentials_from_dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JSON-safe HTML embedding
# ---------------------------------------------------------------------------


def _json_for_script(value: object) -> str:
    """Serialize a value for safe embedding in an HTML <script> element.

    ``json.dumps()`` handles JavaScript string escaping, but it does NOT prevent
    ``</script>`` from terminating the enclosing element.  We replace ``<`` with
    ``\\u003c`` to keep the JSON inert inside the script tag.
    """
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


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
# Picker iframe HTML
# ---------------------------------------------------------------------------

# flake8: noqa: E501 — long HTML template lines are intentional for readability

_PICKER_IFRAME_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0; padding: 10px; overflow: auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 12px; background: #1e1e2e; color: #cdd6f4;
  }}
  #status {{ padding: 8px; }}
  .ok {{ color: #a6e3a1; }}
  .err {{ color: #f38ba8; }}
  .info {{ color: #89b4fa; }}
</style>
</head>
<body>
<div id="status">
  <div>⚡ Diagnostics running&hellip;</div>
</div>

<script id="picker-config" type="application/json">{config_json}</script>
<script>
  // ── Diagnostics run FIRST (before gapi loads) ───────────────────────
  var status = document.getElementById("status");

  function log(msg, cls) {{
    var div = document.createElement("div");
    div.className = cls || "info";
    div.textContent = msg;
    status.appendChild(div);
  }}

  // Parse config (never string-interpolated into executable JS)
  var CONFIG;
  try {{
    CONFIG = JSON.parse(
      document.getElementById("picker-config").textContent
    );
    log("Config parsed: token length=" + (CONFIG.oauthToken || "").length);
  }} catch(e) {{
    log("Config parse FAILED: " + e.message, "err");
  }}

  // Compute origin
  var ORIGIN;
  try {{
    ORIGIN = window.top.location.origin;
    log("Origin (top): " + ORIGIN);
  }} catch(e) {{
    ORIGIN = window.location.origin;
    log("Origin (fallback): " + ORIGIN);
  }}

  // ── Google Picker callback ───────────────────────────────────────────
  function pickerCallback(data) {{
    if (data.action === google.picker.Action.PICKED && data.docs && data.docs.length > 0) {{
      var fileId = data.docs[0].id;
      log("PICKED: " + fileId, "ok");
      bridgeToStreamlit(fileId);
    }} else if (data.action === google.picker.Action.CANCEL) {{
      log("CANCELLED");
    }}
  }}

  // ── Option A: hidden-input bridge ────────────────────────────────────
  function bridgeToStreamlit(fileId) {{
    try {{
      var input = window.parent.document.querySelector(
        'input[aria-label="_drive_picker_bridge"]'
      );
      if (!input) {{
        log("bridge: input not found by aria-label, trying fallback", "err");
        input = window.parent.document.querySelector(
          'input[data-testid="stTextInput"][aria-label*="bridge"]'
        );
      }}
      if (!input) {{
        log("bridge: FAILED — no input found", "err");
        return;
      }}
      var setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, "value"
      ).set;
      setter.call(input, fileId);
      input.dispatchEvent(new Event("input", {{ bubbles: true }}));
      input.dispatchEvent(new Event("change", {{ bubbles: true }}));
      log("bridge: value dispatched", "ok");
    }} catch (e) {{
      log("bridge: CROSS-ORIGIN blocked — " + e.message, "err");
    }}
  }}

  // ── Picker initialisation ────────────────────────────────────────────
  function onPickerApiLoad() {{
    log("gapi loaded — building picker", "ok");
    try {{
      var view = new google.picker.DocsView(google.picker.ViewId.SPREADSHEETS)
        .setMimeTypes(
          "application/vnd.google-apps.spreadsheet," +
          "text/csv," +
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        );
      var picker = new google.picker.PickerBuilder()
        .setOAuthToken(CONFIG.oauthToken)
        .setDeveloperKey(CONFIG.apiKey)
        .setOrigin(ORIGIN)
        .addView(view)
        .setCallback(pickerCallback)
        .build();
      picker.setVisible(true);
      log("picker.setVisible(true) — look for file dialog", "ok");
    }} catch (e) {{
      log("Picker build FAILED: " + e.message, "err");
    }}
  }}

  // ── Load gapi dynamically (non-blocking) ─────────────────────────────
  log("Loading gapi from apis.google.com/js/api.js&hellip;");

  var script = document.createElement("script");
  script.src = "https://apis.google.com/js/api.js";
  script.onload = function() {{
    log("gapi script loaded, calling gapi.load('picker')&hellip;");
    try {{
      gapi.load("picker", {{ callback: onPickerApiLoad }});
    }} catch (e) {{
      log("gapi.load FAILED: " + e.message, "err");
    }}
  }};
  script.onerror = function() {{
    log("FAILED: could not load apis.google.com/js/api.js", "err");
  }};
  document.head.appendChild(script);

  // Safety timeout — if gapi never loads
  setTimeout(function() {{
    if (typeof gapi === "undefined") {{
      log("FAILED: gapi undefined after 5s — network/blocker issue?", "err");
    }}
  }}, 5000);
</script>
</body>
</html>"""


def _picker_iframe_html(oauth_token: str, api_key: str) -> str:
    """Build the Picker iframe HTML with JSON-safe config injection.

    The OAuth token and API key are embedded **only** in a
    ``<script type="application/json">`` element — never string-replaced
    into executable JavaScript.  ``_json_for_script()`` ensures ``</script>``
    cannot terminate the enclosing element.

    The origin expression is embedded directly (not JSON-wrapped) because
    it is a JavaScript IIFE — not a string value — that computes the
    browsing context origin at runtime.
    """
    config = {"oauthToken": oauth_token, "apiKey": api_key}
    config_json = _json_for_script(config)

    # Compute the top-level browsing context origin at runtime.
    # window.top may be denied by cross-origin/sandbox — that is a
    # Phase 0 finding recorded in the browser matrix.
    origin_js = (
        "(function(){try{return window.top.location.origin;}"
        "catch(e){return window.location.origin;}})()"
    )

    return _PICKER_IFRAME_HTML_TEMPLATE.format(
        config_json=config_json,
        origin_json=origin_js,
    )


# ---------------------------------------------------------------------------
# Main render entry-point
# ---------------------------------------------------------------------------


def render_drive_picker_spike() -> None:
    """Phase 0 transport experiment.  Proves a Picker file ID reaches Python.

    Guards:
    * No OAuth credentials → "Connect Google Analytics first" message.
    * Token missing ``drive.file`` → "Reconnect Google" message.
    * Explicit **Open Picker (spike)** button before any iframe is rendered.

    Success indication (minimal):
        ✓ Picker transport verified
        A selection event reached this Streamlit session.
        No file was downloaded, parsed, stored, or imported.

    No file download.  No DataContext.  No ingestion.  No persistent state.
    """
    theme = st.session_state.get("theme", "dark")
    section_color = "#1f2937" if theme == "light" else "#f0f0f5"

    st.markdown(
        f'<p style="font-size:0.8rem;font-weight:600;color:{section_color};'
        f'margin-bottom:0.3rem;">🧪 Drive Picker Spike (Phase 0)</p>',
        unsafe_allow_html=True,
    )

    # ── Success state (session-scoped only) ──────────────────────────────
    if st.session_state.get("_spike_success", False):
        st.success(
            "✓ Picker transport verified\n\n"
            "A selection event reached this Streamlit session.\n"
            "No file was downloaded, parsed, stored, or imported."
        )
        if st.button("🔄 Reset spike result", key="_spike_reset_btn"):
            st.session_state._spike_success = False
            st.session_state._drive_picker_active = False
            st.session_state["_drive_picker_bridge"] = ""
            st.rerun()
        return

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
    api_key = st.secrets.get("GOOGLE_PICKER_API_KEY", "")
    if not api_key:
        st.warning(
            "🔑 Missing `GOOGLE_PICKER_API_KEY` in `.streamlit/secrets.toml`.  "
            "See `.streamlit/secrets.example.toml` for setup instructions."
        )
        return

    # ── Hidden bridge input (must be on-screen before the iframe) ────────
    bridge_value = st.text_input(
        "",
        key="_drive_picker_bridge",
        label_visibility="collapsed",
        placeholder="_drive_picker_placeholder_",
    )

    # If the bridge received a value, transport succeeded.
    # On the next run the success branch renders (before this widget is
    # recreated), so no need to clear the bridge value here.
    if bridge_value and bridge_value != "_drive_picker_placeholder_":
        st.session_state._spike_success = True
        st.session_state._drive_picker_active = False
        st.rerun()

    # ── Open Picker button ───────────────────────────────────────────────
    if st.button("📂 Open Picker (spike)", type="primary", use_container_width=True):
        st.session_state._drive_picker_active = True

    if st.button(
        "✕ Cancel Drive import",
        type="secondary",
        use_container_width=True,
        key="_spike_cancel_btn",
    ):
        st.session_state._drive_picker_active = False
        st.rerun()

    # ── Render picker iframe (only after explicit button click) ──────────
    if st.session_state.get("_drive_picker_active", False):
        try:
            creds = credentials_from_dict(st.session_state.ga4_creds)
            oauth_token = creds.token
        except Exception:
            st.error("Could not read OAuth token. Please reconnect Google.")
            return

        st.caption(
            "📂 The Google Picker opens as a full-window overlay — "
            "look for the file selection dialog on your screen."
        )

        components.html(
            _picker_iframe_html(oauth_token=oauth_token, api_key=api_key),
            height=250,
            scrolling=True,
        )
