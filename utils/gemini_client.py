"""Gemini API client wrapper for GA4 Insight Explorer."""

import logging
import os
from collections.abc import Generator

from dotenv import load_dotenv
from google import genai

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Model configuration — easy to swap later
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.3  # Conservative for analytical consistency
DEFAULT_MAX_OUTPUT_TOKENS = 2048

# Available models with metadata for the model selector
AVAILABLE_MODELS = {
    "gemini-2.5-flash": {
        "label": "Gemini 2.5 Flash",
        "tooltip": "Reliable flash model with multimodal support. 10 RPM, 1,500 RPD free tier. Good balance of speed and quality.",
        "context_window": "1M tokens",
        "tier": "Free",
    },
    "gemini-2.0-flash": {
        "label": "Gemini 2.0 Flash",
        "tooltip": "Previous-gen flash model. Fast responses, good for simple queries. 10 RPM, 1,500 RPD free tier.",
        "context_window": "1M tokens",
        "tier": "Free",
    },
    "gemini-1.5-flash": {
        "label": "Gemini 1.5 Flash",
        "tooltip": "Legacy flash model. Still capable for most tasks. 15 RPM, 1,500 RPD free tier.",
        "context_window": "1M tokens",
        "tier": "Free",
    },
}

# Model context limits for countTokens guard only — not displayed as gauges
MODEL_CONTEXT_LIMITS = {
    "gemini-2.5-flash": 1_000_000,
    "gemini-2.0-flash": 1_000_000,
    "gemini-1.5-flash": 1_000_000,
}

# Lazy-initialized client
_client: genai.Client | None = None


def validate_api_key() -> tuple[bool, str]:
    """Test whether the configured API key is valid.

    Returns (is_valid, message).
    """
    try:
        client = _get_client()
        # Lightweight call: list models (1 token, no quota impact)
        client.models.list(config={"page_size": 1})
        return True, ""
    except ValueError:
        return False, (
            "GEMINI_API_KEY not found. Set it in your .env file. "
            "Get a free key at https://aistudio.google.com/apikey"
        )
    except Exception as e:
        logger.debug("API key validation error", exc_info=True)
        error_msg = str(e).lower()
        if "api_key" in error_msg or "unauthorized" in error_msg or "permission" in error_msg:
            return False, "API key was rejected. Check your GEMINI_API_KEY in .env."
        # Other errors (network, etc.) don't necessarily mean the key is bad
        return True, ""


def _get_client() -> genai.Client:
    """Return a configured genai.Client, creating it on first call."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. Please set it in your .env file. "
            "Get a free key at https://aistudio.google.com/apikey"
        )
    _client = genai.Client(api_key=api_key)
    return _client


def _classify_api_error(e: Exception) -> str:
    """Classify a Gemini API exception into a user-facing message.

    Pure function — no side effects. Trivially testable.
    Uses HTTP status codes (429, 403, 500) for stable classification
    rather than substring-matching on English error text.
    """
    msg = str(e)
    if "429" in msg:
        return "⏱️ Rate limit exceeded. Please wait a moment and try again."
    if "403" in msg:
        return "🔑 API key invalid or missing permissions."
    if "500" in msg:
        return "⚠️ Gemini service error. Please try again shortly."
    logger.debug("Unclassified Gemini API error: %s", msg)
    return "⚠️ Gemini could not complete that request. Please try again shortly."


def generate_response(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to Gemini and return the text response.

    Raises ValueError for missing API key, RuntimeError for API failures.
    """
    try:
        response = _get_client().models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
        )
        # Track token usage if available
        _track_usage(response)
        return response.text
    except ValueError:
        raise  # API key errors propagate as-is
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e


def _track_usage(response) -> dict | None:
    """Extract provider-reported usage metadata from a Gemini response.

    Returns a dict with per-request token counts, or None if metadata
    is unavailable.  Also accumulates session totals in st.session_state
    when running inside Streamlit.
    """
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return None

    per_request = {
        "prompt_tokens": getattr(usage, "prompt_token_count", 0) or 0,
        "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
        "thought_tokens": getattr(usage, "thoughts_token_count", 0) or 0,
        "cached_tokens": getattr(usage, "cached_content_token_count", 0) or 0,
        "tool_tokens": getattr(usage, "tool_use_token_count", 0) or 0,
        "total_tokens": getattr(usage, "total_token_count", 0) or 0,
    }

    # Accumulate session totals (Streamlit only)
    try:
        import streamlit as st

        for key, field in [
            ("total_input_tokens", "prompt_tokens"),
            ("total_output_tokens", "output_tokens"),
            ("total_thought_tokens", "thought_tokens"),
            ("total_cached_tokens", "cached_tokens"),
            ("total_tokens_used", "total_tokens"),
        ]:
            if key not in st.session_state:
                st.session_state[key] = 0
            st.session_state[key] += per_request[field]

        if "api_success_count" not in st.session_state:
            st.session_state.api_success_count = 0
        st.session_state.api_success_count += 1

        # Attach per-request usage to the last chat history entry.
        # Only set once — chart extraction calls must not overwrite
        # the chat response usage.
        history = st.session_state.get("chat_history", [])
        if history and "usage" not in history[-1]:
            history[-1]["usage"] = per_request
    except ImportError:
        pass

    return per_request


def analyze_file_with_gemini(
    file_bytes: bytes,
    mime_type: str,
    prompt: str = "Analyze this file and provide key insights.",
    model: str = DEFAULT_MODEL,
) -> str:
    """Analyze a file (image, PDF, etc.) directly with Gemini's multimodal capabilities.

    Passes raw bytes inline without needing the Files API upload step.
    Supports: images (JPEG, PNG, GIF, WebP), PDFs, and other document types.

    Args:
        file_bytes: Raw file content as bytes.
        mime_type: MIME type of the file (e.g., 'image/png', 'application/pdf').
        prompt: The analysis prompt to send alongside the file.
        model: Gemini model to use.

    Returns:
        The text analysis from Gemini.

    Raises:
        ValueError: For missing API key.
        RuntimeError: For API failures.
    """
    try:
        response = _get_client().models.generate_content(
            model=model,
            contents=[
                prompt,
                {"data": file_bytes, "mime_type": mime_type},
            ],
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
        )
        _track_usage(response)
        return response.text
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e


def generate_response_stream(
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> Generator[str, None, None]:
    """Stream Gemini response tokens one at a time.

    Yields text chunks as they arrive from the API.
    The caller is responsible for collecting the full text
    and running chart detection after the stream completes.

    Raises ValueError for missing API key, RuntimeError for API failures.
    """
    try:
        response = _get_client().models.generate_content_stream(
            model=model,
            contents=prompt,
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
            # Track usage from final chunk
            usage = getattr(chunk, "usage_metadata", None)
            if usage is not None:
                _track_usage(chunk)
    except ValueError:
        raise  # API key errors propagate as-is
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e
