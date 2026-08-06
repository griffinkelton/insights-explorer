# Freebuff Prompt: Wire explorer-store.tsx to FastAPI Endpoints

## Canonical API Decisions (2026-08-05 — master-plan revision)

Single source of truth for implementation-facing documents. Anything below that conflicts with earlier text in this document is **superseded** (old paths are marked, not left active):

| Decision | Value |
|---|---|
| API prefix | `/api/v1` (all routes versioned) |
| Health endpoint | `GET /healthz` |
| Upload response | `{ dataset: ... }` (with `{ dataset, rows }` where specified) |
| Auth/session transport | HttpOnly secure session cookie + `credentials: "include"` |
| API naming | snake_case at the boundary |
| React mapping | `api.ts` performs snake_case → camelCase normalization — never individual components |
| Chat transport | [explicit chosen format — default: plain SSE `text/event-stream`, `data: <chunk>\n\n`] |
| Upload policy | Browser cap **25 MB** (`MAX_BROWSER_UPLOAD_BYTES` — margin below Cloud Run's 32 MiB HTTP/1 boundary); server-side/Drive **100 MB** (`MAX_INGEST_BYTES`, subject to memory/MIME/row-count/decompression safeguards) |

Superseded here: all bare `/api/...` paths (now `/api/v1/...`) and any earlier 32 MB upload default. See `master-plan.md` §4–5 and archive §4.12–4.13.

**F3-specific supersession:** step 2's `API_BASE` default `http://localhost:8000/api` → `http://localhost:8000/api/v1`; step 13's `VITE_API_BASE=/api` → `/api/v1` (same-origin relative).

## Context for Freebuff

This prompt is for use in Freebuff (or any agentic coding assistant with repo access). It assumes:
- You are working in `insights-explorer` repo
- Phase 1 of the migration plan is complete (FastAPI skeleton exists in `api/`)
- The FastAPI app is running on `http://localhost:8000`
- The React frontend (from `insights-whisperer-30`) is in `frontend/` and runs on `http://localhost:5173`
- You have not yet replaced the mock data layer

---

## The Prompt

```
I need you to wire the React store (frontend/src/lib/explorer-store.tsx) to the FastAPI backend (api/) that we just built. The store currently imports mock data from ./mock-ga4 and ./mock-braintree. I want to replace every mock call with a real fetch() to the corresponding FastAPI endpoint while preserving the existing context provider structure, state types, and component API.

## Current State of explorer-store.tsx

The file exports:
- Types: LoadState ("idle" | "loading" | "error" | "ready"), SummaryState ("idle" | "streaming" | "ready" | "error"), Filter, Metric
- Interface: ExplorerValue with fields: loadState, source, error, filters, metrics, summary, summaryState, chat, streamingId, loadData, failLoad, clearData
- A streamAi() helper that calls `/api/v1/chat` with POST and reads the SSE stream
- A React context provider (ExplorerProvider) that holds all state
- A useExplorer() hook for consuming components

It currently imports from ./mock-ga4:
- defaultSource (a DataSource object with fake GA4 data)
- type ChatMessage
- type DataSource

And the chat API route (src/routes/api/chat.ts) imports buildDataContext from ./mock-braintree to construct the system prompt context.

## What to Change

### 1. Remove mock imports

Delete these imports from explorer-store.tsx:
- import { defaultSource, type ChatMessage, type DataSource } from "./mock-ga4"
- Any import from ./mock-braintree

Keep the type definitions (ChatMessage, DataSource, Filter, Metric) but move them into explorer-store.tsx itself or into a new types.ts file in the same directory. Do not depend on mock files for types.

### 2. Define API base URL

Add a constant at the top of the file:

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

This lets us override the API base in production via env var.

### 3. Replace loadData() with real upload + fetch

Currently loadData() simulates loading mock data with a setTimeout. Replace it with:

async function loadData(file?: File, source?: "upload" | "ga4" | "drive"): Promise<void> {
  setLoadState("loading");
  setError(null);
  try {
    let dataContext: DataContext;
    if (file) {
      // Upload flow
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(await res.text().catch(() => "Upload failed"));
      dataContext = await res.json();
    } else if (source === "ga4") {
      // GA4 flow — triggers OAuth redirect handled separately
      throw new Error("GA4 connection requires OAuth flow. Use connectGA4() instead.");
    } else {
      // Default: try to fetch existing session data
      const res = await fetch(`${API_BASE}/data/preview`);
      if (!res.ok) throw new Error("No data loaded");
      dataContext = await res.json();
    }
    setSource(dataContext);
    setLoadState("ready");
  } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to load data");
    setLoadState("error");
  }
}

### 4. Add GA4 OAuth flow

Add these functions to the store:

async function connectGA4(): Promise<void> {
  const res = await fetch(`${API_BASE}/ga4/connect`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start GA4 connection");
  const { authUrl } = await res.json();
  window.location.href = authUrl; // Redirect to Google OAuth
}

async function handleGA4Callback(): Promise<boolean> {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  if (!code) return false;
  // The FastAPI callback endpoint handles the token exchange and redirects back
  // This function is called on the callback route to check if we returned with data
  const res = await fetch(`${API_BASE}/data/preview`);
  if (res.ok) {
    const dataContext = await res.json();
    setSource(dataContext);
    setLoadState("ready");
    return true;
  }
  return false;
}

### 5. Add Drive Picker integration

async function connectDrive(): Promise<void> {
  // Request a Picker token from FastAPI
  const res = await fetch(`${API_BASE}/drive/picker-token`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to get Drive token");
  const { token } = await res.json();
  // Load Google Picker API and show picker
  // The actual picker rendering can stay in a separate component
  // This function just gets the token; the component handles the UI
  return token;
}

async function downloadFromDrive(fileId: string): Promise<void> {
  setLoadState("loading");
  try {
    const res = await fetch(`${API_BASE}/drive/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fileId }),
    });
    if (!res.ok) throw new Error(await res.text().catch(() => "Drive download failed"));
    const dataContext = await res.json();
    setSource(dataContext);
    setLoadState("ready");
  } catch (err) {
    setError(err instanceof Error ? err.message : "Drive download failed");
    setLoadState("error");
  }
}

