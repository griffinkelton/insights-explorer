# Whisperer-30 Reference Capture — What Was Brought Over and Why

> **Source:** [`griffinkelton/insights-whisperer-30`](https://github.com/griffinkelton/insights-whisperer-30) (private) · **Branch:** `main` · **Commit:** `a71c3712` · **Captured:** 2026-08-05
> **Purpose:** reference material for the React/FastAPI migration. These are **design references, not code to be edited** — the full `src/` tree gets copied into the canonical repo at **Phase 4** of the migration plan, when the frontend build is reproducible.
> **Method:** files fetched via the GitHub API (base64-decoded) and stored **verbatim** — only a provenance banner was prepended (see "Provenance conventions" below). Nothing was paraphrased or trimmed.

---

## Why capture these now?

The migration docs (`migration/insights-explorer-migration-plan.md`, the F3 store-wiring prompt, F4 implementation packet, and the archive) reference the whisperer-30 app's shape, state model, chat behavior, and stack. Until Phase 4, this capture is the **only local record** of that design — and the Batch 3 Review Addendum already flags that the source repo's `.env` must be scrubbed before any copy-in, so a clean reference snapshot is valuable even before the real migration.

## What was captured (18 files)

| File (this folder) | Original path in whisperer-30 | Why it's here |
|---|---|---|
| `README.md` | `README.md` | The full **Lovable mega-prompt** — the complete design direction (layout, sidebar, dashboard, chat, dark-first tokens) that F3/F4 and the plan assume. |
| `lovable-plan-insights-explorer-ui-shell.md` | `.lovable/plan/insights-explorer-ui-shell-2026-08-03.md` | The plan doc: design system, page specs, mock-data shape, and the key note *"state lives in a client-side context provider so wiring a Python API later is a single swap of the data source functions"*. |
| `AGENTS.md` | `AGENTS.md` | Lovable-connected repo provenance (the canonical repo must NOT adopt Lovable history-rewriting rules). |
| `lovable-project.json` | `.lovable/project.json` | Template metadata (`tanstack_start_ts_current`). |
| `routes-README.md` | `src/routes/README.md` | TanStack Start file-based routing conventions — the reference for the Phase 4 port and the F4 callback route. |
| `src-lib-explorer-store.tsx` | `src/lib/explorer-store.tsx` | The **UI↔API contract seam** — the store F3 rewires; documents every data-source function that must become a `fetch()` call. |
| `src-routes-api-chat.ts` | `src/routes/api/chat.ts` | The **hardcoded BrainGuide system prompt** + chat endpoint shape. ⚠️ Batch 3 says this must NEVER become production logic — `utils/prompt_templates.py` stays canonical — but it is the behavioral reference for porting. |
| `src-lib-ai-gateway.server.ts` | `src/lib/ai-gateway.server.ts` | The Lovable AI-gateway provider — the thing Batch 3 says to replace with Python/FastAPI routing. Documents the wire shape to replace. |
| `src-lib-research-sources.server.ts` | `src/lib/research/sources.server.ts` | Evidence-connector design reference (aligns with `plans/evidence-connector-design.md`). |
| `src-lib-research-types.ts` | `src/lib/research/types.ts` | Evidence-connector types (paired with the sources above). |
| `src-lib-mock-ga4.ts` | `src/lib/mock-ga4.ts` | The GA4 mock data shape → becomes an **MSW test fixture**, not product code (Batch 3). |
| `src-lib-mock-braintree.ts` | `src/lib/mock-braintree.ts` | The BrainGuide mock data shape → MSW fixture (Batch 3). |
| `src-styles.css` | `src/styles.css` | The design system (oklch semantic tokens, dark-first) — reference for the light-mode / design work. |
| `package.json` | `package.json` | Exact dependency manifest (React 19, Vite 8, TanStack Router 1.170.x, `ai` SDK 7, Tailwind v4, Recharts, etc.) for Phase 4 planning and the npm/bun decision. |
| `bunfig.toml` | `bunfig.toml` | Bun configuration — evidence for the package-manager consolidation decision. |
| `vite.config.ts` | `vite.config.ts` | Vite/TanStack plugin config — the Phase 4 build setup reference. |
| `tsconfig.json` | `tsconfig.json` | TS config reference. |
| `components.json` | `components.json` | shadcn/ui config reference. |

## Deliberately NOT captured (and why)

| Excluded | Reason |
|---|---|
| **`.env`** | **Security** — verified tracked in whisperer-30 (62 B, commit `9059739`, no `.env.example`, no gitignore rule). Never propagate; rotate/revoke before Phase 4. |
| `bun.lock` | Regenerable from `package.json`; not reference material. |
| `src/components/**` (explorer + `ui/`) | The 14 explorer components + 35 shadcn/ui components are **code to migrate at Phase 4**, not reference docs. |
| `src/routes/*.tsx` (except `api/chat.ts`) | App routes (`index.tsx`, `learn.tsx`, `__root.tsx`) are Phase 4 code. |
| `src/lib/error-capture.ts`, `lovable-error-reporting.ts`, `error-page.ts`, `hooks/`, `utils.ts`, `router.tsx`, `server.ts`, `start.ts`, `routeTree.gen.ts` | Runtime glue / Lovable-specific error reporting / auto-generated file — handled in Phase 4. |
| `eslint.config.js`, `.prettierrc`, `.prettierignore`, `.gitignore`, `public/`, `.lovable/*` other than the plan + project.json | Tooling/assets not needed as reference. |

## Provenance conventions

- **`.md`** files get an HTML comment banner (`<!-- ... -->`); **`.ts`/`.tsx`** get `//` comments; **`.css`** gets `/* */`; **`.toml`** gets `#`. The banner records source repo, commit, capture date, and "reference only — do not edit."
- **`.json`** files (`package.json`, `tsconfig.json`, `components.json`, `lovable-project.json`) are **kept byte-clean** — a comment banner would invalidate the JSON. Their provenance lives in this index and in the parent `migration/README.md`.
- The captured commit is `a71c3712cb5228b477a9147770aac36faa70cb2c` (main, 2026-08-05).

## How this relates to the rest of `migration/`

- **F3 (`freebuff-prompt-wire-react-store.md`)** rewires `explorer-store.tsx` → see the captured `src-lib-explorer-store.tsx` for the exact seams.
- **F4 (`phase-1-api-react-callback-tests-implementation.md`)** describes the FastAPI backend → the captured `chat.ts` shows the endpoint shape the React side currently expects.
- **Batch 3 Review Addendum** (in the plan + F3/F4) explains *why* the `.env` is excluded and why the gateway/system prompt are reference-only.
- **`insights-explorer-migration-ingest.md` Part 2** holds the compiled verbatim record of the decision reviews; this folder is the *source-material* capture.

*Nothing in this folder is edited code — it is a frozen, dated reference snapshot. If whisperer-30 changes before Phase 4, re-capture deliberately rather than hand-editing these files.*
## Drift cross-check: captured `explorer-store.tsx` vs F3's 13 steps (2026-08-05)

Line-by-line read of the captured store against F3 (`freebuff-prompt-wire-react-store.md`) at their capture dates, to catch seams where the wiring prompt's assumptions don't match the actual file before Phase 4 executes it.

| F3 step | Captured store reality | Drift / action |
|---|---|---|
| 1. Remove mock imports | ✅ Matches — `import { defaultSource, type ChatMessage, type DataSource } from "./mock-ga4"` at the top; types must be extracted (note: the captured `ChatMessage` carries a `timestamp` field F3's sketch omits) | None — as expected |
| 2. Define `API_BASE` | No constant exists; `streamAi` calls relative `/api/chat` (the TanStack Start server route) | Expected — F3 adds it |
| 3. Replace `loadData()` | Captured `loadData(name?: string)` fakes a load with `setTimeout` + `defaultSource` | F3's `loadData(file?, source?)` signature supersedes; note the mock's `name` param has no API equivalent |
| 4. GA4 OAuth flow | No `connectGA4`/`handleGA4Callback` present | Expected — F3 adds; the callback now reads `status`/`reason` only (F3 Reconciliation item 7 + cross-check item 3) |
| 5. Drive Picker | No Drive code present | Expected — F3 adds; must read `{ token, appId }` (F3 cross-check item 1) |
| 6. `streamAi()` | ✅ Shape matches F3 (plain-text `getReader()`/`TextDecoder` accumulation) but targets relative `/api/chat` | Wire-format decision applies (archive §3.5): plain-text reader is valid only for `toTextStreamResponse()` / plain SSE |
| 7. Data fetchers | None present | Expected |
| 8. Export | None present | Expected |
| 9. `ExplorerValue` interface | Captured members: `loadData(name?)`, `failLoad`, `clearData`, `addFilter/removeFilter`, `addMetric/removeMetric`, `generateSummary`, `sendMessage`, `clearChat` — **F3's step-9 interface omits the filter/metric/sendMessage/clearChat members** | ⚠️ **Drift:** F3 step 9 must **union** — keep every existing member, then add the new ones (`connectGA4`, `handleGA4Callback`, `connectDrive`, `downloadFromDrive`, `fetchQuality/Charts/Forecast/Funnel`, `exportData`) **plus** `setSourceFromApi` (F4 §11). Do not replace the interface wholesale |
| 10. Chat route | `streamAi` targets `/api/chat` (server route) | F3 step 10's delete-or-proxy decision applies |
| 11. Cleanup | `mock-ga4`/`mock-braintree` imports present | As expected |
| 12. `api-types.ts` | No such file in the repo | F4 defines the wire types; normalize once in `setSourceFromApi` (F3 Batch 3 item 4) |
| 13. Env files | None present | As expected |

**Two extra findings beyond the 13 steps:**

1. **Hardcoded command prompts in `sendMessage`.** The captured store hardcodes `/help`, `/equity`, and `/funnel` prompt strings client-side. Batch 3's rule — preserve `utils/prompt_templates.py`, never let hardcoded client prompts become production logic — means these commands should be **server-driven** (`utils/commands.py`) in Phase 4, not kept as client constants.
2. **`useTheme()` persists `ie-theme` in localStorage.** That is a UI preference, not data — acceptable under the server-session rule (which bans raw data/provider tokens in localStorage, not preferences). Keep it.

Also note: chat context is windowed client-side today (`history.slice(-8)`). Decide in Phase 4 whether the server owns prompt-context assembly (recommended: client keeps the display window; server builds the prompt context from the session transcript).
