# Master Plan — Streamlit → React + FastAPI Migration

**Date:** 2026-08-05
**Status:** 🔵 Planning — no migration product code written (planning docs are committed on `main`). This document is the **execution coordinator** for everything in `migration/`.
**Revised:** 2026-08-05 — review feedback folded in (first pass: session store & upload architecture moved to Phase 0/1, canonical API decisions record, data-retention policy, three release gates). **Second revision (2026-08-05):** upload cap locked at 25 MB, session decision reframed as state placement, 8-gate priority checklist.
**How to use this document:** implement *from here*, consult the source docs for detail. Each phase lists its inputs (specific docs/sections), tasks, and exit criteria. Nothing in this plan is executed until it is explicitly approved.

---

## 1. Role of this document

The `migration/` folder holds eleven planning docs plus a reference capture. This master plan does **not** replace them — it **coordinates** them:

| What | Where |
|---|---|
| **Raw material + verification** (source of truth) | `insights-explorer-migration-ingest.md` (archive, Parts 1–4) |
| **The 6-phase roadmap** (the phase *shapes* below come from here) | `insights-explorer-migration-plan.md` |
| **Phase 1 backend implementation packet** (code-level detail) | `phase-1-api-react-callback-tests-implementation.md` (F4) |
| **Frontend store wiring prompt** (13-step change list) | `freebuff-prompt-wire-react-store.md` (F3) |
| **Security gate before any code copy-in** | `env-rotation-checklist.md` |
| **Process policy (branch + freeze)** | `branch-and-freeze-policy.md` |
| **State migration record** (44 keys) | `session-state-inventory.md` |
| **Which tests transfer** (742 = 452 + 290 + 40) | `test-layer-inventory.md` |
| **Hosting pattern** (single-origin Docker) | `dockerfile-pattern.md` |
| **Independent audit lens** | `glm-5-2-vs-perplexity-migration-comparison.md` |
| **Source UI repo frozen capture** (18 files) | `whisperer-30-reference/` |
| **Retention & AI data-boundary policy** (new) | `data-retention-policy.md` |

The master plan adds what none of the source docs have: **execution order, inter-phase dependencies, a single file-organization target, cross-cutting workstreams, and one Definition of Done**.

---

## 2. Guiding principles (locked decisions from the archive)

1. **`insights-explorer` is the system of record.** whisperer-30's React components are adopted wholesale as the new frontend; its mocks/gateway/prompts never become production logic. (Archive §1.1; plan "Decision".)
2. **Server-owned session model.** Browser holds only an opaque `HttpOnly` secure session cookie. Dataset reference, OAuth credentials, filter/metric/chat state live server-side. Raw data and provider tokens never reach localStorage, URLs, logs, or client analytics. (Archive §1.13 / Batch 3, item 3; `session-state-inventory.md` §7.)
3. **Single-origin deployment.** Built React SPA served statically behind the FastAPI container — required for cookies, OAuth callbacks, CORS, and SSE. No split origins. (Archive §3.1, §3.10 item 3, §3.11; `dockerfile-pattern.md`.)
4. **Contract discipline.** `plans/ga4-measurement-contract.md` stays canonical; Python domain models serialize at one API boundary; typed React client generated/validated from OpenAPI; API versioned `/api/v1`; naming normalized once (API emits snake_case, client translates). (Archive §1.13 item 4; §4.2.)
5. **Test by behavior, not implementation.** Four-layer matrix: Python unit · FastAPI contract · React component (MSW) · Playwright E2E. Mocks become test fixtures only. (Archive §1.13 item 5; `test-layer-inventory.md`.)
6. **Tight Phase 1 scope.** One vertical slice first: Upload CSV → validate via existing Python logic → server session → React preview/quality → clear-data → regression tests. Then GA4 → Drive → AI streaming → advanced analysis. (Archive §1.13 item 7.)
7. **Incremental PRs per deliverable; additive documentation.** Original docs preserved; decisions appended as dated addenda.
8. **whisperer-30 stays a living design reference until cutover.** (Archive §1.13 item 2.)

---

## 3. Execution overview

```
Phase 0  Security gate + process setup          (prereq for everything)
   │
   ▼
Phase 1  API contract + FastAPI skeleton (F4)   ──┐  cross-cutting:
   │                                              │  A. State migration
   ▼                                              │  B. Contract discipline
Phase 2  Decouple utils/ from Streamlit           │  C. Test strategy
   │                                              │  D. Security & credentials
   ▼                                              │  E. CI/CD & deployment
Phase 3  Wire real utils into FastAPI             │
   │                                              │
   ▼                                              │
Phase 4  Port React UI into frontend/ (F3)        │
   │                                              │
   ▼                                              │
Phase 5  GA4 OAuth + Drive Picker                 │
   │                                              │
   ▼                                              │
Phase 6  Cutover, hosting (Cloud Run), retire     ┘
```

**Dependency rules (critical path):**
- Phase 0 blocks **all** phases (security + branch policy).
- Phase 1's **chat wire format decision** must be made *before* Phase 3 (backend) and Phase 4 (frontend) implement chat — the two are not interchangeable (plain SSE vs AI SDK data-stream; `useChat` only parses the SDK format). (Plan Phase 1 amendment; archive §3.5.)
- Phase 2 is a prerequisite for Phase 3 (FastAPI calls utils) — but Phase 1's skeleton and Phase 2's decoupling are otherwise independent and may overlap.
- Phase 4 (frontend port) is independent of Phases 2–3 until the store is wired to real endpoints; wire in the order Phase 3 provides.
- Phase 5 (OAuth + Drive) depends on the Phase 1 session/schema layer and on Phase 4's React shell.
- Phase 6 (hosting + retirement) depends on everything.

