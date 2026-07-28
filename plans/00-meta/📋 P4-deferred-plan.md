# 📋 P4+ Deferred Items — Future Batches

> **What:** Everything deferred from the [P4 Wave 1 + Streaming sprint spec](✅ P4-wave1-streaming-sprint-spec.md).
> **Status:** 🔵 Captured — awaiting P4 Wave 1 + Streaming completion before execution.
> **Based on:** [P4 future plan](📋 P4-future-plan.md), user interview (3 rounds) + follow-up analysis (4 rounds), July 28, 2026.
> **Predecessor:** [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md) must be complete and stable first.
> **Already deferred elsewhere:** #8 Onboarding tour → [Onboarding tour](🔵 onboarding-tour.md)

---

## 🧭 What This Covers

| Batch | Item(s) | What | Effort | Why deferred |
|---|---|---|---|---|
| **Batch C** | #18/P3 | Light/dark theme toggle | 3-5 days | CSS-only — do after streaming stable per 📋 UNIFIED_PLAN.md order |
| **Batch D** | #20/P5 | Component refactor | 3-5 days | Mechanical extraction — do after ALL features stable. "Refactoring while streaming and theming are still changing means every feature change requires updating both the original code AND the extracted component." |
| **Batch E** | P6a, P6d, P6f | 3 easy AI/data items: column type detection, smart sampling, chart tokens | ~3-5 hrs | Quick wins after structural work is done |
| **Batch F** | P6b, P6c, P6e | 3 complex AI/data items: JSON chart mapping, comparative mode, anomaly detection | ~10-15 hrs | Largest scope — last |
| — | Wave 3 weaknesses | API key fallback, app-level auth | Varies | Low priority — only if deployability becomes a goal |

**Total deferred: ~20-35 additional days** after P4 Wave 1 + Streaming ships.

---

## 📊 Why This Order

From the analysis:

> "Streaming restructures the most critical path in the entire app. Theme toggle is ~80 CSS variable overrides with no logic changes. If streaming introduces a regression, you want to catch it on a clean codebase."

> "The right trigger for speccing the refactor is: streaming is shipped and stable, theming is shipped and stable, then you look at the final app.py and extract from that."

> "P6c (comparative analysis) is the hardest item in the entire remaining roadmap. Splitting lets you ship 6A as a clean win and tackle 6B as a focused complex sprint."

---

## 📐 Batch C — Theme Toggle (#18/P3)

**Risk:** High effort for polish | **Effort:** 3-5 days | **Files:** `utils/styles.py`, `app.py`, `pages/learn.py`

**Detailed plan:** [p3-p4/🔵 THEME_TOGGLE.md](p3-p4/🔵 THEME_TOGGLE.md)

### What

Sidebar toggle swapping ~80 CSS custom properties between dark and light palettes. JS snippet syncs `document.documentElement.dataset.theme` with `st.session_state.theme`. Plotly chart templates swap between `plotly_dark` and `plotly_light`.

### 5 Phases

1. Convert all hardcoded colors in `styles.py` to CSS custom properties — verify dark mode unchanged
2. Add `[data-theme="light"]` block with inverted colors
3. Add JS snippet + session state + sidebar toggle
4. Update Plotly templates + learn page CSS
5. Edge case polish: flash fix, Plotly cache-busting, syntax highlighting

### Key Edge Cases

| Scenario | Handling |
|---|---|
| Theme flash on load | JS snippet must run before first paint — inject at top of `inject_custom_css()` |
| Plotly charts still dark after toggle | `st.rerun()` regenerates charts. Add cache-buster key: `f"chart_{i}_{theme}"` |
| Streamlit CSS overrides | Our CSS injected via `st.markdown(unsafe_allow_html=True)` runs after Streamlit's. Use `!important` on critical rules. |
| Learn page code blocks | `.stCode` backgrounds must become theme-aware — ~15 syntax token color overrides |

### Test Impact

Visual smoke test only — no automated CSS tests. Verify all components in both themes: sidebar, hero, metrics, expander, chat bubbles, chat input, file uploader, alert boxes, Plotly charts, dataframes, buttons, footer, spinner.

---

## 📐 Batch D — Component Refactor (#20/P5)

> **Now a standalone mini-spec:** [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) — full design decisions, target architecture, 7-phase extraction plan, edge cases, and test impact.

**Risk:** Medium | **Effort:** 3-5 days | **Files:** New `components/` package (6 files), new `utils/charts.py`, rewritten `app.py` (~60 lines)

**Detailed plan:** [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) — complete code samples for all 7 phases.

Split `app.py` (~500 lines) into a thin orchestrator + 6 focused component modules. Addresses the repo assessment's "single-file orchestration" weakness. 7 extraction phases, each verified independently. ~32 new tests. **Must run after streaming AND theming are stable.**

---

## 📐 Batch E — AI/Data Quick Wins (P6d, P6f, P6a)

**Risk:** Low-Medium | **Effort:** ~3-5 hrs | **Files:** `utils/data_loader.py`, `utils/prompt_templates.py`, `app.py`

**Detailed plan:** [p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](p5-p6/🔵 AI_DATA_ENHANCEMENTS.md) (items P6d, P6f, P6a)

### P6d: Column Type Detection (~1-2 hrs)

