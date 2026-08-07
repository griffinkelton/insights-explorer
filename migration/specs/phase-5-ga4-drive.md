# Phase 5 — GA4 OAuth + Drive Import (executable spec)

> 🔵 **ACTIVE — expanded 2026-08-06 from the stub.** **Research gates must run before implementation begins** (Task 0) — the spec is execution-ready *after* Task 0 records its evidence and the open decisions in §Decisions are settled. No code is written from this file until then.
> **This file is the tactical authority for F4's GA4 sections** (F4 §8 OAuth endpoints + §11 React callback — **superseded for execution**, parked here).
> **Phase 5 depends on Phase 1** (session/schema layer) **and Phase 4** (React shell, `/auth/ga4/callback` route, `api.ts` boundary normalization, store stubs). Both are DONE.

## Purpose

GA4 OAuth (connect/callback/pull) and Drive import. Both flows terminate server-side: Google redirects to **FastAPI** (`/api/v1/ga4/callback`), FastAPI validates PKCE/state and exchanges the code, then redirects the browser to React with only a safe `status`/`reason`. The browser never receives GA4 provider credentials, any refresh token, a client secret, or a persisted connection record. For Google Picker only, the browser temporarily receives a **currently valid, short-lived Drive access token in component memory immediately before Picker opens** (token-containment rules: Task 4). Drive ingestion ports the existing hardened Python client (`utils/drive_client.py` — `download_drive_file` is ported/adapted, **not redesigned**; see master-plan §9 trust boundary). **Phase 5 Drive path is download-and-ingest only — no upload-to-Drive code** (a future export/backup feature opens a separate workstream; see Task 2).

**Local-first posture (master-plan principle 9):** in-memory `SessionStore`/`DatasetStore` remain acceptable through Phase 5 for local use. The OAuth transaction store follows the parked flow below and may use an in-memory ephemeral implementation keyed by the session (Redis arrives in Phase 6 for hosted/beta). **In-memory is insufficient as a *generic* state store only when multi-instance hosting starts** — not for single-process Phase 5.

## Inputs / source documents

