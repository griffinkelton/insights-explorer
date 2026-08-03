# 🔵 Interstitial UI/UX Polish — Implementation Spec

> **Status:** 🔵 In design — implementation not started
> **Date:** 2026-08-03 (refined with external review feedback)
> **Based on:** [`plans/🔵 interstitial-ui-polish-design.md`](../🔵%20interstitial-ui-polish-design.md)
> **Scope:** Workstream A (Drive Picker in `st.dialog`) + Workstream C (import-flow UX enhancements). Workstream B (light-mode redesign) is **deferred** to a future spec.
> **Delivery:** Incremental PRs per item, unversioned on `main` (no tag).
> **Effort:** ~3–4 days incl. gated Phase 0 spike.

---

## 1. Overview

v0.3.0 shipped Drive Import, but the Google Picker renders inside the ~300px sidebar iframe where its modal is cramped ("that content is not designed for that size"). This spec moves the Picker into a full-width `st.dialog` modal (Streamlit 1.60 — verified available with `width`, `dismissible`, `icon`, `on_dismiss`), adds a main-content entry point, and hardens the import flow UX (explicit cancel, success toast, dialog copy). Light-mode redesign is explicitly **out of scope** except for making the *new* dialog/component surfaces correct in both themes.

## 2. Interview decisions (the contract)

