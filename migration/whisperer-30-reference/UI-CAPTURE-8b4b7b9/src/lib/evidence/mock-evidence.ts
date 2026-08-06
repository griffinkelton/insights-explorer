// Mock BrainGuide Evidence dashboard connector data.
// Mirrors the v0.4 connector design: manifest discovery -> allowlisted dataset
// catalog -> Playwright DOM extraction -> immutable SyncRecord metadata.

export const SMALL_CELL_MIN = 50;

export const EVIDENCE_SOURCE = {
  id: "evidence-braintree",
  label: "BrainGuide Evidence dashboard",
  baseUrl: "https://dashboard.dev2.mybrainguide.org",
  transport: "Playwright DOM extraction (Parquet paths return the SPA shell)",
  mode: "Phase A — manual sync, session-only, no retained raw extracts",
} as const;

export interface DatasetDescriptor {
  id: string;
  engine: "bigquery";
  description: string;
  allowlisted: boolean;
  rows: number;
  columns: string[];
  /** Rendered-table extraction is only feasible for aggregate datasets. */
  feasible: boolean;
  note?: string;
}

export const evidenceCatalog: DatasetDescriptor[] = [
  {
    id: "questionnaire_funnel",
    engine: "bigquery",
    description: "Funnel starts/completions by date",
    allowlisted: true,
    rows: 90,
    columns: ["date", "starts", "section_1", "section_2", "section_3", "finishes"],
    feasible: true,
  },
  {
    id: "questionnaire_agg",
    engine: "bigquery",
    description: "Aggregate questionnaire metrics by demographic cohort",
    allowlisted: true,
    rows: 412,
    columns: ["cohort_dimension", "cohort_value", "users", "starts", "finishes", "actions"],
    feasible: true,
  },
  {
    id: "questionnaire_trend",
    engine: "bigquery",
    description: "Trend data over time",
    allowlisted: true,
    rows: 26,
    columns: ["week", "starts", "finishes", "completion_rate"],
    feasible: true,
  },
  {
    id: "top_content_by_demographic",
    engine: "bigquery",
    description: "Content × demographic segments",
    allowlisted: true,
    rows: 640,
    columns: ["page_path", "cohort_dimension", "cohort_value", "views", "engaged_views"],
    feasible: true,
  },
  {
    id: "traffic_attribution",
    engine: "bigquery",
    description: "Traffic source attribution",
    allowlisted: true,
    rows: 148,
    columns: ["channel", "source_medium", "users", "starts", "finishes"],
    feasible: true,
  },
  {
    id: "questionnaire_responses",
    engine: "bigquery",
    description: "Individual response data",
    allowlisted: false,
    rows: 12988,
    columns: ["response_id", "…"],
    feasible: false,
    note: "Person-level — outside the aggregate-only allowlist. Never synced.",
  },
  {
    id: "questionnaire_journey_events",
    engine: "bigquery",
    description: "Individual journey events",
    allowlisted: false,
    rows: 214300,
    columns: ["session_id", "event", "ts"],
    feasible: false,
    note: "Event-level — requires the Gate 0B linkage decision.",
  },
  {
    id: "questionnaire_journey_monthly",
    engine: "bigquery",
    description: "Monthly journey aggregates",
    allowlisted: false,
    rows: 3,
    columns: ["month", "…"],
    feasible: true,
    note: "Aggregate but not yet on the approved allowlist.",
  },
];

export interface SyncRecord {
  datasetId: string;
  syncedAt: string;
  rowCount: number;
  manifestHash: string;
  schemaFingerprint: string;
  checksum: string;
  outcome: "synced" | "skipped" | "quarantined";
  reason?: string;
}

export const MANIFEST_HASH = "948fc2226955b507e5678a7ca158fb34";

export const lastSync: { at: string; manifestHash: string; records: SyncRecord[] } = {
  at: "2026-04-02T09:14:00Z",
  manifestHash: MANIFEST_HASH,
  records: [
    rec("questionnaire_funnel", 90, "synced"),
    rec("questionnaire_agg", 412, "synced"),
    rec("questionnaire_trend", 26, "synced"),
    rec("top_content_by_demographic", 640, "synced"),
    rec("traffic_attribution", 148, "synced"),
    {
      ...rec("questionnaire_journey_monthly", 0, "skipped"),
      reason: "Not on the approved dataset allowlist.",
    },
  ],
};

function rec(datasetId: string, rowCount: number, outcome: SyncRecord["outcome"]): SyncRecord {
  return {
    datasetId,
    syncedAt: "2026-04-02T09:14:00Z",
    rowCount,
    manifestHash: MANIFEST_HASH,
    schemaFingerprint: `sha256:${datasetId.slice(0, 6)}9f2c…`,
    checksum: `sha256:${datasetId.slice(-6)}c41a…`,
    outcome,
  };
}

/** Gate 2.2 — linkage coverage / feasibility report. */
export const linkageCoverage = {
  joinKey: "de-identified questionnaire session hash",
  ga4SessionsMatched: 0.78,
  cohortsBelowThreshold: ["Language: Spanish (finishes n=42)"],
  note: "78% of questionnaire completers join to a GA4 session ID. Un-joined completers skew mobile and paid social, so joined-only rates overstate desktop performance.",
};

export const evidenceGates = [
  { id: "2.1", label: "Evidence connector", state: "unlocked" as const },
  { id: "2.2", label: "Linkage coverage report", state: "unlocked" as const },
  { id: "2.3–2.6", label: "Equity reach, funnel, pathway, language access", state: "unlocked" as const },
  { id: "2.7–2.8", label: "Small-cell suppression, difference-attack protection", state: "phase-b" as const },
  { id: "3.1", label: "Survey cohort reporting", state: "phase-b" as const },
  { id: "1.6", label: "Retention", state: "blocked" as const },
  { id: "1.7", label: "Session funnel", state: "blocked" as const },
];

export function evidenceContext(): string {
  const synced = lastSync.records.filter((r) => r.outcome === "synced");
  return [
    `EVIDENCE SOURCE: ${EVIDENCE_SOURCE.label} (${EVIDENCE_SOURCE.baseUrl}) — ${EVIDENCE_SOURCE.mode}.`,
    `  Last manual sync ${lastSync.at}, manifest ${lastSync.manifestHash}.`,
    `  Datasets synced: ${synced.map((r) => `${r.datasetId} (${r.rowCount} rows)`).join(", ")}.`,
    `  Person-level and event-level datasets are NOT synced (aggregate-only allowlist).`,
    `  Linkage coverage: ${(linkageCoverage.ga4SessionsMatched * 100).toFixed(0)}% via ${linkageCoverage.joinKey}. ${linkageCoverage.note}`,
    `  Small-cell rule: cohorts under ${SMALL_CELL_MIN} are descriptive only and must not be reported as rates.`,
  ].join("\n");
}