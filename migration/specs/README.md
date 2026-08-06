# `migration/specs/` — Tactical Execution Index

The **tactical** layer of the React/FastAPI migration. Each phase of the migration has one executable spec here. This README is the authority map: it identifies the **currently active spec**, the phase gates, the source documents each spec draws from, and the supersession rules.

> ## Current execution target
>
> **Phase 1 is DONE** (`eaa6ac5` + `66c0f1d` on `feat/react-fastapi-migration`; 782 tests, guard exit 0; live smoke verified).
>
> **Phase 2 is DONE** (`8c66eea` on `feat/react-fastapi-migration`; 794 tests, guard exit 0). The utils layer is framework-decoupled: import-boundary guard, fingerprint memo, `UsageEvent` usage accounting, structured `DatasetWarning`, `load_file()` adapter, quarantine banners.
>
> **Next spec:** [`phase-3-ai-analysis.md`](phase-3-ai-analysis.md) — **EXECUTION-READY** (2026-08-06). Research gate run (Gemini production readiness) and **all 13 decisions confirmed + refined**. Commits: expansion `bbd15e7` · decisions `75630d4` · refinement `e4bd063` · policy sync `b6f56c5`. Awaiting owner greenlight to begin on `feat/react-fastapi-migration`.

**Strategic authority:** `migration/master-plan.md` (phases, locked decisions, risk register). **Evidence authority:** `migration/archive/insights-explorer-migration-ingest.md` (Parts 1–4: synthesis, verbatim sources, live-verified research, reconciliation ledger). **Semantic authority:** `../../plans/ga4-measurement-contract.md` (metrics + metric-status consumption policy). This folder turns those into **task-ordered, executable instructions** — file-level steps, code, acceptance criteria, and per-phase gates.

---

## Why a suite, not a monolith

A single "master implementation spec" would go stale: later phases depend on fresh external research (Gemini before Phase 3, React 19 before Phase 4, GA4/Drive before Phase 5, Cloud Run before Phase 6 — see the research queue in archive §3.12). Each phase file is therefore **expanded only when its gate opens**; before that it is a stub recording scope, inputs, research gates, and exit criteria. The fully executable files today are Phases 1–2 (done) and Phase 3 (execution-ready).

## Phase/spec status table

| Spec | Status | Gate |
|---|---|---|
| Phase 1 — upload slice (`phase-1-upload-slice.md`) | ✅ **DONE** | Gate 7 closed 2026-08-06 — 782 passed, guard exit 0, commits `eaa6ac5` + `66c0f1d` |
| Phase 2 — utils decoupling (`phase-2-utils-decoupling.md`) | ✅ **DONE** | Closed 2026-08-06 — `8c66eea` on `feat/react-fastapi-migration`, 794 passed, guard exit 0, hooks green |
| Phase 3 — AI/analysis (`phase-3-ai-analysis.md`) | 🔵 **ACTIVE — execution-ready** | Research gate run + all 13 decisions confirmed/refined 2026-08-06 (`bbd15e7`/`75630d4`/`e4bd063`/`b6f56c5`); awaiting owner authorization |
| Phase 4 — React port (`phase-4-react-port.md`) | ⚪ STUB | React/Recharts verification gate |
| Phase 5 — GA4/Drive (`phase-5-ga4-drive.md`) | ⚪ STUB | GA4 + selected Drive UX research |
| Phase 6 — cutover/hosting (`phase-6-cutover-hosting.md`) | ⚪ STUB | Cloud Run readiness gate |

> **Branch-state note (2026-08-06):** Phase 1 + Phase 2 implementations are complete
> on `feat/react-fastapi-migration`; `main` carries the reconciled planning/documentation
> record until the migration branch is merged. **Review implementations on the migration
> branch — `main` holds docs only.**

**Status flow:** `STUB` → (research gate run) → expanded to `ACTIVE` → gate evidence recorded → `DONE`. Flip the banner at the top of this file and the Status column when a phase becomes active.

## How to use this suite

1. **Start at the ACTIVE spec.** Read it top to bottom; it is task-ordered and self-contained (code is embedded, not referenced away).
2. **Consult source documents for rationale.** Each phase spec lists its inputs. The archive is evidence — quoted material there is never rewritten.
3. **When a phase gate opens** (master-plan §4–5, §13 open decisions): run the phase's research prompt from the queue (archive §3.12) **before** expanding its stub, then expand the stub into an executable spec following the Phase 1 file's structure.
4. **Never re-litigate locked decisions.** Canonical contract shapes, the 25 MB/100 MB upload policy, metric-status policy, state placement, npm, `/api/v1` — all locked in master-plan §4–5 and recorded in each phase spec.

---

## Phase 0 — recorded execution (no re-doable work)

Phase 0 gates are **closed** and recorded; the spec suite treats them as settled preconditions:

| Gate | Status | Closure evidence |
|---|---|---|
| 1 — Credential remediation | ✅ Closed 2026-08-06 | `../policies/env-rotation-checklist.md` (keys rotated/revoked, `.env` untracked in whisperer-30 and merged to `main` as `a4d72e8`, history scans clean) |
| 2 — Migration branch + freeze | ✅ Closed 2026-08-06 | `../policies/branch-and-freeze-policy.md` (`feat/react-fastapi-migration` created + pushed; Streamlit feature freeze active on `main`) |
| 6 — Retention/AI boundary | ✅ Closed 2026-08-06 | `../policies/data-retention-policy.md` §11 (five defaults approved by product owner) |
| 7 — Vertical slice | 🟢 **Open** | This is the authorization to execute `phase-1-upload-slice.md` |

