# Phase 5 — GA4 OAuth + Drive Picker (outline — stub)

> ⚪ **STUB** — Phase 5 gate closed. **Research gates must run before this stub is expanded** (see below). No code is written from this file yet.
> **This file is the tactical authority for F4's GA4 sections** (F4 §8 OAuth endpoints + §11 React callback — **superseded for execution**, parked here).

## Purpose

GA4 OAuth (connect/callback/pull) and Drive import. Both flows terminate server-side: Google redirects to **FastAPI** (`/api/v1/ga4/callback`), FastAPI validates PKCE/state and exchanges the code, then redirects the browser to React with only a safe `status`/`reason`. The browser never receives a provider token. Drive ingestion uses the existing hardened Python client (`utils/drive_client.py` — `download_drive_file` is ported/adapted, **not redesigned**).

## Inputs / source documents

- master-plan §9 (Phase 5), §11-A (state placement: ephemeral store for OAuth state/PKCE before this phase), §13 (open decisions #7 GA4 limits, #9 Drive browse UX), §14 (release gates — GA4 + Drive user flows)
- **Parked from F4:** §8 `api/services/ga4_service.py` + `api/routes/ga4.py` (with the PKCE corrections from F4's Research Fold-In Cross-Check), §11 React callback route
- `utils/ga4_client.py`, `utils/drive_client.py` (3-layer size validation, server metadata authority, MIME allowlist, Sheets export path, typed errors — the canonical Drive trust boundary)
- `plans/ga4-measurement-contract.md` — metric-status policy; `POST /api/v1/ga4/pull` returns a `DatasetContext` whose `metrics` carry contract provenance (`contract_row`, `validation_status`); rows 3–5 stay `unavailable` until event-level access exists (aggregate-only reality)
- `../policies/data-retention-policy.md` §2/§5 — 100 MB server-side ingestion subject to metadata/streaming/MIME/decompression/row/column/temp-file limits
- `../whisperer-30-reference/LOVABLE-UPDATES-080525.md` + `../whisperer-30-reference/LOVABLE-ACTIONS-080526.txt` — drive-list contract shape; **Import gotcha**: the prototype's Import only fakes `loadData("drive · <name>")` — the port must wire download → ingest → quality

## Tracks consumed

- **A** (state/session): shared ephemeral store for OAuth state/PKCE — in-memory is insufficient here (state placement, master-plan §5); proven in staging before OAuth work.
- **B** (API/contract): `/api/v1/ga4/*` + `/api/v1/drive/*` schemas; callback status vocabulary locked (`success` / `cancelled` / `error&reason=<code>`).
- **C** (tests): GA4 + Drive contract tests; Drive E2E acceptance matrix in Playwright.
- **D** (security/credentials): provider tokens never reach the browser; least-privilege scopes; Picker key referrer-restricted.
- **F** (retention/AI boundary): 100 MB server-side ingestion subject to metadata/streaming/MIME/decompression/row/column/temp-file limits (`../policies/data-retention-policy.md` §2/§5).
- **G** (research discipline): GA4 feasibility + selected Drive-UX research gates run before this stub expands.

## Research gates — REQUIRED before expansion (dispatch both, in order)

1. **GA4 feasibility** (archive §3.12, prompt 1): `runReport`/`runFunnelReport`/`getMetadata`/`checkCompatibility` compatibility; page-path × device-category engagement; questionnaire events; dimension/metric combos + thresholding; pagination/quota/retry/`returnPropertyQuota`. **Critical distinction:** separate official-documentation facts from **property-specific facts requiring a post-OAuth compatibility probe** — documentation-only research is never proof the target property supports the report. Live-verify open decision #7 (9 dims / 10 metrics, 7 for funnel).
2. **Drive browse-UX research** — only for the chosen path (open decision #9): **Picker iframe** (project number, referrer-restricted API key, scopes, `POST /api/v1/drive/picker-token` returning `{ token, appId }`) **or** slide-out browser (`files.list` pagination via `pageToken`/`nextPageToken`, shared-drive flags `supportsAllDrives`/`includeItemsFromAllDrives`/`corpora`, required scopes, native-Sheets export). Picker iframe is the recommended default; both terminate at the same `POST /api/v1/drive/download`.

## Task outline (expand before execution)

- [ ] OAuth adapters (F4 §8 parked) made production-real: PKCE S256 (`code_verifier`/`code_challenge` persisted on the session), `state` + `compare_digest`, one-time use + short expiry, allowed-host redirect config (local/staging/prod URIs — never derived from request headers).
- [ ] `POST /api/v1/ga4/connect` → `{ authorization_url }`; `GET /api/v1/ga4/callback` → redirect to React with canonical statuses (`success` / `cancelled` / `error&reason=invalid_state|token_exchange_failed`).
- [ ] `POST /api/v1/ga4/pull` → `DatasetContext` with contract-provenanced metrics; quota observability (`returnPropertyQuota: true`); **documentation-facts vs property-probe separation** recorded in the spec when expanded.
- [ ] Drive: `POST /api/v1/drive/picker-token` (or `GET /api/v1/drive/list` if slide-out chosen) + `POST /api/v1/drive/download` — `file_id` is the only trusted client input; server re-fetches metadata, enforces MIME allowlist + `MAX_INGEST_BYTES` (100 MB) + post-download decompression/row/column/temp-file limits; Sheets follow the export path (10 MB Google export cap); typed errors identical to the local upload path.
- [ ] React GA4 callback route (F4 §11 parked) with typed search params; Drive UI per chosen UX (`initial_mount` status updates in the manifest).
- [ ] **Drive E2E acceptance matrix** (master-plan §9): cancel OAuth · Drive not configured · expired permission · unsupported file · forged filename/MIME/size rejected · binary CSV/XLSX import · Sheets export cap · server-enforced size limit · download→parse→quality · Clear Data removes derived state · browser never receives Drive token.

## Exit criteria

- [ ] GA4 connect/callback/pull contract tests green (incl. cancel, invalid-state, exchange-failure); PKCE enforced.
- [ ] Drive download contract tests green (forged metadata rejection, size/MIME caps, Sheets export); Drive E2E matrix green in Playwright.
- [ ] Metric-status policy enforced on every GA4 response (provisional caveated; unavailable never numeric evidence).
- [ ] Shared ephemeral OAuth/session store proven in staging before this phase's OAuth work (state placement, master-plan §5) — in-memory is insufficient here.

## Gate table — Phase 5 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 5 — GA4 + Drive | GA4 + Drive contract tests green · Drive E2E matrix green · shared store proven · no provider token reaches the browser | Implementation agent + reviewer | Record evidence; flip `specs/README.md`; expand `phase-6-cutover-hosting.md` to ACTIVE after the Cloud Run research gate |

## Parked/absorbed content (from F4)

- **F4 §8** `ga4_service.py` (`begin_oauth`/`exchange_code` — PKCE additions per F4's Research Fold-In Cross-Check item 1) + `ga4.py` routes (callback status vocabulary locked: `status=success` · `status=cancelled` · `status=error&reason=<code>`; `provider_denied`/`invalid_oauth_state` are superseded spellings).
- **F4 §11** React callback route (typed `validateSearch`, `errorComponent` for `VALIDATE_SEARCH`).
- **F4 Reconciliation Addendum 2 item 2** — GA4 measurement-contract mapping for `POST /api/v1/ga4/pull`.
- **OAuth transaction flow (owner guidance 2026-08-06 — ready for the expansion; the Redis
  store is Phase 6 infra — an in-memory ephemeral store remains acceptable through Phase 5 per
  master-plan §9):** Authorization Code + PKCE S256. `POST /api/v1/ga4/connect` creates
  cryptographically random `state` + PKCE verifier, stores a short-lived transaction record
  keyed `ie:oauth:state:<sha256(state)>` (10-minute TTL, `NX`), sets an HttpOnly transaction
  cookie binding the browser to the transaction, then 302s to Google. `GET /api/v1/ga4/callback`
  consumes the record **exactly once** (Redis `GETDEL`, or the Lua fallback below), verifies the
  transaction cookie with `compare_digest`, exchanges the code with the stored verifier + the
  single allowlisted redirect URI, persists encrypted provider tokens server-side, rotates the
  app session ID, clears the transaction cookie, and 303s to `/auth/ga4/callback?status=success`.
  Never put the PKCE verifier, state record, Google token, or client secret in React or browser
  storage.

  ```python
  CONSUME_STATE = """
  local value = redis.call("GET", KEYS[1])
  if value then redis.call("DEL", KEYS[1]) end
  return value
  """
  ```

  OAuth rules: state + verifier from cryptographic randomness · PKCE S256 (never plain) · state
  TTL ≈ 10 min · one-time consumption (no replay) · callback bound to the short-lived
  transaction cookie · one allowlisted Google redirect URI · allowlisted relative return paths ·
  provider tokens stored server-side + encrypted · app session rotated after OAuth completes.
