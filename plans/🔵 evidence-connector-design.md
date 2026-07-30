# 🔵 Evidence Dashboard Source Connector — Design Document

> **Status:** 🔵 Design / Planning — not yet scheduled
> **Related:** IDEAS.md #26 | **Predecessor:** v0.2.0 DataContext refactor + v0.3.0 analysis quality release
> **Target version:** v0.4.0

---

## Concept Overview

A **first-class, admin-only data source connector** for Evidence-built static dashboards. Evidence is a static-site data-product framework that pre-compiles every query into Parquet files and lists them in a public `/data/manifest.json`. This connector resolves that manifest, downloads only allowlisted datasets, validates schemas, stages encrypted extracts, and exposes curated aggregate overlays alongside GA4 data — without attempting person-level attribution.

**What it is:** An approved, read-only connector for a specific class of data source (Evidence static dashboards) with strict source configuration, secure server-side secrets, an allowlisted dataset catalog, immutable ingestion metadata, and aggregate-only GA4 overlays.

**What it is NOT:** A generic "connect any website" tool, a credential-scraping engine, a person-level linking feature, or a hosted/public connector.

---

## Storage and Deployment Decision

> **Status:** Accepted for v0.4 local-only development.

Insights Explorer is a **single-user, local-only** analytical tool. Approved Evidence-derived extracts and curated aggregate tables may be stored only in a **local encrypted staging store** on the authorized analyst's company-managed device.

- Raw source files, credentials, and proprietary extracts must **never** enter Git.
- No proprietary source data may be placed in `st.session_state`, `st.cache_data`, browser storage, logs, screenshots, or external AI prompts.
- Sync is **manual only**; no background scheduler or shared service.
- Access is limited to the **authorized local user**.
- Default retention: raw extracts 30 days; curated aggregates 90 days — **pending data-owner confirmation**.
- Local source metadata may record checksums, schema fingerprints, sync time, and approved dataset IDs.
- A hosted/public deployment is **out of scope for v0.4**.

### v0.4 Gate

Before starting v0.4 Phase B implementation:

1. Full-disk encryption verified on the authorized analyst's device (FileVault / BitLocker).
2. Data owner confirms local retention and named-user access are acceptable.
3. Retention windows are confirmed (defaults above are temporary pending policy).

### Future Website Demo

The future public demo is a **separate deployment mode**, not a configuration flag on the local Evidence connector.

| Mode | Data | Connector |
|---|---|---|
| **Local / internal** | Real GA4 + approved Evidence data | Full connector, local staging, OS keychain credentials |
| **Public demo** | Synthetic / fully approved public sample only | No Evidence URL, credentials, or sync; clearly marked demo data |

A public demo letting visitors upload their own GA4 CSV or connect their own GA4 property via OAuth is a separate security, privacy, and legal workstream — requiring terms, privacy notice, consent language, retention/deletion behavior, abuse controls, and incident path. Defer until that is a deliberate product objective.

---

## Roadmap Context

This connector is correctly sequenced **after** the following releases, which establish the product conventions it depends on:

| Version | Release outcome | Why it precedes Evidence |
|---|---|---|
| **v0.2.0** | Trustworthy analytics foundation | DataContext reader migration, cache correctness, release gates |
| **v0.3.0** | Reproducible, contextual GA4 analysis | Data dictionary, saved analysis recipes, annotations, natural-language dates |
| **v0.4.0** | Governed GA4 + Evidence aggregate analysis | This connector |

**v0.3.0 features that directly benefit v0.4.0:**
- **Data dictionary** — gives a place to document Evidence metric definitions, grain, QA status, and unknowns.
- **Saved analysis recipes** — provides the format for reproducible overlay analysis: both source versions, filters, content mapping version, suppression policy, methodology.
- **Annotations / context events** — lets an analyst mark relaunches, campaign starts, tracking changes — essential for interpreting a GA4 + Evidence overlay.
- **Natural-language dates** → visible deterministic filters — transfers cleanly to time-grain joins.

### v0.4 In Scope / Out of Scope

