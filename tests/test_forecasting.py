"""Tests for utils/forecasting.py — forecast_metric, build_forecast_summary, build_forecast_prompt."""

import ast
import pandas as pd
from utils.forecasting import (
    forecast_metric,
    build_forecast_summary,
    build_forecast_prompt,
    ForecastResult,
)

MODULE = "utils/forecasting.py"
CHARTS = "utils/charts.py"
PREVIEW = "components/data_preview.py"


def _parse(path: str) -> ast.Module:
    with open(path) as f:
        return ast.parse(f.read(), filename=path)


# ── Structural tests ────────────────────────────────────────────────────────


class TestForecastingSyntax:
    def test_module_parses(self):
        tree = _parse(MODULE)
        assert isinstance(tree, ast.Module)

    def test_charts_parses(self):
        tree = _parse(CHARTS)
        assert isinstance(tree, ast.Module)

    def test_data_preview_parses(self):
        tree = _parse(PREVIEW)
        assert isinstance(tree, ast.Module)


class TestForecastingStructure:
    def test_has_forecast_metric_function(self):
        source = open(MODULE).read()
        assert "def forecast_metric(" in source

    def test_has_build_forecast_summary(self):
        source = open(MODULE).read()
        assert "def build_forecast_summary(" in source

    def test_has_build_forecast_prompt(self):
        source = open(MODULE).read()
        assert "def build_forecast_prompt(" in source

    def test_has_forecast_chart(self):
        source = open(CHARTS).read()
        assert "def generate_forecast_chart(" in source

    def test_data_preview_has_forecast_section(self):
        source = open(PREVIEW).read()
        assert "def _render_forecast_section(" in source

    def test_data_preview_imports_forecasting(self):
        source = open(PREVIEW).read()
        assert "from utils.forecasting import" in source


# ── Unit tests: forecast_metric ─────────────────────────────────────────────


