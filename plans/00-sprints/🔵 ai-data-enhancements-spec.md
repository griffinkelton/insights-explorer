# 🤖 AI & Data Processing Enhancements — Implementation Spec

> **Source plan:** [plans/p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](../p5-p6/🔵 AI_DATA_ENHANCEMENTS.md)
> **Status:** 🔵 Spec'd — awaiting implementation
> **Effort:** 3-4 days | **Risk:** Medium
> **Based on:** 3 rounds of user interviews (2026-07-28), component refactor + theme toggle already complete

---

## 🎯 Goal

Six independent AI and data enhancements that make the app smarter without changing the core architecture. Each is a pure function or a targeted UI addition with its own tests.

---

## 🏗️ Design Decisions (from 3 interview rounds)

| Decision | Choice | Rationale |
|---|---|---|
| Scope | **All 6 sub-items** | Each is independent. Comparative mode (21c) is the largest — do it last. |
| Chart detection | **Combine 21a + 21b into one** | Gemini outputs JSON chart config (`[CHART:{"type":"bar","x":"...","y":"..."}]`). Token format as fallback. User-specified: unified call with a prompt instruction to run a second call if Gemini doesn't send config. |
| Type badges location | **Between metrics + preview** | Row of colored badges visible without clicking anything. Color: date=indigo, numeric=green, categorical=amber, text=gray. |
| Compare mode location | **Above Clear Data** | Grouped with data actions. `_render_compare_controls()` as a standalone function in sidebar.py. |
| Anomaly UI | **Anomaly table** | Collapsible table listing all anomaly dates, values, Z-scores. Red X markers on charts + summary in AI prompt. |
| Sampling scope | **Everywhere** | Replace `head()` in preview table, chat prompts, and summary prompt. Consistent behavior. |
| Chart API design | **Unified call + retry** | One Gemini call with chart config embedded. Prompt instructs Gemini to output config. If missing, second call extracts it from the response. |
| Compare mode UI | **Standalone function** | `_render_compare_controls()` in sidebar.py, called between Clear Data and API counter. |
| Effort estimate | **3-4 days** | 6 items × ~0.5 days each. Compare mode is the bottleneck. |

---

## 📋 Sub-Item Summary

| # | Enhancement | Files | Type | Tests |
|---|---|---|---|---|
| 21d | Column type detection | `utils/data_loader.py`, `components/data_preview.py` | Pure fn + UI badge | ~4 |
| 21f | Smart sampling | `utils/data_loader.py`, `components/data_preview.py`, `utils/prompt_templates.py` | Pure fn | ~3 |
| 21a+b | Chart token + JSON detection | `utils/prompt_templates.py`, `utils/charts.py`, `components/chat.py` | Pure fn + prompt change | ~5 |
| 21e | Anomaly detection | `utils/data_loader.py`, `utils/charts.py`, `components/data_preview.py`, `utils/prompt_templates.py` | Pure fn + UI table + chart markers | ~3 |
| 21c | Comparative mode | `components/sidebar.py`, `utils/prompt_templates.py`, `components/chat.py` | UI + prompt + data flow | ~3 |
| | **Total** | **6 files changed, 0 new files** | | **~18 new tests** |

---

## 📐 Implementation Order

1. **21d: Column Type Detection** — pure function + badges. Easiest, gives quick visual win.
2. **21f: Smart Sampling** — pure function, replaces `head()` everywhere.
3. **21a+b: Chart Token + JSON Detection** — combined chart detection with unified call + retry.
4. **21e: Anomaly Detection** — Z-score math + anomaly table + chart markers.
5. **21c: Comparative Mode** — largest item. UI toggle + data splitting + dual charts. Do last.

---

## 21d: Column Type Detection

### What it does

Scans uploaded DataFrames and classifies each column as: date, numeric metric, categorical dimension, or text. Shows as colored badges between the metrics row and the preview table.

### New function: `detect_column_types()` (`utils/data_loader.py`)

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
        if "date" in col.lower() or "time" in col.lower() or "day" in col.lower():
            types[col] = ColumnType.DATE
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            types[col] = ColumnType.NUMERIC
            continue
        if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            unique_count = df[col].nunique()
            total_count = len(df)
            if unique_count < total_count * 0.2 and unique_count < 100:
                types[col] = ColumnType.CATEGORICAL
            else:
                types[col] = ColumnType.TEXT
            continue
        types[col] = ColumnType.TEXT
    return types
