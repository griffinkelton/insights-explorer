# 🏷️ Data Quality Scorecard — Detailed Implementation Plan

> **Promoted from:** IDEAS.md — Bonus Enhancement #17
> **Effort:** Medium (2-4 hours) | **Risk:** Low (read-only analytics, no behavior changes)
> **Status:** 🔲 Planned

---

## 🎯 Goal

Add a "Data Quality" card to the data preview section that grades the uploaded dataset on completeness, uniqueness, date coverage, and outlier presence. Like a nutrition label for data — users know at a glance whether their insights are built on solid ground.

---

## 🧠 Why This Matters

Users upload GA4 exports of wildly varying quality. Some have 98% complete data across 2 years. Others have 40% nulls, 3 days of data, and duplicate rows. Gemini answers both with equal confidence unless explicitly told about data limitations.

A quality scorecard:
- Sets expectations: "Your data is 68% complete — insights may be unreliable"
- Prevents false confidence: "Detected 847 duplicate rows (12% of dataset)"
- Guides improvement: "Missing columns: engagement_rate, users"
- Adds trust: Users see the app is rigorous, not just a chat wrapper

---

## 🗂️ Files & Changes

### 1. `utils/data_loader.py` — New Function

```python
from dataclasses import dataclass

from dataclasses import dataclass

@dataclass
class DataQualityReport:
    """Structured data quality assessment."""
    completeness_pct: float       # % of non-null cells
    duplicate_pct: float          # % of duplicate rows
    duplicate_count: int          # absolute duplicate count
    outlier_count: int            # rows with z-score > 3 on any numeric column
    date_range_days: int | None   # days between first and last date
    date_gaps: int                # number of missing days in date range
    column_count: int             # total columns
    missing_columns: list[str]    # expected columns that are absent
    grade: str                    # "A" through "F"
    warnings: list[str]           # human-readable warnings


def assess_data_quality(df: pd.DataFrame, missing_cols: list[str]) -> DataQualityReport:
    """Analyze a DataFrame and produce a quality report card.

    Args:
        df: The uploaded DataFrame
        missing_cols: List of expected-but-missing column names (from validate_columns)

    Returns:
        DataQualityReport with completeness, duplicates, outliers, date coverage
    """
    total_cells = df.size  # rows × cols
    non_null_cells = df.count().sum()
    completeness = (non_null_cells / total_cells * 100) if total_cells > 0 else 0.0

    # Duplicate detection
    duplicate_count = df.duplicated().sum()
    duplicate_pct = (duplicate_count / len(df) * 100) if len(df) > 0 else 0.0

    # Outlier detection (Z-score > 3 on numeric columns)
    outlier_count = 0
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) > 10:
            z_scores = (series - series.mean()) / series.std()
            outlier_count += (z_scores.abs() > 3).sum()

    # Date coverage
    date_cols = [c for c in df.columns if "date" in c.lower()]
    date_range_days = None
    date_gaps = 0
    if date_cols:
        dates = pd.to_datetime(df[date_cols[0]], errors="coerce").dropna()
        if len(dates) >= 2:
            date_range_days = (dates.max() - dates.min()).days
            # Count missing days in the range
            all_days = set(dates.dt.date)
            full_range = set(
                d.date() for d in pd.date_range(dates.min(), dates.max())
            )
            date_gaps = len(full_range - all_days)

    # Grade calculation
    grade, warnings = _calculate_grade(
        completeness, duplicate_pct, outlier_count,
        missing_cols, date_range_days, date_gaps, len(df),
    )

    return DataQualityReport(
        completeness_pct=round(completeness, 1),
        duplicate_pct=round(duplicate_pct, 1),
        duplicate_count=duplicate_count,
        outlier_count=outlier_count,
        date_range_days=date_range_days,
        date_gaps=date_gaps,
        column_count=len(df.columns),
        missing_columns=missing_cols,
        grade=grade,
        warnings=warnings,
    )


def _calculate_grade(
    completeness: float,
    duplicate_pct: float,
    outlier_count: int,
    missing_cols: list[str],
    date_range_days: int | None,
    date_gaps: int,
    row_count: int,
) -> tuple[str, list[str]]:
    """Calculate a letter grade (A-F) and generate warnings."""
    score = 100.0
    warnings = []

    # Completeness penalty
    if completeness < 50:
        score -= 40
        warnings.append(f"Only {completeness:.0f}% of cells have data — major gaps present.")
    elif completeness < 80:
        score -= 20
        warnings.append(f"{completeness:.0f}% data completeness — some gaps present.")
    elif completeness < 95:
        score -= 5
        warnings.append(f"{completeness:.0f}% data completeness — minor gaps.")

    # Duplicate penalty
    if duplicate_pct > 20:
        score -= 30
        warnings.append(f"{duplicate_pct:.0f}% of rows are exact duplicates — data may be corrupted.")
    elif duplicate_pct > 5:
        score -= 15
        warnings.append(f"{duplicate_pct:.0f}% duplicate rows detected.")

    # Outlier penalty
    if outlier_count > 50:
        score -= 15
        warnings.append(f"{outlier_count} statistical outliers found — data may contain errors.")
    elif outlier_count > 10:
        score -= 5
        warnings.append(f"{outlier_count} outliers detected — review before drawing conclusions.")

    # Date coverage penalty
    if date_range_days is not None:
        if date_range_days < 2:
            score -= 20
            warnings.append("Less than 2 days of data — trends are not meaningful.")
        elif date_range_days < 14:
            score -= 5
            warnings.append(f"Only {date_range_days} days of data — limited for trend analysis.")
        if date_gaps > date_range_days * 0.3:
            score -= 10
            warnings.append(f"{date_gaps} missing days in the date range — data is sparse.")

    # Missing columns penalty
    if missing_cols:
        score -= len(missing_cols) * 5
        warnings.append(f"Missing expected columns: {', '.join(missing_cols)}.")

    # Low row count penalty
    if row_count < 20:
        score -= 15
        warnings.append("Very small sample size — conclusions may not be reliable.")

    # Convert score to grade
    grade = (
        "A" if score >= 90 else
        "B" if score >= 75 else
        "C" if score >= 55 else
        "D" if score >= 35 else
        "F"
    )

    return grade, warnings
```

