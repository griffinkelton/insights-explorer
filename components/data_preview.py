"""Data preview — metrics row, preview table, quality scorecard, and filters."""

import pandas as pd
import streamlit as st
from utils.charts import find_date_column, find_column
from utils.data_context import with_filtered_data, with_filters_cleared
from utils.data_loader import (
    filter_dataframe,
    detect_column_types,
    ColumnType,
    smart_sample,
    detect_anomalies,
)
from utils.forecasting import forecast_metric, build_forecast_summary, build_forecast_prompt
from utils.funnels import build_funnel_data
from utils.charts import generate_forecast_chart, generate_funnel_chart
from utils.gemini_client import generate_response


def render_data_preview() -> None:
    """Render metrics row, preview table, quality card, and filter expander."""
    ctx = st.session_state.get("data_context")
    df = ctx.active_df if ctx else st.session_state.get("df")  # REMOVE legacy fallback after Step 4
    stats = st.session_state.stats

    # Use filtered data for metrics/preview if filters are active
    display_df = ctx.active_df if ctx else df

    # Use raw_df for anomaly detection (wants originals, not augmented)
    base_df = (
        ctx.raw_df if ctx else st.session_state.get("df")
    )  # REMOVE legacy fallback after Step 4

    st.markdown("")

    # ── GA4 truncation warning ──────────────────────────────────────────
    if ctx and ctx.truncated:
        st.warning(
            "⚠️ This dataset was truncated at 500,000 rows (GA4 hard cap). "
            "Summary, forecasts, and AI analysis may be based on a partial dataset. "
            "Export a narrower date range from GA4 for complete data."
        )

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
        st.dataframe(smart_sample(display_df, max_rows=10), use_container_width=True)

    # ── Column type badges ───────────────────────────────────────────────
    if df is not None and not df.empty:
        col_types = detect_column_types(display_df)
        badge_css = {
            ColumnType.DATE: ("col-date", "📅"),
            ColumnType.NUMERIC: ("col-numeric", "🔢"),
            ColumnType.CATEGORICAL: ("col-category", "🏷️"),
            ColumnType.TEXT: ("col-text", "📝"),
        }
        badges = " ".join(
            f'<span class="col-badge {badge_css[t][0]}">{badge_css[t][1]} {col}</span>'
            for col, t in col_types.items()
        )
        st.markdown(
            f'<div style="margin:0.5rem 0;">{badges}</div>',
            unsafe_allow_html=True,
        )

    # ── Data quality scorecard ───────────────────────────────────────────
    if st.session_state.get("quality_report"):
        _render_quality_scorecard(st.session_state.quality_report)

    # ── Anomaly detection table (uses original df, not augmented) ───────
    if base_df is not None:
        date_col = find_date_column(base_df)
        metric_col = find_column(base_df, ["sessions", "users"])
        if date_col and metric_col and len(base_df) >= 7:
            anomaly_df = detect_anomalies(base_df, date_col, metric_col)
            anomalies = anomaly_df[anomaly_df["is_anomaly"]]
            if not anomalies.empty:
                with st.expander(
                    f"⚠️ {len(anomalies)} Anomalies Detected ({metric_col})",
                    expanded=False,
                ):
                    st.dataframe(
                        anomalies[[date_col, metric_col, "z_score"]]
                        .sort_values("z_score", key=abs, ascending=False)
                        .head(20),
                        use_container_width=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Forecast card ────────────────────────────────────────────────────
    _render_forecast_section(base_df)

    # ── Funnel analysis ──────────────────────────────────────────────────
    _render_funnel_section(base_df)

    # ── Data filters ─────────────────────────────────────────────────────
    if df is not None:
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
            # v0.2.0: Update DataContext (dual-write with legacy keys)
            if st.session_state.data_context is not None:
                st.session_state.data_context = with_filters_cleared(st.session_state.data_context)
            st.session_state.filters_active = False
            st.session_state.filtered_df = None
            if date_col and not dates.empty:
                st.session_state.filter_dates = (min_date, max_date)
            st.rerun()

    # Apply filters and store result (dual-write: DataContext + legacy keys)
    filtered_df = filter_dataframe(
        df,
        date_col=date_col,
        start_date=start_date,
        end_date=end_date,
        selected_columns=selected_columns,
    )

    # Build filter descriptions for provenance (from user-facing filter choices)
    filter_descriptions: tuple[str, ...] = ()
    if selected_columns != all_columns:
        filter_descriptions += (f"columns:{len(selected_columns)}/{len(all_columns)}",)
    if start_date and end_date:
        filter_descriptions += (f"date:{start_date}:{end_date}",)

    # Update DataContext if filters are active (dual-write with legacy keys)
    if filter_descriptions and st.session_state.data_context is not None:
        st.session_state.data_context = with_filtered_data(
            st.session_state.data_context, filtered_df, filter_descriptions
        )
    elif not filter_descriptions and st.session_state.data_context is not None:
        # No active filter conditions — clear any previous filters
        st.session_state.data_context = with_filters_cleared(st.session_state.data_context)

    if filtered_df.empty:
        st.warning("⚠️ No rows match your filters. Try a wider date range or select more columns.")
        st.session_state.filtered_df = filtered_df
        st.session_state.filters_active = True
    else:
        st.session_state.filtered_df = filtered_df
        st.session_state.filters_active = True
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
                f"</div>",
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
                st.caption(f"Missing expected columns: {', '.join(report.missing_columns)}")

            for warning in report.warnings:
                st.warning(warning, icon="⚠️")

            if not report.warnings:
                st.success("No significant data quality issues detected.", icon="✅")


def _render_forecast_section(base_df: pd.DataFrame | None) -> None:
    """Render the metric forecasting card with chart + AI narrative."""
    if base_df is None or base_df.empty:
        return

    date_col = find_date_column(base_df)
    numeric_cols = base_df.select_dtypes(include=["number"]).columns.tolist()
    if not date_col or not numeric_cols or len(base_df) < 7:
        return

    with st.expander("📈 Linear Trend Projection", expanded=False):
        st.caption(
            "Linear regression trend projection. Intervals are approximate "
            "model-based estimates (not validated forecast accuracy)."
        )

        col_metric, col_periods, col_btn = st.columns([2, 1, 1])
        with col_metric:
            metric_col = st.selectbox(
                "Metric",
                options=numeric_cols,
                index=0,
                key="forecast_metric",
            )
        with col_periods:
            periods = st.selectbox(
                "Periods",
                options=[7, 14, 30, 60, 90],
                index=2,
                key="forecast_periods",
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            generate = st.button(
                "🔮 Generate Forecast",
                use_container_width=True,
                key="forecast_btn",
            )

        # ── Cached forecast (recompute when params change) ────────────
        forecast_key = f"forecast_{metric_col}_{periods}"
        if generate or st.session_state.get(forecast_key):
            if generate:
                result = forecast_metric(base_df, date_col, metric_col, periods)
                if result:
                    st.session_state[forecast_key] = result
                    # Generate AI narrative
                    try:
                        prompt = build_forecast_prompt(result)
                        st.session_state[f"{forecast_key}_narrative"] = generate_response(prompt)
                    except Exception:
                        st.session_state[f"{forecast_key}_narrative"] = build_forecast_summary(
                            result
                        )
                else:
                    st.warning(f"Not enough data to forecast {metric_col}. Need at least 7 days.")
                    st.session_state[forecast_key] = None

            result = st.session_state.get(forecast_key)
            if result:
                # ── Forecast chart ───────────────────────────────────
                theme = st.session_state.get("theme", "dark")
                fig = generate_forecast_chart(result, theme=theme)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"fc_{forecast_key}")

                # ── AI narrative ─────────────────────────────────────
                narrative = st.session_state.get(
                    f"{forecast_key}_narrative",
                    build_forecast_summary(result),
                )
                with st.container(border=True):
                    st.markdown("#### 🤖 AI Trend Projection Analysis")
                    st.markdown(narrative)

                    # ── Summary stats ────────────────────────────────
                    st.caption(
                        f"R² = {result.trend_strength} · "
                        f"Confidence: {result.confidence} · "
                        f"Trend: {result.trend_direction}"
                    )


def _render_funnel_section(base_df: pd.DataFrame | None) -> None:
    """Render the funnel analysis section — define steps and see conversion path."""
    if base_df is None or base_df.empty:
        return

    # Find a page/path column and a metric column
    page_cols = [
        c
        for c in base_df.columns
        if any(kw in c.lower() for kw in ["page", "path", "url", "landing", "screen"])
    ]
    numeric_cols = base_df.select_dtypes(include=["number"]).columns.tolist()
    if not page_cols or not numeric_cols:
        return

    with st.expander("🔻 Page-Path Aggregation", expanded=False):
        st.caption(
            "Compare page-volume totals for selected path patterns. This analyzes "
            "independent page matches — it does not track user/session conversion sequencing."
        )

        col_page, col_metric = st.columns(2)
        with col_page:
            page_col = st.selectbox(
                "Page column",
                options=page_cols,
                key="funnel_page_col",
            )
        with col_metric:
            metric_col = st.selectbox(
                "Metric",
                options=numeric_cols,
                index=(
                    0
                    if "sessions" not in numeric_cols
                    else numeric_cols.index("sessions") if "sessions" in numeric_cols else 0
                ),
                key="funnel_metric_col",
            )

        # ── Step manager ───────────────────────────────────────────────
        funnel_steps = st.session_state.get("funnel_steps", [])

        # Show existing steps with remove buttons
        for i, step in enumerate(funnel_steps):
            col_step, col_del = st.columns([5, 1])
            with col_step:
                st.markdown(f"**{i + 1}.** `{step}`")
            with col_del:
                if st.button("✕", key=f"del_step_{i}", help=f"Remove {step}"):
                    st.session_state.funnel_steps.pop(i)
                    st.rerun()

        # Add new step
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            new_step = st.text_input(
                "Add step (page pattern)",
                placeholder="e.g., /home or product",
                key="funnel_new_step",
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Add", use_container_width=True, key="funnel_add_step"):
                if new_step.strip() and new_step not in funnel_steps:
                    funnel_steps.append(new_step.strip())
                    st.session_state.funnel_steps = funnel_steps
                    st.session_state.funnel_new_step = ""
                    st.rerun()
                elif new_step in funnel_steps:
                    st.warning("Step already in funnel.")

        # Show available page values as hints
        if page_col and len(funnel_steps) == 0:
            sample_pages = base_df[page_col].dropna().astype(str).unique()[:8].tolist()
            if sample_pages:
                st.caption("Sample pages: " + ", ".join(f"`{p[:40]}`" for p in sample_pages))

        # ── Generate button ────────────────────────────────────────────
        if len(funnel_steps) >= 2:
            if st.button("🔻 Generate Page-Path Chart", use_container_width=True, key="funnel_btn"):
                funnel_data = build_funnel_data(base_df, page_col, metric_col, funnel_steps)
                if funnel_data:
                    st.session_state.funnel_data = funnel_data
                else:
                    st.warning(
                        "No matches found for the defined steps. "
                        "Try broader patterns or check the page column."
                    )

        # ── Render funnel chart ────────────────────────────────────────
        funnel_data = st.session_state.get("funnel_data")
        if funnel_data:
            theme = st.session_state.get("theme", "dark")
            fig = generate_funnel_chart(funnel_data, theme=theme)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="funnel_chart")

            # Clear funnel button
            if st.button("🗑️ Clear Funnel", use_container_width=True, key="clear_funnel"):
                st.session_state.funnel_data = None
                st.session_state.funnel_steps = []
                st.rerun()
