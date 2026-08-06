# Phase 4 — Port React UI into `frontend/` (outline — stub)

> ⚪ **STUB** — Phase 4 gate closed. **Research gate must run before this stub is expanded** (see below). No code is written from this file yet.

## Purpose

Port the captured `insights-whisperer-30` UI into `frontend/` and wire the store to the real API. **This file is the tactical authority for F3's content** — F3 (`freebuff-prompt-wire-react-store.md`) is **superseded for execution** and retained as reference. The port is driven from `../whisperer-30-reference/UI-CAPTURE-8b4b7b9/` (frozen source + classification manifest) and `../whisperer-30-reference/STORE-DRIFT-MATRIX.md` (captured store vs F3 — the Phase 4 instruction set).

## Inputs / source documents

- `../whisperer-30-reference/UI-CAPTURE-8b4b7b9/MANIFEST.md` — per-file `runtime_dependency` / `initial_mount` classification (94 files)
- `../whisperer-30-reference/STORE-DRIFT-MATRIX.md` — 13-row drift matrix (captured behavior × F3 assumption × canonical decision × required change)
- F3 (superseded reference), F4 §10–12 (React API client + MSW test pattern — parked here), `../whisperer-30-reference/WHISPERER-30-REFERENCE.md` (what was captured and why)
- master-plan §8 (Phase 4), §11-B (contract), §12 (layout), §13 (open decisions #3 npm, #5 Recharts), §17 (accessibility baseline)
- `../policies/branch-and-freeze-policy.md` (package-manager lock: **npm**, lockfile `package-lock.json`, CI `npm ci`)

## Tracks consumed

- **A** (state/session): the store's client state maps to server-owned sessions — browser holds only the opaque `HttpOnly` cookie (STORE-DRIFT-MATRIX row: no client-authoritative dataset reference).
- **B** (API/contract): `api.ts` performs snake_case → camelCase normalization against the OpenAPI contract; `/api/v1` only.
- **C** (tests): MSW component tests (F4 §12 pattern parked here) + the basic frontend-flow release gate.
- **E** (CI/CD): `npm ci` → typecheck → build gate added to `.github/workflows/test.yml`.
- **G** (research discipline): React 19 + Recharts compatibility check runs before this stub expands.

## Research gate — REQUIRED before expansion

Run the **React 19 + Recharts compatibility** check (archive §3.12 queue, Phase 4 row): lock exact package versions from the captured `package.json` (React 19, Vite 8, TanStack Router 1.170.x, `ai` SDK 7, Tailwind v4, Recharts), decide Recharts 2.15.4 vs 3.x (open decision #5: try 2.15.4 first; `overrides` or 3.x on peer errors). Return locked versions + any override/upgrade decision.

## Task outline (expand before execution)

- [ ] Scaffold `frontend/` (npm, Vite, TanStack Router) per the capture's stack config; regenerate `routeTree.gen.ts` (captured copy is reference only — do not port).
- [ ] Copy components by manifest classification: **Port/adapt** shells (ChartsRow, DataPreview, Chat, EmptyHero — shell copied, mock data source replaced); **Fixture-only** mocks → `src/test/fixtures/` (MSW); **Reference/prototype** (EquityPanel, ResearchPanel, evidence panels) stay out of the production runtime; DriveImportSheet is a **Phase 5 UI candidate only**.
- [ ] Quarantine rules (master-plan §12): production never imports from `test/fixtures/`; prototype pages excluded or demo-flagged; `initial_mount` = `functional` (upload/preview/quality/clear + shell) | `placeholder` (optional) | `deferred` (Chat, AiSummary, ExportMenu, onboarding, Drive sheet, panels).
- [ ] Store wiring per the drift matrix: real `fetch()` via `frontend/src/lib/api.ts` (`credentials: "include"`, snake_case→camelCase normalized once in `setSourceFromApi`); filter/metric changes synced via explicit API calls; chat uses plain SSE reader matching the Phase 3 wire decision.
- [ ] MSW test setup (`onUnhandledRequest: "error"` — live-verified `msw@2.15.0` default is `warn`); typed search params (`validateSearch`/`errorComponent`) for the GA4 callback route (parked content from F4 §11).
- [ ] Accessibility + performance baselines per master-plan §17 (keyboard-operable controls, non-color-only states, bundle <500 KB gzipped, dashboard <2 s, preview <1 s).

## Exit criteria

- [ ] `npm ci && npm run check && npm run build` green in CI (frontend gate).
- [ ] Upload → preview → quality → clear works in React against FastAPI (MSW + real).
- [ ] No production import of mock/prototype modules; all 94 manifest rows accounted for.
- [ ] Playwright user-flow gate: upload → preview → clear (GA4/Drive/chat cases join at their phases).

## Gate table — Phase 4 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 4 — React port | Frontend gate green · MSW tests green · store wired to real API · a11y/performance checks pass | Implementation agent + reviewer | Record evidence; flip `specs/README.md`; expand `phase-5-ga4-drive.md` to ACTIVE after its GA4/Drive research gates |

## Parked/absorbed content (from F3/F4)

- **F3's 13-step store wiring** → the drift matrix supersedes it in depth; the matrix is the instruction set (`../whisperer-30-reference/STORE-DRIFT-MATRIX.md`).
- **F4 §10** `frontend/src/lib/api-types.ts` + `api.ts` (typed client; `API_BASE` from `VITE_API_BASE` or `/api` — Phase 6 makes it same-origin).
- **F4 §11** React GA4 callback route (`/auth/ga4/callback`) — typed `validateSearch` for `status`/`reason`; store addition `setSourceFromApi(dataset)`.
- **F4 §12** MSW test dependencies (`vitest`, `msw`, Testing Library), `handlers.ts`, `server.ts`, `setup.ts`, upload/error/OAuth test patterns.