class TestForecastMetric:
    def _make_daily_df(self, days: int = 30) -> pd.DataFrame:
        """Create a simple daily sessions DataFrame with an upward trend.

        Deterministic — uses integer arithmetic, no random noise.
        """
        dates = pd.date_range("2024-01-01", periods=days, freq="D")
        sessions = [100 + i * 2 for i in range(days)]
        return pd.DataFrame({"date": dates, "sessions": sessions})

    def test_returns_result_with_valid_data(self):
        df = self._make_daily_df(30)
        result = forecast_metric(df, "date", "sessions", periods=14)
        assert result is not None
        assert isinstance(result, ForecastResult)
        assert len(result.forecast_df) == 14
        assert result.metric_col == "sessions"

    def test_forecast_df_has_required_columns(self):
        df = self._make_daily_df(30)
        result = forecast_metric(df, "date", "sessions", periods=10)
        for col in ["date", "predicted", "lower_bound", "upper_bound"]:
            assert col in result.forecast_df.columns

    def test_daily_has_required_columns(self):
        df = self._make_daily_df(30)
        result = forecast_metric(df, "date", "sessions", periods=10)
        assert "date" in result.daily.columns
        assert "sessions" in result.daily.columns

    def test_lower_bound_non_negative(self):
        df = self._make_daily_df(30)
        result = forecast_metric(df, "date", "sessions", periods=10)
        assert (result.forecast_df["lower_bound"] >= 0).all()

    def test_trend_direction_known(self):
        df = self._make_daily_df(30)
        result = forecast_metric(df, "date", "sessions", periods=10)
        assert result.trend_direction in ("upward", "downward", "stable")

    def test_confidence_known(self):
        df = self._make_daily_df(30)
        result = forecast_metric(df, "date", "sessions", periods=10)
        assert result.confidence in ("strong", "moderate", "weak")

    def test_r_squared_between_0_and_1(self):
        df = self._make_daily_df(60)
        result = forecast_metric(df, "date", "sessions", periods=30)
        assert 0 <= result.trend_strength <= 1

    def test_pct_change_computed(self):
        df = self._make_daily_df(30)
        result = forecast_metric(df, "date", "sessions", periods=14)
        assert isinstance(result.pct_change, float)

    def test_insufficient_data_returns_none(self):
        df = pd.DataFrame({"date": ["2024-01-01", "2024-01-02"], "sessions": [100, 200]})
        result = forecast_metric(df, "date", "sessions", periods=10)
        assert result is None

    def test_none_df_returns_none(self):
        result = forecast_metric(None, "date", "sessions")
        assert result is None

    def test_empty_df_returns_none(self):
        result = forecast_metric(pd.DataFrame(), "date", "sessions")
        assert result is None

    def test_missing_columns_returns_none(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = forecast_metric(df, "date", "sessions")
        assert result is None

    def test_does_not_mutate_input(self):
        df = self._make_daily_df(30)
        original_len = len(df)
        forecast_metric(df, "date", "sessions", periods=10)
        assert len(df) == original_len

    def test_downward_trend_detected(self):
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        sessions = [200 - i * 3 for i in range(30)]
        df = pd.DataFrame({"date": dates, "sessions": sessions})
        result = forecast_metric(df, "date", "sessions", periods=10)
        assert result.trend_direction == "downward"

    def test_forecast_periods_match_request(self):
        df = self._make_daily_df(30)
        for p in [7, 14, 30, 60]:
            result = forecast_metric(df, "date", "sessions", periods=p)
            assert len(result.forecast_df) == p


# ── Unit tests: build_forecast_summary ───────────────────────────────────────


class TestBuildForecastSummary:
    def _make_result(self) -> ForecastResult:
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        sessions = [100 + i * 5 for i in range(30)]
        daily = pd.DataFrame({"date": dates, "sessions": sessions})
        future_dates = pd.date_range("2024-01-31", periods=10, freq="D")
        forecast_df = pd.DataFrame(
            {
                "date": future_dates,
                "predicted": [255.0] * 10,
                "lower_bound": [230.0] * 10,
                "upper_bound": [280.0] * 10,
            }
        )
        return ForecastResult(
            daily=daily,
            forecast_df=forecast_df,
            metric_col="sessions",
            periods=10,
            trend_direction="upward",
            trend_strength=0.95,
            last_value=250.0,
            final_forecast=255.0,
            pct_change=2.0,
            confidence="strong",
        )

    def test_returns_string(self):
        result = self._make_result()
        summary = build_forecast_summary(result)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_contains_metric_name(self):
        result = self._make_result()
        summary = build_forecast_summary(result)
        assert "sessions" in summary

    def test_contains_confidence(self):
        result = self._make_result()
        summary = build_forecast_summary(result)
        assert "strong" in summary


# ── Unit tests: build_forecast_prompt ────────────────────────────────────────


class TestBuildForecastPrompt:
    def test_returns_non_empty_string(self):
        daily = pd.DataFrame(
            {"date": pd.date_range("2024-01-01", periods=30), "sessions": range(30)}
        )
        forecast_df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-31", periods=10),
                "predicted": [30.0] * 10,
                "lower_bound": [25.0] * 10,
                "upper_bound": [35.0] * 10,
            }
        )
        result = ForecastResult(
            daily=daily,
            forecast_df=forecast_df,
            metric_col="sessions",
            periods=10,
            trend_direction="upward",
            trend_strength=0.5,
            last_value=29.0,
            final_forecast=30.0,
            pct_change=3.4,
            confidence="moderate",
        )
        prompt = build_forecast_prompt(result)
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert "sessions" in prompt
        assert "forecast" in prompt.lower()


# ── Imports smoke test ───────────────────────────────────────────────────────


class TestForecastingImports:
    def test_forecast_metric_importable(self):
        assert callable(forecast_metric)

    def test_build_forecast_summary_importable(self):
        assert callable(build_forecast_summary)

    def test_build_forecast_prompt_importable(self):
        assert callable(build_forecast_prompt)
