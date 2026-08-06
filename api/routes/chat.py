"""POST /api/v1/chat — SSE streaming chat (spec phase-3-ai-analysis.md Task 6).

Wire format: named SSE events with JSON payloads (``event: text/usage/done/error``
+ optional ``event: warning``), never raw text + ``[DONE]`` (D3). Terminal
behavior (C5): success ``text* → done`` · failure ``error → done`` — ``error``
is terminal for assistant content. Concurrency (C6, settled Option A): AI
requests are serialized per session via ``AppSession.ai_lock`` with a bounded
queue-wait (``AI_QUEUE_WAIT_SECONDS``); on expiry the queued request returns a
typed ``retryable`` ``ai_busy`` SSE error. Failure accounting (settled 2026-08-06):
a ``UsageEvent(success=False)`` is emitted through the sink BEFORE the typed
``error`` event so ``failure_count`` is meaningful.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from api.config import get_settings
from api.dependencies import require_dataset
from api.schemas import ChatRequest
from api.services.ai_service import (
    ContextTooLargeError,
    TypedAiError,
    accumulate_latency,
    build_chat_prompt_payload,
    build_deterministic_context,
    classify_provider_error,
    ledger_sink,
    validate_chat_messages,
)
from api.stores.dataset_store import datasets
from api.stores.session_store import AppSession
from utils.gemini_client import emit_usage_failure, generate_response_stream_async

router = APIRouter(prefix="/api/v1", tags=["ai"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    session: AppSession = Depends(require_dataset),
) -> StreamingResponse:
    settings = get_settings()
    if not settings.has_ai:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI features unavailable — configure GEMINI_API_KEY",
        )
    if settings.gemini_data_policy == "disabled":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI features are disabled.",
        )

    # Layer 1 — request validation (D12): 20 msgs / 4k chars / 24k total / roles.
    try:
        validate_chat_messages(payload.messages)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")

    context = build_deterministic_context(dataset.dataframe, dataset.context, session)
    ledger = session.usage_ledger
    sink = ledger_sink(ledger)
    ledger.request_started_at = _utcnow()
    model = settings.gemini_model

    async def event_stream():
        lock_held = False
        try:
            try:
                # Queue-wait ceiling applies to ACQUIRING ai_lock only — first-token
                # and stream deadlines govern the request once it owns the lock
                # (implementation note, 2026-08-06).
                await asyncio.wait_for(
                    session.ai_lock.acquire(),
                    timeout=settings.ai_queue_wait_seconds,
                )
                lock_held = True
            except asyncio.TimeoutError:
                emit_usage_failure(
                    model,
                    request_type=payload.mode,
                    error_class="AIBusy",
                    usage_sink=sink,
                )
                err = TypedAiError(
                    code="ai_busy",
                    message="Another AI request is in progress. Try again shortly.",
                    retryable=True,
                    retry_after_seconds=settings.ai_queue_wait_seconds,
                )
                yield "event: error\n"
                yield f"data: {json.dumps(err.public_payload())}\n\n"
                return

            try:
                prompt, trimmed, estimated = build_chat_prompt_payload(
                    user_question=payload.messages[-1].content,
                    history=[{"role": m.role, "content": m.content} for m in payload.messages[:-1]],
                    context=context,
                    max_context_tokens=settings.ai_max_context_tokens,
                    reserved_output_tokens=settings.ai_reserved_output_tokens,
                    max_context_chars=settings.ai_max_context_chars,
                    model=model,
                )
                ledger.estimated_prompt_tokens = estimated
                if trimmed:
                    ledger.context_trimmed += 1
                if context.removed_columns:
                    ledger.identifiers_removed += 1
                    yield "event: warning\n"
                    yield (
                        "data: "
                        + json.dumps(
                            {
                                "type": "warning",
                                "code": "identifiers_removed_for_ai",
                                "message": "Potential identifier columns were removed before AI analysis.",
                                "removed_columns": context.removed_columns,
                            }
                        )
                        + "\n\n"
                    )
                async for chunk in generate_response_stream_async(
                    prompt,
                    model=model,
                    request_type=payload.mode,
                    usage_sink=sink,
                    max_output_tokens=settings.ai_reserved_output_tokens,
                    first_token_timeout=settings.ai_first_token_timeout_seconds,
                    stream_timeout=settings.ai_stream_timeout_seconds,
                ):
                    if ledger.provider_first_token_at is None:
                        ledger.provider_first_token_at = _utcnow()
                    yield "event: text\n"
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
            except (ValueError, RuntimeError, TimeoutError, ContextTooLargeError) as exc:
                # Failure accounting: emit BEFORE the typed error event (C2).
                emit_usage_failure(
                    model,
                    request_type=payload.mode,
                    error_class=type(exc).__name__,
                    usage_sink=sink,
                )
                err = classify_provider_error(exc)
                yield "event: error\n"
                yield f"data: {json.dumps(err.public_payload())}\n\n"
        finally:
            if lock_held:
                session.ai_lock.release()
            ledger.provider_completed_at = _utcnow()
            accumulate_latency(ledger)
            # `done` closes the transport; `error` is terminal for content (C5).
            # Guard the terminal yield: on client disconnect Starlette cancels
            # this task, and an async generator that yields during CancelledError/
            # GeneratorExit teardown raises RuntimeError — skip `done` instead.
            if not asyncio.current_task().cancelling():
                yield "event: done\n"
                yield 'data: {"type": "done"}\n\n'

    return StreamingResponse(event_stream(), media_type="text/event-stream")
