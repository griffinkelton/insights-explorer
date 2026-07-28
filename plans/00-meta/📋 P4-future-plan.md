# 📋 P4+ Future-Phase Plan — GA4 Insight Explorer

> **What:** Capture document for all items beyond the current P1–P3 sprint — medium features, large investments, and unresolved repo weaknesses.
> **Status:** 🟢 Partially done — Wave 1 + Streaming sprint executed ✅ (4/4 items). Remaining items (#18, #20, #21, Wave 3) deferred in [P4 deferred plan](📋 P4-deferred-plan.md).
> **Based on:** IMPLEMENTATION_PLAN.md (#15–21), 📋 UNIFIED_PLAN.md (P3–P6), ENHANCEMENTS.md, repo assessment weaknesses.
> **Predecessor:** [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md) — completed. #8 tour deferred to [Onboarding tour](🔵 onboarding-tour.md).
> **Current sprint:** [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md) — #15–17, #19 ✅ Done.
> **Deferred items:** [P4 deferred plan](📋 P4-deferred-plan.md) — #18, #20, #21 (Batches C–F).

---

## 🧭 What This Plan Covers

Everything deferred from the current sprint, organized into three waves:

| Wave | What | Items | Est. Time |
|---|---|---|---|
| **Wave 1** | Medium Features (P4) | #15 Column picker, #16 Conversation memory, #17 Export chat | ~5 hrs |
| **Wave 2** | Large Investments (P5) | #18 Theme toggle, #19 Streaming, #20 Component refactor, #21 AI/data enhancements | 14–24 days |
| **Wave 3** | Repo Weaknesses | API key fallback, app-level auth (if deployability becomes a goal) | Varies |

---## 📊 Current State

**Wave 1 (#15–17) + Streaming (#19)** — ✅ Done. See [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md).

**Everything else** (#18, #20, #21, Wave 3 weaknesses) is captured in [P4 deferred plan](📋 P4-deferred-plan.md) for execution next.

The guardrails (file limits, rate limiting), quick wins (sidebar link, OAuth config), docs, and infra from P1–P3 are solid, so the medium-risk features that change the data flow can now proceed.

---

## 🌊 Wave 1 — Medium Features (P4) ✅ Done

> **Implemented in:** P4 Wave 1 + Streaming sprint. See [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md).

Estimated total time: **~5 hours**

These are the three most-requested user-facing capabilities. Each touches the core data flow or prompt construction.

---

### #15: Column Picker & Date Filters

**Risk:** Medium | **Effort:** ~2 hrs | **Files:** `app.py`, `utils/data_loader.py`

**From:** IMPLEMENTATION_PLAN.md #15, ENHANCEMENTS.md #24

**What:** Let users narrow their analysis to specific date ranges and columns without re-uploading. The filtered DataFrame replaces the full one downstream (summary, chat, charts).

**Key design decisions:**
- `st.session_state.filtered_df` as the working dataset; `st.session_state.df` preserved as source of truth
- `filter_dataframe()` helper in `utils/data_loader.py` — pure function, never mutates
- Every downstream consumer must switch from `df` to `filtered_df` — a silent bug if any are missed

**Downstream consumer checklist:**

| Consumer | Before | After |
|---|---|---|
| Data preview table | `st.dataframe(df.head(10))` | `st.dataframe(filtered_df.head(10))` |
| Summary prompt | `build_summary_prompt(df, stats)` | Recompute stats for filtered data |
| Chat prompt | `build_chat_prompt(prompt, df, stats)` | `build_chat_prompt(prompt, filtered_df, filtered_stats)` |
| Chart generation | `_generate_chart(df, ...)` | `_generate_chart(filtered_df, ...)` |
| Metrics row | `stats['row_count']` | `len(filtered_df)` |

**Edge cases:** Empty filtered dataset (show warning, don't crash), all columns deselected (warn), date columns with mixed formats (`pd.to_datetime(errors="coerce")` handles).

**Test impact:** ~5 new tests in `test_data_loader.py`.

**Dependencies:** P1–P3 sprint must be stable — this touches the same `app.py` areas as #4, #7, #8.

---

### #16: Multi-Turn Conversation Memory

**Risk:** Medium | **Effort:** ~1.5 hrs | **Files:** `utils/prompt_templates.py`, `app.py`

**From:** IMPLEMENTATION_PLAN.md #16, ENHANCEMENTS.md #2

**What:** Include the last 5 Q&A exchanges in each chat prompt so Gemini has context for follow-up questions. Add a "New Chat" button to wipe history without clearing data.

**Key design decisions:**
- Last 5 exchanges only; each response truncated to 500 chars
- "Answer the current question, not these" guard clause prevents Gemini from continuing old answers
- Failed responses (None) are excluded from history block
- `clear_data()` wipes chat history automatically — new data = new conversation

**Edge cases:** 50+ Q&A sessions (only 5 included), first message (empty history — works as before), history across data changes (wiped by `clear_data()`).

**Test impact:** ~4 new tests in `test_prompt_templates.py`.

**Dependencies:** None directly, but changes prompt construction — the most sensitive part of the app.

---

### #17: Export Chat as Markdown Report

**Risk:** Medium | **Effort:** ~1.5 hrs | **Files:** New `utils/report_exporter.py`, `app.py`, `requirements.txt`

**From:** IMPLEMENTATION_PLAN.md #17, ENHANCEMENTS.md #3

**What:** Bundle the AI summary, chat Q&A, and Plotly charts into a downloadable Markdown file. Charts embedded as base64 PNGs via `kaleido`.

**Key design decisions:**
- Markdown (not PDF) — simpler, renders on GitHub/VS Code/any viewer
- `kaleido` for Plotly→PNG conversion (official replacement for deprecated `orca`)
- Charts gracefully skipped if `kaleido` isn't installed (with a warning caption)
- No AI summary? That section is simply omitted.

**Edge cases:** `kaleido` not installed (charts skipped + warning), 100+ Q&A (include all — Markdown has no practical size limit), no charts in session (export still works), slow chart export for complex figures.

**Test impact:** ~3 new tests in `test_report_exporter.py`. New dependency: `kaleido>=0.2.1`.

**Dependencies:** None.

---

## 🌊 Wave 2 — Large Investments (P5)

Estimated total time: **14–24 days** (one person, sequential order per 📋 UNIFIED_PLAN.md)

Each of these has a detailed implementation plan in `plans/p3-p4/ and plans/p5-p6/`. This document provides the summary; implementation should follow the detailed plans.

---

### #18 / P3: Light/Dark Theme Toggle

**Risk:** High effort for polish | **Effort:** 3–5 days | **Files:** `utils/styles.py`, `app.py`, `pages/learn.py`

**From:** IMPLEMENTATION_PLAN.md #18, 📋 UNIFIED_PLAN.md P3, ENHANCEMENTS.md #6

**Detailed plan:** [plans/p3-p4/✅ THEME_TOGGLE.md](p3-p4/✅ THEME_TOGGLE.md)

**What:** Sidebar toggle swapping ~80 CSS custom properties between dark and light palettes. JS snippet syncs `document.documentElement.dataset.theme` with `st.session_state.theme`. Plotly chart templates swap between `plotly_dark` and `plotly_light`.

**5 phases:**
1. Convert hardcoded colors to CSS custom properties — verify dark mode unchanged
2. Add `[data-theme="light"]` block with inverted colors
3. Add JS snippet + session state + sidebar toggle
4. Update Plotly templates + learn page CSS
5. Edge case polish: flash fix, Plotly cache-busting, syntax highlighting, alert boxes

**Key edge cases:** Theme flash on load, Plotly iframe caching, `!important` specificity battles with Streamlit's own CSS.

**Test impact:** Visual smoke test only — no automated CSS tests.

---

### #19 / P4: Streaming Token-by-Token Responses ✅ Done

> **Implemented in:** P4 Wave 1 sprint — st.write_stream with generate_response_stream generator.

**Risk:** High | **Effort:** 3–5 days | **Files:** `utils/gemini_client.py`, `app.py`

**From:** IMPLEMENTATION_PLAN.md #19, 📋 UNIFIED_PLAN.md P4, ENHANCEMENTS.md #21

**Detailed plan:** [plans/p3-p4/✅ STREAMING_RESPONSES.md](p3-p4/✅ STREAMING_RESPONSES.md)

**What:** Instead of waiting 3–5 seconds for the full Gemini response, stream tokens one at a time using `st.write_stream()` — creating a ChatGPT-like real-time feel.

**Why this is complex:** The current architecture is `generate_response` → full text → `detect_chart_request` → render chat + chart. Streaming requires: stream text with `st.write_stream` → collect full text from return value → detect chart on full text → render chart below.

**4 phases:**
1. Add `generate_response_stream()` generator to `gemini_client.py`
2. Rewrite chat handler to use `st.write_stream()` + append→rerun→stream pattern
3. Add error recovery with accumulator wrapper for mid-stream failures
4. Add Streamlit version check + fallback to non-streaming for <1.37

**Key edge cases:** Mid-stream network failure, mid-stream quota exhaustion, empty stream, message ordering.

**Test impact:** 3 new tests in `test_gemini_client.py`.

---

### #20 / P5: Component Refactor 🔵 Mini-spec'd

> **Now a standalone mini-spec:** [p5-p6/✅ COMPONENT_REFACTOR.md](p5-p6/✅ COMPONENT_REFACTOR.md) — design decisions, target architecture, 7-phase extraction plan.

**Risk:** Medium | **Effort:** 3–5 days | **Files:** New `components/` package (6 files), new `utils/charts.py`, rewritten `app.py` (~60 lines)

**From:** IMPLEMENTATION_PLAN.md #20, 📋 UNIFIED_PLAN.md P5, ENHANCEMENTS.md #12

**Detailed plan:** [plans/p5-p6/✅ COMPONENT_REFACTOR.md](p5-p6/✅ COMPONENT_REFACTOR.md)

**What:** Split `app.py` (~400 lines) into a thin orchestrator + 6 focused component modules. This directly addresses the repo assessment's "single-file orchestration" weakness.

**Target architecture:**
```
app.py (~60 lines)              # Page config, session state, error boundary → components.render_all()
components/
├── __init__.py                 # render_all() orchestrator
├── sidebar.py                  # render_sidebar() — uploader, GA4 connect, learn link
├── hero.py                     # render_hero() — empty state
├── data_preview.py             # render_data_preview() — metrics, table, filters
├── chat.py                     # render_chat() — history, input, export button
└── summary.py                  # render_summary() — AI summary + generate button
utils/
└── charts.py                   # generate_chart(), find_column(), find_date_column()
```

**7 extraction phases** — each extracting one section, verifying tests pass, then moving to the next.

**Key edge cases:** Widget key collisions across components, `st.rerun()`/`st.stop()` scope, callback function references after moving, session state access across modules.

**Test impact:** Structural tests for each new component (~25 tests), update `test_app.py`.

**⚠️ Critical ordering:** Do this AFTER Wave 2 features are stable. Refactoring while features are still changing means every feature change requires updating both the original code AND the extracted component.

---

### #21 / P6: AI & Data Enhancements (6 sub-items)

**Risk:** Medium–High | **Effort:** Varies (1–6 hrs each) | **Files:** `utils/prompt_templates.py`, `app.py`, `utils/data_loader.py`

**From:** IMPLEMENTATION_PLAN.md #21, 📋 UNIFIED_PLAN.md P6, ENHANCEMENTS.md #20, #22, #23, #25, #26, #27

**Detailed plan:** [plans/p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](p5-p6/🔵 AI_DATA_ENHANCEMENTS.md)

Six independent sub-items, ordered easiest → hardest:

| Code | ENH # | What | Effort | Risk |
|---|---|---|---|---|
| **P6d** | #25 | Column type detection — auto-classify columns (date, numeric, categorical, text) with CSS badges | 1–2 hrs | Low |
| **P6f** | #27 | Smart sampling — stratified sampling for >10k rows, aggregate stats for >100k | 1 hr | Low |
| **P6a** | #20 | Chart token detection — Gemini appends `[CHART:line:sessions]` tokens; replace keyword heuristics | 2–3 hrs | Medium |
| **P6e** | #26 | Anomaly detection — rolling Z-score on numeric columns, red markers on Plotly charts | 2–3 hrs | Medium |
| **P6b** | #23 | JSON chart mapping — Gemini outputs `{"chart_type":"bar","x":"device","y":"users"}`; parse with `json.loads` | 2–3 hrs | Medium |
| **P6c** | #22 | Comparative analysis — "Compare Q2 vs Q1" — split data, dual prompts, side-by-side charts | 4–6 hrs | High |

**Key edge cases:** Column hallucination (Gemini fabricates column names), invalid JSON in chart mapping, std=0 in Z-score, <7 rows for anomaly detection, empty comparison split.

**Test impact:** ~20 new tests across modules.

---

## 🌊 Wave 3 — Repo Assessment Weaknesses

These were identified in the repo assessment but are out of scope for P1–P3. Two are partially addressed; two remain unresolved.

---

### ✅ Partially Addressed

| Weakness | Already Covered By | Notes |
|---|---|---|
| **Single-file orchestration** | #20 Component Refactor (Wave 2) | Addressed when the component refactor lands |
| **CI tied to GCP** | #14 GitHub Actions (P1–P3 sprint) + Cloud Build coexistence | Both CI pipelines after P1–P3 sprint |

### 🔲 Still Unresolved

| Weakness | What It Would Take | Priority |
|---|---|---|
| **Localhost-only OAuth redirect** | ✅ Addressed in P1–P3 sprint (NEW-A: `OAUTH_REDIRECT_URI` env var) | Done in current sprint |
| **Gemini API key as single point of failure** | See below — requires gemini_client.py changes | Low — existing error banner is adequate for prototype |
| **No app-level auth** | See below — explicitly out of scope per original spec | Low — only relevant if deployability becomes a goal |

---

### Unresolved #1: Gemini API Key Fallback

**What the weakness says:** "There's a startup check and persistent error banner, but no fallback model or graceful degradation if the API is unavailable."

**Analysis:** The current behavior handles this reasonably well for a prototype:
- `validate_api_key()` runs on startup with a persistent error banner
- `generate_response()` catches rate limits and quota errors with user-friendly messages
- The app fails closed — no silent failures

**What a fallback would require:**
- A second model configuration (e.g., `gemini-1.5-flash` as fallback)
- Retry logic with exponential backoff
- Potentially a non-Gemini fallback (OpenAI, local model) — significant complexity
- New tests for the fallback chain

**Recommendation:** Defer until there's a concrete deployment scenario that demands it. For local single-user use, the existing error handling is sufficient. If deployed to Streamlit Cloud with multiple users, revisit.

---

### Unresolved #2: App-Level Authentication

**What the weakness says:** "The app has no user-facing authentication layer, so anyone with the URL can upload data or trigger AI calls against your API key."

**Analysis:** The original spec explicitly states: "Do not add authentication, user accounts, or any database — this is a local single-user prototype." Adding auth would be a fundamental architectural change that contradicts the project's privacy-first, local-only design.

**What auth would require:**
- A user authentication system (OAuth, password, or SSO)
- Session management
- Per-user API key or quota tracking
- A database or external auth provider
- Significant security review

**Recommendation:** Do not add unless the project's scope explicitly shifts from "local prototype" to "deployed multi-user SaaS." If that shift happens, a dedicated auth spec should be written before any implementation.

---

## 📈 Execution Order

```
✅ P1–P3 sprint — DONE (12/13 items implemented, 194 tests)

🔵 CURRENT SPRINT — [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md):
  Phase 1: #19 Streaming (~3-5 days)          ── Changes response pipeline (hardest)
  Phase 2: #15 Column picker + #16 Memory     ── Touches data flow + prompt construction
  Phase 3: #17 Export chat (~1.5 hrs)          ── Standalone (new module)

🔲 DEFERRED — [P4 deferred plan](📋 P4-deferred-plan.md):
  Batch C: #18 Theme toggle (~3-5 days)       ── CSS architecture (after streaming stable)
  Batch D: #20 Component refactor (~3-5 days)  ── Mechanical extraction (after features stable)
  Batch E: #21a Column types + Smart sampling  ── Quick AI/data wins (~2-3 hrs)
  Batch F: #21b Chart tokens + Anomaly + JSON + Comparative ── Complex AI/data (~10-15 hrs)
  Wave 3: API key fallback, app-level auth    ── Only if deployment demands it
```

### Why This Order (from 📋 UNIFIED_PLAN.md)

1. **Streaming before theming** — Streaming changes the response rendering pipeline (the most fundamental part of the app). Theming changes CSS (the most superficial part). If streaming breaks something, you want to know before you've spent 3 days on CSS.

2. **Component refactor after features stabilize** — Mechanical extraction. If you do it while streaming and theming are still changing, every feature change requires updating both the original code AND the extracted component.

3. **AI/Data sub-items last and parallel** — All 6 are independent. Go easiest → hardest.

---

## 📊 Total Scope Summary

| Wave | Items | Est. Time | Risk Level |
|---|---|---|---|
| **Wave 1** (P4) | #15, #16, #17 | ~5 hrs | Medium |
| **Wave 2a** (P5 game changers) | #18/P3, #19/P4 | ~8 days | High |
| **Wave 2b** (P5 structural) | #20/P5 | ~5 days | Medium |
| **Wave 2c** (P5 AI/data) | #21/P6 (6 sub-items) | ~8 days | Medium–High |
| **Wave 3** (weaknesses) | API fallback, app auth | TBD | Low priority |
| **Total** | **16 items** | **~26 days** | |

---

## 📖 Related Docs

- [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md) — **Current sprint:** #15-17, #19 (~6-7 days)
- [P4 deferred plan](📋 P4-deferred-plan.md) — Deferred: #18, #20, #21, Wave 3 (~20-35 days)
- [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md) — Completed sprint (must complete first)
- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — Source 21-item plan
- [📋 UNIFIED_PLAN.md](📋 UNIFIED_PLAN.md) — Master execution plan with detailed P3–P6 breakdowns
- [ENHANCEMENTS.md](../ENHANCEMENTS.md) — 37-item enhancement roadmap
- [p3-p4/✅ THEME_TOGGLE.md](p3-p4/✅ THEME_TOGGLE.md) — Detailed theme toggle plan (5 phases)
- [p3-p4/✅ STREAMING_RESPONSES.md](p3-p4/✅ STREAMING_RESPONSES.md) — Detailed streaming plan (4 phases)
- [p5-p6/✅ COMPONENT_REFACTOR.md](p5-p6/✅ COMPONENT_REFACTOR.md) — **Standalone mini-spec** for #20 (deferred)
- [p5-p6/✅ COMPONENT_REFACTOR.md](p5-p6/✅ COMPONENT_REFACTOR.md) — Detailed refactor plan (7 phases, code samples)
- [p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](p5-p6/🔵 AI_DATA_ENHANCEMENTS.md) — Detailed AI/data plan (6 sub-items)
- [Onboarding tour](🔵 onboarding-tour.md) — Standalone mini-spec for #8 (deferred)
- [ARCHITECTURE.md](../ARCHITECTURE.md) — Design decisions, data flow, security model
- [ORIGINAL_SPEC.md](../ORIGINAL_SPEC.md) — Initial project prompt + 26-item compliance checklist
