"""Prompt construction for Gemini interactions."""

import pandas as pd


def build_summary_prompt(df: pd.DataFrame, stats: dict) -> str:
    """Build a prompt asking Gemini to generate a plain-language data summary."""

    missing = stats.get("missing_columns", [])
    date_info = ""
    if stats.get("date_range_start"):
        date_info = (
            f"Date range: {stats['date_range_start']} to {stats['date_range_end']}."
        )

    # Sample the first few rows for context (compact representation)
    sample_rows = df.head(5).to_string(index=False)

    prompt = f"""You are a data analyst assistant. Summarize the following GA4 dataset in plain language.

Dataset info:
- Row count: {stats['row_count']}
- Columns: {', '.join(stats['columns'])}
- {date_info}

Missing expected columns (not a problem, just FYI): {', '.join(missing) if missing else 'None'}

Sample rows:
{sample_rows}

Please provide:
1. A brief overview of what the data covers (date range, volume)
2. Top pages by sessions (if sessions column exists)
3. Any obvious anomalies (sudden drops, spikes, outliers)
4. Data quality notes (missing values, small sample sizes, etc.)

Keep it concise — about 3-5 bullet points. Flag any data limitations explicitly.
"""
    return prompt


def build_chat_prompt(
    user_question: str,
    df: pd.DataFrame,
    stats: dict,
) -> str:
    """Build a prompt for a user question about the uploaded data.

    Includes a compact data representation (aggregate stats + sample)
    rather than the full raw dataset, to keep the prompt size manageable.
    """

    # Build a compact numeric summary of key columns
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    agg_stats = {}
    if numeric_cols:
        try:
            desc = df[numeric_cols].describe().to_string()
            agg_stats["numeric_summary"] = desc
        except Exception:
            pass

    # Top 10 rows (or fewer if the dataset is small)
    sample_size = min(10, len(df))
    sample = df.head(sample_size).to_string(index=False)

    # Column list
    columns_str = ", ".join(df.columns.tolist())

    date_info = ""
    if stats.get("date_range_start"):
        date_info = (
            f"Date range: {stats['date_range_start']} to {stats['date_range_end']}."
        )

    prompt = f"""You are a helpful data analyst assistant. Answer the user's question about their GA4 data concisely and accurately.

DATA CONTEXT:
- Total rows: {stats['row_count']}
- Columns: {columns_str}
- {date_info}

NUMERIC COLUMN STATISTICS:
{agg_stats.get('numeric_summary', 'No numeric columns available.')}

SAMPLE DATA (first {sample_size} rows):
{sample}

USER QUESTION:
{user_question}

INSTRUCTIONS:
- Answer the question using only the data provided above.
- Be concise and direct.
- If the data doesn't contain enough information to fully answer the question, explicitly flag that limitation.
- If the sample size is small, mention that conclusions may not be statistically significant.
- Suggest a follow-up question the user might find helpful.
"""
    return prompt


def detect_chart_request(gemini_response: str) -> dict | None:
    """Heuristically detect if a Gemini response suggests a chart-able metric.

    Returns a dict with chart config if detected, or None.
    Looks for keywords suggesting: time-series trends, top-N comparisons,
    metric breakdowns, or explicit comparisons.
    """
    text_lower = gemini_response.lower()

    # Time-series / trend indicators
    time_phrases = [
        "over time", "trend", "over the period", "day", "week", "month",
        "per day", "daily", "by date", "timeline", "increase", "decrease",
        "growing", "declining", "spike", "drop", "sessions over",
    ]
    if any(phrase in text_lower for phrase in time_phrases):
        return {"chart_type": "line", "reason": "trend"}

    # Ranking / comparison indicators
    rank_phrases = [
        "top 5", "top 10", "top", "highest", "lowest", "most", "least",
        "ranking", "ranked", "top pages", "breakdown", "compare",
        "comparison", "across", "distribution", "by page", "by source",
        "by channel", "by device",
    ]
    if any(phrase in text_lower for phrase in rank_phrases):
        return {"chart_type": "bar", "reason": "ranking"}

    return None
