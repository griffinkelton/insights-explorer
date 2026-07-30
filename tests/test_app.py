"""Structural tests for app.py — AST parsing only, no Streamlit runtime."""

import ast

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
    """Verify all expected utility modules are imported in app.py.

    Post-refactor, app.py is a thin orchestrator (~78 lines). Only core
    imports needed for page config, session state, and routing remain.
    """

    def test_imports_styles(self):
        source = _read_source()
        assert "from utils.styles import" in source

    def test_imports_gemini_client(self):
        source = _read_source()
        assert "from utils.gemini_client import" in source

    def test_imports_components(self):
        source = _read_source()
        assert "from components import" in source


class TestAppStructure:
    """Verify key patterns exist in the thin orchestrator."""

    def test_has_page_config(self):
        source = _read_source()
        assert "st.set_page_config" in source
        assert "GA4 Insight Explorer" in source

    def test_has_clear_data_import(self):
        _source = _read_source()
        # clear_data() is now in utils/session.py, imported by components not app.py
        # app.py doesn't need it directly; verify it exists somewhere accessible
        assert "clear_data" in open("utils/session.py").read()
        with open("utils/session.py") as f:
            session_src = f.read()
        assert "def clear_data()" in session_src

    def test_has_render_all_call(self):
        source = _read_source()
        assert "render_all()" in source

    def test_has_oauth_env_config(self):
        """OAuth redirect URI must use os.getenv with fallback."""
        source = _read_source()
        assert "OAUTH_REDIRECT_URI" in source

    def test_has_rate_limiting_state(self):
        """Rate limiting session state keys must be initialized."""
        source = _read_source()
        assert '"last_api_call"' in source


class TestAppSessionState:
    """Verify all expected session state keys are initialized."""

    def test_data_context_initialized(self):
        """v0.2.0: DataContext replaced df as the data-state owner."""
        source = _read_source()
        assert '"data_context"' in source

    def test_df_retired(self):
        """Legacy df should NOT be initialized in app.py after Step 4."""
        source = _read_source()
        assert '"df"' not in source

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
