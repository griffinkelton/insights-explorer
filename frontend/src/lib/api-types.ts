// Phase 4 Task 3 — types derived from the FastAPI OpenAPI contract
// (api/schemas.py). The store never imports types from mock fixtures (drift row 12).

export type DataSource = "upload" | "ga4" | "drive";

export interface DateRange {
  start: string | null;
  end: string | null;
}

export interface Column {
  name: string;
  type: "date" | "number" | "string" | "boolean" | "unknown";
  nullable: boolean;
}

export interface DatasetWarning {
  code: "rows_truncated" | "identifiers_removed_for_ai";
  message: string;
  originalRowCount: number | null;
  loadedRowCount: number;
  removedColumns: string[];
}

export interface DatasetContext {
  source: DataSource;
  filename: string;
  rowCount: number;
  dateRange: DateRange;
  columns: Column[];
  filters: Record<string, unknown>[];
  metrics: Record<string, unknown>[];
  provenance: Record<string, unknown>;
  warnings: DatasetWarning[];
}

export interface UploadResponse {
  dataset: DatasetContext;
}

export interface DataPreviewResponse {
  dataset: DatasetContext;
  rows: Record<string, unknown>[];
}

export interface QualityReport {
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

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  mode: "chat" | "summary";
}

export interface SummaryResponse {
  summary: string;
  model: string;
  usage: {
    inputTokens: number;
    outputTokens: number;
    thoughtsTokenCount: number;
    totalTokenCount: number;
  };
}

export interface ForecastPoint {
  date: string;
  value: number | null;
  lower: number | null;
  upper: number | null;
}

export interface ForecastResponse {
  metricCol: string;
  periods: number;
  summary: string;
  forecastPoints: ForecastPoint[];
  insufficientData: boolean;
}

export interface FunnelResponse {
  steps: string[];
  values: number[];
}

export interface UsageResponse {
  requestCount: number;
  successCount: number;
  failureCount: number;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  thoughtTokens: number;
  cachedTokens: number;
  toolTokens: number;
  estimatedPromptTokens: number;
  contextTrimmed: number;
  identifiersRemoved: number;
  avgTtftMs: number | null;
  avgTtltMs: number | null;
  byRequestType: Record<string, number>;
  byModel: Record<string, number>;
}

export interface ApiError {
  detail: string;
}
