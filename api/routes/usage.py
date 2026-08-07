"""GET /api/v1/ai/usage — per-session AI usage ledger view (spec Task 11).

Reads the ``AppSession.usage_ledger`` (counts only, D13). Latency aggregates
(``avg_ttft_ms`` / ``avg_ttlt_ms``) are computed from the ledger's safe
cumulative sums — observability only, no per-request retention. Clear Data
resets the ledger with the rest of the dataset-derived state.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_or_create_session
from api.schemas import UsageResponse
from api.stores.session_store import AppSession

router = APIRouter(prefix="/api/v1", tags=["ai"])


@router.get("/ai/usage")
def ai_usage(session: AppSession = Depends(get_or_create_session)) -> UsageResponse:
    ledger = session.usage_ledger
    count = ledger.request_count
    return UsageResponse(
        request_count=count,
        success_count=ledger.success_count,
        failure_count=ledger.failure_count,
        input_tokens=ledger.input_tokens,
        output_tokens=ledger.output_tokens,
        total_tokens=ledger.total_tokens,
        thought_tokens=ledger.thought_tokens,
        cached_tokens=ledger.cached_tokens,
        tool_tokens=ledger.tool_tokens,
        estimated_prompt_tokens=ledger.estimated_prompt_tokens,
        context_trimmed=ledger.context_trimmed,
        identifiers_removed=ledger.identifiers_removed,
        avg_ttft_ms=int(ledger.ttft_cum_ms / count) if count else None,
        avg_ttlt_ms=int(ledger.ttlt_cum_ms / count) if count else None,
        by_request_type=ledger.by_request_type,
        by_model=ledger.by_model,
    )
