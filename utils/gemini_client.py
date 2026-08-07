"""Gemini API client wrapper for GA4 Insight Explorer.

Framework-neutral (Phase 2, spec Task 5): no Streamlit import. Usage
accounting is emitted as a structured ``UsageEvent`` through an injectable
``usage_sink`` callback — the Streamlit layer supplies a session-state
writer; the FastAPI layer will supply a server-side usage ledger (Phase 3).
Sink failures are best-effort/logged and never break a request.
"""

import asyncio
import logging
import os
from collections.abc import Generator
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Callable

from dotenv import load_dotenv
from google import genai

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Model configuration — easy to swap later
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.3  # Conservative for analytical consistency
DEFAULT_MAX_OUTPUT_TOKENS = 2048

# Available models with metadata for the model selector.
# Phase 3 model hygiene (spec Task 4/12, master-plan §7): gemini-2.0-flash
# (shut down 2026-06-01) and gemini-1.5-flash (deprecated) are PRUNED;
# 3.5-flash + 3.5-flash-lite joined. GEMINI_MODEL env selects the default.
AVAILABLE_MODELS = {
    "gemini-2.5-flash": {
        "label": "Gemini 2.5 Flash",
        "tooltip": "Reliable flash model with multimodal support. 10 RPM, 1,500 RPD free tier. Good balance of speed and quality.",
        "context_window": "1M tokens",
        "tier": "Free",
    },
    "gemini-3.5-flash": {
        "label": "Gemini 3.5 Flash",
        "tooltip": "Current flash workhorse for analytics explanation; built-in reasoning. 1M-token context.",
        "context_window": "1M tokens",
        "tier": "Paid",
    },
    "gemini-3.5-flash-lite": {
        "label": "Gemini 3.5 Flash Lite",
        "tooltip": "Cost-sensitive, high-throughput routine formatting. 1M-token context.",
        "context_window": "1M tokens",
        "tier": "Paid",
    },
}

