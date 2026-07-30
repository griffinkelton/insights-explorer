"""Page-path aggregation — compare page-volume totals for selected path patterns."""

from dataclasses import dataclass
import pandas as pd


@dataclass
class FunnelData:
    """Structured page-path aggregation output for charting."""

    steps: list[str]  # Ordered funnel step labels
    counts: list[float]  # Metric count at each step
    dropoff_pct: list[float]  # Drop-off % from previous step (0.0 for first)
    metric_col: str  # e.g. "sessions" or "users"
    page_col: str  # The column used for page matching


def build_funnel_data(
    df: pd.DataFrame,
    page_col: str,
    metric_col: str,
    steps: list[str],
) -> FunnelData | None:
    """Aggregate page-level data into ordered path-step totals.

    This is page-pattern aggregation — each step independently matches rows
    where ``page_col`` contains the step pattern (case-insensitive, literal
    match). It does NOT track user/session conversion sequencing.

    Args:
        df: Source DataFrame with page-level rows.
        page_col: Column name containing page paths/URLs.
        metric_col: Column name to aggregate (e.g. "sessions", "users").
        steps: Ordered list of page patterns (e.g. ["/home", "/product", "/cart"]).

    Returns:
        FunnelData with steps, counts, and change from previous, or None if no data.
    """
    if df is None or df.empty or not steps or page_col not in df.columns:
        return None
    if metric_col not in df.columns:
        return None

    # Cap at 8 steps max
    steps = [s.strip() for s in steps[:8]]

    counts: list[float] = []
    for step in steps:
        # Literal case-insensitive match (regex=False) on the page column
        mask = df[page_col].astype(str).str.contains(step, case=False, regex=False, na=False)
        matched = df[mask]
        count = float(matched[metric_col].sum()) if not matched.empty else 0.0
        counts.append(count)

    # ── Change from previous ───────────────────────────────────────────
    dropoff: list[float] = [0.0]
    for i in range(1, len(counts)):
        prev = counts[i - 1]
        curr = counts[i]
        if prev > 0:
            dropoff.append(round((1 - curr / prev) * 100, 1))
        else:
            dropoff.append(0.0)

    return FunnelData(
        steps=steps,
        counts=counts,
        dropoff_pct=dropoff,
        metric_col=metric_col,
        page_col=page_col,
    )
