# `.env` Rotation Checklist — `insights-whisperer-30` (Phase 0 security gate)

**Date:** 2026-08-05
**Status:** Checklist — execution is manual (consoles + git), **no code changes**.

This is the concrete checklist behind Batch 3's "do this before anything else" security item and the README's action item 1. Execute it **before any whisperer-30 code is copied into `insights-explorer`** (Phase 4).

## 0. Why this exists (verified facts)

| Fact | Evidence |
|---|---|
| `.env` is **tracked** in the whisperer-30 repo | Repo root listing includes `.env` (62 bytes); git history shows commit `9059739` ("Changes") touching it |
| No `.env.example` exists | `gh api .../contents/.env.example` → HTTP 404 |
| `.gitignore` has **no** `.env` rule | Only `*.local`, `.dev.vars`, etc. — nothing excludes `.env` |
| The captured reference snapshot is clean | `migration/whisperer-30-reference/` deliberately excluded `.env` (see `WHISPERER-30-REFERENCE.md`) |
| Contents **not** decoded during ingest | Treat as potentially live credentials until proven otherwise |

**Operating assumption: the file may contain real, usable credentials. Treat it as already compromised.**

---

## Phase A — Inspect (read-only; safe to run)

```bash
# Every commit that ever touched .env (all branches)
git -C <whisperer-30-clone> log --all --oneline -- .env

# Full history of the file (this reveals the secrets; do not paste output into chats/PRs)
git -C <whisperer-30-clone> log -p --all -- .env

# Which values are real vs placeholder — check each key against its provider
git -C <whisperer-30-clone> show <commit>:.env | grep -E '^[A-Z_]+=' | sed 's/=.*/=<redacted>/'   # key names only, never values

# Remote metadata (names/sizes only — do not decode contents)
gh api repos/griffinkelton/insights-whisperer-30/commits --jq '.[] | .sha[0:7] + " " + (.commit.message | split("\n")[0])' --paginate | head -20
gh api repos/griffinkelton/insights-whisperer-30/contents/.env --jq '{size, sha: .sha[0:8]}'
```

## Phase B — Identify what's at risk

Classify each key found in Phase A against its provider, and mark real vs placeholder:

| Provider | Look for | Real credential looks like |
|---|---|---|
| Google Cloud / OAuth | `CLIENT_ID`, `CLIENT_SECRET`, API keys, Picker `DEVELOPER_KEY`, project number | Long alphanumeric/`GOOG...` strings; `AIza...` for API keys |
| Gemini / AI Studio | `GEMINI_API_KEY` | `AIza...` |
| Lovable | `LOVABLE_*` tokens, AI gateway keys | Opaque strings |
| Anything else | Supabase/Postgres/other | `postgres://...`, `sbp_...`, `sk_...` |

- Any **real** value → rotate (Phase C).
- **Placeholder** values (`your-key-here`, `changeme`, empty) → safe to leave, but still delete the file (Phase D) so the pattern doesn't recur.

### Suspected keys from the conversation export (2026-08-05)

During sanitization of `freebuff-conversation-080525.md` (repo root, committed 2026-08-05) two Google API-key-shaped strings were found and **redacted** in the committed file:

- `AIzaSyC4mri…` prefix key shape (×3 occurrences)
- `AIzaSyDaGmW…` prefix key shape (×1 occurrence)

*(Full fingerprints were redacted from this checklist by the repo's credential guard; the sanitized originals are recoverable from the local pre-sanitization copy only — not from git history.)*

Ownership rule at rotation time (gate 1):
- If a fingerprint belongs to the **insights-explorer** GCP / Drive-Picker / Gemini setup → **treat as exposed and rotate** (the conversation was shared with external reviewers).
- If it originated from the **whisperer-30 (Lovable) tracked `.env`** → those are Lovable's keys, not ours to rotate — still remove the `.env` from that repo per Phase D and confirm nothing of ours uses the same key.

## Phase C — Rotate / revoke (manual, at the provider consoles)

1. **Google Cloud Console** (console.cloud.google.com):
   - OAuth 2.0 Client IDs: create new credentials, **delete the old client** (both the secret and the client ID once nothing references them).
   - API keys: **regenerate** any that exist; restrict the new Picker `DEVELOPER_KEY` to HTTP referrers (research correction 2).
   - Note the **project number** — you'll need it later for `setAppId` (plan Phase 5 amendment 2).
2. **Google AI Studio** (aistudio.google.com): regenerate the Gemini API key.
3. **Lovable**: any exposed Lovable tokens — revoke in the Lovable dashboard if listed; otherwise assume the account-level key is burned.
4. **Anything else** found in Phase B: rotate at its provider.

> Rotate **even if the value looks inert**. Cost of a needless rotation is minutes; cost of a live leaked key is a bill/abuse incident.

## Phase D — Remediate the repo

```bash
# 1. Remove .env from the index (keeps it on disk for the .env.example pass, then delete it)
git -C <whisperer-30-clone> rm --cached .env
rm <whisperer-30-clone>/.env        # or move to a gitignored local secrets store

# 2. Add a safe template (keys only, safe placeholders, no values)
#    <whisperer-30-clone>/.env.example
#    VITE_API_BASE=/api
#    # + any keys discovered in Phase B with <your-key-here> placeholders

# 3. Add the gitignore rule
#    .env
#    .env.*
#    !.env.example

# 4. Optional but recommended: scrub history (rotate-only is acceptable if time-boxed)
#    pip install git-filter-repo
#    git -C <whisperer-30-clone> filter-repo --invert-paths --path .env
#    ⚠️ filter-repo rewrites history — coordinate with any other cloners first.
#    If you skip scrubbing, assume the key remains in history and rotate is mandatory (it is anyway).
```

## Phase E — Prevent recurrence

1. Extend the existing guard: `scripts/check_credentials.py` + `.pre-commit-config.yaml` + the credential-guard tests to cover the **new FastAPI env vars** (`API_SESSION_SECRET`, `API_CORS_ORIGINS`, `FRONTEND_URL`, `MAX_UPLOAD_BYTES` — F4 §3) — keys present, values placeholder-only in `.env.example`.
2. Add a secret-scanning hook (gitleaks / detect-secrets) to the whisperer-30 clone **before** it's copied in; keep it for the merged repo.
3. **History-wide scan (Gate 1 evidence, 2026-08-06):** run the secret scan across **full git history**, not just staged files — e.g. `gitleaks git` (or `git log -p | <guard>`) on both the whisperer-30 clone and `insights-explorer` — to prove no live secret was committed anywhere previously. Record the scan result (no secret values) as Gate 1 evidence.
4. Never commit a `.env` again: the gitignore rule + a CI step that fails if `.env` appears in `git ls-files`.

## Verification (done = checklist complete)

- [ ] `git ls-files | grep -c '^\.env$'` → `0` (no `.env` tracked)
- [ ] `.env.example` committed with key names + safe placeholders only
- [ ] `.gitignore` contains `.env` (+ `!.env.example`)
- [ ] Every real credential from Phase B rotated/revoked at its provider (assumption-of-compromise applied)
- [ ] New FastAPI env vars added to `scripts/check_credentials.py` allowlist/requirements (Phase 1)
- [ ] Recorded in the archive change log (§4.8) with the execution date

---

*Cross-refs: plan Batch 3 Review Addendum (Security — "do this before anything else"); `migration/README.md` action item 1; archive §4.6 (`.env` claim verification).*