# Model context limits for countTokens guard only — not displayed as gauges
MODEL_CONTEXT_LIMITS = {
    "gemini-2.5-flash": 1_000_000,
    "gemini-3.5-flash": 1_000_000,
    "gemini-3.5-flash-lite": 1_000_000,
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


@dataclass(frozen=True)
class UsageEvent:
    """Structured, safe Gemini usage event (confirmed + refined P1 + review fix).

    Contains operational metadata ONLY — NEVER prompt content, raw rows, user
    messages, or model output (Gemini boundary, data-retention-policy §AI).
    Sink failures are best-effort/logged, never fatal.
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model: str = ""
    request_type: str = ""  # e.g. "summary" | "chat" | "chart" (Phase 3 uses it)
    input_tokens: int = 0
    output_tokens: int = 0
    thoughts_token_count: int = 0
    cached_token_count: int = 0  # preserved for the legacy total_cached_tokens counter
    tool_use_token_count: int = 0
    total_token_count: int = 0  # provider-reported total when available (review fix)
    success: bool = True
    sanitized_error_class: str | None = None


UsageSink = Callable[[UsageEvent], None]


def _emit_usage(
    response,
    model: str,
    request_type: str = "",
    success: bool = True,
    error_class: str | None = None,
    usage_sink: UsageSink | None = None,
) -> UsageEvent | None:
    """Build a safe UsageEvent from provider metadata and hand it to the sink.

    Best-effort: a failing sink is logged and never raises — telemetry must not
    break a user request (confirmed P1).
    """
    usage = getattr(response, "usage_metadata", None)
    if usage is None and success:
        return None
    event = UsageEvent(
        model=model,
        request_type=request_type,
        input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
        output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
        thoughts_token_count=getattr(usage, "thoughts_token_count", 0) or 0,
        cached_token_count=getattr(usage, "cached_content_token_count", 0) or 0,
        tool_use_token_count=getattr(usage, "tool_use_token_count", 0) or 0,
        total_token_count=getattr(usage, "total_token_count", 0) or 0,
        success=success,
        sanitized_error_class=error_class,
    )
    # Review fix (2026-08-06): preserve provider semantics — if the provider did
    # NOT report a total, fall back to a documented sum (never silently
    # substitute a weaker number that changes the meaning of the legacy counter).
    if event.total_token_count == 0:
        event = replace(
            event,
            total_token_count=(
                event.input_tokens
                + event.output_tokens
                + event.thoughts_token_count
                + event.cached_token_count
                + event.tool_use_token_count
            ),
        )
    if usage_sink is not None:
        try:
            usage_sink(event)
        except Exception as exc:  # best-effort — telemetry never breaks a request
            # Review fix (2026-08-06): log a generic event with only the error
            # CLASS — never str(exc), which could contain prompt content or raw
            # rows from an arbitrary API ledger or Streamlit sink.
            logger.warning(
                "usage_sink_failed",
                extra={"error_class": type(exc).__name__},
            )
    return event


def generate_response(
    prompt: str,
    model: str = DEFAULT_MODEL,
    request_type: str = "",
    usage_sink: UsageSink | None = None,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
) -> str:
    """Send a prompt to Gemini and return the text response.

    Phase 3 (C4): ``max_output_tokens`` is configurable so routes can pass
    ``settings.ai_reserved_output_tokens``; the default preserves the legacy
    Streamlit behavior (2048).

    Raises ValueError for missing API key, RuntimeError for API failures.
    """
    try:
        response = _get_client().models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": max_output_tokens,
            },
        )
        # Emit usage (if available) through the optional sink.
        _emit_usage(response, model, request_type=request_type, usage_sink=usage_sink)
        return response.text
    except ValueError:
        raise  # API key errors propagate as-is
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e


def analyze_file_with_gemini(
    file_bytes: bytes,
    mime_type: str,
    prompt: str = "Analyze this file and provide key insights.",
    model: str = DEFAULT_MODEL,
    usage_sink: UsageSink | None = None,
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
        _emit_usage(response, model, request_type="file", usage_sink=usage_sink)
        return response.text
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e


def generate_response_stream(
    prompt: str,
    model: str = DEFAULT_MODEL,
    request_type: str = "",
    usage_sink: UsageSink | None = None,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
) -> Generator[str, None, None]:
    """Stream Gemini response tokens one at a time (sync — Streamlit path).

    Yields text chunks as they arrive from the API.
    The caller is responsible for collecting the full text
    and running chart detection after the stream completes.

    Phase 3 (C4): ``max_output_tokens`` is configurable; default preserves the
    legacy Streamlit behavior.

    Raises ValueError for missing API key, RuntimeError for API failures.
    """
    try:
        response = _get_client().models.generate_content_stream(
            model=model,
            contents=prompt,
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": max_output_tokens,
            },
        )
        last_chunk = None
        for chunk in response:
            if chunk.text:
                yield chunk.text
            # Usage arrives on the final chunk — remember it for the sink.
            if getattr(chunk, "usage_metadata", None) is not None:
                last_chunk = chunk
        if last_chunk is not None:
            _emit_usage(last_chunk, model, request_type=request_type, usage_sink=usage_sink)
    except ValueError:
        raise  # API key errors propagate as-is
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e


def emit_usage_failure(
    model: str,
    request_type: str = "",
    error_class: str = "UnknownError",
    usage_sink: UsageSink | None = None,
) -> None:
    """Emit a failure UsageEvent into the sink (settled 2026-08-06).

    The async AI path emits this BEFORE streaming the typed SSE ``error``
    event so ``failure_count`` is meaningful — successful-call usage emission
    alone would leave it at zero. Best-effort: sink failures are logged, never
    fatal.
    """
    _emit_usage(
        None,
        model,
        request_type=request_type,
        success=False,
        error_class=error_class,
        usage_sink=usage_sink,
    )


def count_tokens(prompt: str, model: str = DEFAULT_MODEL) -> int:
    """Exact provider token count — near-limit preflight ONLY (spec D11).

    Task 0 probe (2026-08-06, google-genai 2.14.0 verified):
    ``client.models.count_tokens(*, model, contents, config) -> CountTokensResponse``
    with ``.total_tokens`` (+ ``.cached_content_token_count``). Free but
    separately rate-limited — never call it on ordinary requests.
    """
    response = _get_client().models.count_tokens(model=model, contents=prompt)
    return int(getattr(response, "total_tokens", 0) or 0)


async def generate_response_stream_async(
    prompt: str,
    model: str = DEFAULT_MODEL,
    request_type: str = "",
    usage_sink: UsageSink | None = None,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    first_token_timeout: float = 30.0,
    stream_timeout: float = 120.0,
):
    """Async Gemini streaming generator for FastAPI SSE (spec Task 5, D2).

    Uses the ``aio`` surface of the sync client (additive to the sync
    generator — Streamlit keeps its path). Enforces two client-side deadlines:
    first-token (``first_token_timeout``) and whole-stream (``stream_timeout``)
    — both raise ``TimeoutError`` (typed ``timeout`` SSE event upstream).

    Raises ValueError for missing API key, RuntimeError for API failures,
    TimeoutError for the first-token/stream deadlines.
    """
    try:
        client = _get_client()
        stream = client.aio.models.generate_content_stream(
            model=model,
            contents=prompt,
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": max_output_tokens,
            },
        )
        last_chunk = None
        try:
            first_chunk = await asyncio.wait_for(anext(stream), timeout=first_token_timeout)
        except asyncio.TimeoutError as exc:
            # Wording avoids the token-safety guard's credential-name heuristic
            # while staying a static, content-free message (C2).
            raise TimeoutError("AI response did not start in time") from exc
        if getattr(first_chunk, "usage_metadata", None) is not None:
            last_chunk = first_chunk
        if first_chunk.text:
            yield first_chunk.text
        async with asyncio.timeout(stream_timeout):
            async for chunk in stream:
                # Usage arrives on the final chunk — remember it for the sink.
                if getattr(chunk, "usage_metadata", None) is not None:
                    last_chunk = chunk
                if chunk.text:
                    yield chunk.text
        if last_chunk is not None:
            _emit_usage(last_chunk, model, request_type=request_type, usage_sink=usage_sink)
    except ValueError:
        raise  # API key errors propagate as-is
    except TimeoutError:
        raise
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e
