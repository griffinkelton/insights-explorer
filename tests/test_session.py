"""Tests for utils/session.py."""

from unittest.mock import MagicMock, patch

import pandas as pd

from utils.session import clear_data


class TestClearData:
    def test_clears_analysis_state(self):
        """clear_data should reset all analysis-related session state keys."""
        mock_state = MagicMock()
        with patch("utils.session.st.session_state", mock_state):
            clear_data()
        assert mock_state.data_context is None
        assert mock_state.stats is None
        assert mock_state.summary is None
        assert mock_state.quality_report is None
        assert mock_state.chat_history == []
        assert mock_state.missing_columns == []
        assert mock_state.data_cleared is True
        assert mock_state.data_source is None

    def test_does_not_touch_auth_state(self):
        """clear_data must NOT modify auth/GA4 credentials."""
        mock_state = MagicMock()
        with patch("utils.session.st.session_state", mock_state):
            clear_data()
        # Verify auth keys are NOT reset to None
        assert mock_state.ga4_creds is not None
        assert mock_state.ga4_property_id is not None
        assert mock_state.api_key_valid is not None

    def test_purges_forecast_keys(self):
        """clear_data deletes all forecast_* keys to prevent session state bloat."""
        # Use a dict wrapped in a MagicMock so .keys() returns actual keys
        state_dict = {
            "df": pd.DataFrame({"a": [1]}),
            "stats": {"row_count": 1},
            "forecast_abc123": "stale_cache",
            "forecast_xyz789": "another_cache",
            "chat_history": [{"q": "hello"}],
        }
        mock_state = MagicMock()
        mock_state.__contains__ = lambda self, k: k in state_dict
        mock_state.__getitem__ = lambda self, k: state_dict[k]
        mock_state.__setitem__ = lambda self, k, v: state_dict.__setitem__(k, v)
        mock_state.__delitem__ = lambda self, k: state_dict.__delitem__(k)
        mock_state.keys.side_effect = state_dict.keys
        mock_state.get.side_effect = state_dict.get

        with patch("utils.session.st.session_state", mock_state):
            clear_data()

        # Forecast keys should be deleted from the backing dict
        assert "forecast_abc123" not in state_dict
        assert "forecast_xyz789" not in state_dict
        # Non-forecast analysis keys reset via attribute assignment
        assert mock_state.chat_history == []
        assert mock_state.funnel_steps == []
        assert mock_state.funnel_data is None
