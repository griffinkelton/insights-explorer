# Data Retention & AI Data-Boundary Policy

**Status:** 🔵 Planning — written **before the API exists** (master-plan revision 2026-08-05). **Gate 6: APPROVED 2026-08-06** — all five §11 decisions confirmed by the product owner (reviewer-endorsed defaults; `RETENTION_HOURS` 24 h is an **upper bound** — effective Phase 1 retention is ≤ 12 h, see §2). Binds Phase 1 implementation and must be revisited at Phase 5 (GA4) and Phase 6 (cutover) as new data surfaces arrive.

---

## 1. Purpose & scope

The app handles client analytics data and potentially sensitive public-health/equity context. "Server-owned" sessions are better than browser-owned storage, but they are **not automatically privacy-safe**. This policy fixes, before any endpoint ships:

1. How long uploaded files are retained.
2. Whether raw dataframes are persisted or held only per session.
3. When a session expires.
4. What "Clear Data" deletes.
5. What export logging retains.
6. Which fields are allowed into Gemini prompts.
7. Which identifiers must be removed or aggregated before an AI call.

## 2. Uploaded data retention

- **Approved (2026-08-06):** uploaded files live **only for the lifetime of the server session** — no persistence layer for raw uploads.
- **Phase 1 retention (effective):** raw uploads are session-scoped and are deleted on **Clear Data, idle timeout, absolute session expiry, or process restart**. The effective retention is the **earlier of session expiry and `RETENTION_HOURS`** — with the approved 2 h idle / 12 h absolute session policy, in-memory uploads persist for **no more than 12 hours** in Phase 1.
- `RETENTION_HOURS` (default **24 h**) is an **upper bound for a future persisted dataset store**, not a guarantee of 24-hour availability in Phase 1. *Lengthen only with authenticated persistent workspaces, a user-visible retention notice, and a reliable Clear Data control (reviewer guidance 2026-08-06).*
- Uploaded bytes are released when the session expires or "Clear Data" runs.

## 3. Raw dataframe persistence

- DataFrames are held **in the session/dataset store only** (in-memory in dev; shared store in staging). Never written to disk by default.
- A persisted dataset is an explicit, separate feature decision — never an implementation convenience.

## 4. Session expiry

- **Approved (2026-08-06):** idle timeout **2 h**; absolute maximum **12 h**. After expiry: dataset reference, OAuth credentials, filter/metric/chat state, and usage-ledger entries are purged.

## 5. "Clear Data" semantics

- Deletes: dataset + preview rows, quality/analysis cache, chat context, export temp files.
- Does **not** clear: OAuth credentials (separate "disconnect" action) or theme preference.
- The React "Clear Data" call maps to a single server endpoint that performs exactly the above — no client-side partial clears.

## 6. Export logging

- Logs record metadata only: export format, row count, timestamp, session id — **never row content**.
- Export-log retention is bounded (proposed 30 days) and sanitized per the existing credential-guard rules (`scripts/check_credentials.py`, pre-commit).

## 7. Gemini prompt allowlist

- Only fields present in the current `DataContext` (per `../../plans/ga4-measurement-contract.md`) may be sent to Gemini, constructed via `utils/prompt_templates.py` — never the whisperer-30 hardcoded BrainGuide prompt.
- Never included: provider tokens, session identifiers, secrets, filenames containing PII, or any field outside the allowlist.

### 7.1 Runtime tier policy — `GEMINI_DATA_POLICY` (added 2026-08-06, Phase 3 refinement round)

