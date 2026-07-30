# 🔵 Evidence Dashboard Source Connector — Design Document

> **Status:** 🔵 Design / Planning — not yet scheduled
> **Related:** IDEAS.md #26 | **Predecessor:** v0.2.0 DataContext refactor
> **Target version:** v0.3.0 or later

---

## Concept Overview

A **first-class, admin-only data source connector** for Evidence-built static dashboards. Evidence is a static-site data-product framework that pre-compiles every query into Parquet files and lists them in a public `/data/manifest.json`. This connector resolves that manifest, downloads only allowlisted datasets, validates schemas, stages encrypted extracts, and exposes curated aggregate overlays alongside GA4 data — without attempting person-level attribution.

**What it is:** An approved, read-only connector for a specific class of data source (Evidence static dashboards) with strict source configuration, secure server-side secrets, an allowlisted dataset catalog, immutable ingestion metadata, and aggregate-only GA4 overlays.

**What it is NOT:** A generic "connect any website" tool, a credential-scraping engine, or a person-level linking feature.

---

## Product Boundary

Add a **Data Sources** area to Insights Explorer with two clearly separated concepts:

| Capability | Purpose | Recommendation |
|---|---|---|
| **GA4 source** | First-party web behavior and acquisition data | Keep existing connector |
| **Evidence dashboard source** | Approved dashboard datasets (questionnaire aggregates, demographic overlays) | Add now, read-only |
| **Joined analysis view** | Curated, documented aggregate overlays | Add after source validation |
| **Generic website connector** | Arbitrary URL, authentication, crawling, unknown formats | Do NOT add |

The UX begins with a "Connect Evidence dashboard" form. The implementation allows only approved connector types and approved hostnames. Never build a feature that accepts arbitrary URLs plus arbitrary credentials and fetches whatever it finds — that creates SSRF, credential-leakage, accidental extraction, and support risks.

---

## Safe Architecture

```
Admin UI (Insights Explorer)
    │
    │ creates source configuration; credentials entered once
    ▼
Server-side connector service
    ├── Host allowlist + HTTPS validation
    ├── Auth adapter (none / HTTP Basic / approved cookie flow)
    ├── Evidence manifest resolver
    ├── Parquet downloader + schema validator
    └── Audit log / sync metadata
    │
    ▼
Private encrypted staging store
    ├── Raw immutable extracts
    ├── Curated aggregate tables
    ├── Dataset catalog + lineage
    └── Join/mapping rules
    │
    ▼
Insights Explorer analysis layer
    ├── DataContext source
    ├── GA4 / Evidence / overlay modes
    └── Suppression and QA rules
```

Keep credentialed network access entirely **server-side**. In a Streamlit application, never place credentials in browser-rendered JavaScript, query parameters, downloadable configuration files, cached function arguments, or ordinary session-state fields.

Evidence's use of Parquet makes the connector technically appropriate for a controlled data-ingestion path, but its static deployment model does **not** itself make data safe to ingest or redistribute — the application still needs authorization, retention, audit, and access controls.

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

**Important caveat:** This is a dev/QA environment. The data pipeline may be replaced/reset when production `dashboard.mybrainguide.org` data is finalized. Always label dashboard-derived findings as provisional.

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
    enabled: bool = True
```

Example YAML configuration:

```yaml
display_name: MyBrainGuide Evidence Dashboard (dev)
base_url: https://dashboard.dev2.mybrainguide.org
allowed_host: dashboard.dev2.mybrainguide.org
connector_type: evidence_static
classification: confidential
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

Start with **manual sync only**. Enable scheduled refresh only after confirming the dashboard's refresh cadence, schema stability, and whether the development environment is expected to be reset or replaced.

---

## Credential Handling

Support only a small, deliberate set of authentication modes:

| Mode | When to use | Implementation |
|---|---|---|
| **No authentication** | Public, non-sensitive sources; explicitly approved hosts | Direct manifest fetch |
| **HTTP Basic Auth** | Server responds with `401` + `WWW-Authenticate: Basic` | Prompt for username/password; send via `Authorization` header |
| **Approved session-based sign-in** | Documented login flow; approved organizational access | Prompt for credentials; POST to login endpoint; store session cookie |
| **SSO/OAuth** | Deferred — requires enterprise identity model | Do NOT automate browser-login scraping |