### 6. Replace the streamAi() helper

The existing streamAi() already calls `/api/chat` in the prototype. Update it to point to FastAPI (`/api/v1/chat`) instead of the Lovable/TanStack server route:

async function streamAi(
  body: { messages?: Message[]; mode?: "chat" | "summary" },
  onDelta: (full: string) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) throw new Error(await res.text().catch(() => "AI request failed"));
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let acc = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    acc += decoder.decode(value, { stream: true });
    onDelta(acc);
  }
}

Note: The FastAPI `/api/v1/chat` endpoint must return a Server-Sent Events (SSE) stream. The streamText response format from the Vercel AI SDK uses plain text streaming, so FastAPI should return StreamingResponse with media_type="text/event-stream" or "text/plain" depending on the format. Check the FastAPI implementation and adjust the reader accordingly.

### 7. Add data quality, charts, forecast, funnel fetchers

Add these helper functions that components can call:

async function fetchQuality(): Promise<QualityResult> {
  const res = await fetch(`${API_BASE}/data/quality`);
  if (!res.ok) throw new Error("Failed to fetch quality");
  return res.json();
}

async function fetchCharts(): Promise<ChartsResult> {
  const res = await fetch(`${API_BASE}/data/charts`);
  if (!res.ok) throw new Error("Failed to fetch charts");
  return res.json();
}

async function fetchForecast(): Promise<ForecastResult> {
  const res = await fetch(`${API_BASE}/analysis/forecast`);
  if (!res.ok) throw new Error("Failed to fetch forecast");
  return res.json();
}

async function fetchFunnel(): Promise<FunnelResult> {
  const res = await fetch(`${API_BASE}/analysis/funnel`);
  if (!res.ok) throw new Error("Failed to fetch funnel");
  return res.json();
}

async function generateSummary(): Promise<void> {
  setSummaryState("streaming");
  try {
    await streamAi({ mode: "summary" }, (full) => setSummary(full));
    setSummaryState("ready");
  } catch (err) {
    setSummaryState("error");
  }
}

### 8. Add export function

async function exportData(format: "markdown" | "excel" | "pdf"): Promise<void> {
  const res = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format }),
  });
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `insights-export.${format === "markdown" ? "md" : format === "excel" ? "xlsx" : "pdf"}`;
  a.click();
  URL.revokeObjectURL(url);
}

### 9. Update the ExplorerValue interface

Add the new functions to the interface so consuming components can access them:

interface ExplorerValue {
  // Existing
  loadState: LoadState;
  source: DataSource | null;
  error: string | null;
  filters: Filter[];
  metrics: Metric[];
  summary: string;
  summaryState: SummaryState;
  chat: ChatMessage[];
  streamingId: string | null;
  loadData: (file?: File, source?: "upload" | "ga4" | "drive") => Promise<void>;
  failLoad: () => void;
  clearData: () => void;

