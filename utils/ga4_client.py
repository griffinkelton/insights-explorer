"""Google Analytics 4 Data API client with OAuth 2.0 authentication."""

from typing import Any
import os
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

# OAuth scopes — read-only Analytics access
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

# Path to client secret JSON file for OAuth (downloaded from GCP Console)
CLIENT_SECRETS_FILE = os.getenv(
    "GA4_CLIENT_SECRETS_PATH", "client_secrets.json"
)


def get_auth_url(redirect_uri: str) -> tuple[str, Flow]:
    """Generate a Google OAuth authorization URL.

    Returns (url, flow) — the flow must be stored for token exchange.
    """
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",  # Always get a refresh token
    )
    return auth_url, flow


def exchange_code(flow: Flow, code: str) -> Credentials:
    """Exchange the OAuth authorization code for credentials."""
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_to_dict(creds: Credentials) -> dict[str, Any]:
    """Serialize credentials to a JSON-safe dict for st.session_state."""
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }


def credentials_from_dict(creds_dict: dict[str, Any]) -> Credentials:
    """Deserialize credentials from a JSON-safe dict."""
    return Credentials(**creds_dict)


def pull_ga4_report(
    credentials: Credentials,
    property_id: str,
    start_date: str = "90daysAgo",
    end_date: str = "today",
) -> pd.DataFrame:
    """Pull a standard GA4 report and return as a pandas DataFrame.

    Fetches: date, pagePath, deviceCategory dimensions
             + sessions, totalUsers, activeUsers, engagementRate, bounceRate metrics.
    """
    # Refresh token if needed
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    client = BetaAnalyticsDataClient(credentials=credentials)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="date"),
            Dimension(name="pagePath"),
            Dimension(name="deviceCategory"),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="activeUsers"),
            Metric(name="engagementRate"),
            Metric(name="bounceRate"),
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=100000,  # GA4 API max per request
    )

    response = client.run_report(request)

    # Build DataFrame from response rows
    rows = []
    for row in response.rows:
        rows.append({
            "date": row.dimension_values[0].value,
            "page_path": row.dimension_values[1].value,
            "device_category": row.dimension_values[2].value,
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
            "active_users": int(row.metric_values[2].value),
            "engagement_rate": float(row.metric_values[3].value),
            "bounce_rate": float(row.metric_values[4].value),
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df
