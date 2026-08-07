"""Phase 5 GA4 service (spec phase-5-ga4-drive.md Task 1 + Task 3).

Two responsibilities:

1. **Server-owned OAuth (Task 1)** — PKCE S256 authorization URL construction,
   code exchange with the stored verifier, server-side token encryption at rest
   (Fernet key derived from ``API_SESSION_SECRET``), token refresh, and the
   typed ``Ga4ServiceError`` taxonomy.
2. **First-pull report (Task 3)** — the locked report shape (five canonical
   measurement-contract metrics × ``date``, trailing 90 complete days, daily
   grain), a generic offset pagination loop (proven via mocked contract tests,
   not high-cardinality dimensions), safe provenance, and quota recorded **only
   from successful responses**.

Privacy boundary: nothing here logs tokens, request headers, raw provider
errors, or raw report rows — only property ID, allowlist names, page/row
counts, and the quota snapshot.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from cryptography.fernet import Fernet, InvalidToken
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    OrderBy,
    RunReportRequest,
)
from google.api_core.exceptions import (
    DeadlineExceeded,
    InternalServerError,
    NotFound,
    PermissionDenied,
    ResourceExhausted,
    ServiceUnavailable,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from api.config import get_settings

# ── Locked report shape (D3 fallback; Task 0 decision rules) ───────────────
CANONICAL_GA4_METRICS = (
    "sessions",
    "totalUsers",
    "engagedSessions",
    "engagementRate",
    "bounceRate",
)
GA4_PAGE_SIZE = 10_000  # default limit; API supports up to 250,000/request
GA4_START_DATE = "90daysAgo"
GA4_END_DATE = "yesterday"

# D2 — two separate consents. GA4 requests analytics.readonly (+ OIDC profile
# for identity resolution); Drive is a separate drive.file flow (Task 2/4).
GA4_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/analytics.readonly",
]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Measurement-contract provenance (plans/ga4-measurement-contract.md).
# Rows 1-2 map to aggregate metrics we pull (provisional until named sign-off);
# rows 3-5 stay `unavailable` — blocked on event-level access (aggregate-only
# reality). Unavailable rows are never numeric evidence.
CONTRACT_ROWS: dict[str, int] = {
    "sessions": 1,
    "totalUsers": 1,
    "engagedSessions": 1,
    "engagementRate": 2,
    "bounceRate": 2,
}
UNAVAILABLE_CONTRACT_ROWS: tuple[dict[str, str], ...] = (
    {
        "id": "questionnaire_start_count",
        "name": "questionnaire_start_count",
        "contract_row": "3",
        "validation_status": "unavailable",
        "reason": "requires event-level access",
    },
    {
        "id": "questionnaire_completion_rate",
        "name": "questionnaire_completion_rate",
        "contract_row": "4",
        "validation_status": "unavailable",
        "reason": "requires event-level access + funnel sign-off",
    },
    {
        "id": "post_questionnaire_action_rate",
        "name": "post_questionnaire_action_rate",
        "contract_row": "5",
        "validation_status": "unavailable",
        "reason": "requires action-taxonomy sign-off + event-level access",
    },
)

OAUTH_CLIENT_TYPE = "web"
OAUTH_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
OAUTH_TOKEN_URI = "https://oauth2.googleapis.com/token"


# ── Typed error taxonomy (Task 3 — locked; one HTTP status per row) ────────
@dataclass(frozen=True)
class Ga4ServiceError(Exception):
    code: str
    message: str
    status_code: int
    retryable: bool = False

    def __init__(
        self, *, code: str, message: str, status_code: int, retryable: bool = False
    ) -> None:
        super().__init__(message)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "status_code", status_code)
        object.__setattr__(self, "retryable", retryable)

    def public_payload(self) -> dict:
        return {"code": self.code, "message": self.message, "retryable": self.retryable}


def _client_config() -> dict:
    settings = get_settings()
    return {
        OAUTH_CLIENT_TYPE: {
            "client_id": settings.ga4_client_id,
            "client_secret": settings.ga4_client_secret,
            "auth_uri": OAUTH_AUTH_URI,
            "token_uri": OAUTH_TOKEN_URI,
        }
    }


# ── Token encryption at rest (server-side only; browser never sees these) ──
def _fernet() -> Fernet:
    key = hashlib.sha256(get_settings().api_session_secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_tokens(payload: dict) -> str:
    """Encrypt a credentials dict for session storage (Task 1: encrypted at rest)."""
    return _fernet().encrypt(json.dumps(payload).encode("utf-8")).decode("ascii")


def decrypt_tokens(blob: str) -> dict:
    """Decrypt stored credentials; a corrupt/invalid blob means reconnect."""
    try:
        return json.loads(_fernet().decrypt(blob.encode("ascii")))
    except (InvalidToken, ValueError) as exc:
        raise Ga4ServiceError(
            code="ga4_reconnect_required",
            message="Stored Google credentials are invalid or expired. Reconnect.",
            status_code=401,
        ) from exc


# ── OAuth flow (PKCE S256 — never plain; Task 1 rules) ─────────────────────
def build_authorization_url(*, scopes: list[str], redirect_uri: str) -> tuple[str, str, str]:
    """Build the Google authorization URL.

    Returns ``(authorization_url, state, code_verifier)``. The verifier is
    generated by the flow (``autogenerate_code_verifier`` is the library
    default) and must be stored server-side until the callback.
    """
    flow = Flow.from_client_config(_client_config(), scopes=scopes, redirect_uri=redirect_uri)
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    return auth_url, state, flow.code_verifier


def exchange_code(*, code: str, redirect_uri: str, code_verifier: str, scopes: list[str]) -> dict:
    """Exchange the authorization code server-side with the stored verifier.

    Raises the underlying provider error; the route maps it to the locked
    ``token_exchange_failed`` callback vocabulary.
    """
    flow = Flow.from_client_config(
        _client_config(),
        scopes=scopes,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
    )
    flow.fetch_token(code=code)
    return credentials_to_dict(flow.credentials)


def credentials_to_dict(creds: Credentials) -> dict[str, Any]:
    """Serialize Google credentials to a JSON-safe dict (server-side only)."""
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


def credentials_from_dict(creds_dict: dict[str, Any]) -> Credentials:
    """Deserialize stored credentials (expiry round-trips via isoformat)."""
    payload = dict(creds_dict)
    expiry = payload.pop("expiry", None)
    creds = Credentials(**payload)
    if expiry:
        from datetime import datetime as _dt

        creds.expiry = _dt.fromisoformat(expiry)
    return creds


def get_valid_access_token(creds_dict: dict) -> tuple[str, str | None]:
    """Return (currently valid access token, expires_at isoformat).

    Refreshes via the stored refresh token when expired. The browser only ever
    receives this short-lived value inside the Picker flow (Task 4) — the
    refresh token and download authority stay server-side.
    """
    creds = credentials_from_dict(creds_dict)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    expires_at = creds.expiry.isoformat() if creds.expiry else None
    return creds.token or "", expires_at


def revoke_tokens(creds_dict: dict) -> None:
    """Best-effort revocation at Google's /revoke (never blocks the route).

    Prefers the refresh token (longer-lived). Failures are logged server-side
    only — disconnect still clears the local connection record.
    """
    import logging

    import requests

    creds = credentials_from_dict(creds_dict)
    token = creds.refresh_token or creds.token
    if not token:
        return
    try:
        response = requests.post(
            "https://oauth2.googleapis.com/revoke",
            data={"token": token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=5,
        )
        if not response.ok:
            logging.getLogger(__name__).warning("ga4 revoke returned HTTP %s", response.status_code)
    except requests.RequestException:
        logging.getLogger(__name__).warning("ga4 revoke failed (non-critical)")


def build_ga4_client(creds_dict: dict):
    """Build the async GA4 Data API client from stored credentials."""
    from google.analytics.data_v1beta import BetaAnalyticsDataAsyncClient

    return BetaAnalyticsDataAsyncClient(credentials=credentials_from_dict(creds_dict))


# ── Task 3 — first-pull request + generic pagination ───────────────────────
def build_first_pull_request(*, property_id: str, offset: int = 0) -> RunReportRequest:
    """Server-owned request builder — the browser never sends metrics/dimensions."""
    return RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=GA4_START_DATE, end_date=GA4_END_DATE)],
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name=name) for name in CANONICAL_GA4_METRICS],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date")),
        ],
        limit=GA4_PAGE_SIZE,
        offset=offset,
        return_property_quota=True,
    )


def classify_ga4_error(exc: Exception) -> Ga4ServiceError:
    """Map provider exceptions to the locked taxonomy (Task 3 table)."""
    if isinstance(exc, Ga4ServiceError):
        return exc
    if isinstance(exc, ResourceExhausted):
        # Quota exhaustion is non-retryable — repeated server errors are
        # themselves quota-limited; no retry loop (Task 3).
        return Ga4ServiceError(
            code="ga4_quota_exhausted",
            message="Analytics reporting capacity is currently exhausted.",
            status_code=429,
        )
    if isinstance(exc, PermissionDenied):
        return Ga4ServiceError(
            code="ga4_access_denied",
            message="Access to the selected GA4 property is denied.",
            status_code=403,
        )
    if isinstance(exc, NotFound):
        return Ga4ServiceError(
            code="ga4_property_unavailable",
            message="The GA4 property is unavailable or not found.",
            status_code=404,
        )
    if isinstance(exc, (ServiceUnavailable, InternalServerError)):
        return Ga4ServiceError(
            code="ga4_provider_unavailable",
            message="Google Analytics is temporarily unavailable.",
            status_code=503,
            retryable=True,
        )
    if isinstance(exc, DeadlineExceeded):
        return Ga4ServiceError(
            code="ga4_timeout",
            message="Google Analytics took too long to respond.",
            status_code=504,
            retryable=True,
        )
    return Ga4ServiceError(
        code="ga4_provider_unavailable",
        message="Google Analytics is temporarily unavailable.",
        status_code=503,
        retryable=True,
    )


async def run_report_once_with_retry(client, request: RunReportRequest):
    """Single bounded retry for transient provider failures only.

    Retry rules (Task 3): at most one pre-response retry for 500/503; **no**
    retry for quota exhaustion, authorization, invalid-request, or
    property-access failures.
    """
    try:
        return await client.run_report(request, timeout=30)
    except ResourceExhausted:
        raise
    except DeadlineExceeded:
        raise
    except PermissionDenied:
        raise
    except NotFound:
        raise
    except (ServiceUnavailable, InternalServerError):
        # One retry only — avoids burning GA4 server-error quota.
        try:
            return await client.run_report(request, timeout=30)
        except (ServiceUnavailable, InternalServerError, ResourceExhausted, DeadlineExceeded):
            raise


def _snapshot_quota(quota) -> dict:
    """Operational quota snapshot from a **successful** response (Task 3)."""
    fields = (
        "tokens_per_day",
        "tokens_per_hour",
        "concurrent_requests",
        "server_errors_per_project_per_hour",
    )
    snapshot: dict[str, Any] = {"captured_at": datetime.now(timezone.utc).isoformat()}
    for field in fields:
        part = getattr(quota, field, None)
        if part is not None:
            snapshot[field] = {"consumed": int(part.consumed), "remaining": int(part.remaining)}
    return snapshot


async def pull_ga4_report(client, *, property_id: str) -> tuple[list, dict, dict | None]:
    """Generic offset-pagination pull with provenance + last quota snapshot.

    The production date-only report is ≈90 rows (metrics are columns; ``date``
    is the row dimension) — the loop is proven via mocked contract tests
    (Task 6), not by adding a high-cardinality dimension.
    """
    offset = 0
    rows: list = []
    page_count = 0
    expected_row_count: int | None = None
    last_quota: dict | None = None

    while True:
        response = await run_report_once_with_retry(
            client,
            build_first_pull_request(property_id=property_id, offset=offset),
        )
        page_count += 1
        page_rows = list(response.rows)
        rows.extend(page_rows)
        if expected_row_count is None:
            expected_row_count = int(response.row_count or 0)
        if response.property_quota is not None:
            last_quota = _snapshot_quota(response.property_quota)

        if not page_rows or len(rows) >= expected_row_count:
            break
        offset += len(page_rows)

    provenance = {
        "source": "ga4",
        "property_id": property_id,
        "dimensions": ["date"],
        "metrics": list(CANONICAL_GA4_METRICS),
        "start_date": GA4_START_DATE,
        "end_date": GA4_END_DATE,
        "page_count": page_count,
        "row_count": expected_row_count or 0,
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "quota_observed": last_quota is not None,
        "quota": last_quota,
    }
    return rows, provenance, last_quota


def rows_to_dataframe(rows: list) -> pd.DataFrame:
    """Convert report rows to a DataFrame (date typed; metrics numeric)."""
    records: list[dict[str, Any]] = []
    for row in rows:
        dims = [d.value for d in row.dimension_values]
        metric_values = [m.value for m in row.metric_values]
        record: dict[str, Any] = {"date": dims[0] if dims else None}
        for name, value in zip(CANONICAL_GA4_METRICS, metric_values):
            try:
                record[name] = float(value)
            except (TypeError, ValueError):
                record[name] = value
        records.append(record)
    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def build_contract_metrics() -> list[dict[str, str]]:
    """DatasetContext.metrics with measurement-contract provenance (Task 3)."""
    metrics: list[dict[str, str]] = []
    for name in CANONICAL_GA4_METRICS:
        metrics.append(
            {
                "id": name,
                "name": name,
                "contract_row": str(CONTRACT_ROWS[name]),
                "validation_status": "provisional",
            }
        )
    metrics.extend(list(UNAVAILABLE_CONTRACT_ROWS))
    return metrics


def new_transaction_id() -> str:
    """Cryptographically random transaction id (Task 1 rule: token_urlsafe)."""
    return secrets.token_urlsafe(32)


def state_key(state: str) -> str:
    """Server-side store key — never the raw state in storage (hash only)."""
    digest = hashlib.sha256(state.encode("utf-8")).hexdigest()
    return f"ie:oauth:state:{digest}"
