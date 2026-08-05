# Insights Explorer — Migration & Integration Plan
## Moving from Streamlit UI to React Frontend with FastAPI Bridge

**Date:** 2026-08-05
**Context:** Consolidated analysis of Freebuff conversation, repository inspection, and multi-perspective review
**Status:** Plan (no code written yet)

---

## Executive Summary

Keep `insights-explorer` as the canonical repository. Do **not** switch base to `insights-whisperer-30`. Instead, extract a FastAPI service from the existing Python backend, and fold the React UI from `insights-whisperer-30` into the same repo as a new `frontend/` directory. Retire Streamlit incrementally.

This preserves the 742-test safety net, GA4/Drive/Gemini integration logic, and release infrastructure while removing the Streamlit UI ceiling.

---

## Decision: Which Repo Is the Base?

| Option | Verdict | Rationale |
|---|---|---|
| **A. `insights-explorer` stays base** | ✅ **Recommended** | Contains 8,461 LOC of hardened backend (GA4 OAuth, Drive download guards, DataContext state machine, Gemini streaming, 742 tests, CI, release process). Refactor cost is bounded. |
| **B. `insights-whisperer-30` becomes base** | ❌ Rejected | Losing test suite, CI, docs, release checklist, and repo history. Python backend would need full re-import into a Bun/TS repo. Strictly more work for same end state. |
| **C. Rebuild React UI from scratch in Python repo** | ❌ Rejected | `insights-whisperer-30` already exists, is owned by you, and its own README says it is "the ideal UI shell" for the Python backend. |
| **D. Embed React inside Streamlit** | ❌ Rejected | Worst of both worlds: Streamlit design constraints persist, plus iframe complexity. |

**Bottom line:** `insights-explorer` is the product of record. `insights-whisperer-30` is a design artifact whose components get adopted wholesale.

---

## What Each Repo Actually Contains

### `insights-explorer` (Python/Streamlit)
- **Purpose:** Product of record with real backend
- **Key assets:**
  - `utils/` — 16 modules (data_context, ga4_client, drive_client, gemini_client, forecasting, funnels, quality, charts, exports, commands, sanitize, session, prompt_templates, styles, error_boundary)
  - `components/` — 10 Streamlit UI components (sidebar, hero, chat, summary, data_preview, learning_challenge, onboarding_tour, drive_picker_component)
  - `tests/` — 742 unit tests + 32 Playwright smoke tests
  - CI, pre-commit, credential guard, release checklist, changelog, roadmap
  - `requirements.txt` — 25 lines (light dependency footprint)
  - `app.py` — Streamlit entry point
- **Lines of code:** ~8,461 in utils/components/pages/app
- **Streamlit coupling:** 7 of 16 utils import Streamlit (shallow: cache decorators, session_state reads, styles, error_boundary)
- **Hosting:** Streamlit Community Cloud (currently)

### `insights-whisperer-30` (React/TypeScript)
- **Purpose:** UI shell prototype (explicitly designed to connect to Python backend)
- **Key assets:**
  - `src/components/explorer/` — 14 explorer components (AiSummary, ChartCard, Chat, DataPreview, EmptyHero, EquityPanel, ExportMenu, Markdown, OnboardingTour, ResearchPanel, Scorecard, Sidebar, TopBar, UploadZone)
  - `src/components/ui/` — 35 shadcn/ui components (accordion, alert-dialog, button, card, dialog, etc.)
  - `src/lib/` — mock-ga4, mock-braintree, explorer-store (context provider), ai-gateway.server (Lovable AI gateway), research sources, error capture
  - `src/routes/api/` — chat.ts (streams via Vercel AI SDK), research.ts
  - `src/server.ts`, `src/start.ts` — Nitro server runtime
- **Stack:** React 19, TypeScript, Vite 8, TanStack Router/Start, Tailwind v4, shadcn/ui, Recharts, lucide-react, sonner, `ai` SDK (Vercel AI SDK), Nitro
- **Backend reality:** Mock data only (`mock-ga4.ts`, `mock-braintree.ts`). No real GA4, Drive, or OAuth. Only live call is a chat proxy through Lovable's AI gateway.
- **Design system:** Dark-first (`#0D0D0F` base, `#3B82F6` accent, Inter/Geist typography, 4–6px radius, borders over shadows)
- **Age:** ~2 days (created 2026-08-03)

