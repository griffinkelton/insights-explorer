"""Metric forecasting — linear regression trend projection with prediction intervals."""

from dataclasses import dataclass
import numpy as np
import pandas as pd

from utils.caching import memoize_fingerprint

# Schema version for cached forecast output structure.
# Bump when ForecastResult fields or calculation logic change to invalidate
# the memoized fingerprint cache on forecast_metric(). Wired as a hidden
# default parameter.
FORECAST_SCHEMA_VERSION = "1.0.0"


@dataclass
class ForecastResult:
    """Structured forecast output for rendering and AI narrative generation."""

    daily: pd.DataFrame  # columns: [date, actual]
    forecast_df: pd.DataFrame  # columns: [date, predicted, lower_bound, upper_bound]
    metric_col: str
    periods: int
    trend_direction: str  # "upward" or "downward"
    trend_strength: float  # R² value (0-1)
    last_value: float
    final_forecast: float
    pct_change: float  # percentage change from last actual to final forecast
    confidence: str  # "strong", "moderate", "weak"


@memoize_fingerprint()
def forecast_metric(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    periods: int = 30,
    _schema_version: str = FORECAST_SCHEMA_VERSION,
) -> ForecastResult | None:
    """Produce a linear regression forecast with 95% prediction intervals.

    Aggregates the metric by date (sum), fits a linear trend, and projects
    forward by `periods` days. Returns None if there's insufficient data.

    Args:
        df: Source DataFrame (never mutated).
        date_col: Name of the date column.
        metric_col: Name of the numeric metric column (e.g. "sessions").
        periods: Number of future days to forecast.

    Returns:
        ForecastResult with daily actuals, forecast, intervals, and metadata.
    """
    if periods <= 0:
        return None
    if df is None or df.empty or date_col not in df.columns or metric_col not in df.columns:
        return None

    # ── Aggregate daily metric ────────────────────────────────────────────
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
    # Convert metric to numeric before aggregation
    df_copy[metric_col] = pd.to_numeric(df_copy[metric_col], errors="coerce")
    # Drop rows with invalid dates or non-numeric metrics BEFORE aggregation
    df_copy = df_copy.dropna(subset=[date_col, metric_col])
    daily = df_copy.groupby(date_col)[metric_col].sum().reset_index().sort_values(date_col)

    # Reindex to complete daily calendar (fill missing days with 0)
    if len(daily) >= 2:
        full_date_range = pd.date_range(
            start=daily[date_col].min(), end=daily[date_col].max(), freq="D"
        )
        daily = daily.set_index(date_col).reindex(full_date_range, fill_value=0).reset_index()
        daily = daily.rename(columns={"index": date_col})

    n = len(daily)
    if n < 7:
        return None  # Need at least a week of data for a meaningful forecast

    # ── Linear regression ─────────────────────────────────────────────────
    # Use elapsed days as x-values for correct time spacing
    dates = pd.to_datetime(daily[date_col])
    x = (dates - dates.min()).dt.days.values.astype(float)
    y = daily[metric_col].values.astype(float)
    coeffs = np.polyfit(x, y, 1)  # [slope, intercept]
    predicted = np.polyval(coeffs, x)

    # R²
    residuals = y - predicted
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Standard error of regression
    std_err = float(np.sqrt(ss_res / max(n - 2, 1)))

    # ── Prediction intervals ──────────────────────────────────────────────
    x_mean = np.mean(x)
    ssx = np.sum((x - x_mean) ** 2)
    # Approximate t-critical for 95% CI: ~2.0 for n>=60, slightly wider for smaller n
    t_crit = 2.0 if n >= 60 else 2.0 + 10.0 / n

    # ── Forecast future periods ───────────────────────────────────────────
    x_future = np.arange(x[-1] + 1, x[-1] + periods + 1, dtype=float)
    y_future = np.polyval(coeffs, x_future)

    # Standard error widens with distance from mean
    se_pred_future = std_err * np.sqrt(1 + 1 / n + (x_future - x_mean) ** 2 / ssx)
    lower_future = y_future - t_crit * se_pred_future
    upper_future = y_future + t_crit * se_pred_future
    # Clamp lower bound to >= 0 (negative sessions don't make sense)
    lower_future = np.maximum(lower_future, 0)

    # ── Future dates ──────────────────────────────────────────────────────
    last_date = pd.Timestamp(dates.iloc[-1])
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods)

    forecast_df = pd.DataFrame(
        {
            "date": future_dates,
            "predicted": y_future.round(1),
            "lower_bound": lower_future.round(1),
            "upper_bound": upper_future.round(1),
        }
    )

    # ── Metadata ──────────────────────────────────────────────────────────
    slope = float(coeffs[0])
    trend_direction = "upward" if slope > 0 else "downward" if slope < 0 else "stable"
    last_value = float(y[-1])
    final_forecast = float(y_future[-1])
    pct_change = float(((final_forecast - last_value) / last_value * 100) if last_value != 0 else 0)

    confidence = "strong" if r_squared > 0.7 else "moderate" if r_squared > 0.4 else "weak"

    return ForecastResult(
        daily=daily,
        forecast_df=forecast_df,
        metric_col=metric_col,
        periods=periods,
        trend_direction=trend_direction,
        trend_strength=round(r_squared, 3),
        last_value=last_value,
        final_forecast=final_forecast,
        pct_change=round(pct_change, 1),
        confidence=confidence,
    )


