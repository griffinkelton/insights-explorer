"""GA4 data loading, validation, and preview utilities."""

import pandas as pd
from typing import Optional, Tuple


# Expected GA4 export columns (case-insensitive matching attempted)
EXPECTED_COLUMNS = [
    "date",
    "page_path",
    "sessions",
    "engagement_rate",
    "users",
]


def load_file(file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load a CSV or XLSX file into a DataFrame.

    Returns (df, error_message).  If successful, error_message is None.
    """
    filename = file.name.lower()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(file, engine="openpyxl")
        else:
            return None, f"Unsupported file type: {file.name}. Please upload a CSV or XLSX file."
    except Exception as e:
        return None, f"Failed to parse file: {str(e)}"

    if df.empty:
        return None, "The uploaded file is empty."

    return df, None


def validate_columns(df: pd.DataFrame) -> list[str]:
    """Check which expected columns are missing. Returns list of missing column names."""
    # Case-insensitive column matching
    df_cols_lower = [c.lower().strip() for c in df.columns]
    missing = []
    for col in EXPECTED_COLUMNS:
        if col not in df_cols_lower:
            missing.append(col)
    return missing


def get_dataset_stats(df: pd.DataFrame) -> dict:
    """Compute basic statistics for the uploaded dataset."""
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
            pass

    return stats
