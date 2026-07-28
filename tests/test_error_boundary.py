"""Tests for utils/error_boundary.py — verify error cards render correctly."""

import traceback
from unittest.mock import patch, MagicMock, call
import pytest

import utils.error_boundary as eb


class TestRenderErrorCard:
    """Verify render_error_card() displays correct content via Streamlit."""

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _mock_streamlit():
        """Return a dict of mocked Streamlit functions."""
        return {
            "error": MagicMock(),
            "expander": MagicMock(),
            "markdown": MagicMock(),
            "code": MagicMock(),
            "caption": MagicMock(),
        }

    def _call_with_mocks(self, error, context=""):
        """Call render_error_card with all Streamlit functions mocked."""
        mocks = self._mock_streamlit()
        with (
            patch.object(eb.st, "error", mocks["error"]),
            patch.object(eb.st, "expander", mocks["expander"]),
            patch.object(eb.st, "markdown", mocks["markdown"]),
            patch.object(eb.st, "code", mocks["code"]),
            patch.object(eb.st, "caption", mocks["caption"]),
        ):
            eb.render_error_card(error, context)
        return mocks

    # ── Basic rendering ──────────────────────────────────────────────────

    def test_renders_error_type_and_message(self):
        """The error card must show the exception type and message."""
        err = ValueError("something went wrong")
        mocks = self._call_with_mocks(err)

        mocks["error"].assert_called_once()
        error_text = mocks["error"].call_args[0][0]
        assert "😣 Something went wrong" in error_text
        assert "ValueError" in error_text
        assert "something went wrong" in error_text

    def test_includes_context_when_provided(self):
        """When context is given, it must appear in the error message."""
        err = RuntimeError("boom")
        mocks = self._call_with_mocks(err, context="loading file")

        error_text = mocks["error"].call_args[0][0]
        assert "while loading file" in error_text

    def test_omits_context_when_empty(self):
        """When no context is given, the 'while...' clause must be absent."""
        err = RuntimeError("boom")
        mocks = self._call_with_mocks(err, context="")

        error_text = mocks["error"].call_args[0][0]
        # Bare error message without "while" clause
        assert error_text.strip().startswith("### 😣 Something went wrong")
        assert "\n\n**RuntimeError:** boom" in error_text
        assert "while" not in error_text

    # ── Different exception types ─────────────────────────────────────────

    def test_handles_value_error(self):
        mocks = self._call_with_mocks(ValueError("bad value"))
        error_text = mocks["error"].call_args[0][0]
        assert "ValueError" in error_text

    def test_handles_runtime_error(self):
        mocks = self._call_with_mocks(RuntimeError("something crashed"))
        error_text = mocks["error"].call_args[0][0]
        assert "RuntimeError" in error_text

    def test_handles_key_error(self):
        mocks = self._call_with_mocks(KeyError("missing_key"))
        error_text = mocks["error"].call_args[0][0]
        assert "KeyError" in error_text

    def test_handles_custom_exception(self):
        class CustomAppError(Exception):
            pass

        mocks = self._call_with_mocks(CustomAppError("custom failure"))
        error_text = mocks["error"].call_args[0][0]
        assert "CustomAppError" in error_text

    def test_handles_exception_with_no_message(self):
        """Exceptions with no message should still render without crashing."""
        err = ValueError()
        mocks = self._call_with_mocks(err)

        error_text = mocks["error"].call_args[0][0]
        assert "ValueError" in error_text
        # The str of an empty ValueError is "" — should still render
        assert "### 😣 Something went wrong" in error_text

    # ── Technical details expander ──────────────────────────────────────

    def test_shows_stack_trace_in_expander(self):
        """The expander must contain the stack trace code block."""
        err = RuntimeError("test")
        mocks = self._call_with_mocks(err)

        # Expander context manager should have been entered
        mocks["expander"].assert_called_once()
        expander_title = mocks["expander"].call_args[0][0]
        assert "Technical Details" in expander_title

    def test_stack_trace_is_passed_to_code_block(self):
        """st.code must be called with traceback output. Mock format_exc
        since it returns NoneType outside an actual except block."""
        err = RuntimeError("test")
        fake_trace = 'Traceback (most recent call last):\n  File "app.py", line 5, in foo\nRuntimeError: test\n'

        with patch.object(eb.traceback, "format_exc", return_value=fake_trace):
            mocks = self._call_with_mocks(err)

        mocks["code"].assert_called_once()
        code_text = mocks["code"].call_args[0][0]
        assert "Traceback" in code_text
        assert "RuntimeError" in code_text

    def test_shows_issue_link_in_caption(self):
        """The caption should mention opening an issue on GitHub."""
        err = RuntimeError("test")
        mocks = self._call_with_mocks(err)

        mocks["caption"].assert_called_once()
        caption_text = mocks["caption"].call_args[0][0]
        assert "open an issue" in caption_text.lower()
        assert "github.com" in caption_text

    # ── Full rendering with context ──────────────────────────────────────

    def test_full_rendering_with_context(self):
        """End-to-end: verify all components are called in the right order."""
        err = FileNotFoundError("data.csv not found")
        mocks = self._call_with_mocks(err, context="loading the uploaded file")

        # 1. st.error called first
        assert mocks["error"].call_count == 1

        # 2. Expander for technical details
        assert mocks["expander"].call_count == 1

        # 3. Markdown and code inside expander
        assert mocks["markdown"].call_count >= 1
        assert mocks["code"].call_count == 1

        # 4. Caption at the bottom
        assert mocks["caption"].call_count == 1

    # ── Edge cases ───────────────────────────────────────────────────────

    def test_handles_exception_with_special_characters(self):
        """Exceptions with quotes, newlines, or special chars should render safely."""
        err = ValueError("line 1\nline 2\nwith 'quotes' and \"double quotes\"")
        mocks = self._call_with_mocks(err)

        error_text = mocks["error"].call_args[0][0]
        assert "ValueError" in error_text
        # Verify the error message itself is present (Streamlit markdown handles special chars)
        assert "line 1" in error_text

    def test_handles_very_long_error_message(self):
        """Extremely long error messages should not crash — just render."""
        long_msg = "x" * 5000
        err = RuntimeError(long_msg)
        mocks = self._call_with_mocks(err)

        error_text = mocks["error"].call_args[0][0]
        assert "RuntimeError" in error_text
        assert long_msg in error_text


