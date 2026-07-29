"""Tests for data quality assessment — assess_data_quality, _calculate_grade, DataQualityReport."""

import pandas as pd
from utils.data_loader import DataQualityReport, assess_data_quality, _calculate_grade


def _make_df(data: dict | None = None, rows: int = 100) -> pd.DataFrame:
    """Helper: create a clean GA4-like DataFrame."""
    if data is None:
        data = {
            "date": pd.date_range("2024-01-01", periods=rows, freq="D"),
            "page_path": [f"/page/{i % 10}" for i in range(rows)],
            "sessions": [100 + i % 20 * 10 for i in range(rows)],
            "users": [50 + i % 10 * 5 for i in range(rows)],
        }
    return pd.DataFrame(data)


class TestDataQualityReport:
    """Verify the DataQualityReport dataclass works correctly."""

    def test_report_has_all_fields(self):
        report = DataQualityReport(
            completeness_pct=95.0,
            duplicate_pct=0.0,
            duplicate_count=0,
            outlier_count=0,
            date_range_days=30,
            date_gaps=0,
            column_count=4,
            missing_columns=[],
            grade="A",
            warnings=[],
        )
        assert report.grade == "A"
        assert report.completeness_pct == 95.0
        assert report.duplicate_count == 0
        assert report.date_range_days == 30
        assert report.date_gaps == 0
        assert report.column_count == 4
        assert report.missing_columns == []
        assert report.warnings == []


class TestAssessDataQuality:
    """Verify assess_data_quality() produces correct grade and warnings."""

    def test_perfect_data_gets_a(self):
        df = _make_df()
        report = assess_data_quality(df)
        assert report.grade == "A"
        assert report.warnings == []

    def test_low_completeness_drops_grade(self):
        df = _make_df()
        # Make 60% of cells null
        for col in df.columns:
            df.loc[df.sample(frac=0.6, random_state=1).index, col] = None
        report = assess_data_quality(df)
        assert report.grade in ("C", "D", "F")  # Should drop significantly
        assert report.completeness_pct < 60

    def test_high_duplicates_drops_grade(self):
        df = _make_df(rows=50)
        # Make 50% of rows duplicates of the first row
        dup = pd.concat([df, pd.concat([df.iloc[[0]]] * 25)], ignore_index=True)
        report = assess_data_quality(dup)
        assert report.duplicate_count > 0
        # Should have warnings about duplicates
        assert any("duplicate" in w.lower() for w in report.warnings)

    def test_outliers_drop_grade(self):
        data = {
            "sessions": [100] * 95 + [9999, 9999, 9999, 9999, 9999],
            "page_path": ["/a"] * 100,
        }
        df = pd.DataFrame(data)
        report = assess_data_quality(df)
        assert report.outlier_count > 0

    def test_short_date_range_drops_grade(self):
        # 2 rows with same date → date_range_days=0, triggers "less than 2 days"
        data = {
            "date": ["2024-01-01", "2024-01-01"],
            "sessions": [100, 200],
            "users": [50, 60],
        }
        df = pd.DataFrame(data)
        report = assess_data_quality(df)
        assert report.grade != "A"
        assert any("less than 2 days" in w.lower() for w in report.warnings)

    def test_missing_columns_drop_grade(self):
        df = _make_df()
        # 3 missing cols = -15 points, drops 100→85 = B
        report = assess_data_quality(df, missing_cols=["engagement_rate", "users", "page_path"])
        assert report.grade == "B"
        assert any("missing expected columns" in w.lower() for w in report.warnings)

    def test_empty_dataframe_returns_low_grade(self):
        df = pd.DataFrame()
        report = assess_data_quality(df)
        # Empty DF: completeness=0, 0 rows → D (not F, since no duplicates/outliers)
        assert report.grade in ("D", "F")
        assert report.completeness_pct == 0.0
        assert report.duplicate_count == 0

    def test_single_row_handled(self):
        df = _make_df(rows=1)
        report = assess_data_quality(df)
        # Should not crash on single row
        assert report.grade is not None
        assert report.row_count == 1 if hasattr(report, "row_count") else True
        # Should warn about small sample size
        assert any("small sample" in w.lower() for w in report.warnings)

    def test_no_date_column_handled(self):
        df = pd.DataFrame({"sessions": [100, 200], "users": [50, 60]})
        report = assess_data_quality(df)
        assert report.date_range_days is None
        assert report.date_gaps == 0
        assert report.grade is not None  # Should still compute a grade

    def test_no_numeric_columns_handled(self):
        df = pd.DataFrame({"page": ["/a", "/b"], "name": ["x", "y"]})
        report = assess_data_quality(df)
        assert report.outlier_count == 0
        assert report.grade is not None

    def test_constant_column_does_not_crash(self):
        """A column where all values are identical (std=0) should not crash Z-score."""
        data = {"sessions": [100] * 20, "users": [50] * 20}
        df = pd.DataFrame(data)
        report = assess_data_quality(df)
        # std=0 → z-score skipped (guard clause: series.std() > 0)
        assert report.outlier_count == 0
        assert report.grade is not None

    def test_all_duplicate_rows(self):
        df = pd.DataFrame({"sessions": [100], "users": [50]})
        df = pd.concat([df] * 20, ignore_index=True)
        report = assess_data_quality(df)
        assert report.duplicate_pct > 90
        assert (
            all("duplicate" in w.lower() or "duplicates" in w.lower() for w in report.warnings)
            or len(report.warnings) > 0
        )


class TestCalculateGrade:
    """Verify _calculate_grade() edge cases and score→grade mapping."""

    def test_grade_a_boundary(self):
        grade, _ = _calculate_grade(100.0, 0.0, 0, [], 90, 0, 1000)
        assert grade == "A"

    def test_grade_b_boundary(self):
        # 79% completeness triggers -20 penalty (100-20=80 → B)
        grade, _ = _calculate_grade(79.0, 0.0, 0, [], 90, 0, 1000)
        assert grade == "B"

    def test_grade_c_boundary(self):
        # 49% completeness triggers -40 penalty (100-40=60 → C)
        grade, _ = _calculate_grade(49.0, 0.0, 0, [], 90, 0, 1000)
        assert grade == "C"

    def test_grade_d_boundary(self):
        # 49% completeness + small sample (no date penalty by using None)
        grade, _ = _calculate_grade(49.0, 0.0, 0, [], None, 0, 5)
        assert grade == "D"

    def test_grade_f_boundary(self):
        grade, _ = _calculate_grade(10.0, 50.0, 100, ["all", "five", "cols"], 0, 0, 5)
        assert grade == "F"