| In scope | Out of scope |
|---|---|
| Local-only Evidence connector | Hosted demo with live proprietary connector |
| Manual admin-initiated sync | Multi-user accounts, RBAC, or shared storage |
| Manifest discovery + dataset allowlist | Automatic sync scheduling |
| OS-keychain credential storage | Browser-side credential handling |
| Local private staging outside the repository | Raw proprietary-data export |
| Raw/canonical extract checksums + schema validation | External AI analysis of Evidence-derived rows |
| Curated aggregate data products | Arbitrary-dashboard or arbitrary-URL connector |
| GA4 + Evidence aggregate overlays | Individual-level GA4-to-demographic linking |
| Source lineage, provisional labels, low-cell suppression | Public or broadly shared exports |
| Retention cleanup command | Automated AI over confidential source data |

---

## Product Boundary

Add a **Data Sources** area to Insights Explorer with two clearly separated concepts:

| Capability | Purpose | Recommendation |
|---|---|---|
| **GA4 source** | First-party web behavior and acquisition data | Keep existing connector |
| **Evidence dashboard source** | Approved dashboard datasets (questionnaire aggregates, demographic overlays) | Add in v0.4, read-only |
| **Joined analysis view** | Curated, documented aggregate overlays | Add after source validation |
| **Generic website connector** | Arbitrary URL, authentication, crawling, unknown formats | Do NOT add |

---

## Safe Architecture

```
Admin UI (Insights Explorer)
    │
    │ creates source configuration; credentials entered once via OS keychain
    ▼
Server-side connector service
    ├── Host allowlist + HTTPS validation
    ├── Auth adapter (none / HTTP Basic / approved cookie flow)
    ├── Evidence manifest resolver
    ├── Parquet downloader + schema validator
    └── Audit log / sync metadata
    │
    ▼
LocalStagingStore  (OS app-data dir, outside repository root)
    ├── evidence/raw/          # downloaded Parquet, 30-day retention
    ├── evidence/curated/      # approved aggregate Parquet/DuckDB
    ├── evidence/quarantine/   # failed validation, limited retention
    ├── metadata/catalog.sqlite
    └── logs/connector.log     # redacted operational log
    │
    ▼
Insights Explorer analysis layer
    ├── DataContext source
    ├── GA4 / Evidence / overlay modes
    └── Suppression and QA rules
```

### Local Staging Store Location

Use the OS application-data directory — **not a folder beside the repository**:

```
macOS:   ~/Library/Application Support/InsightsExplorer/
Windows: %LOCALAPPDATA%\InsightsExplorer\
Linux:   ~/.local/share/insights-explorer/
```

Add all development equivalents to `.gitignore`, but **do not rely on `.gitignore` as a security control** — the directory should be outside the repo root so an accidental `git add -f`, zip, or upload is less likely to include proprietary material.

```gitignore
# Never commit local proprietary Evidence data or connector secrets
.insights-explorer/
data/evidence/
*.duckdb
*.parquet
.env
.env.*
!.env.example
```

### LocalStagingStore Abstraction

The connector must not write arbitrary paths directly. Add a `LocalStagingStore` abstraction in `utils/local_staging_store.py`:

```python
import hashlib
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Literal


def _default_staging_root() -> Path:
    """Resolve OS-appropriate app-data directory, outside the repo root."""
    import platform
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "InsightsExplorer"
    elif system == "Windows":
        base = os.environ.get("LOCALAPPDATA", Path.home())
        return Path(base) / "InsightsExplorer"
    else:
        return Path.home() / ".local" / "share" / "insights-explorer"


class LocalStagingStore:
    """Manages local encrypted staging directories for Evidence extracts.

    All paths resolve under the OS app-data directory — never under the
    repository root. Callers must not construct raw paths themselves.
    """

    def __init__(self, root: Path | None = None):
        self.root = root or _default_staging_root()

    def raw_path(self, source_id: str, dataset_name: str) -> Path:
        p = self.root / "evidence" / "raw" / source_id
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{dataset_name}.parquet"

    def curated_path(self, source_id: str, dataset_name: str) -> Path:
        p = self.root / "evidence" / "curated" / source_id
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{dataset_name}.parquet"

    def quarantine_path(self, source_id: str, dataset_name: str) -> Path:
        p = self.root / "evidence" / "quarantine" / source_id
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{dataset_name}.parquet"

    def catalog_db_path(self) -> Path:
        p = self.root / "metadata"
        p.mkdir(parents=True, exist_ok=True)
        return p / "catalog.sqlite"

    def log_path(self) -> Path:
        p = self.root / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p / "connector.log"

    def assert_outside_repo(self) -> None:
        """Raise if staging root is inside the Git repository."""
        repo_root = Path(__file__).resolve().parents[1]
        if self.root.resolve().is_relative_to(repo_root):
            raise RuntimeError(
                f"Staging root {self.root} is inside the repository. "
                "Move it to an OS app-data directory."
            )
```

