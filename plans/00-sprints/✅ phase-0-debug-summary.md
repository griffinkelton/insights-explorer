# Phase 0 Spike — Debugging Summary

> **Branch:** `spike/drive-picker-transport`
> **Goal:** Prove Google Picker can deliver a selected file ID from the browser back to Streamlit Python.
> **Outcome:** ✅ Complete — Option A rejected, Option B selected as the production transport (2026-07-31)

---

## Decision: Option A REJECTED, Option B SELECTED

**Option A** (hidden-input DOM bridge via `components.html()`) was rejected
after platform evidence showed the `srcdoc` iframe origin is fundamentally
incompatible with Google Picker. **Option B** (declared Streamlit component
with `Streamlit.setComponentValue()`) passed the Phase 0 transport gates on
local Chrome/macOS and was **accepted as the production transport** for
v0.3.0 on 2026-07-31. Full cross-browser acceptance (Chrome/Windows, Safari,
Firefox) remains a v0.3.0 release gate per the spec.

---

## Origin evidence — 2026-07-31

- Top-level application URL: `http://localhost:8501/`
- Picker `origin` parameter (via `.setOrigin()`): `http://localhost:8501`
- Browser request `Referer`: `http://localhost:8501/`
- Component iframe URL: `about:srcdoc`
- Component iframe origin: `null`
- Picker request `parent` parameter: `about:favicon.ico`
- Result: Picker `GET https://docs.google.com/picker` returns 403

Conclusion: The explicit configured origin and actual HTTP referrer are
correct, but Picker runs from a `components.html()` `srcdoc` iframe with
an opaque origin and emits an invalid parent identity. Option A cannot
meet the supported, cross-browser transport requirement.

---

## Four bugs found and fixed (Option A — historical)

### Bug 1: `StreamlitAPIException` on Cancel
Streamlit blocks mutation of widget-owned `st.session_state` keys after
widget creation. Fixed by removing direct state-clearing after widget instantiation.

### Bug 2: Script stuck at "Diagnostics running…"
Synchronous `<script src>` blocked inline scripts; `<script type="application/json">`
config embedding interacted badly with real OAuth tokens. Fixed by:
- Dynamic gapi loading (`document.createElement("script")`)
- Config as `var CONFIG = {...}` instead of HTML script-content
- `.replace()` instead of `.format()` (no `{{`/`}}` escaping)

### Bug 3: `status.appendChild is not a function`
`window.status` is a read-only browser built-in. Renamed to `statusEl`.

### Bug 4: Google Picker returns 403
After all code fixes, Google's servers still rejected the Picker request
because the `components.html()` iframe's `about:srcdoc` origin produced
an invalid `parent` parameter, even though `.setOrigin()` and the HTTP
`Referer` were correct.

---

## Option B implementation (as of Phase 0 closeout)

### Architecture

```text
┌─────────────────────────────────────────────────────┐
│ Streamlit (http://localhost:8501)                   │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Python: drive_picker_spike.py                 │  │
│  │  drive_picker_transport(oauth_token,          │  │
│  │    developer_key, app_id, app_origin,         │  │
│  │    request_id)                                │  │
│  │                                               │  │
│  │  → validates {kind, requestId}               │  │
│  │  → sets _spike_success on match               │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Declared component (TypeScript + Vite)        │  │
│  │  Button → gapi.load('picker') → Picker        │  │
│  │  PICKED → Streamlit.setComponentValue({       │  │
│  │    kind: "transport_verified",                │  │
│  │    requestId: currentArgs.requestId           │  │
│  │  })                                            │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Files

| File | Purpose | Post-Phase-0 status |
|---|---|---|
| `components/drive_picker_component.py` | Python wrapper using `components.declare_component()` | ✅ Retained — production component |
| `components/drive_picker_component_frontend/src/main.ts` | TypeScript frontend | ✅ Retained |
| `components/drive_picker_component_frontend/index.html` | Minimal HTML shell | ✅ Retained |
| `components/drive_picker_component_frontend/package.json` | Dependencies (streamlit-component-lib, vite, typescript) | ✅ Retained |
| `components/drive_picker_spike.py` | Spike render entry-point (rewritten for Option B) | 🗑️ Deleted at closeout |
| `tests/test_drive_picker_spike.py` | Structural tests (12 tests, all pass) | 🗑️ Deleted at closeout |

### Key differences from Option A

| Aspect | Option A (REJECTED) | Option B (CURRENT) |
|---|---|---|
| Transport | Hidden `st.text_input` + DOM bridge | `Streamlit.setComponentValue()` |
| Origin | `srcdoc` iframe (`null` origin) | Declared component (real origin) |
| Return channel | `window.parent.document.querySelector()` | Bidirectional component protocol |
| Config injection | `var CONFIG = {...}` in inline script | Structured component args |
| Sanitization | Diagnostic panel rules | Never returns file ID/filename/MIME |

### Contract

The frontend returns **only**:
```json
{"kind": "transport_verified", "requestId": "<server-generated>"}
```

Never returned: file ID, filename, MIME type, OAuth token, API key, raw errors.

---

## Verification performed (2026-07-31, local Chrome/macOS)

The declared component (Option B) passed the Phase 0 transport gates:

1. Picker opened from the declared component's **"Open Picker spike"** button
2. Selecting a CSV/XLSX/Google Sheet returned a valid selection event to Python
3. The UI reported **"✓ Picker transport verified — no file was downloaded, parsed, stored, or imported"**
4. Cancel produced no success marker
5. Repeated select/reset cycles and reruns worked
6. Light/dark theme changes did not break Picker opening, selection, or the return transport (verified on local Chrome/macOS)
7. No token, file ID, filename, Picker payload, or raw error leaked to app-controlled UI/logs/console

### Browser matrix — cross-browser acceptance pending (v0.3.0 release gate)

| Browser | Platform | Gate | Status |
|---|---|---|---|
| Latest Chrome | macOS | Picker opens, selection returns, cancel, repeat ×3, rerun, theme change | ✅ Verified (2026-07-31) |
| Latest Chrome | Windows | Same gates | ⏳ Pending |
| Latest Safari | macOS | Same gates | ⏳ Pending |
| Latest Firefox | macOS | Same gates | ⏳ Pending |
| Latest Firefox | Windows | Same gates | ⏳ Pending |

v0.3.0 may not ship until the full matrix passes (see the spec's release gate).

---

## Cleanup after Phase 0 — completed 2026-07-31

- 🗑️ Deleted `components/drive_picker_spike.py` and `tests/test_drive_picker_spike.py`
- ✅ **Retained** `components/drive_picker_component.py` + frontend as the production component for v0.3.0 (not deleted — it is the chosen transport)
- ✅ Merged only the decision note to `main` (commit `2b965a8`)
- ✅ Preserved `spike/drive-picker-transport` on the remote for audit

---

## Prerequisites

- `.streamlit/secrets.toml` (gitignored, local only):
  ```toml
  PHASE_0_DRIVE_PICKER_SPIKE = true
  GOOGLE_PICKER_API_KEY = "API key restricted to Picker API + http://localhost:8501/*"
  GOOGLE_CLOUD_PROJECT_NUMBER = "123456789012"  # optional; appId skipped if absent
  ```
- Google Picker API enabled in GCP Console
- OAuth consent screen declares `drive.file` scope
- Test account listed under Test users if app is in Testing mode
- Node.js for frontend build (`npm run build` in `components/drive_picker_component_frontend/`)
