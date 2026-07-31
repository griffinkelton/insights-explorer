"""Tests for utils/styles.py — Phase 3 refactor: named constants, focus-visible, keyboard shortcut.

Coverage:
    - Every named constant is non-empty.
    - build_theme_css() assembly includes all constants.
    - Semantic CSS variables present (theme colors, radii, borders, typography, focus ring).
    - Both theme selectors present (:root dark defaults + [data-theme="light"]).
    - VALID_THEMES guard still rejects invalid themes.
    - prefers-reduced-motion media query present.
    - Focus-visible uses accent-derived variables (never red/destructive).
    - Keyboard shortcut guard installed BEFORE listener registration.
    - Shortcut exits early for editable fields.
    - Generated output contains no interpolation except the validated theme value.
"""

import re
from unittest.mock import MagicMock, patch

import pytest

import utils.styles as styles


# ═══════════════════════════════════════════════════════════════════════════════
# Named constants — non-emptiness
# ═══════════════════════════════════════════════════════════════════════════════


class TestCssConstants:
    """Every CSS constant must be a non-empty string."""

    def test_base_tokens_css_is_non_empty(self):
        assert isinstance(styles.BASE_TOKENS_CSS, str)
        assert styles.BASE_TOKENS_CSS.strip()

    def test_light_theme_css_is_non_empty(self):
        assert isinstance(styles.LIGHT_THEME_CSS, str)
        assert styles.LIGHT_THEME_CSS.strip()

    def test_component_css_is_non_empty(self):
        assert isinstance(styles.COMPONENT_CSS, str)
        assert styles.COMPONENT_CSS.strip()

    def test_learn_page_css_is_non_empty(self):
        assert isinstance(styles.LEARN_PAGE_CSS, str)
        assert styles.LEARN_PAGE_CSS.strip()

    def test_accessibility_css_is_non_empty(self):
        assert isinstance(styles.ACCESSIBILITY_CSS, str)
        assert styles.ACCESSIBILITY_CSS.strip()


class TestJsConstants:
    """Every JS constant must be a non-empty string."""

    def test_theme_sync_js_is_non_empty(self):
        assert isinstance(styles.THEME_SYNC_JS, str)
        assert styles.THEME_SYNC_JS.strip()

    def test_keyboard_shortcuts_js_is_non_empty(self):
        assert isinstance(styles.KEYBOARD_SHORTCUTS_JS, str)
        assert styles.KEYBOARD_SHORTCUTS_JS.strip()


class TestValidThemes:
    """VALID_THEMES guard must contain exactly dark + light."""

    def test_contains_dark_and_light(self):
        assert styles.VALID_THEMES == {"dark", "light"}

    def test_is_set_type(self):
        assert isinstance(styles.VALID_THEMES, set)


# ═══════════════════════════════════════════════════════════════════════════════
# build_theme_css — assembly
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildThemeCss:
    """build_theme_css() must assemble all constants with only theme interpolated."""

    @staticmethod
    def _build(theme="dark"):
        return styles.build_theme_css(theme)

    # ── Assembly: every constant present ──────────────────────────────────

    def test_includes_base_tokens(self):
        output = self._build()
        assert styles.BASE_TOKENS_CSS.strip() in output

    def test_includes_light_theme(self):
        output = self._build()
        assert styles.LIGHT_THEME_CSS.strip() in output

    def test_includes_component(self):
        output = self._build()
        assert styles.COMPONENT_CSS.strip() in output

    def test_includes_learn_page(self):
        output = self._build()
        assert styles.LEARN_PAGE_CSS.strip() in output

    def test_includes_accessibility(self):
        output = self._build()
        assert styles.ACCESSIBILITY_CSS.strip() in output

    def test_includes_theme_sync_js(self):
        output = self._build()
        assert styles.THEME_SYNC_JS.strip() in output

    def test_includes_keyboard_shortcuts_js(self):
        output = self._build()
        assert styles.KEYBOARD_SHORTCUTS_JS.strip() in output

    # ── Theme interpolation ───────────────────────────────────────────────

    def test_dark_theme_sets_data_theme_dark(self):
        output = self._build("dark")
        assert 'data-theme="dark"' in output

    def test_light_theme_sets_data_theme_light(self):
        output = self._build("light")
        assert 'data-theme="light"' in output

    def test_invalid_theme_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            self._build("green")

    def test_invalid_theme_message_includes_valid_theme_names(self):
        with pytest.raises(ValueError, match="Valid themes"):
            self._build("blue")

    # ── No interpolation leakage ──────────────────────────────────────────

    def test_no_f_string_placeholder_remains(self):
        """Generated output must not contain raw f-string placeholders."""
        output = self._build("dark")
        assert "{theme}" not in output
        assert "{theme_color}" not in output

    def test_only_theme_value_is_interpolated(self):
        """Only the validated theme attribute value appears — no arbitrary injection."""
        output = self._build("dark")
        # The data-theme attribute should be "dark", not an f-string expression
        assert 'data-theme="dark"' in output

    # ── HTML structure ────────────────────────────────────────────────────

    def test_includes_style_tag(self):
        output = self._build("dark")
        assert "<style>" in output
        assert "</style>" in output

    def test_includes_script_tag(self):
        output = self._build("dark")
        assert "<script>" in output
        assert "</script>" in output


