"""Gemini API client wrapper for GA4 Insight Explorer."""

import os
from collections.abc import Generator
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model configuration — easy to swap later
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.3  # Conservative for analytical consistency
DEFAULT_MAX_OUTPUT_TOKENS = 2048

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
        error_msg = str(e).lower()
        if "api_key" in error_msg or "unauthorized" in error_msg or "permission" in error_msg:
            return False, f"API key rejected: {e}"
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
        return response.text
    except ValueError:
        raise  # API key errors propagate as-is
    except Exception as e:
        error_msg = str(e).lower()
        if "rate" in error_msg and "limit" in error_msg:
            raise RuntimeError(
                "Rate limit hit. Please wait a moment and try again."
            ) from e
        elif "quota" in error_msg:
            raise RuntimeError(
                "API quota exceeded. Check your Google Cloud quota or try again later."
            ) from e
        else:
            raise RuntimeError(
                f"Gemini API error: {str(e)}"
            ) from e


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
    except ValueError:
        raise  # API key errors propagate as-is
    except Exception as e:
        error_msg = str(e).lower()
        if "rate" in error_msg and "limit" in error_msg:
            raise RuntimeError(
                "Rate limit hit. Please wait a moment and try again."
            ) from e
        elif "quota" in error_msg:
            raise RuntimeError(
                "API quota exceeded. Check your Google Cloud quota or try again later."
            ) from e
        else:
            raise RuntimeError(
                f"Gemini API error: {str(e)}"
            ) from e
