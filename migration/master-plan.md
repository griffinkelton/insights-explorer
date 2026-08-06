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
| **Raw material + verification** (source of truth) | `archive/insights-explorer-migration-ingest.md` (archive, Parts 1–4) |
| **The 6-phase roadmap** (the phase *shapes* below come from here) | `archive/insights-explorer-migration-plan.md` |
| **Phase 1 backend implementation packet** (code-level detail) | `specs/phase-1-api-react-callback-tests-implementation.md` (F4) |
| **Frontend store wiring prompt** (13-step change list) | `specs/freebuff-prompt-wire-react-store.md` (F3) |
| **Security gate before any code copy-in** | `policies/env-rotation-checklist.md` |
| **Process policy (branch + freeze)** | `policies/branch-and-freeze-policy.md` |
| **State migration record** (44 keys) | `policies/session-state-inventory.md` |
| **Which tests transfer** (742 = 452 + 290 + 40) | `policies/test-layer-inventory.md` |
| **Hosting pattern** (single-origin Docker) | `policies/dockerfile-pattern.md` |
| **Independent audit lens** | `archive/glm-5-2-vs-perplexity-migration-comparison.md` |
| **Source UI repo frozen capture** (18 files) | `whisperer-30-reference/` |
| **Retention & AI data-boundary policy** (new) | `policies/data-retention-policy.md` |

The master plan adds what none of the source docs have: **execution order, inter-phase dependencies, a single file-organization target, cross-cutting workstreams, and one Definition of Done**.

---

**Planned workstreams vs migration scope (2026-08-06; archive §4.21) — three-way document status:**

| Document | Status | Meaning for the migration |
|---|---|---|
| `plans/ga4-measurement-contract.md` | ✅ **In-migration — canonical** | Semantic source of truth (cross-cutting B); Phase 3 funnel + Phase 5 GA4 alignment build against it; metric-status policy lives here |
| `plans/🔵 ga4-insights-sketch.md` | 🔵 **Deferred workstream** | Design doc for the GA4 insights engine (future); the prototype's `insights/engine.ts` + `InsightCandidates` are mock prototypes of it — quarantined, not ported in the first slice (gate 8) |
| `plans/🔵 evidence-connector-design.md` | 🔵 **Deferred workstream** | 44 KB design for the evidence connector (future); the three Lovable panels are mock prototypes of it — quarantined, out of the first slice (gate 8); the migration only accommodates it via `/api/v1` + quarantine layout |

---

## 2. Guiding principles (locked decisions from the archive)

1. **`insights-explorer` is the system of record.** whisperer-30's React components are adopted wholesale as the new frontend; its mocks/gateway/prompts never become production logic. (Archive §1.1; plan "Decision".)
2. **Server-owned session model.** Browser holds only an opaque `HttpOnly` secure session cookie. Dataset reference, OAuth credentials, filter/metric/chat state live server-side. Raw data and provider tokens never reach localStorage, URLs, logs, or client analytics. (Archive §1.13 / Batch 3, item 3; `policies/session-state-inventory.md` §7.)
3. **Single-origin deployment.** Built React SPA served statically behind the FastAPI container — required for cookies, OAuth callbacks, CORS, and SSE. No split origins. (Archive §3.1, §3.10 item 3, §3.11; `policies/dockerfile-pattern.md`.)
4. **Contract discipline.** `plans/ga4-measurement-contract.md` stays canonical; Python domain models serialize at one API boundary; typed React client generated/validated from OpenAPI; API versioned `/api/v1`; naming normalized once (API emits snake_case, client translates). (Archive §1.13 item 4; §4.2.)
5. **Test by behavior, not implementation.** Four-layer matrix: Python unit · FastAPI contract · React component (MSW) · Playwright E2E. Mocks become test fixtures only. (Archive §1.13 item 5; `policies/test-layer-inventory.md`.)
6. **Tight Phase 1 scope.** One vertical slice first: Upload CSV → validate via existing Python logic → server session → React preview/quality → clear-data → regression tests. Then GA4 → Drive → AI streaming → advanced analysis. (Archive §1.13 item 7.)
7. **Incremental PRs per deliverable; additive documentation.** Original docs preserved; decisions appended as dated addenda.
8. **whisperer-30 stays a living design reference until cutover.** (Archive §1.13 item 2.)
9. **Local-first deployment posture (2026-08-06):** the product runs **locally first**; a hosted beta comes later. In-memory `SessionStore`/`DatasetStore` implementations remain acceptable **through Phase 5** for local use. The shared ephemeral OAuth/session store, object storage, and Cloud Run are **beta/hosting-time work** — proven before the hosted beta, not before Phase 5 code.
10. **External API surface is unchanged by the migration.** The app connects only to: Google OAuth 2.0, Google Analytics Data API v1, Google Drive (download + metadata), the Google Picker API (frontend), and the Gemini API. Cloud Run, Redis/Valkey, Cloud Storage, and Postgres are infrastructure, not app-facing APIs; the only enablement item is the Cloud Resource Manager API (Picker project number, Phase 5). **Drive browse (2026-08-06):** the new Lovable slide-out browse UX (search + breadcrumbs + metadata) uses the *same* Google Drive metadata API, called server-side via FastAPI (`GET /api/v1/drive/list`) — the Google Picker iframe becomes an optional alternative, not a required API (see §9, Phase 5 browse-UX decision).

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

**Phase 0/1 gates — locked before product code (master-plan revision 2026-08-05):** (1) browser-upload architecture decided (**25 MB direct browser cap**); (2) **state-placement architecture** locked — `SessionStore`/`DatasetStore` interfaces defined; a **shared ephemeral OAuth/session store is proven before the hosted beta** (local in-memory stores are acceptable through Phase 5 — local-first posture), and **object storage is proven only if the signed-upload architecture is chosen**; (3) canonical API decisions record published to all implementation-facing docs with old paths marked superseded; (4) data-retention + AI data-boundary policy written. Items 1–6 (incl. gate 5a) of the 8-gate priority checklist (§4) must be locked before the vertical slice starts. **Entry gates all closed as of 2026-08-06:** 1 (credentials) · 2 (branch + freeze) · 3 (API record) · 4 (25 MB policy) · 5a (state contracts) · 6 (retention approval) — **gate 7 (vertical slice) is unblocked** (§4).

---

## 4. Phase 0 — Security gate & process setup (prereq, no product code)

**Inputs:** `policies/env-rotation-checklist.md` (full) · `policies/branch-and-freeze-policy.md` (full) · archive §1.13 / Batch 3.

**Goal:** make it safe to copy whisperer-30 code in, and freeze Streamlit feature work so the migration surface stops growing.