> **Test requirement:** `tests/test_local_staging_store.py` must assert that `assert_outside_repo()` raises when given a path under the repo root, and passes for valid OS app-data paths.

---

## Evidence Manifest Resolution

Evidence pre-compiles every query into static Parquet files at build time. The manifest at `{base_url}/data/manifest.json` lists every pre-built dataset with content-hash paths:

```json
{
  "renderedFiles": {
    "bigquery": [
      "static/data/bigquery/questionnaire_funnel/948fc2226955b507e5678a7ca158fb34/questionnaire_funnel.parquet",
      "static/data/bigquery/questionnaire_agg/7d6715e2285be02136211af278e46b45/questionnaire_agg.parquet",
      "static/data/bigquery/top_content_by_demographic/4d031d56b0edb55a4b7c95ecaa4dad3f/top_content_by_demographic.parquet"
    ]
  }
}
```

The hex string in each path is a content hash Evidence generates at build time — it changes whenever the underlying query/data is rebuilt. **Never hardcode these paths.** The connector must:

1. Fetch `/data/manifest.json` first (stable, un-hashed endpoint)
2. Parse out the current path for each dataset by name
3. Fetch the corresponding Parquet file using the fresh path
4. Store the last-seen hash per dataset for change detection

This makes the pipeline resilient to Evidence rebuild cycles.

### Datasets Discovered (MyBrainGuide Dev Example)

From the manifest at `dashboard.dev2.mybrainguide.org`:

| Dataset | Source | Description |
|---|---|---|
| `campaign_performance` | bigquery | Campaign metrics |
| `core_web_metrics` | bigquery | Core Web Vitals data |
| `ga4_event_names` | bigquery | GA4 event taxonomy |
| `ga4_geography` | bigquery | Geographic traffic (country) |
| `ga4_geography_city` | bigquery | Geographic traffic (city) |
| `ga4_language` | bigquery | Language distribution |
| `ga4_outbound_clicks` | bigquery | Outbound link clicks |
| `page_paths` | bigquery | Page path inventory |
| `page_transitions` | bigquery | Page-to-page navigation |
| `questionnaire_funnel` | bigquery | Funnel starts/completions by date |
| `questionnaire_agg` | bigquery | Aggregate questionnaire metrics |
| `questionnaire_journey_events` | bigquery | Individual journey events |
| `questionnaire_journey_monthly` | bigquery | Monthly journey aggregates |
| `questionnaire_responses` | bigquery | Individual response data |
| `questionnaire_trend` | bigquery | Trend data over time |
| `search_console_*` | bigquery | GSC queries, pages, countries |
| `top_content` | bigquery | Top-performing content |
| `top_content_by_demographic` | bigquery | Content × demographic segments |
| `traffic_attribution` | bigquery | Traffic source attribution |

**Important caveat:** This is a dev/QA environment. The data pipeline may be replaced/reset when production `dashboard.mybrainguide.org` data is finalized. Always label dashboard-derived findings as provisional. Phase C curated data products must be built against **fixture/mock Parquet files**, not live dev data.

---

## Source Configuration

