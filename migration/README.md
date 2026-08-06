# migration/ — React/FastAPI Migration Docs

Index for the migration decision material: moving the `insights-explorer` product from a Streamlit UI to a **React frontend (`insights-whisperer-30` components) + FastAPI backend** built on the existing Python `utils/` layer.

> **Status (2026-08-06):** all twelve documents ingested and cross-checked; research live-verified; corrections folded into the plan; **`master-plan.md` is the execution coordinator**. **Entry gates closed:** Gate 1 (credentials remediated — `.env` untracked, scans clean), Gate 2 (`feat/react-fastapi-migration` created + Streamlit feature freeze **active**), Gate 6 (retention/AI-boundary defaults approved). **The Phase 1 vertical slice (upload → preview → quality → clear) is unblocked.** Still **planning-only — no migration product code written**; implementation begins on `feat/react-fastapi-migration`. Indexed in [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md).

---

## The one-line decision

`insights-explorer` (Python) stays the **system of record**. `insights-whisperer-30` is a mock-data "UI shell" whose React components get adopted wholesale as the new frontend. A thin FastAPI layer exposes the existing `utils/` logic (GA4, Drive, Gemini, DataContext, forecasting, funnels, exports — 742 tests, 8,461 LOC) as HTTP endpoints. Streamlit retires incrementally after feature parity.

---

## The twelve documents

| File | What it is | Contents | Status |
|---|---|---|---|
| **`master-plan.md`** | **The execution coordinator — START IMPLEMENTATION HERE.** | Phases 0–6 with inputs/tasks/exit criteria, 5 cross-cutting workstreams (state, contract, tests, security, CI/CD), target repo file layout, critical-path dependencies, open decisions, consolidated risk register, doc→phase source map | 🔵 Plan (no code) |
| **`insights-explorer-migration-ingest.md`** | **The compiled archive** — the master record of everything provided and verified. Start here. | **Part 1** synthesis (decision, evidence chain, artifact map, batch 1–3 deltas) · **Part 2** verbatim source archive (11 pasted reviews + 4 file copies, URLs collapsed to `[URL1]`–`[URL5]`) · **Part 3** external research (hosting, OAuth/PKCE, Drive Picker, GA4 Data API, SSE/AI SDK, MSW/TanStack — live-verified 2026-08-05) · **Part 4** cross-check & reconciliation ledger (verified claims, contract reconciliation, batch-3 verification) | 🔵 Ingested |
| **`insights-explorer-migration-plan.md`** | **The 6-phase plan** — the actionable roadmap. | Executive summary, repo comparison, risk table, **Phases 1–6** (FastAPI skeleton → utils decoupling → wire real utils → port React UI → GA4 OAuth + Drive Picker → cutover/retire Streamlit), API contract draft, success metrics, open questions, next actions + 3 addenda + **Research Fold-In Log** | 🔵 Plan (no code) |
| **`freebuff-prompt-wire-react-store.md`** | **F3 — the frontend wiring prompt** (for an AI coding agent). | 13-step change list for `explorer-store.tsx`: remove mocks, real `fetch()` calls, GA4/Drive integration, SSE chat, typed client, `.env` files | 🟡 Reference |
| **`phase-1-api-react-callback-tests-implementation.md`** | **F4 — the Phase 1 implementation packet** (backend + OAuth callback + test strategy). | FastAPI vertical slice (config, session, schemas, upload/preview routes), GA4 OAuth start/callback adapters, React GA4 callback route, MSW-based test migration | 🟡 Reference |
| **`glm-5-2-vs-perplexity-migration-comparison.md`** | **GLM-5.2 vs Perplexity plan comparison** — how a second model would approach the same migration. | Approach differences, strengths, combined recommendation | ✅ Verified facts |
| **`session-state-inventory.md`** | **The `st.session_state` key inventory** — the written record Batch 3 recommended before any code changes. | All 44 keys: key → owner → lifecycle → FastAPI/React replacement, grouped by dataset / GA4 / Drive / chat / theme / test-only | 🔵 Ingested |
| **`dockerfile-pattern.md`** | **Phase 6 single-origin Docker pattern** — concrete deliverable sketch for the hosting amendment. | Multi-stage Dockerfile (Vite build → FastAPI runtime serving the SPA), SPA fallback route, platform notes, verification checklist | 🟡 Reference |
| **`env-rotation-checklist.md`** | **The `.env` rotation checklist** — Phase 0 security gate before any whisperer-30 code copy-in. | Verified `.env` facts, inspect → identify → rotate/revoke → remediate → prevent, verification checklist | 🔵 Planning |
| **`branch-and-freeze-policy.md`** | **Migration branch + feature-freeze policy** — Batch 3 process decision, written down. | Branch model (`main` vs `feat/react-fastapi-migration`), freeze rules, fix-forward rule, lift criteria, branch creation command | 🔵 Planning |
| **`test-layer-inventory.md`** | **Which of the 742 tests transfer** — substantiates the "tests won't transfer one-to-one" claim. | 742 = 452 utils-facing (keep) + 290 Streamlit-layer (rewrite/retire) + 40 Playwright; per-file transfer paths + Phase 6 checklist | 🔵 Ingested |
| **`data-retention-policy.md`** | **Retention & AI data-boundary rules** — written before the API exists (review feedback). | Upload retention, raw-frame persistence, session expiry, Clear Data semantics, export-logging retention, Gemini prompt allowlist, identifier removal/aggregation before AI calls | 🔵 Planning |