**Tasks:**
- [ ] **Rotate/revoke credentials (manual — provider consoles).** The whisperer-30 repo tracks a real `.env` (62 B, commit `9059739`, no `.env.example`, no gitignore rule). Treat as potentially exposed: inspect git history → identify real vs placeholder per provider (Google Cloud / Gemini / Lovable / other) → **rotate every real credential** → `git rm --cached .env` → add safe `.env.example` → gitignore rule. History scrub (`git filter-repo`) is optional but documented. *Follow `policies/env-rotation-checklist.md` Phases A–E.*
- [ ] **Cut `feat/react-fastapi-migration` branch.** `main` = production/security fixes only; all migration work lands on the branch with the fix-forward rule. Feature freeze applies to broad Streamlit work (test: any new `st.session_state` key during the freeze needs a documented replacement — see `policies/session-state-inventory.md`). Lift criteria in `policies/branch-and-freeze-policy.md` §5.
- [ ] **Inventory the 44 `st.session_state` keys** (done — `policies/session-state-inventory.md`). Adopt it as the working checklist for Phases 2/4.
- [ ] **Confirm the Streamlit baseline is green** before any changes (see Phase 1 verification commands).
- [x] **Lock the browser-upload architecture — DONE (2026-08-05): 25 MB direct browser cap.** Cloud Run under HTTP/1 caps request size at **32 MiB**; end-to-end HTTP/2 has no stated request-size limit — but HTTP/2 is **not** selected merely to preserve 100 MB browser uploads (it adds transport/deployment complexity without solving parsing memory, dataframe expansion, processing time, retention, or cleanup). Signed Cloud Storage upload is deferred until real file-size evidence requires it. (Archive §4.12–4.13; Cloud Run quotas.)
- [x] **Lock the session/data architecture — DONE (2026-08-05): state placement, not one store.** `SessionStore`/`DatasetStore` interfaces with in-memory implementations for local dev. Staging proof is scoped precisely — **local-first revision (2026-08-06):** prove a *shared OAuth/session implementation* **before the hosted beta** (in-memory stores are acceptable through Phase 5, since local use is single-process); **object storage is proven only if the signed-upload architecture is chosen** — not a Phase 5 prerequisite; **Phase 1's in-memory local implementation is sufficient for the vertical slice** as long as it follows the final interfaces. Cloud Run routes requests across instances and session affinity is best-effort, not a consistency guarantee. The durable database choice (refresh tokens, audit) is postponed until real multi-user/audit requirements exist. (Archive §4.13–4.15.)
- [x] **Publish the canonical API decision record** (prefix `/api/v1`, `/healthz`, `{ dataset }`, HttpOnly cookie + `credentials: "include"`, snake_case at the boundary, `api.ts` camelCase, chat transport, upload policy) and add it to the top of every implementation-facing doc (F3, F4, plan) with old paths marked superseded. **DONE (2026-08-05 revision pass).**
- [x] **Write the data-retention + Gemini data-boundary policy** — **DONE (2026-08-05), defaults APPROVED (2026-08-06):** `policies/data-retention-policy.md` exists and all five §11 defaults were approved by the product owner on 2026-08-06 (24 h retention / 2 h-12 h session / Clear Data semantics / 30-day export metadata / Gemini allowlist-only), closing gate 6.

**Exit criteria (DoD):** `.env` rotation completed with evidence (checklist §Verification) · branch created · baseline test run recorded.

**Phase 0/1 priority gates (8-item checklist, refined 2026-08-05 per third review — archive §4.14).** Gates are technical, not just done/not-done. **A gate closes only when its stated evidence is present — not because its document exists** (closure rule, 2026-08-06). The vertical slice (gate 7) is blocked only by **1, 2, 3, 4, 5a, and 6**; **gate 5b is part of the slice itself**.

| # | Gate | Owner | Status |
|---|---|---|---|
| 1 | Rotate/remove tracked Lovable credentials | You | ✅ **DONE (2026-08-06)** — both exposed `AIzaSy…` keys owned by product owner's insights-explorer GCP setup, rotated/revoked + old keys confirmed invalid (user-confirmed ~2026-08-03); whisperer-30 tracked `.env` (Lovable connector key only) **untracked** (`2341c9c`, branch `fix/remove-tracked-env`, pushed), `.gitignore` rules + `.env.example` added; **history-wide secret scans clean in both repos** + credential guard exit 0; closure recorded without secret values (`policies/env-rotation-checklist.md` — Gate 1 closure record) |
| 2 | Create migration branch + Streamlit feature freeze | You | ✅ **DONE (2026-08-06)** — `feat/react-fastapi-migration` created + pushed from `main` @ `3769575`; Streamlit feature freeze **ACTIVE** on `main` (production/security fixes, CI/deploy fixes, and docs only; feature requests park in `IDEAS.md` as `post-migration`) — `policies/branch-and-freeze-policy.md` §4 |
| 3 | Publish canonical API decision record | ✅ Done | Confirm all implementation docs use `/api/v1` (F3/F4/plan top sections) |
| 4 | Lock upload policy — 25 MB direct / 100 MB server-side with safeguards | ✅ Done | `MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024`; `MAX_INGEST_BYTES = 100 * 1024 * 1024`; revisit only after production evidence shows legit uploads > 25 MB |
| 5a | Lock state contracts and placement policy | ✅ Done | Interface responsibilities, state-placement rules, TTL assumptions, failure behavior — locked in §5 + cross-cutting A |
| 5b | Implement/test local `SessionStore`/`DatasetStore` | Implementation agent | **Phase 1 task** — `InMemorySessionStore`/`InMemoryDatasetStore`; part of the vertical slice |
| 6 | Confirm retention, clear-data, and Gemini boundary defaults | You | **APPROVED (2026-08-06)** — product owner approved all five points in `policies/data-retention-policy.md` §11: **`RETENTION_HOURS` 24 h** (upper bound for a future persisted store — **effective Phase 1 retention ≤ 12 h**, earlier of session expiry and `RETENTION_HOURS`) · **2 h idle / 12 h absolute** session · Clear Data deletes dataset/preview/quality-cache/chat/export-temp (keeps OAuth + theme) · export metadata only (format/timestamp/rows/session id, 30 days) · Gemini allowlist-only with identifiers removed/aggregated, provisional metrics carry caveats, unavailable metrics never numeric evidence |
| 7 | Build upload → preview → quality → clear vertical slice | Implementation agent | ⏳ **Blocked by 1 and 2; includes 5b** — Gate 6 approved 2026-08-06 |
| 8 | Explicitly defer GA4, Drive, chat, and export | You | 🟢 Active (by plan) |

---

## 5. Phase 1 — API contract & FastAPI skeleton (Week 1)

> **STATUS: ✅ DONE (2026-08-06)** — vertical slice shipped on `feat/react-fastapi-migration` (`eaa6ac5` + `66c0f1d`, review fixes; YAML-aware guard). Evidence: 782 tests, guard exit 0, live uvicorn smoke (session-cookie lifecycle) recorded in `specs/phase-1-upload-slice.md` Gate 7.

**Inputs:** `specs/phase-1-api-react-callback-tests-implementation.md` (F4 — full packet) · plan Phase 1 + amendments · archive §3.5 (wire format), §3.9 (ai pin), §4.2 (canonical shapes), §4.11 (size policy).

**Goal:** stand up `api/` (FastAPI) with the JSON contract between React and Python, using F4's vertical slice as the code-level reference.

**Authorization (2026-08-06 — reviewer unblock):** Phase 1 is authorized. **First PR scope (only):** FastAPI app bootstrap · `/healthz` · configuration + safe environment-variable handling · `SessionStore`/`DatasetStore` interfaces + in-memory local implementations · `POST /api/v1/upload` (25 MB browser cap) · `GET /api/v1/data/context` · `GET /api/v1/data/preview` · `GET /api/v1/data/quality` · `POST /api/v1/data/clear` · API contract tests. **Keep out of the first PR:** React UI porting · GA4 OAuth · Drive integration · Gemini/chat · charts/forecasting/funnels/exports · evidence/prototype panels.

