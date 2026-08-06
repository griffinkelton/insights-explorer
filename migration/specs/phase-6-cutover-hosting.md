# Phase 6 — Cutover, Hosting, Retire Streamlit (outline — stub)

> ⚪ **STUB** — Phase 6 gate closed. **Research gate must run before this stub is expanded** (see below). No code is written from this file yet.
> **This file carries the §17 operational-readiness deferred gates** (master-plan §17) — they apply only before a hosted beta/public demo, not Phase 1.

## Purpose

Single-origin production deployment: built React SPA served statically behind the FastAPI container (cookies, OAuth callbacks, CORS, SSE all same-origin), Cloud Run hosting, Streamlit retirement after feature parity, and the documented rollback path. The multi-stage Dockerfile pattern is already drafted in `../policies/dockerfile-pattern.md`.

## Inputs / source documents

- master-plan §10 (Phase 6), §11-E (CI/CD), §12 (SPA fallback in `api/main.py`), §13 (open decision #4 Cloud Run), §14 (DoD — feature parity, credential hygiene, docs, whisperer-30 archive)
- `../policies/dockerfile-pattern.md` (Vite build → FastAPI runtime serving the SPA, SPA fallback route, verification checklist)
- `../policies/branch-and-freeze-policy.md` (Streamlit freeze + lift criteria)
- master-plan §17 (below) + `../policies/data-retention-policy.md` (retention controls for hosted operation)

## Tracks consumed

- **C** (tests): full-parity regression + hosted smoke tests at the overall DoD level (master-plan §14).
- **D** (security/credentials): credential-hygiene sweep enforced in CI; Workload Identity Federation / managed identities + managed secrets preference.
- **E** (CI/CD): unified frontend+backend gates; Cloud Build + Cloud Run configuration; smoke script reworked for the new stack.
- **F** (retention/AI boundary): hosted retention controls; export metadata-only logging.
- **G** (research discipline): Cloud Run readiness prompt (archive §3.12, prompt 4) runs before this stub expands.

## Research gate — REQUIRED before expansion

Run the **Cloud Run readiness** prompt (archive §3.12, prompt 4): container static-file serving + SPA fallback patterns, SSE timeout/reconnect/disconnect/concurrency, cookie security behind Cloud Run proxy headers, request-size + HTTP/1 vs end-to-end HTTP/2 implications (32 MiB HTTP/1 limit supports the 25 MB browser cap — HTTP/2 not selected), memory/concurrency for Pandas/XLSX ingestion, health/readiness + rollout strategy. Return a production checklist + Cloud Build/Cloud Run config review.

## Task outline (expand before execution)

- [ ] Multi-stage Dockerfile per `../policies/dockerfile-pattern.md`; SPA fallback route in `api/main.py` (Phase 6 addition); `pandas>=2.3.3` / `python:3.14-slim` floors (archive §3.10 item 6).
- [ ] Frontend + backend CI gates unified (`.github/workflows/test.yml` + `cloudbuild.yaml`); smoke script reworked for the new stack.
- [ ] Feature-parity checklist (12 items) green in the new UI; Streamlit retired from the default path; whisperer-30 archived with a fold-in note.
- [ ] Credential hygiene sweep: `check_credentials.py` extended (Phase 1 task) enforced in CI; no live credentials in repo/history/captures.
- [ ] Rollback plan: Streamlit available privately while React/FastAPI stabilizes; feature flag or separate beta URL; rollback criteria route users to Streamlit or disable the affected FastAPI feature — never emergency production code changes.
- [ ] **Deferred gates from master-plan §17** (checkboxes, expandable when the beta/demo decision is made): product-mode decision (local/private beta/public demo) · auth/workspace isolation before multi-user · log/backup/error-reporting scrubbing · AI quota/rate-limit/kill-switch · rollback + accessibility/performance release checks. Security-posture preference: Workload Identity Federation / managed identities, managed secrets, least-privilege scopes.

## Exit criteria

- [ ] Single-origin deployment live on Cloud Run (or decided equivalent); `/healthz` + SPA route + SSE verified behind the proxy.
- [ ] Feature parity complete; Streamlit retired; whisperer-30 archived.
- [ ] Three release gates green at the overall DoD level (master-plan §14).
- [ ] §17 deferred gates either closed or explicitly scheduled.

## Gate table — Phase 6 gate (overall migration DoD)

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 6 — cutover | Cloud Run deploy checklist green · parity list green · rollback drill documented · CI gates green | You + implementation agent | Record evidence; flip `specs/README.md` all DONE; master-plan §14 DoD complete; update `migration/` status + repo docs (README/ARCHITECTURE/CHANGELOG/RELEASE_CHECKLIST) |
| §17 deferred gates | Product-mode decision + the five checkboxes | You (product owner) | Expand this file's §17 section when the hosted-beta decision is made |

## Parked/absorbed content

- master-plan §17 operational readiness (product modes table, 5 deferred checkboxes, security posture, out-of-scope list) — reproduced in full here when this phase activates.
- `../policies/dockerfile-pattern.md` — the concrete build/runtime pattern this phase executes.
