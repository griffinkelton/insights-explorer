"""Tests for components/onboarding_tour.py — v0.2.0 replay-fixed contract.

The onboarding tour is browser-persisted via localStorage inside an
st.components.v1.html() iframe.  Python has no knowledge of localStorage
and passes a one-shot ``force_replay`` render flag to clear the key.

Key contract (post-replay-fix):
- _tour_html(force_replay=bool) builds the iframe HTML
- _TOUR_HTML_TEMPLATE is the raw template (not _TOUR_HTML)
- FORCE_REPLAY = true  only when force_replay is True
- clearCompleted() runs before isCompleted() in FORCE_REPLAY path
- render_onboarding_tour() pops _tour_replay_requested, always height=420
- No _tour_completed session-state key
- No window.Streamlit.setComponentValue() call
- No addEventListener('message', ...) replay_tour handler
- Progress bar uses role="progressbar" with ARIA attrs
- Buttons have focus-visible styling
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

    def test_uses_template_not_static_html(self):
        """The module should define _TOUR_HTML_TEMPLATE, not _TOUR_HTML."""
        source = _read_source()
        assert "_TOUR_HTML_TEMPLATE" in source

    def test_has_tour_html_builder(self):
        """_tour_html(force_replay=bool) builds the rendered HTML."""
        source = _read_source()
        assert "def _tour_html" in source
        assert "force_replay" in source

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


# ── _tour_html builder ──────────────────────────────────────────────────────


class TestTourHtmlBuilder:
    def test_normal_render_has_force_replay_false(self):
        """Normal render (no replay) must embed FORCE_REPLAY = false."""
        from components.onboarding_tour import _tour_html

        html = _tour_html(force_replay=False)
        assert "FORCE_REPLAY = false" in html

    def test_replay_render_has_force_replay_true(self):
        """Replay render must embed FORCE_REPLAY = true."""
        from components.onboarding_tour import _tour_html

        html = _tour_html(force_replay=True)
        assert "FORCE_REPLAY = true" in html

    def test_clear_completed_called_before_is_completed_in_replay(self):
        """FORCE_REPLAY path: clearCompleted() must precede isCompleted()."""
        from components.onboarding_tour import _tour_html

        html = _tour_html(force_replay=True)

        # Scope to the entry-point block — function definitions naturally
        # declare isCompleted() first, but the entry point must clear first.
        entry_marker = "// ── Entry point"
        entry_start = html.index(entry_marker)
        entry_block = html[entry_start:]

        clear_pos = entry_block.index("clearCompleted()")
        completed_pos = entry_block.index("isCompleted()")
        assert clear_pos < completed_pos, (
            "In the entry-point block, clearCompleted() must be called "
            "before isCompleted() so the cleared key is visible to the check"
        )

    def test_storage_key_appears_in_rendered_html(self):
        """The rendered HTML must embed the literal storage key value."""
        from components.onboarding_tour import _tour_html, STORAGE_KEY

        html = _tour_html(force_replay=False)
        assert STORAGE_KEY in html, (
            "STORAGE_KEY must appear in the rendered HTML " "after placeholder replacement"
        )

    def test_contains_skip_button(self):
        from components.onboarding_tour import _TOUR_HTML_TEMPLATE

        assert "Skip Tour" in _TOUR_HTML_TEMPLATE

    def test_contains_progressbar_with_aria(self):
        """Progress bar must expose semantics: role, aria-valuenow/min/max."""
        from components.onboarding_tour import _TOUR_HTML_TEMPLATE

        assert 'role="progressbar"' in _TOUR_HTML_TEMPLATE
        assert "aria-valuenow" in _TOUR_HTML_TEMPLATE
        assert "aria-valuemin" in _TOUR_HTML_TEMPLATE
        assert "aria-valuemax" in _TOUR_HTML_TEMPLATE

    def test_has_focus_visible_css(self):
        """Buttons must show visible focus styling."""
        from components.onboarding_tour import _TOUR_HTML_TEMPLATE

        assert ":focus-visible" in _TOUR_HTML_TEMPLATE
        assert "outline" in _TOUR_HTML_TEMPLATE


# ── render_onboarding_tour behavior ─────────────────────────────────────────


class TestRenderOnboardingTour:
    def test_pops_replay_requested_from_session(self, monkeypatch):
        """render_onboarding_tour consumes _tour_replay_requested via pop."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.pop.return_value = False  # no replay requested
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html"):
            render_onboarding_tour()

        mock_session.pop.assert_called_once_with("_tour_replay_requested", False)

    def test_always_uses_height_420(self, monkeypatch):
        """The iframe height is always 420 — no dynamic collapse to 0."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.pop.return_value = False
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html") as mock_html:
            render_onboarding_tour()
            _, kwargs = mock_html.call_args
            assert kwargs.get("height") == 420

    def test_returns_none(self, monkeypatch):
        """render_onboarding_tour returns None — no bool bridge."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.pop.return_value = False
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("streamlit.components.v1.html"):
            result = render_onboarding_tour()
            assert result is None

    def test_passes_force_replay_true_to_builder(self, monkeypatch):
        """When _tour_replay_requested is True, builder gets force_replay=True."""
        import streamlit as st
        from components.onboarding_tour import render_onboarding_tour

        mock_session = MagicMock()
        mock_session.pop.return_value = True  # replay was requested
        monkeypatch.setattr(st, "session_state", mock_session)

        with patch("components.onboarding_tour._tour_html") as mock_builder:
            mock_builder.return_value = "<html></html>"
            with patch("streamlit.components.v1.html"):
                render_onboarding_tour()
            mock_builder.assert_called_once_with(force_replay=True)