Persist a source record with metadata only; store the secret separately.

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class EvidenceSourceConfig:
    source_id: str                       # e.g. "mybrainguide-dev"
    display_name: str                    # e.g. "MyBrainGuide Evidence Dashboard (dev)"
    base_url: str                        # e.g. "https://dashboard.dev2.mybrainguide.org"
    allowed_host: str                    # e.g. "dashboard.dev2.mybrainguide.org"
    connector_type: Literal["evidence_static"] = "evidence_static"
    auth_type: Literal["none", "http_basic", "approved_session"] = "none"
    credential_ref: str | None = None    # Secret-manager reference, never the secret
    allowed_datasets: tuple[str, ...] = ()
    classification: Literal["internal", "confidential"] = "confidential"
    owner: str = ""
    environment: Literal["dev", "prod", "unknown"] = "unknown"
    enabled: bool = True
```

Example YAML configuration:

```yaml
display_name: MyBrainGuide Evidence Dashboard (dev)
base_url: https://dashboard.dev2.mybrainguide.org
allowed_host: dashboard.dev2.mybrainguide.org
connector_type: evidence_static
classification: confidential
environment: dev
allowed_datasets:
  - questionnaire_funnel
  - questionnaire_agg
  - questionnaire_trend
  - top_content_by_demographic
  - page_paths
  - traffic_attribution
  - ga4_language
sync_mode: manual
```

Start with **manual sync only**. Enable scheduled refresh (Phase E) only after confirming the dashboard's refresh cadence, schema stability, and whether the development environment is expected to be reset or replaced.

---

## Sync Metadata

Store a `SyncRecord` for every sync operation in `utils/sync_metadata.py`. This is the primary mechanism for detecting when the dev env resets or schemas drift.

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SyncRecord:
    source_id: str
    dataset_name: str
    manifest_hash: str          # hex from the URL path — changes on Evidence rebuild
    schema_fingerprint: str     # hashlib.sha256 of sorted column names + dtypes
    row_count: int
    synced_at: str              # ISO 8601
    environment: Literal["dev", "prod", "unknown"]
    sync_status: Literal["success", "catalog_validation_failed", "schema_drift", "download_error"]
```

When `manifest_hash` changes between syncs, the connector emits a `SCHEMA_DRIFT` warning and halts before touching downstream curated tables. No silent failures.

---

## Credential Handling

Support only a small, deliberate set of authentication modes:

| Mode | When to use | Implementation |
|---|---|---|
| **No authentication** | Public, non-sensitive sources; explicitly approved hosts | Direct manifest fetch |
| **HTTP Basic Auth** | Server responds with `401` + `WWW-Authenticate: Basic` | Prompt for username/password; send via `Authorization` header |
| **Approved session-based sign-in** | Documented login flow; approved organizational access | Prompt for credentials; POST to login endpoint; store session cookie |
| **SSO/OAuth** | Deferred — requires enterprise identity model | Do NOT automate browser-login scraping |

**Storage:** Use OS keychain (`keyring` package). The stored source record contains a secret reference such as `secret://insights-explorer/evidence/mybrainguide-dev`, never a username/password.

**Operational controls:**

- Encrypt secrets at rest (OS keychain + full-disk encryption on device)
- Redact `Authorization`, `Cookie`, password fields, and signed URLs from logs
- Never use `st.cache_data` for credentialed responses or raw proprietary datasets
- Use short request timeouts, bounded redirects, response-size limits, and certificate verification
- Permit HTTPS only; reject private/reserved IP targets after DNS resolution (SSRF prevention)
- Require admin-initiated sync; no unattended credential use
- Show a confirmation banner before first extraction: "This imports proprietary dashboard data into Insights Explorer."

---

## Connector Contract

Define a small interface to prevent dashboard-specific behavior from leaking across the app. Add to `utils/connector_types.py`:

