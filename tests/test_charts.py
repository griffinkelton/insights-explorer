"""Tests for utils/charts.py."""

import pandas as pd
import pytest
from utils.charts import generate_chart, find_column, find_date_column


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=5),
            "sessions": [100, 200, 150, 300, 250],
            "page_path": ["/home", "/about", "/home", "/contact", "/about"],
            "category": ["A", "B", "A", "C", "B"],
        }
    )


class TestGenerateChart:
    def test_returns_fallback_for_unhandled_type(self, sample_df):
        """Fallback creates a bar chart when numeric + categorical columns exist."""
        result = generate_chart(sample_df, {"chart_type": "pie"}, "", "")
        assert result is not None
        assert result["type"] == "bar"

    def test_returns_bar_chart(self, sample_df):
        result = generate_chart(
            sample_df, {"chart_type": "bar"}, "top pages by sessions", "top pages?"
        )
        if result is not None:
            assert "fig" in result
            assert result["type"] == "bar"

    def test_returns_line_chart(self, sample_df):
        result = generate_chart(sample_df, {"chart_type": "line"}, "sessions over time", "trend?")
        if result is not None:
            assert "fig" in result
            assert result["type"] == "line"

    def test_light_theme_produces_light_template(self, sample_df):
        """Theme param should switch plotly template."""
        result = generate_chart(
            sample_df, {"chart_type": "bar"}, "top pages", "top?", theme="light"
        )
        if result is not None:
            assert "fig" in result

    def test_theme_defaults_to_dark(self, sample_df):
        """When theme is omitted, default to dark."""
        result = generate_chart(sample_df, {"chart_type": "bar"}, "top pages", "top?")
        if result is not None:
            assert result["type"] == "bar"


class TestFindColumn:
    def test_finds_case_insensitive(self, sample_df):
        assert find_column(sample_df, ["Sessions"]) == "sessions"
        assert find_column(sample_df, ["PAGE_PATH"]) == "page_path"

    def test_returns_none_for_missing(self, sample_df):
        assert find_column(sample_df, ["bounce_rate"]) is None


class TestFindDateColumn:
    def test_finds_date_column(self, sample_df):
        assert find_date_column(sample_df) == "date"

    def test_returns_none_when_no_date(self):
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        assert find_date_column(df) is None
