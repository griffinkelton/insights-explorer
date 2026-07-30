"""Unit tests for utils/ga4_client.py — OAuth flow, credentials, GA4 report pull."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import utils.ga4_client as ga4

# ── credential serialization tests ──────────────────────────────────────────


class TestCredentialsSerialization:
    """Tests for credentials_to_dict() and credentials_from_dict()."""

    def test_round_trip_preserves_all_fields(self):
        """Serialize → deserialize should preserve all credential fields."""
        original = {
            "token": "ya29.abc123",
            "refresh_token": "1/def456",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "123.apps.googleusercontent.com",
            "client_secret": "GOCSPX-secret",
            "scopes": ["https://www.googleapis.com/auth/analytics.readonly"],
        }
        creds = ga4.credentials_from_dict(original)
        result = ga4.credentials_to_dict(creds)

        for key, expected_val in original.items():
            assert result[key] == expected_val, f"Field '{key}' mismatch"

    def test_to_dict_returns_all_expected_keys(self):
        """credentials_to_dict should include the standard OAuth keys."""
        creds = ga4.credentials_from_dict(
            {
                "token": "t",
                "refresh_token": "rt",
                "token_uri": "https://example.com",
                "client_id": "id",
                "client_secret": "secret",
                "scopes": ["scope1"],
            }
        )
        d = ga4.credentials_to_dict(creds)

        expected_keys = {
            "token",
            "refresh_token",
            "token_uri",
            "client_id",
            "client_secret",
            "scopes",
        }
        assert set(d.keys()) == expected_keys

    def test_from_dict_creates_credentials(self):
        """credentials_from_dict should return a Credentials object."""
        creds = ga4.credentials_from_dict(
            {
                "token": "t",
                "refresh_token": "rt",
                "token_uri": "https://example.com",
                "client_id": "id",
                "client_secret": "secret",
                "scopes": ["scope1"],
            }
        )
        from google.oauth2.credentials import Credentials

        assert isinstance(creds, Credentials)
        assert creds.token == "t"
        assert creds.refresh_token == "rt"


# ── OAuth flow tests ────────────────────────────────────────────────────────


class TestOAuthFlow:
    """Tests for get_auth_url() and exchange_code()."""

    @patch("utils.ga4_client.save_oauth_state")
    @patch("utils.ga4_client.Flow")
    @patch.object(Path, "exists", return_value=True)
    def test_get_auth_url_returns_url_and_flow(self, mock_exists, mock_flow_class, mock_save):
        """get_auth_url should return (url, flow) tuple and persist state."""
        mock_flow = MagicMock()
        mock_flow.code_verifier = "verifier-123"
        mock_flow.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?...",
            "state-abc",
        )
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        url, flow = ga4.get_auth_url("http://localhost:8501")

        assert url == "https://accounts.google.com/o/oauth2/auth?..."
        assert flow is mock_flow
        mock_save.assert_called_once_with("state-abc", "verifier-123", "http://localhost:8501")

    @patch("utils.ga4_client.save_oauth_state")
    @patch("utils.ga4_client.Flow")
    @patch.object(Path, "exists", return_value=True)
    def test_get_auth_url_uses_offline_access(self, mock_exists, mock_flow_class, mock_save):
        """OAuth flow should request offline access for refresh tokens."""
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("http://auth", "state")
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        ga4.get_auth_url("http://localhost:8501")

        mock_flow.authorization_url.assert_called_once_with(
            access_type="offline",
            prompt="consent",
        )

    @patch("utils.ga4_client.save_oauth_state")
    @patch("utils.ga4_client.Flow")
    @patch.object(Path, "exists", return_value=True)
    def test_get_auth_url_passes_redirect_uri(self, mock_exists, mock_flow_class, mock_save):
        """Redirect URI should be passed through to the Flow constructor."""
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("http://auth", "state")
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        ga4.get_auth_url("http://localhost:8501")

        _, call_kwargs = mock_flow_class.from_client_secrets_file.call_args
        assert call_kwargs["redirect_uri"] == "http://localhost:8501"

    @patch.object(Path, "exists", return_value=False)
    def test_get_auth_url_missing_secrets_file(self, mock_exists):
        """Missing client_secrets.json → FileNotFoundError with instructions."""
        with pytest.raises(FileNotFoundError, match="Google OAuth client secrets"):
            ga4.get_auth_url("http://localhost:8501")

    def test_exchange_code_returns_credentials(self):
        """exchange_code should recreate the flow, fetch token, and return credentials."""
        mock_flow = MagicMock()
        mock_flow.credentials = MagicMock()
        mock_flow.credentials.token = "new-token"

        with patch(
            "utils.ga4_client.load_oauth_state", return_value={"code_verifier": "verifier-123"}
        ), patch("utils.ga4_client.Flow") as mock_flow_class:
            mock_flow_class.from_client_secrets_file.return_value = mock_flow

            creds = ga4.exchange_code("auth-code-xyz", "http://localhost:8501", "state-abc")

            mock_flow_class.from_client_secrets_file.assert_called_once()
            _, call_kwargs = mock_flow_class.from_client_secrets_file.call_args
            assert call_kwargs["code_verifier"] == "verifier-123"
            mock_flow.fetch_token.assert_called_once_with(code="auth-code-xyz")
            assert creds is mock_flow.credentials

    def test_exchange_code_requires_state(self):
        """exchange_code should raise if the OAuth state is missing."""
        with pytest.raises(ValueError, match="state"):
            ga4.exchange_code("auth-code-xyz", "http://localhost:8501", "")

    def test_exchange_code_missing_state_raises(self):
        """exchange_code should raise if the OAuth state cannot be found."""
        with patch("utils.ga4_client.load_oauth_state", return_value=None), pytest.raises(
            ValueError, match="state not found"
        ):
            ga4.exchange_code("auth-code-xyz", "http://localhost:8501", "state-abc")

    def test_exchange_code_redirect_uri_mismatch_raises(self):
        """exchange_code should raise if stored redirect_uri doesn't match."""
        with patch(
            "utils.ga4_client.load_oauth_state",
            return_value={
                "code_verifier": "verifier-123",
                "redirect_uri": "http://localhost:8501",
                "created_at": 9999999999,
            },
        ), pytest.raises(ValueError, match="configuration changed"):
            ga4.exchange_code("auth-code-xyz", "http://evil.example.com", "state-abc")


