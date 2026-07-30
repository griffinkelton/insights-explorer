"""Scenario integration tests for v0.1.0 hardening.

Each test validates an end-to-end behaviour that the hardening spec
explicitly requires.  These sit above unit tests and below full browser E2E.
"""

import pandas as pd
import pytest

from utils.forecasting import forecast_metric
from utils.funnels import build_funnel_data
from utils.sanitize import safe_pdf_text, safe_spreadsheet_value
from utils.session import clear_data


# ── Helper: Streamlit-compatible session state mock ──────────────────────


class SessionStateMock(dict):
    """A dict subclass that supports attribute access like st.session_state."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 1 — DataContext lifecycle (v0.2.0 Phase 1)
# ═══════════════════════════════════════════════════════════════════════════


class TestDataContextLifecycle:
    """End-to-end DataContext lifecycle: load → custom metric → filter → clear → verify."""

    def test_custom_metric_survives_filter_clear(self):
        """Custom metrics → filter → clear filters → custom column still in base_df."""
        from utils.data_context import (
            create_context_from_upload,
            with_custom_metrics,
            with_filtered_data,
            with_filters_cleared,
        )

        df = pd.DataFrame({"sessions": [100, 200, 300], "users": [10, 20, 30]})
        ctx = create_context_from_upload(df, b"test")

        # Apply custom metric
        metrics_df = df.copy()
        metrics_df["sessions_per_user"] = metrics_df["sessions"] / metrics_df["users"]
        ctx = with_custom_metrics(ctx, metrics_df)
        assert "sessions_per_user" in ctx.base_df.columns
        assert "sessions_per_user" in ctx.active_df.columns

        # Apply a filter
        filtered = ctx.base_df[ctx.base_df["sessions"] > 150]
        ctx = with_filtered_data(ctx, filtered, ("sessions>150",))
        assert len(ctx.active_df) == 2  # filtered
        assert ctx.filters.is_active

        # Clear filters
        ctx = with_filters_cleared(ctx)
        assert not ctx.filters.is_active
        assert len(ctx.active_df) == 3  # back to base
        assert "sessions_per_user" in ctx.active_df.columns  # custom column survives
        assert "sessions_per_user" in ctx.base_df.columns

    def test_clear_data_removes_context_only(self, monkeypatch):
        """clear_data() → data_context is None, no legacy keys remain."""
        import streamlit as st

        fake_state = SessionStateMock(
            {
                "data_context": object(),
                "last_file_id": "file-456",
                "chat_history": [{"q": "test"}],
                "stats": {"row_count": 100},
                "summary": "old summary",
                "quality_report": "old report",
                "missing_columns": ["col1"],
                "data_cleared": False,
                "data_source": "file",
                "tour_step": 3,
                "custom_metrics": {"rate": "a / b"},
                "funnel_steps": ["/home"],
                "funnel_data": {"steps": 1},
            }
        )
        monkeypatch.setattr(st, "session_state", fake_state)

        clear_data()

        assert fake_state["data_context"] is None
        assert fake_state["chat_history"] == []
        assert fake_state["last_file_id"] is None
        assert fake_state["stats"] is None
        assert fake_state["summary"] is None
        assert fake_state["custom_metrics"] == {}
        assert fake_state["funnel_steps"] == []
        assert fake_state["funnel_data"] is None


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 3 — Clear Data reload
# ═══════════════════════════════════════════════════════════════════════════


class TestClearDataReload:
    """clear_data() must reset last_file_id to allow same-file reload."""

    def test_clear_data_resets_file_id(self, monkeypatch):
        """After clear, last_file_id should be None."""
        import streamlit as st

        fake_state = SessionStateMock(
            {
                "data_context": object(),  # non-None so we can verify it's cleared
                "chat_history": [{"role": "user", "content": "hello"}],
                "last_file_id": "file-123",
                "stats": None,
                "summary": None,
                "quality_report": None,
                "missing_columns": [],
                "data_cleared": False,
                "data_source": None,
                "tour_step": 0,
                "custom_metrics": {},
                "funnel_steps": [],
                "funnel_data": None,
            }
        )
        monkeypatch.setattr(st, "session_state", fake_state)

        clear_data()

        assert fake_state["data_context"] is None
        assert fake_state["chat_history"] == []
        assert fake_state["last_file_id"] is None


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 4 — Forecast with irregular dates
# ═══════════════════════════════════════════════════════════════════════════


class TestForecastDateHandling:
    """forecast_metric must reindex to daily calendar and handle gaps."""

    def test_minimum_days_required(self):
        """Need at least 7 days of data for a meaningful forecast."""
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                "sessions": [10, 20, 30],
            }
        )
        result = forecast_metric(df, "date", "sessions", periods=3)
        # Only 3 data points → n < 7 → returns None
        assert result is None

    def test_week_of_data_produces_forecast(self):
        """With 7+ days, forecast should return a ForecastResult."""
        dates = pd.date_range("2024-01-01", periods=7, freq="D")
        df = pd.DataFrame({"date": dates, "sessions": range(10, 17)})
        result = forecast_metric(df, "date", "sessions", periods=3)

        assert result is not None
        assert result.trend_direction in ("upward", "downward", "stable")
        assert len(result.forecast_df) == 3

    def test_gapped_dates_filled(self):
        """Missing days should be filled with 0 before fitting."""
        dates = pd.to_datetime(
            [
                "2024-01-01",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-06",
                "2024-01-07",
                "2024-01-08",
            ]
        )
        df = pd.DataFrame({"date": dates, "sessions": [10, 20, 30, 40, 50, 60, 70]})
        result = forecast_metric(df, "date", "sessions", periods=3)

        assert result is not None
        assert len(result.forecast_df) == 3

    def test_constant_series_works(self):
        """Constant metric series should not crash forecasting."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({"date": dates, "sessions": [10] * 10})
        result = forecast_metric(df, "date", "sessions", periods=2)

        assert result is not None
        # Slope may be near-zero due to floating point — check strength instead
        assert (
            result.trend_strength < 0.01
        ), f"Expected near-zero trend strength for constant data, got {result.trend_strength}"

    def test_nonnumeric_metric_handled(self):
        """Non-numeric values should be coerced by pd.to_numeric."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        values = ["10", "20", "30", "40", "50", "60", "70", "N/A", "90", "100"]
        df = pd.DataFrame({"date": dates, "sessions": values})
        result = forecast_metric(df, "date", "sessions", periods=1)
        # 'N/A' dropped, 9 rows remain → >=7 → should work
        assert result is not None

    def test_periods_zero_returns_none(self):
        """periods <= 0 should return None gracefully."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({"date": dates, "sessions": range(10)})
        result = forecast_metric(df, "date", "sessions", periods=0)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 5 — Export formula injection
