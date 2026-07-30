"""Immutable data lifecycle contract for GA4 Insight Explorer — v0.2.0 final.

3-LAYER MODEL:
    raw_df   — Original loaded upload or GA4 result. Never filtered, never
               mutated in place. The immutable ground truth.
    base_df  — Current unfiltered analytical dataset. Initially a copy of
               raw_df. After custom metrics, becomes the custom-metric output.
               This is what "clear filters" restores to.
    active_df — The currently analyzed dataset. When filters are active:
               filtered base_df. When filters are clear: same as base_df.

OWNERSHIP: A DataContext owns its three DataFrames. No caller may retain a
mutable reference and mutate it after passing it to a factory or transition.
Transformations create new DataFrames and return a replacement DataContext.

IMPORTANT: frozen=True is shallow only. DataFrames inside are still mutable.
The invariant is: NO code may mutate raw_df, base_df, or active_df in place.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import NamedTuple

import pandas as pd


# ── FilterState ──────────────────────────────────────────────────────────────


class FilterState(NamedTuple):
    """Immutable description of active filters.

    Attributes:
        descriptions: Human-readable filter descriptions (non-empty when active).
        is_active: True when filters are applied (even if result is empty).
        row_count: Must equal len(active_df). 0 means empty result (valid, not None).
    """

    descriptions: tuple[str, ...] = ()
    is_active: bool = False
    row_count: int = 0


# ── DataContext ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DataContext:
    """Immutable data lifecycle contract — 3-layer DataFrame model.

    All analysis functions receive this explicitly — no st.session_state reads.
    Transformations return a new DataContext via dataclasses.replace().
    """

    source_id: str  # Content-derived: "file:{sha256[:24]}" or "ga4:{sha256[:24]}"
    version: int  # Monotonic — incremented on every analysis-relevant transition
    raw_df: pd.DataFrame  # Original loaded data (never modified after creation)
    base_df: pd.DataFrame  # Unfiltered analytical base (custom metrics modify this)
    active_df: (
        pd.DataFrame
    )  # Current analysis surface (filtered base_df, or base_df when no filters)
    filters: FilterState = FilterState()
    provenance: tuple[str, ...] = ()  # category:detail format: ("upload:Q3.csv", "filters:a>1")
    truncated: bool = False  # True if GA4 500k cap was hit

    @property
    def cache_key(self) -> str:
        """Stable cache namespace prefix: source_id + version.

        Note: This is a namespace prefix. Cached functions must also include
        ALL output-affecting parameters as explicit arguments.
        """
        return f"{self.source_id}:v{self.version}"


# ── Fingerprint ──────────────────────────────────────────────────────────────


def fingerprint_frame(df: pd.DataFrame) -> str:
    """Content-derived fingerprint of a DataFrame for cache identity.

    Changes when values, index, column order, or dtypes change.
    Use this instead of passing the full DataFrame to @st.cache_data functions
    to keep cache hashing lightweight while still detecting data changes.

    Returns:
        24-char hex string (96 bits) — negligible collision risk.
    """
    hashes = pd.util.hash_pandas_object(df)
    return hashlib.sha256(hashes.values).hexdigest()[:24]


# ══════════════════════════════════════════════════════════════════════════════
# Factory Functions
# ══════════════════════════════════════════════════════════════════════════════


def create_context_from_upload(
    df: pd.DataFrame,
    file_bytes: bytes,
    display_name: str = "",
) -> DataContext:
    """Create a DataContext from uploaded file bytes.

    Uses SHA-256 of file content for source_id — same bytes = same ID,
    different bytes = different ID regardless of filename.

    Args:
        df: Validated DataFrame from data_loader.
        file_bytes: Raw file bytes (for content-derived source_id).
        display_name: Human-readable filename stored in provenance, not in the
                      cache namespace.

    Returns:
        DataContext with version=0.
    """
    content_hash = hashlib.sha256(file_bytes).hexdigest()[:24]
    base = df.copy(deep=True)
    return DataContext(
        source_id=f"file:{content_hash}",
        version=0,
        raw_df=df.copy(deep=True),
        base_df=base,
        active_df=base.copy(deep=True),
        provenance=(f"upload:{display_name}",) if display_name else ("upload",),
    )


def create_context_from_ga4(
    df: pd.DataFrame,
    property_id: str,
    date_range: tuple[str, str] | None = None,
    dimensions: list[str] | None = None,
    metrics: list[str] | None = None,
    dimension_filter: dict | None = None,
    metric_filter: dict | None = None,
    order_bys: list[dict] | None = None,
    limit: int | None = None,
    offset: int = 0,
    timezone: str | None = None,
    truncated: bool = False,
) -> DataContext:
    """Create a DataContext from a GA4 data pull.

    Uses SHA-256 of the canonical request fingerprint for source_id.
    Every return-value-affecting request field is included. Identical
    requests produce the same source_id (legitimate cache reuse); any
    difference in parameters produces a distinct ID.

    Args:
        df: DataFrame returned by ga4_client.pull_ga4_report().
        property_id: GA4 property identifier.
        date_range: (start_date, end_date) tuple.
        dimensions: List of dimension names requested.
        metrics: List of metric names requested.
        dimension_filter: Optional GA4 dimension filter expression.
        metric_filter: Optional GA4 metric filter expression.
        order_bys: Optional sort specifications.
        limit: Optional row limit.
        offset: Row offset (default 0).
        timezone: Optional timezone override.
        truncated: True if the 500k row cap was hit.

    Returns:
        DataContext with version=0 and truncated flag set appropriately.
    """
    # Canonical request fingerprint — every return-value-affecting field
    request = {
        "property_id": property_id,
        "date_range": list(date_range) if date_range else None,
        "dimensions": sorted(dimensions) if dimensions else None,
        "metrics": sorted(metrics) if metrics else None,
        "dimension_filter": dimension_filter,
        "metric_filter": metric_filter,
        "order_bys": order_bys or [],
        "limit": limit,
        "offset": offset,
        "timezone": timezone,
    }
    canonical = json.dumps(
        request,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    # 24 hex chars = 96 bits — negligible collision risk for local app
    request_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]

    base = df.copy(deep=True)
    return DataContext(
        source_id=f"ga4:{request_hash}",
        version=0,
        raw_df=df.copy(deep=True),
        base_df=base,
        active_df=base.copy(deep=True),
        provenance=(f"ga4_pull:{property_id}",),
        truncated=truncated,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Transition Functions (return new DataContext)
# ══════════════════════════════════════════════════════════════════════════════
#
# No-op contract: True no-ops do NOT create a new context or increment version.
# This avoids pointless cache churn and noisy provenance. If the UI treats
# clicking a button as meaningful, it shows feedback without invalidating
# analytical caches.
#
# - Clearing filters when none are active → return original context unchanged
# - Applying an identical filter → return original context unchanged
# - Applying unchanged custom metrics → return original context unchanged


def with_custom_metrics(
    context: DataContext,
    metrics_df: pd.DataFrame,
) -> DataContext:
    """Replace the analytical base and clear filters by default.

    Custom metrics change the schema/derived values. Prior filters may not be
    meaningful against the new columns. Clearing filters is the safe default;
    reapply_filters() is a separate, explicit path if needed later.

    Args:
        context: Existing DataContext.
        metrics_df: DataFrame with custom metric columns added.

    Returns:
        New DataContext with base_df replaced, active_df reset, filters cleared.
        Returns context unchanged if metrics_df is identical to base_df (no-op).

    Raises:
        ValueError: if metrics_df is None.
        TypeError: if metrics_df is not a pandas DataFrame.
    """
    if metrics_df is None:
        raise ValueError("metrics_df must be a DataFrame")
    if not isinstance(metrics_df, pd.DataFrame):
        raise TypeError("metrics_df must be a pandas DataFrame")

    # No-op: metrics unchanged
    if metrics_df.equals(context.base_df):
        return context

    base_df = metrics_df.copy(deep=True)
    return replace(
        context,
        version=context.version + 1,
        base_df=base_df,
        active_df=base_df.copy(deep=True),
        filters=FilterState(),
        provenance=(*context.provenance, "custom_metrics:applied"),
    )


def with_filtered_data(
    context: DataContext,
    filtered_df: pd.DataFrame,
    descriptions: tuple[str, ...],
) -> DataContext:
    """Set the filtered active dataset. Zero rows are valid and preserved.

    Args:
        context: Existing DataContext.
        filtered_df: Filtered DataFrame (may be empty with 0 rows).
        descriptions: Human-readable filter descriptions (non-empty —
                      active filters require at least one description).

    Returns:
        New DataContext with active_df set, filters recorded, version bumped.
        Returns context unchanged if same filter is already applied (no-op).

    Raises:
        ValueError: if filtered_df is None.
        TypeError: if filtered_df is not a pandas DataFrame.
        ValueError: if descriptions is empty.
    """
    if filtered_df is None:
        raise ValueError("filtered_df must be a DataFrame, not None")
    if not isinstance(filtered_df, pd.DataFrame):
        raise TypeError("filtered_df must be a pandas DataFrame")
    if not descriptions:
        raise ValueError("active filters require at least one description")

    new_filters = FilterState(
        descriptions=descriptions,
        is_active=True,
        row_count=len(filtered_df),
    )

    # No-op: same filters already applied
    if new_filters == context.filters and filtered_df.equals(context.active_df):
        return context

    active_df = filtered_df.copy(deep=True)
    return replace(
        context,
        version=context.version + 1,
        active_df=active_df,
        filters=new_filters,
        provenance=(*context.provenance, f"filters:{'|'.join(descriptions)}"),
    )


def with_filters_cleared(context: DataContext) -> DataContext:
    """Restore the current unfiltered analytical base.

    Restores active_df from base_df (NOT raw_df) — this preserves custom metrics
    that were applied before filtering.

    Args:
        context: Existing DataContext.

    Returns:
        New DataContext with active_df restored, filters cleared, version bumped.
        Returns context unchanged if no filters are currently active (no-op).
    """
    # No-op: filters already clear
    if not context.filters.is_active:
        return context

    return replace(
        context,
        version=context.version + 1,
        active_df=context.base_df.copy(deep=True),
        filters=FilterState(),
        provenance=(*context.provenance, "filters:cleared"),
    )
