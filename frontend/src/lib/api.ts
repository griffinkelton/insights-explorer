// Phase 4 Task 3 — the single API-base module (Phase 1–3 FastAPI contract).
// All calls are deployment-neutral: the Vite dev proxy and Phase 6 same-origin
// serving both resolve "/api/v1" relative. credentials: "include" carries the
// HttpOnly session cookie — the ONLY client credential (track A).
//
// The backend wire is snake_case; components consume camelCase. Normalization
// happens HERE, once, at the boundary (track B / drift matrix) — never in
// components or the store.
import type {
  ApiError,
  ChatRequest,
  Column,
  DataPreviewResponse,
  DataSource,
  DatasetContext,
  DateRange,
  DriveDownloadRequest,
  DriveDownloadResponse,
  DrivePickerTokenResponse,
  DriveStatusResponse,
  ForecastResponse,
  FunnelResponse,
  Ga4ConnectResponse,
  Ga4StatusResponse,
  OAuthConnection,
  QualityReport,
  SummaryResponse,
  UploadResponse,
  UsageResponse,
} from "./api-types";

export const API_BASE = "/api/v1";

type WireRecord = Record<string, unknown>;

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  try {
    return await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      ...init,
    });
  } catch (err) {
    // Cross-realm test environments (vitest/jsdom) reject AbortSignals created
    // by a different AbortController realm than undici's fetch. Retry without
    // the signal — abort/cancel still works in real browsers (same realm).
    if (
      init.signal &&
      err instanceof TypeError &&
      /signal/i.test(String(err.message))
    ) {
      const rest = { ...init };
      delete rest.signal;
      return fetch(`${API_BASE}${path}`, {
        credentials: "include",
        ...rest,
      });
    }
    throw err;
  }
}

export class ApiRequestError extends Error {
  constructor(
    readonly status: number,
    detail: string,
    /** Phase 5 — server typed error code (e.g. ga4_quota_exhausted). */
    readonly code?: string,
  ) {
    super(detail);
    this.name = "ApiRequestError";
  }
}

/** Phase 5 — REST errors may carry a structured { code, message, retryable } detail. */
function parseErrorDetail(body: ApiError | undefined, fallback: string): { detail: string; code?: string } {
  const raw = body?.detail;
  if (typeof raw === "string") return { detail: raw || fallback };
  if (raw && typeof raw === "object") {
    return {
      detail: raw.message || fallback,
      code: raw.code,
    };
  }
  return { detail: fallback };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await apiFetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    const parsed = parseErrorDetail(body as ApiError | undefined, "Request failed");
    throw new ApiRequestError(res.status, parsed.detail, parsed.code);
  }
  return res.json() as Promise<T>;
}

// ── Boundary normalizers: snake_case wire → camelCase domain ───────────────

function normDateRange(r: WireRecord | null | undefined): DateRange {
  return {
    start: (r?.start as string | undefined) ?? null,
    end: (r?.end as string | undefined) ?? null,
  };
}

function normalizeDatasetContext(d: WireRecord): DatasetContext {
  return {
    source: (d.source as DataSource) ?? "upload",
    filename: String(d.filename ?? ""),
    rowCount: Number(d.row_count ?? 0),
    dateRange: normDateRange(d.date_range as WireRecord | null | undefined),
    columns: Array.isArray(d.columns) ? (d.columns as Column[]) : [],
    filters: Array.isArray(d.filters) ? (d.filters as Record<string, unknown>[]) : [],
    metrics: Array.isArray(d.metrics) ? (d.metrics as Record<string, unknown>[]) : [],
    provenance: (d.provenance as Record<string, unknown>) ?? {},
    warnings: Array.isArray(d.warnings)
      ? d.warnings.map((w) => {
          const ww = w as WireRecord;
          return {
            code: ww.code as DatasetContext["warnings"][number]["code"],
            message: String(ww.message ?? ""),
            originalRowCount: ww.original_row_count == null ? null : Number(ww.original_row_count),
            loadedRowCount: Number(ww.loaded_row_count ?? 0),
            removedColumns: Array.isArray(ww.removed_columns) ? (ww.removed_columns as string[]) : [],
          };
        })
      : [],
  };
}

