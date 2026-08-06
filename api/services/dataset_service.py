"""Dataset service: parsing/context adapter + policy-real Clear Data.

Parsing is an **adapter boundary** to ``utils/data_loader.py`` — do not
duplicate its validation/error taxonomy (spec §8/§Task 7). Phase 2 replaces
the temporary parser with ``utils/data_loader.load_file()`` and surfaces its
row-truncation warning as a structured ``DatasetWarning``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd

from utils.data_loader import load_file

from api.schemas import Column, DatasetContext, DatasetWarning, DateRange
from api.stores.dataset_store import datasets
from api.stores.session_store import AppSession, UsageLedger


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    return "string"


class _NamedBytesIO(BytesIO):
    """BytesIO with a .name — the minimal file-like contract load_file needs."""

    def __init__(self, data: bytes, name: str) -> None:
        super().__init__(data)
        self.name = name


class UploadError(Exception):
    """Typed upload failure; route maps to the Phase 1 HTTP status codes."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def parse_uploaded_file(
    filename: str,
    content: bytes,
) -> tuple[pd.DataFrame, DatasetWarning | None]:
    """Adapter over utils/data_loader.load_file() — single parser, one taxonomy.

    Returns (df, warning) where warning is a structured DatasetWarning when rows
    were truncated (confirmed P2), or None. Errors raise UploadError with the
    Phase 1 status-code mapping.
    """
    df, error, warning = load_file(_NamedBytesIO(content, filename))
    if error is not None:
        status = _error_status(error, filename)
        raise UploadError(status, error)
    structured = None
    if warning is not None:
        structured = DatasetWarning(
            code="rows_truncated",
            message=warning,
            original_row_count=_extract_original_row_count(warning),
            loaded_row_count=len(df),
        )
    return df, structured


def _extract_original_row_count(warning: str) -> int | None:
    """Best-effort parse of the loader's truncation notice; None if format changes."""
    match = re.search(r"Dataset has ([0-9,]+) rows", warning)
    return int(match.group(1).replace(",", "")) if match else None


def _error_status(error: str, filename: str) -> int:
    suffix = Path(filename).suffix.lower()
    if "Unsupported file type" in error or suffix not in {".csv", ".xlsx", ".xls"}:
        return 415
    if "empty" in error.lower():
        return 400
    if "too large" in error.lower():
        return 413
    return 422  # "We couldn't read this file…"


def make_context(
    df: pd.DataFrame,
    *,
    source: str,
    filename: str,
    warnings: list[DatasetWarning] | None = None,
) -> DatasetContext:
    date_columns = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    start = end = None
    if date_columns:
        values = df[date_columns[0]].dropna()
        if not values.empty:
            start = values.min().date()
            end = values.max().date()
    return DatasetContext(
        source=source,
        filename=filename,
        row_count=len(df),
        date_range=DateRange(start=start, end=end),
        columns=[
            Column(name=str(c), type=infer_column_type(df[c]), nullable=bool(df[c].isna().any()))
            for c in df.columns
        ],
        provenance={"created_at": datetime.now(timezone.utc).isoformat(), "transformations": []},
        warnings=warnings or [],
    )


def clear_dataset_state(session: AppSession) -> None:
    """Policy-real Clear Data (retention-policy §5) — an explicit method, never
    an implied metadata.clear(). Establishes the cleanup namespace now so later
    phases don't invent inconsistent cleanup behavior. Preserves only the durable
    GA4 connection (ga4_credentials) and the theme preference; transient OAuth
    flow state is cleared."""
    # Active dataset + derived artifacts.
    if session.dataset_id:
        datasets.remove(session.dataset_id)
        session.dataset_id = None
    session.metadata.pop("filters", None)  # Phase 2+: filter state
    session.metadata.pop("metrics", None)  # Phase 2+: metric state
    session.metadata.pop("preview_cache", None)  # preview rows cache
    session.metadata.pop("quality_cache", None)  # quality/analysis cache
    session.metadata.pop("summary", None)  # Phase 3: summary context
    session.metadata.pop("chat_history", None)  # Phase 3: chat context
    session.metadata.pop("usage_counters", None)  # Phase 3: legacy usage counters
    session.usage_ledger = UsageLedger()  # Phase 3: AI ledger is dataset-derived state (D5)
    session.metadata.pop("export_temp_refs", None)  # Phase 4+: export temp files
    # Transient OAuth-flow artifacts do not survive Clear Data:
    session.oauth_state = None
    session.code_verifier = None
    # session.ga4_credentials is kept — that is the durable provider connection.
