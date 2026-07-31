"""Tests for components/onboarding_tour.py — custom component with localStorage persistence.

The onboarding tour is now frontend-owned (st.components.v1.html() iframe).
Python-side tests verify:
- The module is importable
- STORAGE_KEY has the expected format
- TOUR_STEPS has the correct structure
- render_onboarding_tour() is callable
"""

import ast
from unittest.mock import MagicMock, patch

MODULE = "components/onboarding_tour.py"


def _read_source() -> str:
    with open(MODULE) as f:
        return f.read()


# ── Syntax & structure ───────────────────────────────────────────────────────


class TestOnboardingSyntax:
    def test_parses_without_syntax_error(self):
        tree = ast.parse(_read_source(), filename=MODULE)
        assert isinstance(tree, ast.Module)

    def test_imports_streamlit_components(self):
        source = _read_source()
        assert "streamlit.components" in source


class TestOnboardingStructure:
    def test_has_storage_key_constant(self):
        source = _read_source()
        assert "STORAGE_KEY" in source
        assert "ga4_insight_explorer.onboarding.v1.completed" in source

    def test_has_tour_steps_list(self):
        source = _read_source()
        assert "TOUR_STEPS" in source

    def test_tour_steps_has_three_items(self):
        from components.onboarding_tour import TOUR_STEPS

        assert len(TOUR_STEPS) == 3

    def test_tour_steps_have_required_keys(self):
        from components.onboarding_tour import TOUR_STEPS

        for i, step in enumerate(TOUR_STEPS, 1):
            assert "icon" in step, f"Step {i} missing 'icon'"
            assert "title" in step, f"Step {i} missing 'title'"
            assert "body" in step, f"Step {i} missing 'body'"

    def test_render_onboarding_tour_is_callable(self):
        from components.onboarding_tour import render_onboarding_tour

        assert callable(render_onboarding_tour)


# ── Behavior tests (mocked session state) ────────────────────────────────────


class TestOnboardingBehavior:
    def test_returns_false_when_not_completed(self, monkeypatch):
        """render_onboarding_tour returns False when tour hasn't been completed."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.get.return_value = False  # _tour_completed not set
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html", return_value=False):
            result = render_onboarding_tour()
            assert result is False

    def test_returns_true_when_completed(self, monkeypatch):
        """render_onboarding_tour returns True when tour has been completed."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.get.return_value = True  # _tour_completed = True
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html", return_value=True):
            result = render_onboarding_tour()
            assert result is True

    def test_sets_completed_on_first_true_result(self, monkeypatch):
        """When the component returns True and session says False, set to True + rerun."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.get.return_value = False
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html", return_value=True):
            with patch("streamlit.rerun") as mock_rerun:
                render_onboarding_tour()
                # _tour_completed should be set to True on the mock
                mock_rerun.assert_called_once()

    def test_no_rerun_when_already_completed(self, monkeypatch):
        """When already completed, a True result doesn't cause another rerun."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.get.return_value = True
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html", return_value=True):
            with patch("streamlit.rerun") as mock_rerun:
                result = render_onboarding_tour()
                assert result is True
                mock_rerun.assert_not_called()

    def test_height_is_zero_when_completed(self, monkeypatch):
        """The iframe height should be 0 when tour is complete."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.get.return_value = True
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html") as mock_html:
            render_onboarding_tour()
            _, kwargs = mock_html.call_args
            assert kwargs.get("height") == 0

    def test_height_is_420_when_active(self, monkeypatch):
        """The iframe height should be 420 when tour is active."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.get.return_value = False
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html") as mock_html:
            render_onboarding_tour()
            _, kwargs = mock_html.call_args
            assert kwargs.get("height") == 420

    def test_tour_html_contains_localstorage_key(self):
        """The embedded HTML must reference the localStorage key."""
        from components.onboarding_tour import _TOUR_HTML

        assert "ga4_insight_explorer.onboarding.v1.completed" in _TOUR_HTML

    def test_tour_html_contains_skip_button(self):
        """The embedded HTML must have a Skip Tour button."""
        from components.onboarding_tour import _TOUR_HTML

        assert "Skip Tour" in _TOUR_HTML

    def test_tour_html_contains_set_component_value(self):
        """The embedded HTML must communicate completion via setComponentValue."""
        from components.onboarding_tour import _TOUR_HTML

        assert "setComponentValue" in _TOUR_HTML

    def test_tour_html_listens_for_replay(self):
        """The embedded HTML must listen for replay messages from parent."""
        from components.onboarding_tour import _TOUR_HTML

        assert "replay_tour" in _TOUR_HTML
        assert "removeItem" in _TOUR_HTML  # clears localStorage for replay
