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
                context = "\n".join(lines[max(0, i - 1):i + 1])
                assert "#" in context, f"except Exception: pass without comment at line {i + 1}"