---

## Critical Risks & Challenges

| Risk | Severity | Mitigation |
|---|---|---|
| **OAuth redirect flow breaks** when moving from Streamlit to React | High | Design OAuth callback route in FastAPI that exchanges token and issues session cookie; React holds session. |
| **Streaming chat (SSE) differs** from Streamlit's synchronous model | Medium | Use SSE from FastAPI to React; `ai` SDK already supports streaming; existing `gemini_client` does streaming internally. |
| **Drive Picker component** needs re-integration | Medium | The existing `drive_picker_component_frontend` TS code is reusable; server-side download (`drive_client.py`) stays in Python. |
| **Streamlit-layer tests retire** but not all 742 | High | Track which tests target UI vs utils; rewrite UI tests as API-contract tests; utils tests stay green. |
| **Hosting change required** | Medium | Streamlit Community Cloud won't run FastAPI + React; move to container platform (Railway/Render/Fly). |
| **Two UIs alive during transition** = double work | Medium | Hard cutover per surface; feature-flag or module-by-module migration. |
| **DataContext serialization** from Python to JSON | Medium | DataContext is a dataclass; design clean JSON schema for React store. |
| **Lovable AI gateway dependency** in whisperer-30 | Low | Replace with direct Gemini API calls via FastAPI; Lovable gateway is optional. |

---

## Comprehensive Plan: 6 Phases

### Phase 1: API Contract & FastAPI Skeleton (Week 1)

**Goal:** Define the JSON contract between React and Python, and stand up a minimal FastAPI app.
**Research amendments (2026-08-05):** decide the **chat wire format at contract time** — before `POST /api/chat` is written, pick either plain SSE (`text/event-stream`, `data: <chunk>\n\n` framing) or the Vercel AI SDK data-stream (`toDataStreamResponse()` / `toUIMessageStreamResponse()`); the two are not interchangeable and `useChat` only parses the SDK format. Record the choice in the OpenAPI contract so Phases 3–4 implement against it consistently. *(Source: archive §3.5, §3.8 item 3.)*

**Steps:**
1. Create `api/` directory in `insights-explorer`.
2. Define API endpoints (OpenAPI/Swagger):
   - `POST /api/upload` — accept CSV/XLSX, validate, create DataContext
   - `GET /api/data/preview` — return first N rows + column types
   - `GET /api/data/quality` — return quality scorecard
   - `GET /api/data/charts` — return chart data (sessions/users, top pages)
   - `POST /api/chat` — SSE streaming endpoint
   - `GET /api/analysis/summary` — AI summary generation
   - `GET /api/analysis/forecast` — forecast data
   - `GET /api/analysis/funnel` — funnel data
   - `POST /api/export` — markdown/excel/pdf
   - `POST /api/ga4/connect` — OAuth URL generation
   - `GET /api/ga4/callback` — OAuth token exchange
   - `POST /api/ga4/pull` — pull GA4 data
   - `POST /api/drive/picker-token` — Google Picker token
   - `POST /api/drive/download` — download from Drive
3. Write `api/main.py` with FastAPI app, CORS, health check.
4. Write `api/dependencies.py` for session management (replace `st.session_state`).
5. Write `api/serializers.py` for DataContext → JSON conversion.
6. Add `fastapi`, `uvicorn`, `python-multipart` to `requirements.txt`.

**Deliverable:** FastAPI app runs on `:8000`, health check passes, one endpoint works (e.g., `GET /api/data/quality` with mock data).

---

### Phase 2: Extract Framework-Neutral Services (Week 2)

**Goal:** Decouple `utils/` from Streamlit so they can be called by both FastAPI and (temporarily) Streamlit.

**Steps:**
1. Identify the 7 utils with Streamlit imports: `data_loader`, `error_boundary`, `forecasting`, `gemini_client`, `prompt_templates`, `session`, `styles`.
2. For each, extract Streamlit-specific code into `components/` or `app.py`:
   - `styles.py` → keep in Streamlit only (presentation layer)
   - `error_boundary.py` → keep in Streamlit only (UI error handling)
   - `session.py` → replace with FastAPI session management
   - `data_loader.py` → remove `@st.cache_data`; use FastAPI caching or no caching
   - `forecasting.py` → remove `st.cache` if present; keep pure functions
   - `gemini_client.py` → remove Streamlit rate-limit display; keep core API calls
   - `prompt_templates.py` → remove `st.session_state` reads; pass context as arguments