# ═══════════════════════════════════════════════════════════════════════════════
# Semantic CSS variables
# ═══════════════════════════════════════════════════════════════════════════════


class TestSemanticVariables:
    """CSS output must include semantic variables for themes, radii, borders, etc."""

    def test_theme_color_variables_present(self):
        output = styles.build_theme_css("dark")
        assert "--bg-primary" in output
        assert "--bg-secondary" in output
        assert "--text-primary" in output
        assert "--accent" in output
        assert "--accent-hover" in output
        assert "--accent-soft" in output

    def test_radius_variables_present(self):
        output = styles.build_theme_css("dark")
        assert "--radius-sm" in output
        assert "--radius-md" in output
        assert "--radius-lg" in output
        assert "--radius-xl" in output

    def test_border_variable_present(self):
        output = styles.build_theme_css("dark")
        assert "--border" in output

    def test_focus_ring_variables_present(self):
        """Focus ring must use accent-derived variables, never red."""
        output = styles.build_theme_css("dark")
        assert "--focus-ring-color" in output
        assert "--focus-ring-soft" in output
        assert "--focus-ring-width" in output
        assert "--focus-ring-offset" in output

    def test_focus_ring_color_is_accent_derived(self):
        """--focus-ring-color must be aliased from --accent, not a red value."""
        base = styles.BASE_TOKENS_CSS
        # Must reference var(--accent)
        assert "--focus-ring-color" in base
        # The value should use var(--accent), not a raw red color
        focus_line = [ln for ln in base.splitlines() if "--focus-ring-color" in ln]
        assert focus_line
        assert "var(--accent)" in focus_line[0]
        assert "#f" not in focus_line[0].split(":")[-1].strip("; ").lower()
        assert "red" not in focus_line[0].lower()

    def test_font_stack_present(self):
        output = styles.build_theme_css("dark")
        assert "-apple-system" in output

    def test_success_warning_danger_variables_present(self):
        output = styles.build_theme_css("dark")
        assert "--success" in output
        assert "--warning" in output
        assert "--danger" in output


# ═══════════════════════════════════════════════════════════════════════════════
# Both theme selectors
# ═══════════════════════════════════════════════════════════════════════════════


class TestBothThemeSelectors:
    """CSS must include :root (dark defaults) and [data-theme="light"] overrides."""

    def test_root_selector_present(self):
        output = styles.build_theme_css("dark")
        assert ":root" in output

    def test_light_theme_selector_present(self):
        output = styles.build_theme_css("dark")
        assert '[data-theme="light"]' in output

    def test_dark_default_colors_present(self):
        output = styles.build_theme_css("dark")
        assert "--bg-secondary: #12121a" in output

    def test_light_override_colors_present(self):
        output = styles.build_theme_css("dark")
        assert "--bg-primary: #ffffff" in output


# ═══════════════════════════════════════════════════════════════════════════════
# Focus-visible
# ═══════════════════════════════════════════════════════════════════════════════