```

### Badge rendering (`components/data_preview.py`)

Add to `render_data_preview()`, between metrics row and the preview table expander:

```python
# ── Column type badges ──
from utils.data_loader import detect_column_types
col_types = detect_column_types(display_df)
badge_css = {
    ColumnType.DATE:       ("col-date",     "📅"),
    ColumnType.NUMERIC:    ("col-numeric",  "🔢"),
    ColumnType.CATEGORICAL:("col-category", "🏷️"),
    ColumnType.TEXT:       ("col-text",     "📝"),
}
badges = " ".join(
    f'<span class="col-badge {badge_css[t][0]}">{badge_css[t][1]} {col}</span>'
    for col, t in col_types.items()
)
st.markdown(f'<div style="margin:0.5rem 0;">{badges}</div>', unsafe_allow_html=True)
```

### Badge CSS (`utils/styles.py` — already consolidated)

```css
.col-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.72rem;
    margin: 0 4px 4px 0;
    font-weight: 600;
}
.col-date { background: rgba(99, 102, 241, 0.12); color: var(--accent-hover); }
.col-numeric { background: rgba(52, 211, 153, 0.12); color: var(--success); }
.col-category { background: rgba(251, 191, 36, 0.12); color: var(--warning); }
.col-text { background: rgba(152, 152, 176, 0.12); color: var(--text-muted); }
```

### Edge Cases

| Case | Handling |
|---|---|
| Column named "update_time" | Matches "time" substring → classified as DATE ✅ |
| All-numeric column with many unique values | Classified as NUMERIC, not CATEGORICAL. The `unique_count < total_count * 0.2` gate prevents misclassification. |
| Empty DataFrame | Return empty dict. Guard in render: `if df is not None and not df.empty`. |

---

## 21f: Smart Sampling

### What it does

Replaces `df.head(10)` everywhere with `smart_sample(df, max_rows=50)` — a function that returns a representative sample. Small datasets return all rows. Large datasets use stratified sampling.

### New function: `smart_sample()` (`utils/data_loader.py`)

```python
def smart_sample(df: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
    """Return a representative sample."""
    n = len(df)
    if n <= max_rows:
        return df
    if n <= 10_000:
        return df.head(max_rows)
    # Large dataset: stratified sampling by date if possible
    date_col = _find_date_column(df)
    if date_col:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["_week"] = df[date_col].dt.to_period("W")
        weeks = max(df["_week"].nunique(), 1)
        sample = df.groupby("_week", group_keys=False).apply(
            lambda g: g.sample(n=min(len(g), max(1, max_rows // weeks)), random_state=42)
        )
        sample = sample.drop(columns=["_week"])
        return sample.head(max_rows)
    return df.sample(n=min(max_rows, n), random_state=42)

def _find_date_column(df: pd.DataFrame) -> str | None:
    """Lightweight date column finder — no dependency on utils.charts."""
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            return col
    return None
```

### Replacement sites

| File | Current | Replace with |
|---|---|---|
| `components/data_preview.py` | `display_df.head(10)` | `smart_sample(display_df, max_rows=10)` |
| `utils/prompt_templates.py` | `df.head(10)` in `build_summary_prompt()` | `smart_sample(df, max_rows=15)` |
| `utils/prompt_templates.py` | `df.head(10)` in `build_chat_prompt()` | `smart_sample(df, max_rows=15)` |

### Edge Cases

| Case | Handling |
|---|---|
| Single date bucket | `groupby` returns one group → normal sampling within it. |
| `random_state=42` | Deterministic sampling — same data, same sample. |
| Very small groups | `min(len(g), max(1, max_rows // weeks))` ensures at least 1 row per group. |

---

## 21a+b: Chart Token + JSON Detection (Combined)

### What it does

Replaces the brittle keyword heuristic in `detect_chart_request()` with Gemini-suggested chart config. Gemini is prompted to output a JSON config block. If missing, a second call extracts the config from the response. Falls back to keyword heuristics as a safety net.

### Prompt addition (`utils/prompt_templates.py`)

Add to `build_chat_prompt()`:

```
After your answer, suggest a chart (if applicable) by appending exactly:
[CHART:{"type":"line","x":"date","y":"sessions","title":"Sessions Over Time"}]
Valid types: line, bar, table. x and y are column names from the data.
If no chart would help, omit this entirely.
```

### Updated `detect_chart_request()` (`utils/prompt_templates.py`)

```python
import json
import re

def detect_chart_request(gemini_response: str) -> dict[str, str] | None:
    """Parse [CHART:{json}] token from Gemini response, with fallbacks."""
    # Try JSON config first
    json_match = re.search(r'\[CHART:(\{.*?\})\]', gemini_response)
    if json_match:
        try:
            config = json.loads(json_match.group(1))
            if "type" in config and "y" in config:
                return {
                    "chart_type": config["type"],
                    "x": config.get("x", ""),
                    "y": config["y"],
                    "title": config.get("title", ""),
                    "method": "gemini_json",
                }
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: keyword heuristics (kept for backward compatibility)
    text = gemini_response.lower()
    if any(p in text for p in ["over time", "trend", "daily", "spike"]):
        return {"chart_type": "line", "reason": "trend", "method": "keyword"}
    if any(p in text for p in ["top 5", "highest", "breakdown", "comparison"]):
        return {"chart_type": "bar", "reason": "ranking", "method": "keyword"}
    return None
```

### Retry logic (`components/chat.py`)

After the main `generate_response_stream()` call, if no chart config was found in the response, make a second lightweight call:

```python
chart_config = detect_chart_request(full_text)
if not chart_config and len(full_text) > 100:
    # Second call: ask Gemini to extract chart config from its own response
    retry_prompt = (
        f"Extract a chart suggestion from this analysis. Output ONLY a JSON block "
        f"like {{\"type\":\"bar\",\"x\":\"page\",\"y\":\"sessions\",\"title\":\"...\"}}. "
        f"If no chart applies, output {{\"type\":\"none\"}}.\n\n"
        f"Analysis:\n{full_text[:2000]}"
    )
    try:
        retry_response = generate_response(retry_prompt)
        chart_config = detect_chart_request(retry_response)
    except Exception:
        pass  # Silent skip — chart is optional
```

### Response cleanup

Strip the chart token from the displayed response:

```python
cleaned_response = re.sub(r'\[CHART:.*?\]', '', full_text).strip()
entry["response"] = cleaned_response
```

### Updated `generate_chart()` call

`generate_chart()` already accepts a `theme` param. For combined chart detection, the JSON config provides `x_col` and `y_col` — the existing `find_column()` already handles the column lookup. No change needed to `generate_chart()`.

---

## 21e: Anomaly Detection

### What it does

Flags dates where a metric deviates >2σ from its 7-day rolling mean. Shows red X markers on charts, an anomaly summary in the AI prompt, and a collapsible anomaly table below the data preview.

### New function: `detect_anomalies()` (`utils/data_loader.py`)

```python
def detect_anomalies(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    window: int = 7,
    threshold_std: float = 2.0,
) -> pd.DataFrame:
    """Flag anomalies using rolling Z-score."""
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")
    result = result.sort_values(date_col)
    result["rolling_mean"] = result[metric_col].rolling(window=window, min_periods=window).mean()
    result["rolling_std"] = result[metric_col].rolling(window=window, min_periods=window).std()
    # Guard against zero std
    result["rolling_std"] = result["rolling_std"].replace(0, float("nan"))
    result["z_score"] = (result[metric_col] - result["rolling_mean"]) / result["rolling_std"]
    result["is_anomaly"] = result["z_score"].abs() > threshold_std
    return result
```

### Anomaly table (`components/data_preview.py`)

Add after the quality scorecard, before filters:

```python
# ── Anomaly detection table ──
if st.session_state.df is not None:
    date_col = find_date_column(st.session_state.df)
    metric_col = find_column(st.session_state.df, ["sessions", "users"])
    if date_col and metric_col:
        anomaly_df = detect_anomalies(st.session_state.df, date_col, metric_col)
        anomalies = anomaly_df[anomaly_df["is_anomaly"]]
        if not anomalies.empty:
            with st.expander(
                f"⚠️ {len(anomalies)} Anomalies Detected ({metric_col})", expanded=False
            ):
                st.dataframe(
                    anomalies[[date_col, metric_col, "z_score"]]
                    .sort_values("z_score", key=abs, ascending=False)
                    .head(20),
                    use_container_width=True,
                )
```

### Anomaly markers on charts (`utils/charts.py`)

Add to `generate_chart()` after the main trace:

```python
# Anomaly markers (if anomaly data available)
anomaly_col = chart_config.get("anomaly_col")
if anomaly_col and date_col:
    anomalies = anomaly_df[anomaly_df["is_anomaly"]]
    if not anomalies.empty:
        fig.add_scatter(
            x=anomalies[date_col], y=anomalies[metric_col],
            mode="markers", marker=dict(color="#f87171", size=10, symbol="x"),
            name="Anomaly",
        )
```

### Anomaly context in AI prompt (`utils/prompt_templates.py`)

```python
# In build_summary_prompt() and build_chat_prompt():
anomaly_df = detect_anomalies(df, date_col, metric_col)
anomalies = anomaly_df[anomaly_df["is_anomaly"]]
if not anomalies.empty:
    anomaly_dates = anomalies[date_col].dt.strftime("%Y-%m-%d").tolist()[:10]
    prompt += f"\n\n⚠️ Anomalies detected on: {', '.join(anomaly_dates)}"
```

### Edge Cases

| Case | Handling |
|---|---|
| Fewer than 7 rows | `min_periods=window` → no values computed. Show "Need ≥7 days for anomaly detection." |
| Zero rolling std (constant values) | Guard: `.replace(0, float("nan"))` → Z-score is NaN → not an anomaly. |
| No date/metric column | Skip anomaly detection entirely. |

---

## 21c: Comparative Mode

### What it does

Users toggle Compare mode in the sidebar, select a dimension + two values, and see side-by-side analysis with dual charts.

### Sidebar: `_render_compare_controls()` (`components/sidebar.py`)

Added to `render_sidebar()` between `_render_clear_button()` and `_render_api_counter()`:

```python
def _render_compare_controls() -> None:
    """Render the Compare mode toggle + dimension/value selectors."""
    if st.session_state.df is None:
        return

    st.divider()
    compare_mode = st.toggle("🔬 Compare Mode", value=False, key="compare_mode")
    st.session_state.compare_mode = compare_mode

    if compare_mode:
        from utils.data_loader import detect_column_types
        from utils.data_loader import ColumnType

        col_types = detect_column_types(st.session_state.df)
        categorical_cols = [
            c for c, t in col_types.items()
            if t in (ColumnType.CATEGORICAL, ColumnType.TEXT)
        ]
        if categorical_cols:
            dimension = st.selectbox(
                "Split by", categorical_cols, key="compare_dimension"
            )
            unique_vals = sorted(st.session_state.df[dimension].dropna().unique().tolist())
            if len(unique_vals) >= 2:
                val_a = st.selectbox("Value A", unique_vals, key="compare_val_a")
                val_b = st.selectbox(
                    "Value B",
                    [v for v in unique_vals if v != val_a],
                    key="compare_val_b",
                )
```

### Data splitting + prompt (`utils/prompt_templates.py`)

```python
def build_comparison_prompt(
    question: str, df_a: pd.DataFrame, df_b: pd.DataFrame,
    label_a: str, label_b: str, stats: dict,
) -> str:
    """Build a comparison prompt for side-by-side analysis."""
    return (
        f"Compare {label_a} vs {label_b} for: {question}\n\n"
        f"{label_a} ({len(df_a)} rows):\n{smart_sample(df_a, max_rows=10).to_string()}\n\n"
        f"{label_b} ({len(df_b)} rows):\n{smart_sample(df_b, max_rows=10).to_string()}\n\n"
        f"Provide a comparison with specific numbers and percentages."
    )
```

### Dual chart rendering (`components/chat.py`)

When compare mode is active, render side-by-side charts:

```python
if st.session_state.get("compare_mode"):
    df_a = st.session_state.df[st.session_state.df[dimension] == val_a]
    df_b = st.session_state.df[st.session_state.df[dimension] == val_b]
    col_a, col_b = st.columns(2)
    with col_a:
        fig_a = generate_chart(df_a, chart_config, "", "", theme=theme)
        if fig_a:
            st.plotly_chart(fig_a["fig"], use_container_width=True, key=f"comp_a_{i}_{theme}")
    with col_b:
        fig_b = generate_chart(df_b, chart_config, "", "", theme=theme)
        if fig_b:
            st.plotly_chart(fig_b["fig"], use_container_width=True, key=f"comp_b_{i}_{theme}")
```

### Edge Cases

| Case | Handling |
|---|---|
| One split is empty | Show warning and render only the non-empty side. |
| <2 unique values | Hide the compare controls. Show "Need ≥2 unique values in the selected dimension." |
| Dimension is date-like | Skip — dates aren't meaningful for categorical comparison. Only categorical and text columns. |

---

## 🧪 Test Impact

| Module | New Tests | Type |
|---|---|---|
| `test_data_loader.py` | ~7 | `detect_column_types` (4), `smart_sample` (3), `detect_anomalies` (3) |
| `test_prompt_templates.py` | ~8 | `detect_chart_request` JSON + fallback (5), `build_comparison_prompt` (3) |
| `test_sidebar.py` | ~1 | `_render_compare_controls` exists |
| `test_charts.py` | ~2 | Anomaly markers on charts |
| **Total new** | **~18** | |

**Post-enhancements expected: 231 → ~249 tests.**

---

## 🚫 Out of Scope

- Multi-way comparison (3+ values) — v2 feature
- Date-based comparison ranges (`st.date_input` for date dimensions)
- Anomaly alerts/notifications
- Auto-suggesting comparison dimensions

---

*Spec derived from 3 interview rounds (2026-07-28), the original [p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](../p5-p6/🔵 AI_DATA_ENHANCEMENTS.md), and the post-refactor component structure.*