3. Ensure remaining utils are pure functions: `data_context`, `ga4_client`, `drive_client`, `charts`, `funnels`, `quality`, `exports`, `commands`, `sanitize`.
4. Run 742 tests to confirm nothing breaks.

**Deliverable:** `utils/` is Streamlit-free (or minimally coupled); FastAPI can import and call any util.

---

### Phase 3: Wire FastAPI to Real Utils (Week 3)

**Goal:** Replace mock data in FastAPI with real calls to existing Python logic.
**Research amendments (2026-08-05):** **funnel nuance** — the GA4 Data API includes `runFunnelReport`, so *template* funnels (steps defined by event/dimension filters) may be partially available even where the roadmap marks funnels blocked. When implementing `GET /api/analysis/funnel` via `funnels.py`, scope it to template funnels and re-verify the ROADMAP funnel rows (Gate 1.7 / Top-25) at implementation time. *(Source: archive §3.4, §3.8 item 4.)*

**Steps:**
1. Implement `POST /api/upload` using `data_loader.py`.
2. Implement `GET /api/data/preview` using `data_context.py`.
3. Implement `GET /api/data/quality` using `quality` functions.
4. Implement `GET /api/data/charts` using `charts.py`.
5. Implement `GET /api/analysis/summary` using `gemini_client.py` + `prompt_templates.py`.
6. Implement `GET /api/analysis/forecast` using `forecasting.py`.
7. Implement `GET /api/analysis/funnel` using `funnels.py`.
8. Implement `POST /api/export` using `report_exporter.py`.
9. Write API-contract tests (pytest + httpx) for each endpoint.

**Deliverable:** All read-only endpoints return real data from Python utils; tests pass.

---

### Phase 4: Port React UI into Repo (Week 4)

**Goal:** Move the whisperer-30 components into `insights-explorer` as `frontend/`, and swap mock store calls for API calls.
**Research amendments (2026-08-05):**
- **Wire format:** when swapping `streamAi` → `fetch('/api/chat')`, consume exactly the format chosen in Phase 1 (plain SSE vs SDK data-stream) — do not mix. The store's plain-text `getReader()` + `TextDecoder` accumulation is correct only for plain SSE / `toTextStreamResponse()` output. *(§3.5.)*
- **Routing:** use TanStack Router's `validateSearch` + `Route.useSearch()` for typed search params (e.g., the GA4 callback's `status`/`reason`) rather than raw `window.location.search`. *(§3.6, §3.8 item 6.)*

**Steps:**
1. Copy `src/` from `insights-whisperer-30` into `insights-explorer/frontend/`.
2. Update `frontend/package.json` to remove Lovable-specific dependencies (`@lovable.dev/vite-tanstack-config`, `lovable-error-reporting`).
3. Replace `src/lib/mock-ga4.ts` and `src/lib/mock-braintree.ts` with API calls to FastAPI.
4. Update `src/lib/explorer-store.tsx`:
   - Replace `defaultSource` import with `fetch('/api/data/preview')`
   - Replace `streamAi` with `fetch('/api/chat')` (SSE)
   - Keep the context provider structure (it was designed for this swap)
5. Update `src/lib/ai-gateway.server.ts` to call FastAPI instead of Lovable gateway.
6. Update `src/routes/api/chat.ts` to proxy to FastAPI (or remove if FastAPI handles chat directly).
7. Add `frontend/README.md` explaining the setup.
8. Add `frontend/` to root `.gitignore` if needed (node_modules, dist).

**Deliverable:** React app runs on `:5173`, talks to FastAPI on `:8000`, displays real data.

---

### Phase 5: Migrate OAuth & Drive Picker (Week 5)

