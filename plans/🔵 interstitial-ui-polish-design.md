# 🔵 Interstitial UI/UX Polish Design (v0.3.0 → v0.4.0)

> **Status:** 🔵 Aspirational — design only, **not yet implemented**
> **Date:** 2026-08-03
> **Scope:** UI/UX polish between v0.3.0 (Drive Import, shipped) and v0.4.0 (GA4 insights engine).
> **Parent:** deferred items recorded in [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) — *explicitly out of v0.3.0 release scope*.

---

## 1. Goals & non-goals

### Goals
1. **Fix the #1 reported usability problem:** the Google Picker renders cramped inside the ~300px sidebar iframe — "that content is not designed for that size."
2. **Make light mode genuinely usable and consistent** (toggle works; visual design is unfinished).
3. **Harden the import flow UX** with clear states, cancel affordances, and feedback.
4. Ship as small, independent, testable increments — no architecture rewrites.

### Non-goals (explicitly NOT this work)
- GA4 Insights Engine, evidence connector, multimodal, event-level data (v0.4.0+ roadmap work).
- Cross-browser matrix *execution* (Safari/Firefox/Windows) — tracked separately in the checklist.
- Any change to the server-side import security model (`download_drive_file`, `DriveImportError`, `PickerSelection`, request-freshness, no-secret boundary) — these stay frozen.

---

## 2. Workstream A — Drive Picker in a full-size modal (`st.dialog`)

### 2.1 Problem
The declared component's *own* DOM is just a button + status line (auto-sized via `setFrameHeight`). The **Google-hosted Picker modal** is the thing that's cramped — it renders inside the component iframe, which lives in the ~300px sidebar. Giving the component a full-viewport container fixes it.

### 2.2 Approach (verified against installed Streamlit 1.60)
`st.dialog` is confirmed available with:
- `width="small" | "medium" | "large"` (enum `SMALL/LARGE/MEDIUM` verified in `streamlit/proto/Block_pb2.pyi`)
- `dismissible=True` (click-outside / X / ESC), `on_dismiss="ignore"|"rerun"|callback`
- Fragment behavior: widget interactions inside the dialog rerun **only the dialog function**
- Values flow out via **Session State** (explicitly documented)

**Pattern:**
```python
@st.dialog("Import from Google Drive", width="large", dismissible=True)
def drive_picker_dialog() -> None:
    # render drive_picker_transport() + process selection here
    # on success: store result in st.session_state + st.rerun()  → closes dialog
    ...

# in sidebar _render_drive_picker():
if st.button("📂 Import from Google Drive", ...):
    st.session_state.drive_picker_request_id = str(uuid.uuid4())
    st.session_state.drive_picker_active = True

if st.session_state.get("drive_picker_active"):
    drive_picker_dialog()
```

### 2.3 Why this fixes the earlier failed "overlay" attempt
The v0.3.0 sidebar→main-area overlay attempt failed because it passed Picker config through intermediate session-state keys (`_drive_picker_oauth_token` etc.) across the sidebar→main-content render boundary and `st.rerun()` ordering. `st.dialog` **sidesteps this entirely**: the dialog function is called from the sidebar's own render cycle, renders the component inside the dialog in the *same run*, and the component's selection is processed inside the dialog function body. No cross-section state handoff.

### 2.4 Flow (normal + edge cases)
| Case | Behavior |
|---|---|
| Click Import (sidebar) | `drive_picker_active=True` → dialog opens (`width="large"`), component mounts, loads Picker lib (~1s) |
| Pick a file | Component emits `{kind, requestId, fileId}` → freshness check → `_ingest_drive_file()` → success: `st.toast("✓ Data imported from Drive")`, `active=False`, `st.rerun()` (closes dialog) |
| Pick → download/parse error | `st.error` rendered **inside dialog**, dialog stays open, button resets → user retries or dismisses |
| Cancel (component CANCEL / dialog X / ESC / click-outside) | No selection → `active=False`, `st.rerun()` closes dialog; button resets (already covered by existing `?picker_seam=cancel` tests) |
| Theme toggle during active flow | **Design decision required (see 2.6):** gate dialog on session state so it survives full-app reruns and the component receives the new `theme` arg |
| Second import | Button available again; new `requestId`; fresh dialog; frontend already relabels "✔ Imported — Open Another File" |

