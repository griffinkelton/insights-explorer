# 📋 P4 Wave 1 + Streaming Sprint Spec — GA4 Insight Explorer

> **What:** Execution spec for the next sprint: P4 medium features (Wave 1) + game-changer (#19 streaming).
> **Scope:** IMPL items #15 (column picker), #16 (conversation memory), #17 (export chat), #19 (streaming responses).
> **Status:** 🔴 Spec complete — awaiting implementation.
> **Based on:** [P4-future-plan.md](P4-future-plan.md), [phase5/STREAMING_RESPONSES.md](phase5/STREAMING_RESPONSES.md), user interview (3 rounds, July 28, 2026) + follow-up analysis (4 rounds).
> **Deferred items:** Theme toggle (#18), component refactor (#20), AI/data batches E+F — captured in [P4-deferred-plan.md](P4-deferred-plan.md).
> **Predecessor:** [P1-P3-sprint-spec.md](P1-P3-sprint-spec.md) — must be complete and stable.
> **Test baseline:** 194 tests passing across 9 modules.

---

## 🧭 What This Sprint Covers

| # | Item | Effort | Risk | Why in this sprint |
|---|---|---|---|---|
| **#19** | Streaming token-by-token responses | 3-5 days | High | Single most transformative UX improvement. Do first per plan order: "hardest item first." |
| **#15** | Column picker & date filters | ~2 hrs | Medium | Touches data flow — do after streaming is stable |
| **#16** | Multi-turn conversation memory | ~1.5 hrs | Medium | Touches prompt construction |
| **#17** | Export chat as Markdown report | ~1.5 hrs | Medium | Standalone new module |

**Explicitly deferred — see [P4-deferred-plan.md](P4-deferred-plan.md):**
| Batch | # | Item | Effort | When |
|---|---|---|---|---|
| **C** | #18/P3 | Theme toggle | 3-5 days | After streaming stable |
| **D** | #20/P5 | Component refactor | 3-5 days | After streaming + theming stable |
| **E** | P6d,P6f,P6a | AI/data quick wins | 3-5 hrs | After structural work |
| **F** | P6e,P6b,P6c | AI/data complex | 10-15 hrs | Last |
| — | Wave 3 | Repo weaknesses | Varies | If deployability needed |
| — | #8 | Onboarding tour | ~1 hr | [onboarding-tour.md](onboarding-tour.md) |

---

## 🏗️ Design Decisions (from Interview)

| Decision | Choice | Rationale |
|---|---|---|
| Execution order | **Streaming first (#19)** | "Hardest item first — if it breaks something, you want to know before spending time on filters/memory/export." |
| Filter auto-regenerate | **Manual regenerate only** | Filters change the preview + metrics; summary only regenerates when user clicks Generate Summary. Safest for Gemini quota. |
| New Chat button | **Wipe completely** | Clears chat_history entirely — matches `clear_data()` pattern. Simplest UX. |
| Kaleido dependency | **Optional — graceful fallback** | Export works without it; charts get skipped with a warning caption. |
| Streaming scope | **Chat only, no version fallback** | Summary stays non-streaming (one-click, not conversational). No version check needed since Streamlit ≥ 1.60. |
| Empty filter result | **Warn + disable chat/summary** | Show warning banner; disable Generate Summary and chat input until at least one column with data is available. |
| History injection | **Conversation block format** | Past Q&A injected as CONVERSATION HISTORY block within chat prompts. Guard clause: "answer the current question, not these." |
| Mid-stream failure | **Show partial + error** | Accumulate partial response text; on error, show what was streamed so far + error appended. |
| Component refactor | **Defer entirely** | Not in this sprint. |

---

## 📐 Detailed Implementation

---

### #19: Streaming Token-by-Token Responses

**Risk:** High | **Effort:** 3-5 days | **Files:** `utils/gemini_client.py`, `app.py`

**Detailed plan:** [phase5/STREAMING_RESPONSES.md](phase5/STREAMING_RESPONSES.md)

#### What Changes

The current chat flow is synchronous: `generate_response()` blocks for 3-5 seconds, then the full text renders all at once. Streaming changes this to token-by-token rendering via `st.write_stream()`.

**Architecture change:**

```
Before:  build_prompt → generate_response (BLOCKS) → detect_chart → render
After:   build_prompt → generate_response_stream → st.write_stream → detect_chart → render chart
```

#### Phase 1: `utils/gemini_client.py` — Streaming Generator

Add `generate_response_stream()`:

```python
from collections.abc import Generator

def generate_response_stream(
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> Generator[str, None, None]:
    """Stream Gemini response tokens one at a time.

    Yields text chunks as they arrive from the API.
    The caller is responsible for collecting the full text
    and running chart detection after the stream completes.

    Raises ValueError for missing API key, RuntimeError for API failures.
    """
    try:
        response = _get_client().models.generate_content_stream(
            model=model,
            contents=prompt,
            config={
                "temperature": DEFAULT_TEMPERATURE,
                "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            },
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "rate" in error_msg and "limit" in error_msg:
            raise RuntimeError(
                "Rate limit hit. Please wait a moment and try again."
            ) from e
        elif "quota" in error_msg:
            raise RuntimeError(
                "API quota exceeded. Check your Google Cloud quota or try again later."
            ) from e
        else:
            raise RuntimeError(
                f"Gemini API error: {str(e)}"
            ) from e
```

**Keep `generate_response()`:** The summary button still uses it — a single non-streaming response doesn't benefit from streaming.

#### Phase 2: `app.py` — Streaming Chat Handler

Rewrite the chat input handler to use the append→rerun→stream pattern:

```python
if prompt := st.chat_input("e.g., which pages have the highest drop-off?"):
    # Rate limiting guard (unchanged)
    now = time.time()
    if now - st.session_state.last_api_call < 2.0:
        st.warning("⏳ Please wait a moment between questions...")
        st.stop()
    st.session_state.last_api_call = now
    st.session_state.api_call_count += 1

    # Append question with empty response, then rerun to stream
    st.session_state.chat_history.append({
        "question": prompt,
        "response": "",
        "chart": None,
    })
    st.rerun()

# ── Streaming section (renders on rerun after appending question) ──

# Find the latest unanswered entry
if st.session_state.chat_history and st.session_state.chat_history[-1]["response"] == "":
    entry = st.session_state.chat_history[-1]

    # Render past messages (excluding the streaming one)
    for i, past in enumerate(st.session_state.chat_history[:-1]):
        with st.chat_message("user"):
            st.markdown(past["question"])
        with st.chat_message("assistant"):
            if past.get("response"):
                st.markdown(past["response"])
            if past.get("chart") and past["chart"].get("fig"):
                with st.container(border=True):
                    st.plotly_chart(past["chart"]["fig"], use_container_width=True, key=f"chart_{i}")

    # Render the new user message
    with st.chat_message("user"):
        st.markdown(entry["question"])

    # Stream the response
    with st.chat_message("assistant"):
        accumulated = []
        try:
            def _accumulating_stream():
                for chunk in generate_response_stream(
                    build_chat_prompt(entry["question"], st.session_state.df, st.session_state.stats)
                ):
                    accumulated.append(chunk)
                    yield chunk

            full_response = st.write_stream(_accumulating_stream())

            # After stream completes, detect and render chart
            chart_config = detect_chart_request(full_response)
            if chart_config:
                chart_data = _generate_chart(
                    st.session_state.df, chart_config, full_response, entry["question"]
                )
                if chart_data:
                    with st.container(border=True):
                        st.plotly_chart(
                            chart_data["fig"],
                            use_container_width=True,
                            key=f"chart_stream_{len(st.session_state.chat_history)}",
                        )
                    entry["chart"] = chart_data

            entry["response"] = full_response

        except ValueError as e:
            partial = "".join(accumulated)
            entry["response"] = f"{partial}\n\n*🔑 Configuration error: {e}*"
            st.error(f"🔑 Configuration error: {e}")
        except RuntimeError as e:
            partial = "".join(accumulated)
            entry["response"] = f"{partial}\n\n*⚠️ API error: {e}*"
            st.error(f"⚠️ API error: {e}")
```

**Key design decisions:**
- **`append→rerun→stream` pattern:** Question appended with empty `""` response → `st.rerun()` → on rerun, the unanswered entry triggers the stream. This ensures correct message ordering (user message renders before assistant stream starts).
- **Accumulator wrapper:** `_accumulating_stream()` tracks chunks in a list for partial-output recovery on mid-stream errors.
- **Chart after stream:** Chart detection runs on `full_response` after `st.write_stream()` returns the complete text.

#### Edge Cases

| Scenario | Handling |
|---|---|
| Mid-stream API failure | Accumulated partial text shown + error appended to response |
| Empty stream | Gemini always returns ≥1 token for valid prompts. If empty, `""` response renders as empty bubble (acceptable) |
| Very long response (10k+ tokens) | `max_output_tokens=2048` caps it. Streaming handles 2k tokens smoothly |
| User sends message while streaming | Streamlit disables chat input during processing (default behavior) |
| Summary generation | Stays non-streaming — uses existing `generate_response()` |

#### Test Impact

Add to `test_gemini_client.py` (3 tests):
- `test_generate_response_stream_yields_tokens` — mock `generate_content_stream`, verify generator yields chunks
- `test_generate_response_stream_handles_rate_limit` — mock raises rate limit, verify RuntimeError
- `test_generate_response_stream_handles_quota_exceeded` — mock raises quota error, verify RuntimeError

Smoke test: send chat message, verify text appears progressively.

---

### #15: Column Picker & Date Filters

**Risk:** Medium | **Effort:** ~2 hrs | **Files:** `app.py`, `utils/data_loader.py`

#### What Changes

Add filter controls between the data preview and AI summary. Users narrow analysis to specific date ranges and columns without re-uploading.

#### `utils/data_loader.py` — New helper

```python
def filter_dataframe(
    df: pd.DataFrame,
    date_col: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    selected_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Apply date range and column filters. Never mutates the original."""
    filtered = df.copy()

    if date_col and date_col in filtered.columns:
        filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
        if start_date:
            filtered = filtered[filtered[date_col] >= pd.Timestamp(start_date)]
        if end_date:
            filtered = filtered[filtered[date_col] <= pd.Timestamp(end_date)]

    if selected_columns:
        valid_cols = [c for c in selected_columns if c in filtered.columns]
        if valid_cols:
            filtered = filtered[valid_cols]
        else:
            return filtered.iloc[0:0]  # Empty but preserves column structure hint

    return filtered
```

#### `app.py` — Filter Controls

Between data preview and AI summary:

```python
# ── Data filters ─────────────────────────────────────────────────────────
if st.session_state.df is not None:
    st.markdown("### 🔍 Filter Data")

    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1])

    with col_filter1:
        all_columns = st.session_state.df.columns.tolist()
        selected_columns = st.multiselect(
            "Columns to include",
            options=all_columns,
            default=all_columns,
            key="filter_columns",
        )

    with col_filter2:
        date_col = _find_date_column(st.session_state.df)
        if date_col:
            dates = pd.to_datetime(st.session_state.df[date_col], errors="coerce").dropna()
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

    with col_filter3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reset Filters", use_container_width=True):
            st.session_state.filter_columns = all_columns
            if date_col and not dates.empty:
                st.session_state.filter_dates = (min_date, max_date)
            st.rerun()

    # Apply filters
    filtered_df = filter_dataframe(
        st.session_state.df,
        date_col=date_col,
        start_date=str(date_range[0]) if date_range else None,
        end_date=str(date_range[1]) if date_range else None,
        selected_columns=selected_columns,
    )

    if filtered_df.empty:
        st.warning("⚠️ No rows match your filters. Try a wider date range or select more columns.")
        st.session_state.filtered_df = None
    else:
        st.session_state.filtered_df = filtered_df
        st.caption(f"Showing {len(filtered_df):,} of {len(st.session_state.df):,} rows")
```

#### Downstream Consumer Updates

Every reference to `st.session_state.df` in the rendered content must switch to `filtered_df`:

| Consumer | Before | After |
|---|---|---|
| Data preview | `st.dataframe(df.head(10))` | `st.dataframe(filtered_df.head(10))` |
| Metrics row | `stats['row_count']` | `len(filtered_df)` |
| Summary prompt | `build_summary_prompt(df, stats)` | Manual regenerate only — recompute stats on click |
| Chat prompt | `build_chat_prompt(prompt, df, stats)` | `build_chat_prompt(prompt, filtered_df, filtered_stats)` |
| Chart generation | `_generate_chart(df, ...)` | `_generate_chart(filtered_df, ...)` |

**⚠️ Critical:** Missing any consumer creates a silent bug where charts/prompts use unfiltered data while the UI shows filtered data.

#### Edge Cases

| Scenario | Handling |
|---|---|
| Empty filtered dataset | Warning shown, `filtered_df` set to None, chat/summary disabled |
| All columns deselected | Warning shown, chat/summary disabled |
| Date column with mixed formats | `pd.to_datetime(errors="coerce")` handles — invalid values become NaT and are excluded |
| Filter state persistence | Filter values in `st.session_state` survive reruns. Reset button clears them. |
| Summary after filter change | **Manual only** — user must click Generate Summary again. Prevents quota burn. |

#### Test Impact

Add to `test_data_loader.py` (5 tests):
- `test_filter_dataframe_by_date_range`
- `test_filter_dataframe_by_columns`
- `test_filter_dataframe_empty_result`
- `test_filter_dataframe_no_filters_returns_original`
- `test_filter_dataframe_all_columns_deselected`

---

### #16: Multi-Turn Conversation Memory

**Risk:** Medium | **Effort:** ~1.5 hrs | **Files:** `utils/prompt_templates.py`, `app.py`

#### What Changes

Include the last 5 Q&A exchanges in each chat prompt so Gemini has context for follow-up questions. Add a "New Chat" button that wipes history.

#### `utils/prompt_templates.py` — Modified signature

```python
def build_chat_prompt(
    user_question: str,
    df: pd.DataFrame,
    stats: dict[str, Any],
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
```

After the sample data and before the user question, append:

```python
if conversation_history:
    history_entries = conversation_history[-5:]  # Last 5 exchanges
    history_str = "\n".join(
        f"User: {h['question']}\n"
        f"Assistant: {h.get('response', '')[:500]}"
        for h in history_entries
        if h.get("response")
    )
    if history_str.strip():
        prompt += (
            f"\n\nCONVERSATION HISTORY:\n{history_str}\n\n"
            f"Answer the CURRENT question above, not questions from the history."
        )
```

**Why "Answer the CURRENT question" guard clause:** Without it, Gemini sometimes continues answering previous questions instead of the new one.

#### `app.py` — Pass history

```python
chat_prompt = build_chat_prompt(
    prompt,
    df,
    stats,
    conversation_history=st.session_state.chat_history,
)
```

#### `app.py` — "New Chat" Button

Add between chat header and chat history:

```python
col_chat_header, col_new_chat = st.columns([4, 1])
with col_new_chat:
    if st.button("🆕 New Chat", use_container_width=True,
                 help="Clear chat history but keep your data"):
        st.session_state.chat_history = []
        st.rerun()
```

#### Edge Cases

| Scenario | Handling |
|---|---|
| 50+ Q&A sessions | Only last 5 exchanges included; each response truncated to 500 chars |
| First message | `conversation_history` is empty → no history block appended. Works as before. |
| Failed responses (None) | Skipped from history block via `if h.get("response")` |
| Data change (clear_data) | `clear_data()` wipes chat history → new data = new conversation |
| History + streaming | Streaming entry has `response=""` during streaming — excluded from history until complete |

#### Test Impact

Add to `test_prompt_templates.py` (4 tests):
- `test_build_chat_prompt_includes_history`
- `test_build_chat_prompt_truncates_long_history`
- `test_build_chat_prompt_handles_empty_history`
- `test_build_chat_prompt_history_not_included_for_first_message`

---

### #17: Export Chat as Markdown Report

**Risk:** Medium | **Effort:** ~1.5 hrs | **Files:** New `utils/report_exporter.py`, `app.py`, `requirements.txt`

#### `utils/report_exporter.py` (New)

```python
"""Report exporter — builds downloadable Markdown reports from chat sessions."""

from typing import Any
import base64
import pandas as pd
import plotly.graph_objects as go


def build_markdown_report(
    summary: str | None,
    chat_history: list[dict[str, Any]],
    stats: dict[str, Any],
    data_source: str | None = None,
) -> str:
    """Build a Markdown report from the current session."""
    lines = []

    lines.append("# 📊 GA4 Insight Explorer — Report")
    lines.append("")
    lines.append(f"*Generated on {pd.Timestamp.now().strftime('%Y-%m-%d at %H:%M')}*")
    lines.append(f"*Data source: {data_source or 'Unknown'}*")
    lines.append("")

    lines.append("## 📋 Dataset Overview")
    lines.append("")
    lines.append(f"- **Rows:** {stats.get('row_count', 'N/A'):,}")
    lines.append(f"- **Columns:** {stats.get('column_count', 'N/A')}")
    lines.append(f"- **Date range:** {stats.get('date_range_start', 'N/A')} → {stats.get('date_range_end', 'N/A')}")
    lines.append("")

    if summary:
        lines.append("## 🤖 AI-Generated Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    if chat_history:
        lines.append("## 💬 Q&A")
        lines.append("")
        for i, entry in enumerate(chat_history, 1):
            if entry.get("response"):
                lines.append(f"### Q{i}: {entry['question']}")
                lines.append("")
                lines.append(entry["response"])
                lines.append("")
                if entry.get("chart") and entry["chart"].get("fig"):
                    chart_png = _chart_to_base64(entry["chart"]["fig"])
                    if chart_png:
                        lines.append(f"![Chart for Q{i}]({chart_png})")
                        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Report generated by [GA4 Insight Explorer](https://github.com/griffinkelton/insights-explorer)*")

    return "\n".join(lines)


def _chart_to_base64(fig: go.Figure) -> str | None:
    """Convert Plotly figure to base64 PNG. Requires kaleido."""
    try:
        img_bytes = fig.to_image(format="png", scale=2)
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None  # Silently skip if kaleido isn't installed
```

#### `app.py` — Export Button

In the chat area, after chat history rendering:

```python
if st.session_state.chat_history:
    st.divider()
    if st.button("📥 Export Report", use_container_width=True):
        from utils.report_exporter import build_markdown_report

        report = build_markdown_report(
            summary=st.session_state.summary,
            chat_history=st.session_state.chat_history,
            stats=st.session_state.stats or {},
            data_source=st.session_state.data_source,
        )
        st.download_button(
            label="⬇️ Download Markdown Report",
            data=report,
            file_name=f"ga4_insight_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
        )
        st.caption(
            "⚠️ Charts missing from the report? "
            "Install kaleido: `pip install kaleido`"
        )
```

#### `requirements.txt` — New Dependency

```
kaleido>=0.2.1
```

**Optional:** `kaleido` is listed but export works without it — charts are skipped with a warning caption.

#### Edge Cases

| Scenario | Handling |
|---|---|
| kaleido not installed | Charts skipped, warning caption shown below download button |
| 100+ Q&A session | All included — Markdown has no practical size limit |
| No charts in session | Export still works — just skips chart embedding |
| No AI summary | Summary section omitted |
| Slow chart export | `fig.to_image()` may take 2-5 sec per chart — acceptable for export |

#### Test Impact

Add to new `test_report_exporter.py` (3 tests):
- `test_builds_report_with_summary_and_chat`
- `test_builds_report_without_charts`
- `test_builds_report_handles_empty_state`

---

## 📊 Execution Plan

```
Phase 1 — Streaming (~3-5 days):
  #19a Add generate_response_stream() to gemini_client.py       ~1 day
  #19b Rewrite chat handler for st.write_stream()                ~1-2 days
  #19c Add accumulator wrapper + error recovery                  ~1 day
  → Run tests: python -m pytest tests/ -q
  → Run smoke test: bash scripts/smoke_test.sh

Phase 2 — Filters + Memory (~3.5 hrs):
  #15  Column picker & date filters                             ~2 hrs
  #16  Multi-turn conversation memory                           ~1.5 hrs
  → Run tests: python -m pytest tests/ -q
  → Run smoke test: bash scripts/smoke_test.sh

Phase 3 — Export (~1.5 hrs):
  #17  Export chat as Markdown report                           ~1.5 hrs
  → Run tests: python -m pytest tests/ -q

Verify + Update:
  → Run full test suite
  → Update P4+ completion tracker
  → Update CHANGELOG.md
```

**Total estimated time: ~6-7 days** (streaming is the bulk at 3-5 days)

---

## 🧪 Test Impact Summary

| Item | New Tests | Updated Tests |
|---|---|---|
| #19 Streaming | +3 (`test_gemini_client.py`) | Chat handler restructured |
| #15 Column picker | +5 (`test_data_loader.py`) | — |
| #16 Conversation memory | +4 (`test_prompt_templates.py`) | `build_chat_prompt` signature change |
| #17 Export chat | +3 (`test_report_exporter.py`) | — |
| **Total** | **+15** | |

**Post-implementation expected test count: ~209 tests.**

---

## ⚠️ Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Streaming breaks message ordering | `append→rerun→stream` pattern tested in Phase 2; smoke test verifies |
| Mid-stream errors lose partial response | Accumulator wrapper captures chunks; partial + error shown |
| Filtered_df silent bug (missing a consumer) | Checklist of 5 consumers verified at implementation time |
| History makes Gemini answer old questions | "Answer the CURRENT question" guard clause + only 5 entries |
| kaleido installation fails | Graceful fallback — charts skipped with caption warning |
| Streaming + rate limiting interaction | Rate limiting guard runs BEFORE streaming starts — same as current flow |

---

## 📖 Related Docs

- [P1-P3-sprint-spec.md](P1-P3-sprint-spec.md) — Predecessor sprint (must be complete first)
- [P4-future-plan.md](P4-future-plan.md) — Future-phase plan this sprint derives from
- [phase5/STREAMING_RESPONSES.md](phase5/STREAMING_RESPONSES.md) — Detailed streaming plan (4 phases)
- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — Original 21-item blueprint
- [ENHANCEMENTS.md](../ENHANCEMENTS.md) — 37-item enhancement roadmap
- [onboarding-tour.md](onboarding-tour.md) — Deferred #8 mini-spec
