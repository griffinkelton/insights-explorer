"""Gemini API client wrapper for GA4 Insight Explorer."""

import os
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