function normalizeQualityReport(r: WireRecord): QualityReport {
  return {
    grade: (r.grade as QualityReport["grade"]) ?? "F",
    completenessPct: Number(r.completeness_pct ?? 0),
    duplicatePct: Number(r.duplicate_pct ?? 0),
    duplicateCount: Number(r.duplicate_count ?? 0),
    outlierCount: Number(r.outlier_count ?? 0),
    dateRangeDays: r.date_range_days == null ? null : Number(r.date_range_days),
    dateGaps: Number(r.date_gaps ?? 0),
    columnCount: Number(r.column_count ?? 0),
    missingColumns: Array.isArray(r.missing_columns) ? (r.missing_columns as string[]) : [],
    warnings: Array.isArray(r.warnings) ? (r.warnings as string[]) : [],
  };
}

function normalizeUsage(r: WireRecord): UsageResponse {
  return {
    requestCount: Number(r.request_count ?? 0),
    successCount: Number(r.success_count ?? 0),
    failureCount: Number(r.failure_count ?? 0),
    inputTokens: Number(r.input_tokens ?? 0),
    outputTokens: Number(r.output_tokens ?? 0),
    totalTokens: Number(r.total_tokens ?? 0),
    thoughtTokens: Number(r.thought_tokens ?? 0),
    cachedTokens: Number(r.cached_tokens ?? 0),
    toolTokens: Number(r.tool_tokens ?? 0),
    estimatedPromptTokens: Number(r.estimated_prompt_tokens ?? 0),
    contextTrimmed: Number(r.context_trimmed ?? 0),
    identifiersRemoved: Number(r.identifiers_removed ?? 0),
    avgTtftMs: r.avg_ttft_ms == null ? null : Number(r.avg_ttft_ms),
    avgTtltMs: r.avg_ttlt_ms == null ? null : Number(r.avg_ttlt_ms),
    byRequestType: (r.by_request_type as Record<string, number>) ?? {},
    byModel: (r.by_model as Record<string, number>) ?? {},
  };
}

function normalizeSummary(r: WireRecord): SummaryResponse {
  const u = (r.usage as WireRecord) ?? {};
  return {
    summary: String(r.summary ?? ""),
    model: String(r.model ?? ""),
    usage: {
      inputTokens: Number(u.input_tokens ?? 0),
      outputTokens: Number(u.output_tokens ?? 0),
      thoughtsTokenCount: Number(u.thoughts_token_count ?? 0),
      totalTokenCount: Number(u.total_token_count ?? 0),
    },
  };
}

function normalizeForecast(r: WireRecord): ForecastResponse {
  return {
    metricCol: String(r.metric_col ?? ""),
    periods: Number(r.periods ?? 0),
    summary: String(r.summary ?? ""),
    forecastPoints: Array.isArray(r.forecast_points)
      ? (r.forecast_points as ForecastResponse["forecastPoints"])
      : [],
    insufficientData: Boolean(r.insufficient_data),
  };
}

export const api = {
  upload: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append("file", file);
    const r = await request<WireRecord>("/upload", { method: "POST", body: form });
    return { dataset: normalizeDatasetContext((r.dataset as WireRecord) ?? {}) };
  },
  context: async (): Promise<DatasetContext> =>
    normalizeDatasetContext(await request<WireRecord>("/data/context")),
  preview: async (): Promise<DataPreviewResponse> => {
    const r = await request<WireRecord>("/data/preview");
    return {
      dataset: normalizeDatasetContext((r.dataset as WireRecord) ?? {}),
      rows: Array.isArray(r.rows) ? (r.rows as Record<string, unknown>[]) : [],
    };
  },
  quality: async (): Promise<QualityReport> =>
    normalizeQualityReport(await request<WireRecord>("/data/quality")),
  clear: () => request<{ status: string }>("/data/clear", { method: "POST" }),
  chatStream: (body: ChatRequest, signal?: AbortSignal) =>
    apiFetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    }),
  summary: async (): Promise<SummaryResponse> =>
    normalizeSummary(
      await request<WireRecord>("/analysis/summary", {
        method: "POST",
        body: JSON.stringify({ mode: "summary" }),
      }),
    ),
  forecast: async (metricCol: string, periods = 30): Promise<ForecastResponse> =>
    normalizeForecast(
      await request<WireRecord>("/analysis/forecast", {
        method: "POST",
        body: JSON.stringify({ metric_col: metricCol, periods }),
      }),
    ),
  funnel: (metricCol: string, steps: string[]) =>
    request<FunnelResponse>("/analysis/funnel", {
      method: "POST",
      body: JSON.stringify({ metric_col: metricCol, steps }),
    }),
  usage: async (): Promise<UsageResponse> =>
    normalizeUsage(await request<WireRecord>("/ai/usage")),
  // ── Phase 5 — GA4 + Drive (spec phase-5-ga4-drive.md Task 1/2/4) ──────
  ga4Connect: (connection: OAuthConnection = "ga4"): Promise<Ga4ConnectResponse> =>
    request<WireRecord>("/ga4/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ connection }),
    }).then((r) => ({ authorizationUrl: String(r.authorization_url ?? "") })),
  ga4Status: async (): Promise<Ga4StatusResponse> => {
    const r = await request<WireRecord>("/ga4/status");
    return { connected: Boolean(r.connected) };
  },
  ga4Disconnect: () => request<{ status: string }>("/ga4/disconnect", { method: "POST" }),
  ga4Pull: async (): Promise<UploadResponse> => {
    const r = await request<WireRecord>("/ga4/pull", { method: "POST" });
    return { dataset: normalizeDatasetContext((r.dataset as WireRecord) ?? {}) };
  },
  driveStatus: async (): Promise<DriveStatusResponse> => {
    const r = await request<WireRecord>("/drive/status");
    return { configured: Boolean(r.configured) };
  },
  drivePickerToken: async (): Promise<DrivePickerTokenResponse> => {
    const r = await request<WireRecord>("/drive/picker-token", { method: "POST" });
    return {
      accessToken: String(r.access_token ?? ""),
      expiresAt: r.expires_at == null ? null : String(r.expires_at),
      appId: r.app_id == null ? null : String(r.app_id),
      requestId: String(r.request_id ?? ""),
    };
  },
  driveDownload: async (req: DriveDownloadRequest): Promise<DriveDownloadResponse> => {
    const r = await request<WireRecord>("/drive/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ request_id: req.requestId, file_id: req.fileId }),
    });
    return { dataset: normalizeDatasetContext((r.dataset as WireRecord) ?? {}) };
  },
};

