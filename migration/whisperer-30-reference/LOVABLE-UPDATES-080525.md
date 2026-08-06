# Lovable Update Inventory — `insights-whisperer-30` (2026-08-06)

Commit-to-file-change inventory for the new UI features added to the source UI repo since the frozen capture. **File-level inventory only** — semantic analysis against the migration plans is a separate follow-up (see §4 "Initial read").

## 1. Scope & method

- **Repo:** `griffinkelton/insights-whisperer-30`
- **Range:** `a71c371` (the frozen capture HEAD, `WHISPERER-30-REFERENCE.md`) → `origin/main` (`8b4b7b9`), fetched 2026-08-06
- **Commits in range:** **17** (16 feature commits + 1 merge commit), all authored by Lovable bots between **2026-08-06 00:05–00:13 UTC**
- **Method:** the 9 commits in `migration/lovable-commits.json` were pre-inspected; the 8 `pending_commit_inspection` SHAs were verified locally with `git show --stat --name-status <sha>` after `git fetch origin` (the local clone was stale at `a71c371`).
- **Two bot streams:** `lovable-dev[bot]` (commits 1–9, Drive-import feature) and `gpt-engineer-app[bot]` (commits 10–17, evidence/GA4/insights panels).

## 2. Per-commit inventory (17 commits, oldest → newest)

| # | SHA (short) | Time (UTC) | Message | Files changed (+/−) |
|---|---|---|---|---|
| 1 | `88bea9a` | 00:05:14 | Work in progress | M `src/routeTree.gen.ts` (+10) — *generated* |
| 2 | `36c1e9a` | 00:05:48 | Changes | A `src/lib/research/drive-browse.server.ts` (88) · A `src/routes/api/drive-files.ts` (17) |
| 3 | `0ef1046` | 00:06:35 | Changes | A `src/components/explorer/DriveImportSheet.tsx` (305) · M `src/routeTree.gen.ts` (+27/−3) |
| 4 | `5e85650` | 00:06:43 | Changes | M `src/components/explorer/Sidebar.tsx` (+4/−1) · M `src/routeTree.gen.ts` (−10) |
| 5 | `cf422a9` | 00:06:54 | Changes | M `src/routeTree.gen.ts` (+10) — *generated* |
| 6 | `3f9c56e` | 00:06:58 | Changes | M `src/routeTree.gen.ts` (−10) — *generated* |
| 7 | `3059a0f` | 00:07:01 | **Added import from Drive sidebar** | **Aggregate of the Drive-import feature**: A `DriveImportSheet.tsx` (305) · M `Sidebar.tsx` (+4/−1) · A `drive-browse.server.ts` (88) · M `routeTree.gen.ts` (+27/−3) · A `routes/api/drive-files.ts` (17) — 441 insertions |
| 8 | `e963394` | 00:09:50 | Changes | A `src/lib/measurement-contract.ts` (110) |
| 9 | `e4d1adb` | 00:10:27 | Changes | A `src/lib/evidence/mock-evidence.ts` (174) · M `src/routeTree.gen.ts` (+10) |
| 10 | `95fdb9b` | 00:11:27 | Changes | A `src/lib/insights/engine.ts` (296) · M `src/routeTree.gen.ts` (−10) |
| 11 | `ff841e8` | 00:11:51 | Changes | A `src/components/explorer/InsightCandidates.tsx` (137) |
| 12 | `def46f0` | 00:12:09 | Changes | A `src/components/explorer/MeasurementContractPanel.tsx` (109) |
| 13 | `a0614ae` | 00:12:35 | Changes | A `src/components/explorer/EvidenceConnectorPanel.tsx` (152) |
| 14 | `e117397` | 00:12:43 | Changes | M `src/lib/research/sources.server.ts` (+10/−1) · M `src/lib/research/types.ts` (+2/−1) |
| 15 | `84eecfd` | 00:12:54 | Changes | M `src/lib/research/sources.server.ts` (+19/−1) · M `src/routes/index.tsx` (+6) |
| 16 | `561cafe` | 00:13:05 | Changes | M `src/routes/api/research.ts` (+5/−2) |
| 17 | `8b4b7b9` | 00:13:20 | **Added evidence and GA4 panels** | **Merge commit** (parents `3059a0f`, `561cafe`) — no file changes of its own |