**Goal:** Solve the two hardest integration points: GA4 OAuth and Drive Picker.
**Research amendments (2026-08-05):**
1. **OAuth — add PKCE** (S256 `code_verifier` / `code_challenge`) to `begin_oauth()` / `exchange_code()`; recommended for all client types under RFC 9700 / OAuth 2.1. Keep the exact `redirect_uri` string match constructed in one place. *(§3.2.)*
2. **Drive Picker** — `POST /api/drive/picker-token` must return the OAuth token **and the project number** (`setAppId`); document Cloud Resource Manager API enablement in the Drive-import setup notes. *(§3.3, §3.8 item 2.)*
3. **GA4 pull** — paginate (`limit`/`offset`, 10k-row pages, ≤9 dimensions) and throttle for the **10-concurrent-request** quota; enable `returnPropertyQuota: true` for observability. *(§3.4, §3.8 item 7.)*
4. **Callback route** — implement the React callback page with `validateSearch` / `useSearch` (typed search), not `window.location.search`. *(§3.6.)*
5. **Supersession note:** the original step “React app stores session token in localStorage/cookie” is **superseded** by the Batch 3 server-owned session model (browser holds only the opaque `HttpOnly` cookie; tokens stay server-side) — see the Batch 3 Review Addendum, item 3.
6. **Callback route validation details (live-verified, §3.6):** use a `validateSearch` schema for `status`/`reason` read via `Route.useSearch()`; on validation failure the router sets `error.routerCode === "VALIDATE_SEARCH"` and renders the route's `errorComponent` — that is the invalid-state mechanism for the callback page (verified against `@tanstack/react-router@1.170.20`).

**Steps:**
1. **GA4 OAuth:**
   - Design `POST /api/ga4/connect` to return OAuth URL (from `ga4_client.py`).
   - Design `GET /api/ga4/callback` to exchange code for token, store in session, redirect to React app.
   - React app stores session token in localStorage/cookie.
   - Design `POST /api/ga4/pull` to use stored token.
2. **Drive Picker:**
   - Reuse `components/drive_picker_component_frontend` TS code in React app.
   - Design `POST /api/drive/picker-token` to return Google Picker API token.
   - Design `POST /api/drive/download` to use existing `drive_client.py` download logic.
   - Ensure error taxonomy (size limits, file types) is preserved.
3. Test OAuth flow end-to-end in React.
4. Test Drive Picker end-to-end in React.

**Deliverable:** GA4 and Drive workflows work in React UI.

---

### Phase 6: Cutover & Retire Streamlit (Week 6)

**Goal:** Decommission Streamlit UI, retire Streamlit-specific tests, and move hosting.
**Research amendments (2026-08-05):** **single-origin hosting** — bundle the built React SPA into the FastAPI container via a **multi-stage Dockerfile** on Railway/Render/Fly; avoid Render's default split Static Site + Web Service (split origins break the same-origin session-cookie / OAuth / CORS / SSE model). Also re-check the “Forecast & funnel ✅” parity row — template funnels may be partially available via `runFunnelReport` (see the Phase 3 amendment). *(§3.1, §3.4, §3.8 items 4–5.)*

**Steps:**
1. **Feature parity check:**
   - Upload CSV/XLSX ✅
   - Connect GA4 ✅
   - Import from Drive ✅
   - Data preview ✅
   - Quality scorecard ✅
   - AI summary ✅
   - Charts ✅
   - Forecast & funnel ✅
   - Chat ✅
   - Export ✅
   - Learn page ✅
   - Onboarding tour ✅
2. **Retire Streamlit tests:**
   - Identify tests targeting `components/` (sidebar, chat, hero, etc.)
   - Archive or delete them; replace with API-contract tests.
3. **Move hosting:**
   - Deploy FastAPI + React to Railway/Render/Fly.
   - Update DNS if needed.
   - Keep Streamlit Community Cloud as fallback for 1 week.
4. **Update docs:**
   - `README.md` — new setup instructions
   - `ARCHITECTURE.md` — new architecture diagram
   - `CHANGELOG.md` — v0.4.0 entry
5. **Archive `insights-whisperer-30`:**
   - Add note to README: "Folded into insights-explorer as frontend/ directory."
   - Archive repo on GitHub.

**Deliverable:** Single product at single URL, React UI, FastAPI backend, Streamlit retired.

---

## API Contract (Draft)

### Data Structures

