# 🤖 AI & Data Processing Enhancements — Phase 5 Implementation Plan

> **Roadmap ref:** IMPLEMENTATION_PLAN.md #21, ENHANCEMENTS.md #20, #22, #23, #25, #26, #27
> **Effort:** Medium-High (varies per sub-item) | **Status:** 🔲 Planned — no code written
>
> This file covers 6 sub-items. Each is a standalone enhancement with its own plan.

---

## Sub-Item Map

| # | Enhancement | ENHANCEMENTS.md | Effort | Why |
|---|---|---|---|---|
| 21a | Structured chart detection via Gemini | #20 | Medium | Replace brittle keyword matching with LLM-decided tokens |
| 21b | Gemini-suggested chart mapping | #23 | Medium | Let Gemini output JSON chart config, parse with `json.loads` |
| 21c | Comparative analysis mode | #22 | High | "Q2 vs Q1" or "organic vs paid" — dual-panel analysis |
| 21d | Automatic column type detection | #25 | Medium | Detect date-like, numeric, and categorical columns automatically |
| 21e | Statistical anomaly detection | #26 | Medium | Rolling Z-score to flag 2σ+ deviations |
| 21f | Intelligent sampling for large datasets | #27 | Small | Stratified sampling instead of `df.head(10)` for >10k rows |

---

## 21a: Structured Chart Detection via Gemini

### 🎯 Goal
Replace the current `detect_chart_request()` keyword heuristic (which misses ~40% of chart-able responses) with a Gemini-driven approach. The LLM appends a structured token like `[CHART:line:sessions_over_time]` to its response when a chart would help.

### 🧠 Approach

#### Modified prompt instruction (in `build_chat_prompt()`):
```
If the answer would benefit from a chart, append exactly one of these tokens
at the very end of your response on its own line:
- [CHART:line:<metric_name>] for time-series or trend data
- [CHART:bar:<dimension_name>] for rankings or comparisons
- [CHART:table] for tabular data better shown as a table
If no chart is applicable, do not include any token.
```

#### Updated `detect_chart_request()`:
```python
import re

def detect_chart_request(gemini_response: str) -> dict[str, str] | None:
    """Parse [CHART:...] tokens from Gemini responses."""
    match = re.search(r'\[CHART:(line|bar|table):?(\w+)?\]', gemini_response)
    if match:
        chart_type = match.group(1)
        target = match.group(2) or ""
        return {"chart_type": chart_type, "reason": target, "method": "gemini"}
    
    # Fallback to keyword heuristics for backward compatibility
    # (existing keyword scanning logic)
```

#### Response cleanup:
Strip the token from the displayed response so users don't see it:
```python
cleaned_response = re.sub(r'\[CHART:(line|bar|table):?\w*\]', '', gemini_response).strip()
```

### 🔍 Edge Cases
- **Gemini doesn't include a token:** Fallback to keyword heuristics (keep the existing logic as a safety net)
- **Gemini includes a malformed token:** `[CHART:pie:sessions]` — pie is invalid. Regex only matches `line|bar|table`. Falls back to keywords.
- **Token appears mid-response:** Regex finds it anywhere in the text. Tokens at the end are more likely to be intentional, but anywhere is fine.
- **Multiple tokens:** Only the first match is used. The prompt instruction says "exactly one."

### 🧪 Test Impact
Add to `test_prompt_templates.py`:
- `test_detect_chart_request_parses_gemini_token`
- `test_detect_chart_request_falls_back_to_keywords`
- `test_cleaned_response_strips_chart_token`

---

## 21b: Gemini-Suggested Chart Mapping

### 🎯 Goal
Instead of hardcoding which columns to chart (always `sessions` over `page_path`), ask Gemini to output a JSON chart config that maps any column to any visualization.

### 🧠 Approach

#### Prompt addition:
```
After answering, suggest a chart by outputting a JSON block:
```json
{"chart_type": "bar", "x": "device_category", "y": "users", "title": "Users by Device"}
```
Choose from chart types: line, bar, scatter, table.
```