/** Normalized source summary for the store (boundary, track B / F4 §11). */
export function setSourceFromApi(payload: { dataset: DatasetContext }): {
  source: DataSource;
  filename: string;
  rowCount: number;
  context: DatasetContext;
} {
  const d = payload.dataset;
  return { source: d.source, filename: d.filename, rowCount: d.rowCount, context: d };
}

/** Server typed error code → user-facing message (drift row 2; Task 3 table;
 *  Phase 5 ga4_* / drive_* codes). */
export function mapApiError(status: number, detail?: string, code?: string): string {
  switch (code) {
    case "ga4_not_configured":
    case "drive_not_configured":
      return "Google connections are not configured on this server yet.";
    case "ga4_connection_required":
    case "drive_connection_required":
      return "Connect the source first, then try again.";
    case "ga4_reconnect_required":
    case "drive_reconnect_required":
      return "Your Google connection needs to be refreshed — reconnect and try again.";
    case "ga4_access_denied":
      return "Access to that Google Analytics property is denied.";
    case "ga4_property_unavailable":
      return "The Google Analytics property is unavailable. Check the configured property.";
    case "ga4_quota_exhausted":
      return "Google Analytics reporting capacity is exhausted for now. Try again later.";
    case "ga4_rate_limited":
      return "Google Analytics is rate-limiting requests. Try again shortly.";
    case "ga4_provider_unavailable":
      return "Google Analytics is temporarily unavailable. Try again shortly.";
    case "ga4_timeout":
      return "Google Analytics took too long to respond. Try again.";
    case "ga4_empty_report":
      return "The Google Analytics property returned no rows for the report period.";
    case "stale_picker_request":
      return "That file selection has expired — open the picker again.";
    case "workspace_export_required":
      return "Google Sheets import isn't supported yet — choose a CSV or Excel file.";
    case "unsupported_type":
      return "Unsupported file type — choose a CSV, XLSX, or XLS file.";
    case "too_large":
      return "File too large — the import limit is 100 MB.";
    case "file_not_available":
      return "That Drive file is no longer available.";
    case "download_not_allowed":
    case "access_denied":
      return "Access to that Drive file was denied.";
    case "drive_parse_failed":
      return detail || "Couldn't read the downloaded file.";
  }
  switch (status) {
    case 409:
      return "No active dataset. Upload a file to get started.";
    case 410:
      return "Dataset session has expired — please upload the file again.";
    case 413:
      return "File too large — the browser upload cap is 25 MB. Try a smaller file or Drive import.";
    case 415:
      return "Unsupported file type — upload a CSV, XLSX, or XLS file.";
    case 422:
      return detail || "Couldn't read that file. Please check the format and try again.";
    case 503:
      return "AI features are unavailable right now — check that the Gemini API key is configured.";
    default:
      return detail || "Something went wrong. Please try again.";
  }
}