**Locked decisions (do not re-litigate):**
- **Canonical contract shapes (Part 4 §4.2):** `GET /healthz` (not `/health`) · `POST /api/v1/ga4/connect` returns `{ authorization_url }` (snake_case at the boundary) · upload returns `{ dataset }` wrapper (plus `{ dataset, rows }` where F4 specifies) · `credentials: "include"` in the client · `setSourceFromApi` in the store · API versioned **`/api/v1`** (all routes below use the versioned prefix).
- **Chat wire format — decide at contract time and record in OpenAPI:** plain SSE (`text/event-stream`, `data: <chunk>\n\n`) vs AI SDK data-stream (`toDataStreamResponse()`/`toUIMessageStreamResponse()`). The captured repo pins **`ai@^7.0.48`** and its chat route uses `streamText(...).toTextStreamResponse()` (plain text) — F3's store reader consumes plain text, so **plain SSE is the default unless the team chooses `useChat`** (which requires the SDK format). (Plan Phase 1; archive §3.5, §3.10 item 1.)
- **Upload policy (locked 2026-08-05 — not optional):** direct browser uploads are limited to **25 MB** (`MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024` — margin below Cloud Run's 32 MiB HTTP/1 boundary); Drive/server-side imports may ingest up to **100 MB** (`MAX_INGEST_BYTES = 100 * 1024 * 1024`, matching `utils/drive_client.py`'s guard) **subject to memory, MIME, row-count, and decompression safeguards** — a streaming download path, decompression/row-count limits, cleanup behavior, and sufficient Cloud Run memory (a 100 MB compressed XLSX can expand dramatically in memory). End-to-end HTTP/2 is not selected merely to preserve 100 MB browser uploads. **Revisit the browser cap only after production evidence shows legitimate users need uploads above 25 MB** (that is also the trigger for signed Cloud Storage, which is deferred until then). (Archive §4.11–4.14.)
- **Dependency floors:** `pandas>=2.3.3` (first cp314 wheels), `pydantic>=2.12`, `fastapi`, `uvicorn`, `python-multipart`, `google-genai` (see Phase 3). (Archive §3.10 item 6.)
- **Session/data architecture (state placement, not a single store — locked 2026-08-05; local-first revision 2026-08-06):** `SessionStore`/`DatasetStore` **interfaces** defined now with in-memory implementations for local dev (**sufficient through Phase 5 under the local-first posture**); a **shared ephemeral session/OAuth store is proven before the hosted beta** (GA4 + Drive depend on it at scale); **object storage is proven only if signed-upload architecture is chosen**. State is placed **by type**: browser session ID → HttpOnly cookie; OAuth state/PKCE verifier → ephemeral store with short TTL (Redis/Valkey); active dataset metadata/filters/metrics → shared store; raw uploads → object storage (Cloud Storage); parsed dataframes → memory cache (eviction-tolerant); OAuth refresh tokens → encrypted durable store; chat usage/audit → Postgres later. No provider token or raw dataset is stored in the browser. (Archive §4.13–4.14.)
- **Blocking work:** keep CPU-heavy routes synchronous or run blocking work in a controlled thread pool (never inline in `async def` hot paths — it stalls SSE/chat); hard-cap rows, columns, and **decompressed** size; reject password-protected spreadsheets, suspicious MIME mismatches, and compression bombs; stream or temp-store exports instead of buffering in memory.
- **OAuth production-real from the start:** persist `state`, PKCE verifier, creation time, and intended post-auth return path in the shared session with a short expiry and one-time use; maintain separate redirect URIs for local/staging/production from an allowed-host config — never derive the redirect host loosely from request headers.
- **Data retention (policy before API):** adopt `policies/data-retention-policy.md` — upload retention window, raw-frame persistence, session expiry, Clear Data semantics, export-logging retention, Gemini prompt field allowlist, identifier removal/aggregation before AI calls.

**Tasks (F4 §1–§12 is the implementation packet; this is the task skeleton):**
- [ ] Create `api/` per F4's target layout: `config.py` (env, CORS for `http://localhost:5173`), `dependencies.py` (session), `schemas.py`, `services/dataset_service.py`, `routes/health.py`, `routes/upload.py`, `main.py`.
- [ ] Implement the **vertical slice**: `POST /api/v1/upload` (multipart, **25 MB direct-browser cap** — `MAX_BROWSER_UPLOAD_BYTES`, *not* 100 MB) → `GET /api/v1/data/context` + `GET /api/v1/data/preview` → `GET /api/v1/data/quality` → **`POST /api/v1/data/clear`** (server-side Clear Data per `policies/data-retention-policy.md` §5). The **100 MB `MAX_INGEST_BYTES`** applies to **Drive/server-side ingestion only** (Phase 5), subject to metadata, streaming, MIME, decompression, row, column, and temp-file limits — never to the browser upload path (locked 2026-08-05; wording conflict fixed 2026-08-06).
- [ ] Session: define `SessionStore`/`DatasetStore` interfaces; in-memory implementation keyed by opaque `HttpOnly` cookie for dev; **shared ephemeral session/OAuth storage + object storage for raw uploads proven before Phase 5** (state placement — see cross-cutting A).
- [ ] GA4 OAuth **adapters only** in Phase 1 (start/callback scaffolding per F4 §8) — full flow is Phase 5. PKCE (S256) is required even in the adapter (Plan Phase 5 amendment; archive §3.2).
- [ ] MSW test setup in the frontend *if* the React shell exists yet — otherwise defer to Phase 4 (F4 §12).
- [ ] Add `requirements/base.txt` entries + `run_api.py` or `make run-api` (uvicorn).

**Exit criteria (DoD):** app runs on `:8000`; `/healthz` passes; **upload→preview→quality→clear** works end-to-end via `httpx` contract tests (incl. the Clear Data semantics from `policies/data-retention-policy.md` §5); **25 MB browser cap enforced** (boundary test with the §4 rejection message; the 100 MB `MAX_INGEST_BYTES` is a Phase 5 Drive/server-side concern); baseline 742 pytest still green.

**Verification (planned, not run):** `pytest tests/api/` · `curl localhost:8000/healthz` · full `pytest` suite for regression.

---

## 6. Phase 2 — Decouple `utils/` from Streamlit (Week 2)

> **STATUS: ✅ DONE (2026-08-06)** — `8c66eea` on `feat/react-fastapi-migration`. Import-boundary guard (`tests/test_utils_import_boundary.py`), `utils/caching.py` fingerprint memo, `UsageEvent` + `usage_sink` threading, structured `DatasetWarning` + `load_file()` adapter, quarantine banners on `styles`/`error_boundary`/`session`. Evidence: 794 tests, guard exit 0, hooks green. Full record: `specs/phase-2-utils-decoupling.md`.

**Inputs:** plan Phase 2 · `policies/session-state-inventory.md` (which `st.session_state` reads move where) · `policies/test-layer-inventory.md` §1 (452 utils-facing tests must stay green).

**Goal:** make `utils/` importable by FastAPI while Streamlit keeps working.

**Tasks:**
- [ ] The seven Streamlit-coupled utils: `data_loader` (drop `@st.cache_data`), `error_boundary` (keep Streamlit-only), `forecasting` (drop `st.cache`), `gemini_client` (drop Streamlit rate-limit display; keep core calls), `prompt_templates` (pass context as args, no `st.session_state` reads), `session` (replaced by FastAPI session — see cross-cutting A), `styles` (Streamlit-only, stays).
- [ ] Confirm remaining utils are pure: `data_context`, `ga4_client`, `drive_client`, `charts`, `funnels`, `quality`, `exports`, `commands`, `sanitize`.
- [ ] Every removed `st.session_state` read gets its replacement from `policies/session-state-inventory.md` (44 keys, 6 groups).

**Exit criteria (DoD):** `utils/` Streamlit-free or minimally coupled; FastAPI imports any util without touching `st`; **all 742 tests still pass** (utils tests prove behavior preserved).

**Verification (planned):** full `pytest` · `python -c "import utils.gemini_client"` outside a Streamlit runtime.

---

## 7. Phase 3 — Wire FastAPI to real utils (Week 3)

**Inputs:** plan Phase 3 + amendments · archive §3.4 (funnel nuance), §3.9 (Gemini SDK), §3.10 item 7 (model hygiene).

**Goal:** replace mock/skeleton responses with real `utils/` calls.

**Tasks:**
- [ ] `POST /api/v1/upload` → `data_loader` · preview → `data_context` · quality → `quality` · charts → `charts` · summary → `gemini_client` + `prompt_templates` · forecast → `forecasting` · funnel → `funnels` · export → `report_exporter`.
- [ ] **Gemini:** use the current `google-genai` SDK (`client.models.generate_content_stream(...)`); record `thoughts_token_count` in the server-side usage ledger (the app already tracks `total_thought_tokens` — keep that observability). (Archive §3.9 item 4.)
- [ ] **Model hygiene:** `gemini-2.0-flash` is shut down and `gemini-1.5-flash` deprecated — prune `utils/gemini_client.py`'s `AVAILABLE_MODELS`; keep `gemini-2.5-flash` (1M context) as default. (Archive §3.10 item 7.)
- [ ] **Funnel nuance:** template funnels may be partially available via GA4's `runFunnelReport`; scope `GET /api/v1/analysis/funnel` to template funnels and re-verify the ROADMAP funnel rows at implementation. (Archive §3.4, §3.8 item 4.)
- [ ] Chat streaming per the Phase 1 wire-format decision; `StreamingResponse` with disconnect handling (Starlette cancels the async generator on client disconnect — `CancelledError`). (Archive §3.10 item 8.)
- [ ] Contract tests for every endpoint (pytest + httpx). All endpoints versioned under `/api/v1`.