```python
from typing import Protocol
from dataclasses import dataclass
import pandas as pd


@dataclass
class ConnectionResult:
    success: bool
    message: str
    dataset_count: int = 0

@dataclass
class DatasetDescriptor:
    name: str
    current_hash: str
    size_bytes: int
    columns: list[str]

@dataclass
class SchemaPreview:
    dataset_id: str
    columns: list[str]
    dtypes: dict[str, str]
    row_count_estimate: int

@dataclass
class CatalogValidationResult:
    passed: bool
    missing_columns: list[str]
    unexpected_columns: list[str]
    suppression_violations: list[str]

@dataclass
class SyncResult:
    status: str   # "success" | "catalog_validation_failed" | "schema_drift" | "download_error"
    datasets_synced: list[str]
    datasets_skipped: list[str]
    errors: list[str]


class DataConnector(Protocol):
    def test_connection(self) -> ConnectionResult: ...
    def discover_datasets(self) -> list[DatasetDescriptor]: ...
    def preview_schema(self, dataset_id: str) -> SchemaPreview: ...
    def validate_catalog_entry(self, dataset_id: str, df: pd.DataFrame) -> CatalogValidationResult: ...
    def sync(self, selected_datasets: list[str]) -> SyncResult: ...
```

> **`validate_catalog_entry()` is called before any data reaches `active_df`.** A failed validation returns a `SyncResult` with `status="catalog_validation_failed"` and moves the file to `quarantine/`. It never partially loads bad data into the Explorer.

**Sync pipeline steps:**

1. Fetch the stable manifest endpoint
2. Parse only expected manifest structures
3. Resolve only allowlisted dataset names and only same-origin asset URLs
4. Download the current Parquet asset
5. Verify content type, file size, and expected schema
6. Call `validate_catalog_entry()` — abort to quarantine on failure
7. Store a `SyncRecord` with checksum and schema fingerprint
8. Write immutable raw extract to `LocalStagingStore.raw_path()`
9. Transform only approved datasets into curated aggregates
10. Return a data-quality report — not raw data directly to the UI

**Change detection:** Compare `manifest_hash` in `SyncRecord` against the previous sync. Only re-download and re-process datasets whose hash changed.

---

## content_key Mapping

The overlay's entire value rests on correctly normalizing GA4 `page_path` values to match Evidence `content_key` values across a site that relaunched in March 2026. This mapping is a **versioned artifact** in `utils/content_key_mapping.py` — never inline normalization logic:

```python
MAPPING_VERSION = "v1"
RELAUNCH_DATE = "2026-03-01"  # new site launched ~March 2026

# TODO: populate after manual URL audit with data owner.
# Old path → canonical key. Do NOT auto-populate or guess.
PATH_OVERRIDES: dict[str, str] = {
    # "/old-path/": "canonical-key",
}

def normalize_path(raw_path: str) -> str:
    """Normalize a GA4 page_path or Evidence content_key to canonical form.

    Lower-case, strip query strings, reconcile trailing slashes,
    then apply PATH_OVERRIDES for pre-relaunch URL mapping.
    """
    path = raw_path.lower().split("?")[0].rstrip("/") or "/"
    return PATH_OVERRIDES.get(path, path)
```

> **`PATH_OVERRIDES` requires a manual URL audit — do NOT auto-populate.** Flag as a TODO in any sprint plan that includes Phase C or D work.

---

## Dataset Catalog

A catalog between raw extraction and analysis is the authoritative definition of what can be used and how. Any dataset not in the catalog is rejected at `validate_catalog_entry()` time.

```yaml
questionnaire_funnel:
  classification: confidential
  source_grain: date + questionnaire
  approved_use: aggregate funnel analysis
  required_columns:
    - date
    - questionnaire_started
    - questionnaire_completed
  join_candidates:
    - date
    - content_key
  min_reporting_cell: 10
  status: provisional

top_content_by_demographic:
  classification: confidential
  source_grain: date + content + demographic segment
  approved_use: aggregate content affinity analysis
  required_columns:
    - date
    - content_key
  join_candidates:
    - date
    - content_key
    - language
  min_reporting_cell: 10
  status: provisional
```

---

## Overlay Model

Keep the first overlay intentionally conservative:

\[
\text{GA4 aggregate traffic} \leftrightarrow \text{Evidence aggregate outcomes}
\]

Use joins at a shared aggregate grain such as:

```
date + canonical_content_key + language
```

### Potential Views