## Reference capture: whisperer-30 (`whisperer-30-reference/`)

Frozen, dated snapshot of the source UI repo (`griffinkelton/insights-whisperer-30`): the initial semantic capture @ `a71c3712` (2026-08-05) plus the **full source capture @ `8b4b7b9`** (2026-08-06, `UI-CAPTURE-8b4b7b9/`, 94 files, per-file port-classification manifest with `runtime_dependency` / `initial_mount` columns). Contents: the Lovable design prompt, the UI-shell plan, the explorer-store contract (F3's target — see [whisperer-30-reference/STORE-DRIFT-MATRIX.md](whisperer-30-reference/STORE-DRIFT-MATRIX.md), the Phase 4 store-wiring instruction set), the chat endpoint + BrainGuide system prompt (**reference-only — never production logic**), research types/sources, mock data shapes (→ MSW fixtures), and the stack/config manifest. See [whisperer-30-reference/WHISPERER-30-REFERENCE.md](whisperer-30-reference/WHISPERER-30-REFERENCE.md) for what was captured, why, and what was deliberately excluded (notably the tracked `.env`).

**Update 2026-08-06:** a second wave of Lovable commits (17 commits: Drive-import UI, `measurement-contract.ts`, evidence/GA4/insights panels) is inventoried in [whisperer-30-reference/LOVABLE-UPDATES-080525.md](whisperer-30-reference/LOVABLE-UPDATES-080525.md) — file-level changes only; plan implications pending. The sanitized full conversation export lives in `migration/archive/freebuff-conversation-080525.sanitized.md` — marked **SANITIZED — INTERNAL — DO NOT SEND TO EXTERNAL MODELS**.

---

## How they relate

```
                     ┌─────────────────────────────────────────────┐
                     │  insights-explorer-migration-ingest.md      │
                     │  (archive: ALL raw material + verification) │
                     └──────────────────────┬──────────────────────┘
                                            │ synthesizes + verifies
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
        ┌────────────────────┐   ┌──────────────────────┐   ┌──────────────────────────┐
        │ migration-plan.md  │   │ freebuff-prompt-     │   │ phase-1-api-react-       │
        │ THE 6-phase roadmap│   │ wire-react-store.md  │   │ callback-tests-...md     │
        │ (Phases 1–6)       │   │ (F3: frontend wiring)│   │ (F4: Phase 1 backend)    │
        └────────────────────┘   └──────────────────────┘   └──────────────────────────┘
                          ┌───────────────────────────────────────────────────┐
                          │ glm-5-2-vs-perplexity-migration-comparison.md     │
                          │ (independent audit lens — GLM facts verified)     │
                          └───────────────────────────────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
            ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
            │ master-plan.md   │   │ 7 support docs:  │   │ whisperer-30-        │
            │ EXECUTION        │   │ env-rotation ·   │   │ reference/ (captured │
            │ COORDINATOR      │   │ branch-freeze ·  │   │ UI capture, 94 files │
            │ (phases 0–6 +    │   │ session-state ·  │   │ files)               │
            │ cross-cutting +  │   │ test-layer ·     │   └──────────────────────┘
            │ file layout)     │   │ dockerfile ·     │
            └──────────────────┘   │ comparison       │
                                   └──────────────────┘
```

- **The archive is the source of truth.** Everything else derives from it; when docs disagree, the archive's **Part 4 ledger** records which choice is canonical.
- **The plan is the executable view.** It consumes the archive's research (Part 3) and reconciliation (Part 4) and folds them into its phase sections.
- **`master-plan.md` is the execution coordinator.** It sequences the phases (0–6), adds cross-cutting workstreams and the target file layout, and points each phase at its input docs — implement from it, consult the source docs for detail.
- **F3 and F4 are the two halves of implementation** — F4 builds the backend (Phase 1), F3 wires the frontend store (Phase 4). They share the same API contract, so the plan's contract section + Part 4 reconciliation keep them aligned.
- **The comparison doc is an audit artifact** — it informed the decision but drives no phases.
- **Two support docs feed the plan directly:** `session-state-inventory.md` (state-migration checklist for Phases 2/4) and `dockerfile-pattern.md` (hosting pattern for Phase 6).

---

## The addenda system (how updates layer on)

Every doc's original content is **preserved**; corrections/decisions are appended as dated addenda so history stays intact:

| Addendum | On which docs | What it adds |
|---|---|---|
| **External Research (2026-08-05)** | plan, F3, F4 | Source-backed findings: PKCE, Picker project number, chat wire format, funnel nuance, single-origin Docker, GA4 throttling — plus MSW v2 & TanStack Router v1 verified against live docs (one correction: MSW `onUnhandledRequest` default is `"warn"`, not `"bypass"`) |
| **Reconciliation (2026-08-05)** | plan, F3, F4 | Cross-doc contract fixes: `/healthz`, `authorization_url`, `{ dataset }` wrapper, `credentials: "include"`, `setSourceFromApi` |
| **Verification (2026-08-05)** | comparison doc | GLM-5.2 facts checked (1M context, ~1/10th cost, MIT) |
| **Batch 3 Review (2026-08-05)** | plan, F3, F4 | Product-platform migration review: **`.env` exposure** (tracked in whisperer-30 — rotate before copying), migration branch + feature freeze, server-owned session model, `/api/v1`, typed client, test-by-behavior matrix |
| **Research Fold-In Log (2026-08-05)** | plan | The 7 research corrections mapped into the phase sections (Phase 1/3/4/5/6 amendments) |
| **Research Fold-In Cross-Check (2026-08-05)** | F3, F4, plan, reference | Verifies the 7 corrections against F3's 13 steps and F4's code: F3 gains `{ token, appId }` for the Picker; F4 gains **PKCE in `begin_oauth()`** + **typed-search callback** (`validateSearch` / `errorComponent`); MSW `onUnhandledRequest: "error"` live-confirmed; plan Phase 5 gains the `VALIDATE_SEARCH` detail; reference gains the explorer-store drift cross-check |
| **Pre-Implementation Pack (2026-08-05)** | README, DOCIDX, archive | Two new docs — `.env` rotation checklist (Phase 0 security gate) and branch + feature-freeze policy (Batch 3 process decision) — plus archive §4.8 change log and index updates; first commit of the migration package to `main` |
| **Round 2 Research (2026-08-05)** | archive, plan, F3, F4, dockerfile | Live-verified round 2: GA4 quota/pagination numbers (10 concurrent/property, 250k rows/request max), Gemini SDK (`google-genai` + `thoughts_token_count`), AI SDK pin (`ai@^7.0.48` — corrects a research "v4" claim), bun-in-CI (`oven-sh/setup-bun@v2`) |
| **Round 3 Research (2026-08-05)** | archive, plan, F3, F4, dockerfile | Live-verified round 3: AI SDK v7 + `toTextStreamResponse` confirmed, Start/Lovable→Vite strip list, **Cloud Run path** (timeouts/session affinity/HTTP2), MSW streaming tests, Recharts×React 19, Python 3.14 floors (pandas≥2.3.3), Gemini model hygiene (2.0-flash shut down) |
| **Internal Reconciliation (2026-08-05)** | archive, plan, F4, dockerfile, new doc | Single 100 MB ingestion size policy (Drive/upload mismatch closed); field-level measurement-contract mapping; 742-test layer inventory (new doc); **Vercel hosting evaluation — SPA yes, FastAPI no** |
| **Master Plan (2026-08-05)** | new doc: `master-plan.md` | The execution coordinator — phases 0–6 with per-phase inputs/tasks/exit criteria, 6 cross-cutting workstreams, target file layout, critical path, open decisions, risk register, doc→phase map; README + DOCIDX re-indexed to eleven docs |
| **Master Plan Revision (2026-08-05)** | master-plan, F3, F4, plan, new doc | Review feedback folded in: session store + upload architecture moved to Phase 0/1 (32 MB browser cap / 100 MB server-side), canonical API decisions record in every implementation doc (`/api/v1`, `/healthz`, `{ dataset }`, cookie sessions), blocking-work + OAuth production-real guidance, chat reconnect, three release gates, new `data-retention-policy.md`, doc lifecycle + wording fixes |
| **ChatGPT Review Refinement (2026-08-05)** | master-plan, F3, F4, plan, archive | Upload cap locked at **25 MB** (direct) / 100 MB (Drive, with memory/MIME/row-count/decompression safeguards; HTTP/2 rejected for 100 MB browser uploads; signed Cloud Storage deferred); session decision reframed as **state placement** (cookie / ephemeral Redis-Valkey / shared store / Cloud Storage / memory cache / encrypted durable / Postgres-later) rather than one store; 8-gate priority checklist with owners + completion evidence added to Phase 0 |
| **Third Review Refinement (2026-08-05)** | master-plan, F3, F4, plan, archive, retention doc | Gate 5 split into **5a (lock state contracts — done)** / **5b (implement local stores — Phase 1 work)**; 25 MB upload cap made unambiguous (`25 * 1024 * 1024`) with a production-evidence revisit trigger; staging requirement scoped (shared OAuth/session store before Phase 5; object storage only if signed uploads chosen); gate-6 approval checklist added to `data-retention-policy.md` §11 |
| **Lovable Semantic Context (2026-08-06)** | LOVABLE-UPDATES §5, master-plan, archive | User-verbatim Lovable prompts behind the 17-commit update + code-verified panel semantics; **Drive browse-UX decision** (Picker iframe vs slide-out browse → `GET /api/v1/drive/list`); `measurement-contract.ts` second-contract guard (cross-cutting B); evidence panels kept out of the first slice (gate 8); archive §4.16 ledger |
| **Lovable Implementation Transcript (2026-08-06)** | LOVABLE-UPDATES §6, master-plan, archive | Lovable's raw build transcript captured (`LOVABLE-ACTIONS-080526.txt`); **drive-list contract fully specified** (search/browse query, pageSize, states); **Import gotcha** — prototype Import only fakes `loadData("drive · <name>")`, port must wire download→ingest; **`measurement-contract.ts` verified as a faithful transcription** of the canonical contract (5/5 rows); AI-boundary `context()` pattern maps to `utils/prompt_templates.py` |
| **Review Refinement — Lovable Fold-In (2026-08-06)** | master-plan, LOVABLE-UPDATES §6, archive | Four corrections folded in: **metric-state policy** (validated/provisional/unavailable → display/insights/Gemini; rename `computableMetrics()`), **drive-list pagination** (`next_page_token` + "Load more"), **download trust boundary** (`file_id` only, server-side MIME/size/Sheets-export enforcement), **prototype quarantine** (fixture-only paths, panels unmounted, "Demo / mock data" label); browse-UX decision moved to Phase 5 (Picker iframe recommended default); archive §4.18 |
| **Research Gap Round (2026-08-06)** | master-plan, LOVABLE-UPDATES §6, archive | Drive API v3 live-verified: `pageSize` max **1,000** (default 100), `nextPageToken` semantics, 1B req/day quota; **10 MB Google export cap** on native Sheets/docs; native files have **no `size` field**; **local cross-check: `utils/drive_client.py` already implements the full download trust boundary** — Phase 5 ports `download_drive_file`, it does not design it (risk High → mitigated); archive §4.19 |
| **Review — Path Drift + Policy Sync (2026-08-06)** | master-plan, canonical contract, archive | All bare `/api/` routes in the master plan versioned to `/api/v1/` (upload/data/analysis/ga4/drive); **metric-status policy synced** into `plans/ga4-measurement-contract.md` as the canonical home (master plan links to it); **quarantine layout** added to §12 (`test/fixtures/` + `handlers/` + `prototype/` with import-boundary rules); **paginated-OpenAPI deferred** to Phase 5 (decision #9); archive §4.20 |
| **Feedback Integration + UI Capture (2026-08-06)** | master-plan, F3, F4, sketch, archive, new capture | **Full UI source captured at `8b4b7b9`** (`UI-CAPTURE-8b4b7b9/`, 94 files) with per-file port classification manifest (Port/adapt · Reference · Fixture · Do-not-port); capture spec recorded in master-plan §12; **three-way doc status** recorded (contract = in-migration canonical; GA4 sketch + evidence connector = deferred workstreams); F3/F4 route drift fixed to `/api/v1` (prototype/archive allowlisted); metric policy cross-referenced into the GA4 sketch; conversation-export header upgraded (source SHA + CI-scan rule); archive §4.21 |
| **Review — Store Drift + Manifest Refinement (2026-08-06)** | MANIFEST, F3, master-plan, reference, archive | **Manifest refined** — `runtime_dependency` (none/mock/Lovable-Nitro/Python-FastAPI) + `initial_slice` (yes/no) columns added; `ChartsRow`/`DataPreview`/`Chat`/`EmptyHero` reclassified as **UI-shell ports** (shell copied, data source replaced), `EquityPanel` → prototype/reference unless a real equity API exists, `ResearchPanel` → reference only / deferred evidence workstream, `DriveImportSheet` → Phase 5 UI candidate only; **F3 proxy option removed** (direct `POST /api/v1/chat` + `credentials: "include"`); **package manager LOCKED — npm** (master-plan Phase 4, decision #3, CI `npm ci`); **new `STORE-DRIFT-MATRIX.md`** (captured store vs F3 — union interface, filter/metric server-sync, command-router move to `utils/commands.py`, timestamps, streamingId/reconnect); **Drive E2E acceptance matrix** added to Phase 5 (12 cases: OAuth cancel, forged-metadata rejection, Sheets export cap, token containment, …); archive §4.22 |
| **Review — Four Contradictions + Route Sweep (2026-08-06)** | master-plan, MANIFEST, STORE-DRIFT-MATRIX, F4, archive | **Phase 1 upload wording fixed** — `POST /api/v1/upload` is **25 MB** (`MAX_BROWSER_UPLOAD_BYTES`); 100 MB `MAX_INGEST_BYTES` is Drive/server-side-only; **`initial_slice` renamed `initial_mount`** (`functional`/`placeholder`/`deferred`) — first slice mounts only `functional` (+ optional `placeholder`) components; Chat, AiSummary, ExportMenu, OnboardingTour, Drive sheet, equity/research/evidence panels are `deferred`; **server-session language fixed in the drift matrix** (browser sends no dataset reference; payload `{ messages, mode }`; filter/metric changes synced via explicit API calls); **OAuth callback statuses locked** — `status=success` · `status=cancelled` (replaces `provider_denied`) · `status=error&reason=<code>` (`invalid_state` replaces `invalid_oauth_state`); **F4 addenda routes versioned to `/api/v1`** + 100 MB-policy addendum marked superseded; archive §4.23 |
| **Review — Local OAuth Verification + Trust-Boundary Wording (2026-08-06)** | STORE-DRIFT-MATRIX, archive | **OAuth vocabulary locally verified** with the reviewer's exact grep — `status=cancelled` / `invalid_state` are the only forms in active docs; `provider_denied` / `invalid_oauth_state` appear only in archive/verbatim transcripts and as explicit supersession notes (F4, master-plan §9) — the GitHub code-search hit was a stale index, not drift; **drift-matrix trust-boundary wording tightened** to the reviewer's exact formulation: the client sends only `credentials: "include"` (HttpOnly cookie — the sole browser-held identifier), **no session ID / dataset reference / raw data / provider token travels as request data**, FastAPI resolves session + active dataset server-side, filters/metrics sync via explicit API mutations, chat/summary payloads are `{ messages, mode }` + optional non-authoritative client state/version for stale-write detection; archive §4.24 |
| **Research-Gating Policy (2026-08-06)** | master-plan §11-G, archive §3.12 + §4.25 | **Research discipline adopted** — invoke the web/docs research agent only when an external platform decision is imminent; master-plan gains cross-cutting workstream **G** (timing map: GA4 + Gemini = High before Phases 5/3 · Drive/Picker = UX-dependent Phase 5 · Cloud Run = Phase 6 · React 19/Recharts = Phase 4 version re-check only); **"do not research again" allowlist** (25/100 MB policy, metric-status policy, `file_id`-only Drive boundary, quarantine rules, `measurement-contract.ts` faithfulness, fake Lovable Import, Phase 1 slice — all already live-verified); **four ready-to-use research prompts** recorded verbatim in archive §3.12 (GA4 feasibility · Drive slide-out · Gemini production · Cloud Run readiness); cross-check confirms the two genuinely open external gaps are GA4 dim/metric limits (risk item 7) and Drive shared-drive flags; archive §4.25 |
| **Review — Final Verdict + Gate 6 Approval (2026-08-06)** | data-retention-policy, master-plan, archive | **Reviewer final verdict:** migration package **execution-ready** — OAuth vocabulary, session trust-boundary wording, and 25 MB cap settled; remaining work is the three non-document gates; **Gate 6 CLOSED** — product owner approved all five §11 defaults 2026-08-06 (24 h session-scoped upload retention · 2 h idle / 12 h absolute session · Clear Data semantics keeping OAuth + theme · export metadata only, 30 days · Gemini allowlist-only with identifiers removed, provisional-caveat / unavailable-never-numeric synced to the metric-state policy); ⚠️ flags cleared in `data-retention-policy.md`; master-plan gate 6 → **APPROVED**; only **Gates 1 (credential rotation)** and **2 (branch + freeze)** remain — manual product-owner actions; archive §4.26 |
| **Review — Retention Wording + Operational Readiness (2026-08-06)** | data-retention-policy, master-plan, archive | **Effective Phase 1 upload retention corrected to ≤ 12 h** — deleted on Clear Data / idle timeout / absolute session expiry / process restart; effective retention = earlier of session expiry and `RETENTION_HOURS`; `RETENTION_HOURS` 24 h is an upper bound for a future persisted store, not a 24 h availability guarantee; **Gate 7 status fixed** — blocked by 1 and 2 only (Gate 6 approved; includes 5b); **GA4 research prompt gains the probe distinction** (docs facts vs property-specific facts requiring a post-OAuth compatibility probe) + compact research queue with exit artifacts (first dispatch = Gemini before Phase 3) + boundary rule (research never overrides canonical contract decisions without reconciliation); **new master-plan §17 Operational readiness — deferred gates** (product-modes table + 5 checkboxes: product-mode decision, auth/workspace isolation, log/backup/error-reporting scrubbing, AI quota/rate-limit/kill-switch, rollback + accessibility/performance) + security-posture preference + explicit out-of-scope list — applies only before hosted beta, not Phase 1; archive §4.27 |
| **Gates 1 & 2 Closed (2026-08-06)** | env-rotation-checklist, branch-and-freeze-policy, master-plan, archive | **Gate 1 DONE** — both exposed `AIzaSy…` keys classified as product-owner-owned (insights-explorer GCP), rotated/revoked + old keys invalid (user-confirmed ~2026-08-03); whisperer-30 tracked `.env` **untracked** (`2341c9c` on `fix/remove-tracked-env`, pushed) with `.gitignore` rules + `.env.example`; **history-wide secret scans clean in both repos** + guard exit 0; closure recorded without secret values; **Gate 2 DONE** — `feat/react-fastapi-migration` created + pushed from `main` @ `3769575`; **Streamlit feature freeze ACTIVE** (production/security fixes, CI/deploy fixes, docs only); **gate 7 (vertical slice) now unblocked**; archive §4.28 |
| **Phase 1 Authorized — Branch Sync + PR Scope (2026-08-06)** | master-plan, env-rotation-checklist, archive | **Reviewer unblock folded in** — `feat/react-fastapi-migration` fast-forwarded to `d1f6f6c` (branch current for Phase 1); **first-PR scope recorded** (FastAPI bootstrap · `/healthz` · config + safe env handling · SessionStore/DatasetStore interfaces + in-memory impls · upload 25 MB · context · preview · quality · **clear** · contract tests) with the keep-out list; **added the previously-omitted `POST /api/v1/data/clear`** to §5 tasks + exit criteria; **guard allowlist rule** (names-only validation: `API_SESSION_SECRET` · `API_CORS_ORIGINS` · `FRONTEND_URL` · `MAX_BROWSER_UPLOAD_BYTES` · `MAX_INGEST_BYTES` — no wildcards, no value trust); whisperer-30 `fix/remove-tracked-env` → `main` merge queued (non-blocking); archive §4.29 |

## Document lifecycle (active vs reference vs archive)

Classification from the master-plan review (2026-08-05) — how implementation should treat each doc:

| Class | Documents | Treatment |
|---|---|---|
| **Active** | `master-plan.md` · `session-state-inventory.md` · `test-layer-inventory.md` · `env-rotation-checklist.md` · `dockerfile-pattern.md` · `data-retention-policy.md` (+ `plans/ga4-measurement-contract.md` outside `migration/`) | Consulted during implementation; maintained |
| **Reference** | `freebuff-prompt-wire-react-store.md` (F3) · `phase-1-api-react-callback-tests-implementation.md` (F4) · `whisperer-30-reference/` | Read for implementation detail; prompts archive once their implementation PRs merge |
| **Archive** | `glm-5-2-vs-perplexity-migration-comparison.md` · `insights-explorer-migration-ingest.md` · `insights-explorer-migration-plan.md` | Audit trail / source of truth — read-only (archive gains only change-log appendices); the plan is superseded by `master-plan.md` for execution order |

## Suggested reading paths

- **New to the project (30 min):** README → plan §"Decision" + "Comprehensive Plan" → archive Part 1 (§1.1–1.2) → skim F4.
- **About to implement anything:** `master-plan.md` first (phase → inputs → tasks → exit criteria), then the phase's source docs.
- **About to implement Phase 1:** `master-plan.md` §5 → plan Phase 1 (with amendments) → F4 in full → F3 §3 (API base) → archive Part 4 §4.2 (canonical contract choices).
- **About to do OAuth/Drive (Phase 5):** plan Phase 5 amendments → archive Part 3 §3.2–3.4 → F4 OAuth section + Batch 3 addendum.
- **Reviewing the decision itself:** archive Part 1 (§1.1–1.8) + Part 2 verbatim pastes + comparison doc.

---

## Action items before implementation starts

1. ~~**Security:**~~ **DONE (Gate 1, 2026-08-06)** — credentials rotated/revoked (user-confirmed ~2026-08-03); whisperer-30 tracked `.env` untracked (`2341c9c`, branch `fix/remove-tracked-env`); `.gitignore` rules + `.env.example` added; history-wide scans clean in both repos. Closure record: `migration/env-rotation-checklist.md` (§ Gate 1 closure record).
2. ~~**Process:**~~ **DONE (Gate 2, 2026-08-06)** — `feat/react-fastapi-migration` created + pushed; **Streamlit feature freeze ACTIVE**. Policy: `migration/branch-and-freeze-policy.md` §4.
3. **Contracts:** adopt the Part 4 §4.2 canonical choices (`/healthz`, `authorization_url`, `{ dataset }` wrapper, `credentials: "include"`, `setSourceFromApi`, `/api/v1`).
4. **Fold-in complete:** the 7 research corrections are already in the plan's phase sections (see Research Fold-In Log).
5. **Frontend package manager:** **LOCKED — npm** (2026-08-06) — lockfile `frontend/package-lock.json`, CI install `npm ci`, local scripts `npm run dev/build/test`. (Master-plan Phase 4 + open decision #3.)

*All twelve files were moved here 2026-08-05 from the repo root and are indexed in [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) (section: React/FastAPI Migration).*