**Exit criteria (DoD):** all read-only endpoints return real data; contract tests cover every endpoint; error taxonomy (upload limits, bad types, auth) preserved from the Streamlit layer.

---

## 8. Phase 4 — Port React UI into `frontend/` (Week 4)

**Inputs:** `specs/freebuff-prompt-wire-react-store.md` (F3 — 13 steps) · plan Phase 4 + amendments · archive §3.6 (validateSearch), §3.9 items 3/5 (pins, bun), §3.10 items 2/5 (strip list, Recharts) · `whisperer-30-reference/` (captured source; **the store-wiring instruction set is `whisperer-30-reference/STORE-DRIFT-MATRIX.md`** — captured store vs F3, supersedes the earlier drift cross-check).

**Goal:** copy the whisperer-30 components in, strip the Start/Lovable/Nitro plumbing, and swap mock store calls for real API calls.

**Tasks:**
- [ ] Copy `src/` → `frontend/` (from the frozen capture, not a live clone, until the frontend build is reproducible).
- [ ] **Strip list (round-3 verified):** remove `@lovable.dev/vite-tanstack-config`, `@tanstack/react-start`, `nitro`, `src/server.ts`, `src/start.ts`, `src/routes/api/*` (Start/Nitro server routes); replace the plugin with `@vitejs/plugin-react` + `@tanstack/router-plugin/vite`; file-based `createFileRoute` routing is identical without Start. (Archive §3.10 item 2.)
- [x] **Package manager: LOCKED — npm (2026-08-06).** Rationale: the Drive Picker frontend already uses npm (`package-lock.json`); GitHub Actions, Cloud Build, and hosting tools support npm by default; the captured `bun.lock` was deliberately excluded, so npm gives a clean reproducible start rather than reviving the Lovable toolchain. Bun may still be used locally, but the repo standard is one lockfile + one CI path. **Record:** `frontend/package-lock.json` · CI install `npm ci` · local scripts `npm run dev / build / test`. (Archive §3.9 item 5; §3.10 item 6; review round 2026-08-06.)
- [ ] **Recharts × React 19:** `recharts@^2.15.4` doesn't declare React 19 peer deps — try plain install first; on peer errors use `overrides` or move to recharts 3.x. (Archive §3.10 item 5.)
- [ ] **F3 store wiring (13 steps):** remove mock imports → API base (relative `/api`) → real `loadData()` upload → GA4 flow → Drive flow → `streamAi` → SSE chat per Phase 1 format → quality/charts/forecast/funnel fetchers → export → `ExplorerValue` interface (**union** — F3's §9 omits `addFilter`/`addMetric`/`sendMessage`/`clearChat`) → delete mock files → `api-types.ts` → `.env` files. (F3 §1–13; **follow `STORE-DRIFT-MATRIX.md` row-by-row** — it pins the union, the filter/metric server-sync semantics, the command-router move to `utils/commands.py`, and the `api-types.ts` type extraction.)
- [ ] **Chat route:** remove the Lovable AI gateway path; AI routing stays under Python/FastAPI control (Batch 3; `utils/prompt_templates.py` is the system prompt source — never the whisperer's hardcoded BrainGuide prompt).
- [ ] **Routing:** TanStack Router `validateSearch` + `Route.useSearch()` for typed search params (GA4 callback `status`/`reason`), never raw `window.location.search`. (Archive §3.6.)
- [ ] MSW test setup: `setupServer` from `msw/node`, `onUnhandledRequest: "error"`; mocks (`mock-ga4.ts`, `mock-braintree.ts`) become **test fixtures only**; streaming chat tests use `HttpResponse` + `ReadableStream` body with SSE headers (jsdom has no `EventSource` — test the `getReader()` path). (F4 §12; archive §3.10 item 4.)
- [ ] **Chat reconnect behavior (before any deploy):** the client retains the user message, renders partial output safely, and allows retry without creating duplicate assistant messages. Treat Cloud Run's configurable request timeout (default 300s, up to 3600s) as a ceiling, not a guarantee of one uninterrupted stream. (Archive §3.10; §4.12.)
- [ ] **New Lovable panels stay out of the first slice (gate 8, 2026-08-06):** `EvidenceConnectorPanel`, `InsightCandidates`, `MeasurementContractPanel`, `insights/engine.ts`, and the research-source changes are **mock-driven prototypes of the deferred evidence-connector workstream** (`plans/evidence-connector-design.md`) — do not port them into the vertical slice; `mock-evidence.ts` → MSW fixture material only. (Archive §4.16.)
- [ ] **Prototype quarantine rule (2026-08-06; archive §4.18):** mock-evidence + deterministic-engine prototype code live under **test/fixture or prototype-only paths**, never runtime production sources; the three panels are **not mounted in the first production slice**; any design preview keeps them behind an obvious **"Demo / mock data"** label; mock sources are **never registered in the production source registry**.
- [ ] `frontend/README.md` + gitignore for `node_modules`, `dist`.

**Exit criteria (DoD):** `npm run dev` + `uvicorn` produce a usable app at `localhost:5173`; no references to `mock-ga4.ts`/`mock-braintree.ts` in runtime code (fixture-only); **only `functional` (plus optional `placeholder`) components from the `MANIFEST.md` `initial_mount` column are mounted in the first slice** — `deferred` components (Chat, AiSummary, ExportMenu, OnboardingTour, Drive sheet, equity/research/evidence panels) stay unmounted; no component carrying a `mock` or `Lovable/Nitro` runtime dependency is mounted in the first slice; store talks to FastAPI with `credentials: "include"`.

---

## 9. Phase 5 — GA4 OAuth + Drive Picker (Week 5)

**Inputs:** plan Phase 5 + amendments (items 1–7) · archive §3.2 (PKCE), §3.3 (Picker), §3.4 (GA4), §3.6 (validateSearch) · F4 §8 (OAuth adapters) · `utils/ga4_client.py`, `utils/drive_client.py`, `components/drive_picker_component_frontend/`.

**Goal:** the two hardest integrations, preserving the existing error taxonomy.

**Tasks — GA4 OAuth:**
- [ ] `POST /api/v1/ga4/connect` → OAuth URL from `ga4_client.py`, with **PKCE** (S256 `code_verifier`/`code_challenge`; store verifier server-side). (Plan amendment 1; archive §3.2.)
- [ ] `GET /api/v1/ga4/callback` → validate `state`, exchange code server-side, store credentials server-side, redirect to React callback page with only `status=success` / safe error reason. **Provider tokens never reach React.** (F4 §8; archive §1.13.)
- [ ] **Canonical callback status contract (2026-08-06):** `status=success` · `status=cancelled` (user cancelled at Google — the `provider_denied` reason is superseded) · `status=error&reason=<safe_code>` (`invalid_state` | `token_exchange_failed` | …). The exact same values are used in FastAPI redirects, the React callback route, F4, the Playwright tests, and the E2E matrix — no legacy spellings (`provider_denied`, `invalid_oauth_state`) in new code.
- [ ] React callback route `/auth/ga4/callback` with `validateSearch` schema; on validation failure the router sets `error.routerCode === "VALIDATE_SEARCH"` and renders the route's `errorComponent` (verified against `@tanstack/react-router@1.170.20`). (Plan amendment 6; archive §3.6.)
- [ ] `POST /api/v1/ga4/pull` → paginate (`limit`/`offset`, 10k-row pages, ≤9 dimensions, max 250k rows/request) and throttle for the **10 concurrent requests/property (Standard; 50 for 360)** quota; enable `returnPropertyQuota: true` for observability; account for token budgets (200k/day + 40k/hr per property) and the 120 thresholded-requests/hr cap. (Plan amendment 7; archive §3.9, §3.10.)
- [ ] Align pulled metrics with `plans/ga4-measurement-contract.md` via `contract_row`/`validation_status` provenance; aggregate-only rows stay `unavailable`. (Archive §4.11.)

**Tasks — Drive Picker (browse-UX decision 2026-08-06; archive §4.16; contract shape §4.17 / transcript §6.1):**
- [ ] **Choose the Drive browse UX:** (a) port the Lovable **slide-out browse** (search + folder breadcrumbs + file metadata + open-in-Drive links, per `whisperer-30-reference/LOVABLE-UPDATES-080525.md` §5–6) — requires `GET /api/v1/drive/list?q=&folder_id=` backed by `utils/drive_client.py` metadata calls (the prototype's Nitro `/api/drive-files` route is non-canonical), **or** (b) keep the Google **Picker iframe** (existing `drive_picker_component_frontend/` behavior, `setAppId` project number + referrer-restricted API key). Either way: preserve size safeguards + error taxonomy; the picker-token endpoint is only needed for option (b).
- [ ] **`GET /api/v1/drive/list` contract (if slide-out chosen) — fully specified by the prototype + pagination + live-verified Drive API facts (2026-08-06; archive §4.18–4.19):** params `q` (search) / `folder_id` (browse, default `root`) / **`page_token`** (opaque continuation token, optional); server-side Drive `files.list` query `trashed = false AND (name contains '<term>' OR '<folder_id>' in parents)`, `orderBy: folder,modifiedTime desc`, fields `id,name,mimeType,modifiedTime,size,webViewLink,iconLink`; response `{ state, message?, setupHint?, files: [...], next_page_token }` — **`next_page_token` is required (opaque string or null; omitted = no more pages), passed back as `pageToken`**; a folder larger than the page must paginate, not silently truncate, and the React sheet adds a "Load more" affordance. **Live-verified (Drive API v3 docs):** `pageSize` max is **1,000** (default 100) — the prototype's 50 is safe but can be raised; the app's modest analytics volume is far inside the 1B requests/day default quota (20k queries/100s per user). States `ready|not_configured|permission|error` (`not_configured` → no credentials; 401/403 → `permission` → reconnect + `drive.readonly`; else `error`). (Archive §4.17, §4.19; transcript §6.1.)
- [ ] **⚠️ Import is the real integration seam:** the prototype's Import button only calls `loadData("drive · <name>")` (mock source name) — it does **not** download or ingest. The port must wire Import → `POST /api/v1/drive/download` → `data_loader` → dataset. (Archive §4.17; transcript §6.1.)
- [ ] **`POST /api/v1/drive/download` — server-side trust boundary (2026-08-06; archive §4.18):** accept the Drive **`file_id`** only — never trust a client-provided filename, MIME type, or byte size. Server re-fetches file metadata from Drive, enforces `MAX_INGEST_BYTES = 100 MB` (from metadata where available) and the MIME/type allowlist **server-side**, and handles Google-native Sheets via an **export path** (not byte download). Post-download: decompression, row, column, and temp-file lifetime limits; **return the same typed errors as the local upload path**. The React sheet's MIME/name checks are UX guidance only, never the security authority. **Local cross-check (2026-08-06; archive §4.19): this boundary ALREADY EXISTS in `utils/drive_client.py`** (`download_drive_file`) — server-authoritative `files.get(fields="name,mimeType,size")`, `DRIVE_IMPORT_MIME_TYPES` allowlist, Sheets `export_media(mimeType="text/csv")` first-sheet-only, 3-layer size enforcement (metadata preflight → `_BoundedBytesIO` stream cap → final `len()` check), typed `DriveImportError` codes (`unsupported_type/too_large/empty_file/not_found/access_denied/download_failed`). **Phase 5 is a port of this function into `api/services/drive_service.py`, not new design.** Live-verified nuance: Google-native files have **no `size` metadata field** (hence the stream-cap layer); Google imposes a **10 MB export cap** on Sheets/docs exports — so Sheets can never exceed 10 MB regardless of the 100 MB policy; `alt=media` binary downloads have no practical limit (5 TB/file ceiling).
- [ ] Port the chosen UI as a **native React component** (not an embedded Streamlit component).
- [ ] `POST /api/v1/drive/picker-token` → returns the OAuth token **and the project number** (`setAppId`) — **only if the Picker iframe (b) is chosen**; document Cloud Resource Manager API enablement; restrict the API key to HTTP referrers. (Plan amendment 2; archive §3.3.)
- [ ] **E2E acceptance matrix (2026-08-06) — Playwright, written in Phase 5:**

| # | Case | Expected |
|---|---|---|
| 1 | User cancels Google OAuth | Callback receives `status=cancelled`; safe cancelled state renders; no partial session state |
| 2 | Drive not configured | Sheet state `not_configured` with setup hint; no crash |
| 3 | Drive permission expired | State `permission` → reconnect flow re-requests `drive.readonly` |
| 4 | Unsupported file selected | Typed `unsupported_type` error matching the upload taxonomy |
| 5 | Client sends forged filename/MIME/size metadata | Backend re-fetches Drive metadata and rejects on mismatch |
| 6 | Backend authority on metadata | `file_id` is the only client input; server `files.get` decides |
| 7 | Binary CSV/XLSX import | Downloads server-side, parses, creates the active dataset |
| 8 | Google-native Sheet | Export path (`text/csv`), respects the 10 MB export cap |
| 9 | Size limit enforcement | 100 MB ingestion policy enforced server-side |
| 10 | Download → preview/quality | Parsed dataset becomes active; preview + quality state render |
| 11 | Clear Data | Removes active dataset + derived state (previews, analysis cache, chat context, temp exports) |
| 12 | Token containment | Browser never receives the Drive access token (assert via network logs + credential guard) |

GA4 E2E: connect → pull → preview success path plus the OAuth error/cancel path (row 1). This matrix turns the "Import only fakes `loadData`" discovery into a permanent regression barrier.

**Exit criteria (DoD):** both flows work in React with the server-session model; errors (size, auth, bad type) surface with the established taxonomy; no token leakage (credential guard extends to FastAPI env vars).

---

## 10. Phase 6 — Cutover, hosting, retire Streamlit (Week 6)

**Inputs:** plan Phase 6 + amendments · `policies/dockerfile-pattern.md` (full) · `policies/test-layer-inventory.md` §4 (retirement checklist) · archive §3.10 item 3 (Cloud Run), §3.11 (Vercel eval).

**Goal:** one product at one URL on container hosting; Streamlit retired; docs updated.

**Tasks:**
- [ ] **Hosting: Cloud Run (recommended).** The repo already deploys via `cloudbuild.yaml` → docker build → Artifact Registry → `gcloud run deploy`. Bind `$PORT` (8080); raise the request timeout for SSE (default 300s, max 3600s) or heartbeat; treat session affinity as best-effort (design chat reconnect); enable HTTP/2 (`h2c`); set the OAuth redirect to the explicit public HTTPS URL (Cloud Run proxies `X-Forwarded-Proto`). (Archive §3.10 item 3.)
- [ ] **Single-origin Dockerfile** per `policies/dockerfile-pattern.md`: stage 1 Vite build → stage 2 Python runtime serving static SPA + `/assets` mount + SPA fallback guarded to non-API paths. Vercel is **ruled out for the backend** (≈4.5 MB serverless body cap vs 100 MB ingestion; duration limits vs SSE; stateless vs sessions) — SPA-on-Vercel + API-elsewhere is rejected (split origins). (Archive §3.11.)
- [ ] **Feature-parity checklist** (12 features: upload, GA4, Drive, preview, quality, summary, charts, forecast & funnel, chat, export, Learn, onboarding).
- [ ] **Retire Streamlit tests** per `policies/test-layer-inventory.md`: 290 Streamlit-layer tests rewritten as API-contract tests or retired; 452 utils tests stay; 40 Playwright tests become the new E2E baseline.
- [ ] Update `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md` (v0.4.0 entry); archive `insights-whisperer-30` repo with a fold-in note.
- [ ] Update **both** CI pipelines: `.github/workflows/test.yml` (pytest + frontend build + Playwright) and `cloudbuild.yaml` (container build/deploy). (Archive §1.13.)

**Exit criteria (DoD):** single production URL serves React + FastAPI; all 12 parity items verified; no Streamlit-dependent test failures; Streamlit marked retired.

**Verification (planned):** `scripts/smoke_test.sh` reworked for the new stack (boot both services, `/healthz`, upload CSV, chat stream) · Playwright parity suite · Lighthouse + bundle-size checks (plan Success Metrics table).

---

## 11. Cross-cutting workstreams

These run alongside the phases and are owned by specific source docs.

### A. State migration — `policies/session-state-inventory.md`
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

**Second-contract guard — RESOLVED (2026-08-06):** the whisperer-30 `measurement-contract.ts` (110 lines) was cross-checked field-by-field against the canonical `plans/ga4-measurement-contract.md`: **verified faithful** — all 5 metric IDs, statuses (provisional ×2, unavailable ×3), numerator/denominator, grain, event mapping, blockers, and limitations match row-for-row. Canonical remains the single source of truth (Python/OpenAPI origin); the TS file is safe to reuse as a reference transcription but never as the authoritative contract, and TS types are generated from the canonical source. (Archive §4.16–4.17.)

**Metric-state policy — RESOLVED (2026-08-06; archive §4.18):** the prototype's `computableMetrics()` filters only `unavailable`, so it admits **provisional** rows into model-visible context — and its insight engine cites `unavailable` metrics in findings (with caveats). That is acceptable in a prototype but must be explicit in the product. Adopt:

| Metric state | Display in dashboard | Use in deterministic insights | Send to Gemini |
|---|---|---|---|
| `validated` | Yes | Yes | Yes, with provenance |
| `provisional` | Yes, clearly labeled | **Directional only** (explicit decision — recommended) | Only with an unvalidated label/caveat |
| `unavailable` | Show as unavailable | No computed claim/rate | Only as a blocked capability, never as measured evidence |

Rename the prototype helper to `modelVisibleMetrics()` / `nonUnavailableMetrics()` (or drop it) — `computableMetrics()` invites misreading provisional rows as validated-quality. **Canonical home:** the policy table above is mirrored as the **"Metric-status consumption policy"** section of `plans/ga4-measurement-contract.md` (the semantic source of truth); this plan links to it — see that section if the two ever drift.

### C. Test strategy — `policies/test-layer-inventory.md`
**742 = 452 utils-facing (61%, transfer as-is) + 290 Streamlit-layer (39%, rewrite/retire) + 40 Playwright E2E.** Per-file transfer paths in the inventory; four-layer matrix in archive §1.13 item 5. DoD per phase includes its test gate.

### D. Security & credentials — `policies/env-rotation-checklist.md` + existing credential guard
`.env` rotation (Phase 0 — **Gate 1 closed 2026-08-06**) · credential guard patterns extended to FastAPI env vars · `.env.example` updated with all new API env vars (session secret, CORS origins) · `__Host-` cookie prefix (needs `Secure` + `Path=/` + no `Domain`) · never log keys or echo tokens in responses.

**Guard allowlist rule (2026-08-06):** prepare FastAPI env-var validation now — **names only**: `API_SESSION_SECRET` · `API_CORS_ORIGINS` · `FRONTEND_URL` · `MAX_BROWSER_UPLOAD_BYTES` · `MAX_INGEST_BYTES`. The guard validates variable names, expected presence in deployment, and that **no values are committed** — never treat a secret value as trusted because it matches a broad pattern, and never put permissive wildcard patterns into the allowlist.

### E. CI/CD & deployment — `cloudbuild.yaml` + `.github/workflows/test.yml` + `policies/dockerfile-pattern.md`
Both pipelines updated in Phase 6 · frontend build gate (**`npm ci` → typecheck → build** — package manager locked to npm 2026-08-06) added alongside pytest · container deployment to Cloud Run · smoke script reworked for the new stack.

### F. Data retention & AI data boundary — `policies/data-retention-policy.md`
Written **before the API exists** (Phase 0/1): upload retention window, whether raw dataframes persist or are session-only, session expiry, exactly what "Clear Data" deletes, what export logging retains, which fields are allowed in Gemini prompts, and which identifiers must be removed/aggregated before an AI call. "Server-owned" is better than browser-owned, but it is not automatically privacy-safe.

### G. Research discipline — when to invoke the web/docs research agent (2026-08-06)
Invoke external research **only when an external platform decision is imminent**; never to re-derive internal decisions already locked in this plan. Full policy, the four ready-to-use research prompts, and the "do not research again" allowlist live in **archive §3.12**; this section is the pointer + timing map.

| Priority | Research area | Invoke before | Why |
|---|---|---|---|
| High | GA4 report compatibility + funnel feasibility (`runReport`/`runFunnelReport`/`getMetadata`/`checkCompatibility`, dim/metric combos, thresholding, `returnPropertyQuota`) | Phase 5 | Exact current API support for the app's intended requests, not generic quotas — risk item 7 stays open until then (9 dims / 10 metrics, 7 for funnel; limits page 404s). Output includes a **post-OAuth compatibility-probe checklist** — property-specific facts (available events, custom dims, thresholding) can't be proven from docs alone (archive §3.12) |
| High | Gemini production models — availability, deprecations, pricing, rate limits, `google-genai` streaming + cancel/disconnect | Phase 3 | Model lifecycle changes quickly; §3.10 facts must be re-verified at implementation time |
| Medium | Drive shared-drive behavior (`supportsAllDrives`, `includeItemsFromAllDrives`, `corpora`) | Phase 5, **only if slide-out browse chosen** (decision #9) | The remaining practical external gap for `files.list`; §4.19 verified pagination but not shared drives |
| Medium | Google Picker setup/security (project number, referrer restriction, scopes, token flow) | Phase 5, **only if Picker iframe chosen** (decision #9) | Current launch requirements |
| Medium | Cloud Run production-readiness (SSE timeouts/reconnect, cookies behind proxy, HTTP/1 vs h2c, SPA serving, memory for Pandas/XLSX) | Phase 6 | Needs a current check before hosted beta |
| Low | React 19 / Recharts compatibility + toolchain versions | Phase 4 | **npm is already locked** (2026-08-06) — re-verify versions only, never revisit the package-manager decision |

**Do not research again** (internal/verified): the 25 MB / 100 MB ingestion policy · metric-status consumption policy · the `file_id`-only Drive trust boundary (`utils/drive_client.py`) · mock/prototype quarantine rules · `measurement-contract.ts` faithfulness (verified) · the fake Lovable Import behavior · the Phase 1 vertical-slice scope.

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
│   │   ├── components/           # explorer/* + ui/* (shadcn) — production components only
│   │   ├── lib/
│   │   │   ├── explorer-store.tsx   # context provider (F3 target)
│   │   │   ├── api.ts               # typed client (snake→camel translation)
│   │   │   └── api-types.ts         # OpenAPI-derived types
│   │   ├── routes/               # file-based routing; /auth/ga4/callback (Phase 5)
│   │   ├── test/
│   │   │   ├── fixtures/            # mock-ga4.ts, mock-braintree.ts, mock-evidence.ts — TEST-ONLY
│   │   │   └── handlers/            # api.ts — MSW network handlers
│   │   └── prototype/            # evidence-connector demo panels (optional, non-production)
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
├── Dockerfile                    # multi-stage (Phase 6; policies/dockerfile-pattern.md)
├── cloudbuild.yaml               # updated (Phase 6)
├── .github/workflows/test.yml    # updated (Phase 6)
├── .env.example                  # updated with API env vars
└── …
```

**Deliberate exclusions from the target tree:** the Lovable AI gateway, `mock-ga4.ts`/`mock-braintree.ts`/`mock-evidence.ts` (→ `test/fixtures/` only), the whisperer's hardcoded BrainGuide prompt (→ `utils/prompt_templates.py`), Nitro/Start plumbing.

**Prototype quarantine layout (2026-08-06; archive §4.18–4.20) — rules for `frontend/`:**
1. **Production runtime must never import from `src/test/`** — fixtures and MSW handlers are test-only; enforce via an ESLint boundary or import-linter rule.
2. **Production source registry must never register mock data sources** — the `evidence` mock source stays out of the runtime `sources` registry.
3. **`src/prototype/`** holds the evidence-connector demo panels (EvidenceConnector / InsightCandidates / MeasurementContract) — explicitly non-production, excluded from normal production routes, or guarded behind a clear demo flag.
4. **Any preview using mock evidence must visibly show "Demo / mock data"** — no realistic-looking linkage/equity numbers without the label.

**UI source capture spec (2026-08-06; archive §4.21) — do before Phase 4:** capture the complete current `insights-whisperer-30` UI source at a **frozen commit SHA** so future Lovable changes cannot shift the port reference mid-work.
- **Capture point:** `8b4b7b9` ("Added evidence and GA4 panels" — includes all 17 new commits; supersedes the stale `a71c371` capture).
- **Scope:** `src/components/explorer/` (19) · `src/components/ui/` (46, shadcn — version-pin reference) · `src/routes/` (index/learn/__root port; `api/*` Nitro routes do-not-port) · `src/lib/` (store/utils port; mocks+engine fixture-only; `measurement-contract.ts` reference) · `src/router.tsx`, `src/styles.css` · `package.json`, `vite.config.ts`, `tsconfig.json` · `src/routeTree.gen.ts` (reference only — regenerated).
- **Exclusions:** `.env` (tracked in source repo — rotation is gate 1) · lockfiles unless dependency reproduction needs them · Lovable gateway config/credentials · generated route trees (captured only as reference).
- **Deliverable:** `migration/whisperer-30-reference/UI-CAPTURE-<SHA>/` with a **manifest** listing every file: source SHA · purpose · port classification (`Port/adapt` · `Reference only` · `Fixture only` · `Do not port`) · **`runtime_dependency`** (`none` / `mock` / `Lovable/Nitro` / `Python/FastAPI`) · **`initial_mount`** (`functional` / `placeholder` / `deferred` — renamed from `initial_slice` 2026-08-06; only `functional` components, plus optional `placeholder` shells, mount in the first slice). **Port/adapt means "UI shell" for mock-connected components** — the shell is copied but its data source/commands are replaced by FastAPI endpoints (refined 2026-08-06; see `UI-CAPTURE-8b4b7b9/MANIFEST.md`).
- **Every captured file passes the credential guard** before commit.

---

## 13. Open decisions (each blocks a specific phase gate)

| # | Decision | Blocks | Current recommendation |
|---|---|---|---|
| 1 | Chat wire format (plain SSE vs AI SDK data-stream) | Phases 3–4 | Plain SSE (matches `ai@^7.0.48` + `toTextStreamResponse()` + F3 reader) unless `useChat` is chosen |
| 2 | Durable store for refresh tokens / usage metadata (Postgres vs other) | Only if persistent reconnect or multi-user/audit needs appear | **Architecture locked: state placement** (cookie / ephemeral Redis-Valkey / shared store / Cloud Storage / memory cache / encrypted durable / Postgres-later); durable DB provider choice postponed — further deferred by the **local-first posture** (shared stores are beta-time work) |
| 3 | ~~Package manager (bun vs npm)~~ **LOCKED: npm** | ~~Phase 4~~ — | Locked 2026-08-06 — npm (Drive Picker convention + mature CI/hosting support + clean reproducible start from the deliberately excluded `bun.lock`); Bun optional locally only |
| 4 | Hosting platform | Phase 6 | **Cloud Run** (GCP investment, existing `cloudbuild.yaml`) — Railway/Render equivalent |
| 5 | Recharts 2.15.4 vs 3.x | Phase 4 | Try 2.15.4 first; `overrides` or 3.x on peer errors |
| 6 | `frontend/` vs `api/` layout (siblings) | Phase 1 | Siblings (per plan Open Questions #5; F4 §1 target layout) |
| 7 | GA4 dim/metric limits (9 dims / 10 metrics, 7 for funnel) | Phase 5 | Reported, not live-verified (limits page 404s) — re-verify at implementation |
| 8 | Revisit browser cap / signed Cloud Storage | Only after production evidence | **Locked: 25 MB** (`MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024`); revisit only if legitimate users need uploads above 25 MB; signed upload deferred until then |
| 9 | Drive browse UX (slide-out vs Picker iframe) | **Phase 5 only — NOT a Phase 1 blocker** | **Recommended: Picker iframe initially** (tested component in the Python repo; lower maintenance; native Google selection) — choose the slide-out browser only if Drive is a core differentiator; both call the same `POST /api/v1/drive/download`, so the choice is swappable later without changing ingestion (archive §4.18). **Paginated-OpenAPI deferral (2026-08-06; archive §4.20):** the formal `GET /api/v1/drive/list` OpenAPI/Pydantic schema is deferred until the slide-out browser is chosen in Phase 5 — the prose contract in §9 is the design artifact until then; no premature schema work in Phase 1 |

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
| Whisperer-30 tracked `.env` already exposed | High | Phase 0 rotation gate before any copy-in (`policies/env-rotation-checklist.md`) |
| Start/Nitro plumbing silently eats time in the port | Medium | Round-3 strip list, documented (Phase 4; §3.10 item 2) |
| Recharts × React 19 peer-dep breakage | Medium | Try/override/upgrade path (Phase 4; §3.10 item 5) |
| GA4 10-concurrent quota throttling undercounts | Medium | Live numbers + `returnPropertyQuota` observability (Phase 5; §3.9) |
| Hosting split origins break session/OAuth/SSE | Medium | Single-origin Docker + Cloud Run (Phase 6; §3.1, §3.10–3.11) |
| Two UIs alive = double maintenance | Medium | Feature freeze + fix-forward (Phase 0; branch policy) |
| Gemini model drift (2.0-flash shut down) | Low | Model hygiene pass in Phase 3 (§3.10 item 7) |
| Cloud Run 32 MiB request cap (HTTP/1) vs 100 MB ingestion | High | 25 MB browser cap; HTTP/2 or signed uploads only if real file evidence justifies (Phase 0/1; §4.12–4.13) |
| Sync/CPU-heavy work blocks the FastAPI event loop (SSE/chat stalls) | Medium | Sync routes or controlled thread pool; hard caps on rows/columns/decompressed size; streamed exports (Phase 1) |
| Session affinity ≠ consistency across Cloud Run instances (data loss) | Medium (beta+) | Shared ephemeral session/OAuth store proven before the hosted beta; in-memory acceptable through Phase 5 (local-first posture) |
| Retention/privacy exposure (client analytics + health/equity context) | Medium | `policies/data-retention-policy.md` + Gemini data-boundary rules before the API exists (Phase 1) |
| Second measurement contract (`measurement-contract.ts`) | ~~Medium~~ Low | **Resolved 2026-08-06 — verified faithful** transcription of the canonical contract (5/5 rows match); canonical stays the single source of truth; TS types generated from canonical source (cross-cutting B; archive §4.16–4.17) |
| Drive browse UX drift (slide-out vs Picker iframe) | Low | Explicit Phase 5 browse-UX decision; slide-out path adds `GET /api/v1/drive/list` (server-side Drive metadata); Nitro `/api/drive-files` route non-canonical (Phase 5; archive §4.16) |
| Drive Import button fakes the download (prototype only sets `loadData("drive · <name>")`) | High | Wire Import → `POST /api/v1/drive/download` → `data_loader` in the port; covered by the Phase 5 Drive E2E (Phase 5; archive §4.17) |
| Drive-list pagination missing (folder >50 entries silently truncated) | Medium | `next_page_token` in the list contract + "Load more" in the sheet (Phase 5; archive §4.18) |
| Client-supplied file metadata trusted for download | High (mitigated) | **Already implemented** in `utils/drive_client.py` (`download_drive_file`: server-authoritative metadata, MIME allowlist, Sheets export path, 3-layer size cap, typed errors) — Phase 5 ports it, it does not design it (Phase 5; archive §4.18–4.19) |
| Google Sheets export size cap (10 MB, provider-imposed) | Low (informational) | Native Google files have no `size` field and export is capped at **10 MB** by Google — Sheets imports can never approach the 100 MB policy; CSV/XLSX remain the 100 MB-relevant paths (Phase 5; archive §4.19) |
| Prototype mock evidence mistaken for live client data | Medium | Quarantine rule: fixture-only paths, panels unmounted in first slice, "Demo / mock data" label, no mock sources in prod registry (Phase 4; archive §4.18) |
| `computableMetrics()` admits provisional rows to model context | Low | Metric-state policy table + rename to `modelVisibleMetrics()`/`nonUnavailableMetrics()` (cross-cutting B; archive §4.18) |

---

## 16. Source map (doc → phase feed)

| Source doc | Feeds |
|---|---|
| `archive/insights-explorer-migration-ingest.md` | All phases (evidence + research + reconciliation) |
| `archive/insights-explorer-migration-plan.md` | Phase shapes 1–6, contract draft, metrics, risks |
| `specs/phase-1-api-react-callback-tests-implementation.md` (F4) | Phase 1 (packet), Phase 5 (OAuth adapters), MSW tests |
| `specs/freebuff-prompt-wire-react-store.md` (F3) | Phase 4 (13-step store wiring) |
| `policies/env-rotation-checklist.md` | Phase 0, cross-cutting D |
| `policies/branch-and-freeze-policy.md` | Phase 0 |
| `policies/session-state-inventory.md` | Phases 2/4, cross-cutting A |
| `policies/test-layer-inventory.md` | Phases 2/6, cross-cutting C |
| `policies/data-retention-policy.md` | Phase 1 (policy before API), cross-cutting F |
| `policies/dockerfile-pattern.md` | Phase 6, cross-cutting E |
| `archive/glm-5-2-vs-perplexity-migration-comparison.md` | Audit lens (no phase feed) |
| `whisperer-30-reference/` | Phases 0 (rotation evidence), 4 (source capture), 5 (picker port) |
| `whisperer-30-reference/LOVABLE-UPDATES-080525.md` | Phases 4–5 (Drive-import UI port), evidence-connector workstream, contract reconciliation (`measurement-contract.ts` — verified faithful) |
| `whisperer-30-reference/LOVABLE-ACTIONS-080526.txt` | Phase 5 (drive-list contract shape, Import seam), contract transcription cross-check — **reference evidence only, not default agent context** (doc-role split, archive §4.18) |
| `whisperer-30-reference/UI-CAPTURE-8b4b7b9/` | Phase 4 (frozen port source + classification manifest) — reference only, not default agent context |
| `whisperer-30-reference/STORE-DRIFT-MATRIX.md` | Phase 4 (store-wiring instruction set — captured store vs F3) — reference only, not default agent context |

---

## 17. Operational readiness — deferred gates (added 2026-08-06)

Applies **only before a private hosted beta or public demo — not Phase 1**. The Phase 1 slice stays local-first and single-user. Prevents the dangerous assumption that the first Cloud Run deployment is suitable for public traffic or multi-client data.

**Product modes (explicit decision deferred):**

| Mode | Intended user | Data allowed | Required controls |
|---|---|---|---|
| Local/private development | You | Test or authorized client data | Local encryption, `.env` hygiene, no public exposure |
| Private hosted beta | You / approved client users | Authorized client data | Auth, shared session store, audit/log policy, retention controls |
| Public demo | Portfolio visitors | Dummy or user-provided non-sensitive data only | No client data, legal copy, rate limits, abuse controls, deletion notice |

**Deferred gates (checkboxes):**

- [ ] **Product-mode decision:** local / private beta / public demo — explicitly chosen before any hosted deployment.
- [ ] **Auth/workspace isolation** defined before multi-user access — the hosted beta stays **single-user or explicitly invited-user only** until authentication, workspace isolation, and tenant authorization are implemented. Define workspace/dataset ownership; who can access, clear, export, or reconnect a data source; whether GA4/Drive OAuth credentials are user-, workspace-, or client-scoped; and how revoked access, client offboarding, and account deletion work.
- [ ] **Logging, backup, and error-reporting data-scrubbing policy** implemented — structured logs never contain raw rows, OAuth tokens, API keys, file contents, or Gemini prompt bodies; error reporting scrubs dataset names/identifiers; temp files and cached analysis outputs follow their source dataset's deletion policy; production backups have an explicit retention period and deletion process.
- [ ] **AI quota, rate-limit, and kill-switch controls** implemented — per-session request/token budget; max prompt/context size; rate limit by session or authenticated user; a kill switch that disables AI features while preserving upload/preview; and clear UI language that AI summaries are analytical assistance, not authoritative findings or causal conclusions (consistent with "deterministic computation first, model explains/prioritizes only").
- [ ] **Rollback path and accessibility/performance release checks** verified — Streamlit stays available privately while React/FastAPI stabilizes; feature flag or separate beta URL initially; rollback criteria (failed OAuth, failed upload/preview path, data-isolation bug, persistent AI errors, unrecoverable session loss) route users to Streamlit or disable only the affected FastAPI feature, never emergency code changes in production; accessibility baseline (keyboard-operable upload/Clear Data/filters/chat/dialog/sheet/export, focus returns on dialog/sheet close, non-color-only loading/empty/error/success/permission states, screen-reader labels for icon-only buttons, responsive at mobile/tablet/desktop, no regression of useful Streamlit flows); performance budgets (initial bundle <500 KB gzipped · interactive dashboard <2 s · preview <1 s · first streamed AI token <2 s).

**Security posture preference (recorded):** prefer **Workload Identity Federation** or managed runtime identities over long-lived service-account keys · managed secret storage for production values · least-privilege scopes documented separately for GA4, Drive, Gemini, and deployment · treat the tracked-`.env` incident as a learning artifact (rotate, remove, scan, don't reproduce the pattern).

**Explicitly out of scope for now (do not add):** SOC 2/compliance program · multi-tenant billing · enterprise RBAC · long-term data-warehouse schema · production Drive slide-out browse API · evidence-connector implementation · public-demo legal copy beyond a short future backlog item.

---

*This master plan was synthesized 2026-08-05 from the full `migration/` package and revised from review feedback (first pass: session store + upload architecture moved to Phase 0/1, canonical API decisions record, data-retention policy, three release gates; second pass: 25 MB upload cap, state-placement architecture, 8-gate priority checklist; third pass: gate 5a/5b split, locked 25 MB cap, staging precision; fourth pass 2026-08-06: local-first deployment posture, API-surface confirmation, Lovable update inventory §4.15; fifth pass 2026-08-06: Lovable semantic-layer fold-in — Drive browse-UX decision, second-contract guard, evidence-panel deferral, archive §4.16; sixth pass 2026-08-06: Lovable implementation-transcript fold-in — drive-list contract shape, Import gotcha, verified-faithful contract transcription, archive §4.17; seventh pass 2026-08-06: review refinement — metric-state policy, drive-list pagination, download trust boundary, prototype quarantine, browse-UX timing, archive §4.18; eighth pass 2026-08-06: gates 1/2/6 closed — credential remediation + `.env` untracked, migration branch + Streamlit freeze active, retention/AI-boundary approval, operational-readiness deferred gates §17, archive §4.26–4.28). It is planning-only: no migration product code was written and no commands executed. Each phase begins only on explicit approval, and per the addenda system, any later corrections append as dated addenda rather than rewriting this document.*