  // New
  connectGA4: () => Promise<void>;
  handleGA4Callback: () => Promise<boolean>;
  connectDrive: () => Promise<string>;
  downloadFromDrive: (fileId: string) => Promise<void>;
  generateSummary: () => Promise<void>;
  fetchQuality: () => Promise<QualityResult>;
  fetchCharts: () => Promise<ChartsResult>;
  fetchForecast: () => Promise<ForecastResult>;
  fetchFunnel: () => Promise<FunnelResult>;
  exportData: (format: "markdown" | "excel" | "pdf") => Promise<void>;
}

### 10. Update the chat route (src/routes/api/chat.ts)

The existing chat route in the TanStack server proxies to Lovable's AI gateway. Since we are now using FastAPI for chat, either:

Option A (recommended): Delete src/routes/api/chat.ts entirely and let explorer-store.tsx call FastAPI directly (the streamAi function above already does this).

Option B: Keep it as a thin proxy if you need same-origin requests:
  POST /api/chat → proxy to http://localhost:8000/api/v1/chat

If you keep the proxy, update it to forward to FastAPI instead of the Lovable gateway.

### 11. Clean up mock files

After the store is fully wired:
- Delete frontend/src/lib/mock-ga4.ts
- Delete frontend/src/lib/mock-braintree.ts
- Delete frontend/src/lib/ai-gateway.server.ts (Lovable AI gateway no longer needed)
- Update any component that directly imports from mock files to use the store instead

### 12. Add TypeScript types for API responses

Create frontend/src/lib/api-types.ts with:

interface DataContext {
  source: "upload" | "ga4" | "drive";
  filename: string;
  rowCount: number;
  dateRange: { start: string; end: string };
  columns: Column[];
  filters: Filter[];
  metrics: Metric[];
  provenance: {
    uploadedAt: string;
    lastModified: string;
    transformations: string[];
  };
}

interface Column {
  name: string;
  type: "date" | "number" | "string";
  nullable: boolean;
}

interface QualityResult {
  score: number;
  warnings: string[];
  rowCount: number;
  dateRange: { start: string; end: string };
}

interface ChartsResult {
  sessionsUsers: { x: string[]; y: number[] };
  topPages: { labels: string[]; values: number[] };
}

interface ForecastResult {
  forecast: { dates: string[]; values: number[]; confidence: number[][] };
}

interface FunnelResult {
  steps: { name: string; count: number; dropoff: number }[];
}

### 13. Add .env file for the frontend

Create frontend/.env:

VITE_API_BASE=http://localhost:8000/api

And frontend/.env.production:

VITE_API_BASE=/api

(The production one uses a relative path assuming FastAPI and React are served from the same origin.)

## Rules

- Do not change the component API (what components import from the store) unless absolutely necessary. Components should not know whether data comes from mocks or the API.
- Keep all state in the context provider. Do not introduce a separate state management library (Redux, Zustand) unless I ask.
- Handle every error with a user-visible message in the error state. Never silently fail.
- Add loading states for every async operation. No function should leave the UI hanging.
- Do not hardcode URLs. Use the API_BASE constant.
- Keep the SSE streaming implementation for chat. Do not switch to polling.
- Run the existing tests after changes and fix any that break.
- Do not touch the Python backend (api/) in this task. That is a separate phase.

## Verification