Auto-classify columns (date, numeric, categorical, text) with CSS badges in the data preview.

```python
class ColumnType(Enum):
    DATE = "date"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"

def detect_column_types(df: pd.DataFrame) -> dict[str, ColumnType]:
```

Display as colored badges below the metrics row. Date = purple, Numeric = green, Categorical = yellow, Text = gray.

**Tests:** ~4 new in `test_data_loader.py`.

### P6f: Smart Sampling (~1 hr)

Replace `df.head(10)` in prompts with stratified sampling for large datasets.

```python
def smart_sample(df: pd.DataFrame, max_rows: int = 50) -> pd.DataFrame:
```

- ≤50 rows: return all
- 51-10k rows: return head(50)
- >10k rows: stratified sample preserving date distribution

**Tests:** ~3 new in `test_data_loader.py`.

### P6a: Chart Token Detection (~2-3 hrs)

Replace keyword heuristics with Gemini-appended `[CHART:line:sessions]` tokens.

- Prompt instruction: "If a chart would help, append [CHART:line:<metric>] or [CHART:bar:<dimension>]"
- Updated `detect_chart_request()` parses token with regex fallback
- Strip token from displayed response

**Tests:** ~3 new in `test_prompt_templates.py`.

---

## 📐 Batch F — AI/Data Complex Items (P6e, P6b, P6c)

**Risk:** Medium-High | **Effort:** ~10-15 hrs | **Files:** `utils/data_loader.py`, `utils/prompt_templates.py`, `app.py`

**Detailed plan:** [p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](p5-p6/🔵 AI_DATA_ENHANCEMENTS.md) (items P6e, P6b, P6c)

### P6e: Anomaly Detection (~2-3 hrs)

Rolling Z-score on numeric columns. Flag dates where metric deviates >2 std from 7-day rolling mean. Red X markers on Plotly charts.

**Edge cases:** <7 rows (no anomaly detection possible), std=0 (set z_score=0), non-numeric columns (validate before computing).

**Tests:** ~3 new in `test_data_loader.py`.

### P6b: JSON Chart Mapping (~2-3 hrs)

Gemini outputs structured JSON chart configs. Parse with `json.loads` and map dynamically to Plotly.

```json
{"chart_type": "bar", "x": "device_category", "y": "users", "title": "Users by Device"}
```

**Edge cases:** Column hallucination (Gemini fabricates column names — `find_column()` returns None → skip), invalid JSON (caught, returns None).

**Tests:** ~3 new in `test_prompt_templates.py`.

### P6c: Comparative Analysis (~4-6 hrs)

"Compare Q2 vs Q1" or "organic vs paid traffic" — split data, dual prompts, side-by-side charts via `st.columns(2)`.

- Sidebar toggle: "🔬 Compare Mode"
- Select dimension + two values
- `split_for_comparison()` splits DataFrame
- `build_comparison_prompt()` constructs dual-section prompt
- Dual `st.plotly_chart()` in columns

**Edge cases:** One split empty (show warning + single chart), dimension is date (use date ranges not selectbox), >2 values (disallowed — v1 is 2 only).

**Tests:** ~4 new in `test_prompt_templates.py`.

---

## 📐 Wave 3 — Repo Weaknesses (As Needed)

| Weakness | What It Takes | Priority |
|---|---|---|
| API key fallback | Second model config, retry logic, new tests | Low — existing error banner adequate for prototype |
| App-level auth | OAuth/SSO, session mgmt, database | Out of scope per original spec |

**Recommendation:** Do not address unless project scope explicitly shifts from "local prototype" to "deployed multi-user SaaS."

---

## 📈 Execution Order (After P4 Wave 1 + Streaming)

```
Batch C — Theme Toggle (~3-5 days):
  #18 / P3  Light/dark theme toggle
  → Visual smoke test in both themes

Batch D — Component Refactor (~3-5 days):
  #20 / P5  Split app.py into components/ package
  → Run tests: python -m pytest tests/ -q

Batch E — AI/Data Quick Wins (~3-5 hrs):
  P6d  Column type detection
  P6f  Smart sampling
  P6a  Chart token detection
  → Run tests: python -m pytest tests/ -q

Batch F — AI/Data Complex (~10-15 hrs):
  P6e  Anomaly detection
  P6b  JSON chart mapping
  P6c  Comparative analysis
  → Run tests: python -m pytest tests/ -q
```

**Total: ~20-35 days after P4 Wave 1 + Streaming completes.**

---

## 📖 Related Docs

- [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md) — Current sprint (must complete first)
- [P4 future plan](📋 P4-future-plan.md) — Original future-phase plan this derives from
- [p3-p4/🔵 THEME_TOGGLE.md](p3-p4/🔵 THEME_TOGGLE.md) — Detailed theme toggle plan (5 phases)
- [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) — Standalone mini-spec for #20 (design decisions, edge cases)
- [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) — Detailed refactor plan (7 phases, code samples)
- [p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](p5-p6/🔵 AI_DATA_ENHANCEMENTS.md) — Detailed AI/data plan (6 sub-items)
- [Onboarding tour](🔵 onboarding-tour.md) — Deferred #8 mini-spec
- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — Original 21-item blueprint
- [📋 UNIFIED_PLAN.md](📋 UNIFIED_PLAN.md) — Master execution plan
