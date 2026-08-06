# Session-State Key Inventory
## `st.session_state` → FastAPI server session + React store (key → owner → lifecycle → replacement)

**Date:** 2026-08-05
**Method:** mechanical extraction across `app.py`, `utils/`, `components/`, `pages/` (15 source files, 44 distinct keys), then hand-classified by owner and lifecycle.
**Purpose:** Batch 3 Review Addendum identified `st.session_state` as "the largest hidden migration cost." This inventory is the written record that review recommended *before* any code changes: every key, its owner, its lifecycle, and its replacement in the server-owned session model (browser holds only an opaque `HttpOnly` cookie; FastAPI owns dataset refs, OAuth credentials, filter/metric/chat state; React owns only view-model state).

> Companion docs: plan Batch 3 Review Addendum items 3–5 (server session, contract discipline, four-layer tests); `../specs/phase-1-api-react-callback-tests-implementation.md` §4 (AppSession fields) and §6 (DatasetStore); `../specs/freebuff-prompt-wire-react-store.md` Batch 3 Addendum (view-model only, `credentials: "include"`).

---

## 1. Dataset & analysis state (largest group)

Replacement pattern: the **server owns the dataset** (`AppSession.dataset_id` → `DatasetStore` holding the dataframe + context, F4 §4/§6). The React store keeps a lightweight view-model (`source`, `loadState`, `error`, `filters`, `metrics`).

| Key | Owner(s) | Lifecycle | Replacement |
|---|---|---|---|
| `data_context` | `app.py`, `utils/session.py`, `components/{sidebar,data_preview,__init__}.py`, `pages/learn.py` (+ tests) | Dataset-scoped; set on upload/GA4/Drive import, cleared by `clear_data()` | Server: `AppSession.dataset_id` + `DatasetStore`; wire: `DatasetContext` (F4 §5); React: `source` in store |
| `df` | `utils/data_loader.py:386`, tests | Dataset-scoped; raw frame held for analysis | Server-only: `StoredDataset.dataframe`; **never** shipped to the client (rows go out via `/data/preview`) |
| `data_source` | `app.py`, `utils/session.py`, `components/{sidebar,chat}.py` | Dataset-scoped | `DatasetContext.source` (`"upload" \| "ga4" \| "drive"`) |
| `data_cleared` | `app.py`, `utils/session.py`, `components/sidebar.py` | Flag flipped on clear | Server: no dataset → `409/410` on data endpoints; React: `loadState = "idle"` |
| `stats` | `app.py`, `utils/session.py`, `components/{sidebar,data_preview,summary,chat}.py` | Dataset-scoped; computed summary stats | Compute server-side per request (or cache in session `metadata`); expose via context/preview |
| `summary` | `app.py`, `utils/session.py`, `components/{sidebar,summary,chat}.py` | Dataset-scoped AI summary text | React store `summary` + `summaryState` (chat `mode: "summary"` or `GET /api/analysis/summary`) |
| `quality_report` | `app.py`, `utils/session.py`, `components/{sidebar,data_preview}.py` | Dataset-scoped | `GET /api/data/quality` response |
| `missing_columns` | `app.py`, `utils/session.py`, `components/sidebar.py` | Set at import time (warning list) | `DatasetContext.provenance` / quality warnings |
| `last_file_id` | `app.py`, `utils/session.py`, `components/sidebar.py` | Dataset-scoped; last imported file id | `DatasetContext.provenance`; Drive `fileId` stays server-side only |
| `custom_metrics` | `app.py`, `utils/session.py`, `components/sidebar.py` | Session-scoped; user-defined metrics | Server session `metrics`; React store `metrics` (view-model) |
| `filter_columns` / `filter_dates` | `components/data_preview.py` | UI-scoped filter state | React store `filters`; server session `dataset.filters` for analysis queries |
| `funnel_data` / `funnel_steps` / `funnel_new_step` | `utils/session.py`, `components/{data_preview,sidebar}.py` | Dataset-scoped funnel state | `GET /api/analysis/funnel` (scope: template funnels only — see plan Phase 3 amendment) |
| `ga4_truncated` | tests only | — | Server-side pagination metadata (`returnPropertyQuota`, 10k-row pages — plan Phase 5 amendment 3) |

## 2. GA4 credentials & comparison state

Replacement pattern: **credentials never leave the server** (`AppSession.ga4_credentials`); comparison/segmentation is view-model + server session filters.

