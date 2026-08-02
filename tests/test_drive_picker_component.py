"""Tests for components/drive_picker_component.py — wrapper contract.

The wrapper owns schema validation (v0.3.0 spec §3.3): it returns only
an allowlisted ``PickerSelection`` dict or ``None`` — never raw
component values, Picker metadata, tokens, or error text. Request
freshness (``requestId``) is checked by the sidebar, not the wrapper.
"""

from unittest.mock import patch

import pytest
from streamlit.components.lib.local_component_registry import LocalComponentRegistry
from streamlit.components.v1 import declare_component as st_declare_component
from streamlit.errors import StreamlitAPIException

from components.drive_picker_component import PickerSelection, drive_picker_transport


def _call_component(raw_value: object) -> PickerSelection | None:
    """Invoke the wrapper with a stubbed frontend return value."""
    with patch(
        "components.drive_picker_component._component", return_value=raw_value
    ) as mock_component:
        result = drive_picker_transport(
            oauth_token="test-token",
            developer_key="test-key",
            app_id="123456789012",
            app_origin="http://localhost:8501",
            request_id="req-1",
            key="test_picker",
        )
        mock_component.assert_called_once()
    return result


class TestWrapperReturnsOnlyAllowlistedShapes:
    """Malformed values are ignored — the wrapper never forwards them."""

    def test_none_is_ignored(self):
        assert _call_component(None) is None

    def test_string_is_ignored(self):
        assert _call_component("picked") is None

    def test_list_is_ignored(self):
        assert _call_component([{"kind": "picked"}]) is None

    def test_malformed_dict_is_ignored(self):
        assert _call_component({"kind": "picked"}) is None  # missing fileId

    def test_wrong_kind_is_ignored(self):
        assert _call_component({"kind": "cancel", "requestId": "req-1", "fileId": "f1"}) is None

    def test_picked_without_file_id_is_ignored(self):
        assert _call_component({"kind": "picked", "requestId": "req-1"}) is None

    def test_picked_with_empty_file_id_is_ignored(self):
        assert _call_component({"kind": "picked", "requestId": "req-1", "fileId": ""}) is None

    def test_non_string_file_id_is_ignored(self):
        assert _call_component({"kind": "picked", "requestId": "req-1", "fileId": 123}) is None


class TestWrapperReturnsStrictPickerSelection:
    """A valid Picker payload becomes the exact allowlisted shape."""

    def test_valid_selection_returned_as_is(self):
        result = _call_component({"kind": "picked", "requestId": "req-1", "fileId": "FILE123"})
        assert result == {"kind": "picked", "requestId": "req-1", "fileId": "FILE123"}

    def test_extra_picker_metadata_is_stripped(self):
        """Picker name/mimeType/url never survive the wrapper boundary."""
        result = _call_component(
            {
                "kind": "picked",
                "requestId": "req-1",
                "fileId": "FILE123",
                "name": "secret-report.csv",
                "mimeType": "text/csv",
                "url": "https://drive.google.com/...",
            }
        )
        assert result == {"kind": "picked", "requestId": "req-1", "fileId": "FILE123"}


class TestMissingBuildDirectoryFailsLoudly:
    """A missing frontend ``build/`` dir is a hard error, not a UI fallback.

    Verified via fresh-checkout simulation (2026-08-02): with ``build/``
    missing, registering the declared component raises
    ``StreamlitAPIException: No such component directory`` at registration
    time and the **entire page run fails** (error banner; nothing after the
    component renders) — not just the component iframe. This is fail-fast by
    design (v0.3.0 spec §3.1 Build/ policy): a deploy that skips the
    frontend build step is caught immediately.

    ``declare_component`` only registers when a ``ScriptRunContext`` exists
    (i.e. inside a real Streamlit session); bare-mode imports succeed even
    with ``build/`` missing. These tests therefore exercise the exact
    registration path that runs in a live session, using a temp directory,
    so they are deterministic and CI-safe (they never require ``build/`` to
    exist, which the Python test job runs without).
    """

    def test_registration_raises_when_component_dir_is_missing(self, tmp_path):
        missing = tmp_path / "drive_picker_component_frontend" / "build"
        component = st_declare_component("missing_build_regression", path=str(missing))

        with pytest.raises(StreamlitAPIException, match="No such component directory"):
            LocalComponentRegistry().register_component(component)

    def test_registration_succeeds_when_component_dir_exists(self, tmp_path):
        """Control: an existing dir registers normally — the raise is specific to a missing path."""
        present = tmp_path / "build"
        present.mkdir()
        component = st_declare_component("present_build_control", path=str(present))

        registry = LocalComponentRegistry()
        registry.register_component(component)  # must not raise
        assert registry.get_component_path(component.name) == str(present)

    def test_missing_directory_raise_mentions_the_abs_path(self, tmp_path):
        missing = tmp_path / "frontend" / "build"
        component = st_declare_component("missing_path_message", path=str(missing))

        with pytest.raises(StreamlitAPIException) as excinfo:
            LocalComponentRegistry().register_component(component)
        assert str(missing) in str(excinfo.value)
