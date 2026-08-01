# Phase 0 Spike — Debugging Summary

> **Branch:** `spike/drive-picker-transport` (last commit `4e9ebd9`)
> **Goal:** Prove Google Picker can deliver a selected file ID from an iframe back to Streamlit Python via a hidden-input DOM bridge (Option A).

---

## Architecture

```
User clicks "Open Picker (spike)" in sidebar
  ↓
Python renders `components.html()` iframe containing:
  - OAuth token + API key injected as `var CONFIG = {...}` (via `_json_for_script()`)
  - Google Picker initialized with `gapi.load('picker', ...)`
  - On file selection: `bridgeToStreamlit(fileId)` finds parent DOM's
    `input[aria-label="_drive_picker_bridge"]` and dispatches value events
  ↓
Streamlit detects the hidden `st.text_input(key="_drive_picker_bridge")` change
  ↓
Python reads value → shows "✓ Picker transport verified"
```

---

## Three bugs found and fixed

### Bug 1: `StreamlitAPIException` on Cancel

**Symptom:** Red error page when clicking "Cancel Drive import".

**Root cause:** `st.session_state["_drive_picker_bridge"] = ""` was called AFTER
`st.text_input(key="_drive_picker_bridge")` widget had already been created.
Streamlit blocks mutation of widget-owned state keys in the same run.

**Fix:** Removed direct state-clearing after widget creation. The success branch
renders before the widget on next run, so no explicit clear is needed.

---

### Bug 2: Script stuck at "Diagnostics running…" — config injection

**Symptom:** The diagnostic iframe showed "⚡ Diagnostics running…" but no
subsequent log lines appeared. A minimal HELLO sanity-test iframe confirmed
JavaScript execution works fine in Streamlit iframes — the bug was specific
to the Picker template.

**Root cause:** Multiple issues interacting:

1. The `<script src="https://apis.google.com/js/api.js">` tag was **synchronous**
   (no `async`/`defer`), blocking all subsequent inline scripts if the Google CDN
   hung or loaded slowly.

2. The OAuth token + API key were embedded inside a `<script type="application/json">`
   element. HTML script-content parsing interacted badly with the real OAuth token
   when placed in Streamlit's `srcdoc` iframe attribute.

3. Python's `.format()` with `{{`/`}}` escaping added unnecessary complexity that
   could interact with special characters in tokens.

**Fixes applied:**

- Switched from synchronous `<script src>` to dynamic `document.createElement("script")`
  loading (via `script.onload` / `script.onerror`).
- Changed config injection from `<script type="application/json">content</script>` to
  direct JavaScript variable assignment: `var CONFIG = {...}`.
- Switched from Python `.format()` to `.replace("__CONFIG_JSON__", ...)` —
  eliminates all `{{`/`}}` escaping and prevents token characters from interacting
  with string formatting.
- Added top-level `try/catch` around the entire inline script so any JavaScript
  error is displayed in red instead of a silent hang.

---

### Bug 3: `status.appendChild is not a function`

**Symptom:** The try/catch revealed `SCRIPT ERROR: status.appendChild is not a function`.

**Root cause:** `status` is `window.status`, a read-only browser built-in property
that silently refuses reassignment. `var status = document.getElementById("status")`
failed silently, leaving `status` as the empty string `""`. Strings don't have
`appendChild`.

**Fix:** Renamed variable to `statusEl`.

---

## Current state (ready to test)

The diagnostic iframe now shows a live status log:

```
⚡ Diagnostics running…
Config parsed: token length=…
Origin (top/fallback): http://localhost:8501
Loading gapi from apis.google.com/js/api.js…
```

Then one of:
- ✅ `gapi script loaded` → `gapi loaded — building picker` → `picker.setVisible(true)`
- ❌ `FAILED: could not load apis.google.com/js/api.js`
- ❌ `FAILED: gapi undefined after 5s`

The hidden-input bridge JS uses `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set`
+ `dispatchEvent(new Event("input"/"change"))` to programmatically set the Streamlit
text input from the iframe — this is the **Option A experiment** being tested.

## Next test

1. Hard-refresh browser (Cmd+Shift+R) at `http://localhost:8501`
2. Connect GA4 (the app reuses existing OAuth with `drive.file` scope)
3. Click "📂 Open Picker (spike)"
4. Observe diagnostic output in the 250px iframe panel
5. If `picker.setVisible(true)` appears → look for the Google Picker file dialog
   opening as a full-window overlay (not inside the iframe)
6. Select a file → the bridge should deliver the file ID to Streamlit → expect
   "✓ Picker transport verified"

## Prerequisites

- `.streamlit/secrets.toml` (gitignored, local only):
  ```toml
  PHASE_0_DRIVE_PICKER_SPIKE = true
  GOOGLE_PICKER_API_KEY = "API key restricted to Picker API + http://localhost:8501/*"
  ```
- Google Picker API enabled in GCP Console
- OAuth consent screen declares `drive.file` scope
- Test account listed under Test users if app is in Testing mode
