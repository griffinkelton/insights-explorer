"""Chart generation helpers — extracted from app.py."""

from typing import Any
import pandas as pd
import plotly.express as px


def generate_chart(
    df: pd.DataFrame,
    chart_config: dict[str, str],
    gemini_response: str,
    user_question: str,
) -> dict[str, Any] | None:
    """Generate a Plotly chart based on detected chart config.

    Returns {"fig": go.Figure, "type": "line"|"bar"} or None.
    """
    chart_type = chart_config.get("chart_type", "bar")
    try:
        date_col = find_date_column(df)

        if chart_type == "line" and date_col:
            sessions_col = find_column(df, ["sessions"])
            if sessions_col:
                daily = df.groupby(date_col)[sessions_col].sum().reset_index().sort_values(date_col)
                fig = px.line(
                    daily, x=date_col, y=sessions_col,
                    title="Sessions Over Time", markers=True,
                    template="plotly_dark",
                    color_discrete_sequence=["#818cf8"],
                )
                fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
                fig.update_layout(
                    xaxis_title="Date", yaxis_title="Sessions",
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9898b0", size=12),
                    margin=dict(l=20, r=20, t=40, b=20),
                    hovermode="x unified",
                )
                return {"fig": fig, "type": "line"}

        if chart_type in ("bar", "ranking"):
            page_col = find_column(df, ["page_path", "page", "path", "url", "landing_page"])
            sessions_col = find_column(df, ["sessions"])
            if page_col and sessions_col:
                top = df.groupby(page_col)[sessions_col].sum().nlargest(10).reset_index()
                fig = px.bar(
                    top, x=sessions_col, y=page_col, orientation="h",
                    title=f"Top Pages by {sessions_col.replace('_', ' ').title()}",
                    template="plotly_dark",
                    color_discrete_sequence=["#818cf8"],
                    text_auto=".1s",
                )
                fig.update_traces(textposition="outside", textfont=dict(color="#9898b0", size=11))
                fig.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9898b0", size=12),
                    margin=dict(l=20, r=40, t=40, b=20),
                )
                return {"fig": fig, "type": "bar"}

        # Fallback
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        if numeric_cols and categorical_cols:
            cat_col, num_col = categorical_cols[0], numeric_cols[0]
            agg = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()
            fig = px.bar(
                agg, x=num_col, y=cat_col, orientation="h",
                title=f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                template="plotly_dark",
                color_discrete_sequence=["#818cf8"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9898b0", size=12),
            )
            return {"fig": fig, "type": "bar"}
    except Exception:
        pass
    return None


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Case-insensitive column lookup by candidate names."""
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in candidates:
        key = candidate.lower().strip()
        if key in df_cols_lower:
            return df_cols_lower[key]
    return None


def find_date_column(df: pd.DataFrame) -> str | None:
    """Find the best date column in the DataFrame."""
    date_candidates = ["date", "day", "date_time", "timestamp"]
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for candidate in date_candidates:
        if candidate in df_cols_lower:
            return df_cols_lower[candidate]
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None
