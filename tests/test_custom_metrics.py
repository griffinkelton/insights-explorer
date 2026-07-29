"""Tests for custom metrics — apply_custom_metrics, sidebar UI, session reset."""

import ast
from unittest.mock import patch, MagicMock
import pandas as pd

from utils.data_loader import apply_custom_metrics

MODULE = "utils/data_loader.py"
SIDEBAR = "components/sidebar.py"
SESSION = "utils/session.py"


def _parse(path: str) -> ast.Module:
    with open(path) as f:
        return ast.parse(f.read(), filename=path)


# ── Structural tests ────────────────────────────────────────────────────────


class TestCustomMetricsSyntax:
    def test_data_loader_parses(self):
        tree = _parse(MODULE)
        assert isinstance(tree, ast.Module)

    def test_sidebar_parses(self):
        tree = _parse(SIDEBAR)
        assert isinstance(tree, ast.Module)

    def test_session_parses(self):
        tree = _parse(SESSION)
        assert isinstance(tree, ast.Module)


class TestCustomMetricsStructure:
    def test_has_apply_custom_metrics_function(self):
        source = open(MODULE).read()
        assert "def apply_custom_metrics(" in source

    def test_has_custom_metrics_sidebar_section(self):
        source = open(SIDEBAR).read()
        assert "def _render_custom_metrics()" in source

    def test_sidebar_calls_render_custom_metrics(self):
        source = open(SIDEBAR).read()
        assert "_render_custom_metrics()" in source

    def test_session_resets_custom_metrics(self):
        source = open(SESSION).read()
        assert "custom_metrics" in source
        assert "custom_metrics_df" in source

    def test_sidebar_has_custom_metrics_in_session(self):
        source = open(SIDEBAR).read()
        assert "custom_metrics" in source
        assert "custom_metrics_df" in source


# ── Unit tests: apply_custom_metrics ─────────────────────────────────────────


class TestApplyCustomMetrics:
    def test_empty_metrics_returns_copy(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = apply_custom_metrics(df, {})
        assert list(result.columns) == ["a", "b"]
        assert result is not df  # returns a copy, not the same object

    def test_simple_formula(self):
        df = pd.DataFrame({"sessions": [100, 200, 300], "users": [10, 20, 30]})
        result = apply_custom_metrics(df, {"SPU": "sessions / users"})
        assert "SPU" in result.columns
        assert (result["SPU"] == [10.0, 10.0, 10.0]).all()

    def test_multiple_metrics(self):
        df = pd.DataFrame({"a": [10, 20], "b": [2, 4]})
        metrics = {"sum": "a + b", "product": "a * b", "ratio": "a / b"}
        result = apply_custom_metrics(df, metrics)
        assert "sum" in result.columns
        assert "product" in result.columns
        assert "ratio" in result.columns
        assert result["sum"].tolist() == [12, 24]
        assert result["product"].tolist() == [20, 80]

    def test_does_not_mutate_original(self):
        df = pd.DataFrame({"x": [1, 2, 3]})
        original_cols = list(df.columns)
        apply_custom_metrics(df, {"y": "x * 2"})
        assert list(df.columns) == original_cols  # original unchanged

    def test_invalid_formula_skipped(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = apply_custom_metrics(df, {"bad": "nonexistent * 2", "good": "a + b"})
        # "bad" should be skipped silently, "good" should appear
        assert "good" in result.columns
        assert "bad" not in result.columns

    def test_dangerous_formula_blocked(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = apply_custom_metrics(df, {"evil": "__import__('os').system('ls')"})
        assert "evil" not in result.columns

    def test_none_df_returns_none(self):
        result = apply_custom_metrics(None, {"x": "1 + 1"})
        assert result is None

    def test_empty_df_returns_copy(self):
        df = pd.DataFrame()
        result = apply_custom_metrics(df, {"x": "1 + 1"})
        assert result.empty

    def test_column_name_with_spaces(self):
        """Column names can have spaces (matching Streamlit column naming)."""
        df = pd.DataFrame({"total sessions": [100, 200], "unique users": [10, 20]})
        # Backtick-quote column names with spaces
        result = apply_custom_metrics(
            df, {"Sessions per User": "`total sessions` / `unique users`"}
        )
        assert "Sessions per User" in result.columns

    def test_no_metrics_returns_copy_not_same_object(self):
        df = pd.DataFrame({"a": [1]})
        result = apply_custom_metrics(df, {})
        assert result.equals(df)
        assert result is not df


# ── Integration: session state cleanup ───────────────────────────────────────


class TestSessionClearCustomMetrics:
    def test_clear_data_resets_custom_metrics(self):
        mock_state = MagicMock()
        with patch("utils.session.st.session_state", mock_state):
            from utils.session import clear_data

            clear_data()
        assert mock_state.custom_metrics == {}
        assert mock_state.custom_metrics_df is None


# ── Imports smoke test ───────────────────────────────────────────────────────


class TestCustomMetricsImports:
    def test_apply_custom_metrics_importable(self):
        assert callable(apply_custom_metrics)
