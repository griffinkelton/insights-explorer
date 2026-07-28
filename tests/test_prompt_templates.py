"""Unit tests for utils/prompt_templates.py — prompt construction and chart detection."""

import pytest
import pandas as pd

from utils.prompt_templates import (
    build_summary_prompt,
    build_chat_prompt,
    detect_chart_request,
)


# ── Shared fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def simple_df():
    """A minimal GA4-like DataFrame."""
    return pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "page_path": ["/home", "/about", "/contact"],
        "sessions": [100, 80, 60],
        "engagement_rate": [0.5, 0.4, 0.35],
        "users": [50, 40, 30],
    })


@pytest.fixture
def full_stats():
    return {
        "row_count": 3,
        "column_count": 5,
        "columns": ["date", "page_path", "sessions", "engagement_rate", "users"],
        "date_range_start": "2024-01-01",
        "date_range_end": "2024-01-03",
        "missing_columns": [],
    }


@pytest.fixture
def stats_no_dates():
    return {
        "row_count": 3,
        "column_count": 3,
        "columns": ["page_path", "sessions", "users"],
        "missing_columns": ["date", "engagement_rate"],
    }


# ── build_summary_prompt tests ───────────────────────────────────────────────

class TestBuildSummaryPrompt:
    """Tests for build_summary_prompt()."""

    def test_includes_row_count(self, simple_df, full_stats):
        prompt = build_summary_prompt(simple_df, full_stats)
        assert "Row count: 3" in prompt

    def test_includes_columns(self, simple_df, full_stats):
        prompt = build_summary_prompt(simple_df, full_stats)
        assert "date, page_path, sessions, engagement_rate, users" in prompt

    def test_includes_date_range(self, simple_df, full_stats):
        prompt = build_summary_prompt(simple_df, full_stats)
        assert "2024-01-01 to 2024-01-03" in prompt

    def test_includes_missing_columns(self, simple_df, stats_no_dates):
        prompt = build_summary_prompt(simple_df, stats_no_dates)
        assert "date, engagement_rate" in prompt

    def test_handles_no_missing_columns(self, simple_df, full_stats):
        prompt = build_summary_prompt(simple_df, full_stats)
        assert "None" in prompt  # "Missing expected columns ...: None"

    def test_handles_no_date_range(self, simple_df, stats_no_dates):
        prompt = build_summary_prompt(simple_df, stats_no_dates)
        # Should not have date info
        assert "Date range:" not in prompt

    def test_includes_sample_rows(self, simple_df, full_stats):
        prompt = build_summary_prompt(simple_df, full_stats)
        assert "/home" in prompt
        assert "/about" in prompt

    def test_asks_for_bullet_points(self, simple_df, full_stats):
        prompt = build_summary_prompt(simple_df, full_stats)
        assert "bullet" in prompt.lower() or "bullet" in prompt

    def test_handles_missing_columns_key(self, simple_df):
        stats_no_key = {
            "row_count": 3,
            "columns": ["page_path", "sessions"],
        }
        prompt = build_summary_prompt(simple_df, stats_no_key)
        # Should gracefully default to empty list for missing_columns
        assert "None" in prompt


# ── build_chat_prompt tests ──────────────────────────────────────────────────

class TestBuildChatPrompt:
    """Tests for build_chat_prompt()."""

    def test_includes_user_question(self, simple_df, full_stats):
        prompt = build_chat_prompt("How many sessions?", simple_df, full_stats)
        assert "How many sessions?" in prompt

    def test_includes_row_count(self, simple_df, full_stats):
        prompt = build_chat_prompt("test", simple_df, full_stats)
        assert "Total rows: 3" in prompt

    def test_includes_columns(self, simple_df, full_stats):
        prompt = build_chat_prompt("test", simple_df, full_stats)
        assert "date, page_path, sessions, engagement_rate, users" in prompt

    def test_includes_date_range(self, simple_df, full_stats):
        prompt = build_chat_prompt("test", simple_df, full_stats)
        assert "2024-01-01 to 2024-01-03" in prompt

    def test_includes_numeric_summary(self, simple_df, full_stats):
        prompt = build_chat_prompt("test", simple_df, full_stats)
        # describe() includes count, mean, std, etc.
        assert "count" in prompt.lower() or "mean" in prompt.lower()

    def test_includes_sample_data(self, simple_df, full_stats):
        prompt = build_chat_prompt("test", simple_df, full_stats)
        assert "/home" in prompt

    def test_handles_no_date_range(self, simple_df, stats_no_dates):
        prompt = build_chat_prompt("test", simple_df, stats_no_dates)
        assert "Date range:" not in prompt

    def test_handles_no_numeric_columns(self, full_stats):
        df = pd.DataFrame({
            "page_path": ["/home", "/about"],
            "channel": ["organic", "paid"],
        })
        stats = {"row_count": 2, "columns": list(df.columns)}
        prompt = build_chat_prompt("test", df, stats)
        # Should not crash — falls back to "No numeric columns available"
        assert "No numeric columns available" in prompt

    def test_includes_instructions(self, simple_df, full_stats):
        prompt = build_chat_prompt("test", simple_df, full_stats)
        assert "concise" in prompt.lower()
        assert "limitation" in prompt.lower()

    def test_large_dataset_uses_head(self, full_stats):
        # Create a DataFrame larger than 10 rows — prompt should still use head(10)
        df = pd.DataFrame({
            "date": [f"2024-01-{i:02d}" for i in range(1, 51)],
            "page_path": [f"/page{i}" for i in range(50)],
            "sessions": list(range(50, 100)),
        })
        prompt = build_chat_prompt("test", df, {**full_stats, "row_count": 50})
        # head(10) should limit sample — we check that page40+ don't appear
        assert "/page40" not in prompt
        assert "/page1" in prompt or "/page01" in prompt

    def test_handles_empty_dataframe(self):
        """Edge case: empty DataFrame (0 columns, 0 rows) should not crash."""
        df = pd.DataFrame()
        stats = {"row_count": 0, "columns": []}
        prompt = build_chat_prompt("test", df, stats)
        assert "test" in prompt
        assert "Total rows: 0" in prompt

    def test_handles_empty_numeric_dataframe(self):
        """Edge case: DataFrame with numeric columns but 0 rows.
        Hits the df.describe() path — pandas handles this gracefully."""
        df = pd.DataFrame({
            "sessions": pd.Series(dtype="int64"),
            "users": pd.Series(dtype="int64"),
        })
        stats = {"row_count": 0, "columns": ["sessions", "users"]}
        prompt = build_chat_prompt("how many sessions?", df, stats)
        # Should not crash and should include numeric summary area
        assert "how many sessions?" in prompt
        assert "Total rows: 0" in prompt
        # describe() on empty numeric df returns an empty DataFrame string
        assert "NUMERIC COLUMN STATISTICS" in prompt


