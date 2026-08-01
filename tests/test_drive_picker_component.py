"""Tests for components/drive_picker_component.py — wrapper contract.

The wrapper owns schema validation (v0.3.0 spec §3.3): it returns only
an allowlisted ``PickerSelection`` dict or ``None`` — never raw
component values, Picker metadata, tokens, or error text. Request
freshness (``requestId``) is checked by the sidebar, not the wrapper.
"""

from unittest.mock import patch

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
