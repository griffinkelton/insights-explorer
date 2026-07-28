"""Gemini API client wrapper for GA4 Insight Explorer."""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model configuration — easy to swap later
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.3  # Conservative for analytical consistency
DEFAULT_MAX_OUTPUT_TOKENS = 2048

# Configure the client once at module load time
_api_configured = False


def _configure_client() -> None:
    """Configure the Gemini API client with the key from environment."""
    global _api_configured
    if _api_configured:
        return
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. Please set it in your .env file. "
            "Get a free key at https://aistudio.google.com/apikey"
        )
    genai.configure(api_key=api_key)
    _api_configured = True


def generate_response(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to Gemini and return the text response.

    Raises ValueError for missing API key, RuntimeError for API failures.
    """
    _configure_client()

    try:
        generative_model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
        )
        response = generative_model.generate_content(prompt)
        return response.text
    except ValueError:
        raise  # Re-raise API key errors as-is
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