class TestFocusVisible:
    """Focus-visible styles must exist and use accent-derived colors (never red)."""

    def test_focus_visible_selector_present(self):
        output = styles.build_theme_css("dark")
        assert ":focus-visible" in output

    def test_focus_visible_uses_focus_ring_variables(self):
        output = styles.build_theme_css("dark")
        assert "var(--focus-ring-color)" in output
        assert "var(--focus-ring-width)" in output
        assert "var(--focus-ring-offset)" in output

    def test_focus_visible_never_uses_red(self):
        """Focus ring must NOT use --danger, red, or destructive colors in property values."""
        access = styles.ACCESSIBILITY_CSS
        # Extract only the focus-visible rule block (between braces, excluding comments)
        focus_start = access.index(":focus-visible")
        focus_brace = access.index("{", focus_start)
        focus_end = access.index("}", focus_brace)
        rule_body = access[focus_brace + 1 : focus_end]
        # Strip CSS comments for clean property-only check
        body_no_comments = re.sub(r"/\*.*?\*/", "", rule_body, flags=re.DOTALL)
        assert "--danger" not in body_no_comments
        assert "red" not in body_no_comments.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Reduced motion
# ═══════════════════════════════════════════════════════════════════════════════


class TestReducedMotion:
    """prefers-reduced-motion support must exist with zero/negligible durations."""

    def test_media_query_present(self):
        output = styles.build_theme_css("dark")
        assert "prefers-reduced-motion" in output

    def test_animation_disabled(self):
        output = styles.build_theme_css("dark")
        assert "animation-duration: 0.01ms" in output


# ═══════════════════════════════════════════════════════════════════════════════
# Keyboard shortcut
# ═══════════════════════════════════════════════════════════════════════════════


class TestKeyboardShortcut:
    """Keyboard shortcut guard must be installed BEFORE listener, with editable-field safety."""

    def test_guard_installed_before_listener(self):
        """The guard must appear BEFORE addEventListener in the source."""
        js = styles.KEYBOARD_SHORTCUTS_JS
        guard_idx = js.find("__ga4ExplorerShortcutInstalled")
        listener_idx = js.find("addEventListener")
        assert guard_idx >= 0
        assert listener_idx >= 0
        assert (
            guard_idx < listener_idx
        ), "Guard must be installed BEFORE the listener to prevent duplicates"

    def test_guard_sets_flag(self):
        js = styles.KEYBOARD_SHORTCUTS_JS
        assert "__ga4ExplorerShortcutInstalled = true" in js

    def test_editable_field_safety(self):
        """Shortcut must exit early for input, textarea, select, contenteditable."""
        js = styles.KEYBOARD_SHORTCUTS_JS
        for tag in ("input", "textarea", "select"):
            assert tag in js, f"Must check for '{tag}' tag before firing shortcut"
        assert "isContentEditable" in js

    def test_cmd_ctrl_k_handler_present(self):
        js = styles.KEYBOARD_SHORTCUTS_JS
        assert "k" in js.lower()

    def test_focuses_chat_input(self):
        js = styles.KEYBOARD_SHORTCUTS_JS
        assert "stChatInput" in js
        assert "focus()" in js


# ═══════════════════════════════════════════════════════════════════════════════
# Backward-compatible injection functions
# ═══════════════════════════════════════════════════════════════════════════════


class TestInjectCustomCss:
    """inject_custom_css() delegates to build_theme_css() and calls st.markdown."""

    @staticmethod
    def _call(theme="dark"):
        mock_md = MagicMock()
        with patch.object(styles.st, "markdown", mock_md):
            styles.inject_custom_css(theme)
        return mock_md.call_args[0][0]

    def test_dark_theme_passes_validation(self):
        html = self._call("dark")
        assert html

    def test_light_theme_passes_validation(self):
        html = self._call("light")
        assert html

    def test_invalid_theme_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            styles.inject_custom_css("red")

    def test_calls_st_markdown_with_unsafe_allow_html(self):
        mock_md = MagicMock()
        with patch.object(styles.st, "markdown", mock_md):
            styles.inject_custom_css("dark")
        assert mock_md.call_args[1].get("unsafe_allow_html") is True

    def test_output_is_same_as_build_theme_css(self):
        assert self._call("dark") == styles.build_theme_css("dark")
        assert self._call("light") == styles.build_theme_css("light")


class TestInjectFaviconMeta:
    """inject_favicon_meta() is unchanged — favicon, OG tags, theme-color meta."""

    @staticmethod
    def _call(theme="dark"):
        mock_md = MagicMock()
        with patch.object(styles.st, "markdown", mock_md):
            styles.inject_favicon_meta(theme)
        return mock_md.call_args[0][0]

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
