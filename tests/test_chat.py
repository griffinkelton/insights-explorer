"""Tests for components/chat.py — 5-test pattern."""

import ast

MODULE = "components/chat.py"


def _parse() -> ast.Module:
    with open(MODULE) as f:
        return ast.parse(f.read(), filename=MODULE)


class TestChatSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestChatImport:
    def test_module_imports_without_error(self):
        from components.chat import render_chat_section
        assert callable(render_chat_section)


class TestChatStructure:
    def test_has_render_function(self):
        source = open(MODULE).read()
        assert "def render_chat_section()" in source

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

    def test_stream_chat_has_side_effect_docstring(self):
        """_stream_chat_response must document its in-place mutation side effect."""
        source = open(MODULE).read()
        assert "SIDE EFFECT" in source or "side effect" in source.lower()