#### Parse the JSON:
```python
import json
import re

def detect_chart_from_json(gemini_response: str) -> dict | None:
    """Extract a JSON chart config from Gemini's response."""
    match = re.search(r'```json\s*(.*?)\s*```', gemini_response, re.DOTALL)
    if not match:
        return None
    
    try:
        config = json.loads(match.group(1))
        # Validate required fields
        if "chart_type" not in config or "y" not in config:
            return None
        return config
    except (json.JSONDecodeError, KeyError):
        return None
```

#### Dynamic chart generation:
```python
def generate_chart_from_config(df: pd.DataFrame, config: dict) -> go.Figure | None:
    """Generate a Plotly chart from a JSON config."""
    chart_type = config["chart_type"]
    x_col = find_column(df, [config.get("x", "")])
    y_col = find_column(df, [config["y"]])
    
    if not y_col:
        return None
    
    if chart_type == "bar":
        if x_col:
            data = df.groupby(x_col)[y_col].sum().nlargest(10).reset_index()
            return px.bar(data, x=y_col, y=x_col, orientation="h", title=config.get("title", ""))
        else:
            return px.bar(df, y=y_col, title=config.get("title", ""))
    
    elif chart_type == "line":
        date_col = find_date_column(df)
        if date_col:
            data = df.groupby(date_col)[y_col].sum().reset_index()
            return px.line(data, x=date_col, y=y_col, title=config.get("title", ""))
    
    elif chart_type == "table":
        return None  # Tables are rendered natively in Streamlit, not with Plotly
    
    return None
```

### 🔍 Edge Cases
- **Column doesn't exist:** `find_column` returns `None` → skip chart. Gemini might hallucinate a column name that doesn't exist in the DataFrame.
- **Invalid JSON:** Malformed JSON block → `json.JSONDecodeError` caught, returns `None`.
- **No JSON block:** Returns `None` → no chart rendered (silent skip, per the original spec).

### 🧪 Test Impact
Add to `test_prompt_templates.py`:
- `test_detect_chart_from_json_valid_config`
- `test_detect_chart_from_json_malformed`
- `test_detect_chart_from_json_missing_block`

---

## 21c: Comparative Analysis Mode

### 🎯 Goal
Add a "Compare" mode. Users ask "Compare Q2 vs Q1" or "organic vs paid traffic." The app splits data, runs parallel Gemini prompts, and renders dual-panel charts.

### 🧠 Approach

#### UI: "Compare" toggle in sidebar
```python
compare_mode = st.toggle("🔬 Compare Mode", value=False, key="compare_mode")

if compare_mode:
    dimension = st.selectbox("Split by", categorical_columns, key="compare_dimension")
    value_a = st.selectbox("Value A", unique_values, key="compare_value_a")
    value_b = st.selectbox("Value B", unique_values, key="compare_value_b")
```

#### Data splitting:
```python
def split_for_comparison(df, dimension, value_a, value_b):
    df_a = df[df[dimension] == value_a]
    df_b = df[df[dimension] == value_b]
    return df_a, df_b
```

#### Prompt construction:
```python
def build_comparison_prompt(question, df_a, df_b, label_a, label_b, stats_a, stats_b):
    return f"""
    Compare {label_a} vs {label_b} for the question: {question}
    
    {label_a} data ({stats_a['row_count']} rows): {df_a.head(5).to_string()}
    {label_b} data ({stats_b['row_count']} rows): {df_b.head(5).to_string()}
    
    Provide a comparison with specific numbers and percentages.
    """
```

#### Chart rendering:
Side-by-side charts using `st.columns(2)`:
```python
col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(fig_a, use_container_width=True, key="compare_a")
with col_b:
    st.plotly_chart(fig_b, use_container_width=True, key="compare_b")
```

### 🔍 Edge Cases
- **One split is empty:** Show warning "No data for {value_b}" and render only the non-empty chart.
- **Dimension is date:** Use `st.date_input` for ranges instead of `st.selectbox`.
- **>2 values selected:** Start with 2. Multi-way comparison (3+ values) is a v2 feature.

