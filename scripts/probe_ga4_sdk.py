"""Phase 5 Task 0 — pinned-SDK probe (google-analytics-data 0.23.0).

Records the exact async-client shape, request fields, quota message fields,
and transport requirements so api/services/ga4_service.py can be written
against the installed SDK without guessing (mirrors the Phase 3 countTokens
probe discipline). Throwaway probe — deleted after recording.
"""

from __future__ import annotations

import inspect

from google.analytics.data_v1beta import (
    BetaAnalyticsDataAsyncClient,
    BetaAnalyticsDataClient,
)
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    OrderBy,
    RunReportRequest,
    RunReportResponse,
)

print("=== run_report signatures ===")
print("async:", inspect.signature(BetaAnalyticsDataAsyncClient.run_report))
print("sync: ", inspect.signature(BetaAnalyticsDataClient.run_report))

print("\n=== RunReportRequest fields ===")
print([f.name for f in RunReportRequest()._pb.DESCRIPTOR.fields])

print("\n=== RunReportResponse fields ===")
print([f.name for f in RunReportResponse()._pb.DESCRIPTOR.fields])

print("\n=== PropertyQuota fields ===")
pq = RunReportResponse()._pb.DESCRIPTOR.fields_by_name["property_quota"].message_type
for field in pq.fields:
    sub = field.message_type
    subfields = [s.name for s in sub.fields] if sub is not None else []
    print(f"  {field.name}: {subfields}")

print("\n=== quota submessage (QuotaStatus) fields ===")
for name in (
    "tokens_per_day",
    "tokens_per_hour",
    "concurrent_requests",
    "server_errors_per_project_per_hour",
    "potentially_thresholded_requests_per_hour",
):
    sub = pq.fields_by_name[name].message_type
    print(f"  {name}: {[s.name for s in sub.fields]}")

print("\n=== async transport availability ===")
try:
    import grpc  # noqa: F401

    print("grpc: installed")
except ImportError:
    print("grpc: NOT installed")
try:

    print("rest transport class: available")
except Exception as exc:  # noqa: BLE001
    print("rest transport error:", exc)

print("\n=== builder smoke (construct the locked first-pull request) ===")
req = RunReportRequest(
    property="properties/123456789",
    date_ranges=[DateRange(start_date="90daysAgo", end_date="yesterday")],
    dimensions=[Dimension(name="date")],
    metrics=[
        Metric(name="sessions"),
        Metric(name="totalUsers"),
        Metric(name="engagedSessions"),
        Metric(name="engagementRate"),
        Metric(name="bounceRate"),
    ],
    order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
    limit=10_000,
    offset=0,
    return_property_quota=True,
)
print(
    "request built OK:",
    req.property,
    "| limit",
    req.limit,
    "| return_property_quota",
    req.return_property_quota,
)