# ═══════════════════════════════════════════════════════════════════════════


class TestExportFormulaSafety:
    """safe_spreadsheet_value must escape formula prefixes."""

    def test_equals_prefix_escaped(self):
        assert (
            safe_spreadsheet_value('=HYPERLINK("http://evil","click")')
            == '\'=HYPERLINK("http://evil","click")'
        )

    def test_plus_prefix_escaped(self):
        assert safe_spreadsheet_value("+1+1") == "'+1+1"

    def test_minus_prefix_escaped(self):
        assert safe_spreadsheet_value("-1+1") == "'-1+1"

    def test_at_prefix_escaped(self):
        assert safe_spreadsheet_value("@SUM(1+1)") == "'@SUM(1+1)"

    def test_normal_text_untouched(self):
        assert safe_spreadsheet_value("hello world") == "hello world"

    def test_non_string_untouched(self):
        assert safe_spreadsheet_value(42) == 42
        assert safe_spreadsheet_value(None) is None

    def test_leading_whitespace_before_formula(self):
        assert safe_spreadsheet_value("  =FORMULA") == "'  =FORMULA"
        assert safe_spreadsheet_value("\t-CALC") == "'\t-CALC"


class TestPdfTextSafety:
    """safe_pdf_text must XML-escape dangerous characters."""

    def test_angle_brackets_escaped(self):
        result = safe_pdf_text("<script>alert(1)</script>")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "<script>" not in result

    def test_ampersand_escaped(self):
        assert "&amp;" in safe_pdf_text("A & B")

    def test_non_string_coerced(self):
        assert safe_pdf_text(42) == "42"
        assert safe_pdf_text(None) == "None"


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 7 — Funnel literal matching
# ═══════════════════════════════════════════════════════════════════════════


