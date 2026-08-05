# Migration Branch + Feature Freeze Policy
## `feat/react-fastapi-migration` — process decision from Batch 3, written down

**Date:** 2026-08-05
**Status:** Policy document (pre-planning only). The branch is **not yet created** — the migration docs package commits to `main` first; create the branch with the one-liner in §4 when work starts.

## 1. Why this policy exists

Batch 3 Review Addendum (plan, Process decision 1) put it plainly: **every new Streamlit feature during the migration becomes a second migration obligation.** The API contract needs to stabilize without the Streamlit UI accumulating more surface area to port. This document turns that one-liner into an operating policy.

## 2. Branch model

```
main  (production Streamlit line)
  │  production/security fixes only during the freeze
  │  (fix forward → regularly merged down)
  ▼
feat/react-fastapi-migration  (cut from main; ALL migration work lives here)
  │  Phases 1–6: api/, frontend/, tests, docs
  ▼
cutover (Phase 6): merge back to main when feature parity is reached
```

| Branch | Role during freeze |
|---|---|
| `main` | Deployable Streamlit app. Only **production/security fixes**, CI/deploy fixes, and docs land here. |
| `feat/react-fastapi-migration` | All migration code (FastAPI `api/`, React `frontend/`, API-contract tests). Cut from a fresh `main`; never merged back until Phase 6 (or until the API contract is stable enough to coexist — see §3 lift criteria). |

**Fix-forward rule:** when a production bug is fixed on `main`, merge `main` → migration branch promptly so the branch never drifts. Do **not** hotfix directly on the migration branch and let it languish.

## 3. Feature freeze rules

**Frozen on `main` (deferred to post-migration):**

- New Streamlit features or UI work (anything that adds `st.*` surface)
- Streamlit UI polish / theme work (the interstitial work is done; further UI work belongs in React)
- Non-essential refactors of `components/` or `app.py`
- New experiments that touch the presentation layer

**Still allowed on `main` during the freeze:**

- Production/security fixes (credential guard, OAuth/token handling, data-safety, sanitization)
- CI / deploy / infra fixes (`.github/workflows/test.yml`, `cloudbuild.yaml`)
- Documentation (this package is the proof)
- Dependency bumps that are security-driven

**What happens to new feature requests:** park them in `IDEAS.md` / the roadmap tagged `post-migration`; do not let them sneak into `main` "while we're here."

**The migration-impact test for any `main` change:** does this touch `st.session_state`, `components/`, or `app.py` in a way that grows the porting surface? If yes and it's not a security/production fix → it waits. Use `migration/session-state-inventory.md` as the checklist — any *new* key that appears during the freeze needs a documented replacement before landing.

## 4. Creating the branch (when you're ready — not part of this commit)

```bash
git checkout main && git pull
git checkout -b feat/react-fastapi-migration
# confirm: git branch --show-current  →  feat/react-fastapi-migration
```

## 5. Lift criteria

1. **Phase 1 DoD met** (upload → server session → React preview/quality → clear-data, with contract tests green) → freeze **relaxes** to: "no new Streamlit features that add migration surface; small Streamlit fixes OK."
2. **Phase 6 cutover** (React + FastAPI at parity, Streamlit retired) → freeze **lifted**; `feat/react-fastapi-migration` merges to `main`.

Until Phase 1 DoD, treat the freeze as strict.

## 6. Related rules carried alongside

- **Living design reference:** `insights-whisperer-30` stays as a reference/fallback until the `frontend/` build is reproducible (Batch 3 Process decision 2) — do not archive it early.
- **Security gate stays ahead of the branch:** run `migration/env-rotation-checklist.md` (`.env` rotation) before Phase 4 copies whisperer-30 code in.

---

*Cross-refs: plan Batch 3 Review Addendum (Process decisions 1–2); `migration/README.md` action items 1–2; `migration/session-state-inventory.md`; `migration/env-rotation-checklist.md`.*
