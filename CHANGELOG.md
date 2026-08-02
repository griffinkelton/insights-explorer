# 📝 Changelog — GA4 Insight Explorer

> All notable changes to this project, tracked with commit hashes, dates, and links to related documentation.
>
> Repo: [github.com/griffinkelton/insights-explorer](https://github.com/griffinkelton/insights-explorer)

---

## v0.3.0 — Drive Import Release

**Date:** 2026-08-02 | **Status:** 🚧 Release verification in progress | **Tests:** 663 (non-smoke) + 14 Playwright smoke

### Phase 1: Server-Side Foundation

- `download_drive_file()` — 3-layer size validation, MIME allowlist, server-metadata authority
- `DriveImportError` — 6 typed error codes, catch-all exception hardening, no raw API text exposure
- `PickerSelection` wrapper — structural validation, metadata stripping at component boundary
- Static analysis: token-level AST guard rejects `drive`/`drive.readonly`/`drive.metadata.readonly`

### Phase 2: Provenance & Atomic Ingestion

- `create_context_from_drive()` — content-derived source ID (SHA-256), Drive-specific provenance
- Prepare-then-commit for all three ingestion paths (upload, GA4, Drive)
- `_NamedBytesIO` adapter for parser reuse
- Failure-preservation test matrix (12-field derived-state snapshots)
- Upload replacement failure no longer destroys prior context

### Phase 3.0–3.1: Picker Integration & UX

- Declared Streamlit component (Option B) with bidirectional protocol
- Request-freshness guard, duplicate-emission protection, reset-on-cancel
- Theme synchronization (dark/light propagated to Picker iframe)
- Button states: Ready, Loading, Imported, Retry
- Filename display removed from frontend (server-authoritative metadata only)
- Drive Import section visible only when authenticated + Picker secrets configured

### Phase 3.2: Playwright Smoke Tests

- 3 platform smoke tests (app loads, sidebar visible, no credential leaks)
- 11 drive-import controlled-state tests (visibility, on-demand render, ready/cancel/theme/duplicate/picked-seam)
- Test-mode seam (`DRIVE_PICKER_TEST_MODE=1` + `?picker_seam=` query param)
- No real OAuth, API keys, or Drive files required
- Dedicated Playwright CI job with explicit Chromium install

### Documentation

- README: Drive Import feature entry, scope clarification, supported formats, privacy model, Picker setup
- CHANGELOG: v0.3.0 section
- RELEASE_CHECKLIST: v0.3.0 manual browser matrix
- Spec status updated

### Remaining (manual gate)

- 5-environment browser matrix (Chrome/Safari/Firefox on macOS/Windows)
- Real-account CSV/XLSX/Sheets selection, cancel, second import, theme switching
- Error-path verification (access denied, not found, unsupported type, oversized, empty)
- Sensitive-output leakage check

---

## 2026-08-02 — AI Studio API Key (AQ.) Pattern Added to Credential Guard

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 633

### AI Studio key format (AQ.) added to credential guard — caught after live-key exposure in chat

**Commit:** [`ca87456`](https://github.com/griffinkelton/insights-explorer/commit/ca87456)

| Change | Type | Related Docs |
|---|---|---|
| `scripts/check_credentials.py` — new regex `GOOGLE_AI_STUDIO_KEY = re.compile(r"AQ\.[0-9A-Za-z_-]{30,}")` added to PATTERNS tuple (3 patterns: `AIza`, `AQ.`, `ya29`); docstring updated to mention AI Studio keys and `AQ....` placeholder exemption | Security | [scripts/check_credentials.py](scripts/check_credentials.py) |
| `tests/test_credential_guard.py` — `FAKE_AI_STUDIO_KEY` runtime-built var, new `test_flags_real_ai_studio_key` (asserts hits + correct label), new `test_allows_doc_placeholder_aq_dots` (`AQ....` not flagged) | Testing | [tests/test_credential_guard.py](tests/test_credential_guard.py) |
| Suite: 631 → **633** passed | Testing | [README.md](README.md) |

**Related:** [.pre-commit-config.yaml](.pre-commit-config.yaml), [scripts/check_credentials.py](scripts/check_credentials.py)

---

## 2026-08-02 — v0.3.0 Spec v2.9.0 + GA4 Insights Sketch (Doc-Only)

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 633 (unchanged — docs only)

### Spec refined to v2.9.0 (Phase 2 atomicity, typed errors, multimodal deferral) + GA4 insights engine design sketch created and reframed as trust layer

**Commits:** [`5d06920`](https://github.com/griffinkelton/insights-explorer/commit/5d06920) (spec), [`eb9d33d`](https://github.com/griffinkelton/insights-explorer/commit/eb9d33d) (DOCIDX + closeout), [`b122527`](https://github.com/griffinkelton/insights-explorer/commit/b122527) (sketch v1), [`8b15e5c`](https://github.com/griffinkelton/insights-explorer/commit/8b15e5c) (sketch v2), [`2912950`](https://github.com/griffinkelton/insights-explorer/commit/2912950) (DOCIDX refresh)

| Change | Type | Related Docs |
|---|---|---|
| v0.3.0 spec bumped **v2.8.0 → v2.9.0**: broadened atomicity to all ingestion paths (upload, GA4, Drive), `DriveImportError` + 6 fixed codes, `_NamedBytesIO` adapter for parser reuse, 9→19 Phase 2 tests, step dependency table (2.0/2.1/2.2 parallelism), multimodal/provider abstraction deferred from v0.3.0, Phase 1 goal reworded to past tense | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |
| DOCUMENTATION_INDEX + Phase 1 closeout: all spec rows bumped to v2.9.0 + date 2026-08-02; closeout header + links: v2.2.0 → v2.9.0; cloudbuild + missing-build/ regression evidence added to closeout rows | Docs | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md), [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md) |
| New `plans/🔵 ga4-insights-sketch.md` (v1: 275 lines, v2: 523 lines) — trust-layer design: 5-layer pipeline (sources→normalization→deterministic metrics→insight candidates→Gemini→UI), semantic metric registry, inference labels (Observed/Associated/Hypothesis/Experiment/Not assessable), linkage protocol, data quality gate, 7 equity gaps, survey population separation, structured evidence objects (YAML), prompt injection protection, insights dashboard, operational design, 4-gate phasing (0. Data readiness → 1. GA4 descriptive → 2. Evidence overlay → 3. Outcomes), definition of done (10 questions) | Docs | [plans/🔵 ga4-insights-sketch.md](plans/🔵%20ga4-insights-sketch.md) |
| Cross-refs `evidence-connector-design.md`; sketch is 🔵 aspirational — defers everything to post-v0.3.0 | Docs | [plans/🔵 evidence-connector-design.md](plans/🔵%20evidence-connector-design.md) |
| DOCIDX footer + sketch rows updated to reflect v2 trust-layer reframing (523 lines, 5-layer pipeline, 4-gate phasing) | Docs | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md), [plans/🔵 ga4-insights-sketch.md](plans/🔵%20ga4-insights-sketch.md), [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md)

---

## 2026-08-02 — Closeout Baseline + BytesIO Contract (Doc-Only)

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 633 (unchanged — docs only)

### Closeout current-baseline updated to 633; _NamedBytesIO contract verified in spec

**Commits:** [`5c8838d`](https://github.com/griffinkelton/insights-explorer/commit/5c8838d) (closeout), [`35259eb`](https://github.com/griffinkelton/insights-explorer/commit/35259eb) (spec)

| Change | Type | Related Docs |
|---|---|---|
| Phase 1 closeout audit: two stale values fixed — current repository baseline 631→633 (AI Studio guard +2 at `ca87456`) and CHANGELOG reference refreshed to 633; historical Phase 1 evidence (628 tests, `9754189`) preserved in 3 places | Docs | [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md) |
| v0.3.0 spec §2.3: blockquote added confirming `_NamedBytesIO` BytesIO contract — `data_loader.load_file()` calls `file.read()` + `len()`, never accesses `.size`; `.size` attribute is harmless baggage (verified 2026-08-02) | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |

**Related:** [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md), [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md)

---

## 2026-08-02 — Phase 2.0: DriveImportError + Catch-All Hardening

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 634

### Typed error contract (6 codes) for all download failures + unwrapped Exception mapping

**Commits:** [`8b207c1`](https://github.com/griffinkelton/insights-explorer/commit/8b207c1) (DriveImportError), [`8291692`](https://github.com/griffinkelton/insights-explorer/commit/8291692) (catch-all hardening)

| Change | Type | Related Docs |
|---|---|---|
| New `DriveImportError(RuntimeError)` with `code` + `message` — 6 fixed codes: `not_found`, `access_denied`, `unsupported_type`, `too_large`, `empty_file`, `download_failed` | Feature | [utils/drive_client.py](utils/drive_client.py) |
| All download failures migrated: `ValueError` → `DriveImportError` (unsupported MIME, 3-layer size checks, empty file), `RuntimeError` → `DriveImportError` (404/403/5xx from `_raise_classified_drive_error`), `_BoundedBytesIO.write()` → `DriveImportError` (stream cap) | Refactor | [utils/drive_client.py](utils/drive_client.py) |
| Catch-all `except Exception` wrapper around entire `download_drive_file()` body — unexpected failures (token refresh, service construction, `int(size)` conversion, non-`HttpError` transport) now become `DriveImportError("download_failed", ...)` with `from None` (no traceback exposes raw request/token context) | Security | [utils/drive_client.py](utils/drive_client.py) |
| `DriveImportError` is a `RuntimeError` subclass — backwards-compatible with existing `except RuntimeError` handlers in sidebar/error-boundary | Design | [utils/drive_client.py](utils/drive_client.py) |
| Tests: 18→21 (all 6 `.code` values asserted; new `test_handles_generic_http_error` for `download_failed` via 500; new `test_service_build_failure_maps_to_download_failed` via `ConnectionError`; new `test_non_http_downloader_failure_maps_to_download_failed` via `OSError` + `__cause__ is None`) | Testing | [tests/test_drive_client.py](tests/test_drive_client.py) |
| Suite: 633 → **634** passed | Testing | [tests/test_drive_client.py](tests/test_drive_client.py) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) (v2.9.0 §2.0 DriveImportError prerequisite)

---

## 2026-08-02 — Phase 2.1: create_context_from_drive() — Content-Derived Source ID

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 648

### Drive context factory with content-derived identity + Drive-specific provenance + deep-copy contract

**Commit:** [`dad05d1`](https://github.com/griffinkelton/insights-explorer/commit/dad05d1)

| Change | Type | Related Docs |
|---|---|---|
| New `create_context_from_drive()` in `utils/data_context.py` — follows the exact same pattern as `create_context_from_upload()` but with `drive:` prefix: `source_id = "drive:" + SHA-256(file_bytes)[:24]` (content-derived, same bytes = same Drive identity, distinguishable from `file:` uploads) | Feature | [utils/data_context.py](utils/data_context.py) |
| Deep-copy contract: `raw_df`, `base_df`, `active_df` are all independent `df.copy(deep=True)` — identical to the upload factory | Design | [utils/data_context.py](utils/data_context.py) |
| Provenance: `drive:{server_display_name}` or `drive:unknown` — server-authoritative name, never inferred from bytes | Design | [utils/data_context.py](utils/data_context.py) |
| Validation: `TypeError` for non-DataFrame, `ValueError` for empty/non-bytes — matches the upload factory | Design | [utils/data_context.py](utils/data_context.py) |
| Tests: 98→112 (14 new in `TestCreateContextFromDrive`): content-derived identity, same/different bytes, drive vs upload distinguishability, deep-copy non-mutation, provenance with/without display name, format validation, input validation, truncated default | Testing | [tests/test_data_context.py](tests/test_data_context.py) |
| Suite: 634 → **648** passed | Testing | [tests/test_data_context.py](tests/test_data_context.py) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) (v2.9.0 §2.1 Drive context factory)

---

## 2026-08-02 — Phase 2.2: Atomic Ingestion — Prepare-Then-Commit for All Data Paths

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 648 (no change — behavioral refactor)

### All three ingestion paths (upload, GA4, Drive) now prepare state locally, then commit session state atomically

**Commit:** [`fe39afe`](https://github.com/griffinkelton/insights-explorer/commit/fe39afe)

| Change | Type | Related Docs |
|---|---|---|
| `_populate_data_state()` refactored to prepare-then-commit: all values computed locally (`prepared_df`, `candidate_context`, `candidate_stats`, `candidate_quality`), then all 12 `st.session_state.*` assignments in one atomic block — a factory failure propagates before touching any state | Fix | [components/sidebar.py](components/sidebar.py) |
| Added `"drive"` source branch using `create_context_from_drive(prepared_df, file_bytes, display_name=display_name)` from Phase 2.1 | Feature | [components/sidebar.py](components/sidebar.py) |
| Funnel + forecast derived state cleared in the commit block (previously stale state from old dataset persisted) | Fix | [components/sidebar.py](components/sidebar.py) |
| `_process_uploaded_file()` — removed premature `clear_data()` call before `load_file()`: a malformed replacement upload no longer destroys the prior valid dataset (was: `clear_data()` → `load_file()` → maybe fail; now: `load_file()` → if fails, prior context untouched) | Fix | [components/sidebar.py](components/sidebar.py) |
| Import: `create_context_from_drive` added to sidebar imports for the new drive source branch | Feature | [components/sidebar.py](components/sidebar.py) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) (v2.9.0 §2.2 Atomic ingestion)

---

## 2026-08-02 — Phase 2.3: Drive Ingestion Through _NamedBytesIO + load_file()

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 658

### BytesIO adapter makes Drive-downloaded bytes look like UploadedFile for the existing parser; downloader dependency injection for testability

**Commit:** [`3e7957b`](https://github.com/griffinkelton/insights-explorer/commit/3e7957b)

| Change | Type | Related Docs |
|---|---|---|
| New `_NamedBytesIO(BytesIO)` adapter — provides `.name` (for `file.name.lower()` extension detection) and `.read()` (for `len(file.read())` measurement); `load_file()` never accesses `.size` so the adapter is safe as written | Feature | [components/sidebar.py](components/sidebar.py) |
| New `_ingest_drive_file(downloader, credentials, file_id)` — downloader dependency injection pattern: production supplies `download_drive_file`, tests supply a fake; `Callable[[Credentials, str], tuple[bytes, str]]` typed | Feature | [components/sidebar.py](components/sidebar.py) |
| Error paths preserve prior context: `DriveImportError` → `st.error()` + `return` (zero state mutation); `load_file()` parse failure → `st.error()` + `return` (zero state mutation); warning path (truncated data) → `st.warning()` + continues to populate | Design | [components/sidebar.py](components/sidebar.py) |
| Imports: `BytesIO`, `Callable`, `Credentials`, `DriveImportError`, `download_drive_file` added to sidebar | Feature | [components/sidebar.py](components/sidebar.py) |
| Tests: 7→16 sidebar tests (9 new): `TestNamedBytesIO` (5: interface contract, CSV/XLSX passthrough, `.size` irrelevance) + `TestIngestDriveFile` (4: integration, download failure preservation, parse failure preservation, truncation warning) | Testing | [tests/test_sidebar.py](tests/test_sidebar.py) |
| Suite: 648 → **658** passed | Testing | [tests/test_sidebar.py](tests/test_sidebar.py) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) (v2.9.0 §2.3 Drive loader integration)

---

## 2026-08-02 — Phase 2.4: Failure-Preservation Test Matrix

**Date:** 2026-08-02 | **Status:** ✅ Complete | **Tests:** 664

### 6 tests prove all three ingestion paths preserve prior state on any failure — full 12-field derived-state snapshots

**Commit:** [`08cb2b2`](https://github.com/griffinkelton/insights-explorer/commit/08cb2b2)

| Change | Type | Related Docs |
|---|---|---|
| `TestPhase24FailurePreservation` (4 tests): upload replacement parse failure → all 12 derived-state keys unchanged (last_file_id intentionally updates to prevent re-processing loop); GA4 context factory failure (RuntimeError propagates, zero state mutation); Drive context factory failure (ValueError propagates, zero state mutation); successful commit → every state field replaced (data_context, custom_metrics, stats, missing_columns, quality_report, summary, chat_history, data_source, data_cleared, funnel_steps, funnel_data cleared, forecast_* purged) | Testing | [tests/test_sidebar.py](tests/test_sidebar.py) |
| `TestDriveIngestionEnhanced` (2 tests): Drive download failure (DriveImportError) → full 12-field snapshot comparison; Drive loader failure (load_file error) → full 12-field snapshot comparison — complements the Phase 2.3 tests which only verified `_populate_data_state` was not called | Testing | [tests/test_sidebar.py](tests/test_sidebar.py) |
| `_FakeSessionState(dict)` helper — supports both attribute-style (`st.session_state.key`) and dict-style (`st.session_state["key"]`) access patterns that the production code uses; `_snap_state()` snapshots 11 named keys + all `forecast_*` keys | Testing | [tests/test_sidebar.py](tests/test_sidebar.py) |
| Suite: 658 → **664** passed (16→22 sidebar tests) | Testing | [tests/test_sidebar.py](tests/test_sidebar.py) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) (v2.9.0 §2.4 Failure-preservation tests)

---

## 2026-08-01 — v0.3.0 Regression: Missing-Bundle Failure Mode (build/)

**Date:** 2026-08-01 | **Status:** ✅ Complete | **Tests:** 631

### Test class pins the verified missing-`build/` failure (spec v2.8.0 §3.1)

**Commit:** [`a2a083e`](https://github.com/griffinkelton/insights-explorer/commit/a2a083e)

| Change | Type | Related Docs |
|---|---|---|
| `tests/test_drive_picker_component.py` — new `TestMissingBuildDirectoryFailsLoudly` (3 tests): missing component dir → `StreamlitAPIException: No such component directory` at registration (raise site `LocalComponentRegistry.register_component`, `local_component_registry.py:52`); control test registers normally when the dir exists; exception message carries the absolute missing path | Testing | [tests/test_drive_picker_component.py](tests/test_drive_picker_component.py) |
| CI-safe by design: `tmp_path`-based, never requires `build/` to exist (the Python CI job runs without it); exercises the live-session registration path directly since `declare_component` only registers under a `ScriptRunContext` — bare imports succeed without `build/` | Testing | [tests/test_drive_picker_component.py](tests/test_drive_picker_component.py) |
| Pins the verified 2026-08-02 failure mode (fresh-checkout simulation): a missing `build/` fails the **entire page run** (error banner; nothing after the component renders) — fail-fast by design, so Phase 3 implementers have a test enforcing the spec's claim | Testing | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |
| Suite grows 628 → **631** passed / 0 warnings (still 30 modules — the +3 landed in an existing module) | Testing | [README.md](README.md) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) (v2.8.0 §3.1 Build/ policy), [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md)

---

## 2026-08-01 — v0.3.0 Spec v2.8.0: Missing-Bundle Failure Mode (build/)

**Date:** 2026-08-01 | **Status:** ✅ Complete | **Tests:** 631

### Build/ policy documents the verified missing-`build/` failure mode

**Commit:** [`ce9cf45`](https://github.com/griffinkelton/insights-explorer/commit/ce9cf45)

| Change | Type | Related Docs |
|---|---|---|
| v0.3.0 spec bumped **v2.7.0 → v2.8.0** — Build/ policy block gains a blockquote: a missing `build/` does **not** degrade to a broken iframe — `declare_component` raises `StreamlitAPIException: No such component directory` at registration and the **entire page run fails** (error banner; nothing after the component renders) | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |
| Failure mode **verified 2026-08-02** via fresh-checkout simulation — Phase 3 implementers must treat a missing `build/` as a hard deploy error, not a UI fallback | Docs | [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md) |
| Enforced in tests by `a2a083e` (`TestMissingBuildDirectoryFailsLoudly`, 3 tests): missing dir → registration raises, existing dir registers fine, absolute path in message | Testing | [tests/test_drive_picker_component.py](tests/test_drive_picker_component.py) |
| Footer history preserved: v2.8.0 note prepended over the v2.7.0 → v2.1.0 chain | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md), [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md)

---

## 2026-08-01 — v0.3.0 Build: Frontend Bundle on GCP Deploy (cloudbuild.yaml)

**Date:** 2026-08-01 | **Status:** ✅ Complete | **Tests:** 631

### Frontend build step added to Cloud Build so the bundle exists before Streamlit starts

**Commit:** [`b0b63f1`](https://github.com/griffinkelton/insights-explorer/commit/b0b63f1)

| Change | Type | Related Docs |
|---|---|---|
| `cloudbuild.yaml` — new `build-frontend` step (`node:20`): `npm ci` + `npm run build` (`tsc --noEmit && vite build`) + bundle assertion (`build/index.html` + hashed JS assets) in `components/drive_picker_component_frontend`, mirroring the GitHub Actions frontend gate | CI/CD | [cloudbuild.yaml](cloudbuild.yaml) |
| Step runs **before** `install-and-test` so `build/` exists in the Cloud Build workspace when Streamlit starts (the wrapper hard-codes `path=.../build`) — closes the missing-bundle deploy failure mode | CI/CD | [components/drive_picker_component.py](components/drive_picker_component.py) |
| Timeout 600s → **900s** (covers both heavy steps: npm ci + vite build, then venv + pip install + pytest); header comment updated to note frontend failures also fail the build | CI/CD | [cloudbuild.yaml](cloudbuild.yaml) |
| Build/ policy pinned in v0.3.0 spec (v2.6.0): gitignored + built at deploy time, never committed; `cloudbuild.yaml` owns the GCP deploy build, GitHub Actions owns CI verification | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |

**Related:** [cloudbuild.yaml](cloudbuild.yaml), [.github/workflows/test.yml](.github/workflows/test.yml), [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md)

---

## 2026-08-01 — v0.3.0 Spec v2.5.0: #30 Playwright Deferral

**Date:** 2026-08-01 | **Status:** ✅ Complete | **Tests:** 631

### Defer Playwright smoke coverage to Phase 3 core (IDEAS #30 fast-follow ordering)

**Commit:** [`cc71a48`](https://github.com/griffinkelton/insights-explorer/commit/cc71a48) | **Issue:** [#8](https://github.com/griffinkelton/insights-explorer/issues/8)

| Change | Type | Related Docs |
|---|---|---|
| v0.3.0 spec §Fast-Follow: #30 Playwright explicitly **deferred** — no install, deps, or CI jobs before Phase 3 core integration works (an early seam would lock tests to the Phase 0/2 UI instead of the production flow) | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |
| Tracking identifier recorded: `test/playwright-drive-import-smoke` (issue or branch only — no packages, no CI changes) | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |
| No-secret boundary restated: no OAuth tokens / API keys / Picker credentials; no Google Picker interaction; app-controlled surfaces only (import button, on-demand render, readiness/error/cancel UI, theme sync, duplicate/rerun protection) via a test-mode component seam or fake result | Security | [IDEAS.md #30](IDEAS.md) |
| GitHub issue [#8](https://github.com/griffinkelton/insights-explorer/issues/8) created to track the smoke test through Phase 3 | Docs | [Issue #8](https://github.com/griffinkelton/insights-explorer/issues/8) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md), [IDEAS.md #30](IDEAS.md)

---

## 2026-08-01 — v0.3.0 Phase 1: Drive Import Server-Side Foundation

**Date:** 2026-08-01 | **Status:** ✅ Complete | **Tests:** 631

### Drive import server-side download + component validation + CI frontend gate (v0.3.0 spec §1.2–1.4)

**Commit:** [`9754189`](https://github.com/griffinkelton/insights-explorer/commit/9754189)

| Change | Type | Related Docs |
|---|---|---|
| `utils/drive_client.py` — new `download_drive_file()`: 3-layer size validation (metadata preflight → `_BoundedBytesIO` hard cap rejecting writes over 100 MB on **both** `get_media` and Sheets `export_media` paths → final `len()` check), server metadata authority (`files().get` for name/MIME/size), MIME allowlist (CSV / XLSX / native Sheets export-to-CSV), zero-byte rejection | Feature | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |
| `utils/drive_client.py` — typed `RuntimeError` categories (`not_found` / `access_denied` / `too_large` / `unsupported_type` / `download_failed`) with allowlisted structured logging — no `exc_info`, no raw API text, no file IDs | Security | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |
| `components/drive_picker_component.py` — wrapper structurally validates raw component value into `PickerSelection` (`kind` / `requestId` / `fileId`) or `None`; extra Picker metadata stripped at the boundary | Feature | [components/drive_picker_component.py](components/drive_picker_component.py) |
| `tests/test_drive_client.py` — ~16 new `TestDownloadDriveFile` tests incl. adversarial streamed-cap and independent final-check cases | Testing | [tests/test_drive_client.py](tests/test_drive_client.py) |
| `tests/test_token_safety.py` (new) — source scans: credential vars never reach `st.*` display (incl. `st.exception` / `st.json` / `st.code` / `st.dataframe`), logger calls, or `raise`; no `exc_info=True` in `drive_client.py` | Testing | [tests/test_token_safety.py](tests/test_token_safety.py) |
| `tests/test_static_analysis.py` — `TestDriveScopeRestricted`: token-level AST guard rejects `drive` / `drive.readonly` / `drive.metadata.readonly`, allows `drive.file` | Testing | [tests/test_static_analysis.py](tests/test_static_analysis.py) |
| `tests/test_drive_picker_component.py` (new) — wrapper contract tests (malformed/empty/wrong-kind ignored, metadata stripped) | Testing | [tests/test_drive_picker_component.py](tests/test_drive_picker_component.py) |
| `.github/workflows/test.yml` — frontend CI gate: `npm ci` + `tsc` typecheck + `vite build` + bundle artifact assertion (index.html + hashed JS assets), Node 20 pinned | CI/CD | [.github/workflows/test.yml](.github/workflows/test.yml) |
| v0.3.0 spec — Phase 2 test renamed to `test_successful_drive_import_replaces_previous_context` (atomic-import consistency; failure case `test_failed_drive_import_preserves_existing_context` already present) | Docs | [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |

**Related:** [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md), [plans/00-sprints/✅ phase-0-debug-summary.md](plans/00-sprints/✅%20phase-0-debug-summary.md)

---

## 2026-08-01 — Credential Rotation (IDEAS #29)

**Date:** 2026-08-01 | **Status:** ✅ Complete

### Rotate exposed Picker API key + re-authenticate GA4 (Phase 0 security follow-up)

**Commits:** [`cfa9ec6`](https://github.com/griffinkelton/insights-explorer/commit/cfa9ec6) (prep), [`1f6ca34`](https://github.com/griffinkelton/insights-explorer/commit/1f6ca34) (closeout)

| Change | Type | Related Docs |
|---|---|---|
| Old exposed Google Picker API key deleted/rotated in GCP Console; new key restricted to Picker API + app referrers (user-confirmed) | Security | [IDEAS.md #29](IDEAS.md) |
| GA4 re-authenticated in-app — fresh access token under the existing grant with `analytics.readonly` + `drive.file` scopes (grant not revoked; refresh token was never exposed) | Security | [utils/ga4_client.py](utils/ga4_client.py) |
| `.streamlit/secrets.toml` updated with new key; old value removed; stale `drive_picker_spike.pyc` deleted | Security | [.gitignore](.gitignore) |
| `.streamlit/secrets.example.toml` rewritten to document all v0.3.0 Phase 3 secret keys (`GOOGLE_PICKER_API_KEY`, `GOOGLE_CLOUD_PROJECT_NUMBER`, `DRIVE_PICKER_APP_ORIGIN`, `IS_DEVELOPMENT`) — placeholder-only, dead `PHASE_0_DRIVE_PICKER_SPIKE` flag dropped | Docs | [.streamlit/secrets.example.toml](.streamlit/secrets.example.toml) |
| Full repo sweep — old key absent from git history (all branches), reflog, stash, working tree, and unreachable objects (`git fsck --no-reflogs --unreachable`) | Security | — |
| Fresh token scope verified via `needs_scope_migration()` gate — granted scopes ⊇ `{analytics.readonly, drive.file}` | Testing | [utils/ga4_client.py](utils/ga4_client.py) |
| IDEAS.md #29 marked ✅; v0.3.0 spec fast-follow #29 marked ✅ Complete with 6-item checklist (5 verified, 1 deferred: Picker smoke test runs when Phase 3 wires the component) | Docs | [IDEAS.md](IDEAS.md), [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) |

---

## 2026-08-01 — Credential Leak Guard

**Date:** 2026-08-01 | **Status:** ✅ Done

### Pre-commit + CI guard: reject credential-shaped strings (IDEAS #29 regression guard)

| Change | Type | Related Docs |
|---|---|---|
| New `scripts/check_credentials.py` — scans staged text files for Google API key (`AIza…`, ≥30-char payload) and OAuth access token (`ya29…`, ≥10-char payload) shapes; redacts matches in output; min-length rules keep the `ya29.abc123` test fixture and `AIza...` doc placeholder safe | Security | [scripts/check_credentials.py](scripts/check_credentials.py) |
| Local pre-commit hook `check-credentials` registered (runs on staged text files) | Config | [.pre-commit-config.yaml](.pre-commit-config.yaml) |
| CI step in `test.yml` — `git ls-files -z | xargs -0 python scripts/check_credentials.py` on push/PR | CI/CD | [.github/workflows/test.yml](.github/workflows/test.yml) |
| `tests/test_credential_guard.py` — 13 tests: flags real-shaped keys/tokens, allows fixtures/placeholders/identifiers, redaction, hook + CI registration, end-to-end main() behavior | Testing | [tests/test_credential_guard.py](tests/test_credential_guard.py) |

---

## v0.2.0 — Architecture, UX & Maintenance Release

**Date:** 2026-07-31 | **Status:** ✅ Complete | **Tests:** 593 | **Tag:** `v0.2.0`

> Post-hardening release: immutable DataContext, interactive Learn page, browser-persisted onboarding, styles refactor with focus-visible accessibility, per-request Gemini token accounting, and v0.3.0 Drive Import design.

### Phase 1: DataContext Refactor

- 3-layer frozen dataclass: `raw_df → base_df → active_df` with `FilterState`
- Content-derived identity: SHA-256 for uploads, canonical request fingerprint for GA4
- No-op transitions: clear-when-clear, identical-filter, unchanged-metrics
- Custom-metrics lifecycle: rebuild from `raw_df`, preserve all rows via `rebuild_metrics_context()`
- AST-based retired-key guard: catches attribute, subscript, `.get()`, `setdefault`, `pop`, `del`, membership, and chained-alias access
- 4-step migration: introduce → writers → readers → remove legacy + AST guard

### Phase 2: Learn Page Redesign + Onboarding

- Interactive analyst-first learning experience: side navigation, 7 challenges, progressive disclosure
- Reusable `components/learning_challenge.py` with 6 challenge types
- "Before you conclude" verification checklist in Explore + Ask AI sections
- Repository architecture section with safe-change recipe
- Frontend-owned onboarding: browser localStorage persistence, one-shot `force_replay` flag
- Removed `tour_step` and all Python-side tour state
- Keyboard-accessible: progressbar ARIA, `focusTitle()`, button `:focus-visible`
- Design note documents `components.html()` trade-off; declared component deferred to IDEAS #27

### Phase 3: Styles Refactor + Focus-Visible

- 5 CSS named constants + 1 JS constant + `build_theme_css()` assembly
- Focus-visible with accent-derived variables (never red)
- Reduced-motion support preserved
- Keyboard shortcut (Ctrl/Cmd+K) evaluated and removed — chat input always visible in Streamlit, global listener not justified

### Phase 4: Gemini Per-Request Token Accounting

- `_track_usage()` returns structured dict: prompt, output, thought, cached, tool, total
- Per-request token counts in collapsible expanders on most recent response only
- Cumulative session totals below chat input — informational only, no gauges or quota estimates
- `MODEL_CONTEXT_LIMITS` dict for future `countTokens` guard
- Chart extraction calls do not overwrite chat response usage

### Phase 5: Drive Import Design (Design Only)

- `plans/🔵 v0.3.0-drive-import-design.md`: Picker API architecture, consent UX, security checklist, v0.1.0 baseline preservation, acceptance criteria

### Phase 0: Drive Picker Transport Spike ✅ Complete

- Option A (hidden-input DOM bridge via `components.html()`) **rejected** — `srcdoc` iframe origin fundamentally incompatible with Google Picker (403)
- Option B (declared Streamlit component with `Streamlit.setComponentValue()`) **accepted** — Picker opens, selection reaches Python, cancel/reset work
- Retained: `components/drive_picker_component.py` + `components/drive_picker_component_frontend/` (v0.3.0 foundation)
- Decision: [plans/00-sprints/✅ phase-0-debug-summary.md](plans/00-sprints/✅%20phase-0-debug-summary.md)

**Related:** [plans/audit/✅ v0.2.0-closeout.md](plans/audit/✅%20v0.2.0-closeout.md), [plans/audit/✅ v0.2.0-release-checklist.md](plans/audit/✅%20v0.2.0-release-checklist.md)

---

## v0.1.0 — Hardening Release

**Date:** 2026-07-30 | **Status:** ✅ Released | **Tests:** 389 | **Tag:** `v0.1.0`

> Full-scope hardening release based on GPT-5.6 12-batch audit (~85 findings).
> 4 phased PRs: repository safety → P0 application safety → data contract & integrations → documentation & release.

### PR 0: Repository Safety

| Change | Type |
|---|---|
| History scrub of `email/` + `drive-download-*/` via `git filter-repo` | Security |
| `.gitignore` rules: `email/`, `*.eml`, `data/`, `uploads/`, `exports/` | Config |
| `tests/fixtures/README.md` with synthetic-data provenance policy | Docs |

### PR 1: P0 Application Safety (12 files)

| Change | Type |
|---|---|
| OAuth security: callback binding, atomic writes, bounded cleanup, revocation logging | Security |
| Export escaping: `sanitize.py` with `safe_spreadsheet_value` + `safe_pdf_text` | Security |
| Error redaction: `SHOW_DEBUG_DETAILS`, UUID error IDs, generic messages | Security |
| HTML safety: replaced raw HTML with Streamlit primitives | Security |
| `active_dataframe()` helper with filter → custom → raw precedence | Fix |
| Empty-filter semantics: zero-row filters preserve empty DataFrame | Fix |
| Clear Data reload fix: `last_file_id = None` | Fix |

### PR 2: Data Contract & Integrations (17 files)

| Change | Type |
|---|---|
| Drive scope removal: `drive.readonly` removed, 3 read functions deleted | Security |
| GA4 pagination: offset + limit, 500k cap, dedup, `ga4_truncated` flag | Feature |
| Privacy notices: precise Gemini terms, updated footer | Docs |
| Funnel → "Page-Path Aggregation": literal matching, 8-step cap, caveats | Fix |
| Forecast → "Linear Trend Projection": daily calendar, elapsed days, caveats | Fix |
| API telemetry: success/failure/attempt counters, context meter removed | Refactor |
| Chart extraction opt-in, summary model selection, data quality fixes | Fix |
| UI safety: system fonts, keyboard guard, reduced-motion | Accessibility |

### PR 3: Documentation & Release

| Change | Type |
|---|---|
| README rewrite, LICENSE (MIT), SECURITY.md, RELEASE_CHECKLIST.md | Docs |
| Dependency consolidation: base.txt / dev.txt / requirements.txt | Config |
| CI standardization: dev.txt install, pip caching, lint + coverage | Config |
| .gitignore/.env.example expansion, pre-commit hardening, Sphinx cleanup | Config |

### PR 4: Testing & Validation Gates

| Change | Type |
|---|---|
| Theme validation: `VALID_THEMES = {"dark", "light"}` in styles.py | Security |
| OAuth binding tests: redirect-URI mismatch, POSIX permissions | Testing |
| Static analysis expanded: `drive.readonly` gate, silent except:pass scanner | Testing |
| Scenario tests: 11 groups (dataframe, clear, forecast, exports, funnel, streaming, model, GA4) | Testing |
| 3 silent except:pass blocks documented with justifying comments | Docs |

**Related:** [plans/audit/✅ v0.1.0-hardening-spec.md](plans/audit/✅%20v0.1.0-hardening-spec.md)

---

---

---

### OAuth Security Hardening & Code Quality Remediation

**Date:** 2026-07-29 | **Status:** ✅ Done | **Tests:** 351 → 359

| Change | Type | Related Docs |
|---|---|---|
| OAuth scope reduced from full `drive` to `drive.readonly` + `drive.file` — minimal blast radius (BUG-009) | Security | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| Token revocation on scope migration — `_revoke_token()` calls Google's `/revoke` endpoint, invalidates entire grant | Security | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| OAuth state file permission hardening — `chmod(0o600)` on PKCE code_verifier JSON files (BUG-010) | Security | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| Scope migration banner — `needs_scope_migration()` auto-detects stale cached credentials, persistent sidebar re-auth prompt | Feature | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| Shared error classification — `_classify_api_error()` pure function (HTTP status codes 429/403/500, emoji-prefixed messages) | Refactor | [utils/gemini_client.py](utils/gemini_client.py) |
| Thought + cached token tracking — `_track_usage()` extracts `thoughts_token_count` + `cached_content_token_count` | Feature | [utils/gemini_client.py](utils/gemini_client.py) |
| Flash-only model constraint — removed `gemini-2.5-pro` from `AVAILABLE_MODELS`; all models free-tier | Fix | [utils/gemini_client.py](utils/gemini_client.py) |
| Dead code cleanup — removed `ga4_auth_flow` from `app.py`, `components/sidebar.py`, `components/__init__.py` | Refactor | [utils/ga4_client.py](utils/ga4_client.py) |
| 8 smoke tests — new `tests/test_exports.py` (4 error classification + 2 Excel + 2 PDF export tests) | Testing | [tests/test_exports.py](tests/test_exports.py) |
| BUG-009 & BUG-010 — OAuth scope over-privilege + PKCE state persistence lost across Streamlit redirect | Docs | [BUGLOG.md](BUGLOG.md) |
| File reorganization — `plans/maintenance/` for post-phase-6 maintenance; IMPLEMENTATION_PLAN.md + ENHANCEMENTS.md + PROJECT_COMPLETE.md → `plans/00-meta/` | Docs | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |

**Key decisions (8 from remediation spec):**
- Scope detection: `issubset()` — future-proof, only missing scopes flag stale
- Re-auth UX: clear creds + rerun (not direct OAuth flow trigger from banner)
- Error classification: HTTP status codes (429/403/500) — stable taxonomy
- Streaming errors: yield + return (not raise) — avoids generator exception issues
- Token revocation: one call (prefer refresh token) — Google's /revoke invalidates entire grant
- File permissions: `if os.name != "nt": chmod(0o600)` + `try/except OSError` — best-effort
- Model constraint: flash-only — all free tier, no paid-model footgun
- Token tracking: thought tokens shown conditionally (non-zero only); cached tokens tracked but hidden

**Related:** [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md)

---

### Theme Toggle Executed — 4 phases, light/dark mode, 231 tests

**Date:** 2026-07-28 | **Status:** ✅ Done

| Phase | What | Files |
|---|---|---|
| 1 | Light theme CSS variables + theme param for `inject_custom_css()` | `utils/styles.py` |
| 2 | Session state + toggle button + wiring | `app.py`, `components/sidebar.py`, `components/__init__.py` |
| 3 | Theme-aware chart generation + Plotly cache-busting | `utils/charts.py`, `components/chat.py` |
| 4 | Learn page: delete standalone CSS, use `inject_custom_css()` | `pages/learn.py`, `utils/styles.py` |

**Key decisions (9 from 3 interview rounds):**
- Syntax tokens: background-only (dark colors on white = legible)
- Default: always dark (no `prefers-color-scheme` detection)
- Toggle: bottom of sidebar (learn link → theme → footer)
- Persistence: session-only (`st.session_state`)
- Learn page: same CSS function, standalone block deleted
- Plotly: theme-tagged cache keys (`chart_0_dark` / `chart_0_light`)
- Charts: `generate_chart()` accepts `theme` param for testability
- Hero gradient: darker purples in light mode for contrast
- Learn page styles: concept cards/tips/tabs use CSS variables

**Related:** [plans/p3-p4/✅ THEME_TOGGLE.md](plans/p3-p4/✅ THEME_TOGGLE.md), [plans/00-sprints/✅ theme-toggle-spec.md](plans/00-sprints/✅ theme-toggle-spec.md)

---

### Component Refactor Executed — 7 phases, app.py 809→78 lines, 228 tests

**Date:** 2026-07-28 | **Status:** ✅ Done

| Phase | What | Files |
|---|---|---|
| 1 | Extracted `utils/charts.py` + `utils/session.py` | `utils/charts.py` (new), `utils/session.py` (new), `app.py` |
| 2 | Extracted `components/hero.py` — empty state | `components/hero.py` (new) |
| 3 | Extracted `components/data_preview.py` — metrics, filters, quality | `components/data_preview.py` (new) |
| 4 | Extracted `components/summary.py` — AI summary | `components/summary.py` (new) |
| 5 | Extracted `components/chat.py` — chat, streaming, export | `components/chat.py` (new) |
| 6 | Extracted `components/sidebar.py` — sidebar + file processing | `components/sidebar.py` (new) |
| 7 | Created `components/__init__.py` orchestrator, rewrote `app.py` | `components/__init__.py` (new), `app.py` (rewritten) |

**Key decisions:**
- `clear_data()` lives in `utils/session.py` (shared by sidebar + orchestrator)
- BUG-005 fixed: `on_click=clear_data` → `if st.button` + `st.rerun()` pattern
- `_stream_chat_response` moved as-is with in-place mutation docstring
- Footer moved to `components/__init__.py`
- Widget key audit: all 4 keys unique, no collisions
- Test coverage: 194 → 228 (34 new tests across 8 modules)

**Related:** [plans/p5-p6/✅ COMPONENT_REFACTOR.md](plans/p5-p6/✅ COMPONENT_REFACTOR.md), [plans/00-sprints/✅ component-refactor-spec.md](plans/00-sprints/✅ component-refactor-spec.md)

---

### P4 Wave 1 + Streaming Sprint Executed — 4/4 items, 194 tests

**Date:** 2026-07-28 | **Status:** ✅ Done

| Item | What | Files |
|---|---|---|
| #19 | Streaming token-by-token responses (st.write_stream, generate_response_stream) | `utils/gemini_client.py`, `app.py` |
| #15 | Column picker & date filters (filter_dataframe, _render_data_filters) | `utils/data_loader.py`, `app.py` |
| #16 | Conversation memory (last 5 exchanges, New Chat button) | `utils/prompt_templates.py`, `app.py` |
| #17 | Export chat as Markdown report (report_exporter.py, kaleido) | `utils/report_exporter.py` (new), `app.py`, `requirements.txt` |

**Related:** [plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md](plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md), [plans/00-meta/✅ P4-future-plan.md](plans/00-meta/✅ P4-future-plan.md)

---

### P1–P3 Sprint Executed — 12 items implemented across 5 batches

**Date:** 2026-07-28 | **Tests:** 171 → 194

| Batch | Items | Status |
|---|---|---|
| Batch 1 (Safety) | #4 file limits + download slice, #5 rate limiting | ✅ |
| Batch 2 (Quick Wins) | #1 learn sidebar link, NEW-A OAuth redirect config | ✅ |
| Batch 3 (Docs) | #2 test count update, #3 doc updates, #9 README learn link | ✅ |
| Batch 4 (UX) | #8 onboarding tour | ⚠️ Deferred |
| Batch 5 (Infra) | #10 pytest-cov, #11 dev deps split, #12 test badges, #13 app.py structural test (20 tests), #14 GitHub Actions CI | ✅ |

**Key changes:**
- `utils/data_loader.py`: Added 100MB/50k-row limits, BytesIO parsing, 3-tuple return with warning
- `app.py`: Rate limiting (2-sec debounce + counter), learn sidebar link, OAuth env config, 3-tuple unpacking
- New `tests/test_app.py`: 20 structural tests (syntax, imports, structure, session state)
- New `.github/workflows/test.yml`: GitHub Actions CI pipeline
- New `requirements/base.txt` + `requirements/dev.txt`: Dev/prod dependency split
- `README.md`: Test breakdown table, GitHub Actions badge, learn page access, free-tier limits
- `ENHANCEMENTS.md` + `ARCHITECTURE.md`: Progress counts updated (15→22/37 done)

**Related:** [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md), [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md)

| Change | Commit | Related Docs |
|---|---|---|
| **P1–P3 sprint executed — 12 items implemented across 5 batches** | `83aef98` | [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md), [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md) |

---

### v1.6.0-era — AI & Data Processing Enhancements (2026-07-28)
- **21d**: Column type detection — `detect_column_types()` + colored badges (📅🔢🏷️📝) in data preview
- **21f**: Smart sampling — `smart_sample()` with stratified weekly sampling, replaces `head()` everywhere
- **21a+b**: Chart JSON detection — `[CHART:{json}]` token in prompts, JSON-first `detect_chart_request()` with keyword fallback + retry logic
- **21e**: Anomaly detection — 7-day rolling Z-score, collapsible anomaly table, red X markers on charts
- **21c**: Comparative mode — sidebar toggle, dual-panel charts, `build_comparison_prompt()`
- **CHANGED**: `utils/charts.py` — imports `find_date_column` from `utils/data_loader` (canonical source)
- **CHANGED**: `utils/prompt_templates.py` — chart instruction in chat prompt, JSON + keyword hybrid detection
- **CHANGED**: `components/chat.py` — CHART token stripping (post-detection), retry Gemini call, compare mode dual charts
- **CHANGED**: `components/sidebar.py` — `_render_compare_controls()` between Clear Data and API counter
- **CHANGED**: `app.py` — 5 compare mode session state variables
- **CHANGED**: `utils/styles.py` — `.col-badge` CSS for type badges

---

## 2026-07-28 — Static Analysis & Anti-Pattern Fixes

### Added Patterns 1 & 2 linters + fix BUG-005 on_click anti-pattern + docs sweep

**Commit:** [`7404961`](https://github.com/griffinkelton/insights-explorer/commit/7404961)

| Change | Type | Related Docs |
|---|---|---|
| Added Pattern 1 linter: Streamlit exception guard check (BUG-001 CI gate) | Testing | [BUGLOG.md](BUGLOG.md) |
| Added Pattern 2 linter: `on_click` anti-pattern detection (BUG-005 CI gate) | Testing | [BUGLOG.md](BUGLOG.md) |
| Fixed BUG-005: replaced `on_click=lambda` with `if st.button` + `st.spinner()` for summary generation | Fix | [BUGLOG.md](BUGLOG.md) |
| Docs consistency sweep | Docs | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |

---

### Docs consistency sweep: P2 completion + 166 test counts + build log + BUGLOG gating

**Commit:** [`4286c3d`](https://github.com/griffinkelton/insights-explorer/commit/4286c3d)

| Change | Type | Related Docs |
|---|---|---|
| Updated test counts (110 → 129 → 166) across all docs | Docs | [ARCHITECTURE.md](ARCHITECTURE.md), [README.md](README.md) |
| Added P2 Data Quality Scorecard completion entries to build log | Docs | [ARCHITECTURE.md](ARCHITECTURE.md) |
| BUGLOG patterns CI-gated in `test_static_analysis.py` | Testing | [BUGLOG.md](BUGLOG.md) |

---

### Add synthetic tests for def-before-call linter + FileIO fragility docs

**Commit:** [`4946e2a`](https://github.com/griffinkelton/insights-explorer/commit/4946e2a)

| Change | Type | Related Docs |
|---|---|---|
| Added def-before-call AST linter tests | Testing | [BUGLOG.md](BUGLOG.md) |
| Documented FileIO fragility in test contexts | Docs | [BUGLOG.md](BUGLOG.md) |

---

## 2026-07-28 — P2: Data Quality Scorecard

### Implement P2: Data Quality Scorecard — A-F grading, styled card, prompt integration

**Commit:** [`9842065`](https://github.com/griffinkelton/insights-explorer/commit/9842065)

| Change | Type | Related Docs |
|---|---|---|
| Added `DataQualityReport` dataclass + `assess_data_quality()` to `utils/data_loader.py` | Feature | [plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md](plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md) |
| Added `render_quality_scorecard()` to `app.py` — styled A-F grade card | Feature | [plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md](plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md) |
| Added quality section to `build_summary_prompt()` | Feature | [utils/prompt_templates.py](utils/prompt_templates.py) |
| 18 new tests in `test_data_quality.py` | Testing | [tests/test_data_quality.py](tests/test_data_quality.py) |

---

### Mark ORIGINAL_SPEC.md #15 as fully compliant — privacy wording matches spec verbatim

**Commit:** [`fe1fbac`](https://github.com/griffinkelton/insights-explorer/commit/fe1fbac)

| Change | Type | Related Docs |
|---|---|---|
| Fixed privacy disclaimer wording to match original spec exactly | Fix | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |

---

## 2026-07-28 — Error Boundary & BUG-008 Audit

### Add 14 unit tests for utils/error_boundary.py — render_error_card()

**Commit:** [`dd266d6`](https://github.com/griffinkelton/insights-explorer/commit/dd266d6)

| Change | Type | Related Docs |
|---|---|---|
| 14 tests covering 5 exception types, context rendering, stack trace display | Testing | [tests/test_error_boundary.py](tests/test_error_boundary.py) |

---

### BUG-008: Full except Exception audit — 11 instances across 5 files

**Commit:** [`0cc5278`](https://github.com/griffinkelton/insights-explorer/commit/0cc5278)

| Change | Type | Related Docs |
|---|---|---|
| 11 `except Exception` instances audited — 9 safe, 2 documented risks | Audit | [BUGLOG.md](BUGLOG.md) |

---

### Cross-reference audit: add missing BUGLOG.md links to 6 docs

**Commit:** [`863a940`](https://github.com/griffinkelton/insights-explorer/commit/863a940)

| Change | Type | Related Docs |
|---|---|---|
| BUGLOG.md cross-references added to README, ARCHITECTURE, and 4 other docs | Docs | [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) |

---

### Docs consistency sweep: P1 completion + stale counts + project structure updates

**Commit:** [`67509c3`](https://github.com/griffinkelton/insights-explorer/commit/67509c3)

| Change | Type | Related Docs |
|---|---|---|
| P1 App Icon completion documented across all docs | Docs | [ARCHITECTURE.md](ARCHITECTURE.md), [plans/p1-p2/✅ APP_ICON.md](plans/p1-p2/✅ APP_ICON.md) |
| Stale test counts updated across files | Docs | [README.md](README.md) |

---

### Add BUGLOG.md to DOCUMENTATION_INDEX.md + cross-refs in README and ARCHITECTURE

**Commit:** [`1f45885`](https://github.com/griffinkelton/insights-explorer/commit/1f45885)

| Change | Type | Related Docs |
|---|---|---|
| BUGLOG.md added to documentation index and cross-referenced | Docs | [BUGLOG.md](BUGLOG.md) |

---

### Fix privacy disclaimer wording to match original spec exactly

**Commit:** [`a846780`](https://github.com/griffinkelton/insights-explorer/commit/a846780)

| Change | Type | Related Docs |
|---|---|---|
| Privacy disclaimer now verbatim matches ORIGINAL_SPEC.md #15 | Fix | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |

---

## 2026-07-27 — P1: App Icon & Favicon

### Implement P1: App Icon & Favicon

**Commit:** [`25ca2df`](https://github.com/griffinkelton/insights-explorer/commit/25ca2df)

| Change | Type | Related Docs |
|---|---|---|
| Custom SVG icon + 8 PNG sizes + ICO + PWA manifest + OG image | Feature | [plans/p1-p2/✅ APP_ICON.md](plans/p1-p2/✅ APP_ICON.md) |
| `inject_favicon_meta()` added to `utils/styles.py` | Feature | [utils/styles.py](utils/styles.py) |
| Page configs updated to use custom favicon | Feature | [app.py](app.py), [pages/learn.py](pages/learn.py) |

---

### Apply 7 reviewer fixes to ✅ UNIFIED_PLAN.md + ✅ APP_ICON.md forward-reference fix

**Commit:** [`aad1190`](https://github.com/griffinkelton/insights-explorer/commit/aad1190)

| Change | Type | Related Docs |
|---|---|---|
| 7 review fixes applied to ✅ UNIFIED_PLAN.md | Docs | [plans/00-meta/✅ UNIFIED_PLAN.md](plans/00-meta/✅ UNIFIED_PLAN.md) |

---

## 2026-07-27 — Documentation Foundation

### Add BUGLOG.md — structured bug log with 7 documented bugs

**Commit:** [`ae21220`](https://github.com/griffinkelton/insights-explorer/commit/ae21220)

| Change | Type | Related Docs |
|---|---|---|
| 7 bugs documented with root causes, fixes, learnings, and patterns | Docs | [BUGLOG.md](BUGLOG.md) |

---

### Add app icon plan, bonus idea plan, doc index, cross-references, and fix IMPL plan issues

**Commit:** [`940ebdd`](https://github.com/griffinkelton/insights-explorer/commit/940ebdd)

| Change | Type | Related Docs |
|---|---|---|
| ✅ APP_ICON.md, ✅ BONUS_DATA_QUALITY_SCORECARD.md, DOCUMENTATION_INDEX.md created | Docs | [plans/](plans/) |
| Cross-references and IMPLEMENTATION_PLAN fixes | Docs | [IMPLEMENTATION_PLAN.md](plans/00-meta/IMPLEMENTATION_PLAN.md) |

---

### Add ORIGINAL_SPEC.md — preserve the initial project spec as historical reference

**Commit:** [`6fad5c3`](https://github.com/griffinkelton/insights-explorer/commit/6fad5c3)

| Change | Type | Related Docs |
|---|---|---|
| 26-item compliance checklist + evolution beyond spec documented | Docs | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |

---

### Add Phase 5+ detailed plans + IDEAS.md (25 enhancements + 10 moonshots)

**Commit:** [`c96b0fb`](https://github.com/griffinkelton/insights-explorer/commit/c96b0fb)

| Change | Type | Related Docs |
|---|---|---|
| 4 Phase 5 detailed plans (theme toggle, streaming, component refactor, AI/data) | Docs | [plans/p3-p4/ and plans/p5-p6/](plans/p3-p4/ and plans/p5-p6/) |
| IDEAS.md with 25 bonus enhancements + 10 moonshot ideas | Docs | [IDEAS.md](IDEAS.md) |

---

### Add IMPLEMENTATION_PLAN.md — detailed 21-item execution blueprint

**Commit:** [`585527d`](https://github.com/griffinkelton/insights-explorer/commit/585527d)

| Change | Type | Related Docs |
|---|---|---|
| 21-item plan with file-level precision, risk assessments, sprint plan | Docs | [IMPLEMENTATION_PLAN.md](plans/00-meta/IMPLEMENTATION_PLAN.md) |

---

### Rewrite ENHANCEMENTS.md v2 — 37 enhancements across 7 categories

**Commit:** [`7e964a9`](https://github.com/griffinkelton/insights-explorer/commit/7e964a9)

| Change | Type | Related Docs |
|---|---|---|
| Complete v2 rewrite with progress summary and related docs | Docs | [ENHANCEMENTS.md](plans/00-meta/ENHANCEMENTS.md) |

---

## 2026-07-26 — Learn Page, Testing, CI/CD

### Add '← Back to App' button to /learn page via st.page_link("app.py")

**Commit:** [`7abfdd7`](https://github.com/griffinkelton/insights-explorer/commit/7abfdd7)

| Change | Type | Related Docs |
|---|---|---|
| Cross-page navigation from learn page back to main app | Feature | [pages/learn.py](pages/learn.py) |

---

### Add 19 structural tests for the /learn page (test_learn_page.py)

**Commit:** [`a66e94d`](https://github.com/griffinkelton/insights-explorer/commit/a66e94d)

| Change | Type | Related Docs |
|---|---|---|
| Structural tests: syntax, imports, 8 tabs, content checks, stale detection | Testing | [tests/test_learn_page.py](tests/test_learn_page.py) |

---

### Add headless smoke test script (scripts/smoke_test.sh)

**Commit:** [`aecbce2`](https://github.com/griffinkelton/insights-explorer/commit/aecbce2)

| Change | Type | Related Docs |
|---|---|---|
| Headless boot verification: HTTP 200, no import errors | CI/CD | [scripts/smoke_test.sh](scripts/smoke_test.sh) |

---

### Add global error boundary (#13) — friendly error cards instead of red tracebacks

**Commit:** [`4fc85c9`](https://github.com/griffinkelton/insights-explorer/commit/4fc85c9)

| Change | Type | Related Docs |
|---|---|---|
| `utils/error_boundary.py` with `render_error_card()` | Feature | [utils/error_boundary.py](utils/error_boundary.py) |

---

## 2026-07-26 — Architecture & Test Suite Expansion

### Add ARCHITECTURE.md + update README and ENHANCEMENTS for completed roadmap items

**Commit:** [`af0eb03`](https://github.com/griffinkelton/insights-explorer/commit/af0eb03)

| Change | Type | Related Docs |
|---|---|---|
| Full architecture doc with design decisions, data flow, security model, build log | Docs | [ARCHITECTURE.md](ARCHITECTURE.md) |

---

### Add 18 unit tests for ga4_client module — completes the test suite

**Commit:** [`a8b518e`](https://github.com/griffinkelton/insights-explorer/commit/a8b518e)

| Change | Type | Related Docs |
|---|---|---|
| OAuth flow, credentials serialization, GA4 report pull tests | Testing | [tests/test_ga4_client.py](tests/test_ga4_client.py) |

---

### Add cloudbuild.yaml for CI/CD — auto-run pytest on every push via Google Cloud Build

**Commit:** [`ebb62e6`](https://github.com/griffinkelton/insights-explorer/commit/ebb62e6)

| Change | Type | Related Docs |
|---|---|---|
| GCP Cloud Build pipeline — install deps + run 171-test suite on every push | CI/CD | [cloudbuild.yaml](cloudbuild.yaml) |

---

### Add .streamlit/config.toml with secure defaults (#15 security enhancement)

**Commit:** [`4128741`](https://github.com/griffinkelton/insights-explorer/commit/4128741)

| Change | Type | Related Docs |
|---|---|---|
| Headless mode, XSRF protection, CORS disabled, 200MB upload cap | Security | [.streamlit/config.toml](.streamlit/config.toml) |

---

### Add /learn page — interactive Python & code walkthrough for the app

**Commit:** [`5ba31c5`](https://github.com/griffinkelton/insights-explorer/commit/5ba31c5)

| Change | Type | Related Docs |
|---|---|---|
| 8-tab tutorial: Streamlit, Pandas, Plotly, Gemini API, OAuth, Type Hints, Caching, Testing | Feature | [pages/learn.py](pages/learn.py) |

---

## 2026-07-26 — Security & Testing Foundations

### Add 18 unit tests for _sanitize_question() — prompt injection sanitizer

**Commit:** [`ceb7b87`](https://github.com/griffinkelton/insights-explorer/commit/ceb7b87)

| Change | Type | Related Docs |
|---|---|---|
| Prompt injection coverage: code blocks, backticks, whitespace, delimiters | Testing | [tests/test_prompt_templates.py](tests/test_prompt_templates.py) |

---

### Add Streamlit caching (#10): @st.cache_data on 3 functions

**Commit:** [`b569a79`](https://github.com/griffinkelton/insights-explorer/commit/b569a79)

| Change | Type | Related Docs |
|---|---|---|
| `@st.cache_data` on `validate_columns`, `get_dataset_stats`, `build_summary_prompt` | Performance | [utils/data_loader.py](utils/data_loader.py), [utils/prompt_templates.py](utils/prompt_templates.py) |

---

### Add comprehensive GA4 live connection setup guide to README

**Commit:** [`6426c00`](https://github.com/griffinkelton/insights-explorer/commit/6426c00)

| Change | Type | Related Docs |
|---|---|---|
| Step-by-step OAuth setup with ASCII diagrams and troubleshooting table | Docs | [README.md](README.md) |

---

### Add pytest to requirements.txt and document test command in README

**Commit:** [`358e0b7`](https://github.com/griffinkelton/insights-explorer/commit/358e0b7)

| Change | Type | Related Docs |
|---|---|---|
| Testing infrastructure: pytest dependency + README test command | Docs | [README.md](README.md), [requirements.txt](requirements.txt) |

---

### Add 14 unit tests for gemini_client module — mocked Gemini API

**Commit:** [`89d7a87`](https://github.com/griffinkelton/insights-explorer/commit/89d7a87)

| Change | Type | Related Docs |
|---|---|---|
| `generate_response` and `validate_api_key` tests with mocked API | Testing | [tests/test_gemini_client.py](tests/test_gemini_client.py) |

---

### Refactor: extract CSS to utils/styles.py (#6) and add type hints throughout (#7)

**Commit:** [`35661b4`](https://github.com/griffinkelton/insights-explorer/commit/35661b4)

| Change | Type | Related Docs |
|---|---|---|
| 200+ lines of custom CSS extracted to `utils/styles.py` | Refactor | [utils/styles.py](utils/styles.py) |
| `X \| None` type hints across all modules | Refactor | All `.py` files |

---

## 2026-07-25 — Initial Features

### Implement top 3 quick-wins: keyboard shortcuts, API key validation, prompt injection hardening

**Commit:** [`92869b5`](https://github.com/griffinkelton/insights-explorer/commit/92869b5)

| Change | Type | Related Docs |
|---|---|---|
| Cmd/Ctrl+K keyboard shortcut for chat focus | Feature | [utils/styles.py](utils/styles.py) |
| `validate_api_key()` on startup with persistent error banner | Feature | [utils/gemini_client.py](utils/gemini_client.py) |
| `_sanitize_question()` — prompt injection hardening | Security | [utils/prompt_templates.py](utils/prompt_templates.py) |

---

### Add GA4 live connection via OAuth Sign-in with Google and Analytics Data API

**Commit:** [`0288992`](https://github.com/griffinkelton/insights-explorer/commit/0288992)

| Change | Type | Related Docs |
|---|---|---|
| OAuth 2.0 flow + Google Analytics Data API integration | Feature | [utils/ga4_client.py](utils/ga4_client.py) |
| Google Sign-in button, property ID input, 7/30/90 day pull presets | Feature | [app.py](app.py) |

---

### Migrate from deprecated google.generativeai to google.genai SDK (v2.14.0)

**Commit:** [`8476b8f`](https://github.com/griffinkelton/insights-explorer/commit/8476b8f)

| Change | Type | Related Docs |
|---|---|---|
| SDK migration: `google.generativeai` → `google-genai` (`genai.Client`) | Migration | [utils/gemini_client.py](utils/gemini_client.py) |

---

## 2026-07-25 — Testing & Roadmap Foundation

### Add comprehensive pytest unit tests for data_loader and prompt_templates (59 tests)

**Commit:** [`f26e591`](https://github.com/griffinkelton/insights-explorer/commit/f26e591)

| Change | Type | Related Docs |
|---|---|---|
| 59 tests: data loading, validation, stats, prompt construction, chart detection | Testing | [tests/test_data_loader.py](tests/test_data_loader.py), [tests/test_prompt_templates.py](tests/test_prompt_templates.py) |

---

### Add comprehensive enhancement roadmap: 25 ideas across UX, code, security, AI, and data processing

**Commit:** [`5c92a83`](https://github.com/griffinkelton/insights-explorer/commit/5c92a83)

| Change | Type | Related Docs |
|---|---|---|
| Initial ENHANCEMENTS.md — 25 ideas across 5 categories | Docs | [ENHANCEMENTS.md](plans/00-meta/ENHANCEMENTS.md) |

---

## 2026-07-25 — Initial Commit

### Initial commit: GA4 Insight Explorer

**Commit:** [`c5177cc`](https://github.com/griffinkelton/insights-explorer/commit/c5177cc)

| Change | Type | Related Docs |
|---|---|---|
| Streamlit app with Gemini AI for analyzing GA4 export data | Feature | [app.py](app.py), [utils/](utils/) |
| CSV/XLSX upload, AI summary, chat interface, auto-chart generation | Feature | [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) |
| Privacy-first: in-memory only, clear data button, privacy disclaimer | Feature | [README.md](README.md) |

---

## 📊 Summary

| Metric | Value |
|---|---|
| Total commits tracked | 182 |
| Date range | July 25 – August 2, 2026 |
| Features shipped | GA4 Insight Explorer core, GA4 live OAuth, keyboard shortcuts, API key validation, prompt injection hardening, error boundary, learn page, data quality scorecard, app icon/favicon, OAuth security hardening, theme toggle, component refactor, streaming responses, conversation memory, Markdown report export, custom metrics, forecasting, funnel/aggregation views, command palette, DataContext refactor + onboarding tour, Gemini per-request token accounting, Google Drive import (declared Picker component + server-side download + typed error contract DriveImportError + content-derived Drive context factory + atomic ingestion refactor + _NamedBytesIO adapter + failure-preservation test matrix) |
| Tests | 0 → 664 across 30 modules |
| CI/CD | GitHub Actions CI (Python + frontend build gate) + Cloud Build + smoke test + pre-commit hooks (incl. credential guard) |
| Documentation | 119 MD files (~1.3 MB) incl. 37 plan/spec files under `plans/` + Sphinx docs |
| Plans | 37 files across `plans/00-meta`, `00-sprints`, `audit`, `maintenance`, `p1-p2`, `p3-p4`, `p5-p6` |

---

## 📖 Related Docs

- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central index of all project docs
- [plans/00-meta/✅ UNIFIED_PLAN.md](plans/00-meta/✅ UNIFIED_PLAN.md) — Master execution plan
- [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md) — Current sprint spec
- [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md) — Sprint completion tracker
- [plans/00-meta/✅ P4-future-plan.md](plans/00-meta/✅ P4-future-plan.md) — Future-phase plan
- [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) — Post-phase-6 OAuth security hardening & code quality remediation

---

*Legacy v1.x-era cleanup (2026-08-01): the v1.5.0 Drive picker entry was removed — that picker and its `drive.readonly` scope were removed in v0.1.0 hardening — and this era's test counts (236/239) are superseded by the current 631-test suite.*