### 2. `app.py` — Scorecard UI

Render the scorecard in the data preview section, between the metrics row and the preview table:

```python
def render_quality_scorecard(report: DataQualityReport) -> None:
    """Render the data quality scorecard as a styled card."""
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
            st.markdown(f"**{report.completeness_pct}%** completeness · "
                       f"{report.column_count} columns · "
                       f"{report.duplicate_count:,} duplicates · "
                       f"{report.outlier_count} outliers")

            if report.date_range_days:
                st.markdown(f"📅 {report.date_range_days} days of data "
                           f"({report.date_gaps} missing days)")

            for warning in report.warnings:
                st.warning(warning, icon="⚠️")

            if not report.warnings:
                st.success("No significant data quality issues detected.", icon="✅")
```

#### Wire it into the data processing flow

In the file processing block (after `st.session_state.stats` is computed):

```python
from utils.data_loader import assess_data_quality

# ... after df, stats are set ...
quality_report = assess_data_quality(df, missing)
st.session_state.quality_report = quality_report
```

In `_render_main()` (or `render_data_preview()` after component refactor):

```python
if st.session_state.get("quality_report"):
    render_quality_scorecard(st.session_state.quality_report)
```

#### Include in the AI summary prompt

Add a data quality section to `build_summary_prompt()`:

```python
prompt += (
    f"\n\nDATA QUALITY:\n"
    f"- Grade: {quality_report.grade}\n"
    f"- Completeness: {quality_report.completeness_pct}%\n"
    f"- Duplicates: {quality_report.duplicate_pct}% of rows\n"
    f"- Outliers: {quality_report.outlier_count}\n"
    f"- Date coverage: {quality_report.date_range_days} days "
    f"({quality_report.date_gaps} gaps)\n"
    f"- Warnings: {'; '.join(quality_report.warnings) if quality_report.warnings else 'None'}\n"
)
```

This tells Gemini about data limitations so it can qualify its answers ("Based on the data, which is 68% complete and has 12% duplicates...").

---

## 🔍 Edge Cases

| Edge Case | Handling |
|---|---|
| **Empty DataFrame** | `assess_data_quality` returns a report with all zeros and grade "F". The scorecard renders with "No data to assess." |
| **No date column at all** | `date_range_days` is `None`, `date_gaps` is 0. Date section is omitted from the scorecard. |
| **No numeric columns** | Outlier detection is skipped. `outlier_count` is 0. No "outliers" section in the warnings. |
| **Constant column (std=0)** | Z-score would be NaN → skip that column (the std check `series.std() > 0` before computing z-scores). Add guard. |
| **All duplicate rows (100%)** | `duplicate_pct` is 100. Grade drops to F. Warning: "All rows are duplicates — data appears to be duplicated." |
| **Single row of data** | Date range is 0 days. Grade penalized heavily. Warning: "Only 1 row of data — cannot assess trends." |
| **Very large dataset (1M+ rows)** | `df.duplicated().sum()` and outlier detection are O(n). For >100k rows, use a sample: `df.sample(min(50000, len(df)))` for quality assessment. |

---

## 🧪 Test Impact

New file `tests/test_data_quality.py`:

```python
class TestAssessDataQuality:
    def test_perfect_data_gets_a(self): ...
    def test_low_completeness_drops_grade(self): ...
    def test_high_duplicates_drops_grade(self): ...
    def test_outliers_drop_grade(self): ...
    def test_short_date_range_drops_grade(self): ...
    def test_missing_columns_drop_grade(self): ...
    def test_empty_dataframe_returns_f(self): ...
    def test_single_row_handled(self): ...

class TestDataQualityReport:
    def test_report_has_all_fields(self): ...
    def test_grade_mapping_all_ranges(self): ...
```

~10 new tests.

Update `test_data_loader.py` if `assess_data_quality` is added to `data_loader.py`.

---

## 📐 Implementation Order

1. Add `DataQualityReport` dataclass + `assess_data_quality()` to `utils/data_loader.py`
2. Write tests (`tests/test_data_quality.py`) — ~10 tests
3. Add `render_quality_scorecard()` to `app.py`
4. Wire into the data processing flow (compute after file upload / GA4 pull)
5. Add quality section to `build_summary_prompt()` in `utils/prompt_templates.py`
6. Run tests, smoke test, commit

---

## 💭 Why This Matters

A data quality scorecard turns the app from "here's what the AI thinks" into "here's what the AI thinks, and here's how much you should trust it." It's the difference between a toy and a tool. Analysts demand to know: is this data clean? Is the sample large enough? Are there gaps that make trend analysis unreliable?

The letter grade (A-F) is deliberately simple — it communicates instantly. The warnings are specific and actionable ("847 duplicate rows — data may be corrupted"). And feeding quality metadata into the AI prompt means Gemini can say "Based on this data, which has only 14 days of coverage, the trend may not be reliable" — turning a hallucination risk into a trust signal.

---

*Promoted from IDEAS.md Bonus Enhancement #17. Standalone feature — no dependencies on other plans.*