### 🧪 Test Impact
Add to `test_prompt_templates.py`:
- `test_build_comparison_prompt`
- `test_split_for_comparison`
- `test_split_for_comparison_empty_b`

---

## 21d: Automatic Column Type Detection

### 🎯 Goal
Scan uploaded DataFrames and classify each column as: date, numeric metric, categorical dimension, or text. Show as badges in the data preview and use for smarter chart generation.

### 🧠 Approach

```python
from enum import Enum

class ColumnType(Enum):
    DATE = "date"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"

def detect_column_types(df: pd.DataFrame) -> dict[str, ColumnType]:
    """Classify each column. Returns {column_name: ColumnType}."""
    types = {}
    
    for col in df.columns:
        # Check for date columns
        if "date" in col.lower() or "time" in col.lower() or "day" in col.lower():
            types[col] = ColumnType.DATE
            continue
        
        if pd.api.types.is_numeric_dtype(df[col]):
            types[col] = ColumnType.NUMERIC
            continue
        
        if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            unique_count = df[col].nunique()
            total_count = len(df)
            # If <20% unique values, it's probably a category, not free text
            if unique_count < total_count * 0.2 and unique_count < 100:
                types[col] = ColumnType.CATEGORICAL
            else:
                types[col] = ColumnType.TEXT
            continue
        
        # Fallback
        types[col] = ColumnType.TEXT
    
    return types
```

#### Display in UI:
```python
types = detect_column_types(df)
badge_html = " ".join(
    f'<span class="col-badge col-{t.value}">{col}</span>'
    for col, t in types.items()
)
st.markdown(f'<div style="margin:0.5rem 0;">{badge_html}</div>', unsafe_allow_html=True)
```

With CSS badges:
```css
.col-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    margin: 0 4px 4px 0;
}
.col-date { background: rgba(129, 140, 248, 0.15); color: #818cf8; }
.col-numeric { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.col-categorical { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.col-text { background: rgba(152, 152, 176, 0.15); color: #9898b0; }
```

### 🧪 Test Impact
Add to `test_data_loader.py`:
- `test_detect_column_types_date`
- `test_detect_column_types_numeric`
- `test_detect_column_types_categorical`
- `test_detect_column_types_text`

---

## 21e: Statistical Anomaly Detection

### 🎯 Goal
Flag dates where a metric deviates more than 2 standard deviations from its 7-day rolling mean. Show red markers on charts and surface anomalies in the AI summary.

### 🧠 Approach

```python
def detect_anomalies(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    window: int = 7,
    threshold_std: float = 2.0,
) -> pd.DataFrame:
    """Flag anomalies using rolling Z-score.
    
    Returns a DataFrame with the same rows as df, plus:
    - rolling_mean: 7-day rolling mean
    - rolling_std: 7-day rolling std
    - z_score: (value - mean) / std
    - is_anomaly: True if |z_score| > threshold
    """
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col])
    result = result.sort_values(date_col)
    
    result["rolling_mean"] = result[metric_col].rolling(window=window, min_periods=window).mean()
    result["rolling_std"] = result[metric_col].rolling(window=window, min_periods=window).std()
    result["z_score"] = (result[metric_col] - result["rolling_mean"]) / result["rolling_std"]
    result["is_anomaly"] = result["z_score"].abs() > threshold_std
    
    return result
```

#### Anomaly markers on Plotly charts:
```python
anomalies = data[data["is_anomaly"]]

fig = px.line(data, x=date_col, y=metric_col, ...)
fig.add_scatter(
    x=anomalies[date_col],
    y=anomalies[metric_col],
    mode="markers",
    marker=dict(color="red", size=10, symbol="x"),
    name="Anomaly",
)
```

#### Anomaly summary in AI prompt:
```python
anomaly_dates = anomalies[date_col].dt.strftime("%Y-%m-%d").tolist()
if anomaly_dates:
    anomaly_text = f"⚠️ Anomalies detected on: {', '.join(anomaly_dates[:10])}"
    prompt += f"\n\n{anomaly_text}"
```