# ── Contract: removed/absent items ───────────────────────────────────────────


class TestRetiredContract:
    """Verify that the old contract items are truly gone."""

    def test_no_tour_completed_in_source(self):
        """Production code must not reference _tour_completed."""
        source = _read_source()
        assert (
            "_tour_completed" not in source
        ), "_tour_completed is retired; localStorage is the sole authority"

    def test_no_set_component_value_in_html(self):
        """No window.Streamlit.setComponentValue in the iframe HTML."""
        from components.onboarding_tour import _TOUR_HTML_TEMPLATE

        assert (
            "setComponentValue" not in _TOUR_HTML_TEMPLATE
        ), "setComponentValue is not supported by st.components.v1.html()"

    def test_no_replay_message_listener_in_source(self):
        """No addEventListener('message', ...) replay handler — no sender exists."""
        source = _read_source()
        assert "replay_tour" not in source, (
            "The replay_tour message listener has no parent-side sender; "
            "force_replay flag replaces it"
        )

    def test_no_streamlit_dot_set_component_value(self):
        """Check specifically for window.Streamlit.setComponentValue."""
        source = _read_source()
        assert "Streamlit.setComponentValue" not in source

    def test_no_static_tour_html_constant(self):
        """The old _TOUR_HTML constant should not exist."""
        source = _read_source()
        # _TOUR_HTML_TEMPLATE is fine; bare _TOUR_HTML = is not
        lines = source.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("_TOUR_HTML ") or stripped.startswith("_TOUR_HTML="):
                assert False, "Old _TOUR_HTML constant found — use _TOUR_HTML_TEMPLATE"


# ── Replay button contract (hero.py) ─────────────────────────────────────────


class TestReplayButtonContract:
    """The Replay button in hero.py must set _tour_replay_requested + rerun."""

    def test_hero_sets_replay_requested(self):
        """hero.py must contain the replay flag name."""
        with open("components/hero.py") as f:
            hero_source = f.read()
        assert (
            "_tour_replay_requested" in hero_source
        ), "hero.py must set _tour_replay_requested = True on replay"
        assert (
            "st.rerun()" in hero_source
        ), "hero.py must call st.rerun() after setting the replay flag"
