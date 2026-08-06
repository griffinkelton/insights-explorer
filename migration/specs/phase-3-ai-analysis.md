# Phase 3 — Wire FastAPI to Real `utils/` + AI Analysis (outline — stub)

> ⚪ **STUB** — Phase 3 gate closed. **Research gate must run before this stub is expanded** (see below). No code is written from this file yet.

## Purpose

Add the analysis + AI endpoints that call the decoupled `utils/` services: chat/SSE (Gemini), summaries, forecasting, funnels, and the deterministic-context pattern (domain code assembles contract/evidence/insight context; Gemini explains and prioritizes — it never calculates). Chat wire format is a **locked-but-open decision** recorded at contract time (master-plan open decision #1).

## Inputs / source documents

- master-plan §7 (Phase 3), §11-B/F, §13 (open decisions #1, #7), §14 (release gate 3 — chat reconnect)
- `utils/gemini_client.py`, `utils/forecasting.py`, `utils/funnels.py`, `utils/prompt_templates.py`, `utils/commands.py`, `utils/data_context.py`
- `plans/ga4-measurement-contract.md` — metric-status policy (provisional caveats; unavailable never numeric evidence)
- `../policies/data-retention-policy.md` §7 — Gemini prompt allowlist, identifier removal/aggregation
- archive §3.5 (SSE wire format), §3.9–3.10 (google-genai, ai@^7.0.48, streaming tests)
- **F3's chat content is NOT absorbed here** — F3 is the frontend store wiring; it parks in `phase-4-react-port.md`. This phase owns the backend chat/summary endpoints.

## Tracks consumed

- **B** (API/contract): `/api/v1` chat + analysis schemas; metric-status policy enforced at the model boundary (provisional caveated, unavailable never numeric evidence).
- **C** (tests): chat/analysis contract tests; SSE test asserts partial chunks stream.
- **F** (retention/AI boundary): Gemini prompt allowlist per `../policies/data-retention-policy.md` §7.
- **G** (research discipline): Gemini readiness prompt (archive §3.12, prompt 3) runs before this stub expands.

## Research gate — REQUIRED before expansion (dispatch to the research agent)

Run the **Gemini production readiness** prompt from archive §3.12 (prompt 3), immediately before expanding: currently supported text models for analytics explanation, model deprecations/replacements, pricing/free-tier + quotas, `google-genai` streaming + cancellation/disconnect behavior, request/context limits for DataContext + prompt templates, data-handling/privacy controls. Return: exact model IDs, a fallback strategy, env-var requirements, rate-limit/retry guidance, official citations. *External research never overrides canonical internal contract decisions without a reconciliation step (archive §3.12).*

Also dispatch the **GA4 feasibility** prompt (archive §3.12, prompt 1) only if GA4 pulls enter this phase — the plan schedules GA4 for Phase 5; keep the two prompts separate.

## Task outline (expand before execution)

- [ ] Chat wire format decision recorded in OpenAPI (plain SSE `text/event-stream` default — matches `ai@^7.0.48` + `toTextStreamResponse()` + the captured F3 reader; AI SDK data-stream only if `useChat` is chosen).
- [ ] `POST /api/v1/chat` — `{ messages, mode }` payload; server resolves session + dataset (no client-authoritative references); SSE streaming; reconnect-safe (message retained, partial output safe, retry without duplicate assistant messages — release gate 3).
- [ ] `POST /api/v1/analysis/summary` (+ forecast/funnel per the parity checklist) via the decoupled utils.
- [ ] Deterministic-context assembly (`utils/prompt_templates.py` canonical — never the whisperer-30 hardcoded BrainGuide prompt); metric-status policy enforced at the boundary.
- [ ] Server-side usage ledger (per-session token/request counts; `thoughts_token_count` mapped) — feeds the §17 AI cost guardrails later.
- [ ] Chat/analysis contract tests (MSW streaming pattern for the frontend side lives in Phase 4).

## Exit criteria

- [ ] `pytest tests/api/` covers chat + analysis; SSE contract test with streaming asserts partial chunks.
- [ ] Baseline utils tests green; Gemini calls use the researched model IDs + fallback.
- [ ] Prompt allowlist enforced per `../policies/data-retention-policy.md` §7 (no raw rows / identifiers in Phase 1 posture).

## Gate table — Phase 3 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 3 — AI analysis wired | Chat/SSE + summary contract tests green · usage ledger recorded · reconnect behavior verified | Implementation agent | Record evidence; flip `specs/README.md`; expand `phase-4-react-port.md` to ACTIVE after the React 19 research gate |
