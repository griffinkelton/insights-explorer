"""GA4 data loading, validation, and preview utilities."""

import logging
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from typing import Any
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# File size and row limits
MAX_FILE_SIZE_MB = 100
MAX_ROWS = 50_000


# Expected GA4 export columns (case-insensitive matching attempted)
EXPECTED_COLUMNS = [
    "date",
    "page_path",
    "sessions",
    "engagement_rate",
    "users",
]


@dataclass
class DataQualityReport:
    """Structured data quality assessment."""

    completeness_pct: float  # % of non-null cells
    duplicate_pct: float  # % of duplicate rows
    duplicate_count: int  # absolute duplicate count
    outlier_count: int  # rows with z-score > 3 on any numeric column
    date_range_days: int | None  # days between first and last date
    date_gaps: int  # number of missing days in date range
    column_count: int  # total columns
    missing_columns: list[str]  # expected columns that are absent
    grade: str  # "A" through "F"
    warnings: list[str]  # human-readable warnings


def load_file(file: Any) -> tuple[pd.DataFrame | None, str | None, str | None]:
    """Load a CSV or XLSX file into a DataFrame.

    Returns (df, error_message, warning_message).  If successful, both
    error_message and warning_message are None.  Warning is set when
    data is truncated due to row limits.
    """
    filename = file.name.lower()

    # Read file into bytes ONCE — avoids buffer consumption issues
    file_bytes = file.read()
    file_size = len(file_bytes)

    # Size check
    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return (
            None,
            (
                f"File too large ({file_size / 1024 / 1024:.1f} MB). "
                f"Maximum is {MAX_FILE_SIZE_MB} MB."
            ),
            None,
        )

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(file_bytes))
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
        else:
            return (
                None,
                f"Unsupported file type: {file.name}. Please upload a CSV or XLSX file.",
                None,
            )
    except Exception:
        logger.warning("File parse error", exc_info=True)
        return (
            None,
            "We couldn't read this file. Confirm that it is a valid CSV or XLSX export and try again.",
            None,
        )

    if df.empty:
        return None, "The uploaded file is empty.", None

    # Row count check
    warning = None
    if len(df) > MAX_ROWS:
        warning = (
            f"Dataset has {len(df):,} rows — showing first {MAX_ROWS:,} for performance. "
            "Consider exporting a narrower date range from GA4."
        )
        df = df.head(MAX_ROWS)

    return df, None, warning


@st.cache_data(ttl=600, show_spinner=False)
def validate_columns(df: pd.DataFrame) -> list[str]:
    """Check which expected columns are missing. Returns list of missing column names."""
    # Case-insensitive column matching
    df_cols_lower = [c.lower().strip() for c in df.columns]
    missing = []
    for col in EXPECTED_COLUMNS:
        if col not in df_cols_lower:
            missing.append(col)
    return missing