| # | Decision | Choice |
|---|---|---|
| D1 | Spec scope | **A + C now; B (light mode) deferred** to a future spec |
| D2 | Priority | Workstream A (Picker-in-dialog) is the priority |
| D3 | File format | Plain Markdown spec (the earlier "MMD" was a typo) |
| D4 | Dialog persistence | **Keep dialog open across reruns** — gate on a session flag so theme-switch-during-flow works (Functional #7–#8 parity) |
| D5 | Import error UX | **Error stays inside the dialog** with retry (fixed no-secret copy, e.g. "Import failed. Check the file format and try again." — never filenames/IDs/raw API text); dialog does not close on error |
| D6 | Entry points | **Sidebar button + main-area entry** (empty-state hero card) |
| D7 | Dismissal | **Hybrid:** standard dismissible (X / ESC / click-outside) for idle & error states; **lock dismissal while importing** via a `drive_picker_importing` flag |
| D8 | Dialog width | `width="large"` |
| D9 | Component Cancel button (C1) | **Include** |
| D10 | Success flow | **`st.toast` + auto-close dialog** |
| D11 | Theme contract | New dialog + component surfaces must be correct in **both** dark and light; broader B items still deferred |
| D12 | Test depth | **Basics + error-state-stays-open** — 5 new Playwright tests (dismissal-lock / duplicate-click / second-import as follow-ups, not committed) |
| D13 | Spike | **Phase 0 inside this spec**, gated with pass/fail criteria |
| D14 | Delivery granularity | **Incremental PRs per item** |
| D15 | Definition of Done | **Per-workstream DoD** + overall release gate |
| D16 | Versioning | Unversioned on `main`; CHANGELOG under a general interstitial heading; no tag |

### Rationale (review feedback — preserved for institutional memory)
- **A + C are coupled at the implementation level** (shared `drive_picker_dialog()`, shared Session State keys, shared Playwright selectors) → one coherent spec and acceptance checklist. **B is independent** (CSS/token-only in `utils/styles.py` + component `index.html`) → standalone `interstitial-light-mode-spec.md` later.
- **A is the #1 usability blocker**: the cramped Picker is the first thing a new user hits after OAuth; B and C are quality-of-life, A is functionality.
- **Errors stay adjacent to the action** (D5): closing to main/sidebar forces re-open + re-pick for often-recoverable errors; copy must be fixed no-secret strings.
- **C1 is a flow-level control** (intentional abandonment of the Picker specifically) vs. the dialog X/ESC which is container-level — both are needed and cheap (maps to existing `?picker_seam=cancel`).
- **`width="large"` clamping on small viewports is Streamlit's responsibility** — C8 is a P2 verification item, not a P0 implementation task.
- **Hero card gives three parallel import paths** (Upload / Connect GA4 / Drive Import) with equal visual weight; sidebar remains the primary entry.

## 3. Scope

### In scope
- **Workstream A:** `st.dialog`-based Picker with the state model below; sidebar + hero-card entry points; dismissal lock; theme-correct new surfaces; component protocol extension for explicit cancel.
- **Workstream C P0:** C1 component Cancel button, C2 success toast, C3 dialog copy.
- **Workstream C P1 (stretch):** C4 status-state copy/colors, C6 retry affordance, C7 dialog accessibility — only if P0 lands cleanly. **Not committed.**

### Out of scope (explicit)
- Full light-mode redesign (design-doc B2–B5: hex consolidation, privacy-card inline colors, hero/charts light audit) — deferred to a future spec.
- Cross-browser matrix execution (Safari/Firefox/Windows) — separate checklist track.
- GA4 Insights Engine / evidence connector / event-level data (v0.4.0+ roadmap).
- **No changes to the import security model:** `download_drive_file`, `DriveImportError`, `PickerSelection` allowlist semantics, request-freshness, no-secret boundary all stay frozen (see §5.6 for the one protocol extension and why it's boundary-safe).

---

## 4. Phase 0 — Spike (gated, ~0.5 day)

Verify before committing to the architecture. Do **not** merge spike code. The spike is a **hard gate**: Phase 1 does not start until these are resolved and documented.

**Core pass criteria (the three gating questions from the design doc §2.5):**
1. `drive_picker_transport` renders inside `st.dialog` without unexpected re-mount behavior — Picker opens at natural (large) size inside `[data-testid="stDialog"]`.
2. Gating pattern (b) on `drive_picker_active` keeps the dialog open across full-app reruns — **including a theme toggle** (component receives the updated `theme` arg).
3. `st.sidebar` is never touched inside the dialog body.

**Fail path:** if (2) does not hold, fall back to pattern (a) and document "dialog closes on unrelated full reruns" as an **accepted limitation** before proceeding to Phase 1.

**Supporting items (inform D7/D8; non-blocking if they fall back as noted):**
| # | Spike item | Success criterion | Fallback if it fails |
|---|---|---|---|
| S3 | Dynamic `dismissible`: can `dismissible` be computed per-run (e.g. re-decoration), or must it be static? | Reliable way to lock dismissal while `drive_picker_importing=True` | Static `dismissible=True` + in-dialog "Importing…" lock state (toast still reports outcome server-side) |
| S4 | Calling the dialog function from inside `with st.sidebar:` renders the modal correctly (not into the sidebar) | Modal renders in viewport center regardless of caller context | Define/call the dialog from the main-area path; sidebar only sets the flag |
| S5 | Component re-mount on dialog open: Picker lib reload is idempotent and `key=f"drive_picker_{request_id}"` stays stable | No double-load loops; ready state restored in ~1s | Accept 1s lib reload on open |

**Exit gate:** core criteria 1–3 pass; S3–S5 outcomes + gating/dismissal decisions recorded in Appendix A; Phase 1 may begin.

---

## 5. Phase 1 — Workstream A: Drive Picker in `st.dialog`

### 5.1 Architecture & state model

```python
@st.dialog("Import from Google Drive", width="large",
           dismissible=not st.session_state.get("drive_picker_importing", False))  # per spike S3
def drive_picker_dialog() -> None:
    _render_and_process_picker()  # component render + selection handling (moved from sidebar inline path)

# Entry points (sidebar button + hero card) both do:
if clicked:
    st.session_state.drive_picker_request_id = str(uuid.uuid4())
    st.session_state.drive_picker_active = True

# Dialog is called every run while active (keeps it open across reruns — D4):
if st.session_state.get("drive_picker_active"):
    drive_picker_dialog()
```

**Session state keys (extended from today):**
| Key | Type | Purpose |
|---|---|---|
| `drive_picker_active` | bool | Dialog open gate; persists across reruns (D4) |
| `drive_picker_request_id` | str | Freshness token; new UUID per activation |
| `drive_picker_importing` | bool | **New** — True between file-pick and ingest completion/error; drives dismissal lock (D7) and "Importing…" state |

### 5.2 Entry points
- **Primary — sidebar button** (unchanged label/position): sets the flag instead of rendering inline. Existing users expect it beside Upload and GA4 Connect.
- **Secondary — empty-state hero card** (`components/hero.py`, shown only when no data is loaded): a "📂 Import from Google Drive" card with **equal visual weight** alongside the existing Upload and Connect-GA4 affordances — three parallel import paths. Same gating (authenticated + Picker secrets configured) and the identical flag-setting path; reuses the dialog with no duplicated logic. Coordinates with C10/B4 hero polish (deferred).

### 5.3 Dialog behavior matrix

| Case | Behavior |
|---|---|
| Click Import (sidebar or hero card) | `drive_picker_active=True` → dialog opens (`large`), component mounts, Picker lib loads (~1s) |
| Pick a file | Component emits `{kind:"picked", requestId, fileId}` → freshness check → `drive_picker_importing=True` → `_ingest_drive_file()` → success: `st.toast("✓ Data imported from Drive")`, `active=False`, `importing=False`, `st.rerun()` (closes dialog, D10) |
| Ingest error (download/parse) | `st.error` renders **inside dialog** with fixed no-secret copy (e.g. "Import failed. Check the file format and try again." — never filenames/IDs/raw API text), dialog stays open, `importing=False`, component button resets → retry or dismiss (D5) |
| Cancel (component Cancel btn C1 / Picker CANCEL) | Component emits explicit `{kind:"cancel", requestId}` (see §5.6) → `active=False`, `st.rerun()` closes dialog; sidebar button resets |
| Dismiss (X / ESC / click-outside) while idle/error | `on_dismiss` → `active=False`; state reset (D7 — allowed in these states) |
| Dismiss attempt while importing | **Locked** (D7): dialog not dismissible; "Importing…" state visible |
| Theme toggle during active flow | Full rerun; `drive_picker_active` still True → dialog re-called → stays open; component gets new `theme` arg (S2) |
| Second import | Button available; new `requestId`; fresh dialog; frontend relabels "✔ Imported — Open Another File" (existing) |

### 5.4 Cancel-close asymmetry (important design consequence)
Today the component only emits on **PICKED**; a Picker CANCEL returns `None` to Python, which cannot distinguish "cancelled" from "not yet returned". The dialog needs to close on cancel, so:
- **Component** emits an explicit `{kind: "cancel", requestId}` on Picker-CANCEL and on the new C1 Cancel button.
- **Wrapper** (`drive_picker_transport`) gains a second allowlisted shape: `PickerResult = PickerSelection | CancelSelection | None`, where `CancelSelection = {kind:"cancel", requestId}` (requestId still validated as `str`).
- **Boundary-safe:** cancel carries only `kind` + `requestId` — no filename, MIME, URL, token, or raw callback data. The existing test-mode seam (`?picker_seam=cancel`) maps to this shape and closes the dialog.

### 5.5 Theme contract for new surfaces (D11)
- Dialog container: add `[data-theme="light"]` rules in `utils/styles.py` for the Streamlit dialog surface.
- Component `index.html`: keep self-contained `data-theme` blocks (iframes can't read parent CSS vars) but align light values to app tokens (`#ffffff` bg, `--bg-card`-equivalent button) instead of today's `#fafafa`/`#f0f0f5`.
- Broader light-mode redesign remains deferred (B2–B5).
- **Small-viewport behavior:** `width="large"` clamps to viewport width natively in Streamlit — no custom CSS needed. C8 (responsive verification) is a P2 check, not a P0 task.

### 5.6 Test impact & new tests (D12 — basics)
- `_click_import` (sidebar button) unchanged; `_picker_iframes()` (title `drive_picker_transport`) still finds the iframe — now inside the dialog.
- `test_picker_iframe_not_visible_initially` and `test_import_section_hidden_without_auth` remain valid (with the env-var-bleed fix from `ee45817`).
- **New Playwright smoke tests (5, D12):**
  1. `test_dialog_opens_on_click` — `[data-testid="stDialog"]` visible after clicking Import; iframe inside it.
  2. `test_dialog_closes_on_cancel_seam` — `?picker_seam=cancel` → dialog gone, sidebar button visible/enabled.
  3. `test_dialog_closes_after_picked_seam` — `?picker_seam=picked` → dialog gone (success path).
  4. `test_theme_propagates_to_dialog_component` — theme arg reaches iframe body `data-theme` in both themes; dialog stays open across the toggle.
  5. `test_error_state_keeps_dialog_open` — after a failed import (error seam), dialog stays open and `st.error` is visible — verifies the deliberate "stay in dialog + retry" decision (D5).
- Dismissal-lock-while-importing, duplicate-click, and second-import coverage are **follow-ups** once the happy path is confirmed (not committed here).
- **Unit tests:** update `test_sidebar.py` for the new state model (`drive_picker_importing` lifecycle; cancel closes dialog). `test_drive_picker_component.py` extended for the new cancel shape (allowlisted, no metadata).

---

## 6. Phase 2 — Workstream C: import-flow enhancements

| # | Item | Details | Status |
|---|---|---|---|
| C1 | Component Cancel button | Small "Cancel" button in component that emits `{kind:"cancel"}` (with Picker-CANCEL wiring from §5.4) | **Committed (D9)** |
| C2 | Success toast | `st.toast("✓ Data imported from Drive")` on success; **no filename** (no-secret boundary) | **Committed (D10)** |
| C3 | Dialog copy | Caption: "Select one CSV, XLSX, or Google Sheets file." + privacy line "Only the selected file is accessed — the app does not browse your Drive." | **Committed** |
| C4 | Status-state copy/colors | Loading… / Ready / Choose a file / Importing… / Imported; theme-token colors | Stretch |
| C5 | Sidebar declutter | Diagnostics expander stays collapsed; one-liner under section header | Stretch |
| C6 | Retry affordance | Picker-lib load failure → "Retry" re-enables and reloads cleanly | Stretch |
| C7 | Dialog accessibility | Verify focus trap, ESC, `aria-label`s on dialog + component controls | Stretch |

---

## 7. Deferred (explicit)

- **Workstream B (light-mode redesign):** B2 hex consolidation, B3 privacy-card inline colors, B4 hero/charts light audit, B5 charts light sweep → standalone `interstitial-light-mode-spec.md` (future; independent — CSS/token only). (B1 component theming and B6 dialog light styling are pulled **into** this spec via D11.)
- **C8–C10 (responsive, micro-interactions, hero polish):** nice-to-haves, not committed.
- Cross-browser matrix execution.

---

## 8. Delivery & versioning

- **Incremental PRs** (D14), each with a reviewable scope, a passing test suite, and a clear rollback boundary:
  - **PR 1 (docs):** Phase 0 spike verification result + gating/dismissal decision record (Appendix A).
  - **PR 2 (Workstream A):** state model + dialog refactor of `_render_drive_picker()`; hero-card entry; `test_sidebar.py` updates; new Playwright dialog tests (incl. error-stays-open).
  - **PR 3 (Workstream C P0):** C1 cancel (component + wrapper cancel shape), C2 toast, C3 dialog copy.
  - **PR 4 (Workstream C P1, if time permits):** C4 status states, C6 retry, C7 a11y.
  - Docs: CHANGELOG entry (general interstitial heading — D16) + `RELEASE_CHECKLIST.md` interstitial rows checked off as they land.
- **No tag, no version bump.** Work lands on `main`; v0.4.0 inherits it naturally (D16). The "one UX story" framing applies to the CHANGELOG entry, not the PR structure.

---

## 9. Definition of Done

Per-workstream pass criteria — each row is an independent merge gate (maps to the PR structure in §8):

| Item | Pass criteria | Verified by |
|---|---|---|
| Phase 0 spike | Core criteria 1–3 pass; gating + dismissal decisions documented in Appendix A | PR 1 |
| Dialog flow | Opens on sidebar + hero-card click; closes on success/cancel; `[data-testid="stDialog"]` present; Picker at natural width | PR 2 + smoke tests 1–3 |
| Error state | `st.error` visible inside dialog after failed import; dialog stays open; button resets; no-secret copy | PR 2 + smoke test 5 |
| Dismissal lock | Dialog not dismissible while `drive_picker_importing=True` | PR 2 (per S3 outcome) |
| Theme (new surfaces) | `data-theme` propagates to dialog + component iframe in both themes; dialog stays open on toggle | PR 2 + smoke test 4 |
| Cancel (C1) | Component Cancel button emits validated cancel shape; dialog closes; sidebar button resets; no-secret boundary intact | PR 3 + unit tests |
| Toast (C2) | `st.toast` fires on success; fixed copy; no filename exposed | PR 3 |
| Dialog copy (C3) | Format + privacy copy present in dialog | PR 3 |
| Failure preservation | Failed import leaves prior DataContext + derived state untouched (existing contract) | unit tests |

### Overall gate (after C work completes)
- [ ] Full pytest suite green (672 + new unit tests) incl. `tests/ --ignore=tests/test_drive_import_smoke.py --ignore=tests/e2e`.
- [ ] Playwright smoke **19** (14 existing + 5 new) — both invocation modes (with/without `DRIVE_PICKER_TEST_MODE=1`).
- [ ] E2E leakage suite unaffected (L1–L5) — no new sensitive output.
- [ ] Frontend `npm ci && npm run check && npm run build` clean; credential guard exit 0.
- [ ] Manual Chrome/macOS pass: import CSV/XLSX/Sheets, cancel, second import, theme toggle during active flow, error paths E1–E6 display in-dialog.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Custom component re-mounts inside dialog (state loss / lib reload) | S1/S5 spike; stable `key`; idempotent lib load |
| Dialog persistence semantics differ from expectation | S2 spike gates the whole design; fallback documented |
| Dynamic `dismissible` unsupported | S3 spike; fallback = static dismissible + lock-state overlay |
| Cancel-close asymmetry (Python can't see None-cancel) | §5.4 explicit cancel protocol extension — boundary-safe |
| Hero-card gating duplicates sidebar logic | Single shared flag-setting helper + dialog; hero card only visible when gated |
| Test flakiness around dialog timing | Generous waits (reuse `SIDEBAR_WAIT`), dialog locator `[data-testid="stDialog"]` |

---

## 11. Reference files

- Design doc: [`plans/🔵 interstitial-ui-polish-design.md`](../🔵%20interstitial-ui-polish-design.md)
- Current implementation: `components/sidebar.py` (`_render_drive_picker`), `components/drive_picker_component.py`, `components/drive_picker_component_frontend/src/main.ts` + `index.html`, `utils/styles.py`
- Test suites: `tests/test_drive_import_smoke.py`, `tests/test_sidebar.py`, `tests/test_drive_picker_component.py`, `tests/test_drive_import_errors.py`
- Parent deferrals: [`RELEASE_CHECKLIST.md`](../../RELEASE_CHECKLIST.md) — "Deferred to v0.3.0→v0.4.0 interstitial"
- IDEAS.md #28 (component UX polish intent)

---

## Appendix A — Spike results (fill in after Phase 0)

| Item | Result | Notes |
|---|---|---|
| Core 1 — component renders in dialog, no re-mount | | |
| Core 2 — pattern (b) survives reruns incl. theme toggle | | |
| Core 3 — no `st.sidebar` inside dialog body | | |
| S3 — dynamic `dismissible` | | |
| S4 — dialog called from `with st.sidebar:` context | | |
| S5 — re-mount idempotency / stable `key` | | |