**Suggested PR seams (from the archive's incremental-PR principle):** one PR per phase deliverable; Phase 0 splits into PR-0a (security gate) / PR-0b (branch + policy).

**Phase 0/1 gates — locked before product code (master-plan revision 2026-08-05):** (1) browser-upload architecture decided (**25 MB direct browser cap**); (2) **state-placement architecture** locked — `SessionStore`/`DatasetStore` interfaces defined, shared ephemeral session/OAuth storage + object storage for raw uploads proven before Phase 5; (3) canonical API decisions record published to all implementation-facing docs with old paths marked superseded; (4) data-retention + AI data-boundary policy written. Items 1–6 of the 8-gate priority checklist (§4) must be locked before Phase 1 starts.

---

## 4. Phase 0 — Security gate & process setup (prereq, no product code)

**Inputs:** `env-rotation-checklist.md` (full) · `branch-and-freeze-policy.md` (full) · archive §1.13 / Batch 3.

**Goal:** make it safe to copy whisperer-30 code in, and freeze Streamlit feature work so the migration surface stops growing.

**Tasks:**
- [ ] **Rotate/revoke credentials (manual — provider consoles).** The whisperer-30 repo tracks a real `.env` (62 B, commit `9059739`, no `.env.example`, no gitignore rule). Treat as potentially exposed: inspect git history → identify real vs placeholder per provider (Google Cloud / Gemini / Lovable / other) → **rotate every real credential** → `git rm --cached .env` → add safe `.env.example` → gitignore rule. History scrub (`git filter-repo`) is optional but documented. *Follow `env-rotation-checklist.md` Phases A–E.*
- [ ] **Cut `feat/react-fastapi-migration` branch.** `main` = production/security fixes only; all migration work lands on the branch with the fix-forward rule. Feature freeze applies to broad Streamlit work (test: any new `st.session_state` key during the freeze needs a documented replacement — see `session-state-inventory.md`). Lift criteria in `branch-and-freeze-policy.md` §5.
- [ ] **Inventory the 44 `st.session_state` keys** (done — `session-state-inventory.md`). Adopt it as the working checklist for Phases 2/4.
- [ ] **Confirm the Streamlit baseline is green** before any changes (see Phase 1 verification commands).
- [x] **Lock the browser-upload architecture — DONE (2026-08-05): 25 MB direct browser cap.** Cloud Run under HTTP/1 caps request size at **32 MiB**; end-to-end HTTP/2 has no stated request-size limit — but HTTP/2 is **not** selected merely to preserve 100 MB browser uploads (it adds transport/deployment complexity without solving parsing memory, dataframe expansion, processing time, retention, or cleanup). Signed Cloud Storage upload is deferred until real file-size evidence requires it. (Archive §4.12–4.13; Cloud Run quotas.)
- [x] **Lock the session/data architecture — DONE (2026-08-05): state placement, not one store.** `SessionStore`/`DatasetStore` interfaces with in-memory implementations for local dev; **shared ephemeral storage for session/OAuth state + object storage for raw uploads proven before Phase 5 (GA4 OAuth + Drive)** — Cloud Run routes requests across instances and session affinity is best-effort, not a consistency guarantee. The durable database choice (refresh tokens, audit) is postponed until real multi-user/audit requirements exist. (Archive §4.13.)
- [x] **Publish the canonical API decision record** (prefix `/api/v1`, `/healthz`, `{ dataset }`, HttpOnly cookie + `credentials: "include"`, snake_case at the boundary, `api.ts` camelCase, chat transport, upload policy) and add it to the top of every implementation-facing doc (F3, F4, plan) with old paths marked superseded. **DONE (2026-08-05 revision pass).**
- [x] **Write the data-retention + Gemini data-boundary policy** — **DONE (2026-08-05):** `migration/data-retention-policy.md` exists; the ⚠️-flagged defaults inside (retention window, session expiry, export-log retention) still need product confirmation.

**Exit criteria (DoD):** `.env` rotation completed with evidence (checklist §Verification) · branch created · baseline test run recorded.

**Phase 0/1 priority gates (8-item checklist — review refinement 2026-08-05, archive §4.13).** Gates are technical, not just done/not-done: each carries an owner and completion evidence. Items 1–6 must be locked before item 7 (the vertical slice) starts.

| # | Gate | Owner | Completion evidence | Status |
|---|---|---|---|---|
| 1 | Rotate/remove tracked Lovable credentials | You | Provider-console rotation, `.env` removed from index, secret scan clean (`env-rotation-checklist.md` Phases A–E) | ⏳ Blocked (needs your consoles) |
| 2 | Create migration branch + Streamlit freeze | You | `feat/react-fastapi-migration` exists; freeze policy recorded (`branch-and-freeze-policy.md`) | ⏳ Blocked (one command) |
| 3 | Publish canonical API decision record | ✅ Done (2026-08-05) | `/api/v1`, `/healthz`, `{ dataset }`, cookie auth transport, chat format, upload limit — in F3/F4/plan top sections | ✅ Done |
| 4 | Lock upload policy | ✅ Done (2026-08-05) | **25 MB** direct cap + **100 MB** Drive cap with safeguards + rejection messages defined (Phase 1) | ✅ Locked (25-vs-32 final confirmation optional) |
| 5 | Define state-placement + store interfaces | Implementation agent | `SessionStore`/`DatasetStore` contracts; local in-memory implementation tested (Phase 1) | ⏳ Open (Phase 1 work) |
| 6 | Write retention + AI-data-boundary policy | You | `data-retention-policy.md` exists; ⚠️ defaults (dataset TTL, clear-data behavior, Gemini filtering) confirmed | 🔵 Doc done; decisions pending your confirmation |
| 7 | Build upload vertical slice | Implementation agent | Upload → preview → quality → clear + contract tests (Phase 1) | ⏳ Blocked by 1–2, 5–6 |
| 8 | Explicitly defer GA4, Drive, chat, exports | You | Backlog/phase boundaries maintained (this plan's Phases 3/5 scope) | 🟢 Active (by plan) |

---

## 5. Phase 1 — API contract & FastAPI skeleton (Week 1)

**Inputs:** `phase-1-api-react-callback-tests-implementation.md` (F4 — full packet) · plan Phase 1 + amendments · archive §3.5 (wire format), §3.9 (ai pin), §4.2 (canonical shapes), §4.11 (size policy).

**Goal:** stand up `api/` (FastAPI) with the JSON contract between React and Python, using F4's vertical slice as the code-level reference.

**Locked decisions (do not re-litigate):**
- **Canonical contract shapes (Part 4 §4.2):** `GET /healthz` (not `/health`) · `POST /api/ga4/connect` returns `{ authorization_url }` (snake_case at the boundary) · upload returns `{ dataset }` wrapper (plus `{ dataset, rows }` where F4 specifies) · `credentials: "include"` in the client · `setSourceFromApi` in the store · API versioned **`/api/v1`**.
- **Chat wire format — decide at contract time and record in OpenAPI:** plain SSE (`text/event-stream`, `data: <chunk>\n\n`) vs AI SDK data-stream (`toDataStreamResponse()`/`toUIMessageStreamResponse()`). The captured repo pins **`ai@^7.0.48`** and its chat route uses `streamText(...).toTextStreamResponse()` (plain text) — F3's store reader consumes plain text, so **plain SSE is the default unless the team chooses `useChat`** (which requires the SDK format). (Plan Phase 1; archive §3.5, §3.10 item 1.)
- **Upload policy (locked 2026-08-05, refined per review):** direct browser uploads are limited to **25 MB** (`MAX_BROWSER_UPLOAD_BYTES = 25 MB` — margin below Cloud Run's 32 MiB HTTP/1 boundary); Drive/server-side imports may ingest up to **100 MB** (`MAX_INGEST_BYTES = 100 MB`, matching `utils/drive_client.py`'s guard) **subject to memory, MIME, row-count, and decompression safeguards** — a streaming download path, decompression/row-count limits, cleanup behavior, and sufficient Cloud Run memory (a 100 MB compressed XLSX can expand dramatically in memory). Signed Cloud Storage upload is deferred until real file-size evidence requires it; end-to-end HTTP/2 is not selected merely to preserve 100 MB browser uploads. (Archive §4.11–4.13.)
- **Dependency floors:** `pandas>=2.3.3` (first cp314 wheels), `pydantic>=2.12`, `fastapi`, `uvicorn`, `python-multipart`, `google-genai` (see Phase 3). (Archive §3.10 item 6.)
- **Session/data architecture (state placement, not a single store — locked 2026-08-05):** `SessionStore`/`DatasetStore` **interfaces** defined now with in-memory implementations for local dev; shared ephemeral storage for session/OAuth state and object storage for raw uploads come before Phase 5. State is placed **by type**: browser session ID → HttpOnly cookie; OAuth state/PKCE verifier → ephemeral store with short TTL (Redis/Valkey); active dataset metadata/filters/metrics → shared store; raw uploads → object storage (Cloud Storage); parsed dataframes → memory cache (eviction-tolerant); OAuth refresh tokens → encrypted durable store; chat usage/audit → Postgres later. No provider token or raw dataset is stored in the browser. (Archive §4.13.)
- **Blocking work:** keep CPU-heavy routes synchronous or run blocking work in a controlled thread pool (never inline in `async def` hot paths — it stalls SSE/chat); hard-cap rows, columns, and **decompressed** size; reject password-protected spreadsheets, suspicious MIME mismatches, and compression bombs; stream or temp-store exports instead of buffering in memory.
- **OAuth production-real from the start:** persist `state`, PKCE verifier, creation time, and intended post-auth return path in the shared session with a short expiry and one-time use; maintain separate redirect URIs for local/staging/production from an allowed-host config — never derive the redirect host loosely from request headers.
- **Data retention (policy before API):** adopt `migration/data-retention-policy.md` — upload retention window, raw-frame persistence, session expiry, Clear Data semantics, export-logging retention, Gemini prompt field allowlist, identifier removal/aggregation before AI calls.

**Tasks (F4 §1–§12 is the implementation packet; this is the task skeleton):**
- [ ] Create `api/` per F4's target layout: `config.py` (env, CORS for `http://localhost:5173`), `dependencies.py` (session), `schemas.py`, `services/dataset_service.py`, `routes/health.py`, `routes/upload.py`, `main.py`.
- [ ] Implement the **vertical slice**: `POST /api/upload` (multipart, 100 MB cap) → `GET /api/data/context` + `GET /api/data/preview` → `GET /api/data/quality`.
- [ ] Session: define `SessionStore`/`DatasetStore` interfaces; in-memory implementation keyed by opaque `HttpOnly` cookie for dev; **shared ephemeral session/OAuth storage + object storage for raw uploads proven before Phase 5** (state placement — see cross-cutting A).
- [ ] GA4 OAuth **adapters only** in Phase 1 (start/callback scaffolding per F4 §8) — full flow is Phase 5. PKCE (S256) is required even in the adapter (Plan Phase 5 amendment; archive §3.2).
- [ ] MSW test setup in the frontend *if* the React shell exists yet — otherwise defer to Phase 4 (F4 §12).
- [ ] Add `requirements/base.txt` entries + `run_api.py` or `make run-api` (uvicorn).

**Exit criteria (DoD):** app runs on `:8000`; `/healthz` passes; upload→preview→quality works end-to-end via `httpx` contract tests; 100 MB cap enforced; baseline 742 pytest still green.

**Verification (planned, not run):** `pytest tests/api/` · `curl localhost:8000/healthz` · full `pytest` suite for regression.

---

## 6. Phase 2 — Decouple `utils/` from Streamlit (Week 2)

**Inputs:** plan Phase 2 · `session-state-inventory.md` (which `st.session_state` reads move where) · `test-layer-inventory.md` §1 (452 utils-facing tests must stay green).

**Goal:** make `utils/` importable by FastAPI while Streamlit keeps working.

**Tasks:**
- [ ] The seven Streamlit-coupled utils: `data_loader` (drop `@st.cache_data`), `error_boundary` (keep Streamlit-only), `forecasting` (drop `st.cache`), `gemini_client` (drop Streamlit rate-limit display; keep core calls), `prompt_templates` (pass context as args, no `st.session_state` reads), `session` (replaced by FastAPI session — see cross-cutting A), `styles` (Streamlit-only, stays).
- [ ] Confirm remaining utils are pure: `data_context`, `ga4_client`, `drive_client`, `charts`, `funnels`, `quality`, `exports`, `commands`, `sanitize`.
- [ ] Every removed `st.session_state` read gets its replacement from `session-state-inventory.md` (44 keys, 6 groups).

**Exit criteria (DoD):** `utils/` Streamlit-free or minimally coupled; FastAPI imports any util without touching `st`; **all 742 tests still pass** (utils tests prove behavior preserved).

**Verification (planned):** full `pytest` · `python -c "import utils.gemini_client"` outside a Streamlit runtime.

---

## 7. Phase 3 — Wire FastAPI to real utils (Week 3)

**Inputs:** plan Phase 3 + amendments · archive §3.4 (funnel nuance), §3.9 (Gemini SDK), §3.10 item 7 (model hygiene).

**Goal:** replace mock/skeleton responses with real `utils/` calls.

**Tasks:**
- [ ] `POST /api/upload` → `data_loader` · preview → `data_context` · quality → `quality` · charts → `charts` · summary → `gemini_client` + `prompt_templates` · forecast → `forecasting` · funnel → `funnels` · export → `report_exporter`.
- [ ] **Gemini:** use the current `google-genai` SDK (`client.models.generate_content_stream(...)`); record `thoughts_token_count` in the server-side usage ledger (the app already tracks `total_thought_tokens` — keep that observability). (Archive §3.9 item 4.)
- [ ] **Model hygiene:** `gemini-2.0-flash` is shut down and `gemini-1.5-flash` deprecated — prune `utils/gemini_client.py`'s `AVAILABLE_MODELS`; keep `gemini-2.5-flash` (1M context) as default. (Archive §3.10 item 7.)
- [ ] **Funnel nuance:** template funnels may be partially available via GA4's `runFunnelReport`; scope `GET /api/analysis/funnel` to template funnels and re-verify the ROADMAP funnel rows at implementation. (Archive §3.4, §3.8 item 4.)
- [ ] Chat streaming per the Phase 1 wire-format decision; `StreamingResponse` with disconnect handling (Starlette cancels the async generator on client disconnect — `CancelledError`). (Archive §3.10 item 8.)
- [ ] Contract tests for every endpoint (pytest + httpx). All endpoints versioned under `/api/v1`.

**Exit criteria (DoD):** all read-only endpoints return real data; contract tests cover every endpoint; error taxonomy (upload limits, bad types, auth) preserved from the Streamlit layer.

---

## 8. Phase 4 — Port React UI into `frontend/` (Week 4)

**Inputs:** `freebuff-prompt-wire-react-store.md` (F3 — 13 steps) · plan Phase 4 + amendments · archive §3.6 (validateSearch), §3.9 items 3/5 (pins, bun), §3.10 items 2/5 (strip list, Recharts) · `whisperer-30-reference/` (captured source, incl. the explorer-store drift cross-check in `WHISPERER-30-REFERENCE.md`).

**Goal:** copy the whisperer-30 components in, strip the Start/Lovable/Nitro plumbing, and swap mock store calls for real API calls.

**Tasks:**
- [ ] Copy `src/` → `frontend/` (from the frozen capture, not a live clone, until the frontend build is reproducible).
- [ ] **Strip list (round-3 verified):** remove `@lovable.dev/vite-tanstack-config`, `@tanstack/react-start`, `nitro`, `src/server.ts`, `src/start.ts`, `src/routes/api/*` (Start/Nitro server routes); replace the plugin with `@vitejs/plugin-react` + `@tanstack/router-plugin/vite`; file-based `createFileRoute` routing is identical without Start. (Archive §3.10 item 2.)
- [ ] **Package manager decision (open):** bun (whisperer-30's) vs npm (Drive Picker's + repo convention). Both are CI-supported (`oven-sh/setup-bun@v2` on Actions; install script on Cloud Build) — unconstrained by CI, so pick on repo consistency. (Archive §3.9 item 5; §3.10 item 6.)
- [ ] **Recharts × React 19:** `recharts@^2.15.4` doesn't declare React 19 peer deps — try plain install first; on peer errors use `overrides` or move to recharts 3.x. (Archive §3.10 item 5.)
- [ ] **F3 store wiring (13 steps):** remove mock imports → API base (relative `/api`) → real `loadData()` upload → GA4 flow → Drive flow → `streamAi` → SSE chat per Phase 1 format → quality/charts/forecast/funnel fetchers → export → `ExplorerValue` interface (**union**, it omits `addFilter`/`sendMessage`/`clearChat` — drift cross-check) → delete mock files → `api-types.ts` → `.env` files. (F3 §1–13; reference drift section.)
- [ ] **Chat route:** remove the Lovable AI gateway path; AI routing stays under Python/FastAPI control (Batch 3; `utils/prompt_templates.py` is the system prompt source — never the whisperer's hardcoded BrainGuide prompt).
- [ ] **Routing:** TanStack Router `validateSearch` + `Route.useSearch()` for typed search params (GA4 callback `status`/`reason`), never raw `window.location.search`. (Archive §3.6.)
- [ ] MSW test setup: `setupServer` from `msw/node`, `onUnhandledRequest: "error"`; mocks (`mock-ga4.ts`, `mock-braintree.ts`) become **test fixtures only**; streaming chat tests use `HttpResponse` + `ReadableStream` body with SSE headers (jsdom has no `EventSource` — test the `getReader()` path). (F4 §12; archive §3.10 item 4.)
- [ ] **Chat reconnect behavior (before any deploy):** the client retains the user message, renders partial output safely, and allows retry without creating duplicate assistant messages. Treat Cloud Run's configurable request timeout (default 300s, up to 3600s) as a ceiling, not a guarantee of one uninterrupted stream. (Archive §3.10; §4.12.)
- [ ] `frontend/README.md` + gitignore for `node_modules`, `dist`.

**Exit criteria (DoD):** `npm run dev` (or `bun dev`) + `uvicorn` produce a usable app at `localhost:5173`; no references to `mock-ga4.ts`/`mock-braintree.ts` in runtime code; store talks to FastAPI with `credentials: "include"`.

---

## 9. Phase 5 — GA4 OAuth + Drive Picker (Week 5)

**Inputs:** plan Phase 5 + amendments (items 1–7) · archive §3.2 (PKCE), §3.3 (Picker), §3.4 (GA4), §3.6 (validateSearch) · F4 §8 (OAuth adapters) · `utils/ga4_client.py`, `utils/drive_client.py`, `components/drive_picker_component_frontend/`.

**Goal:** the two hardest integrations, preserving the existing error taxonomy.

**Tasks — GA4 OAuth:**
- [ ] `POST /api/ga4/connect` → OAuth URL from `ga4_client.py`, with **PKCE** (S256 `code_verifier`/`code_challenge`; store verifier server-side). (Plan amendment 1; archive §3.2.)
- [ ] `GET /api/ga4/callback` → validate `state`, exchange code server-side, store credentials server-side, redirect to React callback page with only `status=success` / safe error reason. **Provider tokens never reach React.** (F4 §8; archive §1.13.)
- [ ] React callback route `/auth/ga4/callback` with `validateSearch` schema; on validation failure the router sets `error.routerCode === "VALIDATE_SEARCH"` and renders the route's `errorComponent` (verified against `@tanstack/react-router@1.170.20`). (Plan amendment 6; archive §3.6.)
- [ ] `POST /api/ga4/pull` → paginate (`limit`/`offset`, 10k-row pages, ≤9 dimensions, max 250k rows/request) and throttle for the **10 concurrent requests/property (Standard; 50 for 360)** quota; enable `returnPropertyQuota: true` for observability; account for token budgets (200k/day + 40k/hr per property) and the 120 thresholded-requests/hr cap. (Plan amendment 7; archive §3.9, §3.10.)
- [ ] Align pulled metrics with `plans/ga4-measurement-contract.md` via `contract_row`/`validation_status` provenance; aggregate-only rows stay `unavailable`. (Archive §4.11.)

**Tasks — Drive Picker:**
- [ ] Port the picker as a **native React component** (preserve size safeguards + error taxonomy; not an embedded Streamlit component).
- [ ] `POST /api/drive/picker-token` → returns the OAuth token **and the project number** (`setAppId`); document Cloud Resource Manager API enablement; restrict the API key to HTTP referrers. (Plan amendment 2; archive §3.3.)
- [ ] `POST /api/drive/download` → `drive_client.py` download logic; enforce `MAX_INGEST_BYTES = 100 MB` + MIME allowlist + typed errors.
- [ ] E2E: GA4 connect→pull and Drive pick→download→preview flows in Playwright.

**Exit criteria (DoD):** both flows work in React with the server-session model; errors (size, auth, bad type) surface with the established taxonomy; no token leakage (credential guard extends to FastAPI env vars).

---

## 10. Phase 6 — Cutover, hosting, retire Streamlit (Week 6)

**Inputs:** plan Phase 6 + amendments · `dockerfile-pattern.md` (full) · `test-layer-inventory.md` §4 (retirement checklist) · archive §3.10 item 3 (Cloud Run), §3.11 (Vercel eval).

**Goal:** one product at one URL on container hosting; Streamlit retired; docs updated.

**Tasks:**
- [ ] **Hosting: Cloud Run (recommended).** The repo already deploys via `cloudbuild.yaml` → docker build → Artifact Registry → `gcloud run deploy`. Bind `$PORT` (8080); raise the request timeout for SSE (default 300s, max 3600s) or heartbeat; treat session affinity as best-effort (design chat reconnect); enable HTTP/2 (`h2c`); set the OAuth redirect to the explicit public HTTPS URL (Cloud Run proxies `X-Forwarded-Proto`). (Archive §3.10 item 3.)
- [ ] **Single-origin Dockerfile** per `dockerfile-pattern.md`: stage 1 Vite build → stage 2 Python runtime serving static SPA + `/assets` mount + SPA fallback guarded to non-API paths. Vercel is **ruled out for the backend** (≈4.5 MB serverless body cap vs 100 MB ingestion; duration limits vs SSE; stateless vs sessions) — SPA-on-Vercel + API-elsewhere is rejected (split origins). (Archive §3.11.)
- [ ] **Feature-parity checklist** (12 features: upload, GA4, Drive, preview, quality, summary, charts, forecast & funnel, chat, export, Learn, onboarding).
- [ ] **Retire Streamlit tests** per `test-layer-inventory.md`: 290 Streamlit-layer tests rewritten as API-contract tests or retired; 452 utils tests stay; 40 Playwright tests become the new E2E baseline.
- [ ] Update `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md` (v0.4.0 entry); archive `insights-whisperer-30` repo with a fold-in note.
- [ ] Update **both** CI pipelines: `.github/workflows/test.yml` (pytest + frontend build + Playwright) and `cloudbuild.yaml` (container build/deploy). (Archive §1.13.)

**Exit criteria (DoD):** single production URL serves React + FastAPI; all 12 parity items verified; no Streamlit-dependent test failures; Streamlit marked retired.

**Verification (planned):** `scripts/smoke_test.sh` reworked for the new stack (boot both services, `/healthz`, upload CSV, chat stream) · Playwright parity suite · Lighthouse + bundle-size checks (plan Success Metrics table).

---

## 11. Cross-cutting workstreams

These run alongside the phases and are owned by specific source docs.

### A. State migration — `session-state-inventory.md`
All 44 keys (6 groups) get a server-side replacement: dataset/analysis → `api/services/dataset_service.py` session object · GA4 credentials → server session (never React) · Drive Picker transient state → React dialog state + server import-in-progress flag · chat/AI counters → server-side usage ledger · theme preference → localStorage (safe — preference, not data) · test-only keys → dropped. **Gate rule:** during the freeze, any new `st.session_state` key requires a documented replacement (Phase 0).

**State placement (locked 2026-08-05 — refined from review; archive §4.13):** state is placed **by type**, not in a single store:

| State | Recommended home | Why |
|---|---|---|
| Browser session ID | Secure `HttpOnly` cookie | Opaque identifier only; no tokens or raw data |
| OAuth state / PKCE verifier | Ephemeral store, short TTL (Redis/Valkey) | Security-sensitive, one-time-use state |
| Active dataset metadata, filters, metrics | Shared store (Redis/Valkey or Postgres JSON) | Small structured data; needs shared access across instances |
| Raw upload / large source file | Object storage (Cloud Storage) | Never place 32–100 MB datasets in cookies, Redis, or Postgres rows |
| Parsed dataframe | Memory cache; recompute on eviction | Large and expensive; must tolerate eviction |
| OAuth refresh tokens | Encrypted durable store | Must survive session expiry/restarts if persistent reconnect is required |
| Chat usage/audit metadata | Postgres (later) | Durable reporting, quotas, debugging trail |

Long-term shape: **Redis/Valkey for ephemeral session + OAuth state · Cloud Storage for uploaded files · Postgres only for durable user/account, audit, report, or usage records.**

### B. Contract discipline — `plans/ga4-measurement-contract.md` + archive §4.2/§4.11
Canonical shapes adopted in Phase 1; typed client generated/validated from OpenAPI; snake_case at the API boundary, camelCase only via the client; `/api/v1` from day one (evidence connector evolves safely). Measurement-contract mapping recorded in archive §4.11.

### C. Test strategy — `test-layer-inventory.md`
**742 = 452 utils-facing (61%, transfer as-is) + 290 Streamlit-layer (39%, rewrite/retire) + 40 Playwright E2E.** Per-file transfer paths in the inventory; four-layer matrix in archive §1.13 item 5. DoD per phase includes its test gate.

### D. Security & credentials — `env-rotation-checklist.md` + existing credential guard
`.env` rotation (Phase 0) · credential guard patterns extended to FastAPI env vars · `.env.example` updated with all new API env vars (session secret, CORS origins) · `__Host-` cookie prefix (needs `Secure` + `Path=/` + no `Domain`) · never log keys or echo tokens in responses.

### E. CI/CD & deployment — `cloudbuild.yaml` + `.github/workflows/test.yml` + `dockerfile-pattern.md`
Both pipelines updated in Phase 6 · frontend build gate (npm/bun ci → typecheck → build) added alongside pytest · container deployment to Cloud Run · smoke script reworked for the new stack.

### F. Data retention & AI data boundary — `data-retention-policy.md`
Written **before the API exists** (Phase 0/1): upload retention window, whether raw dataframes persist or are session-only, session expiry, exactly what "Clear Data" deletes, what export logging retains, which fields are allowed in Gemini prompts, and which identifiers must be removed/aggregated before an AI call. "Server-owned" is better than browser-owned, but it is not automatically privacy-safe.

---

## 12. File organization (target layout)

The migration builds toward this single-repo layout. Streamlit pieces are marked *(retired Phase 6)*.

```
insights-explorer/
├── api/                          # FastAPI backend (Phase 1)
│   ├── main.py                   # app, CORS, router includes, SPA fallback (Phase 6)
│   ├── config.py                 # env: session secret, CORS origins, MAX_INGEST_BYTES
│   ├── dependencies.py           # server-owned session (cookie → session object)
│   ├── stores/                  # SessionStore / DatasetStore interfaces + impl (Phase 1)
│   ├── schemas.py                # pydantic models at the API boundary
│   ├── serializers.py            # domain models → JSON (one boundary)
│   ├── services/
│   │   ├── dataset_service.py    # DataContext lifecycle, upload ingestion
│   │   ├── ga4_service.py        # OAuth (PKCE) + pull + quota throttle
│   │   ├── drive_service.py      # picker token + download (size/MIME guards)
│   │   └── chat_service.py       # Gemini streaming + usage ledger
│   └── routes/                   # health, upload, data, chat, analysis,
│                                 # export, ga4, drive — all under /api/v1
├── frontend/                     # React app (Phase 4, from whisperer-30 capture)
│   ├── src/
│   │   ├── components/           # explorer/* + ui/* (shadcn)
│   │   ├── lib/
│   │   │   ├── explorer-store.tsx   # context provider (F3 target)
│   │   │   ├── api.ts               # typed client (snake→camel translation)
│   │   │   └── api-types.ts         # OpenAPI-derived types
│   │   ├── routes/               # file-based routing; /auth/ga4/callback (Phase 5)
│   │   └── test/                 # MSW handlers, fixtures (mock-ga4/braintree → fixtures)
│   ├── package.json              # ai@^7.0.48, react ^19.2, recharts (see Recharts note)
│   └── vite.config.ts            # @vitejs/plugin-react + @tanstack/router-plugin
├── utils/                        # framework-neutral (Phase 2) — unchanged surface
├── components/                   # Streamlit components (retired Phase 6)
├── pages/                        # Streamlit pages (retired Phase 6)
├── app.py                        # Streamlit entry (retired Phase 6)
├── tests/
│   ├── api/                      # FastAPI contract tests (new)
│   ├── e2e/                      # Playwright (40 → new baseline)
│   └── …                          # existing 742 preserved; 290 UI tests retired
├── migration/                    # this planning package (source of truth during work)
├── Dockerfile                    # multi-stage (Phase 6; dockerfile-pattern.md)
├── cloudbuild.yaml               # updated (Phase 6)
├── .github/workflows/test.yml    # updated (Phase 6)
├── .env.example                  # updated with API env vars
└── …
```

**Deliberate exclusions from the target tree:** the Lovable AI gateway, `mock-ga4.ts`/`mock-braintree.ts` (→ test fixtures), the whisperer's hardcoded BrainGuide prompt (→ `utils/prompt_templates.py`), Nitro/Start plumbing.

---

## 13. Open decisions (each blocks a specific phase gate)

| # | Decision | Blocks | Current recommendation |
|---|---|---|---|
| 1 | Chat wire format (plain SSE vs AI SDK data-stream) | Phases 3–4 | Plain SSE (matches `ai@^7.0.48` + `toTextStreamResponse()` + F3 reader) unless `useChat` is chosen |
| 2 | Durable store for refresh tokens / usage metadata (Postgres vs other) | Only if persistent reconnect or multi-user/audit needs appear | **Architecture locked: state placement** (cookie / ephemeral Redis-Valkey / shared store / Cloud Storage / memory cache / encrypted durable / Postgres-later); durable DB provider choice postponed |
| 3 | Package manager (bun vs npm) | Phase 4 | CI-unconstrained; pick on repo consistency |
| 4 | Hosting platform | Phase 6 | **Cloud Run** (GCP investment, existing `cloudbuild.yaml`) — Railway/Render equivalent |
| 5 | Recharts 2.15.4 vs 3.x | Phase 4 | Try 2.15.4 first; `overrides` or 3.x on peer errors |
| 6 | `frontend/` vs `api/` layout (siblings) | Phase 1 | Siblings (per plan Open Questions #5; F4 §1 target layout) |
| 7 | GA4 dim/metric limits (9 dims / 10 metrics, 7 for funnel) | Phase 5 | Reported, not live-verified (limits page 404s) — re-verify at implementation |
| 8 | Browser-upload cap final value (25 vs 32 MB) | Phase 1 (trivial flip) | **Locked: 25 MB** (margin below Cloud Run's 32 MiB HTTP/1 boundary) + 100 MB Drive cap with safeguards; HTTP/2 rejected for this purpose; signed Cloud Storage deferred |

---

## 14. Definition of Done (overall)

- [ ] Phase 0–6 exit criteria met (each phase's DoD above).
- [ ] Feature parity: all 12 items on the parity checklist work in the new UI.
- [ ] Test gates: utils tests stay green (452) · API contract tests cover every endpoint · React tests via MSW · Playwright E2E baseline (40) green.
- [ ] Single-origin deployment live on Cloud Run; Streamlit retired from the default path.
- [ ] Credential hygiene: no live credentials in the repo, in history, or in captured files; `check_credentials.py` extended to API env vars.
- [ ] Docs updated: README, ARCHITECTURE, CHANGELOG (v0.4.0), RELEASE_CHECKLIST; `migration/` status flipped to reflect completion.
- [ ] `insights-whisperer-30` archived with a fold-in note.
- [ ] **Three non-negotiable release gates (master-plan revision 2026-08-05):** (1) **No-regression** — transferable Python behavior tests stay green (452 utils tests); (2) **Contract** — FastAPI schema/error/session/OAuth-state tests run against the OpenAPI contract; (3) **User-flow** — Playwright covers upload → preview → clear, GA4 failure/success, Drive failure/success, chat reconnect/streaming, export.
- [ ] Chat reconnect verified (message retained, partial output safe, retry without duplicate assistant messages).

---

## 15. Risk register (consolidated from the plan + research rounds)

| Risk | Severity | Mitigation (where) |
|---|---|---|
| OAuth redirect breaks in the new stack | High | FastAPI-owned callback + PKCE + exact `redirect_uri` (Phase 5; archive §3.2) |
| Chat wire-format mismatch (SSE vs SDK stream) | High | Decide in Phase 1, record in OpenAPI, implement identically in 3/4 (§3.5) |
| Streamlit-layer test retirement erodes coverage | High | Test-layer inventory (452 keep / 290 rewrite) + per-phase test gates |
| Whisperer-30 tracked `.env` already exposed | High | Phase 0 rotation gate before any copy-in (`env-rotation-checklist.md`) |
| Start/Nitro plumbing silently eats time in the port | Medium | Round-3 strip list, documented (Phase 4; §3.10 item 2) |
| Recharts × React 19 peer-dep breakage | Medium | Try/override/upgrade path (Phase 4; §3.10 item 5) |
| GA4 10-concurrent quota throttling undercounts | Medium | Live numbers + `returnPropertyQuota` observability (Phase 5; §3.9) |
| Hosting split origins break session/OAuth/SSE | Medium | Single-origin Docker + Cloud Run (Phase 6; §3.1, §3.10–3.11) |
| Two UIs alive = double maintenance | Medium | Feature freeze + fix-forward (Phase 0; branch policy) |
| Gemini model drift (2.0-flash shut down) | Low | Model hygiene pass in Phase 3 (§3.10 item 7) |
| Cloud Run 32 MiB request cap (HTTP/1) vs 100 MB ingestion | High | 25 MB browser cap; HTTP/2 or signed uploads only if real file evidence justifies (Phase 0/1; §4.12–4.13) |
| Sync/CPU-heavy work blocks the FastAPI event loop (SSE/chat stalls) | Medium | Sync routes or controlled thread pool; hard caps on rows/columns/decompressed size; streamed exports (Phase 1) |
| Session affinity ≠ consistency across Cloud Run instances (data loss) | Medium | Shared ephemeral session/OAuth store + object storage for raw uploads proven before Phase 5 (Phase 1) |
| Retention/privacy exposure (client analytics + health/equity context) | Medium | `data-retention-policy.md` + Gemini data-boundary rules before the API exists (Phase 1) |

---

## 16. Source map (doc → phase feed)

| Source doc | Feeds |
|---|---|
| `insights-explorer-migration-ingest.md` | All phases (evidence + research + reconciliation) |
| `insights-explorer-migration-plan.md` | Phase shapes 1–6, contract draft, metrics, risks |
| `phase-1-api-react-callback-tests-implementation.md` (F4) | Phase 1 (packet), Phase 5 (OAuth adapters), MSW tests |
| `freebuff-prompt-wire-react-store.md` (F3) | Phase 4 (13-step store wiring) |
| `env-rotation-checklist.md` | Phase 0, cross-cutting D |
| `branch-and-freeze-policy.md` | Phase 0 |
| `session-state-inventory.md` | Phases 2/4, cross-cutting A |
| `test-layer-inventory.md` | Phases 2/6, cross-cutting C |
| `data-retention-policy.md` | Phase 1 (policy before API), cross-cutting F |
| `dockerfile-pattern.md` | Phase 6, cross-cutting E |
| `glm-5-2-vs-perplexity-migration-comparison.md` | Audit lens (no phase feed) |
| `whisperer-30-reference/` | Phases 0 (rotation evidence), 4 (source capture), 5 (picker port) |

---

*This master plan was synthesized 2026-08-05 from the full `migration/` package and revised the same day from review feedback (first pass: session store + upload architecture moved to Phase 0/1, canonical API decisions record, data-retention policy, three release gates; second pass: 25 MB upload cap, state-placement architecture, 8-gate priority checklist). It is planning-only: no migration product code was written and no commands executed. Each phase begins only on explicit approval, and per the addenda system, any later corrections append as dated addenda rather than rewriting this document.*