@st.cache_data(ttl=600, show_spinner=False)
def get_dataset_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Compute basic statistics for the uploaded dataset.

    Cached for 10 minutes (ttl=600s) since stats don't change
    for the same DataFrame across Streamlit reruns.
    """
    stats = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
    }

    # Try to find a date column and compute date range (read-only, no mutation)
    date_cols = [c for c in df.columns if "date" in c.lower()]
    if date_cols:
        date_col = date_cols[0]
        try:
            parsed = pd.to_datetime(df[date_col], errors="coerce")
            valid_dates = parsed.dropna()
            if not valid_dates.empty:
                stats["date_range_start"] = valid_dates.min().strftime("%Y-%m-%d")
                stats["date_range_end"] = valid_dates.max().strftime("%Y-%m-%d")
        except Exception:
            pass  # Non-date columns or mixed-format dates are expected in arbitrary datasets

    return stats


def assess_data_quality(
    df: pd.DataFrame, missing_cols: list[str] | None = None
) -> DataQualityReport:
    """Analyze a DataFrame and produce a quality report card.

    Args:
        df: The uploaded DataFrame.
        missing_cols: List of expected-but-missing column names (from validate_columns).

    Returns:
        DataQualityReport with completeness, duplicates, outliers, date coverage, grade.
    """
    if missing_cols is None:
        missing_cols = []

    total_cells = df.size  # rows × cols
    non_null_cells = df.count().sum()
    completeness = (non_null_cells / total_cells * 100) if total_cells > 0 else 0.0

    # Duplicate detection
    duplicate_count = int(df.duplicated().sum())
    duplicate_pct = (duplicate_count / len(df) * 100) if len(df) > 0 else 0.0

    # Outlier detection (Z-score > 3 on numeric columns, sampled for large datasets)
    outlier_count = 0
    numeric_cols = df.select_dtypes(include=["number"]).columns
    sample = df if len(df) <= 50000 else df.sample(n=50000, random_state=42)
    # Build a boolean row mask tracking rows with any outlier
    outlier_mask = pd.Series(False, index=sample.index)
    for col in numeric_cols:
        series = sample[col].dropna()
        if len(series) > 10 and series.std() > 0:
            z_scores = (series - series.mean()) / series.std()
            outlier_mask |= z_scores.abs().gt(3).fillna(False)
    outlier_count = int(outlier_mask.sum())

    # Date coverage
    date_cols = [c for c in df.columns if "date" in c.lower()]
    date_range_days = None
    date_gaps = 0
    if date_cols:
        dates = pd.to_datetime(df[date_cols[0]], errors="coerce").dropna()
        if len(dates) >= 2:
            date_range_days = (dates.max() - dates.min()).days
            # Count missing days in the range (sample to avoid huge range computation)
            if date_range_days <= 365 * 3:  # Only compute gaps for ranges up to 3 years
                all_days = set(dates.dt.date)
                full_range = set(d.date() for d in pd.date_range(dates.min(), dates.max()))
                date_gaps = len(full_range - all_days)

    # Grade calculation
    grade, warnings = _calculate_grade(
        completeness,
        duplicate_pct,
        outlier_count,
        missing_cols,
        date_range_days,
        date_gaps,
        len(df),
    )

    return DataQualityReport(
        completeness_pct=round(completeness, 1),
        duplicate_pct=round(duplicate_pct, 1),
        duplicate_count=duplicate_count,
        outlier_count=outlier_count,
        date_range_days=date_range_days,
        date_gaps=date_gaps,
        column_count=len(df.columns),
        missing_columns=missing_cols,
        grade=grade,
        warnings=warnings,
    )


def _calculate_grade(
    completeness: float,
    duplicate_pct: float,
    outlier_count: int,
    missing_cols: list[str],
    date_range_days: int | None,
    date_gaps: int,
    row_count: int,
) -> tuple[str, list[str]]:
    """Calculate a letter grade (A-F) and generate warnings from quality metrics."""
    score = 100.0
    warnings: list[str] = []

    # Completeness penalty
    if completeness < 50:
        score -= 40
        warnings.append(f"Only {completeness:.0f}% of cells have data — major gaps present.")
    elif completeness < 80:
        score -= 20
        warnings.append(f"{completeness:.0f}% data completeness — some gaps present.")
    elif completeness < 95:
        score -= 5
        warnings.append(f"{completeness:.0f}% data completeness — minor gaps.")

    # Duplicate penalty
    if duplicate_pct > 20:
        score -= 30
        warnings.append(
            f"{duplicate_pct:.0f}% of rows are exact duplicates — data may be corrupted."
        )
    elif duplicate_pct > 5:
        score -= 15
        warnings.append(f"{duplicate_pct:.0f}% duplicate rows detected.")

    # Outlier penalty
    if outlier_count > 50:
        score -= 15
        warnings.append(f"{outlier_count} values to review — data may contain errors.")
    elif outlier_count > 10:
        score -= 5
        warnings.append(f"{outlier_count} outliers detected — review before drawing conclusions.")

    # Date coverage penalty
    if date_range_days is not None:
        if date_range_days < 2:
            score -= 20
            warnings.append("Less than 2 days of data — trends are not meaningful.")
        elif date_range_days < 14:
            score -= 5
            warnings.append(f"Only {date_range_days} days of data — limited for trend analysis.")
        if date_range_days > 0 and date_gaps > date_range_days * 0.3:
            score -= 10
            warnings.append(f"{date_gaps} missing days in the date range — data is sparse.")

    # Missing columns penalty
    if missing_cols:
        score -= len(missing_cols) * 5
        warnings.append(f"Missing expected columns: {', '.join(missing_cols)}.")

    # Low row count penalty
    if row_count < 20:
        score -= 15
        warnings.append("Very small sample size — conclusions may not be reliable.")

    # Convert score to grade
    grade = (
        "A"
        if score >= 90
        else "B" if score >= 75 else "C" if score >= 55 else "D" if score >= 35 else "F"
    )

    return grade, warnings


def find_date_column(df: pd.DataFrame) -> str | None:
    """Find the best date column in the DataFrame. Lives here as the canonical
    version; charts.py imports from here to avoid data→presentation coupling.
    """
    date_candidates = ["date", "day", "date_time", "timestamp"]
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in date_candidates:
        if candidate in df_cols_lower:
            return df_cols_lower[candidate]
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None


class ColumnType(Enum):
    DATE = "date"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"


def detect_column_types(df: pd.DataFrame) -> dict[str, ColumnType]:
    """Classify each column by type. Returns {column_name: ColumnType}.

    Uses select_dtypes (not is_string_dtype — removed in pandas 3.0).
    """
    types: dict[str, ColumnType] = {}
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower() or "day" in col.lower():
            types[col] = ColumnType.DATE
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            types[col] = ColumnType.NUMERIC
            continue
        # String/object detection (pandas 3.0 compatible)
        if col in df.select_dtypes(include=["object", "string"]).columns:
            unique_count = df[col].nunique()
            total_count = len(df)
            if unique_count < total_count * 0.2 and unique_count < 100:
                types[col] = ColumnType.CATEGORICAL
            else:
                types[col] = ColumnType.TEXT
            continue
        types[col] = ColumnType.TEXT
    return types


def smart_sample(df: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
    """Return a representative sample. Small datasets return all rows.

    Uses stratified weekly sampling for large datasets with a date column.
    Falls back to random sampling otherwise. Deterministic (random_state=42).
    """
    n = len(df)
    if n <= max_rows:
        return df
    if n <= 10_000:
        return df.head(max_rows)
    # Large dataset: stratified sampling by date if possible
    date_col = find_date_column(df)
    if date_col:
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
        df_copy["_week"] = df_copy[date_col].dt.to_period("W")
        weeks = max(df_copy["_week"].nunique(), 1)
        sample = df_copy.groupby("_week", group_keys=False).apply(
            lambda g: g.sample(n=min(len(g), max(1, max_rows // weeks)), random_state=42)
        )
        sample = sample.drop(columns=["_week"])
        return sample.head(max_rows)
    return df.sample(n=min(max_rows, n), random_state=42)


def detect_anomalies(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    window: int = 7,
    threshold_std: float = 2.0,
) -> pd.DataFrame:
    """Flag anomalies using rolling Z-score. Returns a copy with added columns.

    Mutates a copy (not the input) to avoid corrupting st.session_state.df.
    """
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    result = result.sort_values(date_col)
    result["rolling_mean"] = result[metric_col].rolling(window=window, min_periods=window).mean()
    result["rolling_std"] = result[metric_col].rolling(window=window, min_periods=window).std()
    # Guard against zero std (constant values produce Inf Z-scores)
    result["rolling_std"] = result["rolling_std"].replace(0, float("nan"))
    result["z_score"] = (result[metric_col] - result["rolling_mean"]) / result["rolling_std"]
    result["is_anomaly"] = result["z_score"].abs() > threshold_std
    return result


def apply_custom_metrics(df: pd.DataFrame, metrics: dict[str, str]) -> pd.DataFrame:
    """Apply user-defined derived columns to a copy of the DataFrame.

    Uses pd.eval() which is safe — only arithmetic expressions, no function
    calls, imports, or attribute access. Each formula is evaluated against
    the DataFrame's columns as variables.

    Args:
        df: The source DataFrame (never mutated).
        metrics: Dict of {column_name: formula} e.g. {"SPU": "sessions / users"}.

    Returns:
        A new DataFrame with derived columns appended, or the original
        (copied) if no metrics are defined.
    """
    if not metrics or df is None or df.empty:
        return df.copy() if df is not None else df

    result = df.copy()
    for name, formula in metrics.items():
        # Safety: reject formulas with dangerous patterns
        dangerous = ["__", "import ", "exec", "eval(", "open(", "compile"]
        if any(d in formula for d in dangerous):
            continue
        try:
            result[name] = result.eval(formula)
        except Exception:
            # Silently skip invalid formulas rather than crashing the app
            pass
    return result


def filter_dataframe(
    df: pd.DataFrame,
    date_col: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    selected_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Apply date range and column filters. Never mutates the original."""
    filtered = df.copy()

    if date_col and date_col in filtered.columns:
        filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
        if start_date:
            filtered = filtered[filtered[date_col] >= pd.Timestamp(start_date)]
        if end_date:
            filtered = filtered[filtered[date_col] <= pd.Timestamp(end_date)]

    if selected_columns:
        valid_cols = [c for c in selected_columns if c in filtered.columns]
        if valid_cols:
            filtered = filtered[valid_cols]
        else:
            return filtered.iloc[0:0]  # Empty but preserves column structure hint

    return filtered