| Key | Owner(s) | Lifecycle | Replacement |
|---|---|---|---|
| `ga4_creds` | `app.py`, `components/{sidebar,__init__}.py` | **Sensitive.** Session-scoped OAuth credentials | Server-only: `AppSession.ga4_credentials` (F4 §4). No React visibility — tokens never reach the client (F4 §8 correction) |
| `ga4_property_id` | `app.py`, `components/sidebar.py` | Session-scoped selection | Server session metadata; sent to `POST /api/ga4/pull` only |
| `compare_mode` / `compare_dimension` / `compare_val_a` / `compare_val_b` | `app.py`, `components/chat.py` | UI-scoped compare-analysis state | React store view-model; server session filters for the comparison query |

## 3. Drive Picker (transient flow state)

Replacement pattern: React-side dialog/flow state + one server flag for the import-in-progress dismissal lock (interstitial dialog design carried the same flag).

| Key | Owner(s) | Lifecycle | Replacement |
|---|---|---|---|
| `drive_picker_active` | `components/sidebar.py` | Transient; true while Picker dialog open | React dialog open state (native React Picker component, Phase 5) |
| `drive_picker_importing` | `components/sidebar.py` | Transient; true during download+parse | React loading state; server-side flag for dismissal lock + idempotency (duplicate-click guard) |
| `drive_picker_just_imported` | `components/sidebar.py` | Transient; success toast/button relabel | React toast/sonner state after import |
| `drive_picker_request_id` | `components/sidebar.py` | Transient; stable component key across reruns | React key / request id — no server equivalent needed |

## 4. Chat / Gemini / AI instrumentation

Replacement pattern: chat transcript is React view-model + server session (for context assembly); instrumentation moves to server-side metrics/observability (Batch 3: structured logs, request IDs, rate limits).

| Key | Owner(s) | Lifecycle | Replacement |
|---|---|---|---|
| `chat_history` | `app.py`, `utils/session.py`, `components/{sidebar,chat}.py` | Session-scoped transcript | React store `chat`; server session keeps context for prompt assembly (`POST /api/chat`) |
| `selected_model` | `app.py`, `components/sidebar.py` | Session-scoped preference | Server session metadata (per-user quota accounting lives server-side) |
| `last_api_call` | `app.py`, `components/chat.py` | Transient diagnostic | Server-side structured logs + request IDs |
| `api_attempt_count` / `api_failure_count` / `api_success_count` | `components/chat.py` | Session counters | Server-side metrics endpoint; do not expose raw failure internals |
| `api_key_valid` / `api_key_error` | `app.py` | Startup credential check | `scripts/check_credentials.py` + pre-commit guard (Batch 3: keep enforced for FastAPI env vars) |
| `total_input_tokens` / `total_output_tokens` / `total_thought_tokens` / `total_cached_tokens` / `total_tokens_used` | `app.py` | Session usage counters | Server-side per-session usage ledger (observability + per-user Gemini quotas) |

## 5. Theme / UI preferences

| Key | Owner(s) | Lifecycle | Replacement |
|---|---|---|---|
| `theme` | `app.py`, `components/sidebar.py` (+ tests) | Persistent preference across reruns | React `useTheme()` — the captured store already persists `ie-theme` in localStorage; a **UI preference, not data**, so it's acceptable under the server-session rule |
| `_tour_replay_requested` | `components/hero.py` | Transient onboarding flag | React onboarding state / localStorage UI pref |

## 6. Test-only artifacts (not runtime state)

| Key | Owner(s) | Note |
|---|---|---|
| `key` / `{key}` / `filtered_df` / `df` / `ga4_truncated` (test occurrences) | `tests/test_sidebar.py`, `tests/test_static_analysis.py` | Keys exercised under mocked `session_state` in tests — they are **not** production keys. Retire/replace per the four-layer test matrix (Batch 3 item 5), not as runtime state. |

---

## 7. Summary: where state lands post-migration

| Current owner | Future home |
|---|---|
| Dataset objects, raw frames | Server `DatasetStore` (in-memory now → Redis/Postgres-compatible abstraction, F4 §4) |
| GA4 credentials, Drive file ids, OAuth state | Server `AppSession` (never serialized to React) |
| Filters, metrics, compare state | Server session (authoritative) + React store (view-model) |
| Chat history, summary, quality, funnels | API responses + React store |
| Theme, tour flags | React UI preferences (localStorage acceptable — non-sensitive) |
| Counters, attempt/failure stats | Server observability (logs, metrics, usage ledger) |

**Next step before code:** use this table as the checklist when building `api/dependencies.py` (`AppSession` fields) and the store's `ExplorerValue` interface — every key above should have exactly one destination. Nothing from §1–§5 should be silently dropped during Phase 2's Streamlit-coupling extraction.