```typescript
// DataContext (serialized)
interface DataContext {
  source: string;           // "upload" | "ga4" | "drive"
  filename: string;
  rowCount: number;
  dateRange: { start: string; end: string };
  columns: Column[];
  filters: Filter[];
  metrics: Metric[];
  provenance: Provenance;
}

interface Column {
  name: string;
  type: "date" | "number" | "string";
  nullable: boolean;
}

interface Filter {
  id: string;
  field: string;
  value: string;
}

interface Metric {
  id: string;
  name: string;
  agg: "sum" | "avg" | "count" | "min" | "max";
}

interface Provenance {
  uploadedAt: string;
  lastModified: string;
  transformations: string[];
}
```

### Endpoints

| Method | Path | Request | Response |
|---|---|---|---|
| POST | `/api/upload` | `multipart/form-data` (file) | `DataContext` |
| GET | `/api/data/preview` | — | `{ rows: Row[], columns: Column[] }` |
| GET | `/api/data/quality` | — | `{ score: number, warnings: string[], rowCount: number, dateRange: DateRange }` |
| GET | `/api/data/charts` | — | `{ sessionsUsers: ChartData, topPages: ChartData }` |
| POST | `/api/chat` | `{ messages: Message[], mode: "chat" \| "summary" }` | SSE stream |
| GET | `/api/analysis/summary` | — | `{ summary: string, generatedAt: string }` |
| GET | `/api/analysis/forecast` | — | `{ forecast: ForecastData }` |
| GET | `/api/analysis/funnel` | — | `{ funnel: FunnelData }` |
| POST | `/api/export` | `{ format: "markdown" \| "excel" \| "pdf" }` | `Blob` |
| POST | `/api/ga4/connect` | — | `{ authUrl: string }` |
| GET | `/api/ga4/callback` | `?code=...` | Redirect to React |
| POST | `/api/ga4/pull` | `{ propertyId: string, dateRange: DateRange }` | `DataContext` |
| POST | `/api/drive/picker-token` | — | `{ token: string }` |
| POST | `/api/drive/download` | `{ fileId: string }` | `DataContext` |

---

## Success Metrics

| Metric | Target | How to Measure |
|---|---|---|
| Feature parity | 100% | Manual checklist of all 12 features |
| Test coverage | ≥80% of utils | `pytest --cov=utils` |
| API contract tests | 100% of endpoints | `pytest tests/api/` |
| React E2E tests | 5 critical flows | Playwright (upload, GA4, Drive, chat, export) |
| Performance | <2s initial load | Lighthouse |
| Bundle size | <500KB gzipped | `vite build` analysis |
| OAuth success rate | >95% | Error tracking |
| Chat streaming latency | <500ms first token | Server logs |

---

## Open Questions

1. **Hosting platform:** Railway, Render, or Fly? (Each has different pricing and deployment models.)
2. **Session storage:** Redis, PostgreSQL, or in-memory? (Affects scalability and cost.)
3. **Lovable AI gateway:** Keep as optional fallback or remove entirely?
4. **Streamlit fallback:** Keep running for 1 week or decommission immediately?
5. **Repo structure:** `frontend/` and `api/` as siblings, or `frontend/` inside `api/`?

---

## Next Actions

- [ ] Review this plan with stakeholders
- [ ] Create GitHub issues for each phase
- [ ] Set up project board (GitHub Projects)
- [ ] Begin Phase 1: API contract definition
- [ ] Schedule hosting decision meeting

---

*This plan synthesizes the Freebuff conversation, repository inspection, and multi-perspective analysis. It challenges assumptions (e.g., "utils are framework-free" → actually 7/16 import Streamlit), solves for risks (OAuth, streaming, hosting), and provides a concrete, phased path forward.*
---

## External Research Addendum (2026-08-05)

Source-backed research gathered to validate this plan — full detail, citations, and the delta list live in `insights-explorer-migration-ingest.md` Part 3. Highlights that affect plan decisions:

