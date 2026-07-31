# 🔵 Phase 0: Google Picker Transport Spike

> **Status:** Spec'd — not yet implemented
> **Parent:** [v0.3.0 Drive Import Spec](./🔵%20v0.3.0-drive-import-spec.md) §Phase 0
> **Branch:** `spike/drive-picker-transport`
> **Outcome:** This spike determines whether the hidden-input bridge (Option A) or a declared bidirectional Streamlit component (Option B) is the production transport for Phase 3.

---

## Purpose

Prove — in real browser conditions with a live Streamlit session — that a selected Google Picker file ID can reach Python reliably. This is a mandatory gate before any Phase 3 UI work begins.

**This spike does NOT:**
- Download files from Drive
- Call `load_file()`, `DataContext`, or any ingestion pipeline
- Log OAuth tokens, file IDs, or Picker metadata
- Persist anything to session state beyond the current rerun
- Evolve into production code if Option A is chosen (it is deleted after the gate)

---

## Prerequisites

### 1. Google Cloud Platform setup

The Picker requires both an OAuth client (already configured) and a **Google API key** restricted to the Picker API.

#### Step-by-step GCP console instructions

| Step | Action | Where |
|------|--------|-------|
| 1 | Open your GCP project | [console.cloud.google.com](https://console.cloud.google.com/) |
| 2 | Enable the **Google Picker API** | **APIs & Services** → **Library** → search "Google Picker API" → **Enable** |
| 3 | Verify **Google Drive API** is enabled | Same Library → search "Google Drive API" (likely already enabled — your app uses `drive.file`) |
| 4 | Create an API key | **APIs & Services** → **Credentials** → **+ Create Credentials** → **API key** |
| 5 | Restrict the API key to Picker API only | Click the new key → **API restrictions** → **Restrict key** → check **Google Picker API** → **Save** |
| 6 | (Optional, for production) Restrict by HTTP referrer | Under **Application restrictions** → **HTTP referrers** → add `http://localhost:8501/*` |
| 7 | Copy the API key | Store it — you'll add it to `.streamlit/secrets.toml` |

**Important:** For localhost testing, you may need to leave application restrictions **unrestricted** (step 6 is optional during Phase 0). Google's referrer validation can be unreliable with `localhost`. Add the restriction before any non-local deployment.

The OAuth consent screen and `drive.file` scope need **no changes** — the Picker reuses your existing OAuth token.

### 2. Secrets file

Create `.streamlit/secrets.toml` (does not exist yet in this repo):

```toml
# Phase 0: Google Picker transport spike
PHASE_0_SPIKE = true

# Google Picker API key (create in GCP Console → APIs & Services → Credentials)
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
```

The `.gitignore` already excludes `.streamlit/secrets.toml` (Streamlit default). Never commit secrets.

### 3. OAuth prerequisites

- The user must have connected GA4 at least once (valid OAuth token with `drive.file` scope)
- If the token is expired or absent, the spike shows a clear message: "Connect GA4 first to test Drive import" — it does not handle OAuth itself

---

## Branch and file structure

```
spike/drive-picker-transport (branch off main)
├── components/
│   └── drive_picker_spike.py    # Spike module (DELETED after Phase 0)
└── tests/
    └── test_drive_picker_spike.py  # Minimal structural tests (DELETED after Phase 0)
```

### Sidebar integration point

In `components/sidebar.py`, add a single gated call near the existing data-entry controls:

```python
# In _populate_data_state() or the main sidebar render, after _render_file_uploader()
# but before _render_ga4_connect():

if st.secrets.get("PHASE_0_SPIKE", False):
    from components.drive_picker_spike import render_drive_picker_spike
    render_drive_picker_spike()
```

This location reflects the eventual Drive-import position without entangling the spike with GA4 connection logic or upload ingestion.

---

## Module API

```python
# components/drive_picker_spike.py

def render_drive_picker_spike() -> None:
    """Phase 0 transport experiment. Proves a Picker file ID reaches Python.

    No file download. No DataContext. No ingestion. No persistent state.
    Deleted after the Phase 0 gate decision.
    """
```

### Behavior contract

1. **Guard:** If no OAuth credentials exist or the token is expired, render a single info message: *"Connect GA4 first to test Drive import."* Do not render the Picker button.
2. **Button:** Render an explicit **"Open Picker (spike)"** button. The Picker iframe is created **only after this click** — not passively because credentials exist.
3. **Picker:** Opens the Google Picker configured for spreadsheets, CSV, and XLSX views (matching the Phase 3 production config). Uses the OAuth token from `st.session_state.ga4_credentials` and the API key from `st.secrets["GOOGLE_API_KEY"]`.
4. **Cancel:** If the user closes the Picker without selecting a file, the spike returns to the idle state. No error, no stale state.
5. **Selection:** The selected file ID is transported to Python via the candidate transport (Option A or Option B).
6. **Success indication:** A green checkmark and the text *"Transport verified — file ID received."* No filename, no file ID displayed, no metadata shown.
7. **Reset:** A **"Reset"** button clears the success state. The success indication does not survive a Streamlit rerun.
8. **No download:** The spike never calls any Drive API download method. It only proves the ID arrived.
9. **No logging:** Tokens, file IDs, and Picker payloads are never logged, `st.write()`-ed, or persisted.

---

## Option A: Hidden-input bridge

**This is the first implementation attempted.** If it fails in any required browser, abandon it and build Option B — do not patch, add selectors, or add message-based workarounds.

### How it works

```
User clicks "Open Picker (spike)"
  ↓
Python sets _drive_picker_spike_active = True
Python renders components.html() iframe containing:
  - gapi client library load
  - Google Picker initialization (setOAuthToken, setDeveloperKey, setOrigin)
  - Picker callback → postMessage({fileId}) to parent
  - Hidden input mutation: find Streamlit's st.text_input by known label,
    set its value, dispatch input + React change events
  ↓
Streamlit detects the input change, reruns
  ↓
Python reads st.text_input value, validates it's non-empty
  ↓
Python displays "Transport verified — file ID received."
```

### HTML template safety rules

- OAuth token injected via `json.dumps()` → `<script type="application/json">` element — **never** string-replaced into executable JavaScript
- API key injected the same way
- Configuration parsed only after `gapi.load('picker', …)` completes
- `_json_for_script()` escapes `<` to `\u003c` to prevent `</script>` injection
- No file ID, token, or API error appears in `console.log` or any application-controlled browser output

### Implementation sketch

```python
def _json_for_script(value: object) -> str:
    """Serialize a value for safe embedding in an HTML <script> element."""
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def _picker_iframe_html(oauth_token: str, api_key: str) -> str:
    """Build the Picker iframe HTML with JSON-safe config injection."""
    config = {"oauthToken": oauth_token, "apiKey": api_key}
    config_json = _json_for_script(config)

    return f"""<!DOCTYPE html>
<html>
<head>
  <script type="text/javascript" src="https://apis.google.com/js/api.js"></script>
</head>
<body>
<script id="picker-config" type="application/json">{config_json}</script>
<script>
  const CONFIG = JSON.parse(
    document.getElementById("picker-config").textContent
  );

  function onPickerApiLoad() {{
    const view = new google.picker.DocsView(google.picker.ViewId.SPREADSHEETS)
      .setMimeTypes("application/vnd.google-apps.spreadsheet,text/csv,"
        + "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");

    const picker = new google.picker.PickerBuilder()
      .setOAuthToken(CONFIG.oauthToken)
      .setDeveloperKey(CONFIG.apiKey)
      .setOrigin(window.location.protocol + "//" + window.location.host)
      .addView(view)
      .setCallback(pickerCallback)
      .build();
    picker.setVisible(true);
  }}

  function pickerCallback(data) {{
    if (data.action === google.picker.Action.PICKED && data.docs.length > 0) {{
      const fileId = data.docs[0].id;
      // Only fileId crosses the boundary — name/mimeType are untrusted
      // Transport fileId to Python via hidden-input bridge (Option A)
      bridgeToStreamlit(fileId);
    }}
  }}

  gapi.load("picker", {{"callback": onPickerApiLoad}});
</script>
</body>
</html>"""
```

The `bridgeToStreamlit()` function is the Option A experiment — it attempts to find the Streamlit-controlled hidden input and route the file ID through it. The exact bridge implementation is written during the spike, not pre-designed in this spec.

---

## Option B: Declared bidirectional component

**Only implemented if Option A fails in any required browser.**

Option B replaces `components.html()` with a declared Streamlit custom component (`st.components.v1.declare_component`). This requires:

- A small frontend package (e.g., `components/drive_picker/`) with a `package.json`
- The component receives `replay_nonce` and `api_key` as args
- The component returns `{fileId: string}` via `Streamlit.setComponentValue()`
- Picker opens only on user click within the component

The declared component path is the **supported production transport** if Option A fails. It is intentionally not a throwaway — it becomes the foundation for Phase 3.

### Fallback trigger

Option B is triggered when **any** of these occur with Option A:
- `window.parent.document` access is denied (cross-origin)
- The hidden input selector fails to find or mutate the Streamlit widget
- Streamlit does not detect the value change and rerun
- The bridge fails in Safari or Firefox (even if it works in Chrome)

---

## Acceptance gates

All 7 gates must pass in **Chrome, Safari, and Firefox** (latest stable, macOS):

| # | Gate | How to verify |
|---|---|---|
| **G1** | OAuth-authenticated Picker opens after button click | Click "Open Picker (spike)" — Picker modal appears with Drive files |
| **G2** | CSV, XLSX, and Google Sheets files are visible and selectable | Picker shows spreadsheets; CSV/XLSX files are visible via MIME type filter |
| **G3** | Selected file ID reaches Python after selection | Select a file → "Transport verified — file ID received." appears in the sidebar |
| **G4** | Cancel does not trigger stale import state | Open Picker, click Cancel/close → spike returns to idle. No error, no hanging state |
| **G5** | Second selection after a prior selection works | Select file → success → Reset → select another file → success again |
| **G6** | Bridge survives Streamlit reruns and dark/light theme changes | Toggle theme, interact with other sidebar controls, then select a file. Transport still works |
| **G7** | No OAuth token, file ID, or raw API error appears in application-controlled visible UI, application logs, localStorage, or application-generated browser-console output | Inspect sidebar, browser console (app-originated only), and localStorage after each gate. Google Picker/gapi may produce its own diagnostics — those are outside app control |

**Pass:** All 7 gates pass in all 3 browsers.
**Fail:** Any gate fails in any browser. Abandon Option A and build Option B.

---

## Browser version recording template

Record this table during Phase 0 testing:

| Browser | Version | OS | G1 | G2 | G3 | G4 | G5 | G6 | G7 | Notes |
|---------|---------|-----|----|----|----|----|----|----|----|-------|
| Chrome | _fill_ | _fill_ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Safari | _fill_ | _fill_ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Firefox | _fill_ | _fill_ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |

---

## Decision outcome template

After Phase 0 completes, fill this in and commit it as the decision note:

```markdown
## Phase 0 Decision: Drive Picker Transport

**Date:** YYYY-MM-DD
**Outcome:** [Option A: hidden-input bridge / Option B: declared component]

### Tested browsers
- Chrome [version] on [OS]: [PASS/FAIL]
- Safari [version] on [OS]: [PASS/FAIL]
- Firefox [version] on [OS]: [PASS/FAIL]

### Selected transport
[Description of the chosen transport mechanism]

### Rationale
[Why this transport was chosen — include any browser-specific findings]

### Consequences
- [What Phase 3 implementation approach this enables]
- [Any constraints the transport choice imposes]
```

---

## Cleanup procedure

After the decision is recorded:

1. **If Option A passes:**
   - Delete `components/drive_picker_spike.py` and `tests/test_drive_picker_spike.py`
   - Remove the `PHASE_0_SPIKE` gated call from `components/sidebar.py`
   - Commit the decision note to main
   - Delete the `spike/drive-picker-transport` branch
   - The hidden-input bridge pattern is documented in the decision note for Phase 3

2. **If Option B is required:**
   - Delete `components/drive_picker_spike.py` and `tests/test_drive_picker_spike.py`
   - Remove the `PHASE_0_SPIKE` gated call from `components/sidebar.py`
   - Retain the declared component (`components/drive_picker/`) — it becomes the Phase 3 foundation
   - Commit the decision note + declared component to main
   - Delete the `spike/drive-picker-transport` branch

3. **Either way:**
   - The spike branch stays on the remote for historical reference
   - `st.secrets["PHASE_0_SPIKE"]` is no longer checked (the gated call is removed)
   - `st.secrets["GOOGLE_API_KEY"]` is retained — Phase 3 needs it

---

## Non-goals (explicitly excluded)

- Downloading or reading any Drive file contents
- Creating a `DataContext` or invoking `load_file()`
- Testing the `_BoundedBytesIO` writer or file-size validation
- Testing MIME type allowlisting or Google Sheets export
- Testing `create_context_from_drive()` provenance
- Picker folder navigation or multi-select
- Shared Drive support
- Mobile/tablet browser testing
- Performance or load testing
- Accessibility audit (the production Picker in Phase 3 will need this)

---

## References

- [v0.3.0 Drive Import Implementation Spec](./🔵%20v0.3.0-drive-import-spec.md) — Phase 0 section
- [v0.3.0 Drive Import Design Record](../../🔵%20v0.3.0-drive-import-design.md) — Architecture decisions
- [Google Picker API Overview](https://developers.google.com/workspace/drive/picker/guides/overview)
- [GCP Console — APIs & Services](https://console.cloud.google.com/apis/)
