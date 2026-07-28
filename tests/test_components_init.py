"""Tests for components/__init__.py — 5-test pattern."""

import ast

MODULE = "components/__init__.py"


def _parse() -> ast.Module:
    with open(MODULE) as f:
        return ast.parse(f.read(), filename=MODULE)


class TestInitSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestInitImport:
    def test_module_imports_without_error(self):
        from components import render_all
        assert callable(render_all)


class TestInitStructure:
    def test_has_render_all_function(self):
        source = open(MODULE).read()
        assert "def render_all()" in source

    def test_has_render_main_content(self):
        source = open(MODULE).read()
        assert "def _render_main_content()" in source

    def test_has_oauth_handler(self):
        source = open(MODULE).read()
        assert "def _handle_oauth_callback()" in source

    def test_has_error_boundary(self):
        source = open(MODULE).read()
        assert "render_error_card" in source

    def test_has_footer(self):
        source = open(MODULE).read()
        assert "Data processed in-memory only" in source