**Storage:** Use OS keychain (`keyring` package) for a single-user local tool, or a managed secret store for shared deployment. The stored source record contains a secret reference such as `secret://insights-explorer/evidence/mybrainguide-dev`, never a username/password.

**Operational controls:**

- Encrypt secrets at rest
- Redact `Authorization`, `Cookie`, password fields, and signed URLs from logs
- Never use `st.cache_data` for credentialed responses or raw proprietary datasets
- Use short request timeouts, bounded redirects, response-size limits, and certificate verification
- Permit HTTPS only; reject private/reserved IP targets after DNS resolution (SSRF prevention)
- Require Admin/Data Steward role to add, edit, test, or sync a connector
- Show a confirmation banner before first extraction: "This imports proprietary dashboard data into Insights Explorer."

---

## Connector Contract

Define a small interface to prevent dashboard-specific behavior from leaking across the app:

```python
from typing import Protocol


class DataConnector(Protocol):
    def test_connection(self) -> ConnectionResult: ...
    def discover_datasets(self) -> list[DatasetDescriptor]: ...
    def preview_schema(self, dataset_id: str) -> SchemaPreview: ...
    def sync(self, selected_datasets: list[str]) -> SyncResult: ...
```

Then implement:

```python
class EvidenceStaticConnector:
    """Approved Evidence static-data connector.

    Resolves a manifest, permits only allowlisted Parquet assets,
    validates schemas, and writes immutable extracts.
    """

    def __init__(self, config: EvidenceSourceConfig, secret: str | None = None):
        self.config = config
        self._auth = self._build_auth(secret)

    def test_connection(self) -> ConnectionResult:
        """Fetch manifest; return success + dataset count or failure + reason."""
        ...

    def discover_datasets(self) -> list[DatasetDescriptor]:
        """Parse manifest.json; return {name, current_hash, size_bytes, columns}."""
        ...

    def preview_schema(self, dataset_id: str) -> SchemaPreview:
        """Download and inspect a single Parquet file; return column names + types."""
        ...

    def sync(self, selected_datasets: list[str]) -> SyncResult:
        """Resolve paths, download, validate, checksum, and stage each dataset."""
        ...
```

**Sync pipeline steps:**

1. Fetch the stable manifest endpoint
2. Parse only expected manifest structures
3. Resolve only allowlisted dataset names and only same-origin asset URLs
4. Download the current Parquet asset
5. Verify content type, file size, and expected schema
6. Store a checksum plus immutable extract metadata
7. Transform only approved datasets into curated aggregates
8. Return a data-quality report — not raw data directly to the UI

**Change detection:** Store the last-seen hash per dataset in metadata. On each sync, compare; only re-download and re-process datasets whose hash changed. This gives free incremental sync without needing an API contract.

---

## Dataset Catalog

A catalog between raw extraction and analysis becomes the authoritative definition of what can be used and how:

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

This lets the application reject a newly exposed dashboard file unless it is intentionally cataloged, reviewed, and documented.

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
- Pre/post site-relaunch trends

### Important Limitations

- **Never** label any resulting ratio as individual conversion unless GA4 and the Evidence source have an approved, consented, persistent linkage key
- Without that, describe results as **aggregate association**, not a user journey or causal relationship
- Evidence questionnaire demographics are self-reported, not pulled from GA4 — treat them as distinct from GA4 demographic reporting
- Normalize URL paths before joining: lower-case, remove query strings, reconcile trailing slashes, map old/new-site URLs to a canonical `content_key`
- The new site launched around March 2026 and shares the GA4 property with the prior site — include a pre/post-relaunch date flag

---

## Privacy and Proprietary-Data Controls

"De-identified" does not mean "safe to expose without controls." The primary risks:

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
- Audit metadata: source, user, sync time, dataset, manifest path/hash, row count, schema fingerprint, and outcome
- Default AI/chat features to **exclude confidential Evidence rows** until there is an explicit approved policy for model use and redaction