- Daily/weekly traffic versus questionnaire starts/completions
- Content engagement versus downstream result-category distributions
- Channel/campaign traffic versus aggregate questionnaire completion patterns
- Content interest by self-reported demographic segment, with suppression rules
- Pre/post site-relaunch trends (use `RELAUNCH_DATE` from `content_key_mapping.py`)

### Important Limitations

- **Never** label any resulting ratio as individual conversion unless GA4 and the Evidence source have an approved, consented, persistent linkage key
- Without that, describe results as **aggregate association**, not a user journey or causal relationship
- Evidence questionnaire demographics are self-reported, not pulled from GA4 — treat them as distinct from GA4 demographic reporting
- Include a pre/post-relaunch date flag on every overlay view

---

## Privacy and Proprietary-Data Controls

"De-identified" does not mean "safe to expose without controls." Primary risks:

- Small-cell disclosure through rare demographic combinations
- Proprietary metric definitions or product intelligence leaking through exports
- Re-identification through linkage with dates, geography, content, and external context
- Unauthorized redistribution through downloads, logs, screenshots, or AI prompts

**Semantic-layer guardrails:**

- Suppress or roll up results below a minimum cell size (n < 10)
- Never display exact values for sparse intersections (date × demographic × language × campaign)
- Round or bucket sensitive counts when necessary
- Disable CSV export for confidential source-level tables by default
- Separate raw extracts from aggregated, UI-approved views
- Source labels: **"Confidential — dashboard QA data"** and **"Provisional metric definition"**
- Audit metadata: source, sync time, dataset, manifest path/hash, row count, schema fingerprint, outcome
- Default AI/chat features to **exclude confidential Evidence rows** until there is an explicit approved policy for model use and redaction

---

## AI Exclusion — Implementation Path

The existing `build_summary_prompt()` and `build_chat_prompt()` in `utils/prompt_templates.py` receive `df: pd.DataFrame` directly. Add a guard **before** either function is called — and before the `@st.cache_data` path is hit:

```python
def _assert_prompt_safe(df: pd.DataFrame, classification: str = "internal") -> None:
    """Raise if a confidential DataFrame is about to enter an AI prompt.

    Must be called BEFORE build_summary_prompt() / build_chat_prompt()
    and BEFORE any @st.cache_data path. Evidence rows must never be cached
    under a key that could be hit by a GA4-only session.
    """
    if classification == "confidential":
        raise ValueError(
            "AI features are disabled for confidential Evidence data. "
            "Use the overlay view's aggregate-only export instead."
        )
```

In `components/summary.py` and `components/chat.py`, check `st.session_state.data_context.classification` when a DataContext is present. If `"confidential"`, show an info banner: *"AI analysis is disabled for confidential source data"* — not an error state.

---

## DataContext Integration Considerations

Do not force GA4 and Evidence into the same raw DataFrame immediately. Add source-aware fields to DataContext in v0.4 **with safe defaults** so zero existing call sites break:

```python
@dataclass(frozen=True)
class DataContext:
    # --- existing v0.2.0 fields (unchanged) ---
    source_id: str
    version: int
    raw_df: pd.DataFrame
    base_df: pd.DataFrame
    active_df: pd.DataFrame
    filters: FilterState
    provenance: tuple[str, ...]

    # --- v0.4 additive fields: keyword-only defaults, no existing code reads these ---
    source_kind: Literal["ga4", "evidence", "overlay"] = "ga4"
    classification: Literal["internal", "confidential"] = "internal"
    qa_status: Literal["validated", "provisional"] = "validated"
```

> **Test requirement:** `tests/test_data_context_backwards_compat.py` must construct DataContext with only v0.2.0 fields and assert defaults are correct. This is a CI gate.

For overlay analysis, `raw_df` should be the curated joined table — not a giant unfiltered union of both raw sources. Preserve input lineage in provenance:

```python
provenance = (
    "ga4:property-request:ab12cd34",
    "evidence:questionnaire_funnel:manifest-hash:ef56gh78",
    "mapping:content-key:v1",
    "suppression:v1",
    "join:date+content-key+language",
)
```

Every cache key must include both source IDs and versions, mapping version, and suppression-policy version.

---

## Delivery Plan

