# Phase 4 — Port React UI into `frontend/`

> 🔵 **ACTIVE — expanded from the stub (2026-08-06), execution-ready pending Task 0 research probes.**
> Phase 3 (AI/analysis) is DONE (`bb6f564`, 859 tests). This file is the **tactical authority** for the
> React frontend port. F3 (`freebuff-prompt-wire-react-store.md`) is **superseded for execution** and
> retained as reference; `STORE-DRIFT-MATRIX.md` is the store-wiring instruction set.
> **Review implementations on `feat/react-fastapi-migration` — `main` holds docs only.**

## Purpose

Port the captured `insights-whisperer-30` UI into `frontend/` and wire the store to the real
FastAPI surface built in Phases 1–3. The port is made from the **frozen capture**
`../whisperer-30-reference/UI-CAPTURE-8b4b7b9/` (never a live clone), classified by its
`MANIFEST.md`, and wired row-by-row per `STORE-DRIFT-MATRIX.md`.

First-slice scope is the **upload → preview → quality → clear** flow plus the app shell.
`deferred` components (Chat, AiSummary, ExportMenu, OnboardingTour, Drive sheet, panels, learn
page) are ported in their owning phases — the manifest's `initial_mount` column decides.

## Inputs / source documents

- `../whisperer-30-reference/UI-CAPTURE-8b4b7b9/MANIFEST.md` — 94-file classification
  (`runtime_dependency`, `initial_mount`); **the port inventory.**
- `../whisperer-30-reference/STORE-DRIFT-MATRIX.md` — 13-row captured-vs-F3 drift matrix;
  **the store-wiring instruction set (Task 4 is row-by-row).**
- `../whisperer-30-reference/package.json` — captured dependency pins (Task 0 reads these).
- F3 (superseded reference), F4 §10–12 (parked: api client, GA4 callback route, MSW pattern),
  `../whisperer-30-reference/WHISPERER-30-REFERENCE.md`.