1. **Hosting (Phase 6).** Railway, Render, and Fly.io can all run FastAPI (uvicorn) **and** serve the built React SPA from the same origin — but only if the Vite output is bundled into the FastAPI container via a multi-stage Dockerfile. Render's default UI pushes split Static Site + Web Service (split origins → breaks the same-origin cookie rule); use a Docker-based Web Service instead. Streamlit Community Cloud is confirmed **unable** to run FastAPI or React — the "hosting change required" risk stands.
2. **OAuth (Phase 5).** The corrected design (Google → FastAPI callback, server-side `state` validation, server-side token storage) matches current Google guidance. **Add PKCE** (S256 `code_verifier`/`code_challenge`) — recommended for all client types under RFC 9700 / OAuth 2.1 — and note the configured `redirect_uri` must be an exact string match.
3. **Drive Picker.** Launch requires the developer API key (`setDeveloperKey`), an OAuth access token (`setOAuthToken`), and the **project number** (`setAppId`), which may require enabling the Cloud Resource Manager API. Restrict the API key to HTTP referrers. Third-party-cookie blocking can break Picker sign-in in iframes.
4. **GA4 "hard blocker".** Confirmed aggregate-only at the report level (no event/user-level rows; up to 9 dimensions; default 10k rows, paginated). **Nuance:** the Data API includes `runFunnelReport` — template funnels may be partially available without event-level export; user/identifier-level analyses (retention, cohorts, pathing) remain blocked.
5. **SSE (Phases 3–4).** FastAPI should stream `text/event-stream` with `data: ...\n\n` framing. If the React app keeps the Vercel AI SDK's `useChat`, it expects the SDK's structured data-stream — not plain SSE. Decide the wire format deliberately.
---

## Reconciliation Addendum (2026-08-05)

Cross-checked against the repo and the sibling docs (full ledger: `insights-explorer-migration-ingest.md` Part 4). Original content above is preserved; the deltas that affect this plan are:

1. **Component count correction.** The repo profile says "10 Streamlit UI components"; the actual count is **8 Python component modules** (`chat`, `data_preview`, `drive_picker_component`, `hero`, `learning_challenge`, `onboarding_tour`, `sidebar`, `summary`) — the other two entries are `__init__.py` and the `drive_picker_component_frontend/` TS app.
2. **`utils/` precision.** 16 files including `__init__.py` (15 modules). The "7 of 16 import Streamlit" claim was verified exactly — the seven are `data_loader`, `error_boundary`, `forecasting`, `gemini_client`, `prompt_templates`, `session`, `styles`.
3. **Test counts verified.** 742 unit + 32 Playwright smoke, confirmed via `pytest --collect-only` on 2026-08-05.
4. **Health endpoint.** The draft GitHub issue and Phase 1 deliverable say `GET /health`; the implementation packet implements `GET /healthz`. **Adopt `/healthz`** when creating issues and the smoke script.
5. **Response shapes.** The endpoint table shows bare `DataContext` and `{ rows, columns }`; the implementation packet uses `UploadResponse { dataset }` and `{ dataset, rows }`, and adds `GET /api/data/context`. **Adopt the packet's shapes**; the contract table is superseded where it conflicts.
6. **`ga4/connect` field.** Plan table shows `{ authUrl }`; the packet returns `{ authorization_url }` (snake_case at the API boundary). Adopt `authorization_url`, alias if the store needs camelCase.
7. **Summary endpoint.** `GET /api/analysis/summary` (plan) vs chat `mode: "summary"` (store prompt). Recommend **chat-mode streaming as canonical**; keep the GET endpoint only as a non-streaming fallback.
8. **Verified facts unchanged:** 8,461 LOC, 742/32 tests, `plans/ga4-measurement-contract.md` exists, dual CI, Drive Picker standalone TS app.
---

## Batch 3 Review Addendum (2026-08-05)

> Source: PASTE 11 of `insights-explorer-migration-ingest.md` (§1.13 synthesis, §2.15 verbatim, §4.6 verification). Reframes the effort as a **product-platform migration** — data/session ownership, OAuth, security, testing, CI, and deployment change together. All items below are decision inputs for the phases; no existing phase text is rewritten.

### Security — do this before anything else

- **Tracked `.env` in `insights-whisperer-30` is verified** (62 B, committed in `9059739`; **no `.env.example`** exists; **no `.gitignore` rule** covers `.env`). Before copying the repo in: inspect full git history for the file and any secrets, **revoke/rotate** every real credential it may contain (Lovable, Google, Gemini, …), `git rm --cached .env`, and add a safe `.env.example`.
- Keep the existing credential-guard patterns (`scripts/check_credentials.py`, `.pre-commit-config.yaml`, the credential-guard tests) enforced for the FastAPI layer and its env vars.

