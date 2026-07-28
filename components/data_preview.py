"""Data preview — metrics row, preview table, quality scorecard, and filters."""

import pandas as pd
import streamlit as st
from utils.charts import find_date_column
from utils.data_loader import filter_dataframe


def render_data_preview() -> None:
    """Render metrics row, preview table, quality card, and filter expander."""
    df = st.session_state.df
    stats = st.session_state.stats

    # Use filtered data for metrics/preview if available
    display_df = st.session_state.filtered_df if st.session_state.filtered_df is not None else df

    st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)

    # ── Metrics row ──────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Total Rows", f"{len(display_df):,}")
    with col2:
        st.metric("📊 Columns", len(display_df.columns))
    with col3:
        st.metric("📅 From", stats.get("date_range_start", "—"))
    with col4:
        st.metric("📅 To", stats.get("date_range_end", "—"))

    # ── Preview table ────────────────────────────────────────────────────
    with st.expander("🔍 Preview Table (first 10 rows)", expanded=False):
        st.dataframe(display_df.head(10), use_container_width=True)

    # ── Data quality scorecard ───────────────────────────────────────────
    if st.session_state.get("quality_report"):
        _render_quality_scorecard(st.session_state.quality_report)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Data filters ─────────────────────────────────────────────────────
    if st.session_state.df is not None:
        with st.expander("🔍 Filter Data", expanded=False):
            _render_data_filters(df)


def _render_data_filters(df: pd.DataFrame) -> None:
    """Render column picker and date range filter controls."""
    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1])

    date_col = find_date_column(df)
    all_columns = df.columns.tolist()
    dates = None
    min_date = None
    max_date = None

    with col_filter1:
        selected_columns = st.multiselect(
            "Columns to include",
            options=all_columns,
            default=all_columns,
            key="filter_columns",
        )

    with col_filter2:
        start_date = None
        end_date = None
        if date_col:
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if not dates.empty:
                min_date = dates.min().date()
                max_date = dates.max().date()
                date_range = st.date_input(
                    "Date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="filter_dates",
                )
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date = str(date_range[0])
                    end_date = str(date_range[1])

    with col_filter3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.session_state.filter_columns = all_columns
            if date_col and not dates.empty:
                st.session_state.filter_dates = (min_date, max_date)
            st.rerun()

    # Apply filters and store result
    filtered_df = filter_dataframe(
        df,
        date_col=date_col,
        start_date=start_date,
        end_date=end_date,
        selected_columns=selected_columns,
    )

    if filtered_df.empty:
        st.warning("⚠️ No rows match your filters. Try a wider date range or select more columns.")
        st.session_state.filtered_df = None
    else:
        st.session_state.filtered_df = filtered_df
        st.caption(f"Showing {len(filtered_df):,} of {len(df):,} rows")


def _render_quality_scorecard(report) -> None:
    """Render the data quality scorecard as a styled A-F grade card."""
    grade_colors = {
        "A": "#34d399",
        "B": "#818cf8",
        "C": "#fbbf24",
        "D": "#f59e0b",
        "F": "#f87171",
    }
    color = grade_colors.get(report.grade, "#686880")

    with st.container(border=True):
        col_grade, col_stats = st.columns([0.2, 0.8])

        with col_grade:
            st.markdown(
                f'<div style="text-align:center;padding:1rem 0;">'
                f'<div style="font-size:3.5rem;font-weight:800;color:{color};'
                f'line-height:1;">{report.grade}</div>'
                f'<div style="font-size:0.7rem;color:#686880;text-transform:uppercase;'
                f'letter-spacing:0.08em;">Data Quality</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_stats:
            parts = [
                f"**{report.completeness_pct}%** completeness",
                f"**{report.column_count}** columns",
                f"**{report.duplicate_count:,}** duplicates",
            ]
            if report.outlier_count:
                parts.append(f"**{report.outlier_count}** outliers")
            st.markdown(" · ".join(parts))

            if report.date_range_days is not None:
                st.markdown(
                    f"📅 **{report.date_range_days}** days of data "
                    f"({report.date_gaps} missing days)"
                )

            if report.missing_columns:
                st.caption(
                    f"Missing expected columns: {', '.join(report.missing_columns)}"
                )

            for warning in report.warnings:
                st.warning(warning, icon="⚠️")

            if not report.warnings:
                st.success("No significant data quality issues detected.", icon="✅")