class TestOAuthStateStore:
    """Tests for save_oauth_state / load_oauth_state persistence."""

    def test_round_trip_persists_code_verifier(self, tmp_path, monkeypatch):
        """save then load should return the stored verifier and redirect URI."""
        monkeypatch.setattr(ga4, "_state_store_dir", lambda: tmp_path)

        ga4.save_oauth_state("state-123", "verifier-456", "http://localhost:8501")
        data = ga4.load_oauth_state("state-123")

        assert data["code_verifier"] == "verifier-456"
        assert data["redirect_uri"] == "http://localhost:8501"
        assert "created_at" in data

    def test_load_removes_file(self, tmp_path, monkeypatch):
        """load_oauth_state should remove the state file after reading."""
        monkeypatch.setattr(ga4, "_state_store_dir", lambda: tmp_path)

        ga4.save_oauth_state("state-789", "verifier", "http://localhost:8501")
        ga4.load_oauth_state("state-789")

        assert not (tmp_path / "state-789.json").exists()

    def test_load_missing_state_returns_none(self, tmp_path, monkeypatch):
        """load_oauth_state should return None for an unknown state."""
        monkeypatch.setattr(ga4, "_state_store_dir", lambda: tmp_path)

        assert ga4.load_oauth_state("unknown-state") is None

    def test_malformed_state_json_returns_none(self, tmp_path, monkeypatch):
        """load_oauth_state should return None for malformed JSON."""
        monkeypatch.setattr(ga4, "_state_store_dir", lambda: tmp_path)
        (tmp_path / "bad-state.json").write_text("not valid json {{{{{")

        assert ga4.load_oauth_state("bad-state") is None

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission test")
    def test_save_oauth_state_preserves_state_dir_permissions(self, tmp_path, monkeypatch):
        """save_oauth_state should preserve restrictive directory permissions (0o700)."""
        import stat

        store = tmp_path / "custom_state"
        # Ensure directory exists before patching (prune iterates it)
        store.mkdir(parents=True, exist_ok=True, mode=0o700)
        monkeypatch.setattr(ga4, "_state_store_dir", lambda: store)

        ga4.save_oauth_state("perm-state", "verifier", "http://localhost:8501")

        mode = store.stat().st_mode
        assert stat.S_IMODE(mode) == 0o700, f"Expected 0o700, got {oct(stat.S_IMODE(mode))}"

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-only permission test")
    def test_state_file_permissions(self, tmp_path, monkeypatch):
        """Saved state file should have 0o600 permissions on POSIX."""
        import stat

        monkeypatch.setattr(ga4, "_state_store_dir", lambda: tmp_path)
        ga4.save_oauth_state("file-perm", "verifier", "http://localhost:8501")

        file_path = tmp_path / "file-perm.json"
        mode = file_path.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600, f"Expected 0o600, got {oct(stat.S_IMODE(mode))}"


