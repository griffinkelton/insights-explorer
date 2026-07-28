"""Unit tests for utils/prompt_templates.py — prompt construction and chart detection."""

import pytest
import pandas as pd

from utils.prompt_templates import (
    _sanitize_question,
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


# ── _sanitize_question tests ─────────────────────────────────────────────────

class TestSanitizeQuestion:
    """Tests for _sanitize_question() — code blocks, backticks, whitespace."""

    # ── Basic whitespace ──

    def test_strips_leading_trailing_whitespace(self):
        result = _sanitize_question("  hello world  ")
        assert result == "hello world"

    def test_strips_tabs_and_newlines(self):
        result = _sanitize_question("\t\n query \n\t")
        assert result == "query"

    def test_empty_string(self):
        result = _sanitize_question("")
        assert result == ""

    def test_whitespace_only(self):
        result = _sanitize_question("   \n\t  ")
        assert result == ""

    # ── Code block removal ──

    def test_removes_fenced_code_block(self):
        result = _sanitize_question("hello ```print('hack')``` world")
        assert result == "hello [code block removed] world"

    def test_removes_multiline_code_block(self):
        result = _sanitize_question(
            "ignore this:\n```\nprint('line1')\nprint('line2')\n```\nnow answer"
        )
        assert "[code block removed]" in result
        assert "print('line1')" not in result
        assert "now answer" in result

    def test_removes_language_tagged_code_block(self):
        result = _sanitize_question("run ```python\nx = 1\n``` please")
        assert result == "run [code block removed] please"

    def test_removes_multiple_code_blocks(self):
        result = _sanitize_question("a ```x``` b ```y``` c")
        assert result == "a [code block removed] b [code block removed] c"

    # ── Inline backtick removal ──

    def test_removes_inline_backticks(self):
        result = _sanitize_question("run `rm -rf /` command")
        assert result == "run [code removed] command"

    def test_removes_multiple_inline_backticks(self):
        result = _sanitize_question("`x` and `y`")
        assert result == "[code removed] and [code removed]"

    # ── Newline collapsing ──

    def test_collapses_excessive_newlines(self):
        result = _sanitize_question("hello\n\n\n\nworld")
        assert result == "hello\n\nworld"

    def test_preserves_single_newlines(self):
        result = _sanitize_question("hello\nworld")
        assert result == "hello\nworld"

    def test_preserves_double_newlines(self):
        result = _sanitize_question("hello\n\nworld")
        assert result == "hello\n\nworld"

    # ── Edge cases ──

    def test_already_clean_text_passes_through(self):
        result = _sanitize_question("What were the top pages by sessions?")
        assert result == "What were the top pages by sessions?"

    def test_unbalanced_backticks_pass_through(self):
        """Unbalanced ` markers should be left as-is — not stripped."""
        result = _sanitize_question("it costs `5 dollars")
        # Inline regex requires closing ` so unbalanced passes through
        assert "5 dollars" in result
        assert "`" in result  # backtick survives since there's no closing match

    def test_unbalanced_code_fence_pass_through(self):
        """Unbalanced ``` markers pass through since regex requires a closing fence."""
        result = _sanitize_question("use ``` to format")
        # ``` without closing ``` should not match the code block regex
        assert "use ``` to format" == result

    def test_nested_backticks_in_code_block(self):
        """Code block regex runs first, so inline backticks inside are handled."""
        result = _sanitize_question("a ```\n`inner`\n``` b")
        assert result == "a [code block removed] b"

    def test_preserves_special_characters(self):
        result = _sanitize_question("em-dash: — ellipsis: … bullet: •")
        assert "—" in result
        assert "…" in result
        assert "•" in result


# ── detect_chart_request tests ───────────────────────────────────────────────

class TestDetectChartRequest:
    """Tests for detect_chart_request() — JSON + keyword hybrid detection."""

    # ── Line chart triggers (keyword fallback with method tag) ──

    def test_over_time_triggers_line(self):
        result = detect_chart_request("Sessions increased over time.")
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    def test_trend_triggers_line(self):
        result = detect_chart_request("There is a clear upward trend.")
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    def test_daily_triggers_line(self):
        result = detect_chart_request("Daily active users peaked on Monday.")
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    def test_per_day_triggers_line(self):
        result = detect_chart_request("Sessions per day declined.")
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    def test_spike_triggers_line(self):
        result = detect_chart_request("There was a spike in traffic.")
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    def test_decrease_triggers_line(self):
        result = detect_chart_request("Engagement decreased significantly.")
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    # ── Bar chart triggers (keyword fallback with method tag) ──

    def test_top_5_triggers_bar(self):
        result = detect_chart_request("The top 5 pages by sessions are...")
        assert result == {"chart_type": "bar", "reason": "ranking", "method": "keyword"}

    def test_highest_triggers_bar(self):
        result = detect_chart_request("The highest sessions were on /home.")
        assert result == {"chart_type": "bar", "reason": "ranking", "method": "keyword"}

    def test_breakdown_triggers_bar(self):
        result = detect_chart_request("Breakdown by device shows mobile dominant.")
        assert result == {"chart_type": "bar", "reason": "ranking", "method": "keyword"}

    def test_distribution_triggers_bar(self):
        result = detect_chart_request("The distribution across channels...")
        assert result == {"chart_type": "bar", "reason": "ranking", "method": "keyword"}

    def test_comparison_triggers_bar(self):
        result = detect_chart_request("A comparison of pages shows...")
        assert result == {"chart_type": "bar", "reason": "ranking", "method": "keyword"}

    def test_by_source_triggers_bar(self):
        result = detect_chart_request("Traffic by source varies a lot.")
        assert result == {"chart_type": "bar", "reason": "ranking", "method": "keyword"}

    # ── JSON chart config detection ──

    def test_parses_json_chart_config(self):
        """[CHART:{...}] token should be parsed as JSON."""
        result = detect_chart_request(
            'Sessions grew. [CHART:{"type":"line","x":"date","y":"sessions","title":"Trend"}]'
        )
        assert result["chart_type"] == "line"
        assert result["x"] == "date"
        assert result["y"] == "sessions"
        assert result["method"] == "gemini_json"

    def test_json_trumps_keyword(self):
        """JSON config should be preferred over keyword heuristics."""
        result = detect_chart_request(
            'Top pages ranked. [CHART:{"type":"line","x":"date","y":"sessions"}]'
        )
        assert result["chart_type"] == "line"  # JSON says line
        assert result["method"] == "gemini_json"  # not keyword

    def test_invalid_json_falls_back_to_keyword(self):
        """Malformed JSON should fall back to keyword detection."""
        result = detect_chart_request(
            'Top pages trend [CHART:{bad json}] over time'
        )
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    # ── No chart triggers ──

    def test_no_chart_for_plain_text(self):
        assert detect_chart_request("The data looks normal.") is None

    def test_no_chart_for_empty_string(self):
        assert detect_chart_request("") is None

    def test_no_chart_for_vague_text(self):
        assert detect_chart_request("Interesting findings in the dataset.") is None

    def test_none_input_returns_none(self):
        """None input should return None gracefully (None guard added)."""
        assert detect_chart_request(None) is None

    # ── Edge cases ──

    def test_line_before_bar_precedence(self):
        """When both triggers appear, line should take precedence (checked first)."""
        result = detect_chart_request(
            "The top pages trended downward over time."
        )
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}

    def test_case_insensitive(self):
        assert detect_chart_request("Trend Over Time") == {
            "chart_type": "line", "reason": "trend", "method": "keyword"
        }
        assert detect_chart_request("Top 10 Pages") == {
            "chart_type": "bar", "reason": "ranking", "method": "keyword"
        }

    def test_partial_word_boundary(self):
        """'day' should match within words like 'Monday'."""
        result = detect_chart_request("On Monday traffic spiked.")
        assert result == {"chart_type": "line", "reason": "trend", "method": "keyword"}