## 3. Deduplicated final-state file inventory

What actually changed in the working tree between the capture (`a71c371`) and `origin/main` (`8b4b7b9`), excluding the generated `routeTree.gen.ts`:

### New files (9, ≈1,388 product lines)

| File | Lines | Group |
|---|---|---|
| `src/components/explorer/DriveImportSheet.tsx` | 305 | **Drive import UI** |
| `src/lib/insights/engine.ts` | 296 | Insights engine (evidence/GA4 branch) |
| `src/lib/evidence/mock-evidence.ts` | 174 | Evidence prototype **fixture** |
| `src/components/explorer/EvidenceConnectorPanel.tsx` | 152 | Evidence-connector UI |
| `src/components/explorer/InsightCandidates.tsx` | 137 | Insights candidates UI |
| `src/lib/measurement-contract.ts` | 110 | **TS measurement contract** ⚠️ |
| `src/components/explorer/MeasurementContractPanel.tsx` | 109 | Measurement-contract UI |
| `src/lib/research/drive-browse.server.ts` | 88 | Drive-browse **server adapter** (Nitro) |
| `src/routes/api/drive-files.ts` | 17 | Drive-files **server route** (Nitro) |

### Modified files (5)

| File | Change | Group |
|---|---|---|
| `src/components/explorer/Sidebar.tsx` | +4/−1 | Drive-import entry point |
| `src/lib/research/sources.server.ts` | +29/−2 (2 commits) | Research sources adapter |
| `src/routes/index.tsx` | +6 | Main route (panel wiring) |
| `src/routes/api/research.ts` | +5/−2 | Research API route (Nitro) |
| `src/lib/research/types.ts` | +2/−1 | Research types |

### Generated (do not port)

- `src/routeTree.gen.ts` — regenerated repeatedly across commits; never port manually.

## 4. Initial read for the migration plans (to be confirmed)

1. **Drive import** (`DriveImportSheet` + `Sidebar` trigger + `drive-browse.server.ts` + `api/drive-files.ts`) — the React UX/state patterns map directly to master-plan **Phase 4/5**; the Lovable/Nitro server routes must be replaced by FastAPI `/api/v1/drive/*` backed by `utils/drive_client.py` (keep the existing size/MIME/error-taxonomy/credential safeguards).
2. **`measurement-contract.ts`** ⚠️ — a second, competing measurement contract. Compare line-by-line against the canonical `plans/ga4-measurement-contract.md` before reusing anything; prefer generating TS types from the canonical Python/OpenAPI contract (master-plan cross-cutting B).
3. **Evidence/GA4/insights panels** (`EvidenceConnectorPanel`, `InsightCandidates`, `MeasurementContractPanel`, `insights/engine.ts`, `mock-evidence.ts`, research-source changes) — these are **prototype artifacts of the deferred evidence-connector workstream** (`plans/evidence-connector-design.md`). Keep evidence work out of the first vertical slice (master-plan gate 8); `mock-evidence.ts` → MSW fixture material only.
4. **Server routes** (`drive-files.ts`, `research.ts`, `drive-browse.server.ts`) — Lovable/Nitro-only; non-canonical until reconciled with the master plan (same treatment as the existing `ai-gateway.server.ts`).
5. **Merge structure** — `8b4b7b9` merged a gpt-engineer evidence/GA4 branch into main; the Drive-import aggregate is `3059a0f`.

## 5. Semantic layer — what Lovable was told + verified behavior (2026-08-06)

Supplement to §4 from the user's follow-up: the Lovable prompts behind these commits, plus the behavior verified directly from `origin/main` source.