# ── pull_ga4_report tests ───────────────────────────────────────────────────


class TestPullGa4Report:
    """Tests for pull_ga4_report() — success, empty, token refresh, date range."""

    @staticmethod
    def _make_mock_response(dimension_values, metric_values):
        """Helper: build a mock GA4 API response with one row."""
        mock_row = MagicMock()
        mock_row.dimension_values = [MagicMock(value=dv) for dv in dimension_values]
        mock_row.metric_values = [MagicMock(value=mv) for mv in metric_values]
        mock_response = MagicMock()
        mock_response.rows = [mock_row]
        mock_response.row_count = 1  # Single page of results
        return mock_response

    @staticmethod
    def _make_empty_response():
        """Helper: build a mock GA4 API response with no rows."""
        mock_response = MagicMock()
        mock_response.rows = []
        mock_response.row_count = 0
        return mock_response

    def _mock_run_report_single_page(self, mock_client, dim_vals, metric_vals):
        """Set up run_report to return one page then stop (empty second page)."""
        mock_client.run_report.side_effect = [
            self._make_mock_response(dim_vals, metric_vals),
            self._make_empty_response(),
        ]

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_successful_report_returns_dataframe(self, mock_client_class):
        """pull_ga4_report should return a DataFrame with correct columns."""
        mock_client = MagicMock()
        self._mock_run_report_single_page(
            mock_client,
            dim_vals=["2024-01-01", "/home", "desktop"],
            metric_vals=["100", "50", "45", "0.65", "0.42"],
        )
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        df, _metadata = ga4.pull_ga4_report(mock_creds, "123456789")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["date"] == pd.Timestamp("2024-01-01")
        assert df.iloc[0]["page_path"] == "/home"
        assert df.iloc[0]["device_category"] == "desktop"
        assert df.iloc[0]["sessions"] == 100
        assert df.iloc[0]["users"] == 50
        assert df.iloc[0]["active_users"] == 45
        assert df.iloc[0]["engagement_rate"] == 0.65
        assert df.iloc[0]["bounce_rate"] == 0.42

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_empty_response_returns_empty_dataframe(self, mock_client_class):
        """No rows from GA4 → empty DataFrame (not None or crash)."""
        mock_client = MagicMock()
        mock_client.run_report.return_value = self._make_empty_response()
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        df, _metadata = ga4.pull_ga4_report(mock_creds, "123456789")

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    @patch("utils.ga4_client.Request")
    def test_refreshes_expired_token(self, mock_request_class, mock_client_class):
        """Expired credentials with refresh_token should be refreshed."""
        mock_client = MagicMock()
        self._mock_run_report_single_page(
            mock_client,
            dim_vals=["2024-01-01", "/home", "mobile"],
            metric_vals=["10", "5", "4", "0.5", "0.3"],
        )
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh-me"

        df, _metadata = ga4.pull_ga4_report(mock_creds, "123456789")

        mock_creds.refresh.assert_called_once()
        assert len(df) == 1

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_uses_default_date_range(self, mock_client_class):
        """Default start_date should be '90daysAgo' and end_date 'today'."""
        mock_client = MagicMock()
        mock_client.run_report.return_value = self._make_empty_response()
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        _, _meta = ga4.pull_ga4_report(mock_creds, "123456789")

        call_args = mock_client.run_report.call_args[0][0]
        assert call_args.date_ranges[0].start_date == "90daysAgo"
        assert call_args.date_ranges[0].end_date == "today"

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_custom_date_range(self, mock_client_class):
        """Custom start_date and end_date should be passed through."""
        mock_client = MagicMock()
        mock_client.run_report.return_value = self._make_empty_response()
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        _, _meta = ga4.pull_ga4_report(
            mock_creds, "123456789", start_date="7daysAgo", end_date="yesterday"
        )

        call_args = mock_client.run_report.call_args[0][0]
        assert call_args.date_ranges[0].start_date == "7daysAgo"
        assert call_args.date_ranges[0].end_date == "yesterday"

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_property_id_in_request(self, mock_client_class):
        """Property ID should appear in the RunReportRequest."""
        mock_client = MagicMock()
        mock_client.run_report.return_value = self._make_empty_response()
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        _, _meta = ga4.pull_ga4_report(mock_creds, "987654321")

        call_args = mock_client.run_report.call_args[0][0]
        assert call_args.property == "properties/987654321"

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_returns_correct_columns(self, mock_client_class):
        """Returned DataFrame should have all 8 expected columns."""
        mock_client = MagicMock()
        self._mock_run_report_single_page(
            mock_client,
            dim_vals=["2024-03-15", "/pricing", "tablet"],
            metric_vals=["200", "120", "100", "0.55", "0.38"],
        )
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        df, _metadata = ga4.pull_ga4_report(mock_creds, "123456789")

        expected = {
            "date",
            "page_path",
            "device_category",
            "sessions",
            "users",
            "active_users",
            "engagement_rate",
            "bounce_rate",
        }
        assert set(df.columns) == expected

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_date_column_is_datetime(self, mock_client_class):
        """The date column should be converted to datetime64."""
        mock_client = MagicMock()
        self._mock_run_report_single_page(
            mock_client,
            dim_vals=["2024-06-01", "/blog", "desktop"],
            metric_vals=["300", "180", "160", "0.72", "0.29"],
        )
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        df, _metadata = ga4.pull_ga4_report(mock_creds, "123456789")

        assert pd.api.types.is_datetime64_any_dtype(df["date"])

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_expired_without_refresh_token_skips_refresh(self, mock_client_class):
        """Expired=True with no refresh_token → refresh skipped, API call proceeds."""
        mock_client = MagicMock()
        mock_client.run_report.return_value = self._make_empty_response()
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = None

        _, _meta = ga4.pull_ga4_report(mock_creds, "123456789")

        mock_creds.refresh.assert_not_called()

    @patch("utils.ga4_client.BetaAnalyticsDataClient")
    def test_multiple_rows_preserved(self, mock_client_class):
        """Multiple response rows → all preserved in DataFrame."""
        mock_row1 = MagicMock()
        mock_row1.dimension_values = [
            MagicMock(value="2024-01-01"),
            MagicMock(value="/a"),
            MagicMock(value="desktop"),
        ]
        mock_row1.metric_values = [
            MagicMock(value="10"),
            MagicMock(value="5"),
            MagicMock(value="4"),
            MagicMock(value="0.5"),
            MagicMock(value="0.3"),
        ]
        mock_row2 = MagicMock()
        mock_row2.dimension_values = [
            MagicMock(value="2024-01-02"),
            MagicMock(value="/b"),
            MagicMock(value="mobile"),
        ]
        mock_row2.metric_values = [
            MagicMock(value="20"),
            MagicMock(value="12"),
            MagicMock(value="10"),
            MagicMock(value="0.6"),
            MagicMock(value="0.4"),
        ]

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.rows = [mock_row1, mock_row2]
        mock_response.row_count = 2
        # Second page returns empty
        mock_client.run_report.side_effect = [mock_response, self._make_empty_response()]
        mock_client_class.return_value = mock_client

        mock_creds = MagicMock()
        mock_creds.expired = False

        df, _metadata = ga4.pull_ga4_report(mock_creds, "123456789")

        assert len(df) == 2
        assert df.iloc[0]["page_path"] == "/a"
        assert df.iloc[1]["page_path"] == "/b"