After making changes:
1. Run `cd frontend && bun install && bun run dev`
2. Start FastAPI: `cd api && uvicorn main:app --reload --port 8000`
3. Open http://localhost:5173
4. Upload a CSV file — it should appear in the data preview
5. Click "Generate Summary" — it should stream from Gemini via FastAPI
6. Open browser DevTools Network tab and confirm all requests go to localhost:8000/api, not to mock files or Lovable gateway
7. Run `bun run build` and confirm no TypeScript errors
```

---

## How to Use This Prompt

1. Open Freebuff (or your agentic coding tool) in the `insights-explorer` repo
2. Paste the entire prompt above
3. Freebuff should read `explorer-store.tsx`, make the changes, and verify the build

## What This Prompt Does NOT Cover

- **FastAPI implementation** — this assumes the endpoints already exist from Phase 1
- **OAuth callback route in React** — you'll need a `/auth/ga4/callback` route component that calls `handleGA4Callback()`
- **Drive Picker UI component** — the token fetch is wired, but the Google Picker rendering stays in a separate component
- **Test rewriting** — existing React tests that mock `mock-ga4` will break and need updating

If you want, I can also write the **FastAPI endpoint implementations** (Phase 1 code) or the **OAuth callback route component** for React.
---

## Research Addendum (2026-08-05)

Verification of the SSE assumption in section 6 above (full detail: `insights-explorer-migration-ingest.md` §3.5):

- **`toTextStreamResponse()`** (Vercel AI SDK) returns `text/plain` plain-text chunks — so the plain-text `getReader()` + `TextDecoder` accumulation in `streamAi()` is **correct** for that format.
- **Caveat:** if the chat UI uses the SDK's `useChat` hook, it expects the SDK's structured data-stream format (from `toDataStreamResponse()` / `toUIMessageStreamResponse()`), not plain text/SSE. Pick **one** wire format for FastAPI and make the reader match — don't mix.
- If FastAPI emits SSE, use `text/event-stream` with `data: <chunk>\n\n` framing; the reader must strip `data: ` prefixes and blank-line delimiters.

Also: the OAuth flow sketched in section 4 is superseded by the Phase 1 packet's correction — Google redirects to **FastAPI**, not React; React only ever sees `status`/`reason` on the callback page (see `insights-explorer-migration-ingest.md` §1.11 and §3.2).
---

## Reconciliation Addendum (2026-08-05)

The prompt's snippets predate the Phase 1 implementation packet's contract. Apply these adjustments when executing the prompt (full ledger: `insights-explorer-migration-ingest.md` Part 4). The original prompt above is preserved unchanged.

1. **Upload response is wrapped.** `POST /api/v1/upload` returns `{ dataset: DataContext }` — read `const { dataset } = await res.json(); setSource(dataset);` (not the bare object).
2. **Preview response is wrapped.** `GET /api/v1/data/preview` returns `{ dataset, rows }` — the `loadData()` fallback branch must use `preview.dataset`.
3. **OAuth URL field is snake_case.** `POST /api/v1/ga4/connect` returns `{ authorization_url }`, not `authUrl`.
4. **Send cookies.** Add `credentials: "include"` to **every** fetch in the store (and `api.ts`) — F4 requires it or the session cookie is never sent.
5. **Casing rule.** The API is snake_case (`row_count`, `date_range`, `authorization_url`). Keep F4's `api-types.ts` snake_case types as the wire types; normalize to the store's camelCase shape **once**, in the required `setSourceFromApi` setter — do not scatter conversions across components.
6. **`ExplorerValue` must add `setSourceFromApi`** (the non-UI setter F4 §11 requires); it was missing from the interface update in section 9.
7. **OAuth flow superseded.** Section 4's `handleGA4Callback()` reading `?code=` is superseded by F4's design: Google redirects to FastAPI; React only receives `status=success` / a safe `reason` on `/auth/ga4/callback`. Delete the `?code=` logic when implementing the callback route.
8. **Column type union.** Adopt F4's superset (`"date" | "number" | "string" | "boolean" | "unknown"`).
---

## Batch 3 Addendum (2026-08-05)

> Source: PASTE 11 of the ingest archive (§1.13 synthesis, §2.15 verbatim, §4.6 verification). Refines this prompt's assumptions; apply before or while editing `explorer-store.tsx`.

1. **Server-owned session, not client state.** The store must treat its state as view-model only: the browser holds only the opaque `HttpOnly` session cookie, so `credentials: "include"` (already in the prompt) stays required. Never persist raw uploaded data, Drive file contents, GA4 tokens, or provider credentials in localStorage, React state persistence, URLs, or logs. If the store currently persists anything beyond a lightweight view cache, strip it.
2. **Mock files become test fixtures, not product imports.** The prompt already removes the mock imports — also add the MSW handler layer so `mock-ga4.ts` / `mock-braintree.ts` live only behind the test boundary. This prevents a half-migrated production UI from rendering stale fake data.
3. **API versioning + typed client.** Point `API_BASE` at `/api/v1` (e.g. `http://localhost:8000/api/v1`). Prefer generating/validating the store's fetch types from the backend's OpenAPI/JSON Schema over hand-writing `api-types.ts`; if hand-written for now, keep them in a single file and mark them for later generation.
4. **Naming normalization in ONE place.** API boundary emits snake_case; `setSourceFromApi` (already added by the Reconciliation Addendum) is the single camelCase translation point. No component-level field translation.
5. **Session-cookie note for GA4 OAuth.** The callback already redirects through FastAPI (per the implementation packet). The store should only read the safe `status` / `reason` params — never tokens — and rely on the session cookie for all authenticated requests.
---

## Research Fold-In Cross-Check Addendum (2026-08-05)

