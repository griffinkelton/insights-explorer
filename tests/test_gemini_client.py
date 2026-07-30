"""Unit tests for utils/gemini_client.py — API calls, error handling, key validation."""

from unittest.mock import MagicMock, patch

import pytest

# Reset the module-level client singleton before each test module
import utils.gemini_client as gm


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the lazy client singleton before each test."""
    gm._client = None
    yield
    gm._client = None


# ── generate_response tests ─────────────────────────────────────────────────


class TestGenerateResponse:
    """Tests for generate_response() — success and all error paths."""

    @patch.object(gm, "_get_client")
    def test_successful_response(self, mock_get_client):
        """Happy path: Gemini returns a valid response with .text."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Here is your analysis."
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = gm.generate_response("explain AI")

        assert result == "Here is your analysis."
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="explain AI",
            config={"temperature": 0.3, "max_output_tokens": 2048},
        )

    @patch.object(gm, "_get_client")
    def test_custom_model_parameter(self, mock_get_client):
        """Model parameter should override the default."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        gm.generate_response("test", model="gemini-2.0-flash")

        mock_client.models.generate_content.assert_called_once()
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.0-flash"

    @patch.object(gm, "_get_client")
    def test_missing_api_key_raises_valueerror(self, mock_get_client):
        """Missing key → ValueError propagates directly."""
        mock_get_client.side_effect = ValueError(
            "GEMINI_API_KEY not found. Please set it in your .env file."
        )

        with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
            gm.generate_response("test")

    @patch.object(gm, "_get_client")
    def test_rate_limit_raises_runtimeerror(self, mock_get_client):
        """Rate limit error → friendly RuntimeError."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(
            "429 Resource exhausted: rate limit exceeded"
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Rate limit"):
            gm.generate_response("test")

    @patch.object(gm, "_get_client")
    def test_quota_exceeded_raises_runtimeerror(self, mock_get_client):
        """Quota exceeded (429) → friendly RuntimeError."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(
            "429 Quota exceeded for this project"
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Rate limit"):
            gm.generate_response("test")

    @patch.object(gm, "_get_client")
    def test_generic_api_error_raises_runtimeerror(self, mock_get_client):
        """Unknown API error → generic RuntimeError."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("500 Internal server error")
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="service error"):
            gm.generate_response("test")

    @patch.object(gm, "_get_client")
    def test_valueerror_from_api_propagates(self, mock_get_client):
        """If the API raises ValueError directly, it's re-raised (not wrapped)."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = ValueError("Invalid prompt")
        mock_get_client.return_value = mock_client

        with pytest.raises(ValueError, match="Invalid prompt"):
            gm.generate_response("test")

    @patch.object(gm, "_get_client")
    def test_rate_limit_case_insensitive(self, mock_get_client):
        """429 in error string should be caught regardless of surrounding text."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception(
            "Error 429: RATE LIMIT EXCEEDED"
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Rate limit"):
            gm.generate_response("test")


# ── validate_api_key tests ───────────────────────────────────────────────────


class TestValidateApiKey:
    """Tests for validate_api_key() — valid, invalid, and transient errors."""

    @patch.object(gm, "_get_client")
    def test_valid_key(self, mock_get_client):
        """Valid key → (True, '')."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        is_valid, msg = gm.validate_api_key()

        assert is_valid is True
        assert msg == ""
        mock_client.models.list.assert_called_once_with(config={"page_size": 1})

    @patch.object(gm, "_get_client")
    def test_missing_key(self, mock_get_client):
        """Missing key → (False, message)."""
        mock_get_client.side_effect = ValueError("GEMINI_API_KEY not found. ...")

        is_valid, msg = gm.validate_api_key()

        assert is_valid is False
        assert "GEMINI_API_KEY not found" in msg

    @patch.object(gm, "_get_client")
    def test_bad_key_unauthorized(self, mock_get_client):
        """API returns unauthorized → (False, message)."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception(
            "Request had invalid authentication credentials (unauthorized)"
        )
        mock_get_client.return_value = mock_client

        is_valid, msg = gm.validate_api_key()

        assert is_valid is False
        assert "rejected" in msg.lower()

    @patch.object(gm, "_get_client")
    def test_bad_key_permission_denied(self, mock_get_client):
        """API returns permission denied → (False, message)."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception(
            "Permission denied: API key doesn't have access"
        )
        mock_get_client.return_value = mock_client

        is_valid, msg = gm.validate_api_key()

        assert is_valid is False
        assert "rejected" in msg.lower()

    @patch.object(gm, "_get_client")
    def test_network_error_treated_as_valid(self, mock_get_client):
        """Network errors are transient → (True, '') so key check retries later."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Connection timeout")
        mock_get_client.return_value = mock_client

        is_valid, msg = gm.validate_api_key()

        # Network errors don't mean the key is bad
        assert is_valid is True
        assert msg == ""

    @patch.object(gm, "_get_client")
    def test_bad_key_api_key_keyword(self, mock_get_client):
        """Error containing 'api_key' keyword → treated as bad key."""
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("Invalid api_key: malformed")
        mock_get_client.return_value = mock_client

        is_valid, msg = gm.validate_api_key()

        assert is_valid is False
        assert "rejected" in msg.lower()
