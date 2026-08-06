"""Quality report adapter — maps ``utils.data_loader``'s A–F scorecard to the
API schema. The initial endpoint calls it directly; Phase 2 removes any
Streamlit coupling from the underlying module."""

from __future__ import annotations

import pandas as pd

from api.schemas import QualityReport


def build_quality_report(df: pd.DataFrame, missing_cols: list[str] | None = None) -> QualityReport:
    """Adapt utils.data_loader.assess_data_quality / DataQualityReport."""
    from utils.data_loader import assess_data_quality  # direct until Phase 2 decoupling

    report = assess_data_quality(df, missing_cols)
    return QualityReport(
        grade=report.grade,
        completeness_pct=report.completeness_pct,
        duplicate_pct=report.duplicate_pct,
        duplicate_count=report.duplicate_count,
        outlier_count=report.outlier_count,
        date_range_days=report.date_range_days,
        date_gaps=report.date_gaps,
        column_count=report.column_count,
        missing_columns=report.missing_columns,
        warnings=report.warnings,
    )
