"""Unit tests for utils/data_loader.py — CSV/XLSX parsing, validation, and stats."""

import io
import pytest
import pandas as pd

from utils.data_loader import load_file, validate_columns, get_dataset_stats, EXPECTED_COLUMNS


# ── Helper: create an in-memory UploadedFile-like object ─────────────────────

class FakeUploadedFile(io.BytesIO):
    """Mimics Streamlit's UploadedFile — a BytesIO subclass with .name and .size."""

    def __init__(self, content: str | bytes, name: str = "test.csv"):
        if isinstance(content, str):
            content = content.encode("utf-8")
        super().__init__(content)
        self.name = name
        self.size = len(content)


def _make_csv(text: str) -> FakeUploadedFile:
    return FakeUploadedFile(text, name="data.csv")


def _make_xlsx(df: pd.DataFrame) -> FakeUploadedFile:
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return FakeUploadedFile(buf.read(), name="data.xlsx")


# ── load_file tests ──────────────────────────────────────────────────────────

class TestLoadFile:
    """Tests for load_file()."""

    def test_load_valid_csv(self):
        csv = "date,page_path,sessions\n2024-01-01,/home,100\n2024-01-02,/about,80\n"
        df, err, _ = load_file(_make_csv(csv))
        assert err is None
        assert len(df) == 2
        assert list(df.columns) == ["date", "page_path", "sessions"]

    def test_load_valid_xlsx(self):
        df_in = pd.DataFrame({
            "date": ["2024-01-01"],
            "page_path": ["/home"],
            "sessions": [100],
        })
        df, err, _ = load_file(_make_xlsx(df_in))
        assert err is None
        assert len(df) == 1

    def test_load_empty_csv(self):
        df, err, _ = load_file(_make_csv("date,page_path,sessions\n"))
        assert df is None
        assert "empty" in err.lower()

    def test_load_unsupported_extension(self):
        f = FakeUploadedFile("hello", name="data.txt")
        df, err, _ = load_file(f)
        assert df is None
        assert "unsupported" in err.lower()

    def test_load_malformed_csv(self):
        df, err, _ = load_file(_make_csv("garbage$$$not,csv\n"))
        # pandas may read this as a single-row, single-column mess;
        # the key is that it doesn't crash and returns something or an error.
        # Verify we get a result (either df or error message) without exception.
        assert err is not None or df is not None

    def test_load_file_handles_bytes_content(self):
        f = FakeUploadedFile(b"col1,col2\n1,2\n", name="bytes.csv")
        df, err, _ = load_file(f)
        assert err is None
        assert len(df) == 1


# ── validate_columns tests ────────────────────────────────────────────────────

class TestValidateColumns:
    """Tests for validate_columns()."""

    def test_empty_dataframe(self):
        """Edge case: DataFrame with 0 rows and 0 columns."""
        missing = validate_columns(pd.DataFrame())
        assert len(missing) == len(EXPECTED_COLUMNS)

    def test_all_columns_present(self):
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        missing = validate_columns(df)
        assert missing == []

    def test_some_columns_missing(self):
        df = pd.DataFrame(columns=["date", "sessions"])
        missing = validate_columns(df)
        assert "page_path" in missing
        assert "engagement_rate" in missing
        assert "users" in missing

    def test_all_columns_missing(self):
        df = pd.DataFrame(columns=["foo", "bar"])
        missing = validate_columns(df)
        assert len(missing) == len(EXPECTED_COLUMNS)

    def test_case_insensitive_matching(self):
        df = pd.DataFrame(columns=["DATE", "Page_Path", "SeSsIoNs", "Engagement_Rate", "USERS"])
        missing = validate_columns(df)
        assert missing == []

    def test_whitespace_in_column_names(self):
        df = pd.DataFrame(columns=[" date ", "page_path", "sessions", "engagement_rate", "users"])
        missing = validate_columns(df)
        # Strip happens on column names in the function
        assert "date" not in missing

    def test_extra_columns_ignored(self):
        df = pd.DataFrame(columns=EXPECTED_COLUMNS + ["extra_col", "another_one"])
        missing = validate_columns(df)
        assert missing == []

    def test_dataframe_with_data_not_just_columns(self):
        """validate_columns should work on DataFrames with actual data rows."""
        df = pd.DataFrame({"date": ["2024-01-01"], "sessions": [100]})
        missing = validate_columns(df)
        assert "page_path" in missing


# ── get_dataset_stats tests ───────────────────────────────────────────────────

class TestGetDatasetStats:
    """Tests for get_dataset_stats()."""

    def test_basic_stats(self):
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "page_path": ["/home", "/about", "/contact"],
            "sessions": [100, 80, 60],
        })
        stats = get_dataset_stats(df)
        assert stats["row_count"] == 3
        assert stats["column_count"] == 3
        assert stats["columns"] == ["date", "page_path", "sessions"]

    def test_date_range(self):
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-15", "2024-01-31"],
            "sessions": [100, 80, 60],
        })
        stats = get_dataset_stats(df)
        assert stats["date_range_start"] == "2024-01-01"
        assert stats["date_range_end"] == "2024-01-31"

    def test_no_date_column(self):
        df = pd.DataFrame({"foo": [1, 2], "bar": [3, 4]})
        stats = get_dataset_stats(df)
        assert stats["row_count"] == 2
        assert "date_range_start" not in stats
        assert "date_range_end" not in stats

    def test_date_column_with_invalid_values(self):
        df = pd.DataFrame({
            "date": ["2024-01-01", "not-a-date", None, "2024-06-15"],
            "sessions": [10, 20, 30, 40],
        })
        stats = get_dataset_stats(df)
        # Should parse only valid dates
        assert stats["date_range_start"] == "2024-01-01"
        assert stats["date_range_end"] == "2024-06-15"

    def test_does_not_mutate_dataframe(self):
        """Regression: get_dataset_stats must not modify the original DataFrame."""
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02"],
            "sessions": [100, 80],
        })
        original_dtypes = df.dtypes.copy()
        get_dataset_stats(df)
        # After calling, the DataFrame should have identical dtypes
        assert (df.dtypes == original_dtypes).all()

    def test_empty_dataframe(self):
        df = pd.DataFrame({"date": [], "sessions": []})
        stats = get_dataset_stats(df)
        assert stats["row_count"] == 0
        # No valid dates, so no date range
        assert "date_range_start" not in stats