**Branch rule (frozen):** migration *product code* lands on `feat/react-fastapi-migration`; docs and index updates land on `main` (per `../policies/branch-and-freeze-policy.md`). The active spec's changes are committed to the migration branch; the suite's status flips are docs on `main`.

## Cross-cutting tracks (span all phases)

From master-plan §11. Each phase spec lists the track work it consumes; the tracks themselves are owned by the policy docs below.

| Track | Canonical source | Used by | Spanning rule |
|---|---|---|---|
| **A. State/session** | `../policies/session-state-inventory.md` | 1, 2, 4, 5 | 44 `st.session_state` keys → server-side replacements; new keys during the freeze need a documented replacement. State placed **by type** (cookie / ephemeral store / shared store / object storage / memory cache / encrypted durable / Postgres-later). |
| **B. API/measurement contract** | `../../plans/ga4-measurement-contract.md` + archive §4.2/§4.11 | 1–5 | `/api/v1` from day one; snake_case at the boundary; typed client generated/validated from OpenAPI; metric-status policy (validated / provisional / unavailable) enforced. |
| **C. Tests** | `../policies/test-layer-inventory.md` | 1–6 | 742 = 452 utils-facing (transfer) + 290 Streamlit-layer (rewrite/retire) + 40 Playwright E2E. Four-layer matrix: Python unit · FastAPI contract · React (MSW) · Playwright. |
| **D. Security/credentials** | `../policies/env-rotation-checklist.md` + `scripts/check_credentials.py` | 1, 5, 6 | Guard extended to the FastAPI env-var **allowlist** (names only); `.env.example` carries all names; `__Host-` cookie in production; never log keys or echo tokens. **Step 1 of Phase 1** is the guard allowlist. |
| **E. CI/CD** | `.github/workflows/test.yml` + `cloudbuild.yaml` + `../policies/dockerfile-pattern.md` | 1, 4, 6 | Frontend gate (`npm ci` → typecheck → build) added alongside pytest; container deployment to Cloud Run in Phase 6; smoke script reworked for the new stack. |
| **F. Retention/AI boundary** | `../policies/data-retention-policy.md` | 1, 3, 5, 6 | Effective retention ≤ session expiry (≤12 h Phase 1); Clear Data semantics; export metadata only; Gemini allowlist-only. |
| **G. Research discipline** | archive §3.12 (research-gating policy + prompt queue) | 3–6 | Dispatch the phase's research prompt immediately before its gate opens; separate documentation facts from property-specific probes (GA4); external research never overrides canonical internal decisions without a reconciliation step. |

## Release gates (overall summary)

The three non-negotiable release gates (master-plan §14) map to each phase; each phase spec carries its own gate table. Phases are **independently closeable**:

| Phase | Release gates that matter |
|---|---|
| 1 — Upload slice | Python regression · API contract · upload/preview/clear user flow |
| 2 — Utils decoupling | Python regression · framework-decoupling import checks |
| 3 — AI/analysis | API contract · Gemini/provider behavior · analysis flows |
| 4 — React port | React build/typecheck · MSW component behavior · basic frontend flow |
| 5 — GA4/Drive | OAuth + Drive Playwright E2E matrix |
| 6 — Cutover/hosting | Full parity · hosted deployment · rollback · accessibility/performance · smoke tests |

## Supersession rules

- **F3 (`freebuff-prompt-wire-react-store.md`) and F4 (`phase-1-api-react-callback-tests-implementation.md`) are SUPERSEDED FOR EXECUTION** — banner-marked at the top of each file (2026-08-06). They remain in `specs/` as reference evidence and historical implementation input; the suite is the current tactical authority:
  - F4's vertical-slice content → `phase-1-upload-slice.md` (embedded + task-ordered)
  - F4's GA4 OAuth adapters + React callback route → parked in `phase-5-ga4-drive.md`
  - F4's React API client (`api-types.ts`, `api.ts`) → parked in `phase-4-react-port.md`
  - F3's 13-step store wiring → parked in `phase-4-react-port.md` (with `whisperer-30-reference/STORE-DRIFT-MATRIX.md`)
- **Archive rule:** F3/F4 move to `../archive/` only *after* their owning phase's implementation PR merges (per the master-plan review lifecycle classification).
- The **verbatim transcript** (`../archive/freebuff-conversation-080525.sanitized.md`) is never an implementation authority and is never edited.
- Later corrections append as **dated addenda** in the affected phase spec — never silent rewrites (master-plan addenda convention).

## Source document map

| Source | Feeds |
|---|---|
| `../master-plan.md` | All phases (locked decisions, DoD, risk register, open decisions) |
| `../archive/insights-explorer-migration-ingest.md` | All phases (evidence, research §3, reconciliation §4) |
| `../archive/insights-explorer-migration-plan.md` | Phase shapes 1–6, contract draft |
| `phase-1-upload-slice.md` (this suite) | **Active** Phase 1 execution |
| `whisperer-30-reference/UI-CAPTURE-8b4b7b9/MANIFEST.md` | Phase 4 port (frozen source + classification) |
| `whisperer-30-reference/STORE-DRIFT-MATRIX.md` | Phase 4 store wiring |
| `whisperer-30-reference/LOVABLE-UPDATES-080525.md` | Phases 4–5 (Drive-import UI, contract transcription) |
| `../policies/*` | Cross-cutting tracks A–G |
| `../../plans/ga4-measurement-contract.md` | Metric semantics + status policy (Phases 1, 5) |

*Created 2026-08-06 per product-owner interview (suite-over-monolith decision). Suite is planning-only: no migration product code has been written. Active spec: `phase-1-upload-slice.md`.*
