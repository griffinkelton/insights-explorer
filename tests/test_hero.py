"""Tests for components/hero.py — 5-test pattern."""

import ast

HERO = "components/hero.py"


def _parse() -> ast.Module:
    with open(HERO) as f:
        return ast.parse(f.read(), filename=HERO)


class TestHeroSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestHeroImport:
    def test_module_imports_without_error(self):
        from components.hero import render_hero

        assert callable(render_hero)


class TestHeroStructure:
    def test_has_render_hero_function(self):
        source = open(HERO).read()
        assert "def render_hero()" in source

    def test_no_on_click_anti_pattern(self):
        source = open(HERO).read()
        assert "on_click=" not in source

    def test_no_bare_except_exception(self):
        source = open(HERO).read()
        # Allow only if there's a comment explaining it
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if "except Exception" in line and "pass" in line:
                # Check nearby lines for a comment explaining the reason
                context = "\n".join(lines[max(0, i - 1) : i + 1])
                assert "#" in context, f"except Exception: pass without comment at line {i + 1}"