### Process decisions (new)

1. **Migration branch + feature freeze:** create `feat/react-fastapi-migration`; only production/security fixes land on Streamlit while the API contract stabilizes.
2. **Whisperer-30 stays a living design reference until cutover** — copy it into the canonical repo only when the frontend build is reproducible; keep the original for visual comparison, regression checks, and fallback.

### Design disciplines (apply across phases)

3. **Server-owned session model:** browser holds only an opaque `HttpOnly` secure session cookie; FastAPI owns the dataset reference, OAuth credentials, filter/metric/chat state; raw data and provider tokens never reach localStorage / React state persistence / URLs / logs / client-side analytics. Storage abstraction now: in-memory (dev) → Redis/Postgres-compatible (deployed multi-instance).
4. **Contract discipline:** `plans/ga4-measurement-contract.md` stays the source of truth; Python canonical domain models serialized at one API boundary; **typed React client generated or validated from OpenAPI/JSON Schema**; naming normalized once (API emits snake_case, client translates — never individual components); **version the API early as `/api/v1`** so the evidence connector evolves safely.
5. **Test by behavior (four-layer matrix):** Python unit (parsing, GA4/Drive, analysis, quality, forecasting, exports, sanitization) · FastAPI contract (auth/session, schema validity, error taxonomy, upload limits, OAuth state) · React unit/component (loading/empty/error/success/a11y/API-client) · Playwright E2E (upload→preview→chart; GA4 OAuth error/success; Drive selection; AI streaming; export). `mock-ga4.ts` / `mock-braintree.ts` become MSW test fixtures only — never product imports.
6. **Deployment prerequisites before provider choice:** expected file sizes, concurrent users, GA4 query volume, background-task needs, session/data retention, observability (structured logs, request IDs, sanitized error reporting, health/readiness), Gemini rate limits and per-user quotas. Same-origin deployment (React static assets behind the FastAPI container) for cookies/OAuth/CORS/SSE simplicity.
7. **Phase 1 scope (tight):** Upload CSV → validate via existing Python logic → server session → React preview/quality state → clear-data → regression tests. Then GA4 → Drive → AI streaming → advanced analysis, sequentially.

### Reconciliation notes

- Nothing in this batch contradicts the Part 4 §4.2 contract choices (`/healthz`, `authorization_url`, `{ dataset }` wrapper, `credentials: "include"`, `setSourceFromApi`) — it reinforces them: the server-session model implies `credentials: "include"` + an opaque cookie.
- Drive Picker: port as a **native React component** preserving the size safeguards + error taxonomy (not an embedded Streamlit component).
- Preserve `utils/prompt_templates.py` behavior and client/data safeguards — never let the whisperer's hardcoded BrainGuide system prompt become production logic.

---

## Research Fold-In Log (2026-08-05)

The seven research corrections from `insights-explorer-migration-ingest.md` Part 3 §3.8 are now folded into the phase sections above. This pass is **additive** — original phase text is preserved; each affected phase carries an inline **Research amendments (2026-08-05)** note.

| # | Correction | Folded into |
|---|---|---|
| 1 | Add PKCE (S256) to the OAuth flow — RFC 9700 | Phase 5 |
| 2 | Picker token endpoint returns token **and** project number; document Cloud Resource Manager API | Phase 5 |
| 3 | Decide chat wire format explicitly (plain SSE vs AI SDK data-stream) | Phases 1 + 4 |
| 4 | Funnel nuance — `runFunnelReport` makes template funnels partially available | Phases 3 + 6 |
| 5 | Single-origin hosting via multi-stage Dockerfile; avoid Render split Static Site + Web Service | Phase 6 |
| 6 | TanStack Router `validateSearch` / `useSearch` over raw `window.location.search` | Phases 4 + 5 |
| 7 | GA4 pull: paginate + throttle (10 concurrent); `returnPropertyQuota: true` | Phase 5 |

Sources and citations: archive Part 3 (§3.1–3.8). One inline supersession note was added (Phase 5's `localStorage` step vs the Batch 3 server-owned session model) — flagged in the phase amendment, not rewritten.