# ── detect_chart_request tests ───────────────────────────────────────────────

class TestDetectChartRequest:
    """Tests for detect_chart_request()."""

    # ── Line chart triggers ──

    def test_over_time_triggers_line(self):
        result = detect_chart_request("Sessions increased over time.")
        assert result == {"chart_type": "line", "reason": "trend"}

    def test_trend_triggers_line(self):
        result = detect_chart_request("There is a clear upward trend.")
        assert result == {"chart_type": "line", "reason": "trend"}

    def test_daily_triggers_line(self):
        result = detect_chart_request("Daily active users peaked on Monday.")
        assert result == {"chart_type": "line", "reason": "trend"}

    def test_per_day_triggers_line(self):
        result = detect_chart_request("Sessions per day declined.")
        assert result == {"chart_type": "line", "reason": "trend"}

    def test_spike_triggers_line(self):
        result = detect_chart_request("There was a spike in traffic.")
        assert result == {"chart_type": "line", "reason": "trend"}

    def test_decrease_triggers_line(self):
        result = detect_chart_request("Engagement decreased significantly.")
        assert result == {"chart_type": "line", "reason": "trend"}

    # ── Bar chart triggers ──

    def test_top_5_triggers_bar(self):
        result = detect_chart_request("The top 5 pages by sessions are...")
        assert result == {"chart_type": "bar", "reason": "ranking"}

    def test_highest_triggers_bar(self):
        result = detect_chart_request("The highest sessions were on /home.")
        assert result == {"chart_type": "bar", "reason": "ranking"}

    def test_breakdown_triggers_bar(self):
        result = detect_chart_request("Breakdown by device shows mobile dominant.")
        assert result == {"chart_type": "bar", "reason": "ranking"}

    def test_distribution_triggers_bar(self):
        result = detect_chart_request("The distribution across channels...")
        assert result == {"chart_type": "bar", "reason": "ranking"}

    def test_comparison_triggers_bar(self):
        result = detect_chart_request("A comparison of pages shows...")
        assert result == {"chart_type": "bar", "reason": "ranking"}

    def test_by_source_triggers_bar(self):
        result = detect_chart_request("Traffic by source varies a lot.")
        assert result == {"chart_type": "bar", "reason": "ranking"}

    # ── No chart triggers ──

    def test_no_chart_for_plain_text(self):
        assert detect_chart_request("The data looks normal.") is None

    def test_no_chart_for_empty_string(self):
        assert detect_chart_request("") is None

    def test_no_chart_for_vague_text(self):
        assert detect_chart_request("Interesting findings in the dataset.") is None

    # ── Edge cases ──

    def test_line_before_bar_precedence(self):
        """When both triggers appear, line should take precedence (checked first)."""
        result = detect_chart_request(
            "The top pages trended downward over time."
        )
        # "top" triggers bar, "trend" and "over time" trigger line
        # Line is checked first in the function
        assert result == {"chart_type": "line", "reason": "trend"}

    def test_case_insensitive(self):
        assert detect_chart_request("Trend Over Time") == {"chart_type": "line", "reason": "trend"}
        assert detect_chart_request("Top 10 Pages") == {"chart_type": "bar", "reason": "ranking"}

    def test_partial_word_boundary(self):
        """'day' should match within words like 'Monday'."""
        result = detect_chart_request("On Monday traffic spiked.")
        assert result == {"chart_type": "line", "reason": "trend"}

    def test_none_input_raises(self):
        """None input should raise AttributeError (calling .lower() on None).
        If this behavior changes (e.g., a None guard is added), update this test."""
        with pytest.raises(AttributeError):
            detect_chart_request(None)
