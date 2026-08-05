# Insights Explorer → React/FastAPI — Compiled Context Archive

> **What this file is:** a single ingest/archive of everything provided for the *"which repo is the base?"* migration decision — 11 pasted AI-assistant chat records and 4 repo documents, kept **verbatim** in Part 2, plus a synthesis of what it all means and how the pieces fit together in Part 1.
>
> **Batch 2 (appended 2026-08-05):** the frontend-wiring prompt, a deeper repo inspection, and the Phase 1 implementation packet — see §1.10–1.12. **Part 3** adds source-backed external research (2026-08-05). **Part 4** adds the cross-check & reconciliation ledger (2026-08-05).
> **Batch 3 (appended 2026-08-05):** the product-platform migration review (PASTE 11) — see §1.13, Part 4 §4.6, and the per-doc Batch 3 addenda.
>
> **Compiled:** 2026-08-05 · **Status:** 🔵 Ingested for later work — **no plan and no code changes made.**
>
> **Companion docs on disk** (also copied verbatim into Part 2): `insights-explorer-migration-plan.md` · `glm-5-2-vs-perplexity-migration-comparison.md` · `freebuff-prompt-wire-react-store.md` · `phase-1-api-react-callback-tests-implementation.md`

---

## Part 1 — Synthesis: what this means and how it all fits together

### 1.1 The story in one paragraph

One decision session asked the strategic question: *which repo is the base — the mature Python/Streamlit `insights-explorer`, or the two-day-old Lovable-built React `insights-whisperer-30`?* Every review of that session — Perplexity's assistant (four separate analyses), a GLM‑5.2‑style simulation, and the compiled planning work — converged on the **same answer**:

> **`insights-explorer` remains the canonical product repo. `insights-whisperer-30` is a disposable "UI shell" whose React components get adopted wholesale as the new frontend. A thin FastAPI layer exposes the existing `utils/` logic as HTTP endpoints. Streamlit is retired incrementally once feature parity is reached.**

No source recommended switching bases, rebuilding the UI from scratch, or embedding React inside Streamlit.

### 1.2 The decision — unanimous across all sources

| Option | Verdict | Why |
|---|---|---|
| **A. `insights-explorer` stays the base** | ✅ Recommended (all sources) | Hardened backend: GA4 OAuth + reporting, Drive download guards + error taxonomy, DataContext state machine, Gemini streaming, forecasting/funnels/quality/exports, 742 unit + 32 Playwright tests, CI, pre-commit, release process. Refactor cost is bounded. |
| **B. `insights-whisperer-30` becomes base** | ❌ Rejected | Loses tests, CI, docs, and repo history; the Python backend would need full re-import into a TS/Bun repo. Same end state, strictly more work. |
| **C. Rebuild the React UI from scratch** | ❌ Rejected | The UI already exists, is owned by the user, and its own README calls it "the ideal UI shell" for this backend. |
| **D. Embed React inside Streamlit** | ❌ Rejected | Worst of both worlds — Streamlit's constraints persist, plus cross-frame complexity. |

**Bottom line (all sources):** keep the Python repo as the system of record; import the polished React UI as a new frontend; add a proper API boundary; retire Streamlit after parity. Port, don't rebuild.

### 1.3 Why it's well-supported — the evidence chain

1. **Direct repo inspection, not guessing.** The Freebuff session hit a 404 on anonymous API access, correctly inferred the repo was private, then used the authenticated `gh` CLI to pull the file tree, README, plan doc, `package.json`, and key source files.
2. **The smoking gun.** `insights-whisperer-30`'s own README contains the user's original Lovable mega-prompt, which says: *"the backend logic stays in Python… this is a UI shell that would eventually connect to that Python backend via API."* The question had already been answered two days earlier when the prototype was built.
3. **A quantified, falsifiable claim.** Only **7 of 16** `utils/` files import Streamlit, and those imports are shallow (cache decorators, `session_state` reads, styles, error_boundary) — the rest are functions + dataclasses with no UI coupling.
4. **"Switch base to React" ruled out cleanly.** Reading `ai-gateway.server.ts` and `chat.ts` confirmed the whisperer app's only live call is a chat proxy through Lovable's AI gateway over mock data — no real GA4, OAuth, or Drive.
5. **The store was built for the swap.** `explorer-store.tsx` deliberately keeps state in a client-side context provider so wiring a real Python API later is a single swap of the data-source functions.

### 1.4 Artifact map — who made what, and its role

| Artifact | Origin | Role in the workstream |
|---|---|---|
| `insights-explorer-migration-plan.md` | Perplexity-compiled (Freebuff session + repo inspection + multi-perspective review) | **Project document.** 6 time-based phases (Week 1–6), success metrics, 5 open questions, draft API contract in TypeScript interfaces. The chat record also produced GitHub issues 1–6 and a FastAPI skeleton prompt. |
| `glm-5-2-vs-perplexity-migration-comparison.md` | Simulated GLM‑5.2 analysis (model not directly invoked) | **Implementation-audit lens.** Dependency-layer sequencing (Layer 0–3 by import depth), JSON Schema API contract, per-file refactor notes, line-level risk annotations. |
| Paste records 1–7 (Part 2) | The AI-assistant conversations that produced the above | **Raw reasoning trail.** Review → endorsement → verification → deep-dive ("API layer first") → compiled plan → GLM comparison → actionable issues + scaffold prompt. |

### 1.5 How the pieces fit together

