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

## 8. Identifier removal / aggregation

- Identifiers (email, names, device IDs, user-level rows) are **removed or aggregated** before any AI call — consistent with the app's aggregate-only GA4 reality.
- The existing `utils/sanitize.py` rules extend to the API boundary.

## 9. Enforcement

- Enforced at the service layer: `dataset_service` (ingestion + retention), `chat_service` (prompt construction), `export` (logging).
- The **contract gate** (master-plan §14) includes tests asserting no disallowed fields appear in chat/export payloads.

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
