"""Pydantic schemas for the Phase 1 API (spec §11).

Fields mirror ``utils.data_loader.DataQualityReport`` for the quality report
so the adapter in ``api/services/quality_service.py`` stays a thin mapping.
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


class DatasetContext(BaseModel):
    source: Literal["upload", "ga4", "drive"]
    filename: str
    row_count: int = Field(ge=0)
    date_range: DateRange
    columns: list[Column]
    filters: list[dict] = Field(default_factory=list)
    metrics: list[dict] = Field(default_factory=list)
    provenance: dict = Field(default_factory=dict)


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
