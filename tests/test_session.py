"""Tests for utils/session.py."""

from unittest.mock import patch, MagicMock
from utils.session import clear_data


class TestClearData:
    def test_clears_analysis_state(self):
        """clear_data should reset all analysis-related session state keys."""
        mock_state = MagicMock()
        with patch("utils.session.st.session_state", mock_state):
            clear_data()
        assert mock_state.df is None
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
