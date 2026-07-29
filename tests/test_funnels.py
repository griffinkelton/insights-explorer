"""Tests for utils/funnels.py — build_funnel_data and FunnelData."""

import ast
import pandas as pd
from utils.funnels import build_funnel_data, FunnelData

MODULE = "utils/funnels.py"
CHARTS = "utils/charts.py"
PREVIEW = "components/data_preview.py"


def _parse(path: str) -> ast.Module:
    with open(path) as f:
        return ast.parse(f.read(), filename=path)


# ── Structural tests ────────────────────────────────────────────────────────


class TestFunnelsSyntax:
    def test_module_parses(self):
        tree = _parse(MODULE)
        assert isinstance(tree, ast.Module)

    def test_charts_parses(self):
        tree = _parse(CHARTS)
        assert isinstance(tree, ast.Module)

    def test_data_preview_parses(self):
        tree = _parse(PREVIEW)
        assert isinstance(tree, ast.Module)


class TestFunnelsStructure:
    def test_has_build_funnel_data(self):
        source = open(MODULE).read()
        assert "def build_funnel_data(" in source

    def test_has_funnel_chart(self):
        source = open(CHARTS).read()
        assert "def generate_funnel_chart(" in source

    def test_data_preview_has_funnel_section(self):
        source = open(PREVIEW).read()
        assert "def _render_funnel_section(" in source

    def test_data_preview_imports_funnels(self):
        source = open(PREVIEW).read()
        assert "from utils.funnels import" in source


# ── Unit tests: build_funnel_data ───────────────────────────────────────────


class TestBuildFunnelData:
    def _make_page_df(self) -> pd.DataFrame:
        """Deterministic page-level GA4 data."""
        return pd.DataFrame(
            {
                "page_path": [
                    "/home",
                    "/home/index.html",
                    "/product",
                    "/product/item1",
                    "/cart",
                    "/checkout",
                    "/thank-you",
                ],
                "sessions": [1000, 200, 800, 100, 500, 300, 200],
                "users": [900, 180, 700, 90, 400, 250, 180],
            }
        )

    def test_basic_funnel(self):
        df = self._make_page_df()
        result = build_funnel_data(
            df, "page_path", "sessions", ["home", "product", "cart", "checkout"]
        )
        assert result is not None
        assert isinstance(result, FunnelData)
        assert result.steps == ["home", "product", "cart", "checkout"]

    def test_funnel_counts(self):
        df = self._make_page_df()
        result = build_funnel_data(
            df, "page_path", "sessions", ["home", "product", "cart", "checkout"]
        )
        # home: 1000+200=1200, product: 800+100=900, cart: 500, checkout: 300
        assert result.counts == [1200.0, 900.0, 500.0, 300.0]

    def test_dropoff_percentages(self):
        df = self._make_page_df()
        result = build_funnel_data(
            df, "page_path", "sessions", ["home", "product", "cart", "checkout"]
        )
        # home→product: (1-900/1200)*100 = 25.0%
        # product→cart: (1-500/900)*100 = 44.4%
        # cart→checkout: (1-300/500)*100 = 40.0%
        assert result.dropoff_pct[0] == 0.0
        assert result.dropoff_pct[1] == 25.0
        assert result.dropoff_pct[2] == 44.4
        assert result.dropoff_pct[3] == 40.0

    def test_first_step_dropoff_zero(self):
        df = self._make_page_df()
        result = build_funnel_data(df, "page_path", "sessions", ["home", "cart"])
        assert result.dropoff_pct[0] == 0.0

    def test_no_match_returns_zero(self):
        df = self._make_page_df()
        result = build_funnel_data(df, "page_path", "sessions", ["home", "nonexistent"])
        assert result.counts[0] == 1200.0
        assert result.counts[1] == 0.0

    def test_case_insensitive_matching(self):
        df = self._make_page_df()
        result = build_funnel_data(df, "page_path", "sessions", ["HOME", "Product", "Cart"])
        assert result.counts == [1200.0, 900.0, 500.0]

    def test_substring_matching(self):
        df = self._make_page_df()
        result = build_funnel_data(df, "page_path", "sessions", ["prod", "check"])
        # "prod" matches /product and /product/item1
        assert result.counts[0] == 900.0
        # "check" matches /checkout
        assert result.counts[1] == 300.0

    def test_different_metric(self):
        df = self._make_page_df()
        result = build_funnel_data(df, "page_path", "users", ["home", "cart"])
        # home: 900+180=1080, cart: 400
        assert result.counts == [1080.0, 400.0]
        assert result.metric_col == "users"

    def test_none_df_returns_none(self):
        result = build_funnel_data(None, "page", "sessions", ["home"])
        assert result is None

    def test_empty_df_returns_none(self):
        result = build_funnel_data(pd.DataFrame(), "page", "sessions", ["home"])
        assert result is None

    def test_missing_page_col_returns_none(self):
        df = pd.DataFrame({"x": [1], "sessions": [100]})
        result = build_funnel_data(df, "page", "sessions", ["home"])
        assert result is None

    def test_missing_metric_col_returns_none(self):
        df = pd.DataFrame({"page_path": ["/home"], "x": [1]})
        result = build_funnel_data(df, "page_path", "sessions", ["home"])
        assert result is None

    def test_empty_steps_returns_none(self):
        df = self._make_page_df()
        result = build_funnel_data(df, "page_path", "sessions", [])
        assert result is None

    def test_single_step_no_dropoff(self):
        df = self._make_page_df()
        result = build_funnel_data(df, "page_path", "sessions", ["home"])
        assert result is not None
        assert len(result.steps) == 1
        assert result.dropoff_pct == [0.0]

    def test_all_zero_prev_handled(self):
        """If a step has 0 count, the next step's drop-off should be 0 (not NaN)."""
        df = pd.DataFrame(
            {
                "page_path": ["/home", "/cart"],
                "sessions": [0, 100],
            }
        )
        result = build_funnel_data(df, "page_path", "sessions", ["home", "cart"])
        assert result.dropoff_pct == [0.0, 0.0]

    def test_does_not_mutate_input(self):
        df = self._make_page_df()
        original_cols = list(df.columns)
        build_funnel_data(df, "page_path", "sessions", ["home", "cart"])
        assert list(df.columns) == original_cols


# ── Imports smoke test ───────────────────────────────────────────────────────


class TestFunnelsImports:
    def test_build_funnel_data_importable(self):
        assert callable(build_funnel_data)