### Phase A — Validate Source *(v0.4 start gate: v0.3.0 complete)*

- Build an admin-only test screen (not visible in main Explorer)
- Show a human gate checklist: data ownership confirmed, permitted use confirmed, retention period confirmed, named users confirmed — "Enable Source" button requires all four
- Test authentication without storing secrets in code
- Fetch manifest; display dataset names, current asset hashes, sizes, and schemas
- **Do NOT yet expose data in the Explorer or write any local files**
- Confirm staging path resolves outside repository root (`assert_outside_repo()`)

### Phase B — Secure Ingestion *(gate: data-owner approves local retention)*

- Add `EvidenceStaticConnector` implementing `DataConnector` protocol
- Add `LocalStagingStore` with OS app-data directory resolution
- Add `keyring` credential storage; `EvidenceSourceConfig.credential_ref` only in source config
- Implement host allowlist, same-origin enforcement, size limits, logging redaction, schema validation
- Add `SyncRecord` persistence in `catalog.sqlite`
- Add retention cleanup command: deletes expired raw extracts and reports what it removed
- Support only manual sync and only the short dataset allowlist

### Phase C — Curated Data Products *(gate: Phase B green in CI with fixture data)*

- Define `metrics.yml` / dataset catalog
- Build curated aggregate tables against **fixture Parquet files**, not live dev data
- Create `content_key_mapping.py` with `PATH_OVERRIDES` stub — **manual URL audit required before populating**
- Build quality checks: duplicate grain, missing dates, unexpected columns, row-count drift, unmatched content keys, low-cell suppression
- Produce curated aggregate tables only — never serve raw extracts to the UI

### Phase D — Explorer Overlay *(gate: Phase C validated against fixture data; production URL confirmed stable)*

- Add source selector: **GA4**, **Evidence**, **GA4 + Evidence overlay**
- Add a visible methodology drawer: join grain, limitations, QA status, source timestamp, suppression
- Add charts designed for aggregate interpretation, not individual user-path claims
- Add `_assert_prompt_safe()` guard in prompt builders; AI banner in summary + chat components
- Keep exports disabled by default for confidential overlay data

### Phase E — Controlled Scheduling *(gate: two or more successful manual Phase D syncs)*

- Add scheduled refresh
- Alert on schema changes, missing datasets, unexpected row-count deltas, failed auth, stale data
- Require admin approval before a schema change becomes visible in Explorer

---

## What NOT to Build Yet

- Arbitrary "connect any website" support
- Headless-browser credential automation
- Storage of passwords in Streamlit state or application configuration
- Full raw-dashboard ingest by default
- Individual-level GA4-to-demographic linking
- Automated AI analysis over confidential source data
- Public or broadly shared exports
- Hosted/cloud staging store (defer until shared multi-user deployment is a deliberate product decision)

---

## Security Posture Summary

| Concern | Mitigation |
|---|---|
| Credential leakage | OS keychain only; never in Git, logs, session state, `st.cache_data`, or source config |
| Local file exposure | Staging outside repo root; `assert_outside_repo()` test in CI |
| SSRF | HTTPS-only; reject RFC 1918 + loopback IPs after DNS resolution |
| Log exposure | Redact `Authorization`, `Cookie`, passwords, signed URLs from all log output |
| Schema drift | `SyncRecord.manifest_hash` comparison; `SCHEMA_DRIFT` warning halts before curated tables |
| Catalog bypass | `validate_catalog_entry()` required before `active_df`; failure → quarantine, not partial load |
| Small-cell disclosure | Suppress n < 10; round/bucket sparse intersections |
| Proprietary data in AI | `_assert_prompt_safe()` fires before cache path; `classification == "confidential"` blocks AI |
| Unauthorized export | Disable CSV export for confidential source-level tables |
| Retention | Cleanup command; 30-day raw / 90-day curated defaults pending data-owner confirmation |

---

*This design captures findings from Evidence documentation research, live manifest inspection at `dashboard.dev2.mybrainguide.org`, architectural review, and planning decisions made July 2026. See IDEAS.md #26 for the summary. Target: v0.4.0, after v0.3.0 analysis-quality release.*
