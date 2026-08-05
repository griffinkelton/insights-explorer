# migration/ — React/FastAPI Migration Docs

Index for the migration decision material: moving the `insights-explorer` product from a Streamlit UI to a **React frontend (`insights-whisperer-30` components) + FastAPI backend** built on the existing Python `utils/` layer.

> **Status (2026-08-05):** all nine documents ingested and cross-checked; research live-verified (incl. MSW/TanStack against live docs); corrections folded into the plan; final-pass QA complete (links verified, indexed in [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)). Still **planning-only — no code written**, nothing committed to git.

---

## The one-line decision

`insights-explorer` (Python) stays the **system of record**. `insights-whisperer-30` is a mock-data "UI shell" whose React components get adopted wholesale as the new frontend. A thin FastAPI layer exposes the existing `utils/` logic (GA4, Drive, Gemini, DataContext, forecasting, funnels, exports — 742 tests, 8,461 LOC) as HTTP endpoints. Streamlit retires incrementally after feature parity.

---

## The nine documents

| File | What it is | Contents | Status |
|---|---|---|---|
| **`insights-explorer-migration-ingest.md`** | **The compiled archive** — the master record of everything provided and verified. Start here. | **Part 1** synthesis (decision, evidence chain, artifact map, batch 1–3 deltas) · **Part 2** verbatim source archive (11 pasted reviews + 4 file copies, URLs collapsed to `[URL1]`–`[URL5]`) · **Part 3** external research (hosting, OAuth/PKCE, Drive Picker, GA4 Data API, SSE/AI SDK, MSW/TanStack — live-verified 2026-08-05) · **Part 4** cross-check & reconciliation ledger (verified claims, contract reconciliation, batch-3 verification) | 🔵 Ingested |
| **`insights-explorer-migration-plan.md`** | **The 6-phase plan** — the actionable roadmap. | Executive summary, repo comparison, risk table, **Phases 1–6** (FastAPI skeleton → utils decoupling → wire real utils → port React UI → GA4 OAuth + Drive Picker → cutover/retire Streamlit), API contract draft, success metrics, open questions, next actions + 3 addenda + **Research Fold-In Log** | 🔵 Plan (no code) |
| **`freebuff-prompt-wire-react-store.md`** | **F3 — the frontend wiring prompt** (for an AI coding agent). | 13-step change list for `explorer-store.tsx`: remove mocks, real `fetch()` calls, GA4/Drive integration, SSE chat, typed client, `.env` files | 🟡 Reference |
| **`phase-1-api-react-callback-tests-implementation.md`** | **F4 — the Phase 1 implementation packet** (backend + OAuth callback + test strategy). | FastAPI vertical slice (config, session, schemas, upload/preview routes), GA4 OAuth start/callback adapters, React GA4 callback route, MSW-based test migration | 🟡 Reference |
| **`glm-5-2-vs-perplexity-migration-comparison.md`** | **GLM-5.2 vs Perplexity plan comparison** — how a second model would approach the same migration. | Approach differences, strengths, combined recommendation | ✅ Verified facts |
| **`session-state-inventory.md`** | **The `st.session_state` key inventory** — the written record Batch 3 recommended before any code changes. | All 44 keys: key → owner → lifecycle → FastAPI/React replacement, grouped by dataset / GA4 / Drive / chat / theme / test-only | 🔵 Ingested |
| **`dockerfile-pattern.md`** | **Phase 6 single-origin Docker pattern** — concrete deliverable sketch for the hosting amendment. | Multi-stage Dockerfile (Vite build → FastAPI runtime serving the SPA), SPA fallback route, platform notes, verification checklist | 🟡 Reference |
| **`env-rotation-checklist.md`** | **The `.env` rotation checklist** — Phase 0 security gate before any whisperer-30 code copy-in. | Verified `.env` facts, inspect → identify → rotate/revoke → remediate → prevent, verification checklist | 🔵 Planning |
| **`branch-and-freeze-policy.md`** | **Migration branch + feature-freeze policy** — Batch 3 process decision, written down. | Branch model (`main` vs `feat/react-fastapi-migration`), freeze rules, fix-forward rule, lift criteria, branch creation command | 🔵 Planning |

## Reference capture: whisperer-30 (`whisperer-30-reference/`)

Frozen, dated snapshot of the source UI repo (`griffinkelton/insights-whisperer-30` @ `a71c3712`, captured 2026-08-05): the Lovable design prompt, the UI-shell plan, the explorer-store contract (F3's target), the chat endpoint + BrainGuide system prompt (**reference-only — never production logic**), research types/sources, mock data shapes (→ MSW fixtures), and the stack/config manifest. See [whisperer-30-reference/WHISPERER-30-REFERENCE.md](whisperer-30-reference/WHISPERER-30-REFERENCE.md) for what was captured, why, and what was deliberately excluded (notably the tracked `.env`).

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
```

- **The archive is the source of truth.** Everything else derives from it; when docs disagree, the archive's **Part 4 ledger** records which choice is canonical.
- **The plan is the executable view.** It consumes the archive's research (Part 3) and reconciliation (Part 4) and folds them into its phase sections.
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

## Suggested reading paths

- **New to the project (30 min):** README → plan §"Decision" + "Comprehensive Plan" → archive Part 1 (§1.1–1.2) → skim F4.
- **About to implement Phase 1:** plan Phase 1 (with amendments) → F4 in full → F3 §3 (API base) → archive Part 4 §4.2 (canonical contract choices).
- **About to do OAuth/Drive (Phase 5):** plan Phase 5 amendments → archive Part 3 §3.2–3.4 → F4 OAuth section + Batch 3 addendum.
- **Reviewing the decision itself:** archive Part 1 (§1.1–1.8) + Part 2 verbatim pastes + comparison doc.

---

## Action items before implementation starts

1. **Security:** the whisperer-30 repo tracks a real `.env` (62 B, commit `9059739`, no `.env.example`, no gitignore rule) — inspect history, **rotate/revoke** any credentials, remove from index, add `.env.example` before copying the repo in. Run `migration/env-rotation-checklist.md`.
2. **Process:** create `feat/react-fastapi-migration`; freeze broad Streamlit feature work. Policy: `migration/branch-and-freeze-policy.md`.
3. **Contracts:** adopt the Part 4 §4.2 canonical choices (`/healthz`, `authorization_url`, `{ dataset }` wrapper, `credentials: "include"`, `setSourceFromApi`, `/api/v1`).
4. **Fold-in complete:** the 7 research corrections are already in the plan's phase sections (see Research Fold-In Log).

*All nine files were moved here 2026-08-05 from the repo root and are indexed in [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) (section: React/FastAPI Migration).*
