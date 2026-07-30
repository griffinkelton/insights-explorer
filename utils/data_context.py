"""Immutable data lifecycle contract for GA4 Insight Explorer.

Replaces the distributed session-state pattern (df, filtered_df, custom_metrics_df,
filters_active) with a single frozen DataContext in st.session_state.data_context.

IMPORTANT: frozen=True is shallow only. DataFrames inside are still mutable.
The invariant is: NO code may mutate raw_df or active_df in place.
Transformations create new DataFrames and return a replacement DataContext.
"""

from dataclasses import dataclass
from typing import NamedTuple

import pandas as pd


class FilterState(NamedTuple):
    """Immutable description of active filters."""

    descriptions: tuple[str, ...] = ()
    is_active: bool = False
    row_count: int = 0  # 0 means empty result (preserved, not None)


@dataclass(frozen=True)
class DataContext:
    """Immutable data lifecycle contract.

    All analysis functions receive this explicitly — no st.session_state reads.
    Transformations return a new DataContext via dataclasses.replace().
    """

    source_id: str  # e.g. "file:report.csv", "ga4:property_123"
    version: int  # Monotonic — incremented on every analysis-relevant transition
    raw_df: pd.DataFrame  # Original loaded data (never modified after creation)
    active_df: pd.DataFrame  # Current analysis DataFrame (filters + custom metrics applied)
    filters: FilterState = FilterState()
    provenance: tuple[str, ...] = ()  # Human-readable history: ("uploaded", "filters-applied")
    truncated: bool = False  # True if GA4 500k cap was hit

    @property
    def cache_key(self) -> str:
        """Stable cache namespace: source_id + version."""
        return f"{self.source_id}:v{self.version}"


# ── Factory Functions ───────────────────────────────────────────────────────


def create_context_from_upload(df: pd.DataFrame, source_name: str) -> DataContext:
    """Create a DataContext from an uploaded file.

    Args:
        df: Validated DataFrame from data_loader.
        source_name: Original filename (e.g. "Q3_report.csv").

    Returns:
        DataContext with version=0, raw_df and active_df both set to copies of df.
    """
    return DataContext(
        source_id=f"file:{source_name}",
        version=0,
        raw_df=df.copy(),
        active_df=df.copy(),
        provenance=("uploaded",),
    )


def create_context_from_ga4(
    df: pd.DataFrame, property_id: str, truncated: bool = False
) -> DataContext:
    """Create a DataContext from a GA4 data pull.

    Args:
        df: DataFrame returned by ga4_client.pull_ga4_report().
        property_id: GA4 property identifier.
        truncated: True if the 500k row cap was hit.

    Returns:
        DataContext with version=0 and truncated flag set appropriately.
    """
    return DataContext(
        source_id=f"ga4:{property_id}",
        version=0,
        raw_df=df.copy(),
        active_df=df.copy(),
        provenance=("ga4-pull",),
        truncated=truncated,
    )


# ── Transition Functions (return new DataContext) ───────────────────────────


def with_filtered_data(
    context: DataContext,
    filtered_df: pd.DataFrame,
    filters: FilterState,
) -> DataContext:
    """Return a new DataContext with filters applied. Version increments.

    Args:
        context: Existing DataContext.
        filtered_df: Filtered DataFrame (may be empty with 0 rows).
        filters: Immutable FilterState describing the active filters.

    Returns:
        New DataContext with version bumped, active_df set to filtered_df,
        and provenance updated.
    """
    if filtered_df is not None:
        filtered_df = filtered_df.copy()
    new_filters = FilterState(
        descriptions=filters.descriptions,
        is_active=filters.is_active,
        row_count=len(filtered_df) if filtered_df is not None else 0,
    )
    return DataContext(
        source_id=context.source_id,
        version=context.version + 1,
        raw_df=context.raw_df,
        active_df=filtered_df if filtered_df is not None else context.active_df,
        filters=new_filters,
        provenance=(*context.provenance, "filters-applied"),
        truncated=context.truncated,
    )


def with_custom_metrics(context: DataContext, metrics_df: pd.DataFrame) -> DataContext:
    """Return a new DataContext with custom metrics DataFrame. Version increments.

    Args:
        context: Existing DataContext.
        metrics_df: DataFrame with custom metric columns added.

    Returns:
        New DataContext with version bumped, active_df set to metrics_df.
    """
    return DataContext(
        source_id=context.source_id,
        version=context.version + 1,
        raw_df=context.raw_df,
        active_df=metrics_df.copy(),
        filters=context.filters,
        provenance=(*context.provenance, "custom-metrics-applied"),
        truncated=context.truncated,
    )


def with_filters_cleared(context: DataContext) -> DataContext:
    """Return a new DataContext reverting active_df to raw_df. Version increments.

    Args:
        context: Existing DataContext with filters applied.

    Returns:
        New DataContext with version bumped, active_df reset to raw_df copy,
        filters cleared, provenance updated.
    """
    return DataContext(
        source_id=context.source_id,
        version=context.version + 1,
        raw_df=context.raw_df,
        active_df=context.raw_df.copy(),
        filters=FilterState(),
        provenance=(*context.provenance, "filters-cleared"),
        truncated=context.truncated,
    )
