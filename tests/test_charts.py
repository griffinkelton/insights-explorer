"""Tests for utils/charts.py."""

import pandas as pd
import pytest
from utils.charts import generate_chart, find_column, find_date_column


@pytest.fixture
def forecast_result():
    """A real ForecastResult via utils.forecasting.forecast_metric."""
    from utils.forecasting import forecast_metric

    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=30),
            "sessions": [100 + i * 2 for i in range(30)],
        }
    )
    return forecast_metric(df, "date", "sessions", periods=10)


@pytest.fixture
def funnel_data():
    """A real FunnelData via utils.funnels.build_funnel_data."""
    from utils.funnels import build_funnel_data

    df = pd.DataFrame(
        {
            "page_path": [
                "/home",
                "/home/index.html",
                "/product",
                "/product/item1",
                "/cart",
                "/checkout",
            ],
            "sessions": [1000, 200, 800, 100, 500, 300],
        }
    )
    return build_funnel_data(df, "page_path", "sessions", ["home", "product", "cart", "checkout"])


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
        """Theme param should switch plotly template.

        C3: Plotly has no "plotly_light" template — the light template is
        plotly_white. Previously template="plotly_light" raised ValueError
        and the chart silently fell back to None (the old guard made this
        test pass trivially).
        """
        import plotly.io as pio

        result = generate_chart(
            sample_df, {"chart_type": "bar"}, "top pages", "top?", theme="light"
        )
        assert result is not None
        assert result["fig"].layout.template == pio.templates["plotly_white"]

    def test_theme_defaults_to_dark(self, sample_df):
        """When theme is omitted, default to dark."""
        result = generate_chart(sample_df, {"chart_type": "bar"}, "top pages", "top?")
        if result is not None:
            assert result["type"] == "bar"


class TestChartThemeColors:
    """C3 (light-mode spec §3.3): Plotly light fonts + accent legibility.

    - Light font must map to the light --text-secondary token (#6b7280).
    - Light accents switch to darker variants for contrast on white
      (indigo-600 #4f46e5, amber-600 #d97706, red-600 #dc2626).
    - Dark values stay canonical (L5 guard rail).
    """

    @staticmethod
    def _dump(fig) -> str:
        # fig.to_json() (not json.dumps(to_plotly_json())) because forecast
        # charts carry numpy ndarray customdata that the stdlib encoder
        # cannot serialize.
        return fig.to_json()

    def test_light_font_maps_to_text_secondary(self, sample_df):
        result = generate_chart(sample_df, {"chart_type": "bar"}, "top", "q", theme="light")
        assert result is not None
        assert result["fig"].layout.font.color == "#6b7280"

    def test_dark_font_stays_canonical(self, sample_df):
        result = generate_chart(sample_df, {"chart_type": "bar"}, "top", "q")
        assert result is not None
        assert result["fig"].layout.font.color == "#9898b0"

    def test_light_series_uses_indigo_600(self, sample_df):
        result = generate_chart(sample_df, {"chart_type": "bar"}, "top", "q", theme="light")
        assert result is not None
        assert "#4f46e5" in self._dump(result["fig"])
        assert "#818cf8" not in self._dump(result["fig"])

    def test_dark_series_stays_indigo_400(self, sample_df):
        result = generate_chart(sample_df, {"chart_type": "bar"}, "top", "q")
        assert result is not None
        assert "#818cf8" in self._dump(result["fig"])

    def test_forecast_light_uses_amber_600_and_indigo_600(self, forecast_result):
        from utils.charts import generate_forecast_chart

        fig = generate_forecast_chart(forecast_result, theme="light")
        assert fig is not None
        dump = self._dump(fig)
        assert "#d97706" in dump  # forecast (amber-600)
        assert "#4f46e5" in dump  # actuals (indigo-600)
        assert "#f59e0b" not in dump and "#818cf8" not in dump

    def test_forecast_dark_stays_canonical(self, forecast_result):
        from utils.charts import generate_forecast_chart

        fig = generate_forecast_chart(forecast_result)
        assert fig is not None
        dump = self._dump(fig)
        assert "#f59e0b" in dump and "#818cf8" in dump

    def test_funnel_light_uses_indigo_600(self, funnel_data):
        from utils.charts import generate_funnel_chart

        fig = generate_funnel_chart(funnel_data, theme="light")
        assert fig is not None
        dump = self._dump(fig)
        assert "#4f46e5" in dump
        assert "#818cf8" not in dump

    def test_funnel_dark_stays_indigo_400(self, funnel_data):
        from utils.charts import generate_funnel_chart

        fig = generate_funnel_chart(funnel_data)
        assert fig is not None
        assert "#818cf8" in self._dump(fig)

    def test_light_font_constant_defined(self):
        """The light font token constant is defined in the module."""
        from utils.charts import _LIGHT_FONT_COLOR

        assert _LIGHT_FONT_COLOR == "#6b7280"


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
