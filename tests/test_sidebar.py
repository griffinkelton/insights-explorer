"""Tests for components/sidebar.py — 5-test pattern."""

import ast

MODULE = "components/sidebar.py"


def _parse() -> ast.Module:
    with open(MODULE) as f:
        return ast.parse(f.read(), filename=MODULE)


class TestSidebarSyntax:
    def test_parses_without_syntax_error(self):
        tree = _parse()
        assert isinstance(tree, ast.Module)


class TestSidebarImport:
    def test_module_imports_without_error(self):
        from components.sidebar import render_sidebar
        assert callable(render_sidebar)


class TestSidebarStructure:
    def test_has_render_function(self):
        source = open(MODULE).read()
        assert "def render_sidebar()" in source

    def test_has_theme_toggle_function(self):
        """Theme toggle: _render_theme_toggle must exist in sidebar."""
        source = open(MODULE).read()
        assert "def _render_theme_toggle()" in source

    def test_clear_button_no_on_click_anti_pattern(self):
        """BUG-005: _render_clear_button uses `if st.button`, not `on_click=`."""
        import re
        source = open(MODULE).read()
        # Extract the _render_clear_button function body
        idx = source.find("def _render_clear_button")
        assert idx > 0, "Missing _render_clear_button function"
        next_def = source.find("\ndef ", idx + 1)
        func_source = source[idx:next_def if next_def > 0 else len(source)]
        # Strip docstrings and comments before checking for on_click=
        code = re.sub(r'""".*?"""', '', func_source, flags=re.DOTALL)
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        assert "on_click=" not in code, (
            "BUG-005: on_click= anti-pattern in _render_clear_button"
        )

    def test_clear_data_uses_button_if_pattern(self):
        """Clear Data must use `if st.button(...)` pattern per BUG-005."""
        source = open(MODULE).read()
        assert "if st.button" in source
        assert "clear_data()" in source
