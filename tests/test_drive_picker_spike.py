"""Structural tests for Phase 0 Drive Picker transport spike (Option B).

These tests verify the Python wrapper and render logic only — the actual
Picker behaviour can only be validated in a real browser (Phase 0
acceptance gates).

Option A (hidden-input bridge) was rejected; these tests cover the
declared-component approach.

Branch: spike/drive-picker-transport  —  DELETED after the Phase 0 gate decision.
"""

from __future__ import annotations

from components.drive_picker_component import drive_picker_transport
from components.drive_picker_spike import _token_has_drive_scope


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


class TestDrivePickerComponent:
    """Python wrapper for the declared Streamlit component."""

    def test_importable(self) -> None:
        """Wrapper can be imported without error."""
        assert callable(drive_picker_transport)

    def test_has_docstring(self) -> None:
        """Wrapper has documentation."""
        assert drive_picker_transport.__doc__ is not None
        assert "sanitised" in drive_picker_transport.__doc__.lower()


class TestSpikeModuleHasNoOptionA:
    """Option A artefacts must be absent from the spike module."""

    def test_no_hidden_input_bridge_in_source(self) -> None:
        """Source must not contain the rejected hidden-input bridge pattern.

        The module docstring may reference "srcdoc" for historical context
        (explaining why Option A was rejected), so we only check that the
        executable code does not use the bridge.
        """
        import inspect

        from components import drive_picker_spike

        source = inspect.getsource(drive_picker_spike)
        # No hidden Streamlit text_input bridge
        assert "_drive_picker_bridge" not in source
        # No raw Picker iframe injection
        assert "components.html(" not in source
        # No JSON config injection (that was Option A's template approach)
        assert "_json_for_script" not in source
        # No hidden-input DOM manipulation
        assert "HTMLInputElement.prototype" not in source
        assert "getOwnPropertyDescriptor" not in source

    def test_declared_component_imported(self) -> None:
        """Spike module imports the declared component wrapper."""
        import inspect

        from components import drive_picker_spike

        source = inspect.getsource(drive_picker_spike)
        assert "drive_picker_transport" in source


class TestSpikeRenderLogic:
    """render_drive_picker_spike() behavioural contracts."""

    def test_request_id_uses_setdefault(self) -> None:
        """The request_id is initialised with st.session_state.setdefault."""
        import inspect

        from components import drive_picker_spike

        source = inspect.getsource(drive_picker_spike)
        assert "setdefault" in source
        assert "_phase0_request_id" in source

    def test_result_validates_kind_and_request_id(self) -> None:
        """Success path checks both kind and requestId before acting."""
        import inspect

        from components import drive_picker_spike

        source = inspect.getsource(drive_picker_spike)
        assert '"transport_verified"' in source
        assert 'result.get("kind")' in source
        assert 'result.get("requestId")' in source

    def test_reset_pops_request_id(self) -> None:
        """Reset clears the request_id so a fresh one is generated."""
        import inspect

        from components import drive_picker_spike

        source = inspect.getsource(drive_picker_spike)
        assert "_phase0_request_id" in source
        assert 'pop("_phase0_request_id"' in source.replace(" ", "")

    def test_success_message_is_minimal(self) -> None:
        """Success message contains only transport-verified language."""
        import inspect

        from components import drive_picker_spike

        source = inspect.getsource(drive_picker_spike)
        assert "Picker transport verified" in source
        assert "no file was downloaded" in source.lower()

    def test_no_selection_metadata_in_source(self) -> None:
        """Source must not reference file ID, filename, MIME, or Picker payload."""
        import inspect

        from components import drive_picker_spike

        source = inspect.getsource(drive_picker_spike)
        # These should not appear as things the module handles
        assert "fileId" not in source
        assert "data.docs" not in source
        assert "mimeType" not in source
