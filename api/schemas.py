"""Pydantic schemas for the Phase 1 API (spec §11).

Fields mirror ``utils.data_loader.DataQualityReport`` for the quality report
so the adapter in ``api/services/quality_service.py`` stays a thin mapping.
Phase 2 (spec Task 7): structured ``DatasetWarning`` surfaced end-to-end on
``DatasetContext.warnings`` (confirmed P2 — truncation is user-visible data
loss, not a server-log-only concern).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start: date | None = None
    end: date | None = None


class Column(BaseModel):
    name: str
    type: Literal["date", "number", "string", "boolean", "unknown"]
    nullable: bool


class DatasetWarning(BaseModel):
    """Structured non-fatal data warning (confirmed + refined P2, 2026-08-06).

    Phase 3 (D4): ``identifiers_removed_for_ai`` carries the scrubbed column
    names so the user sees exactly what was withheld before AI analysis.
    """

    code: Literal["rows_truncated", "identifiers_removed_for_ai"]
    message: str
    original_row_count: int | None = None
    loaded_row_count: int = 0
    removed_columns: list[str] = Field(default_factory=list)


class DatasetContext(BaseModel):
    source: Literal["upload", "ga4", "drive"]
    filename: str
    row_count: int = Field(ge=0)
    date_range: DateRange
    columns: list[Column]
    filters: list[dict] = Field(default_factory=list)
    metrics: list[dict] = Field(default_factory=list)
    provenance: dict = Field(default_factory=dict)
    warnings: list[DatasetWarning] = Field(default_factory=list)


class UploadResponse(BaseModel):
    dataset: DatasetContext


class DataPreviewResponse(BaseModel):
    dataset: DatasetContext
    rows: list[dict]


class QualityReport(BaseModel):
    grade: Literal["A", "B", "C", "D", "E", "F"]
    completeness_pct: float
    duplicate_pct: float
    duplicate_count: int
    outlier_count: int
    date_range_days: int | None
    date_gaps: int
    column_count: int
    missing_columns: list[str]
    warnings: list[str]


class APIError(BaseModel):
    detail: str


# ── Phase 3 — AI / analysis (spec phase-3-ai-analysis.md) ──────────────────


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)  # D12: 4k chars/message


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)  # D12: 20 msgs
    mode: Literal["chat", "summary"] = "chat"


class SummaryRequest(BaseModel):
    mode: Literal["summary"] = "summary"


class UsageSummary(BaseModel):
    input_tokens: int
    output_tokens: int
    thoughts_token_count: int
    total_token_count: int


class SummaryResponse(BaseModel):
    summary: str
    model: str
    usage: UsageSummary


class ForecastRequest(BaseModel):
    date_col: str | None = None  # auto-detect via find_date_column when omitted
    metric_col: str
    periods: int = Field(default=30, ge=1, le=365)


class ForecastPoint(BaseModel):
    date: str
    value: float | None = None
    lower: float | None = None
    upper: float | None = None


class ForecastResponse(BaseModel):
    metric_col: str
    periods: int
    summary: str  # build_forecast_summary(result)
    forecast_points: list[ForecastPoint] = Field(default_factory=list)
    insufficient_data: bool = False


class FunnelRequest(BaseModel):
    page_col: str | None = None  # auto-detect when omitted
    metric_col: str
    steps: list[str] = Field(min_length=2)


class FunnelResponse(BaseModel):
    steps: list[str]
    values: list[float]


# ── Phase 5 — GA4 + Drive (spec phase-5-ga4-drive.md Task 1/2) ────────────


class OAuthConnectRequest(BaseModel):
    connection: Literal["ga4", "drive"] = "ga4"  # D2 — two separate consents, one client


class Ga4ConnectResponse(BaseModel):
    authorization_url: str  # snake_case locked (F4 §11)


class Ga4StatusResponse(BaseModel):
    connected: bool


class DriveStatusResponse(BaseModel):
    configured: bool


class DrivePickerTokenResponse(BaseModel):
    """JIT Picker bootstrap — short-lived access token + app id + active request id.

    The token is browser-memory-only (Task 4): never persisted, never revoked on
    Picker close. ``request_id`` must be echoed back on ``/drive/download``.
    """

    access_token: str
    expires_at: str | None = None
    app_id: str | None = None
    request_id: str


class DriveDownloadRequest(BaseModel):
    request_id: (
        str  # must match the active server/session picker request (stale/duplicate -> typed error)
    )
    file_id: str  # the ONLY authority input — client filename/MIME/size ignored


class UsageResponse(BaseModel):
    request_count: int
    success_count: int
    failure_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    thought_tokens: int
    cached_tokens: int
    tool_tokens: int
    estimated_prompt_tokens: int
    context_trimmed: int
    identifiers_removed: int
    avg_ttft_ms: int | None  # mean time-to-first-token (observability only)
    avg_ttlt_ms: int | None  # mean time-to-last-token (observability only)
    by_request_type: dict[str, int]
    by_model: dict[str, int]
