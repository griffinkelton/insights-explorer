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

---

*Source data: `migration/lovable-commits.json` + `git show --stat --name-status` runs on `insights-whisperer-30` @ `8b4b7b9` (fetched 2026-08-06); panel semantics verified from `origin/main` source (2026-08-06). Compiled 2026-08-05/06.*