- master-plan §9 (Phase 5), §11-A (state placement: ephemeral store for OAuth state/PKCE), §13 (open decisions #7 GA4 limits, #9 Drive browse UX), §14 (release gates — GA4 + Drive user flows), §15 (risk register)
- **Parked from F4:** §8 `api/services/ga4_service.py` + `api/routes/ga4.py` (with the PKCE corrections from F4's Research Fold-In Cross-Check), §11 React callback route
- `utils/ga4_client.py`, `utils/drive_client.py` (3-layer size validation, server metadata authority, MIME allowlist, Sheets export path, typed errors — the canonical Drive trust boundary)
- `plans/ga4-measurement-contract.md` — metric-status policy; `POST /api/v1/ga4/pull` returns a `DatasetContext` whose `metrics` carry contract provenance (`contract_row`, `validation_status`); rows 3–5 stay `unavailable` until event-level access exists (aggregate-only reality)
- `../policies/data-retention-policy.md` §2/§5 — 100 MB server-side ingestion subject to metadata/streaming/MIME/decompression/row/column/temp-file limits
- `../whisperer-30-reference/LOVABLE-UPDATES-080525.md` + `../whisperer-30-reference/LOVABLE-ACTIONS-080526.txt` — drive-list contract shape; **Import gotcha**: the prototype's Import only fakes `loadData("drive · <name>")` — the port must wire download → ingest → quality
- `../whisperer-30-reference/UI-CAPTURE-8b4b7b9/MANIFEST.md` — Drive/GA4 UI port-classification (`initial_mount` columns), `drive_picker_component_frontend/` reference
- `api/services/ai_service.py` + `api/schemas.py` (Phase 3) — `DatasetContext` shape reused by `POST /api/v1/ga4/pull`
- `frontend/` (Phase 4) — `api-types.ts`, `explorer-store.tsx` Phase 5 stubs (`connectGA4`, `handleGA4Callback`, `connectDrive`, `downloadFromDrive`), `routes/auth/ga4/callback.tsx` (already scaffolded with `validateSearch`)

## Tracks consumed

- **A** (state/session): ephemeral OAuth state/PKCE store — in-memory session-keyed implementation acceptable for single-process Phase 5 (master-plan §9); Redis swap is Phase 6.
- **B** (API/contract): `/api/v1/ga4/*` + `/api/v1/drive/*` schemas; callback status vocabulary locked (`success` / `cancelled` / `error&reason=<code>`).
- **C** (tests): GA4 + Drive contract tests; Drive E2E acceptance matrix in Playwright.
- **D** (security/credentials): provider tokens never reach the browser; least-privilege scopes; Picker key referrer-restricted (only if Picker chosen).
- **F** (retention/AI boundary): 100 MB server-side ingestion subject to metadata/streaming/MIME/decompression/row/column/temp-file limits (`../policies/data-retention-policy.md` §2/§5).
- **G** (research discipline): GA4 feasibility + selected Drive-UX research gates run before implementation (Task 0).

---

## Decisions still open (settled in Task 0 / by owner — see §Decisions)

These are the *only* things not yet executable; everything below is specified up to them. **Owner decision-detail fold-in (2026-08-06):** D3 locked fallback (`metrics × date`, 90 days, daily grain) + Task 0 decision rules, consent-state model + labels, live-smoke coverage checklist, sidebar action states — recorded in Task 0/1/3/5/6. **Implementation-detail fold-in (2026-08-06, second round):** GA4 pull contract (canonical metrics, generic pagination, provenance, quota record-only + typed error taxonomy), disk-backed Drive download + no-upload boundary, Picker JIT/memory-only token rules — recorded in Task 0/2/3/4/6.

| # | Decision | **Settled (2026-08-06)** | Why it matters |
|---|---|---|---|
| D1 | Drive browse UX: **slide-out** (`GET /api/v1/drive/list`) vs **Picker iframe** (`POST /api/v1/drive/picker-token`) | **Both — Picker iframe first (vertical slice), slide-out as a follow-up** — both end at `POST /api/v1/drive/download`, so the choice is swappable without changing ingestion | Task 4 builds the Picker path first (`picker-token` + ported picker component); the slide-out `drive/list` contract stays specified (master-plan §9) for the follow-up swap |
| D2 | GA4 OAuth scope set | **Two separate consents** — GA4 connect requests `openid email profile analytics.readonly`; Drive connect requests `drive.file` separately (least-privilege; two button flows + two status states) | Drive scope never granted for GA4-only users; separate reconnect UX per source |
| D3 | GA4 first-pull report shape: dimensions + date range for the vertical slice | **Let Task 0 research decide, with a locked fallback** — if the probe succeeds, lock **five canonical measurement-contract metrics × `date`, daily grain, trailing 90 complete days**, pagination enabled + tested, provenance recorded; **no `defaultChannelGroup` in slice 1** (see Task 0 decision rules) | Sets the `pull` request contract, pagination math, and the compatibility-probe checklist |
| D4 | Live opt-in smoke test | **Yes — owner provides a test GA4 property + Drive account**; opt-in, never-in-CI local smoke (connect → pull → drive download) records the post-OAuth property-probe checklist | Gates the "post-OAuth compatibility probe" evidence for D3 |
| D5 | Drive import UX placement | **Sidebar** — port the captured sidebar Drive sheet per the manifest's `initial_mount` classification | Consistent with the Phase 4 sidebar shell; one Drive surface |

---

## Task 0 — Research gates + probes (required before implementation)

Run both research gates (archive §3.12 prompts), then record evidence in this section. **No Phase 5 code before Task 0 closes.**

1. **GA4 feasibility gate** (prompt 1): `runReport`/`runFunnelReport`/`getMetadata`/`checkCompatibility` compatibility; page-path × device-category engagement; questionnaire events; dimension/metric combos + thresholding; pagination/quota/retry/`returnPropertyQuota`. **Critical distinction:** separate official-documentation facts from **property-specific facts requiring a post-OAuth compatibility probe** — documentation-only research is never proof the target property supports the report. Live-verify open decision #7 (9 dims / 10 metrics, 7 for funnel).
   - **Deliverable:** a "documentation facts vs property-probe checklist" table; the property-probe section is executed only under D4 (opt-in).

   **✅ Evidence recorded 2026-08-06 (documentation-facts column):**
   - **SDK pin — pinned-SDK probe (`scripts/probe_ga4_sdk.py`, committed Task 0 artifact):** `google-analytics-data` **0.23.0** installed (requirements `>=0.18.0`); `BetaAnalyticsDataAsyncClient.run_report(request, *, retry, timeout, metadata) -> RunReportResponse` — async variant confirmed, `timeout: float` accepted; gRPC transport available (grpc installed; REST transport class also present). Request fields verified: `property, dimensions, metrics, date_ranges, dimension_filter, metric_filter, offset, limit, metric_aggregations, order_bys, currency_code, cohort_spec, keep_empty_rows, return_property_quota, comparisons`. Response fields verified: `dimension_headers, metric_headers, rows, totals, maximums, minimums, row_count, metadata, property_quota, kind`. The locked first-pull request (5 canonical metrics × `date`, 90daysAgo→yesterday, order date asc, limit 10 000, `return_property_quota=True`) **builds cleanly against 0.23.0**. `PropertyQuota` fields (each `consumed`/`remaining`): `tokens_per_day, tokens_per_hour, concurrent_requests, server_errors_per_project_per_hour, potentially_thresholded_requests_per_hour, tokens_per_project_per_hour` (the last two are additions to the Task 3 snapshot).
   - **Pagination (REST reference):** `offset` = zero-based row index; `limit` defaults to **10,000** and the API returns a **maximum of 250,000 rows per request**; it returns fewer rows when fewer dimension values exist (≈90 rows for `date` × 90 days — the D3 90-row reality). ⚠️ The `PAGE_SIZE = 100_000` comment in `utils/ga4_client.py` is **stale** (official max is 250,000) — fix the comment when Task 3 lands. Sources: developers.google.com REST `properties.runReport` + `/devguides/reporting/data/v1/basics` (2026-08-06).
   - **Quotas (authoritative — supersedes any earlier figure):** Standard **200,000 Core tokens/property/day · 40,000/hour · 14,000/project-per-property/hour · 10 concurrent requests · 10 server errors/project/property/hour**; 360: 2,000,000 / 400,000 / 140,000 / 50 / 50. **120 potentially thresholded requests/hour** (dims `userAgeBracket`, `userGender`, `brandingInterest`, `audienceId`, `audienceName`). Token cost rises with row count, dims/metrics count, filter complexity, date-range length, **data cardinality** (high-cardinality dims like `pagePath` raise cost — validates the low-cardinality slice-1 shape), and event volume. Source: developers.google.com `/devguides/reporting/data/v1/quotas` (fetched 2026-08-06).
   - **Thresholding:** applied by default for low-traffic/sensitive data; `potentially_thresholded_requests_per_hour` is a `PropertyQuota` field (SDK-verified). Actual behavior on the test property is confirmed only by the D4 probe.
   - **Errors/retry:** `google.api_core.exceptions.ResourceExhausted` (429) · `DeadlineExceeded` (504) · `ServiceUnavailable` (503) · `InternalServerError` (500); client libraries retry idempotent methods by default — **no app-level retry loop on top** (Task 3 taxonomy governs). Source: googleapis.dev `python/google-api-core/latest/exceptions.html`.
   - **Scope:** `https://www.googleapis.com/auth/analytics.readonly` (REST reference authorization scopes). Existing `utils/ga4_client.py` combines `analytics.readonly` + `drive.file` in one grant — **Phase 5 splits these into two consents (D2); the split is a migration point, not a port**.
   - **Open decision #7:** the **9-dimension cap is confirmed** (official guide: "up to nine dimensions"); the **10-metric / 7-for-funnel figures remain documentation-reported** (limits page 404) — pending the D4 probe.
   - **Property-probe column (D4, pending):** which of the five canonical metrics the test property supports · thresholding on low-traffic synthetic data · real token cost of the locked report. Not closable without credentials.
2. **Drive browse-UX gate** — **Picker iframe path first (D1 settled)**; slide-out research is deferred to the follow-up swap:
   - **✅ Picker iframe (evidence recorded 2026-08-06):**
     - **Reference wiring (`components/drive_picker_component_frontend/src/main.ts`):** loads `https://apis.google.com/js/api.js` then `gapi.load("picker")`; builds `google.picker.PickerBuilder().setDeveloperKey(...).setOAuthToken(...).setOrigin(appOrigin)` + optional `.setAppId(...)`; `DocsView(ViewId.SPREADSHEETS).setMimeTypes([spreadsheet, text/csv, xlsx])`; emits `{kind:"picked", requestId, fileId}` / `{kind:"cancel", requestId}`. The React port reuses this builder wiring with a JIT token from `POST /api/v1/drive/picker-token`.
     - **`setAppId` takes the Cloud project number, not the ID** (Picker API reference: `setAppId('1234567890') // Cloud Project number`). Visible at GCP Console → IAM & Admin → Settings → Project number; programmatic path = Cloud Resource Manager API `projects.get` (enablement documented in Task 4/7).
     - **API key (developer key):** GCP Console → APIs & Services → Credentials; must be **restricted to HTTP referrers** (dev `http://localhost:5173/*` + production origin); public by design (ships in the frontend bundle) — never a secret, never in `picker-token` responses.
     - **OAuth access token:** passed via `setOAuthToken`; must be a currently valid token for the signed-in user; `drive.file` is a confirmed web-app Picker scope (Picker overview: web apps support `drive.file`; "to use the drive.file scope the user must be signed in while accessing the Google Picker"). **Download/export authority stays with FastAPI** — the token is JIT + browser-memory-only (Task 4).
     - **Sheets MIME reconciliation:** the reference filter includes `application/vnd.google-apps.spreadsheet`, but Phase 5 returns `workspace_export_required` for Google-native files — **the port drops Sheets from the Picker MIME filter (CSV/XLSX only) or labels it "not yet supported"** (Task 4).
   - **Slide-out (deferred, follow-up):** `files.list` pagination via `pageToken`/`nextPageToken` (max `pageSize` 1,000), shared-drive flags `supportsAllDrives`/`includeItemsFromAllDrives`/`corpora` (only if shared drives are in scope), required scopes, native-Sheets export.
   - Both terminate at the same `POST /api/v1/drive/download` — the choice is swappable without changing ingestion (master-plan §13 #9).
3. **D3 decision rules (locked fallback):**
   - If all five canonical metrics + `date` work in the selected test property → lock **metrics × `date`, daily grain, 90 days**.
   - If one or more metrics are unavailable/incompatible → record the exact incompatibility; substitute only with measurement-contract approval, or mark the metric unavailable — **never silently synthesize**.
   - If pagination, quota, or row volume is problematic → keep the same semantic report, reduce the date range only for the test fixture, and document the production paging behavior.
   - Do **not** add `defaultChannelGroup` in slice 1 — it adds a second semantic and cardinality axis; it belongs to the next report-shape increment after the contract, property probe, provenance, and import parity are stable.
4. **Task 0 acceptance (2026-08-06):** Gate 1 + Gate 2 **documentation-facts evidence recorded with dates + sources** (above); D1–D5 settled; SDK pin + Picker API facts resolved; **D4 property-probe column remains explicitly pending** (cannot close without test credentials).
5. **Residual research gaps (after the 2026-08-06 evidence pass):**
   - ✅ **Resolved — GA4 SDK pin + async shape:** `google-analytics-data` **0.23.0** (requirements `>=0.18.0`); `BetaAnalyticsDataAsyncClient.run_report(request, *, retry, timeout, metadata)` verified by pinned-SDK probe (Gate 1 evidence).
   - ✅ **Resolved — Picker API facts:** `setAppId` = Cloud project **number**; developer key = public API key restricted to HTTP referrers; `drive.file` supported by web-app Picker; reference wiring recorded (Gate 2 evidence). **Owner console action remains:** create the referrer-restricted API key + note the project number — no code can do this.
   - ⏳ **Open — property-specific compatibility probe (D4):** which canonical metrics the test property supports + thresholding + real token cost — **requires owner test-property credentials**; the single remaining empirical gate.
   - ⏳ **Open — open decision #7 tail:** 10-metric / 7-for-funnel figures still documentation-reported (limits page 404) — re-verify under D4.
   - ⏳ **Deferred by design:** Workspace/Sheets export contract (`workspace_export_required` is the Phase 5 behavior); token-service shape; loader `filename=` refinement.
   - ⚠️ **Implementation note:** stale `PAGE_SIZE = 100_000` comment in `utils/ga4_client.py` (official max 250,000 rows/request) — fix the comment when Task 3 lands.

---

## Task 1 — GA4 OAuth service + routes (server-owned, PKCE S256)

**Files:** `api/services/ga4_service.py` · `api/routes/ga4.py` · settings additions in `api/config.py` (`GA4_CLIENT_ID`, `GA4_CLIENT_SECRET`, `GA4_REDIRECT_URI` — guard allowlist; `GA4_ENABLED` policy flag mirroring `GEMINI_DATA_POLICY` semantics: `disabled` fails fast, never an undefined runtime state).

### Flow (parked F4 §8, made production-real — owner guidance 2026-08-06)

```
Browser → POST /api/v1/ga4/connect → FastAPI creates state + PKCE verifier
  → ephemeral store keeps short-lived transaction (10-min TTL, NX)
  → HttpOnly transaction cookie binds the browser to the transaction
  → 302 to Google
Google → GET /api/v1/ga4/callback → FastAPI consumes state exactly once
  → verifies transaction cookie (compare_digest)
  → exchanges code server-side (stored verifier + single allowlisted redirect URI)
  → persists encrypted provider tokens server-side (session-owned)
  → rotates the app session ID
  → clears transaction cookie → 303 to /auth/ga4/callback?status=success
```

### Endpoints

| Endpoint | Method | Contract |
|---|---|---|
| `/api/v1/ga4/connect` | POST | `{ authorization_url }` (snake_case; locked). Creates `state` + PKCE verifier, stores `ie:oauth:state:<sha256(state)>` record `{ transaction_id, code_verifier, redirect_uri, created_at, return_path }` with 10-min TTL + `NX`, sets HttpOnly transaction cookie, returns the Google authorization URL with `code_challenge_method=S256`. **Never derive the redirect host from request headers** — allowlisted per-environment config only. |
| `/api/v1/ga4/callback` | GET | Consumes state **exactly once** (`GETDEL` or Lua get-and-delete — see parked snippet below), verifies transaction cookie via `secrets.compare_digest`, exchanges code with the stored verifier, stores encrypted tokens on the session, rotates the session ID, 303-redirects to `/auth/ga4/callback?status=success` (or `status=cancelled` / `status=error&reason=<code>`). |
| `/api/v1/ga4/status` | GET | `{ connected: bool }` — drives the React connect button state without exposing tokens. |
| `/api/v1/ga4/disconnect` | POST | Revokes + clears session provider tokens; keeps the app session. |
| `/api/v1/ga4/pull` | POST | See Task 3. |

### OAuth rules (locked)

- State + PKCE verifier from cryptographic randomness (`secrets.token_urlsafe`); PKCE S256, never plain.
- State TTL ≈ 10 minutes; one-time consumption (no replay); callback bound to the short-lived HttpOnly transaction cookie.
- One exact allowlisted Google redirect URI per environment (local/staging/prod config, never headers).
- Provider tokens stored **server-side + encrypted** (session-owned); rotated app session after OAuth completes.
- Callback status vocabulary locked: `status=success` · `status=cancelled` (supersedes `provider_denied`) · `status=error&reason=<code>` (`invalid_state` | `token_exchange_failed` | `scope_denied`). No legacy spellings in new code.
- **Clear Data does not disconnect OAuth** (retention policy: OAuth connection retained; only dataset-derived state clears).

```python
# One-time state consumption — atomic get-and-delete (Redis GETDEL or Lua fallback):
CONSUME_STATE = """
local value = redis.call("GET", KEYS[1])
if value then redis.call("DEL", KEYS[1]) end
return value
"""
```

### Consent-state model (two application-level connections)

GA4 and Drive are **separate application-level connections** — even if Google's incremental authorization eventually returns a token containing previously granted scopes, a combined token result is never permission to blur feature-level consent, UI state, audit records, or Clear Data behavior.

```text
GA4:   status = disconnected | connecting | connected | expired | error   scope = analytics.readonly
Drive: status = disconnected | connecting | connected | expired | error   scope = drive.file
```

Consent labels (Task 5):

```text
Connect Google Analytics — "Read aggregate Analytics reporting data from a selected GA4 property."
Connect Google Drive — "Choose a CSV or spreadsheet from Google Drive for import."
```

### Settings validation

- `GA4_CLIENT_ID` / `GA4_CLIENT_SECRET` / `GA4_REDIRECT_URI` presence checked at settings load when `GA4_ENABLED=true` (fail-fast, same pattern as Phase 3's `GEMINI_DATA_POLICY` Literal).
- Credential guard: add `GA4_CLIENT_ID` · `GA4_CLIENT_SECRET` · `GA4_REDIRECT_URI` · `GA4_ENABLED` · `DRIVE_ENABLED` to `ALLOWLISTED_ENV_VARS`; `GA4_CLIENT_SECRET` joins `SECRET_ENV_VARS` (values never committed; `.env.example` placeholders only).

---

## Task 2 — Drive service port (server-side trust boundary — port, not design)

**Files:** `api/services/drive_service.py` · `api/routes/drive.py`.

Port `utils/drive_client.py::download_drive_file` **verbatim in behavior** into `api/services/drive_service.py`:

- **Input:** `{ request_id, file_id }` (canonical, locked) — **`file_id` is the only authority input**: never trust a client-provided filename, MIME type, or byte size (master-plan §9; archive §4.18). **`request_id`** binds the selection to the active server/session picker request — stale or duplicate `request_id` returns a typed non-retryable error, and a second selection can never replace the active dataset.
- Server re-fetches metadata: `files.get(fields="id,name,mimeType,size,md5Checksum,trashed,capabilities(canDownload)")` — server-authoritative. Reject `trashed` files (`file_not_available`) and files without `capabilities.canDownload` (`download_not_allowed`).
- MIME/suffix allowlist (`DRIVE_IMPORT_MIME_TYPES` — CSV/XLSX + Google-native) enforced server-side; React sheet checks are UX guidance only.
- **Google-native Sheets are NOT auto-exported in Phase 5** — reject with typed `workspace_export_required` until an explicit export contract (allowlisted export MIME, row/size behavior, typed errors) is defined. That follow-up branch uses the same actual-byte cap + temp-file ownership; the **10 MB Sheets/docs export cap** applies there, not to Phase 5.
- Size enforcement — **declared + actual**: reject when declared metadata `size` > `MAX_INGEST_BYTES = 100 MB`; then enforce an **actual-byte counter during transfer** (`temp.tell() > max_bytes` → abort immediately). The counter covers absent/untrusted metadata and export paths — never rely on declared size alone.
- **Disk-backed temp file, not an in-memory buffer:** stream via `MediaIoBaseDownload` (256 KiB chunks) into `NamedTemporaryFile(mode="w+b", suffix=<sanitized filename suffix>, prefix="insights-drive-", delete=False)` — raw 100 MB content never occupies process RAM before Pandas allocates its own parse structures (Phase 2 `_BoundedBytesIO` is the local-upload pattern; Drive downloads at the 100 MB cap need disk backing).
- Google client code is **synchronous → run in a worker thread** (`anyio.to_thread.run_sync`) — never block the FastAPI event loop.
- Parse through the existing unified ingestion adapter (filename semantics preserved by the temp suffix); **preserve the old dataset on every failure** (replace only on success). Delete the temp artifact in `finally`/exception path — deterministic cleanup, no orphaned client data after parser/provider/timeout/cancellation/validation failures.
- **No Drive uploads in Phase 5** — download-and-ingest only. Explicit boundary: **no Drive export endpoint · no resumable upload · no app-created Drive folder · no report backup · no Drive write scope**. A future export/backup workstream would add resumable uploads only with an explicit retention, ownership, duplicate-prevention, and Drive-write-scope decision — parked as reference, not Phase 5 scope.
- Typed errors reuse the Phase 1 upload taxonomy plus Drive-specific codes: `unsupported_type` / `too_large` / `empty_file` / `not_found` / `access_denied` / `download_failed` / `file_not_available` / `download_not_allowed` / `workspace_export_required`.
- On success: ingest via the same `data_loader` path as local upload → set the active `DatasetContext` with `source: "drive"` and the server-fetched filename → clear derived state first (same semantics as a fresh local upload). Never log file content or full Drive metadata.

### Endpoints

| Endpoint | Method | Contract |
|---|---|---|
| `/api/v1/drive/download` | POST | `{ request_id, file_id }` (canonical, locked) → `{ dataset }` (same wrapper shape as local upload); `request_id` must match the active server/session picker request (stale/duplicate → typed non-retryable error); **only `file_id`** is used for Drive metadata/download authority — client filename/MIME/size ignored; errors typed identically. |
| `/api/v1/drive/status` | GET | `{ configured: bool }` — reconnect affordance state. |
| `/api/v1/drive/picker-token` | POST | **Only if Picker iframe (D1)** — JIT, browser-memory-only (see Task 4): `{ access_token, expires_at?, app_id }`; `Cache-Control: no-store` + `Pragma: no-cache`; CSRF/origin enforced; never revoked on Picker close; document Cloud Resource Manager API enablement; API key HTTP-referrer restricted. |
| `/api/v1/drive/list` | GET | **Only if slide-out (D1)** — see Task 4. |

---

## Task 3 — GA4 pull (contract-provenanced DatasetContext)

**File:** `api/routes/ga4.py` (+ `api/services/ga4_service.py::pull_report`).

### Server-owned request builder (browser never sends metrics/dimensions)

- Property is **server-resolved** from the authenticated GA4 connection (stored on the session in Task 1). The browser payload is just `POST /api/v1/ga4/pull` — **no client-supplied metrics, dimensions, or date ranges**.
- First-pull report (D3 locked fallback): `date_ranges=[90daysAgo → yesterday]` (trailing 90 complete days), `dimensions=[date]`, `metrics=CANONICAL_GA4_METRICS`, `order_bys=[date ascending]`, `limit=10_000`, `offset`, `return_property_quota=True`.
- Canonical metric allowlist: `sessions` · `totalUsers` · `engagedSessions` · `engagementRate` · `bounceRate`. Substitute only with measurement-contract approval (Task 0 rules); never silently synthesize.

### 90-row reality → pagination proven in mocks

- Metrics are **columns** in a `runReport` response; `date` is the row dimension. Five metrics × 90 days ≈ **90 rows** — the production vertical-slice report will not exercise live pagination.
- **Still implement the generic offset loop** (needed for later report shapes): page size 10,000 (API supports up to 250,000 rows/request); accumulate `rows`, capture `row_count` from the first page, keep the last `property_quota` snapshot; break when a page is empty or `len(rows) >= row_count`; advance `offset += len(page_rows)`.
- **Do not add a high-cardinality dimension** (channel, page path) merely to force live pagination — pagination is proven in mocked contract tests (Task 6). `date + sessionDefaultChannelGroup` is a **Phase 5.1 candidate** only after the property probe confirms availability and the measurement contract decides channel-level aggregation.
- Throttle for the **10 concurrent requests/property (Standard; 50 for 360)** quota; account for token budgets (200k/day + 40k/hr per property) and the 120 thresholded-requests/hr cap.

### Provenance (safe aggregate record)

```json
{ "source": "ga4", "property_id": "123456789", "dimensions": ["date"],
  "metrics": ["sessions", "totalUsers", "engagedSessions", "engagementRate", "bounceRate"],
  "start_date": "...", "end_date": "...", "page_count": 1, "row_count": 90,
  "pulled_at": "...", "quota_observed": true }
```

Provider tokens, raw OAuth metadata, and user identifiers never enter provenance.

### Quota handling (record-only, typed on failure)

- `return_property_quota=True`; **record quota only from successful responses** — a subsequent `ResourceExhausted` failure is not guaranteed to carry a fresh quota object, so retain the last successful snapshot for diagnostics.
- Snapshot: `tokens_per_day` / `tokens_per_hour` / `concurrent_requests` / `server_errors_per_project_per_hour` (each with `consumed`/`remaining`), plus `captured_at`.
- Quota data is an **operational/provenance record, not a user-facing "traffic light"**; never infer a billing tier from a value; never log tokens or raw rows alongside quota metadata.
- `ResourceExhausted` → typed **non-retryable** `ga4_quota_exhausted` (429). **No retry loop on quota exhaustion** — repeated server errors are themselves quota-limited, so aggressive retries are counterproductive.

### Typed error taxonomy (locked)

| GA4/provider condition | Public result | Retry? |
|---|---|---|
| Invalid metric/dimension/date request | `ga4_invalid_report` / 422 | No |
| No GA4 connection established | `ga4_connection_required` / 409 | No — connect first |
| Stored credentials invalid/expired | `ga4_reconnect_required` / 401 | No — reconnect |
| Permission denied for property | `ga4_access_denied` / 403 | No |
| Property not found/unavailable | `ga4_property_unavailable` / 404 | No |
| Rate-limited temporarily | `ga4_rate_limited` / 429 | At most one pre-response retry |
| Property/project quota exhausted | `ga4_quota_exhausted` / 429 | **No** |
| Google 500/503 or network interruption | `ga4_provider_unavailable` / 503 | At most one retry |
| Client/provider deadline exceeded | `ga4_timeout` / 504 | Usually no automatic retry |

Retry only clearly transient transport/provider failures; never authorization, invalid-request, property-access, or exhausted-quota failures. Preserve diagnostic data safely: property ID, allowlist metric/dimension names, date range, page/row counts, provider quota snapshot, typed failure class, request duration, retry count — never raw tokens, headers, complete provider errors, or raw report rows.

### Output

- Output is a **`DatasetContext`** (Phase 3 shape) whose `metrics` carry measurement-contract provenance: `contract_row`, `validation_status`. Rows 3–5 of the contract stay `unavailable` until event-level access exists (aggregate-only reality) — **unavailable never renders as numeric evidence**; provisional metrics carry explicit caveats (metric-status consumption policy, master-plan §11-B).
- Dimension/metric combos + thresholding follow the Task 0 research evidence; the compatibility-probe checklist determines what the *target property* actually supports (D3; **fallback locked: five canonical metrics × `date`, daily grain, trailing 90 complete days**).
- Request-size guard: cap dimensions per request at the verified limit (open decision #7: 9 dims / 10 metrics, 7 for funnel — re-verified in Task 0).

---

## Task 4 — Drive browse path (D1: Picker first, slide-out follow-up)

**Task 4 builds the Picker iframe path (D1). The slide-out `drive/list` path below stays specified as the follow-up swap — same `download` trust boundary, no ingestion change.**

**Slide-out (follow-up, D1):**
- `GET /api/v1/drive/list?q=&folder_id=&page_token=` backed by `utils/drive_client.py` metadata calls.
- Server `files.list` query: `trashed = false AND (name contains '<term>' OR '<folder_id>' in parents)`, `orderBy: folder,modifiedTime desc`, fields `id,name,mimeType,modifiedTime,size,webViewLink,iconLink`.
- Response `{ state, message?, setupHint?, files: [...], next_page_token }` — **`next_page_token` required** (opaque string or null); a folder larger than the page **must paginate, not silently truncate**; React sheet adds a "Load more" affordance.
- States `ready|not_configured|permission|error` (`not_configured` → no credentials; 401/403 → `permission` → reconnect + `drive.readonly` — **deferred slide-out path only; never requested by the Picker-first slice**; else `error`).
- Shared-drive support only if Task 0 research + D1 scope include it (`supportsAllDrives`, `includeItemsFromAllDrives`, `corpora`).

**Picker iframe (D1 → picker):**
- `POST /api/v1/drive/picker-token` → `{ access_token, expires_at?, app_id }` (project number); port the existing `drive_picker_component_frontend/` component behavior into the native React shell (Task 5) with `setAppId` + referrer-restricted API key.

**Picker token security (JIT, browser-memory-only):**
- **Just-in-time issuance:** the frontend calls `/drive/picker-token` immediately before opening Picker and passes the token to Google Picker via `setOAuthToken`. Return the **currently valid** access token + its real `expires_at` when available — the server generally cannot mint an arbitrary 5-minute token on demand.
- Response headers `Cache-Control: no-store` + `Pragma: no-cache`; CSRF/origin enforcement (POST, unsafe method); **one active picker request ID at a time**.
- **Browser may temporarily receive:** short-lived Drive access token, Cloud project/app ID, expiry metadata. **Browser must never receive:** refresh token, client secret, the stored GA4/Drive connection record, or the app session ID beyond its HttpOnly cookie.
- Token lives only in a local component variable → `setOAuthToken`; cleared on select/cancel/error. **Forbidden:** store/Zustand persistence, localStorage/sessionStorage, URL/search params, logs/telemetry/analytics, error reports, fixtures/screenshots/test snapshots, backend response caching.
- **Do NOT revoke the token when Picker closes** — if it came from the stored Google grant, revocation can invalidate the grant/refresh-token relationship and disconnect the user. Browser-memory cleanup + just-in-time issuance + narrow scope + strong CSP + XSS prevention are the correct controls.
- Server retains: refresh token, client secret, connection record, token refresh, download authority, session identity.
- Selection → `POST /api/v1/drive/download` with `{ request_id, file_id }` (same trust boundary as Task 2).

**Selection contract (canonical):**

```json
{ "request_id": "picker-request-uuid", "file_id": "google-drive-file-id" }
```

- `request_id` must match the active server/session picker request; stale or duplicate → typed non-retryable error (a second selection can never replace the active dataset).
- Only `file_id` is used for Drive metadata/download authority; client filename, MIME type, and byte size are ignored.
- **Sheets in the Picker UI:** initially filter to CSV/XLS/XLSX where possible, or visibly label Google Sheets as "not yet supported" — users must not select a Sheet only to discover `workspace_export_required` at the API boundary.

**Either path:** **Import is the real integration seam** — the prototype's Import button only calls `loadData("drive · <name>")`; the port wires Import → `POST /api/v1/drive/download` → `data_loader` → dataset (master-plan §9; archive §4.17).

---

## Task 5 — React UI (Phase 4 shell wiring)

- **`/auth/ga4/callback`** — already scaffolded in Phase 4 (`routes/auth/ga4/callback.tsx` with `validateSearch`); wire the store's `handleGA4Callback` stub to it: on `status=success` → refresh session + optionally auto-pull; on `cancelled` → neutral state; on `error&reason=<code>` → safe message keyed by code (no raw provider text).
- **Connect affordances:** sidebar/topbar buttons calling `connectGA4()` / `connectDrive()` (store stubs already exist) → `POST /api/v1/ga4/connect` returns `authorization_url` → `window.location.assign(url)`; disabled/hidden when `status` says not-configured per D5 placement.
- **Drive action states (D5):** no dataset → `Upload File` + `Import from Drive`; dataset loaded → `Replace Dataset` + `Import from Drive` + `Clear Data`. First interaction: disconnected → explain scope → Connect Drive; connected → open Picker; picker cancelled → return to prior sidebar state; file selected → server-side download + normal ingest flow. No persistent files-list UI in the first Phase 5 PR (deferred with the slide-out).
- **Drive sheet / picker component** per D1: native React component (never an embedded Streamlit component); `initial_mount` classification from `UI-CAPTURE-8b4b7b9/MANIFEST.md`.
- **Pull flow:** after GA4 connects, a "Load GA4 data" action → `POST /api/v1/ga4/pull` → dataset context → existing preview/quality/scorecard render (Phase 4 components reused; no new chart contract).
- **Store:** replace Phase 4 stubs (`connectGA4`, `handleGA4Callback`, `connectDrive`, `downloadFromDrive`) with real `api.ts` calls — the drift-matrix union members are already present; **no new store members required** (drift row 13 satisfied).
- **Errors:** typed error map extension in `api.ts` for `ga4_*` / `drive_*` codes; `mapApiError` covers new statuses.

---

## Task 6 — Contract tests + Drive E2E matrix

**Contract tests (`tests/api/`):**
- GA4: connect returns `{ authorization_url }` with PKCE params; callback invalid/expired/replayed state → typed 400; transaction-cookie mismatch → 400; exchange failure → `token_exchange_failed`; success rotates session; disconnect revokes; status reflects connection; metric-status provenance (`contract_row`/`validation_status`) present; unavailable rows never numeric.
- GA4 pull — **pagination proven via mocks** (production ≈ 90 rows; no high-cardinality dimension added to force paging): `rowCount=90` → one page; `rowCount=20,001` → pages 10,000 + 10,000 + 1; empty report → no rows + valid provenance + `page_count=1`; second request `offset` = first page row count; no duplicate rows; final partial page handled.
- GA4 pull — quota/errors: quota snapshot recorded from **successful** responses only (last successful snapshot retained); `ResourceExhausted` → typed **non-retryable** `ga4_quota_exhausted` with **no retry loop**; `ServiceUnavailable`/`InternalServerError` → at most one retry → `ga4_provider_unavailable`; `DeadlineExceeded` → `ga4_timeout`; invalid request → `ga4_invalid_report`; provenance `page_count`/`row_count`/`quota_observed` present; no tokens/raw rows logged with quota.
- Drive: picker-token is JIT — `no-store`/`no-cache` headers, CSRF enforced, `expires_at` when available, token never revoked on close; **no Drive upload endpoints exist in Phase 5** (boundary test); `download` with forged filename/MIME/size metadata → server metadata wins; `trashed` → `file_not_available`; `canDownload=false` → `download_not_allowed`; MIME/suffix reject (`unsupported_type`); size caps (`too_large` — declared preflight **and** actual-byte counter during transfer); Google-native file → `workspace_export_required`; empty file; not-found; access-denied; success sets `source: "drive"` + server-fetched filename; temp artifact deleted in `finally` (no orphans); Clear Data removes drive-derived state but keeps OAuth connection. **Runtime additions:** **duplicate/stale picker `request_id`** → second selection cannot replace the active dataset (typed non-retryable error; old dataset preserved); **picker-token non-persistence** → `no-store`/`no-cache` headers asserted, token never enters session metadata, logs, usage ledger, or API fixture output; **cancellation during Drive transfer** → temp artifact deleted and the prior dataset remains active.
- Guard: `tests/test_credential_guard.py` allowlist additions for `GA4_*`/`DRIVE_*` env vars.

**Drive E2E acceptance matrix (Playwright, master-plan §9):**

| # | Case | Expected |
|---|---|---|
| 1 | User cancels Google OAuth | Callback receives `status=cancelled`; safe cancelled state; no partial session state |
| 2 | Drive not configured | Sheet state `not_configured` with setup hint; no crash |
| 3 | Drive permission expired | State `permission` → reconnect flow re-requests `drive.file` (Picker-first slice) |
| 4 | Unsupported file selected | Typed `unsupported_type` matching the upload taxonomy |
| 5 | Client sends forged filename/MIME/size metadata | Backend re-fetches Drive metadata and rejects on mismatch |
| 6 | Backend authority on metadata | `file_id` is the only authority input (`request_id` is the picker-freshness binding); server `files.get` decides |
| 7 | Binary CSV/XLSX import | Downloads server-side, parses, creates the active dataset |
| 8 | Google-native Sheet | Phase 5: typed `workspace_export_required` (export contract deferred; the 10 MB export cap applies to the future branch) |
| 9 | Size limit enforcement | 100 MB ingestion policy enforced server-side |
| 10 | Download → preview/quality | Parsed dataset becomes active; preview + quality render |
| 11 | Clear Data | Removes active dataset + derived state; OAuth connection retained |
| 12 | Token containment | Browser never receives the Drive/GA4 access token (network logs + credential guard) |

GA4 E2E: connect → pull → preview success path plus the OAuth error/cancel path (row 1). This matrix turns the "Import only fakes `loadData`" discovery into a permanent regression barrier.

**Live opt-in smoke (D4, never CI):** local-key run against the owner-provided **non-client test GA4 property + dedicated Drive account** (synthetic/non-client traffic and fixtures only); explicit opt-in flag (`E2E_REAL_GOOGLE=1`); headed/local-only auth setup; no tokens, cookies, property IDs, emails, file IDs, or raw response bodies committed — record a sanitized compatibility checklist, not credentials. Coverage:
1. GA4 consent succeeds with `analytics.readonly`.
2. Correct property can be selected/resolved.
3. Metrics × `date` report succeeds.
4. Pagination + provenance fields recorded.
5. Drive consent succeeds with `drive.file`.
6. Picker opens and returns selected file metadata.
7. Download/parse/quality pipeline succeeds.
8. Clear Data removes dataset-derived state but retains OAuth connections.
9. Disconnect/revoke behavior verified.
Skipped when no credentials are provided — contract tests close code correctness, but the property probe stays **explicitly pending** (never falsely closed).

---

## Task 7 — CI + security gate additions

- `.github/workflows/test.yml`: extend the credential guard invocation to `api/services/ga4_service.py` + `api/routes/ga4.py` + `api/routes/drive.py` (already a global scan — confirm no committed `GA4_*`/`DRIVE_*` values).
- Contract-test job unchanged (already runs `tests/api/`); E2E matrix runs only with opt-in credentials (`GA4_E2E_ENABLED=true` guard — never in default CI).
- `.env.example`: add `GA4_CLIENT_ID`, `GA4_CLIENT_SECRET`, `GA4_REDIRECT_URI`, `GA4_ENABLED`, `DRIVE_ENABLED` placeholders + comments (no values).

---

## Exit criteria

- [ ] GA4 connect/callback/pull contract tests green (incl. cancel, invalid-state, replay, exchange-failure); PKCE enforced; tokens server-side only.
- [ ] Drive download contract tests green (forged metadata rejection, size/MIME caps, Sheets export); Drive E2E matrix green (with opt-in credentials) or documented as skipped + manually verified.
- [ ] Metric-status policy enforced on every GA4 response (provisional caveated; unavailable never numeric evidence).
- [ ] React: GA4 callback + connect/pull + Drive UI mounted per D1/D5; no new store members; no provider token in browser storage/URLs/logs.
- [ ] Credential guard green with the `GA4_*`/`DRIVE_*` allowlist; hooks green.
- [ ] Task 0 evidence + post-OAuth probe recorded (or explicitly deferred under D4).

## Gate table — Phase 5 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 5 — GA4 + Drive | GA4 + Drive contract tests green · Drive E2E matrix green (or documented opt-in) · Task 0 evidence recorded · no provider token reaches the browser | Implementation agent + reviewer | Record evidence; flip `specs/README.md`; expand `phase-6-cutover-hosting.md` to ACTIVE after the Cloud Run research gate |

---

## Parked/absorbed content (from F4)

- **F4 §8** `ga4_service.py` (`begin_oauth`/`exchange_code` — PKCE additions per F4's Research Fold-In Cross-Check item 1) + `ga4.py` routes (callback status vocabulary locked: `status=success` · `status=cancelled` · `status=error&reason=<code>`; `provider_denied`/`invalid_oauth_state` are superseded spellings).
- **F4 §11** React callback route (typed `validateSearch`, `errorComponent` for `VALIDATE_SEARCH`) — scaffolded in Phase 4, wired in Task 5.
- **F4 Reconciliation Addendum 2 item 2** — GA4 measurement-contract mapping for `POST /api/v1/ga4/pull`.
- **OAuth transaction flow (owner guidance 2026-08-06):** Authorization Code + PKCE S256. `POST /api/v1/ga4/connect` creates cryptographically random `state` + PKCE verifier, stores a short-lived transaction record keyed `ie:oauth:state:<sha256(state)>` (10-minute TTL, `NX`), sets an HttpOnly transaction cookie binding the browser to the transaction, then 302s to Google. `GET /api/v1/ga4/callback` consumes the record **exactly once** (Redis `GETDEL`, or the Lua fallback above), verifies the transaction cookie with `compare_digest`, exchanges the code with the stored verifier + the single allowlisted redirect URI, persists encrypted provider tokens server-side, rotates the app session ID, clears the transaction cookie, and 303s to `/auth/ga4/callback?status=success`. Never put the PKCE verifier, state record, Google token, or client secret in React or browser storage.

  OAuth rules: state + verifier from cryptographic randomness · PKCE S256 (never plain) · state TTL ≈ 10 min · one-time consumption (no replay) · callback bound to the short-lived transaction cookie · one allowlisted Google redirect URI · allowlisted relative return paths · provider tokens stored server-side + encrypted · app session rotated after OAuth completes.