- master-plan §8 (Phase 4), §11-B (contract), §12 (target layout + prototype quarantine),
  §13 (open decisions #3 npm, #5 Recharts, #1 SSE), §17 (a11y + performance baselines).
- `../policies/branch-and-freeze-policy.md` (package-manager lock: **npm**, `package-lock.json`, CI `npm ci`).
- Phase 3 spec `phase-3-ai-analysis.md` — the SSE wire format, typed error codes, and endpoint
  contracts this frontend consumes (Tasks 5, 6, 8).

## Tracks consumed

- **A** (state/session): browser holds only the opaque `HttpOnly` cookie; the store holds client
  view state; the server resolves dataset/filters/metrics from the session (drift rows 1–4).
- **B** (API/contract): `api.ts` normalizes snake_case → camelCase once; `/api/v1` only.
- **C** (tests): MSW component tests (F4 §12 parked pattern) + the frontend-flow release gate.
- **E** (CI/CD): `npm ci` → typecheck → build gate in `.github/workflows/test.yml`.
- **G** (research discipline): Task 0 version-pin + Recharts probe runs before build work.

---

## Task 0 — Research gate: version pins + Recharts × React 19 probe

> The captured `package.json` (frozen at `8b4b7b9`) is the version source. Lock these **exact**
> pins into `frontend/package.json` at scaffold time and **record the resolved versions** in the
> Phase 4 gate table. Do not float ranges.

**Locked pins (from the capture — `^` ranges resolve at install; record the resolved versions):**

```text
react                ^19.2.0          react-dom              ^19.2.0
vite                 ^8.1.5           @vitejs/plugin-react   ^5.2.0
@tanstack/react-router  ^1.170.18     @tanstack/react-query  ^5.101.1
@tanstack/router-plugin ^1.168.23     tailwindcss            ^4.2.1
@tailwindcss/vite    ^4.2.1           recharts               ^2.15.4
ai                   ^7.0.48          zod                    ^3.24.2
lucide-react         ^0.575.0         date-fns               ^4.1.0
typescript           ^5.8.3           vitest                 (add; see Task 6)
msw                  ^2.15.0          @testing-library/react (add; see Task 6)
```

**Strip list — do NOT install (Lovable/Nitro/Start plumbing; archive §3.10 item 2):**

```text
@lovable.dev/vite-tanstack-config   @tanstack/react-start   nitro
```

**Recharts × React 19 probe (open decision #5):**

1. `npm install` with `recharts@^2.15.4` first — `recharts` 2.x does **not** declare React 19
   peer deps; npm may emit `ERESOLVE`.
2. On peer errors: try npm `overrides` (`"overrides": { "recharts": { "react": "^19.2.0" } }`)
   or `--legacy-peer-deps` for the initial install **only** (not CI).
3. If neither yields a clean `npm ci` + build: move to `recharts@^3.x` and record the version.
4. **Acceptance:** `npm ci && npm run build` green with the chosen resolution; record
   `recharts <resolved>` in the gate table.
5. **Lockfile discipline:** commit `frontend/package-lock.json` with the resolved versions of
   React, TanStack Router/plugin, Vite, Tailwind, Recharts (if used), MSW, and every
   shadcn-generated dependency. CI installs with `npm ci` only; version bumps are deliberate,
   reviewed PRs — never floating-range drift. Recharts stays **absent** from the first-slice
   runtime if ChartsRow is a visual placeholder; do not add it merely for future use.

**TanStack Router validation probe (parked from F4 §11; master-plan §8):** verify
`validateSearch` + `errorComponent` behavior against the resolved router version
(`error.routerCode === "VALIDATE_SEARCH"` path) — a one-file spike route, not a task blocker
(GA4 callback lands Phase 5; the spike validates the pattern now).

---

## Task 1 — Scaffold `frontend/`

Create `frontend/` as a **sibling of `api/`** (master-plan §13 decision #6; owner decision 2026-08-06), npm-based, from the strip-list-derived stack. **Do not port `routeTree.gen.ts`** — regenerate via the router plugin (captured copy is reference only).

**Dev topology — owner decision 2026-08-06: plain Vite SPA + TanStack Router, Vite proxy to FastAPI.** Two dev processes, one browser-facing origin. Do NOT use TanStack Start (its SPA mode still carries Start build/runtime machinery — unnecessary when FastAPI owns the server).

```text
Terminal 1:  uvicorn api.main:app --reload --port 8000
Terminal 2:  cd frontend && npm run dev
Browser:     http://localhost:5173  (Vite proxies /api → http://127.0.0.1:8000)
```

```bash
# Scaffold (from repo root)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install @tanstack/react-router
npm install -D @tanstack/router-plugin
npm install -D tailwindcss @tailwindcss/vite
npm install clsx tailwind-merge class-variance-authority
npx shadcn@latest init          # after Tailwind + aliases are configured
```

```ts
// frontend/vite.config.ts
import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tanstackRouter({ target: "react", autoCodeSplitting: true }), react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } },
  },
});
```

```jsonc
// frontend/tsconfig.app.json
{ "compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["./src/*"] } } }

// frontend/package.json scripts
{ "dev": "vite", "build": "tsc -b && vite build", "check": "tsc --noEmit" }
```

```tsx
// frontend/src/main.tsx  — RouterProvider entry
import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";
import { router } from "./router";
import "./index.css";
declare module "@tanstack/react-router" { interface Register { router: typeof router; } }
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><RouterProvider router={router} /></React.StrictMode>,
);

// frontend/src/router.tsx
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
export const router = createRouter({ routeTree, defaultPreload: "intent" });

// frontend/src/routes/__root.tsx
import { Outlet, createRootRoute } from "@tanstack/react-router";
export const Route = createRootRoute({ component: () => (<main><Outlet /></main>) });
```

**CORS note:** the Vite proxy means ordinary browser traffic never hits FastAPI cross-origin —
CORS is a **dev/direct-access fallback only**, never the normal production path (Phase 6 is
same-origin). Keep `API_CORS_ORIGINS=http://localhost:5173` for direct integration checks.

**Typed search params — GA4 callback pattern (parked from F4 §11; Task 0 validates it):**

```tsx
// frontend/src/routes/auth/ga4/callback.tsx
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

const callbackSearch = z.object({
  status: z.enum(["success", "cancelled", "error"]).optional(),
  reason: z.string().optional(),
});

export const Route = createFileRoute("/auth/ga4/callback")({
  validateSearch: callbackSearch,
  component: Ga4CallbackPage,
});

function Ga4CallbackPage() {
  const { status, reason } = Route.useSearch();
  return status === "success"
    ? <section>Google Analytics connected.</section>
    : <section>{reason ?? "Connection failed."}</section>;
}
```

`validateSearch` is TanStack Router's supported typed search-param entry point; on validation
failure the router renders the route's `errorComponent` (`error.routerCode === "VALIDATE_SEARCH"`).

**Layout target (master-plan §12):**

```text
frontend/
├── package.json               # locked pins from Task 0 (npm; package-lock.json committed)
├── vite.config.ts             # @vitejs/plugin-react + @tanstack/router-plugin/vite
├── tsconfig.json              # from capture (path aliases: @/ → src/)
├── components.json            # shadcn config (captured)
├── index.html
├── .gitignore                 # node_modules/, dist/, *.local
├── src/
│   ├── router.tsx             # TanStack Router config (ported infra)
│   ├── routeTree.gen.ts       # REGENERATED — never hand-edited
│   ├── styles.css             # Tailwind v4 entry (captured, strip Lovable-only blocks)
│   ├── routes/                # __root.tsx, index.tsx (functional); learn.tsx (deferred);
│   │                          #   auth/ga4/callback.tsx (Phase 5, validateSearch spike now)
│   ├── components/
│   │   ├── explorer/          # ported shell components (Task 2)
│   │   └── ui/                # shadcn primitives — regenerate ONLY the subset actually
│   │                          #   imported by ported components (owner decision
│   │                          #   2026-08-06: selective regenerate, not all 46)
│   ├── lib/
│   │   ├── explorer-store.tsx # context provider (Task 4)
│   │   ├── api.ts             # typed client (Task 3)
│   │   ├── api-types.ts       # OpenAPI-derived types (Task 3)
│   │   └── utils.ts           # cn() helper (ported)
│   ├── hooks/use-mobile.tsx   # responsive hook (ported infra)
│   ├── test/
│   │   ├── fixtures/          # mock-ga4.ts, mock-braintree.ts, mock-evidence.ts — TEST-ONLY
│   │   ├── handlers/          # api.ts — MSW network handlers (Task 6)
│   │   ├── server.ts          # setupServer (Task 6)
│   │   └── setup.ts           # vitest setup (Task 6)
│   └── prototype/             # evidence panels — non-production (Task 2 quarantine)
└── README.md                  # run instructions; gitignored dirs
```

**Acceptance:** `npm ci` resolves with the Task 0 pins; `npm run dev` serves the shell;
`npm run build` produces `dist/`; `npm run check` (typecheck + lint) green.

---

## Task 2 — Port components by manifest classification

Copy from the **frozen capture** into `frontend/src/`. The rule: **Port/adapt = shell copied,
data source/commands replaced by FastAPI endpoints — mock imports never survive into runtime.**

### `initial_mount: functional` — mounted and working in the first slice

| File | Port action |
|---|---|
| `routes/__root.tsx`, `routes/index.tsx` | Port as-is (routing), strip any Start-specific wrappers |
| `components/explorer/Sidebar.tsx` | Port; nav + upload/clear entries active; Drive entry defers with the sheet |
| `components/explorer/TopBar.tsx` | Port as-is |
| `components/explorer/EmptyHero.tsx` | Port shell; **replace mock `loadData("GA4 · …")` actions** with real upload (and GA4 Phase 5) flows |
| `components/explorer/UploadZone.tsx` | Port; wire dropzone → `POST /api/v1/upload` (Task 3) |
| `components/explorer/DataPreview.tsx` | Port shell; rows/columns from `GET /api/v1/data/preview` — **never `mock-ga4`** |
| `components/explorer/Scorecard.tsx` | Port; hydrate from `DatasetContext` + quality |
| `lib/explorer-store.tsx` | Port + **rewrite per the drift matrix (Task 4)** |
| `lib/utils.ts`, `hooks/use-mobile.tsx`, `router.tsx`, `styles.css` | Port as infra |

### `initial_mount: placeholder` — mounted as a visual shell only

| File | Port action |
|---|---|
| `components/explorer/ChartCard.tsx` | Shell only |
| `components/explorer/ChartsRow.tsx` | Shell only; chart data from `/api/v1/data/charts` **when that endpoint exists** — no mock chart data in the first slice |

### `initial_mount: deferred` — ported later, in the owning phase

| File | Owning phase / note |
|---|---|
| `components/explorer/Chat.tsx` | **Ported + SSE reader MSW-tested in this phase, but NOT mounted in slice 1** (owner decision 2026-08-06) — mounts in a Phase 4 follow-up PR after the upload→preview→quality→clear slice ships |
| `components/explorer/AiSummary.tsx`, `Markdown.tsx` | Phase 4 (with Chat) |
| `components/explorer/ExportMenu.tsx` | Phase 4/5 — needs export endpoints (deferred from Phase 3 per decision D6) |
| `components/explorer/OnboardingTour.tsx` | Phase 4 polish pass |
| `components/explorer/DriveImportSheet.tsx` | **Phase 5 UI candidate only** — never a first-slice port |
| `components/explorer/EquityPanel.tsx`, `ResearchPanel.tsx` | **Prototype/reference only** — evidence workstream; see quarantine below |
| `routes/learn.tsx` | Phase 4 polish pass |

### Fixture-only + reference + do-not-port

```text
Fixture-only (→ src/test/fixtures/, TEST-ONLY):
  lib/mock-ga4.ts · lib/mock-braintree.ts · lib/mock-evidence.ts
  → MSW fixture material (Task 6). Runtime must never import them.

Reference only:
  lib/measurement-contract.ts — verified-faithful transcription; TS types are generated
    from plans/ga4-measurement-contract.md, never from this file.
  routeTree.gen.ts — regenerate.
  components/ui/* (46 files) — selective shadcn regeneration (below), not manual copy.

Do-not-port (deleted / never copied) — the full removal list (owner guidance 2026-08-06):
  @tanstack/react-start/plugin/vite · tanstackStart(...) vite config · Nitro/server config
  src/routes/api/* (incl. src/routes/api/chat.ts) · server.ts · start.ts
  createServerFileRoute(...) · createServerFn(...) · ai-gateway.server.ts
  server-only secrets/env reads · any server-side Gemini/OpenAI/GA4/Drive call
  Start middleware duplicating FastAPI auth/session ownership
  research/* · insights/* · evidence/* · lovable-error-reporting.ts
```

### shadcn/ui primitives — selective regeneration (owner decision 2026-08-06)

Initialize shadcn for Vite (lock the resulting deps), then add **only the primitives the
first-slice shells actually import** — the capture is a visual/behavioral reference, not a
vendored dependency tree. Do not add all 46, and do not add unused registry components.

```text
First-slice primitives (only):
  button · card · dialog · input · label · tooltip · skeleton · dropdown-menu
  separator · scroll-area · badge · sonner/toast
```

### First-slice scope — mounted vs deferred (owner decision 2026-08-06)

```text
Included (first PR):
  app shell + theme tokens · sidebar/navigation shell · upload form · upload progress/error
  states · GET /data/context hydration · preview + quality display · Clear Data action
  · ChartsRow placeholder/empty state · MSW/API contract tests · a11y smoke coverage

Deferred (owned by later PRs/phases):
  mounted chat UI · summary UI · live charts + chart API · Drive UI · GA4 OAuth UI
  · exports · evidence/prototype panels · client-side analytics calculations
  · filter/metric control UI (no sync endpoints in slice 1 — see note below)
```

**Filter/metric controls are OUT of the first-slice flow (review decision 2026-08-06).**
Phase 3 ships no filter/metric mutation or synchronization endpoints, and filter/metric state
is server-owned (master-plan §8; drift rows 1–4). Slice 1 therefore does **not** render
interactive filter/metric controls — they are omitted (or visibly disabled/deferred) until a
later PR adds the sync endpoints plus their request/version contracts, validation, tests,
stale-state handling, and Clear Data reset behavior. Upload → context → preview → quality →
clear is the complete slice-1 user flow.

### Implementation waves (PR sequencing)

Treat Phase 4 as **two waves**, even though it is one spec:

```text
Wave 4A — functional shell (first PRs):
  Task 0 probes · Vite + TanStack Router scaffold · theme/tokens/layout shell · selective
  shadcn primitives · api.ts + api-types.ts · upload, context hydration, preview, quality,
  Clear Data · ChartsRow deferred/empty state · MSW + Playwright functional slice · CI
  frontend build/typecheck

Wave 4B — AI UI integration (follow-up PRs; Phase 3 already provides the backend):
  SSE reader utility · MSW named-SSE parser tests · chat store wiring · mounted Chat panel
  · Summary/AiSummary UI · reconnect/cancel/error UX · TTFT + stream-completion observability
```

ChartsRow renders an explicit empty state, e.g. **"Charts will appear when the chart-analysis
API is available."** — never derive charts from preview data client-side (that would create an
undocumented second charting/analytics contract).

### Prototype quarantine (master-plan §12 rules — enforced, not aspirational)

1. Production runtime **never imports from `src/test/`** (ESLint boundary rule, Task 8).
2. Production source registry **never registers mock data sources**.
3. `src/prototype/` holds the evidence-connector demo panels (EvidenceConnector /
   InsightCandidates / MeasurementContract) — excluded from production routes or behind a
   clear demo flag.
4. Any preview using mock evidence must visibly show **"Demo / mock data"**.**Acceptance:** every one of the 94 captured files accounted for (ported / selectively re-added / fixture / reference / do-not-port) in the gate table; no `mock-*` import reachable from production code.

---

## Task 3 — API client: `api-types.ts` + `api.ts`

### Types (`api-types.ts`)

Generated/validated from the FastAPI OpenAPI contract — **the store never imports types from
mock fixtures** (drift row 12). First-slice types:

```ts
export type DataSource = "upload" | "ga4" | "drive";

export interface DateRange { start: string | null; end: string | null; }
export interface Column { name: string; type: "date" | "number" | "string" | "boolean" | "unknown"; nullable: boolean; }
export interface DatasetWarning {
  code: "rows_truncated" | "identifiers_removed_for_ai";
  message: string;
  originalRowCount: number | null;
  loadedRowCount: number;
  removedColumns: string[];
}
export interface DatasetContext {
  source: DataSource; filename: string; rowCount: number;
  dateRange: DateRange; columns: Column[]; filters: Record<string, unknown>[];
  metrics: Record<string, unknown>[]; provenance: Record<string, unknown>;
  warnings: DatasetWarning[];
}
export interface QualityReport {
  grade: "A" | "B" | "C" | "D" | "E" | "F"; completenessPct: number; duplicatePct: number;
  duplicateCount: number; outlierCount: number; dateRangeDays: number | null; dateGaps: number;
  columnCount: number; missingColumns: string[]; warnings: string[];
}
export interface UploadResponse { dataset: DatasetContext; }
export interface DataPreviewResponse { dataset: DatasetContext; rows: Record<string, unknown>[]; }
export interface ChatMessage { role: "user" | "assistant"; content: string; timestamp?: string; }
export interface ChatRequest { messages: ChatMessage[]; mode: "chat" | "summary"; }
export interface SummaryResponse { summary: string; model: string; usage: Record<string, number>; }
export interface ForecastPoint { date: string; value: number | null; lower: number | null; upper: number | null; }
export interface ForecastResponse { metricCol: string; periods: number; summary: string; forecastPoints: ForecastPoint[]; insufficientData: boolean; }
export interface FunnelResponse { steps: string[]; values: number[]; }
export interface UsageResponse { requestCount: number; successCount: number; failureCount: number; /* …counts only… */ }
export interface ApiError { detail: string; }
```

### Client (`api.ts`)

```ts
// F4 §10 parked pattern, adapted to the Phase 1–3 contract (owner guidance 2026-08-06).
// Single API-base module; all calls deployment-neutral (dev proxy + Phase 6 same-origin).
export const API_BASE = "/api/v1";

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    credentials: "include", // HttpOnly session cookie — the ONLY client credential (track A)
    ...init,
  });
}

export class ApiRequestError extends Error {
  constructor(readonly status: number, detail: string) { super(detail); }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await apiFetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiRequestError(res.status, (body as ApiError).detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

export const api = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<UploadResponse>("/upload", { method: "POST", body: form });
  },
  context: () => request<DatasetContext>("/data/context"),
  preview: () => request<DataPreviewResponse>("/data/preview"),
  quality: () => request<QualityReport>("/data/quality"),
  clear: () => request<{ status: string }>("/data/clear", { method: "POST" }),
  chatStream: (body: ChatRequest, signal?: AbortSignal) =>
    apiFetch("/chat", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body), signal }),
  summary: () => request<SummaryResponse>("/analysis/summary", { method: "POST", body: JSON.stringify({ mode: "summary" }) }),
  forecast: (metricCol: string, periods = 30) =>
    request<ForecastResponse>("/analysis/forecast", { method: "POST", body: JSON.stringify({ metric_col: metricCol, periods }) }),
  funnel: (metricCol: string, steps: string[]) =>
    request<FunnelResponse>("/analysis/funnel", { method: "POST", body: JSON.stringify({ metric_col: metricCol, steps }) }),
  usage: () => request<UsageResponse>("/ai/usage"),
};

/** Snake_case → camelCase normalized ONCE at the boundary (track B, F4 §11). */
export function setSourceFromApi(payload: UploadResponse | DataPreviewResponse) {
  const d = payload.dataset;
  return {
    source: d.source,
    filename: d.filename,
    rowCount: d.rowCount,
    dateRange: d.dateRange,
    columns: d.columns,
    filters: d.filters,
    metrics: d.metrics,
    provenance: d.provenance,
    warnings: d.warnings,
  };
}
```

Do **not** put `http://localhost:8000` into ordinary components or stores — the proxy is
development-only; components call `apiFetch("/data/context")` style relative paths.

**Error mapping (drift row 2):** `failLoad()` must map **server typed error codes** to messages —
never a hardcoded string. Code → message table (matches the upload taxonomy):

```text
409  No active dataset — prompt the upload flow
410  Dataset session expired — offer re-upload
413  File too large (browser cap 25 MB) — explain the cap
415  Unsupported file type — list .csv/.xlsx/.xls
422  Couldn't read the file / invalid payload — show detail
503  AI unavailable — show the configuration hint (chat/summary only)
```

**Acceptance:** typecheck green; `credentials: "include"` on every call; no raw `fetch` to
`/api/v1` outside `api.ts` (enforced by an ESLint rule, Task 8).

---

## Task 4 — Store wiring: `explorer-store.tsx` per the drift matrix

Port the context provider and apply **every drift-matrix row** — the matrix is the instruction
set; F3's 13 steps are superseded. Rows not listed here are "keep as captured" (theme row 10,
timestamps row 8).

| # | Captured behavior → required change | Implementation |
|---|---|---|
| 1 | `loadData(name?)` fake timeout → real upload | Replace body with `api.upload(file)`; set `source` from `setSourceFromApi(resp)`; **never fall back to `defaultSource`**; `loadState: "loading"` during, `"error"` on `ApiRequestError`, `"ready"` after |
| 2 | `failLoad()` hardcoded message | Map `ApiRequestError.status` → message per Task 3 table; keep the member |
| 3 | `clearData()` doesn't reset filters/metrics or call server | **Extend:** reset `filters`/`metrics` to `[]`, reset `summary`/`chat`, then `await api.clear()` — derived state dies with the dataset (retention policy) |
| 4 | Hardcoded seeds `initialFilters`/`initialMetrics` | **Remove seeds** — start empty; hydrate from `GET /api/v1/data/context` after a dataset loads |
| 5 | `addFilter`/`removeFilter`/`addMetric`/`removeMetric` local-only | **Keep the members (union, F3 §9)** — filter/metric state is **server-owned**: the browser calls explicit sync endpoints before summary/chat; never sends dataset IDs or client-authoritative state |
| 6 | `generateSummary()` no dataset context in payload | Payload stays `{ mode: "summary" }` — server resolves session → dataset → filters/metrics; **no dataset reference in the payload** |
| 7 | `sendMessage()` client command router + hardcoded prompts | **Move command routing server-side** (`utils/commands.py`, `utils/prompt_templates.py`); the store keeps optimistic append + `streamingId`-keyed reconnect/retry; payload is `{ messages, mode }` |
| 8 | `clearChat()` `setChat([])` | Keep; server chat context clears in the same call path as row 3 |
| 9 | `ChatMessage.timestamp` | Keep client display timestamps; prefer server timestamps when present |
| 10 | `streamAi()` → relative `/api/chat`, plain-text reader, no credentials | → `POST /api/v1/chat` via `api.chat()`, `credentials: "include"`, **named-SSE reader (Task 5)**; delete `src/routes/api/chat.ts` |
| 11 | `streamingId` | **Retain** — reconnect rule: keep the user message, render partial output safely, retry without duplicate assistant messages |
| 12 | Types from `./mock-ga4` | Move to `api-types.ts`; store never imports mock fixtures |
| 13 | `ExplorerValue` interface (20 members) | **Union, never replace:** keep all existing members + add `connectGA4`, `handleGA4Callback`, `connectDrive`, `downloadFromDrive`, `fetchQuality`, `fetchCharts`, `fetchForecast`, `fetchFunnel`, `exportData`, `setSourceFromApi` |

**The union `ExplorerValue` (drift row 13 — first-slice members marked ✓):**

```ts
interface ExplorerValue {
  // state
  loadState: LoadState;           // ✓
  source: DataSource | null;      // ✓
  error: string | null;           // ✓
  filters: Filter[];              // ✓ server-synced
  metrics: Metric[];              // ✓ server-synced
  summary: string;                // ✓
  summaryState: SummaryState;     // ✓
  chat: ChatMessage[];            // ✓ optimistic + server-reconciled
  chatState: "idle" | "streaming" | "ready" | "error";  // ✓
  streamingId: string | null;     // ✓
  theme: "dark" | "light";        // ✓ (localStorage "ie-theme")
  quality: QualityReport | null;  // ✓
  charts: unknown[];              // placeholder data only
  usage: UsageResponse | null;    // Phase 3 endpoint
  // actions
  loadData(file: File): Promise<void>;                     // ✓
  failLoad(message: string): void;                         // ✓
  clearData(): Promise<void>;                              // ✓
  addFilter(f: Omit<Filter, "id">): void;                  // ✓ sync on next request
  removeFilter(id: string): void;                          // ✓
  addMetric(m: Omit<Metric, "id">): void;                  // ✓
  removeMetric(id: string): void;                          // ✓
  generateSummary(): Promise<void>;                        // ✓
  sendMessage(text: string): Promise<void>;                // ✓ (Task 5)
  clearChat(): void;                                       // ✓
  setSourceFromApi(payload: UploadResponse | DataPreviewResponse): void;  // ✓
  connectGA4(): Promise<void>;       // Phase 5
  handleGA4Callback(params: unknown): Promise<void>;       // Phase 5
  connectDrive(): Promise<void>;     // Phase 5
  downloadFromDrive(id: string): Promise<void>;            // Phase 5
  fetchQuality(): Promise<void>;                           // ✓ (first slice quality)
  fetchCharts(): Promise<void>;      // placeholder
  fetchForecast(metricCol: string, periods?: number): Promise<void>;  // ✓
  fetchFunnel(metricCol: string, steps: string[]): Promise<void>;     // ✓
  exportData(): Promise<void>;       // deferred (export endpoints)
  refreshUsage(): Promise<void>;     // Phase 3 endpoint
}
```

**Acceptance:** MSW tests assert each row's behavior (Task 6); no `defaultSource`, no
hardcoded seeds, no client command router, no dataset id in any payload.

---

## Task 5 — Chat: named-SSE reader (plain SSE, Phase 3 wire format)

Phase 3 decision D3 + C5 lock the wire format: **named SSE events with JSON payloads** —
`event: text / usage / done / error` (+ optional `event: warning`), never raw text + `[DONE]`.
The captured store's plain-text `getReader()` accumulation (drift row 10) must be replaced.

> **Backend status (accuracy correction, 2026-08-06):** Phase 3 IS implemented and closed
> (`bb6f564`, 859 tests) — `POST /api/v1/chat` exists and its SSE contract is covered by
> `tests/api/test_chat.py` (text→done, error→done, ai_busy, warning events). The decision to
> **defer the mounted chat panel** is therefore scope discipline (smallest honest vertical
> slice), NOT backend unavailability. The wire fields below are snake_case to match the
> backend's `TypedAiError.public_payload()` and usage payloads exactly.

### Reader

```ts
// Wire shape — matches the FastAPI backend byte-for-byte (snake_case).
export type ChatStreamEvent =
  | { type: "text"; content: string }
  | { type: "usage"; input_tokens?: number; output_tokens?: number }
  | { type: "warning"; code: string; message: string; removed_columns?: string[] }
  | { type: "error"; code: string; retryable: boolean; message: string; retry_after_seconds?: number }
  | { type: "done" };

/** Parse the Phase 3 named-SSE wire format. Throws on a malformed frame. */
function parseSseFrame(frame: string): { event: string; data: unknown } {
  const lines = frame.split("\n");
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event: ")) event = line.slice(7);
    else if (line.startsWith("data: ")) dataLines.push(line.slice(6));
  }
  if (!dataLines.length) throw new Error("Malformed SSE frame: no data line");
  return { event, data: JSON.parse(dataLines.join("\n")) };
}

export async function readChatStream(
  res: Response,
  onEvent: (e: ChatStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  if (!res.ok || !res.body) throw new ApiRequestError(res.status, "AI request failed");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let terminal = false;
  for (;;) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const { event, data } = parseSseFrame(frame);
      const e = data as ChatStreamEvent;
      if (event === "text") onEvent({ type: "text", content: e.content });
      else if (event === "usage") onEvent({ type: "usage", ...(e as object) });
      else if (event === "warning") onEvent({ type: "warning", ...(e as object) });
      else if (event === "error") onEvent({ type: "error", ...(e as object) });
      else if (event === "done") { onEvent({ type: "done" }); terminal = true; }
    }
  }
  if (!terminal) onEvent({ type: "error", code: "connection_closed", retryable: true, message: "Stream ended without a terminal event." });
}
```

The store calls `api.chatStream(body, signal)` and passes the `Response` to
`readChatStream(res, onEvent, signal)` — `AbortSignal` powers the client-disconnect /
retry-cancel path in the `streamingId` rule below.

### Client rules (C5 terminal behavior — enforced in the UI)

```text
Success: text* → done          — append text deltas; stop on `done`.
Failure before text: error → done — render the typed error; no partial content.
Failure after text: text+ → error → done — keep partial output; show the error; mark the
  reply non-actionable (no retry/duplicate append of the same assistant turn).
`error` is terminal for assistant content; `done` closes the transport.
```

### `streamingId` reconnect rule (drift row 11)

1. On send: assign `streamingId`, append the user message optimistically.
2. On disconnect/cancel: **retain the user message**, keep partial assistant output rendered
   as "interrupted", and allow a manual retry.
3. Retry sends the **same** `{ messages, mode }` history; the server treats it as a fresh
   request — the client must not append a duplicate assistant message (drop the partial turn
   before retry or replace it, never both).
4. No auto-retry after any text has streamed (matches the Phase 3 provider-retry policy).

**Acceptance:** MSW streaming test drives `text → done` and `text → error → done` frames and
asserts the client terminal behavior (Task 6); no `[DONE]` handling anywhere.

---

## Task 6 — MSW component tests

Follow the parked F4 §12 pattern. Dependencies: `vitest`, `msw@^2.15.0`, `@testing-library/react`,
`@testing-library/user-event`, `jsdom` (or happy-dom).

### Setup

```ts
// src/test/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers/api";
export const server = setupServer(...handlers);

// src/test/setup.ts
import { server } from "./server";
beforeAll(() => server.listen({ onUnhandledRequest: "error" })); // live-verified: msw@2.15.0 default is "warn"
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Handlers (`src/test/handlers/api.ts`) — real endpoint shapes

```text
POST /api/v1/upload        → 201 UploadResponse  | 413/415/422 typed errors
GET  /api/v1/data/context  → 200 DatasetContext  | 409
GET  /api/v1/data/preview  → 200 DataPreviewResponse | 409
GET  /api/v1/data/quality  → 200 QualityReport   | 409
POST /api/v1/data/clear    → 200 { status: "cleared" }
POST /api/v1/chat          → text/event-stream; body = ReadableStream of named-SSE frames
                             (jsdom has no EventSource — test the getReader() path)
POST /api/v1/analysis/forecast · funnel · summary → typed responses
GET  /api/v1/ai/usage      → 200 UsageResponse
```

### Required component tests

| Test | Asserts (drift row) |
|---|---|
| Upload happy path: `loadData(file)` → `source`/`rowCount` set | row 1 |
| Upload failure maps server code → message (413/415/422/409) | row 2 |
| Clear Data resets filters/metrics/summary/chat and calls `/data/clear` | row 3 |
| No seeds: fresh store has empty `filters`/`metrics` until context hydrates | row 4 |
| Filter/metric add/remove are optimistic + synced before summary/chat | row 5 |
| Summary request payload is `{ mode: "summary" }` — no dataset reference | row 6 |
| Chat send: `{ messages, mode }`, no command routing client-side, `streamingId` set | rows 7, 11 |
| Chat stream: `text → done` appends; `text → error → done` keeps partial + shows error; no duplicate assistant append on retry | C5, row 11 |
| Clear chat empties local history (server clears in the same call) | row 8 |
| Production tree imports nothing from `src/test/` | quarantine rule 1 |
| Store imports types from `api-types`, never `mock-ga4` | row 12 |

**Acceptance:** `npm run test` green under CI with `onUnhandledRequest: "error"` (any un-mocked
call fails the suite — keeps handlers honest).

---

## Task 7 — Accessibility + performance baselines (master-plan §17)

Applied to the first-slice shell (Sidebar, TopBar, UploadZone, EmptyHero, DataPreview,
Scorecard) and carried into every deferred component:

```text
Keyboard-operable: upload zone, Clear Data, all dialog/sheet controls reachable and operable
  via Tab/Enter/Space (filter/metric and chat controls join when their PRs land — Waves 4A/4B).
Focus management: dialogs/sheets trap focus; focus returns to the trigger on close.
Non-color-only states: loading / empty / error / success / permission each carry
  icon+text (never color alone).
Screen-reader labels on every icon-only button (aria-label).
Responsive: mobile / tablet / desktop — sidebar collapses via use-mobile; tables scroll.
Perf budget: initial bundle < 500 KB gzipped · interactive dashboard < 2 s ·
  preview < 1 s · first streamed AI token < 2 s (measured in the gate).
```

---

## Task 8 — CI gate + lint boundaries

Add to `.github/workflows/test.yml` (after the Python jobs):

```yaml
  frontend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - run: npm ci
      - run: npm run check     # typecheck + lint (eslint + tsc --noEmit)
      - run: npm run build
      - run: npm run test      # vitest run (MSW)
```

ESLint boundary rules (enforced in CI):

```text
no-restricted-imports: forbid `src/test/*`, `src/prototype/*`, `mock-ga4`, `mock-braintree`,
  `mock-evidence` from any production path (components/, routes/, lib/, hooks/, router.tsx).
no-restricted-syntax or a dedicated rule: forbid raw `fetch(` outside `src/lib/api.ts`.
```

**Acceptance:** the frontend job is required (not allow-failure) in `test.yml`; green on PR.

---

## Task 9 — Playwright user-flow gate

Extend the existing Playwright suite with the first-slice frontend flow (real FastAPI + React
together; MSW is for component tests, not this gate):

```text
1. Serve via the **Vite proxy** (Task 1): `uvicorn api.main:app --port 8000`  +  `npm run dev` (frontend at 5173, `/api` proxied to 8000).
2. Flow: load / → upload sample.csv → preview renders rows → quality renders grade →
        (filter/metric controls NOT in slice 1 — review decision; chat panel not mounted,
        reader covered by MSW tests) → Clear Data → empty state returns, /ai/usage resets.
3. Assert: no console errors; no 409/410 unless expected; a11y smoke (tab through controls);
        bundle size and TTFT within the Task 7 budgets.
```

All API calls in this gate run through the Vite proxy with cookie-aware
`fetch(..., { credentials: "include" })` — the session cookie set by FastAPI must round-trip
through the proxied browser origin (`localhost:5173`) exactly as it will in production
same-origin serving.

**Acceptance:** the gate passes locally and in CI (headless Chromium); recorded in the gate table.

---

## Exit criteria

- [ ] `npm ci && npm run check && npm run build && npm run test` green in CI (frontend gate);
      installs use `npm ci` against the committed `package-lock.json`.
- [ ] Upload → preview → quality → clear works in React against FastAPI (MSW + real).
- [ ] Chat + summary stream over the named-SSE wire with correct terminal behavior; no
      `[DONE]`; `streamingId` reconnect rule implemented (Wave 4B).
- [ ] Every one of the 94 captured manifest rows accounted for; no production import of
      mock/prototype modules; prototype quarantine rules hold.
- [ ] No dataset id / provider token / session secret in any payload; `credentials: "include"`
      everywhere. Frontend no-secrets guard: no `GEMINI_*`, Google OAuth secret, Drive
      credential, session key, or backend-only config in `frontend/.env`, Vite variables,
      source maps, fixtures, or browser storage.
- [ ] `routeTree.gen.ts` generated by the router plugin (local/CI) and checked for drift —
      never hand-edited or copied from the capture; generated shadcn components committed as
      project source, not regenerated in CI.
- [ ] Filter/metric controls omitted (or visibly disabled/deferred) in slice 1 — no
      client-authoritative state; sync endpoints land with their own contracts in a later PR.
- [ ] First React PR verifies mobile/desktop shell behavior + keyboard operation before visual
      polish expands (review acceptance item).
- [ ] A11y + performance baselines measured and recorded (Task 7).
- [ ] Playwright user-flow gate green.

## Gate table — Phase 4 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 4 — React port | Frontend gate green · MSW tests green · store wired to real API per drift matrix · a11y/perf checks recorded | Implementation agent + reviewer | Record evidence (commit SHA + test counts + Task 0 resolved pins); flip `specs/README.md` to DONE; expand `phase-5-ga4-drive.md` to ACTIVE after its GA4/Drive research gates |

---

## Parked/absorbed content (from F3/F4 — superseded or deferred)

- **F3's 13-step store wiring** → `STORE-DRIFT-MATRIX.md` supersedes it in depth; the matrix
  is the instruction set (Task 4).
- **F4 §10** `api-types.ts` + `api.ts` → absorbed as Task 3; `API_BASE = "/api/v1"` relative
  everywhere (dev Vite proxy + Phase 6 same-origin — no `VITE_API_BASE`).
- **F4 §11** React GA4 callback route (`/auth/ga4/callback`) — typed `validateSearch` for
  `status`/`reason` (pattern + code in Task 1; canonical status values `success|cancelled|error`
  per master-plan §9); store `setSourceFromApi`. **Lands Phase 5** (with the OAuth endpoints);
  Task 0 runs the router-validation spike now.
- **F4 §12** MSW test dependencies + patterns → absorbed as Task 6.
- **Export endpoints + React download flow** → deferred to Phase 4/5 (Phase 3 decision D6):
  exports are deterministic but their value is tied to the React download experience, so they
  ship with the frontend that consumes them.
