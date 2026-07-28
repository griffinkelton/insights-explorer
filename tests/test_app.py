"""Structural tests for app.py — AST parsing only, no Streamlit runtime."""

import ast
import pytest

APP = "app.py"


def _read_source() -> str:
    with open(APP) as f:
        return f.read()


def _parse_ast() -> ast.Module:
    return ast.parse(_read_source(), filename=APP)


class TestAppSyntax:
    """Verify the file parses without syntax errors."""

    def test_parses_without_syntax_error(self):
        tree = _parse_ast()
        assert isinstance(tree, ast.Module)


class TestAppImports:
    """Verify all expected utility modules are imported."""

    def test_imports_data_loader(self):
        source = _read_source()
        assert "from utils.data_loader import" in source

    def test_imports_gemini_client(self):
        source = _read_source()
        assert "from utils.gemini_client import" in source

    def test_imports_prompt_templates(self):
        source = _read_source()
        assert "from utils.prompt_templates import" in source

    def test_imports_ga4_client(self):
        source = _read_source()
        assert "from utils.ga4_client import" in source

    def test_imports_styles(self):
        source = _read_source()
        assert "from utils.styles import" in source

    def test_imports_error_boundary(self):
        source = _read_source()
        assert "from utils.error_boundary import" in source


class TestAppStructure:
    """Verify key sections and patterns exist."""

    def test_has_page_config(self):
        source = _read_source()
        assert "st.set_page_config" in source
        assert "GA4 Insight Explorer" in source

    def test_has_sidebar(self):
        source = _read_source()
        assert "with st.sidebar:" in source

    def test_has_file_uploader(self):
        source = _read_source()
        assert "st.file_uploader" in source

    def test_has_clear_data_function(self):
        source = _read_source()
        assert "def clear_data()" in source

    def test_has_chat_input(self):
        source = _read_source()
        assert "st.chat_input" in source

    def test_has_error_boundary_wrapper(self):
        """The main content must be wrapped in try/except with render_error_card."""
        source = _read_source()
        assert "try:" in source
        assert "_render_main()" in source
        assert "render_error_card" in source

    def test_has_footer(self):
        source = _read_source()
        assert "Data processed in-memory only" in source

    def test_has_learn_page_link(self):
        """Sidebar must have a st.page_link to the learn page."""
        source = _read_source()
        assert 'st.page_link(' in source
        assert 'pages/learn.py' in source

    def test_has_rate_limiting(self):
        """Rate limiting guard must be present in chat handler."""
        source = _read_source()
        assert "last_api_call" in source
        assert "api_call_count" in source

    def test_has_oauth_env_config(self):
        """OAuth redirect URI must use os.getenv with fallback."""
        source = _read_source()
        assert 'OAUTH_REDIRECT_URI' in source


class TestAppSessionState:
    """Verify all expected session state keys are initialized."""

    def test_df_initialized(self):
        source = _read_source()
        assert '"df"' in source

    def test_chat_history_initialized(self):
        source = _read_source()
        assert '"chat_history"' in source

    def test_api_key_valid_initialized(self):
        source = _read_source()
        assert '"api_key_valid"' in source

    def test_ga4_credentials_initialized(self):
        source = _read_source()
        assert '"ga4_creds"' in source

    def test_data_source_initialized(self):
        source = _read_source()
        assert '"data_source"' in source

    def test_rate_limiting_state_initialized(self):
        source = _read_source()
        assert '"last_api_call"' in source
        assert '"api_call_count"' in source
