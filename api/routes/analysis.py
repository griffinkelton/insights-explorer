"""Analysis endpoints (spec phase-3-ai-analysis.md Tasks 8–9).

- ``POST /api/v1/analysis/summary`` — Gemini narrative over the deterministic
  context (non-streaming; provider output capped at the reserved allowance).
- ``POST /api/v1/analysis/forecast`` · ``/analysis/funnel`` — server-side
  DETERMINISTIC calls (``forecast_metric`` / ``build_funnel_data``) — no
  Gemini, no AI quota, no ai_lock.

Error policy (C2): non-SSE endpoints raise HTTPException whose ``detail`` is
the approved typed message from ``classify_provider_error`` — never raw
exception text. Failure usage events are emitted BEFORE the exception so the
ledger's ``failure_count`` is meaningful (settled 2026-08-06).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from api.config import get_settings
from api.dependencies import require_dataset
from api.schemas import (
    ForecastPoint,
    ForecastRequest,
    ForecastResponse,
    FunnelRequest,
    FunnelResponse,
    SummaryRequest,
    SummaryResponse,
    UsageSummary,
)
from api.services.ai_service import (
    ContextTooLargeError,
    accumulate_latency,
    build_deterministic_context,
    build_summary_prompt_payload,
    classify_provider_error,
    ledger_sink,
)
from api.stores.dataset_store import datasets
from api.stores.session_store import AppSession, UsageLedger
from utils.data_loader import find_date_column
from utils.forecasting import build_forecast_summary, forecast_metric
from utils.funnels import build_funnel_data
from utils.gemini_client import emit_usage_failure, generate_response

router = APIRouter(prefix="/api/v1", tags=["analysis"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _snapshot_usage(ledger: UsageLedger) -> tuple[int, int, int, int]:
    return (
        ledger.input_tokens,
        ledger.output_tokens,
        ledger.thought_tokens,
        ledger.total_tokens,
    )


def _usage_delta(before: tuple[int, int, int, int], ledger: UsageLedger) -> UsageSummary:
    return UsageSummary(
        input_tokens=ledger.input_tokens - before[0],
        output_tokens=ledger.output_tokens - before[1],
        thoughts_token_count=ledger.thought_tokens - before[2],
        total_token_count=ledger.total_tokens - before[3],
    )


def _status_for(code: str) -> int:
    """Map typed error codes to HTTP status for non-SSE endpoints (C2)."""
    return {
        "rate_limited": status.HTTP_429_TOO_MANY_REQUESTS,
        "quota_exhausted": status.HTTP_429_TOO_MANY_REQUESTS,
        "ai_busy": status.HTTP_429_TOO_MANY_REQUESTS,
        "context_too_large": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "timeout": status.HTTP_504_GATEWAY_TIMEOUT,
        "provider_unavailable": status.HTTP_502_BAD_GATEWAY,
    }.get(code, status.HTTP_502_BAD_GATEWAY)


@router.post("/analysis/summary")
async def analysis_summary(
    payload: SummaryRequest,
    session: AppSession = Depends(require_dataset),
) -> SummaryResponse:
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

    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")

    context = build_deterministic_context(dataset.dataframe, dataset.context, session)
    ledger = session.usage_ledger
    sink = ledger_sink(ledger)
    ledger.request_started_at = _utcnow()
    model = settings.gemini_model

    # Queue-wait ceiling applies to ACQUIRING ai_lock only (C6, settled 2026-08-06);
    # AI_GENERATE_TIMEOUT_SECONDS governs the provider call once the lock is owned.
    lock_held = False
    try:
        try:
            await asyncio.wait_for(
                session.ai_lock.acquire(),
                timeout=settings.ai_queue_wait_seconds,
            )
            lock_held = True
        except asyncio.TimeoutError:
            emit_usage_failure(
                model,
                request_type="summary",
                error_class="AIBusy",
                usage_sink=sink,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Another AI request is in progress. Try again shortly.",
            )

        prompt, trimmed, estimated = build_summary_prompt_payload(
            context=context,
            max_context_tokens=settings.ai_max_context_tokens,
            reserved_output_tokens=settings.ai_reserved_output_tokens,
        )
        ledger.estimated_prompt_tokens = estimated
        if trimmed:
            ledger.context_trimmed += 1
        if context.removed_columns:
            ledger.identifiers_removed += 1
        before = _snapshot_usage(ledger)
        text = await asyncio.wait_for(
            asyncio.to_thread(
                generate_response,
                prompt,
                model=model,
                request_type="summary",
                usage_sink=sink,
                max_output_tokens=settings.ai_reserved_output_tokens,
            ),
            timeout=settings.ai_generate_timeout_seconds,
        )
        return SummaryResponse(
            summary=text,
            model=model,
            usage=_usage_delta(before, ledger),
        )
    except (ValueError, RuntimeError, TimeoutError, ContextTooLargeError) as exc:
        # Failure accounting: emit BEFORE the typed error (C2 + settled note).
        emit_usage_failure(
            model,
            request_type="summary",
            error_class=type(exc).__name__,
            usage_sink=sink,
        )
        err = classify_provider_error(exc)
        raise HTTPException(
            status_code=_status_for(err.code),
            detail=err.message,
        ) from exc
    finally:
        if lock_held:
            session.ai_lock.release()
        ledger.provider_completed_at = _utcnow()
        accumulate_latency(ledger)


def _find_page_col(df: pd.DataFrame) -> str | None:
    """Best-effort page/path column auto-detect (FunnelRequest.page_col=None)."""
    for col in df.columns:
        name = str(col).lower()
        if "page" in name or "path" in name:
            return str(col)
    return None


@router.post("/analysis/forecast")
def analysis_forecast(
    payload: ForecastRequest,
    session: AppSession = Depends(require_dataset),
) -> ForecastResponse:
    """Deterministic projection — no Gemini. Insufficient data → 200 with flag."""
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")
    df = dataset.dataframe

    date_col = payload.date_col or find_date_column(df)
    if date_col is None or date_col not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Could not detect a date column; pass date_col explicitly.",
        )
    if payload.metric_col not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Metric column '{payload.metric_col}' not found in dataset.",
        )

    result = forecast_metric(df, date_col, payload.metric_col, periods=payload.periods)
    if result is None:
        return ForecastResponse(
            metric_col=payload.metric_col,
            periods=payload.periods,
            summary="Insufficient data for forecasting.",
            insufficient_data=True,
        )
    points = [
        ForecastPoint(
            date=str(row.date),
            value=float(row.predicted),
            lower=float(row.lower_bound),
            upper=float(row.upper_bound),
        )
        for row in result.forecast_df.itertuples(index=False)
    ]
    return ForecastResponse(
        metric_col=payload.metric_col,
        periods=payload.periods,
        summary=build_forecast_summary(result),
        forecast_points=points,
    )


@router.post("/analysis/funnel")
def analysis_funnel(
    payload: FunnelRequest,
    session: AppSession = Depends(require_dataset),
) -> FunnelResponse:
    """Deterministic page-path aggregation — no Gemini."""
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")
    df = dataset.dataframe

    page_col = payload.page_col or _find_page_col(df)
    if page_col is None or page_col not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Could not detect a page/path column; pass page_col explicitly.",
        )
    if payload.metric_col not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Metric column '{payload.metric_col}' not found in dataset.",
        )

    result = build_funnel_data(df, page_col, payload.metric_col, payload.steps)
    if result is None:
        return FunnelResponse(steps=payload.steps, values=[])
    return FunnelResponse(steps=result.steps, values=result.counts)