### 5.1 What Lovable was asked to build (user verbatim)

- **Drive import:** *"Create an 'import from Drive' selector as in sidebar, modal, slide out. Whatever you think is best."* → Lovable delivered a **right-side slide-out** with search, folder breadcrumbs, file metadata, open-in-Drive links, and connected/empty/permission/error states.
- **Evidence connector / GA4 / insights panels:** asked with `plans/evidence-connector-design.md`, `plans/ga4-measurement-contract.md`, `plans/ga4-insights-sketch.md` shared → Lovable added three dashboard panels **on realistic mock data**, wired into the research/AI flow.

### 5.2 Verified implementation semantics (from `origin/main` source)

| File | Verified semantics |
|---|---|
| `DriveImportSheet.tsx` | Direct browser slide-out browse (search + breadcrumbs + metadata); fetches `/api/drive-files?q\|folderId` through the Lovable gateway — **non-canonical** Nitro route |
| `EvidenceConnectorPanel.tsx` | `evidenceGates`, `lastSync`/`linkageCoverage` (SyncRecord metadata), manual `runSync` (`phase: "idle" \| "syncing"`), gate-tone mapping |
| `InsightCandidates.tsx` | Deterministic trust layer: categories (all/equity/funnel/access/reach/quality/change), `uncertainty` tones, **Caveats**, **Provenance** (source · metric · `metricStatus` incl. `unavailable`) |
| `MeasurementContractPanel.tsx` | All five metric rows with **Numerator/Denominator**, `grain`, validation counts (provisional/unavailable); "No metric reaches the insights layer or the model until it has a row here. Unavailable rows are never presented as measured." |

### 5.3 Implications for the migration plans

