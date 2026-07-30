"""Tests for utils/error_boundary.py — verify error cards render correctly."""

from unittest.mock import patch, MagicMock

import utils.error_boundary as eb


class TestRenderErrorCardProduction:
    """Test production mode rendering (SHOW_DEBUG_DETAILS=false, the default)."""

    @staticmethod
    def _mock_streamlit():
        return {
            "error": MagicMock(),
            "expander": MagicMock(),
            "markdown": MagicMock(),
            "code": MagicMock(),
            "caption": MagicMock(),
        }

    def _call_in_production(self, error, context=""):
        mocks = self._mock_streamlit()
        with (
            patch.object(eb, "SHOW_DEBUG_DETAILS", False),
            patch.object(eb.st, "error", mocks["error"]),
            patch.object(eb.st, "expander", mocks["expander"]),
            patch.object(eb.st, "markdown", mocks["markdown"]),
            patch.object(eb.st, "code", mocks["code"]),
            patch.object(eb.st, "caption", mocks["caption"]),
        ):
            eb.render_error_card(error, context)
        return mocks

    def test_shows_generic_message_not_raw_exception(self):
        """Production mode hides exception type/message."""
        err = ValueError("secret details")
        mocks = self._call_in_production(err)
        error_text = mocks["error"].call_args[0][0]
        assert "Something went wrong" in error_text
        assert "ValueError" not in error_text
        assert "secret details" not in error_text

    def test_shows_error_id(self):
        """Production mode shows a reference error ID."""
        err = RuntimeError("test")
        mocks = self._call_in_production(err)
        error_text = mocks["error"].call_args[0][0]
        assert "error ID" in error_text.lower() or "`" in error_text

    def test_no_expander_in_production(self):
        """Production mode does not show the technical details expander."""
        err = RuntimeError("test")
        mocks = self._call_in_production(err)
        mocks["expander"].assert_not_called()

    def test_no_traceback_in_production(self):
        """Production mode does not render tracebacks."""
        err = RuntimeError("test")
        mocks = self._call_in_production(err)
        mocks["code"].assert_not_called()


class TestRenderErrorCardDebug:
    """Test debug mode rendering (SHOW_DEBUG_DETAILS=true)."""

    @staticmethod
    def _mock_streamlit():
        return {
            "error": MagicMock(),
            "expander": MagicMock(),
            "markdown": MagicMock(),
            "code": MagicMock(),
            "caption": MagicMock(),
        }

    def _call_in_debug(self, error, context=""):
        mocks = self._mock_streamlit()
        with (
            patch.object(eb, "SHOW_DEBUG_DETAILS", True),
            patch.object(eb.st, "error", mocks["error"]),
            patch.object(eb.st, "expander", mocks["expander"]),
            patch.object(eb.st, "markdown", mocks["markdown"]),
            patch.object(eb.st, "code", mocks["code"]),
            patch.object(eb.st, "caption", mocks["caption"]),
        ):
            eb.render_error_card(error, context)
        return mocks

    def test_renders_error_type_and_message(self):
        err = ValueError("something went wrong")
        mocks = self._call_in_debug(err)
        error_text = mocks["error"].call_args[0][0]
        assert "ValueError" in error_text
        assert "something went wrong" in error_text

    def test_includes_context_when_provided(self):
        err = RuntimeError("boom")
        mocks = self._call_in_debug(err, context="loading file")
        error_text = mocks["error"].call_args[0][0]
        assert "while loading file" in error_text

    def test_shows_stack_trace_in_expander(self):
        err = RuntimeError("test")
        mocks = self._call_in_debug(err)
        mocks["expander"].assert_called_once()

    def test_stack_trace_is_passed_to_code_block(self):
        err = RuntimeError("test")
        fake_trace = 'Traceback (most recent call last):\n  File "app.py", line 5, in foo\nRuntimeError: test\n'
        with patch.object(eb.traceback, "format_exc", return_value=fake_trace):
            mocks = self._call_in_debug(err)
        mocks["code"].assert_called_once()

    def test_shows_issue_link_in_caption(self):
        err = RuntimeError("test")
        mocks = self._call_in_debug(err)
        mocks["caption"].assert_called_once()