Cross-checks the 7 research corrections from the plan's Research Fold-In Log against **this prompt's 13 steps** (source: `insights-explorer-migration-ingest.md` Part 3 §3.8). Additive — the prompt above is unchanged; apply these adjustments when executing it.

1. **Picker token returns token **and** project number (correction 2).** Step 5's `connectDrive()` reads `const { token } = await res.json()`. Update it to also read the project number and hand it to the Picker component: `const { token, appId } = await res.json()` → component calls `setAppId(appId)` (Phase 5's `POST /api/v1/drive/picker-token` will return both — plan Phase 5 amendment 2).
2. **Wire format confirmed (correction 3).** Already covered by this prompt's Research Addendum: the plain-text `getReader()`/`TextDecoder` accumulation in step 6 is correct only for plain text/`toTextStreamResponse()` or plain SSE with `data: `-stripping. Re-confirm the Phase 1 decision recorded in the OpenAPI contract and keep the reader matching — do not mix formats.
3. **Callback route uses typed search params (correction 6).** Step 4's `handleGA4Callback()` reading `?code=` is already superseded (Reconciliation Addendum item 7). When the `/auth/ga4/callback` **route component** is implemented (not the store), read `status`/`reason` via TanStack Router `validateSearch`/`useSearch` — never `new URLSearchParams(window.location.search)` (F4 §11 cross-check item 2; plan Phase 5 amendment 4).
4. **Funnel availability is partial (correction 4).** Step 7's `fetchFunnel()` — at Phase 3/6 implementation, scope the funnel to **template funnels** (`runFunnelReport`); user/identifier-level funnel analysis remains blocked by aggregate-only GA4 access. Re-verify the ROADMAP funnel rows at that time.
5. **Single-origin assumption is consistent (correction 5).** Step 13's `.env.production` `VITE_API_BASE=/api` already assumes same-origin serving — matches the multi-stage Dockerfile pattern in `migration/dockerfile-pattern.md` (Phase 6). No change needed; cite the pattern doc when implementing.
6. **No store-side change for corrections 1 (PKCE) and 7 (GA4 throttling).** Both are FastAPI-side concerns (see the F4 cross-check addendum items 1 and 6); the store merely consumes the endpoints as written.
---

## Round 2 Research Addendum (2026-08-05)

> Source: archive §3.9 (live-verified round-2 research). Applies on top of the Research Fold-In Cross-Check Addendum.

1. **AI SDK version pin.** The captured `package.json` pins `"ai": "^7.0.48"` — not v4 as one research agent claimed. If the chat UI keeps the SDK's `useChat` hook, it parses the SDK v7 structured data-stream / UI-message protocol; the store's plain-text `getReader()`/`TextDecoder` reader in step 6 is correct **only** for the plain-text path (`toTextStreamResponse()`). Re-confirm the Phase 1 wire-format decision against v7 before wiring `streamAi`.
2. **Gemini thought tokens.** `google-genai` exposes `usage_metadata.thoughts_token_count`. The Streamlit app already tracks `total_thought_tokens` — keep that counter **server-side** in the FastAPI usage ledger (Batch 3: instrumentation is server-side, never in React).
3. **Stack pins for reference:** `react ^19.2.0`, `vite ^8.1.5`, `@tanstack/react-router ^1.170.18`, `@tanstack/router-plugin ^1.168.23` — the TanStack pins match the live-verified §3.6 versions (1.170.20 / 1.168.25).
---

## Round 3 Research Addendum (2026-08-05)

> Source: archive §3.10 (live-verified round-3 research). Applies on top of the Round 2 addendum.

1. **`toTextStreamResponse()` confirmed against the captured code.** The captured `src/routes/api/chat.ts` streams chat via `streamText(...).toTextStreamResponse()` — plain `text/plain` output. Step 6's plain-text reader is exactly right for the plain-text path; the `useChat` caveat (structured v7 protocol) still applies if the chat UI ever switches to `useChat`. (Archive §3.10 item 1.)
2. **Nitro/Lovable server routes are removed in Phase 4 — the store calls FastAPI directly.** The captured chat route lives under `src/routes/api/` (a Start/Nitro server route). After the Phase 4 strip (archive §3.10 item 2), `streamAi` targets `${API_BASE}/chat` — already the plan — with no server-route fallback left behind.
3. **MSW chat-stream tests.** Mock the stream with an MSW `HttpResponse` + `ReadableStream` body and `Content-Type: text/event-stream`; drive the store's `getReader()` path — jsdom ships no real `EventSource`. (Archive §3.10 item 4.)