1. **Drive browse UX is now a Phase 5 decision** — Google **Picker iframe** (existing `drive_picker_component_frontend/` behavior) **vs the Lovable slide-out browse**. The slide-out needs server-side Drive metadata listing (`GET /api/v1/drive/list?q=&folder_id=` on FastAPI, backed by `utils/drive_client.py`); the prototype's Nitro `/api/drive-files` route is non-canonical (same treatment as `ai-gateway.server.ts`). Master-plan Phase 5 updated.
2. **The three panels are mock-driven prototypes of the deferred evidence-connector workstream** (`plans/evidence-connector-design.md`) — keep out of the first vertical slice (master-plan gate 8); `mock-evidence.ts` → MSW fixture material only.
3. **`measurement-contract.ts` is a second competing contract** — must be diffed against the canonical `plans/ga4-measurement-contract.md`; TS types should come from the canonical Python/OpenAPI contract, never from this file.
4. **"Gemini only prioritizes and explains, never calculates"** (Lovable's own framing of the insights engine) aligns with the plan's stance: deterministic trust-layer logic lives in Python; Gemini's role stays advisory.

## 6. Implementation transcript — distilled facts (2026-08-06)

Raw transcript of what Lovable actually did (build actions + full file dumps): **`migration/whisperer-30-reference/LOVABLE-ACTIONS-080526.txt`**. This section distills the implementation-level facts that matter for the port.

### 6.1 Drive browse — exact contract shape (from `drive-browse.server.ts` + `api/drive-files.ts`)

- **Gateway:** `https://connector-gateway.lovable.dev` proxying Drive API v3 `files.list`; auth via `LOVABLE_API_KEY` + `GOOGLE_DRIVE_API_KEY` env vars — **all non-canonical** (must be replaced by FastAPI + `utils/drive_client.py` server-side calls).
- **Query (search or folder browse):** `trashed = false` AND (`name contains '<term>'` **or** `'<folderId>' in parents`, default `root`); `pageSize: 50`; `orderBy: folder,modifiedTime desc`; `fields: files(id,name,mimeType,modifiedTime,size,webViewLink,iconLink)`.
- **State machine:** `BrowseState = "ready" | "not_configured" | "permission" | "error"`, each with `message` and `setupHint` (e.g. not_configured → "Connect the Google Drive connector… grant read access"; 401/403 → `permission` → "include the drive.readonly scope"). HTTP: `502` on error state, else `200`.
- **Slide-out UX (`DriveImportSheet.tsx`):** right-side `Sheet` (max-w-md); search input with 350 ms debounce; folder breadcrumb path state (`[{id:"root",name:"My Drive"}]`); file/folder icons by MIME; `isTabular()` gate (google-spreadsheet / spreadsheetml / `text/csv` / `.(csv|xlsx?|tsv)` name); size + modified-date formatting; open-in-Drive links; double-click or footer Import to select; Cancel/Import footer with loading state.
- **⚠️ Critical gotcha for the port:** `importFile(file)` calls `loadData("drive · ${file.name}")` and closes the sheet — **it does NOT download or ingest the file**. The prototype's Import button only sets the mock store's source name. In the React port, Import must be wired to a real `POST /api/v1/drive/download` → `data_loader` → dataset flow (master-plan Phase 5).
- **Sidebar wiring:** `driveOpen` state, `onClick={() => setDriveOpen(true)}` replacing the old hardcoded `loadData("drive · ga4_q1_export.xlsx")` button, `<DriveImportSheet open={driveOpen} onOpenChange={setDriveOpen}/>`. Note in the transcript: the mobile drawer renders `SidebarContent` twice → duplicate sheet instances (independent state, works).

### 6.2 The three panels — all mock-data driven

- **`measurement-contract.ts` (110 lines)** — a **faithful TS transcription of the canonical `plans/ga4-measurement-contract.md`**: all 5 metric IDs match (`daily_reach`, `page_device_engagement_rate`, `questionnaire_start_count`, `questionnaire_completion_rate`, `post_questionnaire_action_rate`), statuses match (provisional ×2, unavailable ×3), and numerator/denominator/grain/eventMapping/blockedBy/limitations match row-for-row. Adds helpers `computableMetrics()` (filters `unavailable`) and `contractContext()` (the governance RULE string fed to the model). **Cross-checked 2026-08-06 against the canonical doc — verified faithful.** ⚠️ **Policy nuance (2026-08-06):** `computableMetrics()` filters only `unavailable`, so it admits **provisional** rows into model-visible context — contradicting the doc's "no metric until `validated`" wording. The insight engine also cites `unavailable` metrics in findings (with caveats). Acceptable in a prototype; the product needs an explicit metric-state policy (master-plan cross-cutting B) and a clearer helper name (`modelVisibleMetrics()` / `nonUnavailableMetrics()`).
- **`mock-evidence.ts` (174 lines)** — BrainGuide Evidence dashboard mock: `SMALL_CELL_MIN = 50`; `EVIDENCE_SOURCE` (Playwright DOM extraction, "Phase A — manual sync, session-only, no retained raw extracts"); `evidenceCatalog` (8 datasets — 5 allowlisted aggregates; `questionnaire_responses` person-level 12,988 rows and `questionnaire_journey_events` 214,300 rows **never synced**; `questionnaire_journey_monthly` aggregate-but-not-yet-allowlisted); `SyncRecord` (manifestHash/schemaFingerprint/checksum/outcome `synced|skipped|quarantined`); `linkageCoverage` 78% (join key "de-identified questionnaire session hash", cohort below threshold: Spanish n=42); `evidenceGates` (2.1–2.6 unlocked, 2.7–2.8 & 3.1 phase-b, 1.6 & 1.7 blocked); `evidenceContext()`.
- **`insights/engine.ts` (296 lines)** — deterministic candidate engine: `buildInsightCandidates()` computes ~8 candidate types (equity gaps, language-access small-cell, funnel drop-off, device gap, channel quality, relaunch change, race/ethnicity equity) with `uncertainty` (high-confidence/directional/descriptive-only), `suppressed` (small-cell), `priority`, and per-candidate provenance (source · metric · metricStatus · grain). `insightContext()` is explicitly "PRECOMPUTED INSIGHT CANDIDATES (deterministic — do not recalculate, reprioritize and explain only)" — **the model's ONLY numeric input**.
- **Wiring (`sources.server.ts`, `index.tsx`, `types.ts`):** `SourceId` gains `"evidence"`; GA4 source context = `buildDataContext()` + `contractContext()`; evidence source context = `evidenceContext()` + `insightContext()`; panels mounted on `index.tsx`.

### 6.3 Implications for the migration plans

1. **`GET /api/v1/drive/list` contract is now fully specified** by the prototype: params `q` (search) / `folder_id` (browse), response `{ state, message?, setupHint?, files: [{id,name,mimeType,modifiedTime,size,webViewLink,iconLink}] }`, states `ready|not_configured|permission|error`. FastAPI replaces the gateway with real Drive API calls; `not_configured` → no credentials, `permission` → 401/403 → reconnect + `drive.readonly` scope, `error` → everything else. Master-plan Phase 5 updated.
2. **The Import action is the real integration seam** — the prototype only fakes it; Phase 5 must wire Import → download → ingest.
3. **The `context()` serialization pattern** (`contractContext()` / `evidenceContext()` / `insightContext()` → model context) is exactly the AI-boundary pattern to preserve: deterministic text assembled from a single source of truth, model never recalculates. Maps to `utils/prompt_templates.py` in the port.
4. **Second-contract guard is now resolved:** `measurement-contract.ts` is a verified-faithful transcription of the canonical contract (5/5 rows match). Canonical `plans/ga4-measurement-contract.md` remains the single source of truth (Python/OpenAPI origin); the TS file is safe to reuse as a reference transcription but not as the authoritative contract.
5. **Evidence connector mock details** (allowlist, sync records, 78% linkage, small-cell rule) are design-reference material for the deferred evidence-connector workstream — keep out of the first slice (master-plan gate 8).
6. **Pagination gap (2026-08-06; live-verified Drive API v3):** the prototype's list has `pageSize: 50` but **no continuation token** — folders >50 entries silently truncate. The port adds `page_token` (request) + `next_page_token` (response, opaque string or null; omitted = no more pages) + a "Load more" affordance. Live-verified: `pageSize` max is **1,000** (default 100), so 50 is safe but raisable; default quota (1B requests/day, 20k/100s per user) is far above this app's needs.
7. **Download trust boundary (2026-08-06) — ALREADY IMPLEMENTED in the Python repo:** the sheet's MIME/name checks are UX guidance only, never the security authority. The required behavior exists in `utils/drive_client.py` (`download_drive_file`): accept `file_id` only, server-authoritative `files.get(fields="name,mimeType,size")`, `DRIVE_IMPORT_MIME_TYPES` allowlist, Sheets `export_media(mimeType="text/csv")` first-sheet-only, 3-layer size enforcement (metadata preflight → `_BoundedBytesIO` stream cap → final `len()` check), typed `DriveImportError` codes. Live-verified nuances: **Google-native files have no `size` metadata field** (why the stream cap exists) and Google imposes a **10 MB export cap** on Sheets/docs — Sheets imports can never approach 100 MB.
8. **Prototype quarantine (2026-08-06):** `mock-evidence.ts` + the deterministic engine stay under test/fixture or prototype-only paths, never runtime production sources; panels not mounted in the first production slice; "Demo / mock data" label in design previews; mock sources never registered in the production source registry.

---

*Source data: `migration/lovable-commits.json` + `git show --stat --name-status` runs on `insights-whisperer-30` @ `8b4b7b9` (fetched 2026-08-06); panel semantics verified from `origin/main` source (2026-08-06); implementation transcript `LOVABLE-ACTIONS-080526.txt` (2026-08-06); contract transcription cross-checked against `plans/ga4-measurement-contract.md` (2026-08-06). Compiled 2026-08-05/06.*