- The **Freebuff session** produced the recommendation plus the evidence.
- **Four Perplexity analyses** stress-tested it (all agree; one added the *"do the API layer first, not the UI port"* sequencing; one added the honest correction in §1.6).
- The **GLM‑style analysis is the complement, not a competitor**: Perplexity's plan = shareable project doc for stakeholders and sprints; GLM-style = code-level audit to feed implementation. **Recommendation: use both.**
- **Phase ↔ dependency-layer mapping** (from the comparison doc):
  - Phase 1 (API contract + skeleton) ↔ **Layer 0–1** (no-dependency + data-only utils: sanitize, funnels, commands, data_context, ga4_client, drive_client, charts, report_exporter)
  - Phase 2 (extract framework-neutral services) ↔ **Layer 2** (data_loader, forecasting, gemini_client, prompt_templates)
  - Phase 4 (port React UI) ↔ **Layer 3** (UI-coupled: session, styles, error_boundary, components/*)
  - Phase 6 (cutover) ↔ full graph traversed
- The **GitHub issues 1–6** turn the 6 phases into trackable tasks with acceptance criteria; the **FastAPI skeleton prompt** is the ready-made handoff to a coding assistant for Phase 1.

### 1.6 The honest correction + two costs to keep visible

> *"utils are framework-free"* is directionally right but **literally wrong**: 7/16 `utils/` files import Streamlit. Extraction must be a deliberate **boundary-refactor** (pull cache decorators, `session_state` reads, styles, and error handling out of domain services), not a blind wrap-and-expose.

Two costs the analysis flagged as easy to underweight:

1. **Hosting changes are a real project.** Streamlit Community Cloud cannot run FastAPI + React, so the migration forces a hosting decision (Railway/Render/Fly) — a separate workstream, not a footnote.
2. **The "742 tests" figure doesn't survive unchanged.** Streamlit-layer UI tests must be retired/rewritten as API-contract tests + React E2E tests; only `utils/` domain tests carry over as-is.

### 1.7 Decided vs. still open

**Decided (unanimous):** base repo = `insights-explorer` · adopt whisperer-30's React UI · FastAPI bridge over `utils/` · incremental Streamlit retirement · port rather than rebuild · no React-in-Streamlit embedding.

**Open (the plan's 5 questions + 2 flagged costs):**
1. Hosting platform — Railway, Render, or Fly?
2. Session storage — Redis, PostgreSQL, or in-memory?
3. Lovable AI gateway — keep as optional fallback or remove entirely?
4. Streamlit fallback — keep ~1 week or decommission immediately?
5. Repo structure — `frontend/` + `api/` as siblings, or nested?
6. (Flagged) Hosting-migration effort — track as its own line item.
7. (Flagged) Streamlit-test retirement — track visibly so "742 tests" doesn't create false post-migration confidence.

### 1.8 Ties to the rest of the repo (context for later cross-referencing — not a plan)

- **`ROADMAP.md`** sequences v0.4.0 (Gates 0A/0B) → v0.5.0 (Gate 1) → v0.6.0 (Gate 2) → v0.7.0 (Gate 3) and names the **hard blocker**: `pull_ga4_report()` is aggregate-only — no event-level/session/identifier data.
- **`braintree-reqs.md` / `BRAINTREE_CHECKLIST.md`** — Top‑25 analysis feasibility: **4 available / 2 partial / 19 unavailable**, most blocked on the event-level GA4 gap.
- **`plans/🔵 evidence-connector-design.md`** — BrainGuide Evidence dashboard connector: the SPA (S3 + CloudFront) serves the same HTML shell on every path, so parquet files are not directly fetchable; a headless-browser auth+scrape or a direct data export is required.
- **Interstitial UI polish (v0.3.0 → v0.4.0)** — Workstream A (Picker in `st.dialog`) ✅, Workstream B (light mode) ✅, Workstream C P0 (cancel/toast/copy, PR 3) ✅, C P1 (C4–C7) still open.
- The React/FastAPI migration discussed here is the container in which much of that roadmap work would eventually land. **Cross-reference only — no plan is drawn in this file.**

### 1.9 Source provenance

| # | Source | One-line summary |
|---|---|---|
| P1 | Paste 1 (Perplexity) | Review of the Freebuff session; endorses "keep Python repo as base"; notes inspection cut off mid-exploration. |
| P2 | Paste 2 (Perplexity) | Endorses the strategic framing; proposes listing components → endpoints → transition strategy. |
| P3 | Paste 3 (Perplexity) | Verified-work recap with evidence table; flags hosting cost + Streamlit-test retirement. |
| P4 | Paste 4 (Perplexity) | Deep-dive: "do the API layer first, not the UI port"; 3-phase sequencing; 7/16 Streamlit correction. |
| P5 | Paste 5 (Perplexity) | Compiled 6-phase plan summary; repo contents; risks; next steps. |
| P6 | Paste 6 (Perplexity) | GLM 5.2 vs Perplexity comparison; "use both" recommendation. |
| P7 | Paste 7 (Perplexity) | GitHub issues 1–6 (full text) + FastAPI skeleton prompt for Freebuff. |
| F1 | `insights-explorer-migration-plan.md` (file) | Full 6-phase plan with API contract draft, success metrics, open questions. |
| F2 | `glm-5-2-vs-perplexity-migration-comparison.md` (file) | Full comparison doc with simulated GLM plan outline. |
| P8 | Paste 8 (Perplexity) | Cover note for `freebuff-prompt-wire-react-store.md`: the 13 store changes, key design decisions, gaps. |
| P9 | Paste 9 (Perplexity) | Deeper repo inspection: 8 findings + updated 10-item checklist (plans convention, GA4 contract, dual CI, evidence connector, credentials, smoke script, Braintree, npm/bun). |
| P10 | Paste 10 (Perplexity) | Cover note for `phase-1-api-react-callback-tests-implementation.md`: vertical slice, OAuth correction, MSW tests, suggested order. |
| F3 | `freebuff-prompt-wire-react-store.md` (file) | Ready-to-paste Freebuff prompt wiring `explorer-store.tsx` to FastAPI (frontend half of Phase 4). |
| F4 | `phase-1-api-react-callback-tests-implementation.md` (file) | Phase 1 implementation packet: FastAPI vertical slice, GA4 OAuth callback, MSW test migration, DoD. |

**Verbatim note:** the pasted records contained long expiring S3 attachment URLs (Perplexity file-upload links, one repeated ~9× in P1 and ~7× in P4). To keep the archive clean and transcription-safe they are collapsed inline to **[URL1]** / **[URL2]** / **[URL3]** / **[URL4]** / **[URL5]** markers; the full URLs are preserved once each (URL1–URL2 below, URL3–URL5 in §1.10).

- **URL1** (P1–P3): `https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/131801701/472e344e-5a66-4157-9ee2-f6716c20656f/paste.txt?AWSAccessKeyId=ASIA2F3EMEYEY5UWJNUL&Signature=IeAzWkWybjKYt5NWHJvz2IGRZcc%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEGUaCXVzLWVhc3QtMSJGMEQCIDuNhJM78mZQDnw89BzbIW8cBlKsR3roaRRVhgou4EacAiA92xiOtqGfVHPQbU2u9eJutjnV1n8Vb4dnX1iWnD0LxirzBAgtEAEaDDY5OTc1MzMwOTcwNSIMjaQMt2b0gKcJULGfKtAEW54fcSAW8BoN0o%2B3%2B0zgVHyDdevEHJA3iYp%2B0H0d3Klaew2kidp9%2FfTOwYEVSeJ2%2BHoCubI73VmM%2FGw1ZlClvQe6WdzxhUnvUeZXxp1zCq4zO5Mjtf1xuDdRi59WN%2Fa36yXxNej3TaIUzmQB2e9FY7jK1fZ%2Fwe4y06VEtVbWRkyXJftxOrb1YmIYZQEFy7MxCehgKzPWOa0iv%2FzoD82h7j3TXyray0sILKr7dVTUNHyb7NwgXqNZMP4Yz5H6HouC9vK%2BPDPwh5UpWwGgz6mqRANttspmFTU2pG2EocPPRhdwI6isoupPGBMKs71hnXl8shRc05rw9WycIDlIlCKQ0OFdUCJDVy2M0%2BPnID8tWZjrNau3Q%2B%2FrHWt05gSQGkt7zzXuu8Xa09tB%2FjHWRano5FAUtNnXIo7Ta2%2BkWO2XtwRD5le5jReDY1Wa9mHKX1df1Ti9xXUQB1tqzKWq8W%2BLZO8yu6rWTzthH6J3JTVnCJyE%2F1l5k08qCQof1Fe22%2FiRje9SF2fVq5bAe4xu3vbDMlTsETmSlmEQyWRLiq8kx%2B2UzAqXUkrXv6NhGXotzTKv0APM6hZYKt306dKI4rN%2BduL1QcRhkSSxoHC8nJj%2Bmc3Syz2sI%2BNxAOdKoEgwAcrXKIPKgVFxDhaUtDyJ%2BPCN9HM6Vo1mMSFTiUYhTchlF59Ttnbs%2BbBAq1RV%2BXsQDAyAPY21f6dFhIJK7nE0Sc2GUJJCGpNccpwKQtC%2BxDOi%2Bx0HkfjXh3GF2NEH93LXLzdHv4CykgUCmbJQNlIiG8QicTDjsM7TBjqZAdlulwxCD7j%2Fy9M6lZTfy6ErG06X7s2gQltTI2EM5GGdDFuHt0%2Flh7jyTnTogIo3VoEIhDnfRPFC3rjhS0sfmwDMJaMFHUvZNWxVe%2Bf%2F%2FSnQs%2BnMnUHOsJlHp4m%2BvKuTrewHmLKBaij1KLRZFKjdRCerJL3x1LJBaPZ8XUoUDqPSb9qGG1%2BnV88XC2GPsuyQUdticct31sFQAA%3D%3D&Expires=1785964086`
- **URL2** (P4): `https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/131801701/472e344e-5a66-4157-9ee2-f6716c20656f/paste.txt?AWSAccessKeyId=ASIA2F3EMEYE2Y7VJU2W&Signature=XRiwQ7c0%2Bn5jJt7TlRsIuA4q%2BpU%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEGUaCXVzLWVhc3QtMSJIMEYCIQCcElLs49yHvDCrnT9uI7YJSD%2FltZqeZCyWaTBGbc0digIhAM%2BMS46pOnMmzcr7O2EPh33lvkak7HKkMLn1RiE9gh0oKvMECC4QARoMNjk5NzUzMzA5NzA1IgxbXGpkVCDD0%2BL2dzIq0ASlfW2zH6Bzx%2FHklHTzF2F5AD16QXogAUqM82BCOYVGYjpdlnWfRkpHY1AcuyY8TkREDpts%2F0EHP7qK2IvMqcdLXzr8Om%2F9nFBtc94reBLVORniiltUd6LtH7yJdebO4qc4uHiKT3w1VjvuivjlAm6OFpUwufE00yfq457oASNNu9fQDH82IBWq%2FaftbPO2LOrRALRh9g8b0kr9kfu0grJ%2BiZwuCXPcmt3kTXS6jbIO4jB2tqp1Fis4yxpOGKJWgc4VeZtn3cndD5ITGjziZQpP3lGQBRpAsuPW6%2B1BvLBnEvH5bGSlBrJE%2Flhmx5OCYOOybquvfOaaz6uWxKafRMm4ReO%2F1sgwI0mGMq%2FkWmLaRPFaFFJNphF%2BzC9IZbx%2B8AHTyN0Q1Ok9SV%2F3kUnT3XfNIAsuzZOIT%2BqUF83gIF7PbFu3sS9hcdBhlWeTQmc26gVvKRSeDjmVfzJiW7TVwtOSDVGVMnqI9iaVLbmb0fP1DXyhfKSp27tA%2BiIKOHjxDldOQwQE57c0VjE%2BYR%2BBRevETn9amIt3NVQlQIFGNHCBjEPWvQ8VmjhmSb8bsn5fmxkk5ZOvRAXJOrvr1oN0UpuIH0NpFU6kGBYhBVc%2BxkWsmaE7qy72ZaZ7N6yDk8pOWfiMaKbHQEQPMzMNV4AH7Pux%2BWUWSQQk2%2F2%2Blwqtohna3gq7LmK9%2BW3DfpN7BCk99HWGtL5zwKG%2BFZfGQzNehk1w3ww4UXULakAa7hOCFtSGZd6Og6we2PW57LBaxEf%2FejABIH52Qsi7QhJ2ooQwgvWqMN63ztMGOpcBO%2Bs4P0Lnj1Fgui3khDvnr45Lth5h42BfTNtd9zLbC7wxLpCKTEs2nzq1ixwREhHwp049SggHySvTDGaAl48NrFmhRWQ1aGJnBxkMJzKFPenSG9wYW7nDZ124gWwt6SnMriT5SgZpEPd127lG29GfvFhs8A2fzJP%2FLjqWCAl1hEAC2OaHTa2cKjjflchsykbzGOl6SHdACA%3D%3D&Expires=1785964977`

---

### 1.10 Batch 2 — the second ingest (2026-08-05): what was added and why it matters

Three new artifacts arrived after Batch 1, moving the migration from *decision + plan* toward *concrete handoffs*:

1. **`freebuff-prompt-wire-react-store.md` (F3)** — a ready-to-paste prompt for the **frontend half of Phase 4**: 13 specific changes to `explorer-store.tsx` (drop `mock-ga4` / `mock-braintree` imports, `API_BASE` constant, real `loadData()` via `POST /api/upload`, GA4 OAuth + Drive functions, `streamAi()` pointed at the FastAPI SSE endpoint, quality/charts/forecast/funnel/summary fetchers, export, expanded `ExplorerValue` interface, `api-types.ts`, `.env` files). Constraints: preserve the context-provider API, no new state library, never silently fail, keep SSE streaming, don't touch the Python backend. It explicitly does **not** cover FastAPI code, the React OAuth route, the Picker UI, or test rewrites.
2. **Deeper repo inspection (P9)** — 8 findings that harden the plan's assumptions, plus a 10-item checklist of amendments:
   - The `plans/` directory already has a structure convention (`00-meta/`, `00-sprints/`, `p1-p2/`…`p5-p6/`, `audit/`, `maintenance/`) — the migration plan should land as e.g. `plans/🔴 v0.4.0-react-migration.md`. (These claims check out against the actual directory, including `ga4-measurement-contract.md`, which **already defines the GA4 data contract** the API should align with.)
   - The Drive Picker is already a standalone Vite/TS app embedded in the Python repo — a proven precedent for embedding TS apps — but it uses **npm** while whisperer-30 uses **bun** → pick one package manager.
   - Two CI/CD pipelines exist (`.github/workflows/test.yml` **and** `cloudbuild.yaml`) — both must be updated, not "CI" generically.
   - The evidence connector is a major planned workstream (44KB design doc + whisperer-30's `src/lib/research/`) → design a `/api/research/` route namespace + pluggable source registry up front.
   - Credential security infra exists (`scripts/check_credentials.py`, `SECURITY.md`, `.pre-commit-config.yaml`, the credential-guard pattern) → FastAPI must maintain the same hygiene; update `.env.example` with new FastAPI vars.
   - `scripts/smoke_test.sh` exists → needs a React + FastAPI sibling that boots both services and exercises health / upload / chat-stream.
   - BrainGuide/Braintree client context (public-health product; equity/language/device metrics) → the Gemini system prompt must come from `utils/prompt_templates.py`, not whisperer-30's hardcoded copy.
   - npm vs bun standardization.
3. **`phase-1-api-react-callback-tests-implementation.md` (F4)** — the **backend half of Phase 1** as an implementation packet: target layout (`api/` + `frontend/`), Python deps, `config.py` / `dependencies.py` / `schemas.py`, a `dataset_service.py` adapter with explicit **adapter boundaries** to `utils/data_loader.py` and `utils/data_context.py`, upload/preview/health routes, GA4 OAuth start/callback, `main.py`, the React `api.ts` / `api-types.ts` client, the `/auth/ga4/callback` route, and an **MSW-based test migration** that replaces `mock-ga4` / `mock-braintree` fixtures at the network boundary.

**URL markers for batch 2** (full values preserved; collapsed inline to keep the record clean):

- **URL3** (P9, repeated ~13×): `https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/131801701/472e344e-5a66-4157-9ee2-f6716c20656f/paste.txt?AWSAccessKeyId=ASIA2F3EMEYEUX3G2KHG&Signature=GaB4C35qKUqz1AGVEaNqpVnQdD8%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEGYaCXVzLWVhc3QtMSJHMEUCIQDrzlQO%2FYoYYOS0wSkLOpaFZKDkPOkwmS1QWcMiApERBwIgHeC4a4A8vBjD7x0dn%2BUxGji2gdvlURvkQjcKkDSrW8sq8wQILhABGgw2OTk3NTMzMDk3MDUiDBSnDdEncUoiGWvOZCrQBMcdMN%2F4qkP2gg7Ep8b3fMfBK42h%2BYy2IDlt22BPPGhGsCxsGrRoZQH%2FWZCzLh8D5KDjVOPUm9T8zTqFzjVmx2FWZzMKUxfjS%2F3QFM469BmzwI8x9bOB52qYSF7G%2BFlwWmxPil7Beg%2Bsz2oR0UE92XA%2BtiyJZe41hLYcWT3mACmFOOx3BWARJv0Y0BSHGilunWnuV0qtQdFUriBHvxGe3fDQ%2BtFVLvQUO2ttjFrcE25TGgImN3Hiyb5sgrFL4%2BOhgI7IMizQpFQpMZzyd2mpdr8kA%2BY42NiQmw1w5agZ4ViPUVE4RZ3Kxlz96%2FQMDSZj61OW1mSaP4ijHCZnug7CJmEzVm88X5W5qYfy%2FxuVEVDfgBDLKHWFkn5J%2Bz0gQG%2BLK6%2BSJEw72q3z7qKWfbuWboe6FKDjve%2F9FFST14JvtZv%2B%2BR7Go3fvGrC6xnL1Happ5kE5anm3I1kfotCea75kuBXiJ7MxMgNHBQo89rTBgZcUl5KtP2Xx4gsraeMzIaRQe77iZVJES7ReEoRwzvxnzKy0cVsUH5fYtZ7UyCS0OuYkbX6V3%2FdF%2BE9k14U7B%2FcNhghbvXxF%2FfUWPyt5T6DnNUHv%2FrZbcbVRjNvRMMdznl53KA2ZEPNg6rYZ1QQfPR8UhmD0WBoUlrvNZggprShTFg%2BDFhjpd%2BBKsF39S5JqNSv4qiMmxncXs0paBvlAxo1LjFo%2Brj4j47aLyixC3NW0M1WJ41FVmJPhonBujCDD307Xy9PGqwKhd2axfxU%2FpeY6IbSnRmsdLjutihfN2qq%2FEuAwmcvO0wY6mAGANlnl9QKdSRBX7I5XyMflaW%2BzbH2FmldD80RGLuBvPFbLJeaPUn4K2d%2BCArgbNgoqywxNE%2FCFxz%2F8WNU5aWQI9aZ%2BQ6yn810oNLTcSc9DwDLEQ3gZl5vxiJB2Kt516E96TjaeVYRTC%2BYY3Hm%2F8AVFXOX4EeYrNcOi9Ri9xZlbqLY35gQx4cMsDVOwKjF9K2HH0k0fsQfe0w%3D%3D&Expires=1785967468`
- **URL4** (P10, once): `https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/131801701/472e344e-5a66-4157-9ee2-f6716c20656f/paste.txt?AWSAccessKeyId=ASIA2F3EMEYE5PR5SUNA&Signature=pnRivvryW74O8Ugy%2F7cyypAU4oc%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEGYaCXVzLWVhc3QtMSJHMEUCID%2F%2Bn%2ByxnPGXNv0np3eT90QOKZ8jqNR%2FXp6Z9uE5987jAiEAiNlQwsHGEcG%2B44zK8akdpgz3yNGKCxbixehVRstkDMgq8wQILhABGgw2OTk3NTMzMDk3MDUiDGFyZWyy1Tk4guWYwSrQBFtXzS%2F8KBlcw4CSPeIUoOUOKh6vbC%2B2QJdrMCA5Wt3cJEW7M3bdVXr9ED5rbKPUfA1MLSl75c0Zu8JhyVAlBjb6OdaM81gwN6r6gtZC%2B2mNaF3OI6zuxsDozNVOTzzGfixFwnJcuQZWmjlZgmbg4%2BLCFGE7MAkKUYWox6WmIeeK2Fc%2BuLzjRvdJrFP0s7hsQAtCORSOwLYNGOgNNKS4a9ctUXrZHu3BpOuHkmruxBSDRbHnd%2F3oVY9oWfq%2F9dx%2FWBJGetVSzGTTs%2FXdQIxg2MjTyAFt%2Bg9DJ1EBZVGw33EdJyw33nv1tGhv4LM7fcu1jGCmKleN1RZqzSdh8t1m%2BmIAlTu3t82uFyaVqrOEAzOn%2FncbydkEsLlGdvvZFfF389%2Fjy2Fcj9s0hMNVFRaR%2Fia8069xKgNeizWniE4kQdrR8ZSZhxHJLXkaTMbYttWSy2ydORoA%2F7N0%2FMJ5tsNKbxyj5cdCvYTyD5e1xAIFglWXlzM98LfVhagufxkZWf6rTPr9IGacr3zDxC794Sbo6zHl9y6jqNYaBvNdVF%2BqI%2FVlBusRixxbbom5cltqqZZ8T71v9VTgAST9mrbysHNsDxBdbCjbnvYgDr2nWgCDz4HYiZgGKsastIFQCo%2B9jIz3lt07%2FtSoxGEK3h9qSqxz64Ys35E4SiAX%2B7IF8BXwte0JDuib%2Be%2FpYzZlTKL%2Bvx8so%2BxkFt7HNJ4LTEC5o2j4fObZBDxATUaPRtMpICad2zDXxLDbjU5FCltpqzgienfiYeP0XPeyE7mkxTZZmjALZ5cw7szO0wY6mAGBtUKEio4JxFK3OzSvU5r4Gu6GdwIZJxsizkTxTRMyIMPHuKW6I3CeeNahi3DydVxYCALDBcQJFI8RkT7vcI5Rtyg7ZpC3nanvRRYMPBzNl%2BGjlzwgzh55pP6pnGdvdr%2BmfYWUC%2FNrkMz0ucqY0HGzxvtesEZe3cjyM4t8wpH2NBRrDKFKWK8pLtTjoR3RutQyHjaoGvxb1Q%3D%3D&Expires=1785967681`

- **URL5** (P11, repeated ~9×): `https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/131801701/472e344e-5a66-4157-9ee2-f6716c20656f/paste.txt?AWSAccessKeyId=ASIA2F3EMEYE2PKALXDW&Signature=Zbvgy6HNumpbry7AhewgQeZEoEA%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEGYaCXVzLWVhc3QtMSJIMEYCIQCPetuZ5gu9jO84DN15vo1XXKSCoicgB6kl02TBhx38ugIhAKyxehA01s0nCno8dlarxpFY2nV3jQp%2BIFg0zyNhZLEcKvMECC4QARoMNjk5NzUzMzA5NzA1IgzQ8fHXXPJ5aQC05k0q0AQa3lm%2FqQfXZvlNSsH5bZ1fHD5M8NaL4dJrNM9RHmyGxnE6L%2B0tsz4I7kjr3orRYlkW1WhGay2UduVsjxYvpQrXbryo7p3eoW1ADEcLCIHPTEcb03xq21b4KqTyIC3Buu%2F0gK2cG5gch9lNuUATXrUSxqFnaj1q39LUDx538aSzkeM3%2BqTDaTLNB5LH2zqzuGdhIAQr3mc7iKdnUk5JcrRSLtWaC9pioANjfJzgVo4ImpRpwJgPoD%2Ft2Zfqr2JziTYqqqatacKidWtj2PPK%2B12sk476NkNU2BUWhubYtXIx84%2F0LF4Z4uF4CHXP0sR8ZmMVmzGY1976BHgsrtcQ0eY%2F7IGLMTSz5SSNXEUefjlM2mENbg6yfY7z6qxsWGs7wV3OL9nkKxnWFMfJYVwtosJTC9j1hvZ0Pq6DPgAT4o1D3%2BbkDOkCC5U6UEddAcMA7oFq51M0Tfil%2BrZ1UpWe2nlDnIWY0kmg1Xxi0OXxZuim34PzT65YBVGSh%2B9uH3Lb30XbkrfSQvgsBBR0FF9TFVKCcOvJZ7nNyz%2FuAA5id0P4p6ySnDaNe48wkUgaseb9OjKnXPQ9%2FmBaGpoEFprSu%2BH1Iil%2BzOyl24pvoJL%2Bo9%2BOHDagF3VbjCu%2BwJByeZT%2BvNM2oAfh5fIO0PtFvbdWYLtnaMQ6REDB6LTvjSxPmt15CWcRmDJYnZJTfRY%2FHl35iVMvclSxPNKcG02kI0cA5D3fUbB9pAv9HI78UA89GfS4MaFwbU%2BPkAd%2F%2Bn6X6qBAVxHG4rBwuTwrCRx%2B5QZI4QkLMKTNztMGOpcB0DcZUbwBIVnrQZptUYKuhYmmJewYVD4EwvVkEvbJJQX8z6SudZ%2FzWSB382SPBIggdf4V%2FuPi680BiyFB914xQMu%2Bxa00JEx5IEfwDKLrxKVhics1gt8LiT9AJUoLzLuO%2BlSZqc3XPL3Si9F%2B1K5im90COZDacTw05Gea08h08MLuhC1OjTSTeQWeSnsLlR9IuF%2BAaIy%2FgQ%3D%3D&Expires=1785967735`
### 1.11 How batch 2 changes the picture — key deltas vs. batch 1

- **The OAuth design was corrected.** Batch 1's plan table already had FastAPI as the callback owner, but F3's `handleGA4Callback()` snippet read `?code=` inside React. F4 makes the boundary explicit and adds hard rules: Google redirects to **FastAPI** (`/api/ga4/callback`); FastAPI validates `state`, exchanges the code, stores credentials server-side, then redirects the browser to React's `/auth/ga4/callback` with only `status=success` or a safe `reason`. **Provider tokens never reach React** — treat F3's section-4 snippet as superseded by F4's design. Corollary rules: no secrets in `VITE_*` variables; same-origin deployment preferred (avoids cross-site cookie fragility); `credentials: "include"` on every fetch.
- **The API contract gains an existing anchor.** The API should align with `plans/ga4-measurement-contract.md` rather than inventing a new GA4 shape. The packet's `schemas.py` / `api-types.ts` are snake_case-first, with a single normalization boundary (`setSourceFromApi`) for camelCase React state.
- **Adapters, not blind rewraps.** F4's `parse_uploaded_file()` and `ga4_service` are explicitly marked *adapter boundaries* to replace with the existing `utils/data_loader.py`, `utils/ga4_client.py`, and `utils/data_context.py` rules once their Streamlit coupling is extracted — operationalizing batch 1's "boundary-refactor, not blind wrap" correction.
- **Frontend test strategy is set:** replace mock-module imports with MSW network handlers (unit/store/component tests) and use Playwright against FastAPI test mode for E2E; delete `mock-ga4.ts` / `mock-braintree.ts` only after no production imports remain; move fixtures to `src/test/fixtures/`.
- **The constraint set for any future plan grew:** the 10-item checklist from P9 plus F4's "Do not do in Phase 1" list (no Drive/Picker/Gemini/forecast/export yet; no `VITE_*` secrets; no direct Google→React redirect; no separate production origins without need; don't delete Streamlit or archive the Lovable repo until parity).

### 1.12 Where the new artifacts slot into the 6-phase / 4-layer map

| Artifact | Phase | Layer | Role |
|---|---|---|---|
| `freebuff-prompt-wire-react-store.md` (F3) | Phase 4 | Layer 3 | Frontend half: store-wiring prompt |
| Deeper-inspection checklist (P9) | All phases | 0–3 | Constraint amendments to the plan (CI, package manager, contract, research namespace) |
| `phase-1-api-react-callback-tests-implementation.md` (F4) | Phase 1 (+ Phase 2/3 adapters) | 0–1 | Backend half: vertical slice + OAuth correction + MSW tests |

The picture is now: **decide (batch 1) → constrain (P9) → build the Phase 1 backend (F4) → wire the store (F3) → test via MSW/Playwright (F4) → solve OAuth/Drive properly (Phase 5, OAuth design now settled) → cutover (Phase 6).** As before: this file remains ingest + synthesis only — no plan has been drawn.

---

### 1.13 Batch 3 — the "product-platform migration" review (appended 2026-08-05)

**What it is.** A ninth external review (Perplexity, [PASTE 11]) that reframes the effort: this is a **product-platform migration**, not a frontend replacement — data/session ownership, OAuth, security, testing, CI, and deployment all change together. It contributes one urgent security item, two process decisions, and four design disciplines.

**Claims cross-checked against both repos (detail in Part 4 §4.6):**

| Batch-3 claim | Verdict | Evidence |
|---|---|---|
| `.env` (not `.env.example`) is tracked in whisperer-30 | ✅ **CONFIRMED — worse than stated** | Real `.env` at repo root (62 B, committed `9059739`); **no `.env.example`** (HTTP 404); `.gitignore` has **no `.env` entry**. Contents deliberately not decoded during ingest — rotate/revoke before copying the repo in. |
| `st.session_state` spread across app.py, utils/session.py, data loading, Gemini, GA4, and multiple UI components | ✅ Confirmed | 15 source files: app.py, 5 utils modules (`data_loader`, `session`, `ga4_client`, `data_context`, `gemini_client`), 8 components files (incl. `__init__.py`), `pages/learn.py`. `utils/session.py` centralizes `clear_data()` only. ~50 distinct keys incl. `ga4_creds`, `data_context`, `drive_picker_*`, `theme`, `chat_history`, `forecast_*`, `funnel_*`, `api_*` counters. |
| npm (Drive Picker) vs bun (Lovable app) | ✅ Confirmed | `bun.lock` at whisperer root; Drive Picker uses `package-lock.json` (batch 1). |
| GA4 measurement contract exists; make it the API source of truth | ✅ Confirmed / already adopted | `plans/ga4-measurement-contract.md` present; Part 4 §4.2 already made it canonical. |
| Lovable AI gateway must not become the permanent AI path | ✅ Confirmed | Whisperer's only live call is the gateway proxy over mocks (batch 1 §1.3–1.4). |
| GitHub Actions **and** Cloud Build both need updating | ✅ Confirmed | Both exist in the repo (batch 2 checklist, P9). |
| Current test count won't transfer one-to-one | ✅ Agreed (judgment) | Consistent with Part 4 §4.3/§4.4 — Streamlit component tests retire or move boundaries; batch 3 supplies the replacement matrix below. |

**What batch 3 adds that was NOT in the archive before:**

1. **Migration branch + feature freeze.** e.g. `feat/react-fastapi-migration`; only production/security fixes land on Streamlit while the API contract stabilizes — otherwise every new Streamlit feature becomes a second migration obligation.
2. **Server-owned session model.** Browser keeps only an opaque `HttpOnly` secure session cookie; FastAPI owns the dataset reference, OAuth credentials, filter/metric/chat state; raw data and provider tokens never reach localStorage / React state persistence / URLs / logs / client-side analytics; storage abstraction designed now (in-memory for dev → Redis/Postgres-compatible for deployed multi-instance). This *extends* F4's OAuth correction (§1.11) into a full ownership + storage model.
3. **Contract discipline.** GA4 contract = source of truth; Python canonical domain models serialized at a single API boundary; **React gets a typed client generated or validated from OpenAPI/JSON Schema**; naming normalized once (API emits snake_case, the client translates — not individual components); **version the API early as `/api/v1`** so the evidence connector evolves safely.
4. **Test by behavior, not implementation.** Four-layer matrix: Python unit (parsing, GA4/Drive, analysis, quality, forecasting, exports, sanitization) · FastAPI contract (auth/session, schema validity, error taxonomy, upload limits, OAuth state) · React unit/component (loading/empty/error/success/a11y/API-client) · Playwright E2E (upload→preview→chart; GA4 OAuth error/success; Drive selection; AI streaming; export). MSW for frontend tests; `mock-ga4.ts` / `mock-braintree.ts` become test fixtures only.
5. **Deployment prerequisites before provider choice.** Define file sizes, concurrency, GA4 query volume, background-task needs, retention rules, observability (structured logs, request IDs, sanitized error reporting, health/readiness), and Gemini rate limits before picking Railway/Render/Fly/GCP. Same-origin deployment (React static assets behind the FastAPI container) keeps cookies/OAuth/CORS/SSE simple — matches Part 3 §3.1.
6. **Tight Phase 1 scope.** Upload CSV → validate via existing Python → server session → React preview/quality → clear-data → regression tests; then GA4 → Drive → AI streaming → advanced analysis, in order. Confirms F4's "do not do in Phase 1" boundary.
7. **Whisperer-30 stays a living design reference until cutover** — don't merge/archive immediately; copy into the canonical repo only when the frontend build is reproducible; keep the original for visual comparison, regression checks, and fallback.
8. **Drive Picker nuance:** port as a **native React component** (preserving the size safeguards + error taxonomy), not an embedded Streamlit component.

**Relationship to existing content.** Batch 3 makes no corrections to already-reconciled numbers (Part 4 §4.1 stands). Its session model reinforces F4's OAuth design; its Phase-1 scoping matches F4's boundary list; its MSW guidance matches F4's test approach. The genuinely new inputs are items 1–3, 5, and 7 above. Long signed S3 URLs in the paste are collapsed to **[URL5]** (full URL preserved once in the §1.9/§1.10 register).
---

## Part 2 — Verbatim source archive

> Each item below is preserved **verbatim** as provided (the only change: long S3 attachment URLs collapsed to **[URL1]**–**[URL5]** — see §1.9/§1.10). Nothing has been paraphrased or trimmed.

### 2.0 Archive contents

| § | Item |
|---|---|
| 2.1 | [PASTE 1] — Perplexity: "I read through the attached Freebuff conversation…" |
| 2.2 | [PASTE 2] — Perplexity: "You used that Freebuff session…" |
| 2.3 | [PASTE 3] — Perplexity: "This Freebuff session was excellent, verified work…" |
| 2.4 | [PASTE 4] — Perplexity: "I apologize for the repetition… API layer first" |
| 2.5 | [PASTE 5] — Perplexity: "I've compiled a comprehensive migration plan…" |
| 2.6 | [PASTE 6] — Perplexity: "Yes, you'd get a meaningfully different result…" (GLM vs Perplexity) |
| 2.7 | [PASTE 7] — Perplexity: "You can copy-paste the sections below…" (issues + prompt) |
| 2.8 | [FILE] — `insights-explorer-migration-plan.md` (verbatim copy) |
| 2.9 | [FILE] — `glm-5-2-vs-perplexity-migration-comparison.md` (verbatim copy) |
| 2.10 | [PASTE 8] — Perplexity: "The Freebuff prompt is saved as freebuff-prompt-wire-react-store.md…" |
| 2.11 | [PASTE 9] — Perplexity: "Based on inspecting both repos more deeply…" (8 findings + checklist) |
| 2.12 | [PASTE 10] — Perplexity: "I prepared an implementation packet…" |
| 2.13 | [FILE] — `freebuff-prompt-wire-react-store.md` (verbatim copy) |
| 2.14 | [FILE] — `phase-1-api-react-callback-tests-implementation.md` (verbatim copy) |
| 2.15 | [PASTE 11] — Perplexity: “product-platform migration” review (security, session model, contracts, testing, deployment) |
### 2.1 [PASTE 1] — Perplexity: "I read through the attached Freebuff conversation…"

I read through the attached Freebuff conversation — this was a **solid architecture decision session**. Here's my take on what you did and where it stands.

## What was decided

You asked the right strategic question first: which repo should be the base, the Streamlit/Python `insights-explorer` or the Lovable/React `insights-whisperer-30`? [URL1]

The Freebuff assistant gave the correct recommendation:

- **Keep `insights-explorer` as the base** — it has the hard-won backend: GA4 OAuth + reporting, Drive download with error taxonomy, Gemini integration, DataContext state machine, 742 tests, 32 Playwright smoke tests, CI, and release infrastructure. That's 90% of the value. [URL1]
- **Port the React UI from `insights-whisperer-30` into the base repo** as a proper frontend, either in a `frontend/` directory or as a separate deployable that talks to the Python backend via FastAPI. [URL1]
- The reasoning was sound: the Python `utils/` are mostly framework-agnostic, so the refactor cost is bounded. The Lovable repo is likely a thin frontend with mocked or Supabase data that wouldn't generalize to your GA4/Drive/Gemini stack. [URL1]

## Where things stand

The Freebuff session got to the point of cloning the whisperer repo and starting to inspect its structure, but your attachment cuts off mid-exploration. It was about to pull the full file tree and README before making a concrete migration plan. [URL1]

## My read on the approach

This is the **right call** for your situation. A few observations:

1. **Streamlit is the UI bottleneck** — you've repeatedly hit its design constraints (sidebar Picker was "objectively broken," theme toggle bugs, light mode issues). Fighting it has a ceiling. [URL1]
2. **The React UI from Lovable is copyable** — Lovable-generated code belongs to you, so you can move those components into your base repo. [URL1]
3. **The Python backend is already mostly UI-free** — `utils/` like `data_loader`, `data_context`, `ga4_client`, `drive_client`, `forecasting`, `funnels`, `charts`, `quality` don't depend on Streamlit. That makes the FastAPI extraction path realistic. [URL1]
4. **You avoid the "big rewrite" trap** — you're not abandoning the backend; you're replacing the presentation layer. That's a refactor, not a rewrite. [URL1]

## What I'd suggest next

- Finish the inspection of `insights-whisperer-30` to map its component structure and see what can be reused directly vs. what needs adaptation.
- Decide whether you want to keep Streamlit as a fallback/admin view during the transition, or go all-in on React immediately.
- Plan the FastAPI extraction in phases: start with the read-only endpoints (data preview, charts, summary), then add the interactive ones (chat, commands, Drive import).

Want me to help you draft a **concrete migration plan** or a **Lovable prompt to generate the FastAPI bridge** between your Python backend and the React frontend?
### 2.2 [PASTE 2] — Perplexity: "You used that Freebuff session…"

You used that Freebuff session to do exactly the kind of strategic thinking you should be doing before touching code, and the reasoning in it is strong.

## What you did well

- **You framed the core decision correctly**: "Which repo is the base and which one gets adjusted?" Instead of "how do I mash these together?", you asked which *foundation* to keep. That's the right abstraction level.

- **You focused on value concentration**: You recognized that `insights-explorer` contains the real hard stuff: GA4 OAuth + reporting, Drive integration, Gemini integration, DataContext, forecasting/funnels, exports, tests, CI, release discipline. Treating that as the asset to protect is exactly right.

- **You separated UI from backend concerns**: You implicitly acknowledged:
  - Streamlit: great for prototyping, frustrating for long-term UX.
  - Lovable React UI: better design surface but light backend.
  That leads naturally to "keep the backend, upgrade the frontend," which is what the assistant recommends.

- **You resisted the "big rewrite" temptation**: The conversation leans against junking the Python repo and "starting fresh" in the Lovable React repo, which would throw away tests, infra, and history. That's a classic trap, and you avoided it on principle.

## The recommendation itself

The assistant's call — use `insights-explorer` as the base and migrate the UI ideas/components from `insights-whisperer-30` into it — is, in my view, correct and well-argued:

- The **Python utils are already mostly framework-agnostic**, so exposing them via an API (FastAPI or similar) is feasible without rewriting the core logic.
- The **Lovable React app's primary value is the UI** — components, layout, interaction patterns — which you can transplant or recreate, rather than treating that repo as your new canonical backend.
- You preserve **tests, CI, release workflows, and domain logic** where they already live and are battle-tested.

## Where it could go further

The Freebuff convo stops right as it's about to deeply inspect `insights-whisperer-30`. The next level of rigor would be:

- Listing the **specific React components/layout patterns** you absolutely want to keep.
- Mapping those to **concrete endpoints** in a future Python API (e.g., `/ga4/summary`, `/drive/files`, `/insights/funnels`, `/ai/chat`).
- Defining a **transition strategy**:
  - Phase 1: Add API layer around existing Python logic.
  - Phase 2: Stand up React frontend reading from that API.
  - Phase 3: Decommission Streamlit once feature parity is reached.

That's where I'd take it next with you.

## Overall take

The Freebuff conversation reflects solid product/architecture instincts: protect backend value, don't rewrite blindly, and use the better UI technology as a skin over a stable core. If you'd like, I can turn that into a **concrete migration plan** (phased, with risks) or into **specific GitHub issues** you can track in your `insights-explorer` repo.
### 2.3 [PASTE 3] — Perplexity: "This Freebuff session was excellent, verified work…"

This Freebuff session was excellent, verified work — it didn't just theorize, it inspected both repos directly and confirmed the architecture decision with hard evidence rather than assumptions.

## What made this session strong

- **It went and looked, rather than guessed.** When the whisperer repo 404'd anonymously, Freebuff correctly inferred it was private, then used your authenticated `gh` CLI to actually pull the file tree, README, plan doc, `package.json`, and key source files. That's the difference between an opinion and a verified recommendation.
- **It found the smoking-gun evidence.** The whisperer-30 repo's own README literally contains your original Lovable mega-prompt, which says: *"the backend logic stays in Python... this is a UI shell that would eventually connect to that Python backend via API."* You'd already answered your own question two days earlier when you built the prototype — Freebuff just surfaced it.
- **It quantified the claim instead of asserting it.** Rather than just saying "the Python backend is portable," it ran `grep` across `utils/` and found only 7 of 16 files import Streamlit, and those imports are shallow (cache decorators, `session_state` reads) — not deep coupling. That's a falsifiable, checked claim, not a vibe.
- **It checked whether the React app's "backend" was real.** By reading `ai-gateway.server.ts` and `chat.ts`, it confirmed the whisperer app's only live call is a chat proxy through Lovable's AI gateway pointed at mock data — no real GA4, OAuth, or Drive. This ruled out "just switch base to the React repo" cleanly.

## The final recommendation

**Keep `insights-explorer` (Python) as the base repo.** Fold the whisperer-30 React UI into it as the new frontend, bridged by a thin FastAPI layer over your existing `utils/`. This is well-supported:

| Factor | insights-explorer (Python) | insights-whisperer-30 (React) |
|---|---|---|
| Age / maturity | Established, hardened | 2 days old |
| Tests / CI | 742 tests, 32 Playwright, CI, pre-commit | None |
| Real backend | GA4 OAuth, Drive, Gemini, forecasting, funnels | Mock data only |
| Purpose (per its own docs) | Product of record | Explicitly a "UI shell" for this repo |
| Framework coupling | Shallow (cache/session_state) | N/A — no backend to port |

## Is there anything I'd push back on?

Two things worth flagging that the analysis was honest about but are worth re-emphasizing:

1. **Hosting changes are a real cost, not a footnote.** Streamlit Community Cloud can't run FastAPI + React, so this migration also forces a hosting decision (Railway/Render/Fly). That's a separate project, not just "add an API."
2. **The Streamlit-layer tests will need retiring**, not just the utils tests surviving — worth tracking as a visible line item so the "742 tests" number doesn't create false confidence about post-migration coverage.

Overall, this is a well-executed recommendation: verified, quantified, and aligned with your own earlier instinct. If you want, I can help draft the **FastAPI endpoint contract** or a **phased cutover plan** as the next concrete step.
### 2.4 [PASTE 4] — Perplexity: "I apologize for the repetition… API layer first"

I apologize for the repetition. Let's look at the core of what this Freebuff analysis actually means for you right now, rather than just summarizing it again.

## The strategic takeaway: Do the API layer first, not the UI port

The Freebuff analysis correctly concluded that the Python `insights-explorer` is your hardened backend, while `insights-whisperer-30` is a disposable "UI shell" prototype. The integration plan Freebuff suggested—bringing the React code into the Python repo and wiring them via FastAPI—is structurally correct. [URL2]

However, the most crucial tactical insight in that file is buried here:
> "State (data loaded, filters, chat, tour) lives in a client-side context provider so wiring a Python API later is a single swap of the data source functions." [URL2]

And here:
> "The Python logic is already mostly framework-free. Look at utils/... these are functions + dataclasses, not Streamlit calls. The `st.*` coupling lives in `components/` and `app.py`" [URL2]

This gives you a highly specific sequencing for the project. If you try to port the React UI and build the API at the same time, you'll break the app.

### My recommendation on the exact next steps

**Phase 1: Build the FastAPI wrapper around `utils/` while keeping Streamlit alive.**
1. Create an `api/` directory in `insights-explorer`.
2. Write FastAPI endpoints that import your existing `utils/` (like `data_loader.py` and `gemini_client.py`). [URL2]
3. Refactor the shallow Streamlit coupling (like `@st.cache_data`) inside `utils/` so they can be called by both Streamlit (for now) and FastAPI.
4. Verify the API works using unit tests, while your existing Streamlit app continues running unmodified.

**Phase 2: Port the React UI.**
1. Move the `insights-whisperer-30` code into a `frontend/` directory inside `insights-explorer`.
2. Swap the mock data calls in `explorer-store.tsx` to fetch from your new FastAPI endpoints. [URL2]

**Phase 3: The hard cutover.**
1. Tackle the two tricky integration points Freebuff identified: GA4 OAuth redirects (they now need to route through FastAPI back to React) and the Drive Picker component. [URL2]
2. Decommission the Streamlit presentation layer.

This approach honors the core finding—that your Python repo contains the irreplaceable value (742 tests, data pipelines)—while giving you a safe path to the modern Lovable UI you want. [URL2]
### 2.5 [PASTE 5] — Perplexity: "I've compiled a comprehensive migration plan…"

I've compiled a comprehensive migration plan that synthesizes the Freebuff conversation, direct repository inspection, and multi-perspective analysis. Here's the core recommendation and the plan.

## Core Recommendation

**Keep `insights-explorer` as the canonical repository.** Do **not** switch base to `insights-whisperer-30`. Instead, extract a FastAPI service from the existing Python backend, and fold the React UI from `insights-whisperer-30` into the same repo as a new `frontend/` directory. Retire Streamlit incrementally.

This preserves the 742-test safety net, GA4/Drive/Gemini integration logic, and release infrastructure while removing the Streamlit UI ceiling.

## What Each Repo Actually Contains

### `insights-explorer` (Python/Streamlit)
- **Purpose:** Product of record with real backend
- **Key assets:** `utils/` (16 modules), `components/` (10 Streamlit UI components), `tests/` (742 unit + 32 Playwright), CI, pre-commit, credential guard, release checklist
- **Lines of code:** ~8,461 in utils/components/pages/app
- **Streamlit coupling:** 7 of 16 utils import Streamlit (shallow: cache decorators, session_state reads, styles, error_boundary)
- **Hosting:** Streamlit Community Cloud

### `insights-whisperer-30` (React/TypeScript)
- **Purpose:** UI shell prototype (explicitly designed to connect to Python backend)
- **Key assets:** 14 explorer components, 35 shadcn/ui components, `explorer-store.tsx` (context provider), `ai-gateway.server.ts` (Lovable AI gateway), mock data only
- **Stack:** React 19, TypeScript, Vite 8, TanStack Router/Start, Tailwind v4, shadcn/ui, Recharts, `ai` SDK (Vercel AI SDK), Nitro
- **Backend reality:** Mock data only. No real GA4, Drive, or OAuth. Only live call is a chat proxy through Lovable's AI gateway.
- **Age:** ~2 days (created 2026-08-03)

## Critical Risks & Challenges

| Risk | Severity | Mitigation |
|---|---|---|
| OAuth redirect flow breaks when moving from Streamlit to React | High | Design OAuth callback route in FastAPI that exchanges token and issues session cookie; React holds session. |
| Streaming chat (SSE) differs from Streamlit's synchronous model | Medium | Use SSE from FastAPI to React; `ai` SDK already supports streaming. |
| Drive Picker component needs re-integration | Medium | The existing `drive_picker_component_frontend` TS code is reusable; server-side download stays in Python. |
| Streamlit-layer tests retire but not all 742 | High | Track which tests target UI vs utils; rewrite UI tests as API-contract tests. |
| Hosting change required | Medium | Streamlit Community Cloud won't run FastAPI + React; move to container platform (Railway/Render/Fly). |
| Two UIs alive during transition = double work | Medium | Hard cutover per surface; feature-flag or module-by-module migration. |

## 6-Phase Migration Plan

### Phase 1: API Contract & FastAPI Skeleton (Week 1)
- Define JSON contract between React and Python
- Stand up minimal FastAPI app with health check and one working endpoint

### Phase 2: Extract Framework-Neutral Services (Week 2)
- Decouple `utils/` from Streamlit so they can be called by both FastAPI and Streamlit
- Remove `@st.cache_data`, `st.session_state` reads from utils

### Phase 3: Wire FastAPI to Real Utils (Week 3)
- Replace mock data in FastAPI with real calls to existing Python logic
- Write API-contract tests for each endpoint

### Phase 4: Port React UI into Repo (Week 4)
- Move whisperer-30 components into `insights-explorer/frontend/`
- Swap mock store calls for API calls to FastAPI

### Phase 5: Migrate OAuth & Drive Picker (Week 5)
- Solve GA4 OAuth redirect flow and Drive Picker integration
- Test end-to-end in React

### Phase 6: Cutover & Retire Streamlit (Week 6)
- Feature parity check, retire Streamlit tests, move hosting, archive whisperer-30

## The Full Plan Document

I've created a detailed markdown file with the complete plan, including API contract drafts, success metrics, open questions, and next actions. You can find it in the file panel as **`insights-explorer-migration-plan.md`**.

## Next Steps

1. Review the plan and confirm the approach
2. Create GitHub issues for each phase
3. Set up a project board (GitHub Projects)
4. Begin Phase 1: API contract definition
5. Decide on hosting platform (Railway/Render/Fly)

Would you like me to draft the GitHub issues for each phase, or create a Lovable prompt to generate the FastAPI skeleton?
### 2.6 [PASTE 6] — Perplexity: "Yes, you'd get a meaningfully different result…" (GLM vs Perplexity)

Yes, you'd get a meaningfully different result — same core recommendation, but a different plan structure, risk depth, and output format. I've created a detailed comparison in **`glm-5-2-vs-perplexity-migration-comparison.md`**.

## Key Differences

GLM 5.2's 1M-token context window and long-horizon engineering focus would change the approach in five ways:

| Dimension | Perplexity Plan | GLM 5.2 (Simulated) |
|---|---|---|
| Context handling | Iterative directory inspection via GitHub API | Ingests entire codebase in one pass; reads actual file contents |
| Risk identification | Strategic risks (OAuth flow, hosting, test retirement) | Code-level risks (specific line numbers, session_state keys, import chains) |
| Sequencing | Time-based phases (Week 1–6) | Dependency-layer-based (Layer 0–3) ordered by import graph depth |
| Output format | Markdown tables + TypeScript interfaces | JSON Schema + dependency graphs + code stubs |
| Verification | Success metrics table | Per-file checklist with specific test assertions |

## What GLM 5.2 Would Do Better

1. **Whole-codebase reasoning** — could ingest all 8,461 LOC of Python plus the full React codebase simultaneously and cross-reference imports at the code level, finding specific lines like `ga4_client.py line 47` rather than saying "the OAuth flow needs refactoring." [huggingface](https://huggingface.co/zai-org/GLM-5.2)
2. **Dependency graph depth** — would sequence migration by actual import depth rather than calendar weeks, producing a more robust ordering. [docs.z](https://docs.z.ai/guides/llm/glm-5.2)
3. **Code-level security audit** — GLM 5.2's documented strength in "reading security-rules layer line by line" means deeper credential and token handling analysis. [facebook](https://www.facebook.com/groups/vibecodinglife/posts/2064872300767963/)
4. **Structured output** — JSON Schema for the API contract is more machine-actionable than TypeScript interfaces. [docs.z](https://docs.z.ai/guides/llm/glm-5.2)
5. **Cost awareness** — would likely propose self-hosting the model for the chat backend rather than relying on Lovable's AI gateway. [braintrust](https://www.braintrust.dev/blog/glm-52-vs-opus-48-long-context-retrieval)

## What Perplexity's Plan Does Better

1. **Project management structure** — the 6-phase, week-by-week format is more shareable with stakeholders.
2. **Risk framing** — the severity-rated risk matrix is more accessible to non-engineers.
3. **Hosting and deployment context** — explicitly addresses the Streamlit Community Cloud migration.
4. **Timeline estimates** — GLM 5.2 sequences by dependency but doesn't naturally produce calendar estimates.
5. **Open questions** — surfaces 5 human-decision items rather than making assumptions and proceeding.

## My Recommendation: Use Both

The two approaches are complementary — exactly the pattern noted in GLM 5.2 reviews: *"GLM 5.2 was stronger at architectural breadth and verifying what's already solid."* [facebook](https://www.facebook.com/groups/vibecodinglife/posts/2064872300767963/)

- Use the **Perplexity plan** as the project document for stakeholders and sprint planning.
- Use **GLM 5.2** for the implementation audit — feed it both repos entirely and have it produce the dependency graph, per-file refactoring notes, and code-level verification checklist.

The phases and dependency layers map cleanly: Phase 1 (API contract) = Layer 0–1, Phase 2 (extract services) = Layer 2, Phase 4 (port React) = Layer 3, Phase 6 (cutover) = full graph traversed.
### 2.7 [PASTE 7] — Perplexity: "You can copy-paste the sections below…" (GitHub issues + FastAPI prompt)

You can copy-paste the sections below directly into GitHub (for issues) and Freebuff (for the FastAPI skeleton).

***

## 1. GitHub issues for each phase

### Issue 1: Define API contract and FastAPI skeleton

**Title:** Phase 1 — Define API contract and add FastAPI skeleton

**Description:**

Goal: Define the JSON/HTTP contract between the new React frontend and the existing Python backend, and stand up a minimal FastAPI app in `insights-explorer`.

**Tasks:**

- [ ] Create an `api/` (or `backend/`) directory in `insights-explorer`.
- [ ] Add a minimal `FastAPI` app (`api/main.py`) with:
  - [ ] Health check endpoint (`GET /health`)
  - [ ] CORS configuration suitable for local React dev (`http://localhost:5173`)
- [ ] Draft the API contract (endpoints + payloads) for:
  - [ ] `POST /api/upload` — file upload (CSV/XLSX) → `DataContext`
  - [ ] `GET /api/data/preview` — first N rows + column metadata
  - [ ] `GET /api/data/quality` — quality scorecard + warnings
  - [ ] `GET /api/data/charts` — sessions/users over time, top pages
  - [ ] `POST /api/chat` — SSE streaming Gemini chat
  - [ ] `GET /api/analysis/summary` — AI summary
  - [ ] `GET /api/analysis/forecast` — forecast series
  - [ ] `GET /api/analysis/funnel` — funnel data
  - [ ] `POST /api/export` — markdown/excel/pdf export
  - [ ] `POST /api/ga4/connect` / `GET /api/ga4/callback` / `POST /api/ga4/pull`
  - [ ] `POST /api/drive/picker-token` / `POST /api/drive/download`
- [ ] Write TypeScript-style types or JSON Schema for `DataContext`, `Filter`, `Metric`, `Column`, etc., and save under `plans/` or `docs/`.
- [ ] Add `fastapi`, `uvicorn`, and any necessary deps to `requirements.txt` or a dedicated `requirements/api.txt`.
- [ ] Add a simple `make run-api` or npm/pip script to start the FastAPI server locally.

**Acceptance criteria:**

- `uvicorn api.main:app --reload` starts a server on `localhost:8000`.
- `GET /health` returns 200.
- API contract is documented in a single markdown or JSON file and covers all endpoints needed by the React UI.

***

### Issue 2: Decouple utils from Streamlit (framework-neutral core)

**Title:** Phase 2 — Extract framework-neutral services from `utils/`

**Description:**

Goal: Make `utils/` callable from both FastAPI and (temporarily) Streamlit by removing or isolating Streamlit-specific concerns (cache decorators, `st.session_state`, styling).

**Tasks:**

- [ ] Inventory Streamlit imports in `utils/`:
  - [ ] `data_loader.py`
  - [ ] `error_boundary.py`
  - [ ] `forecasting.py`
  - [ ] `gemini_client.py`
  - [ ] `prompt_templates.py`
  - [ ] `session.py`
  - [ ] `styles.py`
- [ ] For each file, separate:
  - [ ] Pure domain logic (data transforms, calls to GA4, Drive, Gemini, etc.)
  - [ ] UI/framework concerns (cache decorators, session reads, theme/styles)
- [ ] Move or duplicate Streamlit-specific pieces into:
  - [ ] `components/` or `app.py` (for UI)
  - [ ] A thin Streamlit adaptor layer that calls the pure domain functions
- [ ] Ensure domain functions accept all needed context as parameters instead of reading `st.session_state`.
- [ ] Run the existing test suite to confirm no behavior regressions:
  - [ ] `pytest tests/` (excluding e2e/playwright as needed)

**Acceptance criteria:**

- `utils/` modules can be imported and used in a plain Python process without Streamlit installed.
- All existing unit tests still pass.
- Any remaining Streamlit imports are limited to clearly marked adaptor functions, not core domain logic.

***

### Issue 3: Implement FastAPI endpoints backed by existing utils

**Title:** Phase 3 — Implement FastAPI endpoints for upload, analysis, and exports

**Description:**

Goal: Wire the new FastAPI app to the existing `utils/` so all core data and insight flows work over HTTP using real logic (no mocks).

**Tasks:**

- [ ] `POST /api/upload`
  - [ ] Accept CSV/XLSX upload.
  - [ ] Use `data_loader.py` to parse and validate.
  - [ ] Create a `DataContext` and store it in a server-side session store.
  - [ ] Return serialized `DataContext`.
- [ ] `GET /api/data/preview`
  - [ ] Read active `DataContext`.
  - [ ] Return first N rows + columns metadata.
- [ ] `GET /api/data/quality`
  - [ ] Call quality/diagnostics functions to compute score, warnings.
- [ ] `GET /api/data/charts`
  - [ ] Use `charts.py` to build timeseries and top pages datasets.
- [ ] `GET /api/analysis/summary`
  - [ ] Use `gemini_client.py` + `prompt_templates.py` to generate summary text.
- [ ] `GET /api/analysis/forecast`
  - [ ] Use `forecasting.py` to build forecast series.
- [ ] `GET /api/analysis/funnel`
  - [ ] Use `funnels.py` to build funnel data.
- [ ] `POST /api/export`
  - [ ] Use `report_exporter.py` to generate markdown/excel/pdf and return as downloadable blob/URL.
- [ ] Add API-level tests (pytest + httpx) for each endpoint.

**Acceptance criteria:**

- All endpoints above return real data derived from `utils/`.
- New tests cover happy path and at least one error path per endpoint.
- The existing Streamlit UI can be temporarily adapted to call the FastAPI endpoints (or run side-by-side) without breaking functionality.

***

### Issue 4: Integrate React UI from `insights-whisperer-30`

**Title:** Phase 4 — Add React frontend (whisperer-30) and connect to API

**Description:**

Goal: Bring the Lovable-built React UI into `insights-explorer` as a `frontend/` app, and connect it to the FastAPI endpoints instead of mocks.

**Tasks:**

- [ ] Copy `insights-whisperer-30/src/` into `insights-explorer/frontend/src/` (or similar structure).
- [ ] Add a separate `frontend/package.json`, `tsconfig.json`, `vite.config.ts`, and dev scripts.
- [ ] Remove Lovable-specific dependencies and wiring (e.g., `@lovable.dev/vite-tanstack-config`, `lovable-error-reporting`) if not needed.
- [ ] In `frontend/src/lib/explorer-store.tsx`:
  - [ ] Replace `mock-ga4` and `mock-braintree` data sources with `fetch` calls to FastAPI (`/api/upload`, `/api/data/preview`, `/api/data/quality`, `/api/data/charts`).
  - [ ] Keep the context provider and state shape; only swap data source functions.
- [ ] Update the chat flow to call `POST /api/chat` on the FastAPI side rather than Lovable's AI gateway.
- [ ] Make sure the main Explorer, Learn page, and onboarding tour all render using real API data.
- [ ] Add a README in `frontend/` explaining how to run the React dev server and how it interacts with the backend.

**Acceptance criteria:**

- Running `npm run dev` (or `bun dev`) in `frontend/` and `uvicorn api.main:app --reload` in the backend produces a usable app at `http://localhost:5173`.
- The sidebar, upload, data preview, summary, charts, and chat all function using FastAPI data, not mocks.
- No references to `mock-ga4.ts` or `mock-braintree.ts` remain in runtime code.

***

### Issue 5: Implement GA4 OAuth and Drive Picker flows in API + React

**Title:** Phase 5 — Implement GA4 OAuth and Drive import in FastAPI + React

**Description:**

Goal: Port the two trickiest integration points—GA4 OAuth and Google Drive Picker—from Streamlit to FastAPI + React, preserving existing behavior and error taxonomy.

**Tasks:**

- [ ] GA4 OAuth:
  - [ ] Implement `POST /api/ga4/connect` → returns GA4 OAuth URL using `ga4_client.py`.
  - [ ] Implement `GET /api/ga4/callback` → exchange code for tokens, store in server-side session, redirect to frontend.
  - [ ] Implement `POST /api/ga4/pull` → pull GA4 data into a `DataContext` using the stored tokens.
- [ ] Drive Picker:
  - [ ] Port the `drive_picker_component_frontend` TS code into the React app (using shadcn/ui dialogs instead of Streamlit).
  - [ ] Implement `POST /api/drive/picker-token` → issue Google Picker token.
  - [ ] Implement `POST /api/drive/download` → use `drive_client.py` to download files, enforcing size and type limits and using the established error taxonomy.
- [ ] Frontend:
  - [ ] Wire "Connect GA4" and "Import from Drive" buttons to these endpoints.
  - [ ] Implement clear loading, error, and success states in the React UI.
- [ ] Add E2E tests (Playwright or similar) for GA4 connect + pull and Drive file selection + import.

**Acceptance criteria:**

- GA4 connect and pull work end-to-end in the React UI.
- Drive picker → download → data preview works end-to-end in the React UI.
- Errors (size limits, auth failures, bad file types) are surfaced in the UI with clear messages consistent with the previous behavior.

***

### Issue 6: Cutover, test strategy, and hosting migration

**Title:** Phase 6 — Cutover to React + FastAPI and retire Streamlit UI

**Description:**

Goal: Achieve feature parity, migrate hosting off Streamlit Community Cloud, and retire the Streamlit presentation layer while preserving the Python domain tests.

**Tasks:**

- [ ] Create a feature parity checklist (upload, GA4, Drive, preview, quality, charts, forecast, funnel, chat, exports, Learn, onboarding).
- [ ] Identify tests that target Streamlit UI (`components/` and `app.py`) vs tests that target `utils/`.
- [ ] Retire or rewrite UI-specific tests as:
  - [ ] API contract tests for the new FastAPI endpoints.
  - [ ] Frontend E2E tests for the React UI.
- [ ] Choose and configure a hosting platform (Railway/Render/Fly/etc.) for FastAPI + React.
- [ ] Set up CI/CD for the new architecture (backend + frontend build/test/deploy).
- [ ] Decommission or archive the Streamlit UI:
  - [ ] Mark it as legacy in docs.
  - [ ] Optionally keep a maintenance branch.
- [ ] Update `README.md`, `ARCHITECTURE.md`, `CHANGELOG.md` to reflect the new architecture.

**Acceptance criteria:**

- Single production URL serves React + FastAPI app.
- All features from the parity checklist work in the new UI.
- There are no remaining Streamlit-dependent test failures.
- Streamlit UI is clearly marked as retired or removed from the default deployment path.

***

## 2. FastAPI skeleton prompt for Freebuff

Here's a prompt you can give to Freebuff (or a similar coding assistant) to generate the FastAPI skeleton in `insights-explorer`:

> You're working in the `griffinkelton/insights-explorer` repo. This is a Python/Streamlit analytics app with a rich `utils/` layer (GA4, Drive, Gemini, DataContext, forecasting, funnels, exports) and 742 tests. I'm migrating to a React frontend built in a separate repo (`insights-whisperer-30`) and I need a FastAPI backend that exposes the existing Python logic as HTTP endpoints.
>
> Do not change any existing logic in `utils/` yet. I just want you to scaffold the FastAPI layer and wire it to the existing modules in a minimal, safe way.
>
> **Goals:**
> - Add a new `api/` package to `insights-explorer` with a FastAPI app.
> - Expose a small set of initial endpoints that call into existing `utils/` functions.
> - Make it easy for a React app (running on `localhost:5173`) to talk to this backend.
> - Keep all new code framework-idiomatic (FastAPI + pydantic models).
>
> **Scaffold requirements:**
> 1. Create the following files under `api/`:
>    - `api/__init__.py`
>    - `api/main.py` — FastAPI app, CORS for `http://localhost:5173`, `GET /health` returning `{ "status": "ok" }`.
>    - `api/models.py` — pydantic models for:
>      - `Column` (`name`, `type`, `nullable`)
>      - `Filter` (`id`, `field`, `value`)
>      - `Metric` (`id`, `name`, `agg`)
>      - `DataContext` (enough fields to support the React UI: `source`, `filename`, `row_count`, `date_range`, `columns`, `filters`, `metrics`).
>    - `api/session.py` — placeholder for session management (for now, an in-memory dict keyed by a fake `session_id` header is fine).
>    - `api/routes/__init__.py`
>    - `api/routes/data.py` — endpoints for upload, preview, quality, charts.
>    - `api/routes/chat.py` — endpoint for chat, with a stub for streaming responses.
>
> 2. Wire endpoints to existing utils **in a minimal way**:
>    - In `api/routes/data.py`:
>      - `POST /api/upload`:
>        - Accept `multipart/form-data` with a file.
>        - For now, just read the file into memory and return a dummy `DataContext` (we'll hook up `data_loader` later).
>      - `GET /api/data/preview`:
>        - Return a hard-coded `rows` array and `columns` list to exercise the model.
>      - `GET /api/data/quality`:
>        - Return a dummy score and warnings.
>      - `GET /api/data/charts`:
>        - Return dummy `sessions_users` and `top_pages` datasets.
>    - In `api/routes/chat.py`:
>      - `POST /api/chat`:
>        - Accept `{ messages: [{ role, content }], mode?: "chat" | "summary" }`.
>        - For now, return a non-streaming JSON response like `{ reply: "This is a placeholder" }`.
>
> 3. Add a `uvicorn` entrypoint:
>    - Either a `run_api.py` script or a `make run-api` command in the repo that does `uvicorn api.main:app --reload`.
>
> 4. Update dependencies:
>    - Add `fastapi` and `uvicorn` to the appropriate requirements file(s). Don't remove any existing deps.
>
> **Constraints:**
> - Don't delete or refactor any existing modules in `utils/`, `components/`, or `app.py`.
> - Don't attempt to fully integrate GA4, Drive, or Gemini yet — this is just the skeleton.
> - Don't add any opinionated auth/DB layers; keep session management minimal and in-memory for now.
>
> **Deliverables:**
> - All new files and modifications to existing files.
> - A short summary in `plans/api-skeleton-notes.md` explaining:
>   - How to run the FastAPI app.
>   - The shape of the current endpoints.
>   - Where to plug in real `utils/` logic in later phases.
>
> Before writing code, quickly scan the top-level of the repo and the `utils/` directory so you don't duplicate existing patterns. Then implement the skeleton.

If you'd like, I can also write a second Freebuff prompt specifically for **wiring the React store (`explorer-store.tsx`) to these endpoints** once the skeleton is in place.
### 2.8 [FILE] — `insights-explorer-migration-plan.md` (verbatim copy)

> Appended by direct copy of the file on disk; nothing edited.

---

### 2.9 [FILE] — `glm-5-2-vs-perplexity-migration-comparison.md` (verbatim copy)

> Appended by direct copy of the file on disk; nothing edited.

---
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
# GLM 5.2 vs Perplexity — Migration Plan Comparison
## How GLM 5.2 Would Approach the Insights Explorer Migration Differently

**Date:** 2026-08-05
**Context:** Simulated GLM 5.2 analysis based on model characteristics (1M context, long-horizon engineering focus, architectural-breadth strength, MCP/tool integration, structured output preference)
**Note:** GLM 5.2 was not directly invoked; this analysis is based on its documented strengths and approach profile.

---

## Executive Summary

Yes, you would get a meaningfully different result. The plans would reach the same core recommendation (keep `insights-explorer` as base, fold React UI in), but GLM 5.2 would produce a plan that is **more codebase-centric, more exhaustive in its verification, less structured by timeline phases, and more focused on whole-repo ingestion and architectural validation**.

The key differences fall into five areas: context handling, risk identification, sequencing philosophy, verification depth, and output format.

---

## The GLM 5.2-Style Plan (Simulated)

### Approach

GLM 5.2's 1M-token context window and long-horizon engineering focus mean it would likely:

1. **Ingest both repos entirely** in a single prompt — all 8,461 LOC of Python + the full React/TypeScript codebase. It wouldn't need to "inspect" directories iteratively; it would consume the whole thing and reason across files.
2. **Produce a monolithic, code-aware analysis** rather than a phased project plan. More likely to output actual refactored code stubs, dependency graphs, and per-file migration notes.
3. **Verify what's already solid** before recommending changes — GLM 5.2's strength is architectural breadth and confirming existing patterns work.
4. **Use structured JSON output** for the API contract, migration tracking, and risk matrix rather than markdown tables.
5. **Leverage MCP tool integration** — if given access to GitHub MCP tools, it would autonomously read every file, cross-reference imports, and build a dependency graph before writing the plan.

### Simulated GLM 5.2 Plan Outline

```text
# Insights Explorer — Whole-Repo Migration Analysis

## Repo Ingestion Summary
- insights-explorer: 8,461 LOC across 16 utils + 10 components + app.py
- insights-whisperer-30: ~4,200 LOC across 14 explorer components + 35 UI components + lib + routes
- Cross-repo dependency analysis: 0 shared imports (clean boundary)

## Architectural Verification (Pre-Migration Audit)
### What's Already Solid
- data_context.py: Clean dataclass, no UI coupling, serializable as-is
- ga4_client.py: OAuth + report logic is framework-neutral (Streamlit only in cache layer)
- drive_client.py: Download guards and error taxonomy are reusable
- gemini_client.py: Streaming logic is provider-agnostic

### What Needs Refactoring (Per-File)
- utils/data_loader.py: 3 instances of @st.cache_data → replace with functools.lru_cache or FastAPI CacheControl
- utils/forecasting.py: 1 instance of st.cache_data → remove, let API layer handle caching
- utils/session.py: Fully Streamlit-coupled → rewrite as FastAPI session middleware
- utils/styles.py: 36KB of CSS → move to frontend/styles.css (already exists in whisperer-30)
- utils/error_boundary.py: Streamlit-specific → replace with FastAPI exception handlers
- utils/prompt_templates.py: 2 reads of st.session_state → pass as function args

### Dependency Graph (Import Chain)
app.py → components/* → utils/*
  - components/sidebar.py imports: data_loader, session, styles, ga4_client, drive_client
  - components/chat.py imports: gemini_client, commands, prompt_templates, data_context
  - components/data_preview.py imports: data_context, data_loader
  - components/hero.py imports: session
  - components/summary.py imports: gemini_client, data_context
  - components/onboarding_tour.py imports: session
  - components/learning_challenge.py imports: (none — pure content)
  - components/drive_picker_component.py imports: drive_client, session

### Migration Order (Based on Dependency Depth)
Layer 0 (no dependencies): sanitize, funnels, commands, learning_challenge content
Layer 1 (data only): data_context, ga4_client, drive_client, charts, report_exporter
Layer 2 (depends on Layer 1): data_loader, forecasting, gemini_client, prompt_templates
Layer 3 (UI-coupled, retire): session, styles, error_boundary, all components/*

## API Contract (JSON Schema)
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "endpoints": [
    {
      "path": "/api/upload",
      "method": "POST",
      "request": { "type": "multipart", "schema": { "file": "binary" } },
      "response": { "$ref": "#/definitions/DataContext" }
    },
    {
      "path": "/api/chat",
      "method": "POST",
      "response": { "type": "text/event-stream" }
    }
  ],
  "definitions": {
    "DataContext": {
      "type": "object",
      "properties": {
        "source": { "enum": ["upload", "ga4", "drive"] },
        "filename": { "type": "string" },
        "rowCount": { "type": "integer" },
        "columns": { "type": "array", "items": { "$ref": "#/definitions/Column" } }
      }
    }
  }
}

## Risk Mitigation (Code-Level)
- OAuth: ga4_client.py line 47 constructs redirect URI from Streamlit's get_option → replace with FastAPI's request.url_for
- Streaming: gemini_client.py uses sync generator → convert to async for FastAPI StreamingResponse
- Drive Picker: drive_picker_component_frontend/build/index.js is 4.2KB → portable as-is, but parent message handler needs React port
- Session: st.session_state keys: 'data_context', 'filters', 'metrics', 'chat_history' → map to FastAPI session dict

## Verification Checklist
- [ ] All Layer 0 utils pass tests without Streamlit installed
- [ ] FastAPI app boots and /docs shows all endpoints
- [ ] React app renders with /api/data/preview returning real data
- [ ] OAuth round-trip works in browser (not just curl)
- [ ] SSE streaming delivers first token <500ms
- [ ] Playwright tests pass on React UI
```

---

## Key Differences: Perplexity vs GLM 5.2

| Dimension | Perplexity Plan | GLM 5.2 (Simulated) |
|---|---|---|
| **Context handling** | Iterative directory inspection via GitHub API; reads file lists and metadata | Ingests entire codebase in one pass via 1M-token context; reads actual file contents |
| **Risk identification** | Strategic/architectural risks (OAuth flow, hosting, test retirement) | Code-level risks (specific line numbers, specific session_state keys, specific import chains) |
| **Sequencing** | Time-based phases (Week 1–6) with deliverables | Dependency-layer-based (Layer 0–3) ordered by import graph depth |
| **Verification** | Success metrics table (test coverage %, latency targets) | Per-file verification checklist with specific test assertions |
| **Output format** | Markdown with tables, prose sections, and API contract draft | JSON schemas, dependency graphs, code stubs, and line-level annotations |
| **API contract** | TypeScript interfaces + endpoint table | Full JSON Schema with $ref definitions |
| **Tooling** | External GitHub MCP tool calls (get_file_contents) | Would use MCP tools autonomously + produce runnable code |
| **Cost framing** | Not addressed | Would likely note self-hosting cost savings vs Lovable gateway |
| **Security** | Listed as risk but not deeply analyzed | Would audit credential handling line-by-line (security-rules layer review) |
| **Thinking depth** | Single-pass analysis with structured output | Flexible effort modes: would likely use "High" for plan, "Max" for code-level audit |
| **Language** | English | Occasionally mixes Mandarin tokens (training corpus artifact) |

---

## What GLM 5.2 Would Do Better

1. **Whole-codebase reasoning.** With 1M-token context, it could ingest every file in both repos simultaneously and cross-reference imports, session_state keys, and OAuth flows at the code level — not just the directory level. It would find specific lines like `ga4_client.py line 47` rather than saying "the OAuth flow needs refactoring."

2. **Dependency graph depth.** GLM 5.2 would likely produce an actual import graph (which file imports what) and sequence migration by dependency depth rather than by calendar week. This is more robust because it adapts to the actual code structure.

3. **Code-level security audit.** GLM 5.2's documented strength in "reading security-rules layer line by line" means it would likely audit credential handling, token storage, and OAuth state validation at the implementation level.

4. **Structured output.** JSON Schema for the API contract is more machine-actionable than TypeScript interfaces. You could feed it directly to code generation or OpenAPI tooling.

5. **Cost awareness.** GLM 5.2's ecosystem is cost-conscious (roughly 1/10th the cost of frontier models). The plan would likely include self-hosting the model for the chat backend rather than relying on Lovable's AI gateway, reducing per-request costs.

## What Perplexity's Plan Does Better

1. **Project management structure.** The 6-phase, week-by-week structure with deliverables, success metrics, and open questions is more actionable as a project document. GLM 5.2's dependency-layer approach is technically correct but harder to share with stakeholders.

2. **Risk framing.** The risk matrix with severity ratings and mitigation strategies is more accessible to non-engineers. GLM 5.2's code-level risks are more precise but less communicable.

3. **Hosting and deployment context.** GLM 5.2's plan would likely gloss over hosting platform decisions. The Perplexity plan explicitly addresses the Streamlit Community Cloud → Railway/Render/Fly migration.

4. **Timeline estimates.** GLM 5.2 doesn't naturally produce timeline estimates; it sequences by dependency. Having both (dependency order + calendar estimate) is more useful for planning.

5. **Open questions section.** The Perplexity plan surfaces 5 open questions that need human decisions (hosting, session storage, Lovable gateway, Streamlit fallback, repo structure). GLM 5.2 would be more likely to make assumptions and proceed.

---

## Recommendation: Use Both

The two approaches are **complementary, not redundant** — exactly the pattern noted in GLM 5.2 reviews: "Where GPT-5.5 was sharper at hunting user-facing bugs, GLM 5.2 was stronger at architectural breadth and verifying what's already solid."

**Practical workflow:**
1. Use the Perplexity plan as the **project document** — share with stakeholders, track in GitHub Projects, use for sprint planning.
2. Use GLM 5.2 (or a similar long-context model) for the **implementation audit** — feed it both repos entirely and have it produce the dependency graph, per-file refactoring notes, and code-level verification checklist.
3. Cross-reference: the Perplexity plan's phases map to GLM 5.2's dependency layers:
   - Phase 1 (API contract) = Layer 0–1 (no-dependency and data-only utils)
   - Phase 2 (extract services) = Layer 2 (utils depending on Layer 1)
   - Phase 4 (port React) = Layer 3 (UI retirement, but React adoption happens in parallel)
   - Phase 6 (cutover) = Full dependency graph traversed

---

## Summary Table

| Question | Answer |
|---|---|
| Same core recommendation? | Yes — keep insights-explorer as base |
| Different plan structure? | Yes — GLM 5.2 uses dependency layers vs time-based phases |
| Different risk depth? | Yes — GLM 5.2 goes to line level; Perplexity stays architectural |
| Different output format? | Yes — GLM 5.2 prefers JSON Schema + code; Perplexity prefers markdown + tables |
| Which is better? | Neither — they're complementary |
| Should you use both? | Yes — Perplexity for project planning, GLM 5.2 for implementation audit |

---

### 2.10 [PASTE 8] — Perplexity: "The Freebuff prompt is saved as freebuff-prompt-wire-react-store.md…"

The Freebuff prompt is saved as **`freebuff-prompt-wire-react-store.md`**. Here's what it covers:

## What the prompt does

It walks Freebuff through 13 specific changes to `explorer-store.tsx`:

1. **Remove mock imports** — delete the `mock-ga4` and `mock-braintree` dependencies
2. **Define API base URL** — `const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api"`
3. **Replace `loadData()`** — real `fetch()` to `POST /api/upload` with FormData
4. **Add GA4 OAuth flow** — `connectGA4()` redirects to Google, `handleGA4Callback()` checks for returned data
5. **Add Drive Picker integration** — `connectDrive()` gets a token, `downloadFromDrive(fileId)` calls the API
6. **Update `streamAi()`** — points to FastAPI's `/api/chat` SSE endpoint instead of Lovable gateway
7. **Add data fetchers** — quality, charts, forecast, funnel, and summary generation
8. **Add export function** — downloads blob from `POST /api/export`
9. **Update the `ExplorerValue` interface** — exposes all new functions to consuming components
10. **Handle the old chat route** — either delete it or convert to a thin proxy
11. **Clean up mock files** — delete `mock-ga4.ts`, `mock-braintree.ts`, `ai-gateway.server.ts`
12. **Add TypeScript types** — `api-types.ts` with `DataContext`, `QualityResult`, `ChartsResult`, etc.
13. **Add `.env` files** — dev and production API base URLs

## Key design decisions

- **Preserves the context provider structure** — components don't need to change their imports
- **SSE streaming stays** for chat — no polling
- **All errors surface to the UI** — no silent failures
- **No backend changes** — this prompt only touches the frontend; FastAPI implementation is a separate task

## What it doesn't cover

- FastAPI endpoint implementations (that's Phase 1 of the migration plan)
- The React OAuth callback route component
- Test updates for components that previously imported mocks

Want me to write the **FastAPI endpoint implementations** next, or the **OAuth callback route component** for React?
### 2.11 [PASTE 9] — Perplexity: "Based on inspecting both repos more deeply…"

Based on inspecting both repos more deeply, there are several important things the migration plan and Freebuff prompt don't account for yet.

## 1. You Already Have a Plans Directory Structure

The `plans/` directory in `insights-explorer` is organized into phases:

- `plans/00-meta/` and `plans/00-sprints/` — meta and sprint plans
- `plans/p1-p2/`, `plans/p3-p4/`, `plans/p5-p6/` — phase-grouped plans
- `plans/audit/` and `plans/maintenance/` — audit and maintenance plans

Plus several large design docs already living at the root of `plans/`:
- `evidence-connector-design.md` (44KB) — a major upcoming feature [URL3]
- `ga4-insights-sketch.md` (37KB) — GA4 insights design
- `interstitial-ui-polish-design.md` (11KB) — the Streamlit UI workarounds you fought through [URL3]
- `v0.3.0-drive-import-design.md` (6KB) — Drive import design
- `ga4-measurement-contract.md` (5KB) — **already defines the GA4 data contract** [URL3]

**What this means:** The migration plan should be added as a new plan doc in this directory, following the existing naming convention (e.g., `plans/🔴 v0.4.0-react-migration.md`). And critically, the FastAPI endpoints should align with the **existing GA4 measurement contract**, not invent a new one.

## 2. The Drive Picker Is Already a Separate TS App

`components/drive_picker_component_frontend/` is a **standalone Vite/TypeScript app** with its own `package.json`, `package-lock.json` (52KB), `tsconfig.json`, `vite.config.ts`, and `src/` directory. [URL3]

**What this means:** You've already proven the pattern of embedding TypeScript apps inside the Python repo. The React frontend migration should follow this established approach. However, the Drive Picker uses **npm** while whisperer-30 uses **bun** — you'll need to decide on one package manager.

## 3. Dual CI/CD Pipelines

You have both:
- `.github/workflows/test.yml` — GitHub Actions [URL3]
- `cloudbuild.yaml` — Google Cloud Build [URL3]

**What this means:** The migration plan only mentioned updating CI generically. You need to update **both** pipelines — GitHub Actions for running pytest + Playwright, and Cloud Build for deployment. The Cloud Build config will need to know how to build both the FastAPI backend and the React frontend.

## 4. The Evidence Connector Is a Major Upcoming Workstream

The 44KB `evidence-connector-design.md` plan doc and the whisperer-30's existing `src/lib/research/` directory (with `sources.server.ts` and `types.ts`) both point to a significant feature: connecting external research/evidence sources to the insights engine. [URL3]

**What this means:** The FastAPI architecture should be designed to accommodate the evidence connector from the start — add a `/api/research/` route namespace and a pluggable source registry, so you don't have to restructure later.

## 5. Credential Security Infrastructure

The repo has dedicated security tooling:
- `scripts/check_credentials.py` — validates credentials [URL3]
- `SECURITY.md` — security policy [URL3]
- `.pre-commit-config.yaml` — pre-commit hooks [URL3]
- The Freebuff conversation mentioned a "credential guard" pattern [URL3]

**What this means:** The FastAPI layer must maintain the same credential hygiene. Never log API keys, never expose tokens in responses, and the `.env.example` should be updated with all new FastAPI env vars (FastAPI secret key, CORS origins, session secret, etc.).

## 6. Smoke Test Script Exists

`scripts/smoke_test.sh` (3.5KB) exists for the current Streamlit app. [URL3]

**What this means:** You'll need a new smoke test script for the React + FastAPI stack — one that boots both services, hits the health endpoint, uploads a test CSV, and verifies the chat streaming works.

## 7. BrainGuide/Braintree Client Context

The Freebuff conversation and the whisperer-30's chat route both reference a **BrainGuide** client — a public health product with equity analysis, language access, and device access metrics. There's also `BRAINTREE_CHECKLIST.md` (6.5KB) and `braintree-reqs.md` (49KB). [URL3]

**What this means:** The system prompt in the whisperer-30's `chat.ts` is already tuned for this client. When wiring the React store to FastAPI, make sure the Gemini system prompt (currently in `utils/prompt_templates.py`) is the one that gets used — not the whisperer-30's hardcoded version.

## 8. Two Package Managers in Play

| Component | Package Manager | Lock File |
|---|---|---|
| Drive Picker frontend | npm | `package-lock.json` (52KB) |
| Whisperer-30 React app | bun | `bun.lock` (150KB) |

**What this means:** Standardize on one. Bun is faster and the whisperer-30 already uses it, but npm is more widely supported in CI/CD environments. If you pick bun, make sure Cloud Build and GitHub Actions both support it.

## Updated Checklist

Based on all of this, add these items to the migration plan:

- [ ] Add migration plan as `plans/🔴 v0.4.0-react-migration.md` following existing naming convention
- [ ] Align FastAPI endpoints with existing `plans/ga4-measurement-contract.md`
- [ ] Design `/api/research/` route namespace for the evidence connector (per `evidence-connector-design.md`)
- [ ] Update both `.github/workflows/test.yml` AND `cloudbuild.yaml`
- [ ] Standardize on one package manager (bun or npm) across Drive Picker + React frontend
- [ ] Update `scripts/smoke_test.sh` for React + FastAPI stack
- [ ] Update `.env.example` with all new FastAPI env vars
- [ ] Ensure FastAPI maintains credential guard patterns from `scripts/check_credentials.py`
- [ ] Use `utils/prompt_templates.py` for Gemini system prompt, not the whisperer-30's hardcoded version
- [ ] Preserve design decisions from `plans/interstitial-ui-polish-design.md` in the React UI

Want me to update the migration plan file with these additions, or create GitHub issues for each?
### 2.12 [PASTE 10] — Perplexity: "I prepared an implementation packet…"

I prepared an implementation packet covering all three requested areas in **`phase-1-api-react-callback-tests-implementation.md`**.

## Included

- **FastAPI Phase 1 vertical slice:** configuration, session handling, schemas, upload/data-context/preview routes, GA4 OAuth-start and callback adapters, health endpoint, CORS, and a clear boundary for connecting existing Python utilities.
- **React GA4 callback route:** a TanStack Router component for `/auth/ga4/callback`, including success, cancellation, invalid-state, and token-exchange failure states.
- **Test migration approach:** replaces direct `mock-ga4.ts` / `mock-braintree.ts` imports with MSW network handlers, plus upload, error, and OAuth callback test examples.

## Important adjustment

The original Freebuff prompt described React as the OAuth callback target. The implementation packet corrects that: **Google should redirect to FastAPI**, which validates OAuth `state`, exchanges the code server-side, stores credentials server-side, then redirects the browser to the React callback page with only `status=success` or a safe error reason. Provider access tokens must never reach React. The existing repo already has real GA4 and Drive client modules, a credential-check script, pre-commit setup, and CI, so the FastAPI adapters should reuse those controls rather than duplicate provider logic. [URL4]

## Suggested order

1. Implement and test `/healthz`, `/api/upload`, `/api/data/context`, and `/api/data/preview`.
2. Add MSW-based React-store tests and remove production imports of mock files.
3. Add the OAuth start/callback flow, backed by the existing `utils/ga4_client.py`.
4. Only then move to Drive, Gemini streaming chat, analysis, and exports.
### 2.13 [FILE] — `freebuff-prompt-wire-react-store.md` (verbatim copy)

> Appended by direct copy of the file on disk; nothing edited.

---

### 2.14 [FILE] — `phase-1-api-react-callback-tests-implementation.md` (verbatim copy)

> Appended by direct copy of the file on disk; nothing edited.

---
# Freebuff Prompt: Wire explorer-store.tsx to FastAPI Endpoints

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
- A streamAi() helper that calls /api/chat with POST and reads the SSE stream
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

The existing streamAi() already calls /api/chat. Update it to point to FastAPI instead of the Lovable/TanStack server route:

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

Note: The FastAPI /api/chat endpoint must return a Server-Sent Events (SSE) stream. The streamText response format from the Vercel AI SDK uses plain text streaming, so FastAPI should return StreamingResponse with media_type="text/event-stream" or "text/plain" depending on the format. Check the FastAPI implementation and adjust the reader accordingly.

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
  POST /api/chat → proxy to http://localhost:8000/api/chat

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
# Phase 1 Implementation Packet
## FastAPI endpoints, React GA4 callback, and mock-to-API test updates

**Status:** Prepared implementation blueprint — no repository files have been changed.

This packet implements the first vertical slice only: **upload a CSV/XLSX → create a server session → receive a serialized data context → render it in React**. It also includes the GA4 OAuth callback route and the testing approach needed when `mock-ga4.ts`/`mock-braintree.ts` are removed.

> Important: keep all actual GA4, Drive, Gemini, and data-processing logic in Python. The FastAPI layer is an adapter around existing `utils/`; React is never allowed to receive provider credentials or access tokens.

---

## 1. Target layout

```text
insights-explorer/
  api/
    __init__.py
    main.py
    config.py
    dependencies.py
    schemas.py
    services/
      __init__.py
      dataset_service.py
      ga4_service.py
    routes/
      __init__.py
      health.py
      upload.py
      ga4.py
  frontend/
    src/
      lib/
        api.ts
        api-types.ts
        explorer-store.tsx
      routes/
        auth/
          ga4/
            callback.tsx
      test/
        server.ts
        handlers.ts
        render.tsx
```

Keep the current Streamlit UI alive while this new vertical slice is introduced. It should call the same Python services temporarily, but should not call FastAPI from inside Streamlit.

---

## 2. Python dependencies

Add these to `requirements.txt` or a new `requirements/api.txt`:

```txt
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
python-multipart>=0.0.9,<1
pydantic-settings>=2.0,<3
itsdangerous>=2.2,<3
```

Do **not** add a database or Redis in Phase 1. Use an in-memory server-side session store only for local development and a single-instance staging deploy. Make the storage implementation swappable before production.

---

## 3. FastAPI configuration

### `api/config.py`

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_cors_origins: str = "http://localhost:5173"
    api_session_secret: str
    frontend_url: str = "http://localhost:5173"
    max_upload_bytes: int = 25 * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.api_cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Add, but do not commit, these `.env` values:

```dotenv
API_SESSION_SECRET=replace-with-a-long-random-value
API_CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
MAX_UPLOAD_BYTES=26214400
```

Update `.env.example` with variable names and safe placeholders only. Continue using `scripts/check_credentials.py` and pre-commit secret checks; add the new session secret to their allowed/required configuration if necessary.

---

## 4. Session dependency

### `api/dependencies.py`

```python
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4

from fastapi import Cookie, HTTPException, Response, status

SESSION_COOKIE = "insights_session"


@dataclass
class AppSession:
    dataset_id: str | None = None
    ga4_credentials: dict | None = None
    oauth_state: str | None = None
    metadata: dict = field(default_factory=dict)


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, AppSession] = {}
        self._lock = RLock()

    def create(self) -> tuple[str, AppSession]:
        session_id = uuid4().hex
        session = AppSession()
        with self._lock:
            self._sessions[session_id] = session
        return session_id, session

    def get(self, session_id: str) -> AppSession | None:
        with self._lock:
            return self._sessions.get(session_id)


sessions = InMemorySessionStore()


def get_or_create_session(
    response: Response,
    insights_session: str | None = Cookie(default=None),
) -> AppSession:
    session = sessions.get(insights_session) if insights_session else None
    if session:
        return session

    session_id, session = sessions.create()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=False,  # Set True in production HTTPS.
        samesite="lax",
        max_age=60 * 60 * 8,
        path="/",
    )
    return session


def require_dataset(session: AppSession = None) -> AppSession:
    if not session or not session.dataset_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active dataset. Upload a file or connect GA4 first.",
        )
    return session
```

**Production replacement:** Replace `InMemorySessionStore` with a server-side store (Redis or Postgres), retain only a signed opaque session ID in the `HttpOnly` cookie, set `secure=True`, set a real cookie domain if needed, and use a narrow CORS allowlist.

---

## 5. API schemas

### `api/schemas.py`

```python
from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start: date | None = None
    end: date | None = None


class Column(BaseModel):
    name: str
    type: Literal["date", "number", "string", "boolean", "unknown"]
    nullable: bool


class DatasetContext(BaseModel):
    source: Literal["upload", "ga4", "drive"]
    filename: str
    row_count: int = Field(ge=0)
    date_range: DateRange
    columns: list[Column]
    filters: list[dict] = Field(default_factory=list)
    metrics: list[dict] = Field(default_factory=list)
    provenance: dict = Field(default_factory=dict)


class UploadResponse(BaseModel):
    dataset: DatasetContext


class GA4ConnectResponse(BaseModel):
    authorization_url: str


class APIError(BaseModel):
    detail: str
```

Use snake_case internally in FastAPI first. If the React store is already camelCase-heavy, configure Pydantic aliases at the API boundary rather than creating two parallel schemas.

---

## 6. Dataset-service adapter

### `api/services/dataset_service.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

import pandas as pd

from api.schemas import Column, DatasetContext, DateRange


@dataclass
class StoredDataset:
    id: str
    dataframe: pd.DataFrame
    context: DatasetContext


class DatasetStore:
    def __init__(self) -> None:
        self._items: dict[str, StoredDataset] = {}

    def put(self, dataframe: pd.DataFrame, context: DatasetContext) -> StoredDataset:
        item = StoredDataset(id=uuid4().hex, dataframe=dataframe, context=context)
        self._items[item.id] = item
        return item

    def get(self, dataset_id: str) -> StoredDataset | None:
        return self._items.get(dataset_id)


datasets = DatasetStore()


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    return "string"


def make_context(df: pd.DataFrame, *, source: str, filename: str) -> DatasetContext:
    date_columns = [column for column in df.columns if pd.api.types.is_datetime64_any_dtype(df[column])]
    start = end = None
    if date_columns:
        values = df[date_columns[0]].dropna()
        if not values.empty:
            start = values.min().date()
            end = values.max().date()

    return DatasetContext(
        source=source,
        filename=filename,
        row_count=len(df),
        date_range=DateRange(start=start, end=end),
        columns=[
            Column(
                name=str(column),
                type=infer_column_type(df[column]),
                nullable=bool(df[column].isna().any()),
            )
            for column in df.columns
        ],
        provenance={
            "created_at": datetime.now(timezone.utc).isoformat(),
            "transformations": [],
        },
    )


def parse_uploaded_file(filename: str, content: bytes) -> pd.DataFrame:
    """Adapter boundary.

    Replace the pandas parsing branch with the existing vetted loader in
    utils/data_loader.py once its Streamlit cache/UI coupling is extracted.
    Do not duplicate validation, supported-file, or error-taxonomy logic.
    """
    suffix = Path(filename).suffix.lower()
    with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        if suffix == ".csv":
            return pd.read_csv(tmp.name)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(tmp.name)
    raise ValueError("Supported formats are CSV, XLSX, and XLS.")
```

**Adapter rule:** once `utils/data_loader.py` exposes a pure `load_file(path_or_bytes)` function, replace `parse_uploaded_file()` rather than maintaining two parsers. The same rule applies to `utils/data_context.py`: prefer its established filter/metric/provenance rules over this initial serializer.

---

## 7. Upload and preview routes

### `api/routes/upload.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from api.config import get_settings
from api.dependencies import AppSession, get_or_create_session
from api.schemas import DatasetContext, UploadResponse
from api.services.dataset_service import datasets, make_context, parse_uploaded_file

router = APIRouter(prefix="/api", tags=["data"])

ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    response: Response,
    file: UploadFile = File(...),
    session: AppSession = Depends(get_or_create_session),
) -> UploadResponse:
    settings = get_settings()
    filename = file.filename or "upload"
    suffix = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload a CSV, XLSX, or XLS file.")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit.")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        dataframe = parse_uploaded_file(filename, content)
        context = make_context(dataframe, source="upload", filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Log exception metadata server-side; never echo file contents or secrets.
        raise HTTPException(status_code=422, detail="Unable to parse this file.") from exc

    stored = datasets.put(dataframe, context)
    session.dataset_id = stored.id
    return UploadResponse(dataset=stored.context)


@router.get("/data/context", response_model=DatasetContext)
def get_data_context(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> DatasetContext:
    if not session.dataset_id:
        raise HTTPException(status_code=409, detail="No active dataset.")
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")
    return dataset.context


@router.get("/data/preview")
def get_data_preview(
    response: Response,
    limit: int = 10,
    session: AppSession = Depends(get_or_create_session),
) -> dict:
    if not session.dataset_id:
        raise HTTPException(status_code=409, detail="No active dataset.")
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")

    safe_limit = min(max(limit, 1), 100)
    frame = dataset.dataframe.head(safe_limit).where(dataset.dataframe.notna(), None)
    return {
        "dataset": dataset.context.model_dump(mode="json"),
        "rows": frame.to_dict(orient="records"),
    }
```

### `api/routes/health.py`

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

---

## 8. GA4 OAuth endpoints

### `api/services/ga4_service.py`

```python
from __future__ import annotations

import secrets
from urllib.parse import urlencode

from api.config import get_settings


def begin_oauth() -> tuple[str, str]:
    """Adapter boundary for utils/ga4_client.py.

    Replace URL construction with the existing GA4 OAuth client as soon as it
    exposes a framework-neutral authorization-url function.
    """
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    callback_url = f"{settings.frontend_url.rstrip('/')}/auth/ga4/callback"

    # Placeholder: use only the provider library already used by ga4_client.py.
    # Do not hand-roll token exchange or duplicate the project's OAuth scopes.
    params = {
        "client_id": "READ_FROM_EXISTING_GA4_CONFIG",
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/analytics.readonly",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return state, "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def exchange_code(code: str) -> dict:
    """Call the existing ga4_client token-exchange implementation here.

    Do not put client secrets in React, query strings, error messages, or logs.
    """
    raise NotImplementedError("Wire this adapter to utils.ga4_client.")
```

### `api/routes/ga4.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse

from api.config import get_settings
from api.dependencies import AppSession, get_or_create_session
from api.schemas import GA4ConnectResponse
from api.services.ga4_service import begin_oauth, exchange_code

router = APIRouter(prefix="/api/ga4", tags=["GA4"])


@router.post("/connect", response_model=GA4ConnectResponse)
def connect_ga4(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> GA4ConnectResponse:
    state, authorization_url = begin_oauth()
    session.oauth_state = state
    return GA4ConnectResponse(authorization_url=authorization_url)


@router.get("/callback")
def ga4_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    response: Response = None,
    session: AppSession = Depends(get_or_create_session),
):
    settings = get_settings()
    callback = f"{settings.frontend_url.rstrip('/')}/auth/ga4/callback"

    if error:
        return RedirectResponse(f"{callback}?status=error&reason=provider_denied")
    if not code or not state or not secrets.compare_digest(state, session.oauth_state or ""):
        return RedirectResponse(f"{callback}?status=error&reason=invalid_oauth_state")

    try:
        session.ga4_credentials = exchange_code(code)
        session.oauth_state = None
        return RedirectResponse(f"{callback}?status=success")
    except Exception:
        # Record sanitized diagnostic server-side.
        return RedirectResponse(f"{callback}?status=error&reason=token_exchange_failed")
```

**Correction before implementation:** The OAuth `redirect_uri` must point to the **FastAPI callback** (`https://api.example.com/api/ga4/callback`), not React. Google redirects to FastAPI; FastAPI validates `state`, exchanges the code, sets server session state, and then redirects the browser to React at `/auth/ga4/callback?status=success`. Replace the placeholder callback URL in `begin_oauth()` accordingly.

---

## 9. FastAPI application entry point

### `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import ga4, health, upload

settings = get_settings()
app = FastAPI(title="Insights Explorer API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(ga4.router)
```

Add `api/routes/__init__.py` and `api/services/__init__.py` as empty files.

Run locally:

```bash
uvicorn api.main:app --reload --port 8000
```

Expected checks:

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

---

## 10. React API client

### `frontend/src/lib/api-types.ts`

```ts
export type SourceKind = "upload" | "ga4" | "drive";

export interface DateRange {
  start: string | null;
  end: string | null;
}

export interface Column {
  name: string;
  type: "date" | "number" | "string" | "boolean" | "unknown";
  nullable: boolean;
}

export interface DataContext {
  source: SourceKind;
  filename: string;
  row_count: number;
  date_range: DateRange;
  columns: Column[];
  filters: Record<string, unknown>[];
  metrics: Record<string, unknown>[];
  provenance: Record<string, unknown>;
}

export interface UploadResponse {
  dataset: DataContext;
}

export interface DataPreviewResponse {
  dataset: DataContext;
  rows: Record<string, unknown>[];
}

export interface ApiError {
  detail: string;
}
```

### `frontend/src/lib/api.ts`

```ts
import type { DataContext, DataPreviewResponse, UploadResponse } from "./api-types";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

async function assertOk(response: Response): Promise<Response> {
  if (response.ok) return response;
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(body?.detail ?? `Request failed (${response.status})`);
}

export async function uploadDataset(file: File): Promise<DataContext> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await assertOk(
    await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
      credentials: "include",
    }),
  );
  const payload = (await response.json()) as UploadResponse;
  return payload.dataset;
}

export async function fetchPreview(): Promise<DataPreviewResponse> {
  const response = await assertOk(
    await fetch(`${API_BASE}/data/preview`, { credentials: "include" }),
  );
  return response.json() as Promise<DataPreviewResponse>;
}

export async function beginGa4OAuth(): Promise<void> {
  const response = await assertOk(
    await fetch(`${API_BASE}/ga4/connect`, {
      method: "POST",
      credentials: "include",
    }),
  );
  const { authorization_url } = (await response.json()) as { authorization_url: string };
  window.location.assign(authorization_url);
}
```

Always send `credentials: "include"`; otherwise the browser will not return the session cookie needed to correlate upload, OAuth, and analysis requests.

---

## 11. React OAuth callback route

Create the route matching the TanStack file-routing convention already used by the app.

### `frontend/src/routes/auth/ga4/callback.tsx`

```tsx
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AlertCircle, CheckCircle2, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchPreview } from "@/lib/api";
import { useExplorer } from "@/lib/explorer-store";

export const Route = createFileRoute("/auth/ga4/callback")({
  component: Ga4CallbackPage,
});

type CallbackState = "loading" | "success" | "error";

function readableReason(reason: string | undefined): string {
  switch (reason) {
    case "provider_denied":
      return "Google authorization was cancelled. No data was connected.";
    case "invalid_oauth_state":
      return "The authorization session expired or could not be verified. Please try again.";
    case "token_exchange_failed":
      return "Google authorization completed, but Insights Explorer could not establish a GA4 session.";
    default:
      return "We could not connect Google Analytics. Please try again.";
  }
}

function Ga4CallbackPage() {
  const navigate = useNavigate();
  const { setSourceFromApi, setLoadState, setError } = useExplorer();
  const search = new URLSearchParams(window.location.search);
  const status = search.get("status");
  const reason = search.get("reason") ?? undefined;
  const [state, setState] = useState<CallbackState>(status === "success" ? "loading" : "error");

  useEffect(() => {
    if (status !== "success") {
      setError(readableReason(reason));
      setLoadState("error");
      return;
    }

    let cancelled = false;
    async function finishConnection() {
      try {
        setLoadState("loading");
        const preview = await fetchPreview();
        if (cancelled) return;
        setSourceFromApi(preview.dataset);
        setLoadState("ready");
        setState("success");
        window.setTimeout(() => navigate({ to: "/" }), 700);
      } catch (error) {
        if (cancelled) return;
        const message = error instanceof Error ? error.message : "Unable to load the GA4 dataset.";
        setError(message);
        setLoadState("error");
        setState("error");
      }
    }
    void finishConnection();
    return () => {
      cancelled = true;
    };
  }, [navigate, reason, setError, setLoadState, setSourceFromApi, status]);

  const isSuccess = state === "success";
  const isLoading = state === "loading";

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <section className="w-full max-w-md rounded-md border border-border bg-card p-6" aria-live="polite">
        {isLoading ? <LoaderCircle className="mb-4 size-6 animate-spin text-primary" aria-hidden /> : null}
        {isSuccess ? <CheckCircle2 className="mb-4 size-6 text-emerald-500" aria-hidden /> : null}
        {state === "error" ? <AlertCircle className="mb-4 size-6 text-destructive" aria-hidden /> : null}
        <h1 className="text-lg font-semibold">
          {isLoading ? "Connecting Google Analytics…" : isSuccess ? "Google Analytics connected" : "Connection unsuccessful"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {isLoading
            ? "Loading your selected analytics data."
            : isSuccess
              ? "Returning you to Insights Explorer."
              : readableReason(reason)}
        </p>
        {state === "error" ? (
          <button className="mt-5 rounded-sm bg-primary px-3 py-2 text-sm text-primary-foreground" onClick={() => navigate({ to: "/" })}>
            Return to explorer
          </button>
        ) : null}
      </section>
    </main>
  );
}
```

### Required store addition

The route requires a non-UI setter so it does not recreate upload logic:

```ts
setSourceFromApi: (dataset: DataContext) => void;
```

Its implementation should normalize Python snake_case fields at **one** boundary, then set existing store state. Do not scatter `row_count` → `rowCount` conversions across components.

---

## 12. Test updates: replace mock-module tests

### Testing principle

Do not replace `mock-ga4.ts` with a production fixture that components import. Instead:

- **Unit tests:** Mock the network boundary with MSW.
- **Store tests:** Test loading, ready, error, and streaming behavior against MSW responses.
- **Component tests:** Render real provider + MSW; assert user-visible state.
- **E2E:** Use Playwright against FastAPI staging/local test mode for upload and OAuth error/success paths.

This keeps test data out of production code and prevents components from knowing whether data is mock or live.

### Add dependencies in `frontend/package.json`

```json
{
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.6.1",
    "jsdom": "^25.0.0",
    "msw": "^2.4.0",
    "vitest": "^2.1.0"
  },
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

### `frontend/src/test/handlers.ts`

```ts
import { http, HttpResponse } from "msw";
import { API_BASE } from "@/lib/api";

export const uploadedDataset = {
  source: "upload",
  filename: "analytics.csv",
  row_count: 3,
  date_range: { start: "2026-01-01", end: "2026-01-03" },
  columns: [
    { name: "date", type: "date", nullable: false },
    { name: "sessions", type: "number", nullable: false },
  ],
  filters: [],
  metrics: [],
  provenance: { created_at: "2026-08-05T00:00:00Z", transformations: [] },
};

export const handlers = [
  http.post(`${API_BASE}/upload`, async () => HttpResponse.json({ dataset: uploadedDataset }, { status: 201 })),
  http.get(`${API_BASE}/data/preview`, () =>
    HttpResponse.json({
      dataset: uploadedDataset,
      rows: [
        { date: "2026-01-01", sessions: 30 },
        { date: "2026-01-02", sessions: 50 },
      ],
    }),
  ),
  http.post(`${API_BASE}/ga4/connect`, () =>
    HttpResponse.json({ authorization_url: "https://accounts.google.com/test-oauth" }),
  ),
];
```

### `frontend/src/test/server.ts`

```ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

### `frontend/src/test/setup.ts`

```ts
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Upload/store behavior test

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ExplorerProvider, useExplorer } from "@/lib/explorer-store";

function TestHarness() {
  const { loadData, loadState, source, error } = useExplorer();
  return (
    <>
      <input
        aria-label="Upload data"
        type="file"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0];
          if (file) void loadData(file, "upload");
        }}
      />
      <output data-testid="status">{loadState}</output>
      <output data-testid="filename">{source?.filename ?? ""}</output>
      <output data-testid="error">{error ?? ""}</output>
    </>
  );
}

describe("ExplorerProvider", () => {
  it("uploads a file and exposes the server dataset to consumers", async () => {
    const user = userEvent.setup();
    render(
      <ExplorerProvider>
        <TestHarness />
      </ExplorerProvider>,
    );

    await user.upload(
      screen.getByLabelText("Upload data"),
      new File(["date,sessions\n2026-01-01,30"], "analytics.csv", { type: "text/csv" }),
    );

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("ready"));
    expect(screen.getByTestId("filename")).toHaveTextContent("analytics.csv");
    expect(screen.getByTestId("error")).toHaveTextContent("");
  });
});
```

### Error-state test

```tsx
import { http, HttpResponse } from "msw";
import { server } from "@/test/server";
import { API_BASE } from "@/lib/api";

it("surfaces upload errors instead of silently retaining mock data", async () => {
  server.use(
    http.post(`${API_BASE}/upload`, () => HttpResponse.json({ detail: "Uploaded file is empty." }, { status: 400 })),
  );

  // Render the same harness, upload an empty file, then assert:
  // loadState === "error" and error includes "Uploaded file is empty."
});
```

### OAuth callback tests

Test three cases by setting the route search string and mocking `GET /data/preview`:

1. `?status=success`: calls preview, writes dataset to store, navigates home.
2. `?status=error&reason=provider_denied`: shows cancellation explanation and return button.
3. `?status=success` + preview failure: shows API error and does not navigate.

### Delete/update tests that do this

```ts
vi.mock("@/lib/mock-ga4", () => ({ defaultSource: ... }));
```

Replace with MSW response overrides. Delete `mock-ga4.ts` and `mock-braintree.ts` only after all direct imports are removed; during the transition, move test fixtures into `src/test/fixtures/`, not `src/lib/`.

---

## 13. Definition of done for this slice

- [ ] `GET /healthz` returns `{"status":"ok"}`.
- [ ] React upload sends multipart data to FastAPI with credentials included.
- [ ] FastAPI returns a validated dataset context and persists it in the current server session.
- [ ] React store transitions `idle → loading → ready`; failed upload transitions to `error` with a visible message.
- [ ] Existing UI components consume the existing `useExplorer()` API; they do not import mock data.
- [ ] `mock-ga4.ts` and `mock-braintree.ts` have no production imports.
- [ ] OAuth callback validates state server-side, performs token exchange server-side, and never exposes a provider token to React.
- [ ] Unit/component tests use MSW; no test depends on live GA4, Drive, Gemini, or Lovable.
- [ ] `pytest`, React unit tests, TypeScript build, and the existing smoke-test suite pass before the next endpoint family is added.

---

## Do not do in Phase 1

- Do not implement Drive Picker, Gemini chat streaming, forecasting, funnels, or exports yet.
- Do not move secrets into `VITE_*` variables; Vite exposes these to the browser.
- Do not redirect Google OAuth directly to React.
- Do not deploy FastAPI and React on separate production origins unless there is a clear need; same-origin deployment avoids fragile cross-site cookie behavior.
- Do not delete Streamlit or archive the Lovable repo until feature parity and regression coverage exist.
---

### 2.15 [PASTE 11] — Perplexity: "product-platform migration" review (security, session, contracts, testing, deployment)

Yes. The main thing to keep in mind is that this is a **product-platform migration**, not merely a frontend replacement: data/session ownership, OAuth, security, testing, CI, and deployment all change together.

## Address immediately

- **Check the tracked `.env` in `insights-whisperer-30`.** The repository root includes an actual `.env` file, not just `.env.example`. Treat it as potentially exposed: inspect its Git history, revoke/rotate any Lovable, Google, Gemini, or other API credentials that may have been committed, remove it from the index, and add a safe `.env.example`. Do this before copying the project into the canonical repo. [URL5]
- **Create a migration branch and freeze broad feature work.** Use something like `feat/react-fastapi-migration`; allow only production/security fixes to the Streamlit UI while the API contract stabilizes. Otherwise, every new Streamlit feature becomes a second migration obligation. [URL5]
- **Do not use the Lovable AI gateway as the permanent backend path.** The React repo has a Lovable-specific gateway and a hardcoded model reference. Move AI routing to Python/FastAPI so your provider, model, quotas, rate limits, data boundaries, and prompt logic remain under your control. [URL5]

## Treat state as a first-class design

The largest hidden migration cost is not chart rendering; it is moving `st.session_state` safely. It appears across `app.py`, `utils/session.py`, data loading, Gemini logic, GA4 logic, and multiple UI components—so make a written inventory of every key, its owner, lifecycle, and replacement before changing code. [URL5]

Use a server-owned session model:

- Browser keeps only an opaque, `HttpOnly`, secure session cookie.
- FastAPI owns the dataset reference, OAuth credentials, filter state, selected metrics, and chat context.
- Raw uploaded data and provider tokens never go to localStorage, React state persistence, URLs, logs, or client-side analytics.
- Design a storage abstraction now: in-memory for local development, Redis/Postgres-compatible for deployed multi-instance hosting.

## Keep contracts stable

You already have a GA4 measurement contract in `plans/ga4-measurement-contract.md`; make it the source of truth for API request/response schemas. Do not let the React mock types become a competing domain model. [URL5]

Also establish these rules before implementation:

- Python uses canonical domain models; FastAPI serializes them at a single API boundary.
- React gets a typed client generated or validated from OpenAPI/JSON Schema.
- Normalize naming once—either FastAPI emits camelCase or the API client translates snake_case. Do not make individual React components translate fields.
- Version the API early, even if only as `/api/v1`, so future work such as the evidence connector can evolve safely.

## Preserve existing work deliberately

The repo has a mature plans structure, credential checks, smoke tests, GitHub Actions, Cloud Build, and a standalone TypeScript Drive Picker. These are assets to migrate, not incidental files to replace. [URL5]

A few practical implications:

- Update **both** GitHub Actions and `cloudbuild.yaml`; otherwise a passing Python CI build may hide a broken React build or vice versa.
- Consolidate package management. The Drive Picker uses npm while the Lovable app uses Bun; choose one before adding a third frontend build path.
- Reuse the Drive Picker behavior, its file-size safeguards, and its error taxonomy—but port it as a native React component rather than retaining an embedded Streamlit component.
- Preserve the `utils/prompt_templates.py` behavior and client/data safeguards; do not let the React prototype's hardcoded BrainGuide system prompt silently become production logic. [URL5]

## Test by behavior, not implementation

Your current test count is valuable, but it will not transfer one-to-one. Streamlit component tests should not be mechanically preserved; replace them with tests at the right boundary:

| Layer | What to protect |
|---|---|
| Python unit tests | Parsing, GA4/Drive behavior, analysis, quality, forecasting, exports, sanitization |
| FastAPI contract tests | Auth/session behavior, schema validity, error taxonomy, upload limits, OAuth state validation |
| React unit/component tests | Loading, empty, error, success, accessibility, API-client behavior |
| Playwright E2E | Upload → preview → chart; GA4 OAuth error/success; Drive selection; AI streaming; export |

Use MSW for frontend tests rather than importing `mock-ga4.ts` into product components. The mock modules should become test fixtures only; that prevents a half-migrated production UI from accidentally rendering stale fake data. [URL5]

## Deployment decisions matter early

Avoid a production split between unrelated frontend and API origins unless you have a strong reason. Same-origin deployment—React served as static assets behind the FastAPI/container deployment—makes cookie-based sessions, OAuth callbacks, CORS, and SSE streaming much simpler.

Before selecting Railway, Render, Fly, or GCP, define:

- Expected file size, concurrent users, and GA4 query volume.
- Background-task needs for large imports or report exports.
- Session/data retention rules.
- Observability: structured logs, request IDs, sanitized error reporting, health/readiness endpoints.
- Rate limits and per-user quotas for Gemini/AI use.

## Scope the first release tightly

Your Phase 1 should prove one end-to-end path:

> Upload CSV → validate through existing Python logic → server session → React preview/quality state → clear-data → regression tests.

Do not start with GA4 OAuth, Drive Picker, chat streaming, evidence research, forecasting, and exports simultaneously. Those are distinct risk families. Once the upload vertical slice is solid, add GA4, then Drive, then AI streaming, then advanced analysis.

## One more strategic point

Keep `insights-whisperer-30` as a **living design reference until cutover**, rather than immediately merging and archiving it. Copy it into the canonical repo when the frontend build is reproducible, but retain the original for visual comparison, regression checking, and a clean fallback while the React app reaches parity. The React project's mock-data and AI gateway orientation reinforces that it is a prototype/frontend asset—not the system of record. [URL5]
---

## Part 3 — External research context (added 2026-08-05)

> Source-backed research gathered via web/docs research agents and direct fetches of official documentation (2026-08-05). Purpose: validate the claims the migration docs rely on, surface corrections, and record external context for future implementation. Each subsection gives the finding, the source, and the implication. Where a research agent could not fetch a live page, the entry is flagged **[tool-knowledge — verify at implementation]**.

### 3.1 Hosting: FastAPI + React on a single origin (Railway / Render / Fly.io)

| Platform | Python ASGI (uvicorn) | SPA + API same origin | Approx. small-app cost | Main gotcha |
|---|---|---|---|---|
| **Railway** | ✅ (Nixpacks or Dockerfile) | ✅ via container (`StaticFiles`) | ~$5–10/mo beyond credits | Nixpacks auto-detects a single language when the repo mixes Node + Python → use a multi-stage Dockerfile or `nixpacks.toml` |
| **Render** | ✅ Web Services | ✅ only via Docker-based Web Service | Free (spins down after 15 min; ~30–50 s cold start) / Individual ~$7/mo | Default UI pushes split Static Site + Web Service → **split origins break the same-origin cookie rule** |
| **Fly.io** | ✅ (any OCI container) | ✅ via multi-stage Dockerfile | ~$3–5/mo | Must bake `VITE_*` env at build time, not runtime; Fly Volumes for uploads need explicit mount config |

- **Sources:** Railway FastAPI guide (docs.railway.com/guides/fastapi) · Render FastAPI guide (docs.render.com/docs/deploy-fastapi) · Fly.io FastAPI guide (fly.io/docs/python/frameworks/fastapi/).
- **Implication:** the packet's "same-origin deployment preferred" rule is achievable on all three, but only by bundling the Vite build into the FastAPI container (multi-stage Dockerfile). Streamlit Community Cloud is confirmed **unable** to run FastAPI or React (strictly `streamlit run`) — the plan's "hosting change required" risk is real and hosting remains its own workstream (open question #1).

### 3.2 Google OAuth 2.0 (GA4) — what the packet got right + PKCE

- **Confirmed correct in F4:** `state` generated server-side and compared with `compare_digest` on callback (CSRF protection) — matches Google's web-server-app guidance; tokens stored server-side only and never exposed to React; code exchanged via a server-to-server call.
- **Gap to add:** **PKCE** (S256 `code_verifier` / `code_challenge`) is recommended for all client types under RFC 9700 / OAuth 2.1 — add it to `begin_oauth()` / `exchange_code()` even though this is a confidential web app.
- **Gotcha:** the configured `redirect_uri` must be an **exact string match** (scheme, host, path, trailing slash) — keep `callback_url` construction in one place (F4's `config.py` + adapter).
- **Sources:** Google "Using OAuth 2.0 for Web Server Applications" (developers.google.com/identity/protocols/oauth2/web-server) · RFC 9700 (datatracker.ietf.org/doc/rfc9700/).

### 3.3 Google Picker API — launch requirements

- To launch the Picker, the frontend needs three things: the **developer API key** (`setDeveloperKey`), an **OAuth access token** (`setOAuthToken`), and the **project number / App ID** (`setAppId`).
- The project number comes from Cloud Console (IAM & Admin → Settings); retrieving it programmatically may require enabling the **Cloud Resource Manager API** — exactly the setup hurdle hit during the v0.3.0 Drive-import work.
- Restrict the API key to the app's HTTP referrers and to the required APIs. Legacy client libraries are deprecated in favor of **Google Identity Services (GIS)** + the API loader. Third-party-cookie blocking (browser privacy settings, embedded iframes) can break Picker sign-in state — consistent with the earlier "Comet browser can't open the Picker" symptom.
- **Sources:** Google Workspace "Integrate the Google Picker into web apps" + web-picker sample (developers.google.com/workspace/drive/picker/guides/web-picker).
- **Implication:** `POST /api/drive/picker-token` should return the token **and** the project number; document Cloud Resource Manager API enablement in the Drive-import setup notes.

### 3.4 GA4 Data API — aggregate-only confirmed + the funnel nuance

- **Aggregate-only:** `runReport` returns aggregated report tables (dimensions × metrics), not event-level rows. Up to **9 dimensions** per request; default page **10,000 rows**, paginate with `limit`/`offset` for more.
- **Quotas (standard property):** Core tokens 200,000/property/day (2,000,000 for Analytics 360) · 40,000/hour · 14,000 per project-per-property/hour · **10 concurrent requests** · 10 server errors per project-per-property/hour · 120 potentially-thresholded requests/hour (thresholds apply to demographic dimensions).
- **Event-level data requires BigQuery export / Measurement Protocol / Data Streams** — the roadmap's "hard blocker" (no event/session/user identifiers via the report API) is **confirmed**.
- **Nuance worth recording:** the Data API has a dedicated **`runFunnelReport`** (Funnel quota category) — *template* funnels (steps defined by event/dimension filters) are available without event-level export. User/identifier-level analyses (retention, cohorts, pathing, LTV) remain blocked. Revisit the roadmap rows that mark funnels as unavailable at implementation time — funnel may be partially unblocked.
- **Sources (fetched directly 2026-08-05):** Data API limits & quotas (developers.google.com/analytics/devguides/reporting/data/v1/quotas) · Create a report (developers.google.com/analytics/devguides/reporting/data/v1/basics).

### 3.5 SSE chat streaming — FastAPI framing + Vercel AI SDK wire format

- **FastAPI SSE:** use `StreamingResponse(gen, media_type="text/event-stream")` with `data: <chunk>\n\n` framing (each event ends with a blank line).
- **Vercel AI SDK:** `toTextStreamResponse()` returns **`text/plain`** plain-text chunks — the plain-text `getReader()` + `TextDecoder` accumulation in the store prompt (F3 §6) is **correct** for that format.
- **Caveat:** the SDK's `useChat` hook expects the **structured data-stream** format (`toDataStreamResponse()` / `toUIMessageStreamResponse()`), not plain text/SSE. Pick one wire format for FastAPI (plain SSE vs SDK data-stream) and keep the client reader consistent; don't mix.
- **Sources:** FastAPI docs (fastapi.tiangolo.com, `StreamingResponse`) · Vercel AI SDK (ai-sdk.dev). **[tool-knowledge — verify exact helper names at implementation]**

> **Verification status update (2026-08-05):** this flag is now cleared by round-3 research (§3.10 item 1). The AI SDK docs live at `/v7/` (v7 is the current major), and the captured whisperer-30 `chat.ts` uses `streamText(...).toTextStreamResponse()` — plain text, exactly what F3's reader consumes. The `useChat` caveat stands (it parses the structured v7 protocol, not plain SSE).

### 3.6 Frontend testing & routing — MSW v2 + TanStack Router v1 (live-verified 2026-08-05)

> **Verification status update (2026-08-05):** this section was originally flagged `[tool-knowledge — live docs fetch unavailable]`. It has since been re-verified against the live official sources (direct fetches of npm, mswjs.io, and tanstack.com/router on 2026-08-05). One factual correction surfaced: MSW's `onUnhandledRequest` **default is `"warn"`, not `"bypass"`** (see below). No other claim changed.

**MSW — live-verified:**
- **Current stable: v2.15.0** (`msw@^2.15.0` per npm, published ~July 2026). MSW v2 remains the current major — the v1→v2 `res(ctx.json())` API is gone; the canonical API is `http` + `HttpResponse` imported from `'msw'`, with `setupWorker` from `'msw/browser'` and `setupServer` from `'msw/node'` (confirmed via the npm README usage example and mswjs.io).
- **Node integration** (mswjs.io/docs/integrations/node): `import { setupServer } from 'msw/node'` + `import { handlers } from './handlers'` → `export const server = setupServer(...handlers)`. Three required lifecycle steps: `server.listen()` before all tests, `server.resetHandlers()` between tests, `server.close()` after all tests. The official Vitest example is exactly:
  ```js
  beforeAll(() => server.listen())
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())
  ```
  F4's test design (setupServer, `http`/`HttpResponse` handlers, beforeAll/afterEach/afterAll) **matches** the documented pattern.
- **CORRECTION — `onUnhandledRequest` default:** the live `listen()` reference (mswjs.io/docs/api/setup-server/listen) documents the default as **`"warn"`** — *not* `"bypass"` as an earlier research pass claimed. Valid values: `"warn"` (default), `"error"`, `"bypass"`, or a custom callback `(request, print) => void` (`print.warning()`, etc.). F4's suggested `server.listen({ onUnhandledRequest: "error" })` is a valid, documented strategy — and the right choice in tests when you want stray network calls to fail loudly. Note the official Vitest example uses plain `server.listen()` (i.e., default `"warn"`).
- **Sources:** npmjs.com/package/msw (version) · mswjs.io/docs/integrations/node · mswjs.io/docs/api/setup-server/listen.

**TanStack Router — live-verified:**
- **Current stable: v1.170.20** (`@tanstack/react-router` per npm, published 2026-08-05); route plugin `@tanstack/router-plugin@1.168.25`.
- **File-based routing convention** (tanstack.com/router/latest/docs/routing/file-based-routing): a route file `src/routes/auth/ga4/callback.tsx` maps to `/auth/ga4/callback` via `createFileRoute('/auth/ga4/callback')({ ... })`; directory, flat (`.`) and mixed route structures are all supported. The route tree is auto-generated by the bundler plugin (`@tanstack/router-plugin`, Vite usage via `@tanstack/router-plugin/vite`) during dev/build — no hand-maintained route table. F4's callback route at `src/routes/auth/ga4/callback.tsx` follows this convention.
- **Typed search params** (tanstack.com/router/latest/docs/guide/search-params): `validateSearch` is the type-safe idiom. It accepts a function `(search: Record<string, unknown>) => TypedSearch` **or** a schema object (a raw Zod v4 schema, or `zodValidator()` from `@tanstack/zod-adapter` for Zod v3). Use `.catch()`/fallbacks for malformed params (non-blocking) vs `.default()` when a param should be required for navigation. If validation throws, the route's `onError` fires with `error.routerCode === "VALIDATE_SEARCH"` and `errorComponent` renders — ideal for the GA4 callback page's invalid-state handling.
- **Reading search params:** in the route component use `Route.useSearch()`; outside route components use `useSearch({ from: Route.fullPath })` or `getRouteApi('/auth/ga4/callback').useSearch()` (code-split-safe). This **confirms** §3.8 item 6 and the plan's Phase 4/5 amendments: prefer `validateSearch`/`useSearch` over F4's raw `window.location.search` (which works but bypasses typing, validation, and the error-handling path).
- **Sources:** npmjs.com/package/@tanstack/react-router (version) · npmjs.com/package/@tanstack/router-plugin (package + canonical docs path) · tanstack.com/router/latest/docs/routing/file-based-routing · tanstack.com/router/latest/docs/guide/search-params.

**Implication:** no change to the plan's Phase 4/5 research amendments — both flagged facts are confirmed and now source-backed. The only correction is the `onUnhandledRequest` default (`"warn"`, not `"bypass"`), which matters for test-hygiene expectations: opt into `"error"` deliberately rather than assuming it is the default.

### 3.7 Tooling — bun vs npm in CI; GLM-5.2 facts

- **bun in CI:** GitHub-hosted runners do **not** preinstall bun — use the official `oven-sh/setup-bun@v2` action. Google Cloud Build's Node buildpacks detect bun via `bun.lock` / `bun.lockb` or `GOOGLE_PACKAGE_MANAGER=bun`. npm remains the most portable default across CI providers and build systems.
- **GLM-5.2 (z.ai / Zhipu):** released 2026-06-13; **1M-token context confirmed** (via `glm-5.2[1m]`), up to 131,072 output tokens, sparse MoE + IndexShare attention; **MIT open weights** (self-hostable — relevant for the security-audit use case); pricing $1.40/M input ($0.26 cached) and $4.40/M output — the comparison doc's "roughly 1/10th the cost of frontier models" claim is **largely accurate**; documented strengths align with whole-codebase analysis and security-rules review (agentic tool use, High/Max reasoning modes).
- **Sources:** bun CI docs (bun.com/docs/guides/runtime/cicd) · Cloud Build Node.js buildpacks (cloud.google.com/docs/buildpacks/nodejs) · z.ai pricing (docs.z.ai/guides/overview/pricing) · Eigent AI GLM-5.2 write-up (eigent.ai/blog/glm-5-2).

### 3.8 What the research corrects or confirms — delta summary

**Confirmed (no change needed):**
- Aggregate-only GA4 report API → roadmap "hard blocker" holds for user/identifier-level work.
- Server-side token storage + state validation in F4 match Google guidance.
- F3's plain-text SSE reader is correct for `toTextStreamResponse()`.
- F4's MSW test pattern matches current MSW v2.
- Comparison doc's GLM-5.2 claims (1M context, ~1/10th cost) check out.
- Streamlit Community Cloud cannot host the new stack → hosting is a real workstream.

**Corrections / additions (actionable):**
1. **Add PKCE** to the OAuth flow (F4 §8) — RFC 9700 recommendation.
2. **Picker token endpoint should also return the project number**; document Cloud Resource Manager API enablement (already needed in the v0.3.0 Drive setup).
3. **Decide the chat wire format explicitly**: plain SSE (`text/event-stream`, `data:` framing) vs Vercel AI SDK data-stream — and make the React reader match. F3 §6's open question is now answered: both options exist; pick one.
4. **Funnel nuance:** `runFunnelReport` exists — template funnels may be partially available; revisit ROADMAP funnel rows (Gate 1.7 / Top-25 rows) at implementation time.
5. **Single-origin hosting pattern:** bundle the Vite build into the FastAPI container on all three platforms; avoid Render's split Static Site + Web Service.
6. **TanStack Router:** prefer `validateSearch` / `useSearch` over raw `window.location.search` in the callback route.
7. **GA4 quotas** (10 concurrent requests, token budgets) → the pull service should paginate and throttle; enable `returnPropertyQuota: true` for observability.
8. **GA4 pagination numbers (live).** Default `limit` 10,000 rows; max 250,000 per request — the Phase 5 pull design should page at the default and cap request limits accordingly. *(§3.9 item 1.)*
9. **GA4 quotas refined (live).** “10 concurrent requests” = **Core Concurrent Requests Per Property: 10 (Standard) / 50 (360)**; add token budgets (200k/day, 40k/hr per property) and the 120 thresholded-requests/hour cap to the throttling design. *(§3.9 item 2.)*
10. **AI SDK version pin.** Whisperer-30 pins `ai@^7.0.48` (not v4 as one research agent claimed) — validate the wire-format decision against v7. *(§3.9 item 3.)*
11. **Gemini SDK.** Use `google-genai` (current) for FastAPI `/api/chat` + summary; map `thoughts_token_count` into the server usage ledger. *(§3.9 item 4.)*
12. **bun in CI.** `oven-sh/setup-bun@v2` covers GitHub Actions; Cloud Build can install bun via the official install script — the npm-vs-bun decision is unconstrained by CI. *(§3.9 item 5.)*
13. **AI SDK v7 + `toTextStreamResponse` verified.** v7 is the current docs line; the captured `chat.ts` streams with `streamText(...).toTextStreamResponse()` (plain text — matches F3's reader). *(§3.10 item 1.)*
14. **Start/Lovable → plain Vite strip list.** Remove `@lovable.dev/vite-tanstack-config`, `@tanstack/react-start`, `nitro`, `src/server.ts`, `src/start.ts`, `src/routes/api/*`; file routing is identical without Start. *(§3.10 item 2.)*
15. **Cloud Run is the GCP path.** `$PORT` 8080; request timeout default 300s/max 3600s (SSE); session affinity best-effort; HTTP/2 (`h2c`); proxy headers → explicit HTTPS OAuth redirect. *(§3.10 item 3.)*
16. **MSW streaming tests.** `HttpResponse` + `ReadableStream` body; SSE headers; jsdom has no `EventSource` — test the `getReader()` path. *(§3.10 item 4.)*
17. **Recharts 2.15.x lacks React 19 peer deps.** Use `overrides` or move to recharts 3.x at Phase 4 if install errors/warnings appear. *(§3.10 item 5.)*
18. **Python 3.14 floors.** Raise `pandas` floor to `>=2.3.3` (cp314 wheels); `pydantic>=2.12`; `python:3.14-slim` valid. *(§3.10 item 6.)*
19. **Gemini model hygiene.** `gemini-2.0-flash` is shut down — prune `AVAILABLE_MODELS`; 3.x line current; `total_thought_tokens` confirmed in usage payloads; Interactions API now GA. *(§3.10 item 7.)*

---

### 3.9 Round-2 research (live-verified 2026-08-05) — GA4 quotas & pagination, Gemini SDK, AI SDK version pin, bun in CI

Second research pass. Sources fetched live on 2026-08-05: Google Analytics Data API **quotas** page and **`properties.runReport`** reference; GitHub **`oven-sh/setup-bun`**; plus a repo-level cross-check against the captured whisperer-30 `package.json`. One research claim was corrected by the cross-check (item 3), and one reported number was corrected by the live page (item 1).

1. **GA4 pagination (live).** `RunReportRequest` pages with `limit` + `offset` (both int64). Default `limit` = **10,000 rows**; the API returns **at most 250,000 rows per request** no matter how many are requested (a docs-research agent said 100,000 — the live reference says 250,000); `limit` must be positive. `offset` = row count of the start row; first request uses 0, the second uses the first page's `limit`. *(developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport)*
2. **GA4 quotas (live).** Three categories — **Core** (`runReport`, `runPivotReport`, `batchRunReports`, `batchRunPivotReports`, `runAccessReport`, `getMetadata`, `checkCompatibility`, `createAudienceExports`), **Realtime** (`runRealtimeReport`), **Funnel** (`runFunnelReport`) — each request consumes exactly one. Standard-property numbers: **Core Concurrent Requests Per Property = 10** (Analytics 360: 50); Core tokens 200,000/day and 40,000/hour per property (14,000/hour per project-per-property); server errors 10/hour per project-per-property; **120 potentially-thresholded requests/hour** (`userAgeBracket`, `userGender`, `brandingInterest`, `audienceId`, `audienceName`). `returnPropertyQuota: true` → response includes `PropertyQuota` with consumed/remaining balances. Daily quotas reset midnight PST; hourly within an hour. *(developers.google.com/analytics/devguides/reporting/data/v1/quotas)*
3. **AI SDK version pin — cross-check correction.** A docs-research agent reported the `ai` package is at major "v4"; the **captured whisperer-30 `package.json` pins `"ai": "^7.0.48"`** (also `react ^19.2.0`, `vite ^8.1.5`, `@tanstack/react-router ^1.170.18`, `@tanstack/router-plugin ^1.168.23` — the TanStack pins consistent with the live-verified §3.6). The Phase 1 wire-format decision (§3.5) must be validated against the **v7** API surface.
4. **Gemini SDK + usage metadata (docs research).** Current Python SDK: **`google-genai`** (`google-generativeai` is legacy — ai.google.dev/gemini-api/docs/migrate). Streaming: `client.models.generate_content_stream(...)`. Usage metadata fields: `prompt_token_count`, `candidates_token_count`, **`thoughts_token_count`**, `total_token_count` — the Streamlit app's `total_thought_tokens` session key maps directly onto `thoughts_token_count` for the server-side usage ledger. Current models: `gemini-2.5-flash` / `gemini-2.5-pro`. Rate limits are tier-based (free vs paid).
5. **bun in CI (live).** GitHub Actions: **`oven-sh/setup-bun@v2`** is the canonical action — auto-detects the `packageManager` field in `package.json` (falls back to `engines.bun`, then latest), supports `bun-version-file`, private registries, and caching. Cloud Build: install bun in a build step via the official install script. **Conclusion: the npm-vs-bun decision is unconstrained by CI** — either pipeline can support either manager.
6. **Funnel shape (docs research).** `RunFunnelReportRequest` uses `funnelVisualizationType` (`STANDARD_FUNNEL` / `OPEN_FUNNEL`) and `funnelStepRange`; works on standard GA4 properties; consumes the **Funnel** quota category (live-confirmed on the quotas page). *(funnel-reports guide; quotas page above.)*
7. **Dimension/metric limits (reported — limits page 404 at fetch time).** Max **9 dimensions / 10 metrics** per standard report (≤7 dimensions for funnel reports), per the Data API limits guide. Consistent with the plan's "≤9 dimensions"; re-verify against the limits page at Phase 5 implementation.

---

### 3.10 Round-3 research (live-verified 2026-08-05) — AI SDK v7, Start→Vite strip list, Cloud Run, MSW streaming, Recharts×React 19, Python 3.14, Gemini models & thinking, FastAPI SPA/SSE/cookies

Third research pass, closing the six gaps from the round-2 review. Live sources fetched 2026-08-05: ai.google.dev (models + thinking pages), ai-sdk.dev (v7 docs), captured whisperer-30 files (`vite.config.ts`, `package.json`, `src/routes/api/chat.ts`), plus docs-research agents for TanStack/Cloud Run/MSW/Recharts/Python/FastAPI.

1. **AI SDK v7 confirmed (clears the §3.5 flag).** The current AI SDK docs live under **`/v7/`** (ai-sdk.dev) — **v7 is the current major**. The captured whisperer-30 `src/routes/api/chat.ts` uses `streamText` from `ai` + **`result.toTextStreamResponse()`** — plain `text/plain` output, exactly what F3's `getReader()`/`TextDecoder` reader consumes. `useChat` (v7) parses the structured data-stream / UI-message protocol, not plain SSE. *(§3.5 caveat stands; version and helper now verified.)*
2. **TanStack Start → plain Vite — precise strip list.** whisperer-30 is Start-based **through the Lovable plugin**: `vite.config.ts` uses `@lovable.dev/vite-tanstack-config` (v2.8.5) with `tanstackStart: { server: { entry: "server" } }`; `package.json` has `@tanstack/react-start ^1.168.32`, `nitro 3.0.260603-beta`, `@tanstack/react-query ^5.101.1`. **Remove:** the Lovable vite plugin (replace with `@vitejs/plugin-react` + `@tanstack/router-plugin/vite` + tailwind + path alias), `@tanstack/react-start`, `nitro`, `src/server.ts`, `src/start.ts`, and **`src/routes/api/*` (Start/Nitro server routes — `chat.ts`, `research.ts`)**. **Keep:** `@tanstack/react-router` + `@tanstack/router-plugin` (file-based `createFileRoute` works identically without Start), `ai`, `recharts`, `lucide-react`, `sonner`, tailwind, shadcn/ui. Start-only features (server functions, server loaders, request/cookie context) aren't used by the explorer components.
3. **Cloud Run is the natural GCP path (repo already deploys via `cloudbuild.yaml`).** Canonical shape: docker build → push to Artifact Registry → `gcloud run deploy` (docs.cloud.google.com/build/docs/deploying-builds/deploy-cloud-run). Cloud Run specifics that matter here: bind **`$PORT` (default 8080)**; **request timeout default 300s, max 3600s** — SSE chat streams that outlive 5 minutes need `--timeout` raised or a heartbeat; **session affinity is best-effort** (30-day routing cookie; breaks on scale-down/autoscale — chat/reconnect state must tolerate it); **HTTP/2 (`h2c`)** avoids HTTP/1.1 per-domain connection limits for streaming; **proxy headers** (`X-Forwarded-Proto`) mean the OAuth redirect URL must be the explicit public HTTPS URL (or trust proxy headers); `--min-instances` avoids cold starts on OAuth flows. Cloud Run does **no** SPA rewrite — the FastAPI catch-all (item 8) must serve `index.html`.
4. **MSW streaming/SSE testing.** MSW v2 `HttpResponse` accepts a `ReadableStream` body — the documented way to mock streaming (mswjs.io/docs/api/http-response). For `text/event-stream` mocks set `Content-Type: text/event-stream` + `Cache-Control: no-cache`. Caveats: Node/undici may buffer unless the client consumes incrementally via `getReader()`; **jsdom ships no real `EventSource`** — chat-stream tests must drive the store's fetch+`getReader()` path (which F3's store uses), not `EventSource`.
5. **Recharts ^2.15.4 × React 19.2.** Recharts 2.15.x peerDependencies are `^16.8 || ^17 || ^18` — React 19 not declared; a 19.2 install may need `overrides`, and 2.x may emit legacy-pattern warnings. **Recharts 3.x is the React-19-first line.** Plan: plain install first at Phase 4; on peer-dep errors/warnings use `overrides` or move to 3.x.
6. **Python 3.14 stack (verified).** `python:3.14-slim` exists (Docker Hub) — the dockerfile-pattern base is valid. **pandas needs ≥2.3.3 for cp314 wheels** — the repo's `pandas>=2.0.0` floor must be raised to `>=2.3.3` for reproducible 3.14 builds (the venv already resolves newer pandas, which is why tests pass today). `openpyxl` is pure-Python (fine); `google-analytics-data` 0.23.0 declares Python 3.14 (repo floor `>=0.18.0` is loose but resolvable); `google-genai` supports 3.14; `fastapi`/`uvicorn`/`pydantic` (≥2.12) all support 3.14 — **pydantic v1 does not**.
7. **Gemini models & thinking (live).** The **Gemini 3.x line is now current** (3.6-flash stable, 3.5-flash, 3.1-pro preview, 3-flash preview); **2.5-flash / 2.5-pro / 2.5-flash-lite remain stable**; **2.0-flash is shut down** — and the repo's `utils/gemini_client.py` `AVAILABLE_MODELS` still lists `gemini-2.0-flash` and `gemini-1.5-flash` (prune when building `/api/chat`). Repo default: `gemini-2.5-flash`, 1M-token context per `MODEL_CONTEXT_LIMITS`. Thinking: 2.5/3 models think by default; `thinking_level` (minimal/low/medium/high) controls effort; usage reports **`total_thought_tokens`** (confirmed in a live SSE usage payload: `total_tokens`, `total_input_tokens`, `total_output_tokens`, `total_thought_tokens`) — the exact counters the Streamlit app already tracks. The **Interactions API is now GA** (recommended: `client.interactions.create`, with `thinking_summaries`); the existing `generateContent` path still works. *(ai.google.dev/gemini-api/docs/models + /thinking)*
8. **FastAPI SPA fallback + SSE + `__Host-` (verified).** Pattern confirmed: `app.mount("/assets", StaticFiles(...))` + catch-all `@app.get("/{full_path:path}")` returning `FileResponse(index.html)` (fastapi.tiangolo.com/tutorial/static-files) — matches the dockerfile-pattern sketch. `StreamingResponse` cancels the async generator on client disconnect (`asyncio.CancelledError` — use `try/finally`); add SSE heartbeats for long idle streams (starlette.io/responses). `__Host-` cookie: requires `Secure`, `Path=/`, and **no `Domain`** attribute — FastAPI `Response.set_cookie` supports it directly (`secure=True`, `path="/"`, omit `domain`). *(developer.mozilla.org Set-Cookie)*

---

### 3.11 Hosting evaluation — can this stack live on Vercel? (evaluated 2026-08-05)

Product-owner question: *"could we host this on Vercel like my website?"* Answer: **the SPA, yes — the FastAPI backend, no.** Vercel is a strong fit for the React app alone, but the API cannot run on Vercel serverless functions given this workload's requirements.

**What Vercel handles well:** the React SPA (static Vite output, CDN, preview deployments) — the user already hosts a site there.

**Why the FastAPI backend fails on Vercel functions:**
1. **Request-body limits.** Vercel serverless functions cap request/response bodies at roughly **4.5 MB** on the Hobby tier — the ingestion policy is **100 MB** (see §4.11, size-policy decision). Even a 25 MB CSV upload cannot reach a Vercel function. Hard blocker, not a tuning issue.
2. **Function duration limits** (Hobby ~10–15 s, Pro 60 s; higher only on Enterprise). Long-lived SSE chat streams would be cut off, and streaming from Python functions on Vercel is unreliable.
3. **Serverless statelessness.** The server-owned session model (F4 in-memory store) breaks on stateless functions — every request may hit a different instance; would require Vercel KV/Postgres plus a session-store rewrite.
4. **No long-lived connections** (SSE) or WebSockets on serverless functions.

**The single-origin catch:** serving the SPA on Vercel and the API on a container host would split origins — breaking the same-origin cookie/OAuth/SSE model (plan Phase 6). Same-domain rewrites (SPA + `api/*` in one Vercel project) still route `api/*` to functions and inherit every blocker above.

**Recommendation (recorded):** keep the container path — **Cloud Run** (the repo already deploys via `cloudbuild.yaml`; §3.10 item 3), with Railway/Render as equivalents. Vercel remains a *frontend-only* option only if the architecture changes (not recommended). *Sources: vercel.com/docs (limits); gravity-index hosting comparison (2026-08-05).*

---

## Part 4 — Cross-check & reconciliation ledger (added 2026-08-05)

> Method: repo-level claims were verified against the actual codebase on 2026-08-05 (file listing, `grep` for Streamlit imports, `wc -l`, `pytest --collect-only`); API-contract claims were cross-referenced across `insights-explorer-migration-plan.md` (the plan), `freebuff-prompt-wire-react-store.md` (F3), and `phase-1-api-react-callback-tests-implementation.md` (F4). **Rule applied: original content is preserved everywhere; corrections are recorded here and in per-doc addenda, never by rewriting the source text.**

### 4.1 Repo-fact claims — verified against the codebase

| Claim | Where stated | Verified (2026-08-05) | Verdict |
|---|---|---|---|
| "16 utils modules" | plan · pastes | 16 files incl. `__init__.py`; 15 module files | ✅ Confirmed (prefer "15 modules + `__init__.py`" going forward) |
| "7 of 16 utils import Streamlit" | plan · P3 · §1.3 | exactly 7: `data_loader`, `error_boundary`, `forecasting`, `gemini_client`, `prompt_templates`, `session`, `styles` | ✅ Confirmed exactly |
| "10 Streamlit UI components" | plan · P5 | 8 Python component modules (`chat`, `data_preview`, `drive_picker_component`, `hero`, `learning_challenge`, `onboarding_tour`, `sidebar`, `summary`) + `__init__.py` + `drive_picker_component_frontend/` TS app | ⚠️ **Corrected → 8** (the other two entries are `__init__.py` and the TS picker app) |
| "~8,461 LOC" | plan · archive | `wc -l utils components pages app` = 8,461 | ✅ Confirmed exactly |
| "742 unit tests + 32 Playwright smoke" | plan · archive · F3 · F4 | `pytest --collect-only` = 742 unit (excl. smoke/e2e) + 32 smoke | ✅ Confirmed exactly |
| "`plans/ga4-measurement-contract.md` exists" | P9 · §1.10 | present | ✅ Confirmed |
| "Drive Picker is a standalone TS app (npm)" | P9 | `components/drive_picker_component_frontend/` with own `package.json` / `package-lock.json` | ✅ Confirmed |
| "dual CI: GitHub Actions + Cloud Build" | P9 | `.github/workflows/test.yml` + `cloudbuild.yaml` | ✅ Confirmed |

### 4.2 Cross-doc API contract reconciliation

| Topic | Plan | F3 (store prompt) | F4 (impl packet) | Reconciled (2026-08-05) |
|---|---|---|---|---|
| Health endpoint | `GET /health` (GitHub issue #1 draft · plan Phase 1) | — | `GET /healthz` | ✅ **Adopt `/healthz`** (F4). Use it in any created issues + the new smoke script. |
| `ga4/connect` response field | `{ authUrl: string }` | reads `{ authUrl }` | `{ authorization_url: string }` (snake_case) | ✅ **Adopt `authorization_url`** at the API boundary; add a Pydantic alias only if the store insists on camelCase. |
| Upload response shape | bare `DataContext` | bare `res.json()` → `setSource` | `UploadResponse { dataset: DatasetContext }` | ✅ **Adopt the `{ dataset }` wrapper** (F4 is the implementation). F3 must read `.dataset`. |
| Preview response shape | `{ rows, columns }` | bare (fallback branch) | `{ dataset, rows }` | ✅ **Adopt `{ dataset, rows }`**; F3's fallback branch must read `.dataset`. |
| `GET /api/data/context` | not in plan table | — | added (returns `DatasetContext`) | ➕ **Addition** beyond the plan — keep; useful for session restore. |
| Summary endpoint | `GET /api/analysis/summary` | uses `POST /api/chat` with `mode: "summary"` | deferred (Phase 3+) | ⚠️ Recommend **chat-mode streaming as canonical** (matches F3/F4 direction); keep the GET endpoint only as an optional non-streaming fallback. |
| API types casing | camelCase TS | camelCase (`rowCount`, `dateRange`) | snake_case (`row_count`, `date_range`) | ✅ **Adopt F4's rule**: snake_case at the API boundary, camelCase in store state, normalized once in `setSourceFromApi`. F3's `api-types.ts` represents the store-facing (post-normalization) shape. |
| Session cookies | not addressed | fetch snippets omit `credentials` | requires `credentials: "include"` on every fetch | ⚠️ **F3's snippets need `credentials: "include"`** or the session cookie is never sent. |
| `Column.type` union | — | `"date" \| "number" \| "string"` | `+ "boolean" \| "unknown"` | ✅ **Adopt F4's superset** (matches `infer_column_type`). |
| OAuth callback target | FastAPI callback (plan table) | `?code=` read in React (superseded) | Google → FastAPI → React with `status`/`reason` only | ✅ F4 correct; **F3 §4 is superseded** (see §1.11). |
| `ExplorerValue` additions | — | interface lacks `setSourceFromApi` | requires `setSourceFromApi` | ⚠️ F3's interface update must add `setSourceFromApi` (non-UI setter, single normalization boundary). |
| Test counts | 742 + 32 | 742 | 742 | ✅ consistent and verified (§4.1). |

### 4.3 Research-backed confirmations (Part 3 summary)

- Aggregate-only GA4 report API → roadmap "hard blocker" holds; `runFunnelReport` nuance recorded (§3.4).
- GLM-5.2: 1M context, MIT weights, pricing $1.40/$4.40 per M — comparison doc claims verified (§3.7).
- Hosting, Picker requirements, SSE wire format, MSW/TanStack — see §3.1–3.6.

### 4.4 Deliberate non-changes and open items

- **Verbatim records are untouched** — Part 2 pastes and the two verbatim file copies are source-fidelity artifacts; corrections live in Part 4 and the per-doc addenda.
- **GitHub issues were never created** — when they are, apply the reconciled values (`/healthz`, `authorization_url`, `{ dataset }` wrapper, `credentials: "include"`, `setSourceFromApi`).
- **ROADMAP funnel rows** (`plans/ROADMAP.md`) are outside `migration/` scope — revisit at implementation time given the `runFunnelReport` nuance (§3.4).
- **MSW / TanStack Router facts** are now **live-verified** (2026-08-05) — see §3.6; the one correction surfaced was the `onUnhandledRequest` default (`"warn"`, not `"bypass"`).
- **Component-count correction** (10 → 8) affects the plan's repo-profile prose only; no implementation impact.

### 4.5 Change log for this pass

| File | Change (all additive) |
|---|---|
| `insights-explorer-migration-ingest.md` | Part 4 ledger appended; front-matter note updated |
| `insights-explorer-migration-plan.md` | Reconciliation Addendum appended (see its tail) |
| `freebuff-prompt-wire-react-store.md` | Reconciliation Addendum appended (execution-time corrections for the prompt) |
| `phase-1-api-react-callback-tests-implementation.md` | Reconciliation Addendum appended (canonical choices confirmed) |
| `glm-5-2-vs-perplexity-migration-comparison.md` | Verification Addendum appended (GLM-5.2 facts checked) |

---

### 4.6 Batch 3 claim verification (added 2026-08-05)

Verification of [PASTE 11]'s claims against both repos and this codebase (see §1.13 for the synthesis; verbatim text in §2.15).

| Claim | Status | Detail |
|---|---|---|
| Tracked `.env` in whisperer-30 (not just `.env.example`) | ✅ **Confirmed** | Root listing includes `.env` (62 B); git history shows commit `9059739` ("Changes") touching it; `.env.example` returns HTTP 404; `.gitignore` has no `.env` rule (only `*.local`, `.dev.vars`, etc.). **Contents not decoded during ingest.** Action required before repo copy-in: inspect git history for the full set of secrets, rotate/revoke any real credentials (Lovable, Google, Gemini, …), `git rm --cached .env`, add a safe `.env.example`. |
| `st.session_state` spread (app.py, utils/session.py, data loading, Gemini, GA4, multiple UI components) | ✅ Confirmed | 15 source files: app.py; `utils/data_loader.py`, `session.py`, `ga4_client.py`, `data_context.py`, `gemini_client.py`; `components/{learning_challenge,sidebar,onboarding_tour,data_preview,__init__,summary,chat,hero}.py`; `pages/learn.py`. `utils/session.py` = `clear_data()` owner only. ~50 distinct keys observed (sample list in §1.13). Recommendation stands: written key inventory (key → owner → lifecycle → replacement) before any code changes. |
| npm vs bun split | ✅ Confirmed | whisperer: `bun.lock`; Drive Picker: npm `package-lock.json`. |
| GA4 measurement contract = source of truth | ✅ Confirmed & already canonical | See §4.2. |
| Lovable gateway not a permanent path | ✅ Confirmed | §1.3–1.4 evidence; no correction needed. |
| Both CI pipelines need updates | ✅ Confirmed | `.github/workflows/test.yml` + `cloudbuild.yaml` present. |
| "Current test count won't transfer one-to-one" | ✅ Agreed (judgment, not a repo fact) | Matches §4.4's test-retirement note; batch 3 supplies the four-layer replacement matrix (§1.13 item 4). |
| New process/design inputs (branch + freeze, server session, /api/v1, typed client, deployment prerequisites, living reference) | 🆕 New — no prior doc contradicted | Recorded in §1.13; adopted into the per-doc Batch 3 addenda (plan / F3 / F4). No existing claim needed correction. |

**Non-changes:** verbatim pastes untouched (Part 2); `glm-5-2-vs-perplexity-migration-comparison.md` is unaffected by batch 3 (nothing GLM- or Perplexity-specific in the paste) — no addendum appended there.

**Change log for this pass (all additive):**

| File | Change |
|---|---|
| `insights-explorer-migration-ingest.md` | §1.13 synthesis + §2.15 verbatim PASTE 11 + §4.6 ledger + URL5 register entry + front-matter/provenance/index updates |
| `insights-explorer-migration-plan.md` | Batch 3 Review Addendum appended |
| `freebuff-prompt-wire-react-store.md` | Batch 3 Addendum appended (session model, typed client, /api/v1) |
| `phase-1-api-react-callback-tests-implementation.md` | Batch 3 Addendum appended (server session + storage abstraction, /api/v1, test matrix, pre-copy security gate) |
| `glm-5-2-vs-perplexity-migration-comparison.md` | Not affected (no batch-3 claims about GLM/Perplexity) |
---

### 4.7 Change log — research fold-in, §3.6 live verification & follow-up batch (added 2026-08-05)

Records the three passes after the §4.6 ledger: the research fold-in, the §3.6 live verification, and the follow-up deliverables batch. All additive.

**Pass 1 — Research fold-in (plan doc):** the 7 research corrections from Part 3 §3.8 were folded into the plan's 6 phases as inline **Research amendments (2026-08-05)** notes (additive, original phase text preserved). Mapping and citations recorded in the plan's `## Research Fold-In Log (2026-08-05)`. One inline supersession flag added (Phase 5's `localStorage` step vs the Batch 3 server-owned session model).

**Pass 2 — §3.6 live verification:** the two `[tool-knowledge]` flags in §3.6 were replaced with source-backed detail fetched directly from npm registry / mswjs.io / tanstack.com (both doc-research agents hit a docs outage; `read_url` worked). Established: `msw@2.15.0`, `@tanstack/react-router@1.170.20`, `@tanstack/router-plugin@1.168.25`; `onUnhandledRequest` **default is `"warn"` (not `"bypass"`)** — a correction to the earlier research claim; `validateSearch`/`useSearch`/`getRouteApi` and the `VALIDATE_SEARCH`/`errorComponent` mechanism confirmed. §4.4 flag cleared.

**Pass 3 — Follow-up deliverables (this batch):**

| File | Change |
|---|---|
| `migration/session-state-inventory.md` | **New** — 44-key `st.session_state` inventory (key → owner → lifecycle → replacement), per Batch 3 recommendation |
| `migration/dockerfile-pattern.md` | **New** — multi-stage single-origin Dockerfile sketch (Phase 6 deliverable, correction 5) |
| `freebuff-prompt-wire-react-store.md` | Research Fold-In Cross-Check Addendum appended (picker `{token, appId}`, wire-format confirm, typed-search callback, funnel scope, single-origin) |
| `phase-1-api-react-callback-tests-implementation.md` | Research Fold-In Cross-Check Addendum appended (**PKCE added to §8 sketch**, **`validateSearch`/`errorComponent` for §11 callback**, MSW `onUnhandledRequest: "error"` live-confirmed) |
| `insights-explorer-migration-plan.md` | Phase 5 amendment extended with the `VALIDATE_SEARCH`/`errorComponent` pattern (live-verified) |
| `whisperer-30-reference/WHISPERER-30-REFERENCE.md` | Drift cross-check section added — captured `explorer-store.tsx` vs F3's 13 steps |
| `migration/README.md` | Document table + addenda table updated (7 docs) |

**Non-changes:** all verbatim pastes (Part 2) untouched; `glm-5-2-vs-perplexity-migration-comparison.md` unaffected; no captured reference file edited.

### 4.8 Change log — pre-implementation pack & docs commit (added 2026-08-05)

| File | Change |
|---|---|
| `migration/env-rotation-checklist.md` | **New** — `.env` rotation checklist (Phase 0 security gate; inspect → identify → rotate/revoke → remediate → prevent) |
| `migration/branch-and-freeze-policy.md` | **New** — `feat/react-fastapi-migration` branch + feature-freeze policy (Batch 3 process decision 1, written down; branch not created — commits land on `main`) |
| `migration/README.md` | Nine-doc table + addenda row + action-item pointers to the two new docs |
| `DOCUMENTATION_INDEX.md` | Migration section + status table gain the four support docs (incl. the two from §4.7's batch that were missing from the index) |
| repo (git) | **First commit of the migration package** — `migration/`, `README.md`, `DOCUMENTATION_INDEX.md` land on `main` (docs only) |

**Non-changes:** no application code; the branch `feat/react-fastapi-migration` is **documented, not created** — per this pass, the docs package commits to `main` and the branch is cut when Phase 1 work starts (`branch-and-freeze-policy.md` §4).

### 4.9 Change log — round-2 research pass (added 2026-08-05)

| File | Change |
|---|---|
| this archive | §3.9 round-2 research (live-verified) added; §3.8 delta list extended with items 8–12 |
| `insights-explorer-migration-plan.md` | Research amendments extended: Phase 1 (`ai@^7.0.48` pin), Phase 3 (Gemini `google-genai` SDK + thought tokens), Phase 4 (bun-in-CI + captured stack pins), Phase 5 (GA4 live quota/pagination numbers, item 7) |
| `freebuff-prompt-wire-react-store.md` | Round 2 Research Addendum appended (`ai@^7` + `useChat` protocol, Gemini thought tokens, stack pins) |
| `phase-1-api-react-callback-tests-implementation.md` | Round 2 Research Addendum appended (GA4 client names, GA4 numbers for the Phase-5-forward pull, Gemini SDK, AI SDK pin) |
| `dockerfile-pattern.md` | CI note added: `oven-sh/setup-bun@v2` for GitHub Actions |
| `README.md` | Addenda table row for the round-2 pass |

**Corrections this pass (both recorded in §3.9):** AI SDK version — research agent said "v4", actual pin is `ai@^7.0.48`; GA4 max rows/request — research agent said 100,000, live reference says 250,000.

### 4.10 Change log — round-3 research pass (added 2026-08-05)

| File | Change |
|---|---|
| this archive | §3.10 round-3 research (live-verified) added; §3.5 `[tool-knowledge]` flag cleared with a verification note; §3.8 delta list extended with items 13–19 |
| `insights-explorer-migration-plan.md` | Amendments extended: Phase 1 (AI SDK v7 verified), Phase 3 (Gemini model hygiene — 2.0-flash shut down; thought-token counters confirmed), Phase 4 (Start/Lovable strip list, Recharts×React 19), Phase 6 (Cloud Run as the GCP path) |
| `freebuff-prompt-wire-react-store.md` | Round 3 Research Addendum appended (`toTextStreamResponse` confirmed in captured chat.ts; Nitro server routes removed; MSW chat-stream tests) |
| `phase-1-api-react-callback-tests-implementation.md` | Round 3 Research Addendum appended (MSW streaming pattern + jsdom `EventSource` caveat, Python 3.14 floors, GA4 client naming, `__Host-` cookie verification) |
| `dockerfile-pattern.md` | GCP row replaced with the Cloud Run path; Python-3.14 dependency floors note added |
| `README.md` | Addenda table row for the round-3 pass |

**Corrections/new facts this pass:** `gemini-2.0-flash` is shut down (repo model list still offers it); pandas floor must be ≥2.3.3 on Python 3.14; recharts 2.15.x lacks React 19 peer deps; AI SDK v7 is the current docs line and the captured chat route uses `toTextStreamResponse()`.

### 4.11 Change log — internal reconciliation batch (added 2026-08-05)

Closes the three internal gaps identified after round-3 research, plus the Vercel hosting evaluation. No external research was required for the first three — all verified against the repo.

| Item | Resolution | Where recorded |
|---|---|---|
| 1. **Size-policy mismatch** — Drive guards at 100 MB (`utils/drive_client.py:48`, `MAX_DRIVE_IMPORT_BYTES`); F4's upload defaults to 25 MB; the Streamlit upload path has **no** explicit guard | Single ingestion policy: **`MAX_INGEST_BYTES = 100 MB`** for both upload and Drive in the API (env-overridable). Note platform body caps: Vercel functions ≈4.5 MB (blocked — §3.11); Cloud Run configurable to ~128 MB; Drive downloads are server-side so unaffected by browser/request-body caps | F4 Reconciliation Addendum 2 · plan Phase 1 amendment · this ledger |
| 2. **F4 schemas vs `plans/ga4-measurement-contract.md`** — declared canonical but never field-checked | Field-level check: **no conflict** — the contract defines *computed metrics* (5 rows: numerator/denominator/grain/event mapping/validation status); F4's `DatasetContext` is a *transport* descriptor. Documented the mapping: contract rows → `/api/ga4/pull` `DatasetContext.metrics` entries with `provenance` carrying `contract_row` + `validation_status`; future `ReportContract` objects per the contract's Next-steps item 4. Rows 3–5 stay `unavailable` — consistent with aggregate-only GA4 access + the funnel nuance (§3.4) | F4 Reconciliation Addendum 2 · this ledger |
| 3. **No 742-test layer inventory** | New doc `migration/test-layer-inventory.md`: **742 = 452 utils-facing (61%, keep as-is) + 290 components-facing (39%, rewrite/retire)**; plus 32 Playwright smoke + 8 E2E stay | new doc · README · this ledger |
| 4. **Vercel hosting question** | Evaluated: SPA yes, FastAPI no (≈4.5 MB body cap vs 100 MB policy; function duration vs SSE; stateless sessions). Container path (Cloud Run) stays the recommendation | archive §3.11 · plan Phase 6 · dockerfile-pattern §4 |

**Non-changes:** no code touched. `requirements/base.txt` floors remain a Phase-1 implementation item (raise `pandas>=2.3.3` per §3.10 item 6; introduce the shared `MAX_INGEST_BYTES` constant per item 1).

### 4.12 Master-plan revision (2026-08-05)

Peer review of the migration package ("tighten before Phase 1") produced this revision pass — folded into `master-plan.md`, F3/F4/plan (canonical API decisions), and a new policy doc. **Nothing executed.**

| Change | Where | What |
|---|---|---|
| Session/dataset store moved forward | master-plan §4–5, §13; F4 supersession | `SessionStore`/`DatasetStore` interfaces in Phase 1 (in-memory for dev); shared staging store (Redis/Valkey or Postgres) proven **before Phase 5** — Cloud Run session affinity is best-effort, not a consistency guarantee |
| Browser-upload architecture decision | master-plan §4–5, §13; F4 supersession | Cloud Run HTTP/1 caps requests at **32 MiB**; options (32 MB browser cap — recommended / tested end-to-end HTTP/2 / signed Cloud Storage); two-tier policy `MAX_BROWSER_UPLOAD_BYTES = 32 MB` + `MAX_INGEST_BYTES = 100 MB` |
| Canonical API decisions record | F3, F4, plan (new top sections) | `/api/v1` · `/healthz` · `{ dataset }` · HttpOnly cookie + `credentials: "include"` · snake_case boundary · `api.ts` camelCase · chat transport · upload policy; old `/api` and 25 MB references marked superseded |
| Blocking-work guidance | master-plan §5, §15 | CPU-heavy routes synchronous or in a controlled thread pool; hard caps on rows/columns/**decompressed** size; reject password-protected sheets, MIME mismatches, compression bombs; streamed/temp-store exports; job model later if needed |
| Data retention + AI data boundary | new `data-retention-policy.md`; master-plan cross-cutting F | Policy before the API exists: retention window, raw-frame persistence, session expiry, Clear Data semantics, export-logging retention, Gemini prompt allowlist, identifier removal/aggregation |
| OAuth production-real | master-plan §5 | Persist `state`/PKCE verifier/creation time/return path with short expiry + one-time use; per-env redirect URIs from an allowed-host config |
| Chat reconnect | master-plan §4/§8, §14 | Client retains message, partial output safe, retry without duplicate assistant messages; Cloud Run timeout is a ceiling, not a guarantee |
| Three release gates | master-plan §14 | No-regression · Contract · User-flow |
| Doc lifecycle + wording | README | Active vs reference vs archive classification; "nothing committed to git" corrected to "no migration product code written" |

*— End of compiled archive —*