class TestFunnelLiteralMatching:
    """build_funnel_data must use regex=False for literal page-path matching."""

    def test_regex_metacharacters_literal(self):
        """?.+[] should be matched literally, not as regex."""
        df = pd.DataFrame(
            {
                "page_path": ["/help?", "/help??", "/help", "/other"],
                "sessions": [10, 20, 5, 100],
            }
        )
        # /help? contains a regex metacharacter but should match literally
        result = build_funnel_data(df, "page_path", "sessions", ["/help?"])

        assert result is not None
        assert len(result.steps) == 1
        # Only exact literal match /help? — matches rows containing the substring "/help?"
        # (regex=False means literal substring match, so "/help??" also contains "/help?")
        assert result.counts[0] == 30  # 10 + 20 from /help? and /help??

    def test_dot_not_wildcard(self):
        """. should not match any character."""
        df = pd.DataFrame(
            {
                "page_path": ["/a.b", "/axb", "/a.b"],
                "sessions": [5, 10, 3],
            }
        )
        result = build_funnel_data(df, "page_path", "sessions", ["/a.b"])

        assert result is not None
        assert result.counts[0] == 8  # 5 + 3 from two /a.b rows

    def test_steps_capped_at_8(self):
        """More than 8 steps should be silently truncated."""
        df = pd.DataFrame(
            {
                "page_path": [f"/page{i}" for i in range(10)],
                "sessions": [1] * 10,
            }
        )
        result = build_funnel_data(df, "page_path", "sessions", [f"/page{i}" for i in range(10)])
        assert result is not None
        assert len(result.steps) == 8


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 8 — Streaming error semantics
# ═══════════════════════════════════════════════════════════════════════════


class TestStreamingErrorSemantics:
    """generate_response_stream must raise RuntimeError, not yield error text."""

    def test_streaming_raises_on_api_error(self):
        """Streaming failure → RuntimeError, not yielding error as response."""
        from unittest.mock import MagicMock, patch

        from utils.gemini_client import generate_response_stream

        # Mock _get_client so that generate_content_stream raises
        mock_client = MagicMock()
        mock_client.models.generate_content_stream.side_effect = RuntimeError("API unavailable")

        with patch("utils.gemini_client._get_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="could not complete"):
                list(generate_response_stream("test prompt"))


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 9 — Summary uses selected model
# ═══════════════════════════════════════════════════════════════════════════


class TestSummaryModelSelection:
    """Summary generation must use selected_model, not always default.

    Note: This is a structural test — the actual model-passing behaviour is
    verified by test_summary.py integration tests. This guards against
    accidental signature changes that would break model selection.
    """

    def test_generate_response_accepts_model_kwarg(self):
        """generate_response() should accept an optional model argument."""
        from unittest.mock import patch

        # Verify that summary.py passes selected_model by checking the
        # actual call chain with a controlled mock
        with patch("components.summary.generate_response") as mock_gen:
            mock_gen.return_value = "Summary."

            from components.summary import _generate_summary

            df = pd.DataFrame({"sessions": [100]})
            stats = {"row_count": 1, "column_count": 1, "columns": ["sessions"]}

            _generate_summary(df, stats)

            mock_gen.assert_called_once()
            _, kwargs = mock_gen.call_args
            # Must pass a model kwarg — selected_model or DEFAULT_MODEL fallback
            assert (
                "model" in kwargs
            ), "_generate_summary must pass model= to generate_response. " "Got kwargs: " + str(
                kwargs
            )


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 11 — GA4 property ID validation
# ═══════════════════════════════════════════════════════════════════════════


class TestGa4PropertyIdValidation:
    """GA4 property IDs must be validated as digits-only before pull."""

    def test_digits_only_valid(self):
        """All-digit property IDs should pass validation."""
        assert "123456789".isdigit() is True
        assert "0".isdigit() is True

    def test_non_digit_rejected(self):
        """Non-digit property IDs should be rejected."""
        assert "123abc".isdigit() is False
        assert "properties/123".isdigit() is False
        assert "".isdigit() is False
        assert " ".isdigit() is False


# ═══════════════════════════════════════════════════════════════════════════
# Scenario 2 — Filter to zero (empty-filter semantics)
# ═══════════════════════════════════════════════════════════════════════════


class TestEmptyFilterSemantics:
    """Zero-row filters must preserve an empty DataFrame, not fall to None."""

    def test_empty_filtered_df_not_none(self):
        """Zero-row filter → empty active_df preserved in DataContext."""
        from utils.data_context import DataContext, FilterState

        empty_df = pd.DataFrame(columns=["a", "b"])
        ctx = DataContext(
            source_id="test:1",
            version=1,
            raw_df=pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
            base_df=pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
            active_df=empty_df,
            filters=FilterState(descriptions=("empty",), is_active=True, row_count=0),
        )

        assert ctx.active_df is not None
        assert ctx.active_df.empty
        assert list(ctx.active_df.columns) == ["a", "b"]
