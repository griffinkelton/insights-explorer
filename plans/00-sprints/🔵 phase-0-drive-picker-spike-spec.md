# 🔵 Phase 0: Google Picker Transport Spike

> **Status:** Spec'd — not yet implemented
> **Parent:** [v0.3.0 Drive Import Spec](./🔵%20v0.3.0-drive-import-spec.md) §Phase 0
> **Branch:** `spike/drive-picker-transport`
> **Outcome:** This spike determines whether the hidden-input bridge (Option A) or a declared bidirectional Streamlit component (Option B) is the production transport for Phase 3.

---

## Failure criteria and decision rule

Phase 0 tests a transport mechanism, not the Drive-import feature.

### Option A fails immediately if any required browser fails any gate

Treat the hidden-input DOM bridge as failed if any supported browser/platform combination produces any of the following:

- The Picker does not open with valid existing OAuth credentials and configured developer key.
- A selection does not reliably produce the expected current-session Python success marker.
- The transport requires a cross-origin exception, DOMException, browser-specific selector, timing retry, postMessage workaround, Python completion-state mirror, or a change to Streamlit internals beyond the documented spike design.
- Cancel produces a marker, stale selection, rerun loop, or any import/download behavior.
- Three consecutive selections cannot be completed reliably.
- A normal Streamlit rerun or light/dark theme change breaks the picker or transport.
- The app emits an OAuth token, file ID, filename, raw Picker payload, or raw API error to application-controlled UI, logs, localStorage, or application-generated browser-console output.
- The behavior depends on a browser-specific exception or a configuration that cannot be reproduced on every required browser/platform.

**A failure on one required browser/platform is sufficient to reject Option A.** Do not add selectors, retries, browser branches, postMessage bridges, or session-state synchronization to rescue it.

### Option A outcome

- If all required gates pass on every target browser/platform, record: `Option A accepted for v0.3.0 implementation`.
- If any gate fails, record: `Option A rejected; proceed to Option B, declared bidirectional component`.

**Option A rejection is an expected Phase 0 outcome, not a release failure.**

### Option B pass rule

Option B must pass every common gate above on the complete browser matrix and, in addition:

- `Streamlit.setComponentValue()` delivers the expected current-session result.
- Repeated selections are distinguishable through a documented nonce or value-change mechanism.
- The declared component renders correctly in both themes.
- The component uses no hidden Streamlit DOM selector or unsupported parent-document bridge.

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

## Developer prerequisites

### 1. Google Cloud Platform setup

The Picker requires both an OAuth client (already configured) and a **Google API key** restricted to the Picker API.

#### Step-by-step GCP console instructions