The Gemini tier is an **explicit runtime policy** — it is **never inferred from the API key format** (a key's format does not reliably prove free/paid tier, billing linkage, or whether submitted content is subject to improvement/review terms). Free-tier prompts/responses **may be logged and human-reviewed** — acceptable for local synthetic/public/personally-controlled test data only, **never** client analytics data.

| Mode | Allowed | Behavior |
|---|---|---|
| `local_free` | Local development + synthetic / public / personally-controlled test data only | Startup/log warning: free-tier prompts may be logged and reviewed by humans; no hosted deployment; no client analytics data |
| `client_paid` | Hosted beta + real client analytics data | Requires documented billing/project verification + paid-tier/privacy review before deployment |
| `disabled` | Nothing | AI endpoints return `503` `{"detail": "AI features are disabled."}` (typed `feature_disabled` error) |

Implementation authority: `../specs/phase-3-ai-analysis.md` Task 2 (settings) + Task 6 (route behavior); enforced in `api/config.py` (`gemini_data_policy`) and the AI routes.

### 7.2 AI environment variables (Phase 3 — names-only guard-allowlisted)

Values are **never committed**; `.env.example` holds placeholders/safe defaults only (per master-plan §11-D). Names below are allowlist-validated by `scripts/check_credentials.py` (names only — a real secret value in a committed file always fails).

| Env var | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | (none — placeholder in `.env.example`) | Provider key; the app boots without it (AI endpoints degrade to 503) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Env-configurable model; selector allowlist {`gemini-2.5-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`} (shut-down 2.0 / deprecated 1.5 pruned) |
| `GEMINI_DATA_POLICY` | `local_free` | Runtime tier policy (§7.1) |
| `AI_MAX_CONTEXT_TOKENS` | `24000` | Total context budget = input allowance + reserved output (corrected 2026-08-06: effective input allowance = 24,000 − 4,096) |
| `AI_RESERVED_OUTPUT_TOKENS` | `4096` | Reserved output; provider `max_output_tokens` is set to this value (corrected 2026-08-06) |
| `AI_MAX_CONTEXT_CHARS` | `96000` | Deterministic-trim ceiling (≈ chars÷4 = 24k tokens) |
| `AI_FIRST_TOKEN_TIMEOUT_SECONDS` | `30` | First-token deadline (typed `timeout` event on expiry) |
| `AI_GENERATE_TIMEOUT_SECONDS` | `60` | Non-streaming per-request timeout |
| `AI_STREAM_TIMEOUT_SECONDS` | `120` | Whole-stream deadline |
| `AI_QUEUE_WAIT_SECONDS` | `30` | Bounded `ai_lock` queue-wait ceiling — Option A (settled 2026-08-06) |

## 8. Identifier removal / aggregation

- Identifiers (email, names, device IDs, user-level rows) are **removed or aggregated** before any AI call — consistent with the app's aggregate-only GA4 reality.
- The existing `utils/sanitize.py` rules extend to the API boundary.

## 9. Enforcement

- Enforced at the service layer: `dataset_service` (ingestion + retention), `ai_service` (deterministic-context assembly, identifier scrub, prompt-budget trim, `GEMINI_DATA_POLICY` mode), `export` (logging).
- The **contract gate** (master-plan §14) includes tests asserting no disallowed fields appear in chat/export payloads, and that the runtime tier mode (`local_free` / `client_paid` / `disabled`) behaves as documented.
- AI env vars are names-only guard-allowlisted (§7.2) — real secret values in committed files always fail the credential guard.

## 10. Review cadence

- Revisit at Phase 5 (GA4 OAuth — new credential surfaces) and Phase 6 (cutover — hosting/provider decisions), and whenever a persistence feature is proposed.

## 11. Decision points requiring approval (gate 6)

This policy was **drafted, not decided** (third-review refinement 2026-08-05) until the **product owner approved all five points on 2026-08-06** (seventh review round — reviewer-endorsed defaults), closing gate 6 in `../master-plan.md` Phase 0. Decisions are binding for Phase 1; amendments require a dated addendum.

| # | Decision | Approved value (2026-08-06) | Status |
|---|---|---|---|
| 1 | Raw upload retention duration | Session-scoped only; deleted on Clear Data / idle timeout / absolute session expiry / process restart — **effective Phase 1 retention ≤ 12 h** (earlier of session expiry and `RETENTION_HOURS`); `RETENTION_HOURS` **24 h** is an upper bound for a future persisted store, not a 24 h availability guarantee | ✅ Approved 2026-08-06 |
| 2 | Session idle timeout + absolute expiry | **2 h idle / 12 h absolute** | ✅ Approved 2026-08-06 |
| 3 | What "Clear Data" deletes immediately | Dataset, preview rows, quality/analysis cache, chat context, export temp files (not OAuth credentials or theme) | ✅ Approved 2026-08-06 |
| 4 | Whether export/report metadata is logged | Format, row count, timestamp, session id only — never row content; 30-day retention | ✅ Approved 2026-08-06 |
| 5 | What Gemini receives | Fields from the current `DataContext` allowlist only; identifiers removed/aggregated before AI calls; **provisional metrics carry caveats, unavailable metrics are never numeric evidence** (metric-state policy) | ✅ Approved 2026-08-06 |

---

*Drafted 2026-08-05 as part of the master-plan revision pass (peer review: "specify data retention now"). All five §11 defaults **approved by product owner 2026-08-06** (seventh review round — reviewer-endorsed defaults; the flagged 24 h upload-retention judgment call was confirmed). Binding for Phase 1. Amendments require a dated addendum.*

*2026-08-06 addendum (Phase 3 refinement round): §7 extended with the **`GEMINI_DATA_POLICY` runtime tier policy** (§7.1 — explicit policy, never inferred from key format) and the **AI environment-variable allowlist** (§7.2). Implementation authority: `../specs/phase-3-ai-analysis.md` (Tasks 1–2, 5–7). The five §11 gate-6 decisions are unchanged.*
