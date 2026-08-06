# Phase 2 — Decouple `utils/` from Streamlit (outline — stub)

> ⚪ **STUB** — Phase 2 gate closed. Expand to executable when Phase 1 closes (per the gate flow in `README.md`). No code is written from this file yet.

## Purpose

Remove Streamlit coupling from the Python `utils/` layer so FastAPI can call the same services as Streamlit. 7 of 16 utils modules currently couple to `st.session_state` (archive §4.2). The vertical-slice adapters in Phase 1 (`parse_uploaded_file`, `build_quality_report`) already point at the decoupled targets (`utils/data_loader.load_file()`, `utils.data_loader.assess_data_quality`).

## Inputs / source documents

- `../policies/session-state-inventory.md` — the 44-key replacement map (Phase 2's checklist)
- `../policies/test-layer-inventory.md` — which of the 742 tests transfer vs rewrite/retire
- `../archive/insights-explorer-migration-ingest.md` Part 4 (reconciliation facts: 7/16 utils coupling)
- master-plan §6

## Tracks consumed

- **A** (state/session): the 44-key replacement map in `../policies/session-state-inventory.md` is this phase's checklist; any new key during the freeze must be documented per `../policies/branch-and-freeze-policy.md`.
- **B** (API/contract): the Phase 1 adapter error taxonomy stays identical when `parse_uploaded_file()` → `utils/data_loader.load_file()`.
- **C** (tests): 452 utils-facing tests transfer; 290 Streamlit-layer tests retire per `../policies/test-layer-inventory.md`.

## Research gate

**None required** — internal refactoring; no external platform facts. (Do not dispatch a research agent for Phase 2.)

## Task outline (expand before execution)

- [ ] Inventory per-module Streamlit imports (`st.` / `st.session_state` / `st.cache_data`) — reconcile against `session-state-inventory.md`.
- [ ] Extract pure functions: `utils/data_loader.py` `load_file(path_or_bytes)` (no cache/UI coupling), `utils/data_context.py` filter/metric/provenance rules, `utils/session.py` key accessors → explicit arguments.
- [ ] Replace `parse_uploaded_file()` (Phase 1) with `utils/data_loader.load_file()`; keep the error taxonomy identical.
- [ ] Convert `st.cache_data` caches to explicit memoization or dependency injection (no implicit caching in the API layer).
- [ ] Keep Streamlit behavior identical (feature freeze: no new `st.session_state` keys — replacement must be documented per `../policies/branch-and-freeze-policy.md`).
- [ ] Retire or rewrite the 290 Streamlit-layer tests; keep 452 utils-facing tests green (per `../policies/test-layer-inventory.md`).
- [ ] Verify GA4/Drive/Gemini clients are framework-neutral (they are already HTTP-layer; confirm no `st.` imports).

## Exit criteria

- [ ] No `utils/` module imports `streamlit` (or the API entry path is fully decoupled).
- [ ] 452 utils-facing tests green; Streamlit smoke still passes.
- [ ] Phase 1 endpoints work against the decoupled loaders (contract tests re-run green).

## Gate table — Phase 2 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 2 — decoupled `utils/` | Zero `st.` imports in `utils/` · 452 utils tests green · Phase 1 contract tests green on decoupled loaders | Implementation agent | Record evidence; flip `specs/README.md` status; expand `phase-3-ai-analysis.md` to ACTIVE after its research gate |

## Parked/absorbed content

None — Phase 2 is internal refactoring; F3/F4 don't cover it (F4 §6 adapter note points here).