| Step | Action | Where |
|------|--------|-------|
| 1 | Open your GCP project | [console.cloud.google.com](https://console.cloud.google.com/) — select the project that owns the existing OAuth client |
| 2 | Enable the **Google Picker API** | **APIs & Services** → **Library** → search "Google Picker API" → **Enable** |
| 3 | Verify **Google Drive API** is enabled | Same Library → search "Google Drive API" (must remain enabled — Phase 1+ needs server-side metadata/download calls) |
| 4 | Create an API key | **APIs & Services** → **Credentials** → **+ Create Credentials** → **API key** |
| 5 | Restrict the API key by HTTP referrer | Click the new key → **Application restrictions** → **HTTP referrers (websites)** → add `http://localhost:8501/*` AND `http://127.0.0.1:8501/*` (they are distinct origins) |
| 6 | Restrict the API key by API | Under **API restrictions** → **Restrict key** → check **Google Picker API** → **Save** |
| 7 | Confirm OAuth consent screen | Ensure the existing consent configuration includes `https://www.googleapis.com/auth/drive.file` and that your test Google account is listed under **Test users** if the app remains in Testing |
| 8 | Copy the API key | Store it — you'll add it to `.streamlit/secrets.toml` |

**Troubleshooting:** `localhost` and `127.0.0.1` are distinct origins for referrer validation. If you browse via `http://127.0.0.1:8501`, you need `http://127.0.0.1:8501/*` in the referrer allowlist separately from `http://localhost:8501/*`. Test both during Phase 0 to confirm the configured referrers match the actual browsing origin.

The OAuth consent screen and `drive.file` scope need **no changes** — the Picker reuses your existing OAuth token. An API key identifies the Cloud project for the client-side Picker request; it is not equivalent to the OAuth client ID or user access token.

### 2. Secrets file

Create `.streamlit/secrets.toml` (does not exist yet in this repo; `.gitignore` already excludes it):

```toml
# Phase 0: Google Picker transport spike
PHASE_0_DRIVE_PICKER_SPIKE = true

# Google Picker API key (create in GCP Console → APIs & Services → Credentials)
GOOGLE_PICKER_API_KEY = "AIza..."
```

Also create `.streamlit/secrets.example.toml` (committed, with empty placeholders only) to document the required key names:

```toml
# Example secrets for Google Drive import.
# Copy to .streamlit/secrets.toml and fill in real values.

# Google Picker developer key (browser API key, restricted to Picker API)
GOOGLE_PICKER_API_KEY = ""

# Phase 0 development flag (remove after Phase 0 completes)
PHASE_0_DRIVE_PICKER_SPIKE = false
```

Never commit actual secret values. The `.gitignore` already excludes `.streamlit/secrets.toml`.

### 3. OAuth prerequisites

- The user must have connected GA4 with a token that includes the `drive.file` scope
- **Scope check:** The spike must check the actual token scopes — not just the configured scopes — because existing stored credentials may predate `drive.file`. If the token lacks `drive.file`, show: **"Reconnect Google to enable Drive import"** — do not silently fall back or request broader scope
- If the token is expired or absent, the spike shows: **"Connect or reconnect Google Analytics first to test Drive Picker."** — it does not handle OAuth itself

---

## Branch and file structure

```
spike/drive-picker-transport (branch off main)
├── components/
│   └── drive_picker_spike.py    # Spike module (DELETED after Phase 0)
├── tests/
│   └── test_drive_picker_spike.py  # Minimal structural tests (DELETED after Phase 0)
└── .streamlit/
    └── secrets.example.toml     # Committed — documents required key names
```

### Sidebar integration point

In `components/sidebar.py`, add a single gated call near the existing data-entry controls:

```python
# In the main sidebar render, after _render_file_uploader() but before _render_ga4_connect():

def _phase_0_spike_enabled() -> bool:
    return bool(st.secrets.get("PHASE_0_DRIVE_PICKER_SPIKE", False))

if _phase_0_spike_enabled():
    from components.drive_picker_spike import render_drive_picker_spike
    render_drive_picker_spike()
```

A key-presence gate conflates two different facts ("the app has credentials" and "this experimental UI is enabled"). A dedicated toggle makes intent auditable, lets you validate missing-key behavior while the spike is visible, and prevents accidental exposure if the browser key is later added to a non-development environment.

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

1. **Guard:** If no OAuth credentials exist, the token is expired, or the token lacks `drive.file` scope, render an info message directing the user to (re)connect GA4. Do not render the Picker button.
2. **Button:** Render an explicit **"Open Picker (spike)"** button. The Picker iframe is created **only after this click** — not passively because credentials exist.
3. **Picker:** Opens the Google Picker configured for spreadsheets, CSV, and XLSX views (matching the Phase 3 production config). Uses the OAuth token from `st.session_state.ga4_credentials` and the API key from `st.secrets["GOOGLE_PICKER_API_KEY"]`.
4. **Cancel:** If the user closes the Picker without selecting a file, the spike returns to the idle state. No error, no stale state.
5. **Selection:** The selected file ID is transported to Python via the candidate transport (Option A or Option B).
6. **Success indication:** Display only:
   ```
   ✓ Picker transport verified

   A selection event reached this Streamlit session.
   No file was downloaded, parsed, stored, or imported.
   ```
   Store a boolean plus a short-lived event timestamp in `st.session_state` only. Do not display or persist the file ID, name, MIME type, URL, or raw callback payload.
7. **Reset:** A **"Reset spike result"** button clears the success state. The success indication does not survive a Streamlit rerun.
8. **No download:** The spike never calls any Drive API download method. It only proves the ID arrived.
9. **No logging:** Tokens, file IDs, and Picker payloads are never logged, `st.write()`-ed, or persisted.

---

## Option A: Hidden-input bridge

**This is the only transport on the `spike/drive-picker-transport` branch.** If it fails in any required browser, abandon the branch and create `spike/drive-picker-declared-component` for Option B — do not patch, add selectors, or add message-based workarounds.

### How it works

```
User clicks "Open Picker (spike)"
  ↓
Python sets _drive_picker_spike_active = True
Python renders components.html() iframe containing:
  - gapi client library load
  - Google Picker initialization (setOAuthToken, setDeveloperKey, setOrigin)
  - Picker callback → transport fileId through the bridge
  - Hidden input mutation: find Streamlit's st.text_input by known label,
    set its value, dispatch input + React change events
  ↓
Streamlit detects the input change, reruns
  ↓
Python reads st.text_input value, validates it's non-empty
  ↓
Python displays minimal success marker (no file ID shown)
```

### HTML template safety rules

- OAuth token injected via `json.dumps()` → `<script type="application/json">` element — **never** string-replaced into executable JavaScript
- API key injected the same way
- Configuration parsed only after `gapi.load('picker', …)` completes
- `_json_for_script()` escapes `<` to `\u003c` to prevent `</script>` injection
- No file ID, token, or API error appears in `console.log` or any application-controlled browser output
- Origin computed via `window.top.location.origin` (access to `window.top.location` may be restricted by cross-origin/sandbox settings — this is exactly a behavior the spike must test)

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
  <meta charset="utf-8">
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

    // Use window.top.location.origin for the real browsing context origin.
    // Access may be denied by cross-origin/sandbox — that is a Phase 0 finding.
    const origin = window.top.location.origin;

    const picker = new google.picker.PickerBuilder()
      .setOAuthToken(CONFIG.oauthToken)
      .setDeveloperKey(CONFIG.apiKey)
      .setOrigin(origin)
      .addView(view)
      .setCallback(pickerCallback)
      .build();
    picker.setVisible(true);
  }}

  function pickerCallback(data) {{
    if (data.action === google.picker.Action.PICKED && data.docs.length > 0) {{
      const fileId = data.docs[0].id;
      // Only fileId crosses the boundary — name/mimeType are untrusted
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

**Only implemented if Option A fails in any required browser.** In that case, create a **fresh branch** `spike/drive-picker-declared-component` — do not extend Option A with additional DOM workarounds.

Option B replaces `components.html()` with a declared Streamlit custom component (`st.components.v1.declare_component`). This requires:

- A small frontend package (e.g., `components/drive_picker/`) with a `package.json`
- The component receives `api_key` as an arg and uses `Streamlit.setComponentValue()` to return results
- Picker opens only on user click within the component

The declared component path is the **supported production transport** if Option A fails. It is intentionally structured for refinement into the Phase 3 implementation.

### Fallback trigger

Option B is triggered when **any** of Option A's failure criteria are met (see the Failure Criteria section at the top of this spec). Create `spike/drive-picker-declared-component` as a clean branch — do not extend the hidden-input spike branch.

---

## Acceptance gates

All gates must pass in the browser matrix below. G1–G7 are the transport gates; G8 and G9 are prerequisite infrastructure gates.

| # | Gate | How to verify |
|---|---|---|
| **G1** | OAuth-authenticated Picker opens after button click | Click "Open Picker (spike)" — Picker modal appears with Drive files |
| **G2** | CSV, XLSX, and Google Sheets files are visible and selectable | Picker shows spreadsheets; CSV/XLSX files are visible via MIME type filter |
| **G3** | Selected file reaches Python after selection | Select a file → "✓ Picker transport verified" appears in the sidebar. No file ID, filename, or metadata displayed |
| **G4** | Cancel does not trigger stale import state | Open Picker, click Cancel/close → spike returns to idle. No error, no hanging state |
| **G5** | Repeated selections work (3 consecutive) | Select file → Reset → select again → Reset → select again. All succeed |
| **G6** | Bridge survives Streamlit reruns and dark/light theme changes | Toggle theme, interact with other sidebar controls, then select a file. Transport still works |
| **G7** | No OAuth token, file ID, or raw API error appears in application-controlled visible UI, application logs, localStorage, or application-generated browser-console output | Inspect sidebar, browser console (app-originated only), and localStorage after each gate. Google Picker/gapi may produce its own diagnostics — those are outside app control |
| **G8** | Picker opens with referrer- and Picker-API-restricted browser key; fails safely when missing or invalid | Remove the key temporarily from secrets → confirm actionable warning appears. Restore key → confirm Picker works again |
| **G9** | Picker opens using token from existing GA4 OAuth with `drive.file`; old/missing-scope credential shows reconnect instruction | Test with a valid token (works) and simulate missing scope (shows reconnect message, does not attempt import) |

### Additional acceptance case

Confirm that running the same app at `localhost` and then `127.0.0.1` behaves according to the configured allowed referrers and uses the exact live page origin, rather than silently assuming the two hosts are interchangeable.

**Pass:** All 9 gates pass in all browsers in the matrix.
**Fail:** Any gate fails in any browser. Abandon Option A and build Option B.

---

## Browser version recording template

Every transport gate must pass on:

| Browser | Platform |
|---|---|
| Latest stable Chrome | macOS and Windows |
| Latest stable Safari | macOS |
| Latest stable Firefox | macOS and Windows |

Record the **exact version**, operating system version, test date, local origin, and API-key referrer configuration:

| Browser | Version | OS | Origin | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 | Notes |
|---------|---------|-----|--------|----|----|----|----|----|----|----|----|----|-------|
| Chrome | _fill_ | _fill_ | _fill_ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Safari | _fill_ | _fill_ | _fill_ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |
| Firefox | _fill_ | _fill_ | _fill_ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | |

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

### Tested origins
- [e.g., http://localhost:8501]
- [e.g., http://127.0.0.1:8501]

### API-key referrer configuration
[Exact referrer patterns configured]

### Selected transport
[Description of the chosen transport mechanism]

### Rationale
[Why this transport was chosen — include any browser-specific findings]

### Known constraints
[Any limitations of the selected transport]

### Consequences
- [What Phase 3 implementation approach this enables]
- [Any constraints the transport choice imposes]

### Next action
- [If Option A: proceed to Phase 1. If Option B: create spike/drive-picker-declared-component]
```

---

## Branch finalization criteria

Finalize the Phase 0 branch only when **one transport option has passed every required gate on the full browser matrix, the decision is recorded, and the spike code is removed from the merge to `main`**.

### Prerequisites checklist

- [ ] A restricted Picker developer key is available only through local secrets.
- [ ] Existing GA4 credentials produce a valid OAuth access token with `drive.file`.
- [ ] The spike is enabled only by the dedicated development flag (`PHASE_0_DRIVE_PICKER_SPIKE`).
- [ ] The picker is rendered only after an explicit **Open Picker spike** action.
- [ ] The spike performs no download, parsing, file validation, provenance creation, `DataContext` creation, or disk write.

### Transport acceptance checklist

For the selected option, verify all of the following:

- [ ] Google Picker opens successfully.
- [ ] Picker offers the intended CSV, XLSX, and Google Sheets selection surfaces.
- [ ] Selecting a real permitted test file causes a selection event to reach Python.
- [ ] Python stores only a current-session success marker; it does not retain or display picker file ID, name, MIME type, URL, or raw callback payload.
- [ ] The UI reports only: "✓ Picker transport verified. A selection event reached this Streamlit session. No file was downloaded, parsed, stored, or imported."
- [ ] Cancel closes the Picker without producing a success marker or stale selection state.
- [ ] Three consecutive selections work, including after resetting the success marker.
- [ ] A Streamlit rerun does not leave stale state, duplicate listeners, an unusable picker, or an accidental import path.
- [ ] Light and dark theme changes do not break Picker opening, selection, or return transport.
- [ ] No token, file ID, picker payload, or raw API error appears in application-controlled UI, logs, localStorage, or application-generated browser-console output.

### Merge/cleanup gate

- [ ] A Phase 0 decision note is committed, stating **Option A accepted** or **Option A rejected; Option B selected**.
- [ ] The note includes the matrix, versions, date, tested origin, selection/cancel/repeat/rerun/theme outcomes, and any limitations.
- [ ] No credentials, token, file ID, filename, raw callback payload, screenshots with identifiers, or local secret configuration appear in commits, diffs, logs, or the note.
- [ ] The spike module and temporary sidebar hook are deleted before anything merges to `main`.
- [ ] Only the decision/evidence note merges to `main`; preserve the remote spike branch temporarily under the agreed retention policy.
- [ ] If Option B wins, create a **fresh implementation branch** (`spike/drive-picker-declared-component`) for the declared component; do not extend Option A with additional DOM workarounds.

---

## Cleanup procedure

After the decision is recorded:

1. **If Option A passes:**
   - Delete `components/drive_picker_spike.py` and `tests/test_drive_picker_spike.py`
   - Remove the `PHASE_0_DRIVE_PICKER_SPIKE` gated call from `components/sidebar.py`
   - Commit the decision note to main
   - Delete the `spike/drive-picker-transport` branch (mark retention window: delete after v0.3.0 ships)
   - Keep the remote spike branch for short-term auditability
   - The hidden-input bridge pattern is documented in the decision note for Phase 3

2. **If Option B is required:**
   - Delete `components/drive_picker_spike.py` and `tests/test_drive_picker_spike.py`
   - Remove the `PHASE_0_DRIVE_PICKER_SPIKE` gated call from `components/sidebar.py`
   - Create `spike/drive-picker-declared-component` as a fresh branch (not extending the hidden-input spike)
   - Retain the declared component (`components/drive_picker/`) — it becomes the Phase 3 foundation
   - Commit the decision note + declared component to main
   - Delete the `spike/drive-picker-transport` branch

3. **Either way:**
   - The spike branch stays on the remote for historical reference
   - `st.secrets["PHASE_0_DRIVE_PICKER_SPIKE"]` is no longer checked (the gated call is removed)
   - `st.secrets["GOOGLE_PICKER_API_KEY"]` is retained — Phase 3 needs it
   - Do not squash the spike into `main`: experimental code should not be preserved in mainline history

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
- [Google Picker: setOrigin reference](https://developers.google.com/workspace/drive/picker/reference/picker.pickerbuilder.setorigin)
- [Streamlit Secrets Management](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
- [GCP Console — APIs & Services](https://console.cloud.google.com/apis/)
