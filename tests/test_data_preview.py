"""Tests for components/data_preview.py — 5-test pattern."""

import ast

MODULE = "components/data_preview.py"


def _parse() -> ast.Module:
    with open(MODULE) as f:
        return ast.parse(f.read(), filename=MODULE)


class TestDataPreviewSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestDataPreviewImport:
    def test_module_imports_without_error(self):
        from components.data_preview import render_data_preview

        assert callable(render_data_preview)


class TestDataPreviewStructure:
    def test_has_render_function(self):
        source = open(MODULE).read()
        assert "def render_data_preview()" in source

    def test_no_on_click_anti_pattern(self):
        source = open(MODULE).read()
        assert "on_click=" not in source

    def test_no_bare_except_exception(self):
        source = open(MODULE).read()
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if "except Exception" in line and "pass" in line:
                context = "\n".join(lines[max(0, i - 1) : i + 1])
                assert "#" in context, f"except Exception: pass without comment at line {i + 1}"


class TestInterstitialLightAccents:
    """A3/A4 (interstitial PR-L4): insight + grade accents are theme-aware
    via _accent(); the grade caption uses --text-muted."""

    def test_has_theme_aware_accent_helper(self):
        source = open(MODULE).read()
        assert "def _accent(dark_hex: str, light_hex: str)" in source

    def test_insight_accents_have_light_variants(self):
        source = open(MODULE).read()
        for pair in (
            '_accent("#34d399", "#059669")',
            '_accent("#f87171", "#dc2626")',
            '_accent("#818cf8", "#4f46e5")',
            '_accent("#c4b5fd", "#6366f1")',
            '_accent("#fbbf24", "#d97706")',
        ):
            assert pair in source, f"missing theme-aware accent {pair}"

    def test_grade_palette_is_theme_aware(self):
        source = open(MODULE).read()
        assert '_accent("#f59e0b", "#c2410c")' in source
        assert '_accent("#686880", "#6b7280")' in source

    def test_grade_caption_uses_text_muted(self):
        source = open(MODULE).read()
        assert "color:var(--text-muted)" in source
