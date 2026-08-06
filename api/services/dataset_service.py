"""Dataset service: parsing/context adapter + policy-real Clear Data.

Parsing is an **adapter boundary** to ``utils/data_loader.py`` — do not
duplicate its validation/error taxonomy (spec §8).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from api.schemas import Column, DatasetContext, DateRange
from api.stores.dataset_store import datasets
from api.stores.session_store import AppSession


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    return "string"


def make_context(df: pd.DataFrame, *, source: str, filename: str) -> DatasetContext:
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
    )


def parse_uploaded_file(filename: str, content: bytes) -> pd.DataFrame:
    """Adapter boundary — replace with utils/data_loader.load_file() once its
    Streamlit cache/UI coupling is extracted (Phase 2). No duplicate parsers."""
    suffix = Path(filename).suffix.lower()
    with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        if suffix == ".csv":
            return pd.read_csv(tmp.name)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(tmp.name)
    raise ValueError("Supported formats are CSV, XLSX, and XLS.")


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
    session.metadata.pop("usage_counters", None)  # Phase 3: per-session usage
    session.metadata.pop("export_temp_refs", None)  # Phase 4+: export temp files
    # Transient OAuth-flow artifacts do not survive Clear Data:
    session.oauth_state = None
    session.code_verifier = None
    # session.ga4_credentials is kept — that is the durable provider connection.
