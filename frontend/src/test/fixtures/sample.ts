// TEST-ONLY fixtures — never imported from production code (drift row 12,
// prototype quarantine). Shapes mirror the real FastAPI wire (snake_case) —
// api.ts normalizes to camelCase at the boundary.
import type { UsageResponse } from "@/lib/api-types";

export const sampleContextWire = {
  source: "upload",
  filename: "sessions.csv",
  row_count: 1240,
  date_range: { start: "2026-01-01", end: "2026-05-31" },
  columns: [
    { name: "date", type: "date", nullable: false },
    { name: "sessions", type: "number", nullable: false },
    { name: "channel", type: "string", nullable: true },
  ],
  filters: [],
  metrics: [],
  provenance: { uploaded_at: "2026-08-06T12:00:00Z" },
  warnings: [],
};

export const sampleUploadWire = { dataset: sampleContextWire };

// Phase 5 — GA4 first-pull + Drive download wire fixtures (Task 6 MSW).
export const sampleGa4ContextWire = {
  ...sampleContextWire,
  source: "ga4",
  filename: "ga4-123456789.csv",
  row_count: 90,
  date_range: { start: "2026-05-08", end: "2026-08-05" },
  metrics: [
    { id: "sessions", name: "sessions", contract_row: "1", validation_status: "provisional" },
    { id: "totalUsers", name: "totalUsers", contract_row: "1", validation_status: "provisional" },
    { id: "engagedSessions", name: "engagedSessions", contract_row: "1", validation_status: "provisional" },
    { id: "engagementRate", name: "engagementRate", contract_row: "2", validation_status: "provisional" },
    { id: "bounceRate", name: "bounceRate", contract_row: "2", validation_status: "provisional" },
    { id: "questionnaire_start_count", name: "questionnaire_start_count", contract_row: "3", validation_status: "unavailable" },
    { id: "questionnaire_completion_rate", name: "questionnaire_completion_rate", contract_row: "4", validation_status: "unavailable" },
    { id: "post_questionnaire_action_rate", name: "post_questionnaire_action_rate", contract_row: "5", validation_status: "unavailable" },
  ],
  provenance: {
    source: "ga4",
    property_id: "123456789",
    dimensions: ["date"],
    metrics: ["sessions", "totalUsers", "engagedSessions", "engagementRate", "bounceRate"],
    start_date: "90daysAgo",
    end_date: "yesterday",
    page_count: 1,
    row_count: 90,
    pulled_at: "2026-08-06T20:45:00Z",
    quota_observed: true,
  },
};

export const sampleGa4PullWire = { dataset: sampleGa4ContextWire };

export const sampleDriveDownloadWire = {
  dataset: { ...sampleContextWire, source: "drive", filename: "monthly-report.csv" },
};

export const samplePreviewWire = {
  dataset: sampleContextWire,
  rows: [
    { date: "2026-01-01", sessions: 120, channel: "organic" },
    { date: "2026-01-02", sessions: 142, channel: "direct" },
    { date: "2026-01-03", sessions: 131, channel: "organic" },
  ],
};

export const sampleQualityWire = {
  grade: "B",
  completeness_pct: 96.4,
  duplicate_pct: 0.4,
  duplicate_count: 5,
  outlier_count: 12,
  date_range_days: 151,
  date_gaps: 2,
  column_count: 12,
  missing_columns: ["utm_campaign"],
  warnings: ["2 missing dates detected", "utm_campaign has 3.6% missing values"],
};

export const sampleUsageWire = {
  request_count: 1,
  success_count: 1,
  failure_count: 0,
  input_tokens: 420,
  output_tokens: 180,
  total_tokens: 600,
  thought_tokens: 0,
  cached_tokens: 0,
  tool_tokens: 0,
  estimated_prompt_tokens: 410,
  context_trimmed: 0,
  identifiers_removed: 0,
  avg_ttft_ms: null,
  avg_ttlt_ms: null,
  by_request_type: { chat: 1 },
  by_model: { "gemini-2.5-flash": 1 },
};

/** Expected camelCase shape after api.ts normalization (for assertions). */
export const expectedQuality: QualityReportShape = {
  grade: "B",
  completenessPct: 96.4,
  duplicatePct: 0.4,
  duplicateCount: 5,
  outlierCount: 12,
  dateRangeDays: 151,
  dateGaps: 2,
  columnCount: 12,
  missingColumns: ["utm_campaign"],
  warnings: ["2 missing dates detected", "utm_campaign has 3.6% missing values"],
};

export const expectedUsage: UsageResponse = {
  requestCount: 1,
  successCount: 1,
  failureCount: 0,
  inputTokens: 420,
  outputTokens: 180,
  totalTokens: 600,
  thoughtTokens: 0,
  cachedTokens: 0,
  toolTokens: 0,
  estimatedPromptTokens: 410,
  contextTrimmed: 0,
  identifiersRemoved: 0,
  avgTtftMs: null,
  avgTtltMs: null,
  byRequestType: { chat: 1 },
  byModel: { "gemini-2.5-flash": 1 },
};

interface QualityReportShape {
  grade: "A" | "B" | "C" | "D" | "E" | "F";
  completenessPct: number;
  duplicatePct: number;
  duplicateCount: number;
  outlierCount: number;
  dateRangeDays: number | null;
  dateGaps: number;
  columnCount: number;
  missingColumns: string[];
  warnings: string[];
}

export const csvFile = (name = "sessions.csv", size = 256) =>
  new File([new ArrayBuffer(size)], name, { type: "text/csv" });
