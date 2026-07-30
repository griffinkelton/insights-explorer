"""Chart generation helpers — extracted from app.py."""

import logging
from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import find_date_column

logger = logging.getLogger(__name__)


def generate_chart(
    df: pd.DataFrame,
    chart_config: dict[str, str],
    gemini_response: str,
    user_question: str,
    theme: str = "dark",
) -> dict[str, Any] | None:
    """Generate a Plotly chart based on detected chart config.

    Args:
        theme: "dark" (default) or "light". Controls plotly template + font colors.

    Returns {"fig": go.Figure, "type": "line"|"bar"} or None.
    """
    template = "plotly_dark" if theme == "dark" else "plotly_light"
    font_color = "#9898b0" if theme == "dark" else "#4b5563"
    chart_type = chart_config.get("chart_type", "bar")
    try:
        date_col = find_date_column(df)

        if chart_type == "line" and date_col:
            sessions_col = find_column(df, ["sessions"])
            if sessions_col and sessions_col in df.columns:
                daily = df.groupby(date_col)[sessions_col].sum().reset_index().sort_values(date_col)
                fig = px.line(
                    daily,
                    x=date_col,
                    y=sessions_col,
                    title="Sessions Over Time",
                    markers=True,
                    template=template,
                    color_discrete_sequence=["#818cf8"],
                )
                fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Sessions",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=font_color, size=12),
                    margin=dict(l=20, r=20, t=40, b=20),
                    hovermode="x unified",
                )
                return {"fig": fig, "type": "line"}

        if chart_type in ("bar", "ranking"):
            page_col = find_column(df, ["page_path", "page", "path", "url", "landing_page"])
            sessions_col = find_column(df, ["sessions"])
            if page_col and sessions_col and page_col in df.columns and sessions_col in df.columns:
                top = df.groupby(page_col)[sessions_col].sum().nlargest(10).reset_index()
                fig = px.bar(
                    top,
                    x=sessions_col,
                    y=page_col,
                    orientation="h",
                    title=f"Top Pages by {sessions_col.replace('_', ' ').title()}",
                    template=template,
                    color_discrete_sequence=["#818cf8"],
                    text_auto=".1s",
                )
                fig.update_traces(textposition="outside", textfont=dict(color=font_color, size=11))
                fig.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=font_color, size=12),
                    margin=dict(l=20, r=40, t=40, b=20),
                )
                return {"fig": fig, "type": "bar"}

        # Fallback
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        if numeric_cols and categorical_cols:
            cat_col, num_col = categorical_cols[0], numeric_cols[0]
            if cat_col not in df.columns or num_col not in df.columns:
                return None
            agg = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()
            fig = px.bar(
                agg,
                x=num_col,
                y=cat_col,
                orientation="h",
                title=f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                template=template,
                color_discrete_sequence=["#818cf8"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=font_color, size=12),
            )
            return {"fig": fig, "type": "bar"}
    except (KeyError, TypeError, ValueError) as e:
        logger.info("Chart generation skipped: %s", e)
        return None
    except Exception:
        logger.warning("Chart generation error", exc_info=True)
        return None


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Case-insensitive column lookup by candidate names."""
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        key = candidate.lower().strip()
        if key in df_cols_lower:
            return df_cols_lower[key]
    return None


def generate_forecast_chart(
    result: Any,
    theme: str = "dark",
) -> go.Figure | None:
    """Generate a Plotly chart showing historical data + forecast with CI band.

    Args:
        result: ForecastResult from utils.forecasting.forecast_metric().
        theme: "dark" or "light".

    Returns:
        A Plotly Figure, or None if the result is invalid.
    """
    if result is None:
        return None

    template = "plotly_dark" if theme == "dark" else "plotly_light"
    font_color = "#9898b0" if theme == "dark" else "#4b5563"
    actual_color = "#818cf8"  # Indigo
    forecast_color = "#f59e0b"  # Amber
    band_color = "rgba(245, 158, 11, 0.15)"  # Semi-transparent amber

    daily = result.daily
    forecast_df = result.forecast_df
    metric_col = result.metric_col

    fig = go.Figure()

    # ── Historical actuals (solid line) ────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=daily[daily.columns[0]],
            y=daily[metric_col],
            mode="lines",
            name="Actual",
            line=dict(color=actual_color, width=2.5),
            hovertemplate=f"Date: %{{x|%b %d, %Y}}<br>{metric_col}: %{{y:,.0f}}<extra>Actual</extra>",
        )
    )

    # ── Confidence band (shaded area) ───────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=pd.concat([forecast_df["date"], forecast_df["date"][::-1]]),
            y=pd.concat([forecast_df["upper_bound"], forecast_df["lower_bound"][::-1]]),
            fill="toself",
            fillcolor=band_color,
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=True,
            name="95% CI",
            hoverinfo="skip",
        )
    )

    # ── Forecast line (dashed) ──────────────────────────────────────────
    fig.add_trace(
        go.Scatter(
            x=forecast_df["date"],
            y=forecast_df["predicted"],
            mode="lines",
            name="Forecast",
            line=dict(color=forecast_color, width=2.5, dash="dash"),
            hovertemplate=(
                "Date: %{x|%b %d, %Y}<br>Predicted: %{y:,.0f}<br>"
                "95% CI: %{customdata[0]:,.0f} – %{customdata[1]:,.0f}<extra>Forecast</extra>"
            ),
            customdata=forecast_df[["lower_bound", "upper_bound"]].values,
        )
    )

    # ── Divider line (vertical, today → tomorrow) ───────────────────────
    last_actual_date = daily[daily.columns[0]].iloc[-1]
    fig.add_vline(
        x=last_actual_date,
        line_dash="dot",
        line_color="#686880",
        line_width=1,
        opacity=0.5,
    )

    periods = result.periods
    fig.update_layout(
        title=f"{metric_col.replace('_', ' ').title()} — {periods}-Day Forecast",
        xaxis_title="Date",
        yaxis_title=metric_col.replace("_", " ").title(),
        template=template,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color, size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig


def generate_funnel_chart(
    funnel_data: Any,
    theme: str = "dark",
) -> go.Figure | None:
    """Generate a Plotly funnel chart with drop-off annotations.

    Args:
        funnel_data: FunnelData from utils.funnels.build_funnel_data().
        theme: "dark" or "light".

    Returns:
        A Plotly Figure, or None if funnel_data is invalid.
    """
    if funnel_data is None or not funnel_data.steps:
        return None

    template = "plotly_dark" if theme == "dark" else "plotly_light"
    font_color = "#9898b0" if theme == "dark" else "#4b5563"
    bar_color = "#818cf8"

    steps = funnel_data.steps
    counts = funnel_data.counts
    dropoff = funnel_data.dropoff_pct
    metric_label = funnel_data.metric_col.replace("_", " ").title()

    fig = go.Figure()

    # ── Funnel bars ─────────────────────────────────────────────────────
    # Build labels with count + drop-off %
    labels = []
    for i, (step, count, dp) in enumerate(zip(steps, counts, dropoff)):
        if i == 0:
            labels.append(f"{step}<br>{count:,.0f} {metric_label}")
        else:
            labels.append(
                f"{step}<br>{count:,.0f} {metric_label}<br>"
                f"<span style='color:#f87171;font-size:0.85em;'>{dp:+.1f}% change</span>"
            )

    fig.add_trace(
        go.Bar(
            x=counts,
            y=steps,
            orientation="h",
            text=labels,
            textposition="inside",
            insidetextanchor="middle",
            marker=dict(
                color=bar_color,
                line=dict(color="rgba(255,255,255,0.1)", width=1),
            ),
            hovertemplate=(
                "Step: %{y}<br>"
                f"{metric_label}: %{{x:,.0f}}<br>"
                "Drop-off: %{customdata}%<extra></extra>"
            ),
            customdata=dropoff,
        )
    )

    # ── Drop-off connectors (arrows with text) ─────────────────────────
    for i in range(1, len(steps)):
        if dropoff[i] != 0:
            mid_y = i - 0.5  # Position between bars
            max_x = max(counts)
            fig.add_annotation(
                x=max_x * 0.5,
                y=mid_y,
                text=f"{dropoff[i]:+.1f}%",
                showarrow=False,
                font=dict(color="#f87171", size=11),
                bgcolor="rgba(0,0,0,0.4)",
                borderpad=4,
            )

    title = f"{metric_label} by Page Pattern"
    fig.update_layout(
        title=title,
        xaxis_title=metric_label,
        template=template,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color, size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.1)"),
        yaxis=dict(autorange="reversed"),  # First step at top
    )

    return fig
