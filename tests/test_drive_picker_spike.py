"""Structural tests for Phase 0 Drive Picker transport spike.

These tests verify source-level contracts only — the actual bridge behaviour
can only be validated in a real browser (Phase 0 acceptance gates).

Branch: spike/drive-picker-transport  —  DELETED after the Phase 0 gate decision.
"""

from __future__ import annotations

from components.drive_picker_spike import (
    _json_for_script,
    _picker_iframe_html,
    _token_has_drive_scope,
)


class TestJsonForScript:
    """JSON serialization for safe HTML <script> embedding."""

    def test_plain_object(self) -> None:
        result = _json_for_script({"key": "value"})
        assert '"key"' in result
        assert '"value"' in result

    def test_script_tag_injection_blocked(self) -> None:
        """A value containing </script> must be escaped so it cannot terminate
        the enclosing HTML script element."""
        dangerous = {"payload": "</script><script>alert(1)"}
        result = _json_for_script(dangerous)
        assert "</script>" not in result
        assert "\\u003c/script>" in result

    def test_angle_bracket_in_string(self) -> None:
        result = _json_for_script({"name": "a < b"})
        assert "\\u003c" in result
        assert "a < b" not in result

    def test_ascii_values_preserved(self) -> None:
        result = _json_for_script({"emoji": "🚀", "text": "hello"})
        assert "🚀" in result
        assert "hello" in result


class TestPickerIframeHtml:
    """Template generation with safe config injection."""

    def test_config_embedded_as_js_variable(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        # Config includes appOrigin (passed from Python, not iframe-computed)
        assert 'var CONFIG = {"oauthToken": "tok"' in html
        assert '"appOrigin": "http://localhost:8501"' in html

    def test_config_as_js_variable(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        # Config is now a JS variable assignment, not JSON.parse
        assert "var CONFIG = {" in html
        assert "gapi.load" in html

    def test_picker_callback_exists(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        assert "function pickerCallback" in html
        assert "google.picker.Action.PICKED" in html
        assert "google.picker.Action.CANCEL" in html

    def test_bridge_to_streamlit_exists(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        assert "function bridgeToStreamlit" in html

    def test_hidden_input_aria_label_targeted(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        assert "_drive_picker_bridge" in html

    def test_native_input_value_setter_used(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        assert "getOwnPropertyDescriptor" in html
        assert "HTMLInputElement.prototype" in html

    def test_input_and_change_events_dispatched(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        assert 'new Event("input"' in html
        assert 'new Event("change"' in html

    def test_oauth_token_in_js_config(self) -> None:
        """OAuth token should appear in var CONFIG = {...} JS statement.

        The _json_for_script() function prevents </script> injection."""
        html = _picker_iframe_html(oauth_token="secret-token-abc", api_key="key")
        assert "secret-token-abc" in html
        assert "var CONFIG = {" in html

    def test_config_escape_prevents_script_breakout(self) -> None:
        """If token or API key contain </script>, it must be escaped to
        \\u003c/script> so it cannot close the enclosing script element."""
        html = _picker_iframe_html(oauth_token="tok</script><script>alert(1)", api_key="key")
        # The raw </script> must not appear in a way that closes the script
        assert "</script>" not in html.replace("</script>\n</body>", "X")
        # Escaped form should be present
        assert "\\u003c/script>" in html

    def test_api_key_in_js_config(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="api-key-123")
        assert "api-key-123" in html
        assert "var CONFIG = {" in html

    def test_set_origin_uses_app_origin(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        # Origin now comes from Python config, not iframe-computed
        assert ".setOrigin(CONFIG.appOrigin)" in html
        assert '"appOrigin": "http://localhost:8501"' in html

    def test_spreadsheet_mime_types_configured(self) -> None:
        html = _picker_iframe_html(oauth_token="tok", api_key="key")
        assert "application/vnd.google-apps.spreadsheet" in html
        assert "text/csv" in html
        assert ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") in html


class TestTokenHasDriveScope:
    """drive.file scope detection on stored credentials."""

    def test_no_credentials_returns_false(self) -> None:
        import streamlit as st

        saved = st.session_state.get("ga4_creds", None)
        st.session_state.ga4_creds = None
        try:
            assert _token_has_drive_scope() is False
        finally:
            st.session_state.ga4_creds = saved

    def test_credentials_with_drive_scope(self) -> None:
        import streamlit as st

        saved = st.session_state.get("ga4_creds", None)
        st.session_state.ga4_creds = {
            "token": "tok",
            "refresh_token": "ref",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "cid",
            "client_secret": "cs",
            "scopes": [
                "https://www.googleapis.com/auth/analytics.readonly",
                "https://www.googleapis.com/auth/drive.file",
            ],
        }
        try:
            assert _token_has_drive_scope() is True
        finally:
            st.session_state.ga4_creds = saved

    def test_credentials_without_drive_scope(self) -> None:
        import streamlit as st

        saved = st.session_state.get("ga4_creds", None)
        st.session_state.ga4_creds = {
            "token": "tok",
            "refresh_token": "ref",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "cid",
            "client_secret": "cs",
            "scopes": [
                "https://www.googleapis.com/auth/analytics.readonly",
            ],
        }
        try:
            assert _token_has_drive_scope() is False
        finally:
            st.session_state.ga4_creds = saved
