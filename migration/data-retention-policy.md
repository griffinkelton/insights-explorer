# Data Retention & AI Data-Boundary Policy

**Status:** 🔵 Planning — written **before the API exists** (master-plan revision 2026-08-05). Binds Phase 1 implementation and must be revisited at Phase 5 (GA4) and Phase 6 (cutover) as new data surfaces arrive.

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

- **Proposed default:** uploaded files live **only for the lifetime of the server session** — no persistence layer for raw uploads. Env-overridable `RETENTION_HOURS` (proposed default 24 h) for any future persisted dataset store. ⚠️ *Confirm with product before Phase 1.*
- Uploaded bytes are released when the session expires or "Clear Data" runs.

## 3. Raw dataframe persistence

- DataFrames are held **in the session/dataset store only** (in-memory in dev; shared store in staging). Never written to disk by default.
- A persisted dataset is an explicit, separate feature decision — never an implementation convenience.

## 4. Session expiry

- **Proposed defaults (confirm):** idle timeout ~2 h; absolute maximum ~12 h. After expiry: dataset reference, OAuth credentials, filter/metric/chat state, and usage-ledger entries are purged.

## 5. "Clear Data" semantics

- Deletes: dataset + preview rows, quality/analysis cache, chat context, export temp files.
- Does **not** clear: OAuth credentials (separate "disconnect" action) or theme preference.
- The React "Clear Data" call maps to a single server endpoint that performs exactly the above — no client-side partial clears.

## 6. Export logging

- Logs record metadata only: export format, row count, timestamp, session id — **never row content**.
- Export-log retention is bounded (proposed 30 days) and sanitized per the existing credential-guard rules (`scripts/check_credentials.py`, pre-commit).

## 7. Gemini prompt allowlist

- Only fields present in the current `DataContext` (per `plans/ga4-measurement-contract.md`) may be sent to Gemini, constructed via `utils/prompt_templates.py` — never the whisperer-30 hardcoded BrainGuide prompt.
- Never included: provider tokens, session identifiers, secrets, filenames containing PII, or any field outside the allowlist.

## 8. Identifier removal / aggregation

- Identifiers (email, names, device IDs, user-level rows) are **removed or aggregated** before any AI call — consistent with the app's aggregate-only GA4 reality.
- The existing `utils/sanitize.py` rules extend to the API boundary.

## 9. Enforcement

- Enforced at the service layer: `dataset_service` (ingestion + retention), `chat_service` (prompt construction), `export` (logging).
- The **contract gate** (master-plan §14) includes tests asserting no disallowed fields appear in chat/export payloads.

## 10. Review cadence

- Revisit at Phase 5 (GA4 OAuth — new credential surfaces) and Phase 6 (cutover — hosting/provider decisions), and whenever a persistence feature is proposed.

---

*Drafted 2026-08-05 as part of the master-plan revision pass (peer review: "specify data retention now"). Proposed defaults are flagged ⚠️ for product confirmation before Phase 1 code.*
