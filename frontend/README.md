# Insights Explorer — frontend

Vite + React 19 + TanStack Router + Tailwind v4 SPA, served through the FastAPI API in Phase 6.
Phase 4 Wave 4A (functional shell) + Wave 4B (AI UI) implementation.

## Stack (locked pins — see `package.json` + `package-lock.json`)

React 19 · Vite 8 · TanStack Router 1.x (generated `routeTree.gen.ts`, never hand-edited) ·
Tailwind v4 · TypeScript 5.8 · vitest + MSW for component tests. No TanStack Start/Nitro.

## Development

```bash
# Terminal 1 — FastAPI (repository root)
uvicorn api.main:app --reload --port 8000

# Terminal 2 — this directory
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` → http://127.0.0.1:8000, so the browser sees
one origin (`credentials: "include"` carries the HttpOnly session cookie).

## Commands

```bash
npm run dev        # Vite dev server (port 5173)
npm run check      # tsc --noEmit + eslint (boundary rules: no src/test|prototype|mock-* in prod, no raw fetch outside lib/api.ts)
npm run build      # tsr generate → tsc -b → vite build (dist/)
npm run test       # vitest run (MSW component tests)
```

## Layout

```text
src/
  routes/            __root.tsx · index.tsx · auth/ga4/callback.tsx (Phase 5 validateSearch spike)
  components/
    explorer/        AppShell, Sidebar, TopBar, UploadZone, EmptyHero, DataPreview,
                     Scorecard, ChartsRow (honest empty state), ChatPanel, AiSummary, Markdown
    ui/              selective shadcn primitives (committed as source)
  lib/
    api.ts           typed client — the ONLY module that calls fetch (credentials: "include")
    api-types.ts     OpenAPI-derived types (snake_case → camelCase normalized at the boundary)
    chat-stream.ts   named-SSE reader (Phase 3 wire format, byte-for-byte)
    explorer-store.tsx  drift-matrix store (server-owned state; browser holds view state only)
  test/              TEST-ONLY fixtures/handlers/server/setup (never imported from production)
  hooks/use-mobile.ts
```

## First-slice scope

Mounted: app shell, theme, upload → context → preview → quality → Clear Data, ChartsRow
placeholder, AI chat + summary (Wave 4B). Deferred: filter/metric controls (no sync endpoints
yet), Drive/GA4 UI, exports, evidence panels, live charts.
