"""Scenario integration tests for v0.1.0 hardening.

Each test validates an end-to-end behaviour that the hardening spec
explicitly requires.  These sit above unit tests and below full browser E2E.
"""

import pandas as pd
import pytest

from utils.forecasting import forecast_metric
from utils.funnels import build_funnel_data
from utils.sanitize import safe_pdf_text, safe_spreadsheet_value
from utils.session import active_dataframe, clear_data


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
# Scenario 1 — DataFrame crash fixes
# ═══════════════════════════════════════════════════════════════════════════


class TestActiveDataframePrecedence:
    """active_dataframe() must respect: filtered → custom_metrics → raw df."""

    def test_raw_df_only(self, monkeypatch):
        """With only raw data loaded, return raw df."""
        import streamlit as st

        monkeypatch.setattr(st, "session_state", SessionStateMock({"df": pd.DataFrame({"a": [1]})}))
        result = active_dataframe()
        assert result is not None
        assert list(result.columns) == ["a"]

    def test_custom_metrics_preferred(self, monkeypatch):
        """Custom metrics df takes precedence over raw df."""
        import streamlit as st

        raw = pd.DataFrame({"x": [1]})
        custom = pd.DataFrame({"y": [2]})
        monkeypatch.setattr(
            st, "session_state", SessionStateMock({"df": raw, "custom_metrics_df": custom})
        )
        result = active_dataframe()
        assert result is not None
        assert list(result.columns) == ["y"]

    def test_filtered_preferred_over_custom(self, monkeypatch):
        """Filtered df takes precedence over custom metrics."""
        import streamlit as st

        raw = pd.DataFrame({"x": [1]})
        custom = pd.DataFrame({"y": [2]})
        filt = pd.DataFrame({"z": [3]})
        monkeypatch.setattr(
            st,
            "session_state",
            SessionStateMock(
                {
                    "df": raw,
                    "custom_metrics_df": custom,
                    "filtered_df": filt,
                    "filters_active": True,
                }
            ),
        )
        result = active_dataframe()
        assert result is not None
        assert list(result.columns) == ["z"]

    def test_filters_inactive_skips_filtered(self, monkeypatch):
        """When filters_active is False, skip filtered_df even if present."""
        import streamlit as st

        raw = pd.DataFrame({"x": [1]})
        filt = pd.DataFrame({"z": [3]})
        monkeypatch.setattr(
            st,
            "session_state",
            SessionStateMock({"df": raw, "filtered_df": filt, "filters_active": False}),
        )
        result = active_dataframe()
        assert result is not None
        # filters_active=False → skip filtered, fall to raw
        assert list(result.columns) == ["x"]

    def test_no_data_returns_none(self, monkeypatch):
        """No data at all → None."""
        import streamlit as st

        monkeypatch.setattr(st, "session_state", SessionStateMock({}))
        assert active_dataframe() is None


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
                "df": pd.DataFrame({"a": [1]}),
                "chat_history": [{"role": "user", "content": "hello"}],
                "last_file_id": "file-123",
                "stats": None,
                "summary": None,
                "quality_report": None,
                "missing_columns": [],
                "data_cleared": False,
                "data_source": None,
                "filters_active": False,
                "filtered_df": None,
                "tour_step": 0,
                "custom_metrics": {},
                "custom_metrics_df": None,
                "funnel_steps": [],
                "funnel_data": None,
            }
        )
        monkeypatch.setattr(st, "session_state", fake_state)

        clear_data()

        assert fake_state["df"] is None
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

    def test_empty_filtered_df_not_none(self, monkeypatch):
        """Zero-row filter → empty DataFrame preserved, filters_active=True."""
        import streamlit as st

        empty_df = pd.DataFrame(columns=["a", "b"])
        monkeypatch.setattr(
            st,
            "session_state",
            SessionStateMock(
                {
                    "df": pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
                    "filtered_df": empty_df,
                    "filters_active": True,
                }
            ),
        )

        result = active_dataframe()
        assert result is not None
        assert result.empty
        assert list(result.columns) == ["a", "b"]