### 2.5 Open questions to resolve in a **spike first** (before committing to this design)
1. **Custom component inside dialog:** confirm `drive_picker_transport` renders and does not re-mount mid-flow. Component state is module-level in the iframe, so a re-mount just reloads the Picker lib (idempotent, ~1s) — acceptable, but verify. Keep `key=f"drive_picker_{request_id}"` stable across reruns.
2. **Dialog persistence semantics:** confirm that calling the dialog function on every rerun (gated on `drive_picker_active`) keeps it open across *full-app* reruns (needed for theme-switch-during-flow), and that dismissal sets the expected state. Two candidate gating patterns:
   - (a) call dialog only from button click → closes on any unrelated full rerun (simpler, weaker)
   - (b) gate on `drive_picker_active` session flag → persists across reruns (required for Functional #7–#8 parity)
3. **`st.sidebar` inside dialog is unsupported** — ensure the dialog body never touches `st.sidebar` (it won't; component + captions only).

### 2.6 Test impact (playwright smoke suite)
- `_click_import` (sidebar button) still works; the iframe now appears inside the dialog — `_picker_iframes()` (title `drive_picker_transport`) still finds it.
- `test_picker_iframe_not_visible_initially` still valid (no iframe until dialog opens).
- **New smoke tests to add:** dialog opens on click (locator `[data-testid="stDialog"]`); dialog closes after `picked`/`cancel` seam; theme change while dialog open re-renders component with new `data-theme`; dialog not open without auth.
- Unit tests in `test_sidebar.py` asserting the inline `drive_picker_active` render path must be updated to the dialog shape.

---

## 3. Workstream B — Light mode design polish

### 3.1 Audit summary (from `utils/styles.py`)
Light mode has broad coverage (buttons, metrics, expanders, dataframes, chat, alerts, uploader, inputs, tabs, code, scrollbar, tooltips, Learn cards) but these gaps/rough spots remain:

| # | Gap | Fix |
|---|---|---|
| B1 | **Component `index.html` hard-codes light colors** (`#fafafa` bg, `#f0f0f5` button) that clash with app tokens (`#ffffff`/`--bg-card`) | Convert component CSS to consume the `theme` arg via `data-theme` blocks using near-app token values; keep self-contained (component iframes can't read parent CSS vars) |
| B2 | Hard-coded hexes scattered in `LIGHT_THEME_CSS` (e.g., `#e5e7eb`, `#e0e0eb` secondary hovers) | Consolidate into a small set of light-mode variables for consistency |
| B3 | Privacy card uses inline `rgba` colors baked by theme branch in `sidebar.py` | Reuse CSS vars (`--bg-card`, `--border`, `--text-secondary`) via a class instead of inline styles |
| B4 | Hero/empty-state: verify contrast + gradient legibility in light mode (gradient clip-text on white can be low-contrast) | Audit `components/hero.py`; add light-mode overrides |
| B5 | Plotly charts: theme-tagged cache keys exist; verify light template colors against the new light palette | Sweep `utils/charts.py` light templates |
| B6 | Dialog/portal surfaces (new in Workstream A) need light styling | Add `[data-theme="light"]` rules for Streamlit dialog container |

### 3.2 Verification
- Manual: toggle dark→light→dark across all sections (main, sidebar, Learn, dialog).
- Playwright: `test_theme_propagates_to_iframe_body` extended to both themes.
- No changes to `VALID_THEMES` / `build_theme_css` contract; keep FOUC-prevention preemptive style.

---

## 4. Workstream C — Additional UI enhancements (prioritized)

### P0 — completes the import flow
| # | Enhancement | Notes |
|---|---|---|
| C1 | **Visible cancel/close affordance in the component itself** (IDEAS #28 intent) | A small "Cancel" button in the component that emits a cancel (maps to existing `?picker_seam=cancel` semantics) |
| C2 | **Import success feedback** | `st.toast` on success; filename is *not* displayed (no-secret boundary — use fixed "Data imported from Drive") |
| C3 | **Dialog content copy** | Caption: "Select one CSV, XLSX, or Google Sheets file." + privacy line "Only the selected file is accessed — the app does not browse your Drive." |

### P1 — quality of life
| # | Enhancement | Notes |
|---|---|---|
| C4 | Refined component status states (Loading… / Ready / Choose a file / Importing… / Imported) | Already partially present in `main.ts`; tighten copy + colors via theme tokens |
| C5 | Sidebar declutter | Diagnostics expander stays collapsed; "Setup Required" copy already improved; keep section one-liner |
| C6 | Retry affordance on Picker-lib load failure | `main.ts` already labels "Retry"; ensure button re-enables and retries cleanly |
| C7 | Accessibility pass on dialog | Streamlit dialog has focus trap; add `aria-label`s, verify ESC + focus-visible inside dialog/component |

### P2 — nice-to-haves (only if P0/P1 land cleanly)
| # | Enhancement | Notes |
|---|---|---|
| C8 | Responsive check | `width="large"` dialog on small viewports; confirm Streamlit clamps width |
| C9 | Micro-interactions | Consistent hover/active states on component button matching app buttons |
| C10 | Empty-state hero polish in light mode | Coordinate with B4 |

---

## 5. Rollout plan (no execution yet)

1. **Spike (0.5 day):** implement 2.5 open questions on a branch — `st.dialog` + component + theme-toggle-during-open. Do NOT merge until verified; decide gating pattern (a) vs (b).
2. **Workstream A (1–1.5 days):** dialog refactor of `_render_drive_picker()`; move component render + selection processing into dialog function; update sidebar copy; update `test_sidebar.py` unit tests; extend playwright smoke suite (dialog open/close/theme).
3. **Workstream B (1 day):** component theming (B1), variable consolidation (B2/B3), hero/charts audit (B4/B5), dialog light rules (B6).
4. **Workstream C P0 (0.5 day):** C1–C3 (component cancel, toast, dialog copy).
5. **Workstream C P1 (0.5 day):** C4–C7 as time allows; P2 deferred.
6. **Gate:** full pytest (672 + new), 14+ playwright smoke, frontend `npm run check && npm run build`, credential guard, manual Chrome/macOS pass of import + theme flows.
7. **Docs:** CHANGELOG entry; check off interstitial rows in `RELEASE_CHECKLIST.md` that are actually completed; leave cross-browser matrix pending.

---

## 6. Explicitly out of scope reminder

- GA4 Insights Engine, evidence connector, multimodal adapters, event-level GA4 queries → v0.4.0+ (`ROADMAP.md` gates).
- Cross-browser matrix execution (Safari/Firefox/Windows) → separate checklist track.
- No changes to the import security boundary or the `no-secret` contract.
