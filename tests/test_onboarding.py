"""Tests for utils/onboarding.py — structural + TOUR_STEPS validation."""

import ast

MODULE = "utils/onboarding.py"


def _parse() -> ast.Module:
    with open(MODULE) as f:
        return ast.parse(f.read(), filename=MODULE)


class TestOnboardingSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestOnboardingImports:
    def test_imports_streamlit(self):
        source = open(MODULE).read()
        assert "import streamlit" in source


class TestOnboardingStructure:
    def test_has_render_tour_step_function(self):
        source = open(MODULE).read()
        assert "def render_tour_step" in source

    def test_has_tour_steps_list(self):
        source = open(MODULE).read()
        assert "TOUR_STEPS" in source

    def test_tour_steps_has_three_items(self):
        from utils.onboarding import TOUR_STEPS
        assert len(TOUR_STEPS) == 3

    def test_tour_steps_have_required_keys(self):
        from utils.onboarding import TOUR_STEPS
        for i, step in enumerate(TOUR_STEPS, 1):
            assert "icon" in step, f"Step {i} missing 'icon'"
            assert "title" in step, f"Step {i} missing 'title'"
            assert "body" in step, f"Step {i} missing 'body'"

    def test_render_tour_step_is_callable(self):
        from utils.onboarding import render_tour_step
        assert callable(render_tour_step)

    def test_has_progress_bar(self):
        source = open(MODULE).read()
        assert "st.progress" in source

    def test_has_skip_button(self):
        source = open(MODULE).read()
        assert "Skip Tour" in source

    def test_has_centering_columns(self):
        """Tour card should use [1, 2, 1] centering like the hero."""
        source = open(MODULE).read()
        assert "st.columns([1, 2, 1])" in source