### 🔍 Edge Cases
- **Fewer than 7 rows:** `min_periods=window` means no values computed for first 7 days. Result: empty anomaly set. Show a warning: "Need at least 7 days of data for anomaly detection."
- **Constant values (std=0):** Z-score would be infinite. Guard: if `rolling_std == 0`, set `z_score = 0` (no anomaly).
- **Non-numeric metric column:** `detect_anomalies` should validate that `metric_col` is numeric before computing.

### 🧪 Test Impact
Add to `test_data_loader.py`:
- `test_detect_anomalies_flags_spike`
- `test_detect_anomalies_no_anomalies_in_flat_data`
- `test_detect_anomalies_insufficient_data`

---

## 21f: Intelligent Sampling for Large Datasets

### 🎯 Goal
The current approach sends `df.head(10)` to Gemini in every prompt. For 1M-row datasets, this is fine but misses data diversity. For 10k rows, it's wasteful (we could include more). Apply stratified sampling: for large datasets, sample proportionally across date ranges; for small datasets, include all rows.

### 🧠 Approach

```python
def smart_sample(df: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
    """Return a representative sample of the DataFrame.
    
    - If len(df) <= max_rows: return all rows
    - If len(df) <= 10k: return head(max_rows)
    - If len(df) > 10k: stratified sample preserving date distribution
    """
    n = len(df)
    
    if n <= max_rows:
        return df
    
    if n <= 10_000:
        return df.head(max_rows)
    
    # Large dataset: stratified sampling
    date_col = find_date_column(df)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        
        # Create date buckets (weekly)
        df["_week"] = df[date_col].dt.to_period("W")
        weeks = df["_week"].nunique()
        
        # Allocate rows per week proportionally
        sample = df.groupby("_week", group_keys=False).apply(
            lambda g: g.sample(n=min(len(g), max(1, max_rows // weeks)), random_state=42)
        )
        sample = sample.drop(columns=["_week"])
        return sample.head(max_rows)
    
    # No date column: random sample
    return df.sample(n=min(max_rows, n), random_state=42)
```

#### Use in prompt construction:
Replace:
```python
sample = df.head(10)
```
With:
```python
sample = smart_sample(df, max_rows=15)
```

### 🔍 Edge Cases
- **All rows in one date bucket:** `groupby` returns a single group → normal sampling within that group.
- **Very small groups:** `min(len(g), max(1, max_rows // weeks))` ensures at least 1 row per group, even if `max_rows // weeks` is < 1.
- **`random_state=42`:** Deterministic sampling — same data, same sample. Good for reproducibility.

### 🧪 Test Impact
Add to `test_prompt_templates.py`:
- `test_smart_sample_small_dataset_returns_all`
- `test_smart_sample_medium_dataset_returns_head`
- `test_smart_sample_large_dataset_stratified`

---

## 📐 Implementation Order

These six sub-items are independent. Recommended order:

1. **21d (Type Detection)** — easiest, pure function, lots of test coverage. Gets you familiar with the enhancement flow.
2. **21f (Smart Sampling)** — another pure function, small scope. Makes prompts better immediately.
3. **21a (Chart Token Detection)** — replaces keyword heuristics. The fallback to keywords keeps backward compatibility.
4. **21b (JSON Chart Mapping)** — builds on 21a. More sophisticated but optional.
5. **21e (Anomaly Detection)** — mathematical, but well-scoped. The Z-score approach is textbook.
6. **21c (Comparative Mode)** — largest scope. Touches UI, data flow, prompts, and charts. Do it last.

Each sub-item should be implemented, tested, committed, and pushed independently. They don't depend on each other.

---

*Plan created from review of `utils/prompt_templates.py` (detect_chart_request, build_chat_prompt), `utils/data_loader.py` (get_dataset_stats), and `app.py` (chart generation pipeline).*