def build_forecast_summary(result: ForecastResult) -> str:
    """Build a machine-generated summary of the forecast (no Gemini call).

    Used as a fallback when Gemini is unavailable or as a starting point
    for the AI narrative. Returns 2-3 sentences.
    """
    direction_word = (
        "increase"
        if result.trend_direction == "upward"
        else "decline" if result.trend_direction == "downward" else "remain broadly stable"
    )
    return (
        f"Based on the historical trend, **{result.metric_col}** is projected to "
        f"{direction_word} from **{result.last_value:,.0f}** to approximately "
        f"**{result.final_forecast:,.0f}** over the next {result.periods} days "
        f"({result.pct_change:+.1f}%). "
        f"Confidence in this trend is **{result.confidence}** "
        f"(R² = {result.trend_strength})."
    )


def build_forecast_prompt(result: ForecastResult) -> str:
    """Build a prompt for Gemini to generate a forecast narrative.

    Includes the statistical summary and asks Gemini to produce a natural
    language interpretation with caveats.
    """
    actual_head = result.daily.tail(5).to_string(index=False)
    forecast_head = result.forecast_df.head(5).to_string(index=False)
    forecast_tail = result.forecast_df.tail(3).to_string(index=False)

    return (
        f"You are a data analyst. Write a concise forecast narrative (3-5 sentences) "
        f"based on the following statistical trend analysis:\n\n"
        f"TREND ANALYSIS:\n"
        f"- Metric: {result.metric_col}\n"
        f"- Trend direction: {result.trend_direction}\n"
        f"- R² (goodness of fit, 0-1): {result.trend_strength}\n"
        f"- Confidence: {result.confidence}\n"
        f"- Last actual value: {result.last_value:,.0f}\n"
        f"- Forecast for day {result.periods}: {result.final_forecast:,.0f}\n"
        f"- Projected change: {result.pct_change:+.1f}% over {result.periods} days\n\n"
        f"LAST 5 ACTUAL DAYS:\n{actual_head}\n\n"
        f"FIRST 5 FORECAST DAYS:\n{forecast_head}\n\n"
        f"LAST 3 FORECAST DAYS:\n{forecast_tail}\n\n"
        f"Write a 3-5 sentence narrative. Include the projected value at day "
        f"{result.periods}, the percentage change, trend direction, and at least "
        f"one important caveat (R², data limitations, seasonality not modeled, etc.). "
        f"Keep it professional but accessible."
    )
