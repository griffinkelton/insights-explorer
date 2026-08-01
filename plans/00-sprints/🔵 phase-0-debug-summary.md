# Phase 0 Spike — Debugging Summary

> **Branch:** `spike/drive-picker-transport` (last commit `d8dcaf9`)
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

### Bug 4 (UNRESOLVED): Google Picker returns 403 Forbidden

**Symptom:** The diagnostic iframe loads, the HELLO sanity test passes,
gapi loads successfully (`gapi script loaded` appears in the log),
but the Picker iframe displays a Google-branded **403 error page**:
"403. That's an error. We're sorry, but you do not have access to this page."
The 403 page replaces the diagnostic output, so the Origin line and
subsequent logs are not visible.

**What this means:** The JavaScript is executing correctly now (all three
code bugs are fixed). The Google Picker API call itself is being rejected
by Google's servers. This is a GCP configuration issue, not a code bug.

**API key configuration on file:**
- Key is restricted to **Google Picker API** only (correct)
- HTTP referrer restriction: `http://localhost:8501/*` and `http://127.0.0.1:8501/*` (added after initial 403)
- The `*` wildcard was initially missing from localhost — now present
- User saved the changes but propagation may take 2–5 minutes

**Possible remaining causes:**
1. **Google Picker API not enabled** — The Picker API is separate from the
   Drive API. Even with a key restricted to it, the API must be explicitly
   enabled in **APIs & Services → Library → Google Picker API**.
2. **API key propagation delay** — Changes can take up to 5 minutes to
   propagate across Google's infrastructure.
3. **Origin mismatch** — The iframe's `srcdoc` attribute may cause the
   browser to report a different referrer origin than the parent page.
   The diagnostic was meant to log the computed origin, but the 403 page
   replaces the output before it can be read.
4. **OAuth token scope** — The OAuth token might not include `drive.file`
   scope (though the Python guard should catch this before rendering).
5. **Google Cloud project billing** — Some Google APIs require a billing
   account, even for free-tier usage.

**Debugging steps to try:**
- Wait 5+ minutes after saving API key changes, then hard-refresh and retry.
- Verify Google Picker API is **enabled** (not just restricted on the key).
  Go to: GCP Console → APIs & Services → Library → search "Google Picker API".
- Open the browser DevTools (F12) → Network tab → filter for `picker` or
  `google` and look at the failed request's response headers for clues.
- Check if the OAuth token is still valid (expired tokens can cause 403).
- Try temporarily setting the API key to **"Don't restrict key"** (API
  restrictions → None) to isolate whether the restriction is the cause.
  If the Picker works unrestricted, the referrer pattern needs adjustment.
- Try browsing via `http://127.0.0.1:8501` instead of `localhost` to see
  if the origin mismatch is caused by the browser treating them differently.

---

## Next test

1. Wait 5+ minutes for GCP API key changes to propagate.
2. Verify Google Picker API is **enabled** in GCP Console (not just restricted).
3. Hard-refresh browser (Cmd+Shift+R) at `http://localhost:8501`
4. Connect GA4 (the app reuses existing OAuth with `drive.file` scope)
5. Click "📂 Open Picker (spike)"
6. If the 403 persists, open DevTools Network tab and inspect the failed
   request for the specific referrer origin being sent.
7. If `picker.setVisible(true)` appears → look for the Google Picker file dialog
   opening as a full-window overlay (not inside the iframe)
8. Select a file → the bridge should deliver the file ID to Streamlit → expect
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