---

## DataContext Integration Considerations

Do not force GA4 and Evidence into the same raw DataFrame immediately. A future `DataContext` revision could add source-aware fields:

```python
@dataclass(frozen=True)
class DataContext:
    # ... existing fields from v0.2.0 ...
    source_kind: Literal["ga4", "evidence", "overlay"] = "ga4"
    classification: Literal["internal", "confidential"] = "internal"
    qa_status: Literal["validated", "provisional"] = "validated"
```

For overlay analysis, `raw_df` should be the curated joined table — not a giant unfiltered union of both raw sources. Preserve input lineage in provenance:

```python
provenance = (
    "ga4:property-request:ab12cd34",
    "evidence:questionnaire_funnel:manifest-hash:ef56gh78",
    "mapping:content-key:v1",
    "join:date+content-key+language",
)
```

Every cache key should include the source IDs and versions of **both inputs**, mapping version, and suppression-policy version:

```python
overlay_cache_key = (
    ga4_ctx.source_id,
    ga4_ctx.version,
    evidence_ctx.source_id,
    evidence_ctx.version,
    "content-key-mapping:v1",
    "suppression:v1",
)
```

> **⚠️ Note:** The `source_kind`, `classification`, and `qa_status` fields expand the DataContext surface beyond what v0.2.0 Phase 1 just finalized. These should be optional/defaulted when introduced, and added in a future DataContext revision — not retrofitted into the current migration.

---

## Delivery Plan

### Phase A — Validate Source

- Build a non-production command or admin-only test screen
- Test authentication without storing secrets in code
- Fetch manifest and display dataset names, current asset hashes, sizes, and schemas
- Do NOT yet expose data in the Explorer
- Confirm data ownership, permitted use, retention period, and approved users

### Phase B — Secure Ingestion

- Add `EvidenceStaticConnector` class implementing the `DataConnector` protocol
- Add secret-manager integration (`keyring` for local, or managed store for shared)
- Implement host allowlist, same-origin enforcement, size limits, logging redaction, schema validation
- Save encrypted/private raw extracts and sync metadata
- Support only manual sync and only a short dataset allowlist

### Phase C — Curated Data Products

- Define `metrics.yml` / dataset catalog
- Create canonical `content_key` mapping and version it
- Build quality checks: duplicate grain, missing dates, unexpected columns, row-count drift, unmatched content keys, low-cell suppression
- Produce curated aggregate tables only — never serve raw extracts to the UI

### Phase D — Explorer Overlay

- Add source selector: **GA4**, **Evidence**, **GA4 + Evidence overlay**
- Add a visible methodology drawer explaining join grain, limitations, QA status, source timestamp, and suppression
- Add charts designed for aggregate interpretation, not individual user-path claims
- Keep exports disabled by default for confidential overlay data

### Phase E — Controlled Scheduling

- Add scheduled refresh after two or more successful manual syncs
- Alert on schema changes, missing datasets, unexpected row-count deltas, failed authentication, or stale data
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

---

## Security Posture Summary

| Concern | Mitigation |
|---|---|
| Credential leakage | Secrets in OS keychain/secret manager only; never in Git, logs, session state, or `st.cache_data` |
| SSRF | HTTPS-only; reject private/reserved IPs after DNS resolution |
| Log exposure | Redact `Authorization`, `Cookie`, passwords, signed URLs from all log output |
| Small-cell disclosure | Suppress n < 10; round/bucket sparse intersections |
| Proprietary data in AI | Default AI features to exclude confidential Evidence rows |
| Unauthorized export | Disable CSV export for confidential source-level tables |
| Schema drift | Hash-based change detection; admin approval required for schema changes |
| Stale data | Audit metadata records sync time, manifest hash, row count per extract |

---

*This design captures findings from Evidence documentation research, live manifest inspection at `dashboard.dev2.mybrainguide.org`, and architectural review. See IDEAS.md #26 for the summary. Not yet on any sprint plan.*
