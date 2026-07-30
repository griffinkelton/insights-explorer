"""Tests for utils/styles.py — validate theme guard, CSS structure, and JS injection."""

import re
from unittest.mock import MagicMock, patch

import pytest

import utils.styles as styles


# ── VALID_THEMES ──────────────────────────────────────────────────────────────


class TestValidThemes:
    def test_contains_dark_and_light(self):
        """VALID_THEMES must contain exactly 'dark' and 'light'."""
        assert styles.VALID_THEMES == {"dark", "light"}

    def test_is_set_type(self):
        """VALID_THEMES is a set — ensure it hasn't accidentally become a list."""
        assert isinstance(styles.VALID_THEMES, set)


# ── inject_favicon_meta ──────────────────────────────────────────────────────


class TestInjectFaviconMeta:
    @staticmethod
    def _call(theme="dark"):
        """Call inject_favicon_meta with st.markdown mocked, return the HTML string."""
        mock_md = MagicMock()
        with patch.object(styles.st, "markdown", mock_md):
            styles.inject_favicon_meta(theme)
        return mock_md.call_args[0][0]  # first positional arg to st.markdown

    def test_dark_theme_outputs_dark_theme_color(self):
        html = self._call("dark")
        assert 'content="#0a0a0f"' in html
        assert "theme-color" in html

    def test_light_theme_outputs_light_theme_color(self):
        html = self._call("light")
        assert 'content="#ffffff"' in html

    def test_includes_favicon_links(self):
        html = self._call("dark")
        assert 'rel="icon"' in html
        assert 'rel="shortcut icon"' in html
        assert 'rel="apple-touch-icon"' in html
        assert 'rel="manifest"' in html

    def test_includes_og_tags(self):
        html = self._call("dark")
        assert "og:title" in html
        assert "og:description" in html
        assert "og:image" in html
        assert "twitter:card" in html

    def test_invalid_theme_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            styles.inject_favicon_meta("green")

    def test_invalid_theme_message_includes_valid_themes(self):
        with pytest.raises(ValueError, match="Valid themes"):
            styles.inject_favicon_meta("blue")

    def test_calls_st_markdown_with_unsafe_allow_html(self):
        mock_md = MagicMock()
        with patch.object(styles.st, "markdown", mock_md):
            styles.inject_favicon_meta("dark")
        assert mock_md.call_args[1].get("unsafe_allow_html") is True


# ── inject_custom_css ────────────────────────────────────────────────────────


class TestInjectCustomCss:
    @staticmethod
    def _call(theme="dark"):
        """Call inject_custom_css with st.markdown mocked, return the HTML/CSS/JS string."""
        mock_md = MagicMock()
        with patch.object(styles.st, "markdown", mock_md):
            styles.inject_custom_css(theme)
        return mock_md.call_args[0][0]

    # ── Theme validation ─────────────────────────────────────────────────

    def test_dark_theme_passes_validation(self):
        html = self._call("dark")
        assert html  # no exception raised

    def test_light_theme_passes_validation(self):
        html = self._call("light")
        assert html  # no exception raised

    def test_invalid_theme_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            styles.inject_custom_css("red")

    def test_invalid_theme_message_includes_valid_theme_names(self):
        with pytest.raises(ValueError, match="Valid themes"):
            styles.inject_custom_css("purple")

    # ── Data-theme attribute ─────────────────────────────────────────────

    def test_includes_data_theme_div(self):
        html = self._call("dark")
        assert 'data-theme="dark"' in html

    def test_light_theme_sets_data_theme_light(self):
        html = self._call("light")
        assert 'data-theme="light"' in html

    # ── CSS variables ────────────────────────────────────────────────────

    def test_includes_css_root_variables(self):
        html = self._call("dark")
        assert "--bg-secondary" in html
        assert "--text-primary" in html
        assert "--accent" in html
        assert "--radius-md" in html

    def test_includes_both_theme_variable_sets(self):
        html = self._call("dark")
        # Default (dark) variables
        assert "--bg-secondary: #12121a" in html
        # Light overrides
        assert '[data-theme="light"]' in html

    def test_light_theme_overrides_present(self):
        html = self._call("dark")
        assert "--bg-primary: #ffffff" in html  # inside light override block

    # ── Keyboard shortcut JS ─────────────────────────────────────────────

    def test_includes_keyboard_shortcut_script(self):
        html = self._call("dark")
        assert "Cmd/Ctrl + K" in html

    def test_includes_theme_sync_js(self):
        html = self._call("dark")
        assert "getElementById('theme-data')" in html
        assert "setAttribute('data-theme'" in html

    def test_includes_guard_against_duplicate_listener(self):
        html = self._call("dark")
        assert "__ga4ExplorerShortcutInstalled" in html

    def test_includes_reduced_motion_media_query(self):
        html = self._call("dark")
        assert "prefers-reduced-motion" in html

    # ── CSS structure ────────────────────────────────────────────────────

    def test_includes_global_style_tag(self):
        html = self._call("dark")
        assert "<style>" in html
        assert "</style>" in html

    def test_includes_script_tag(self):
        html = self._call("dark")
        assert "<script>" in html
        assert "</script>" in html

    def test_css_is_not_empty(self):
        html = self._call("dark")
        # Extract content between style tags
        match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
        assert match is not None
        css = match.group(1).strip()
        assert len(css) > 500  # substantial CSS content

    # ── Accessibility ────────────────────────────────────────────────────

    def test_includes_reduced_motion_support(self):
        html = self._call("dark")
        assert "animation-duration: 0.01ms" in html

    # ── st.markdown call ─────────────────────────────────────────────────

    def test_calls_st_markdown_with_unsafe_allow_html(self):
        mock_md = MagicMock()
        with patch.object(styles.st, "markdown", mock_md):
            styles.inject_custom_css("dark")
        assert mock_md.call_args[1].get("unsafe_allow_html") is True
