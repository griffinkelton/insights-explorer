# 🗺️ Unified Implementation Plan — GA4 Insight Explorer

> **Purpose:** Single-source execution blueprint for all plans in the `plans/` directory. These plans are **additive** to the 21 items in [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — P3–P6 here are the detailed breakdowns of IMPL items #18–#21. P1 and P2 are bonus items not in the implementation plan.
>
> **Status:** 🟢 In progress — P1–P2 done ✅, P1–P3 sprint done ✅, P4 Wave 1 + Streaming done ✅, remaining items deferred/captured 🔵.
> **Last updated:** 2026-07-28 (P4 Wave 1 + Streaming sprint executed; 4/4 items, 194 tests)
>
> **Relationship to other docs:** This consolidates 6 plan files into one execution blueprint. It's referenced from [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md). The 21 items in [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) cover smaller, faster changes; the 6 plans here cover larger, multi-day features. Derived planning docs: [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md) (✅ done), [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md) (🔵 active), [P4 deferred plan](📋 P4-deferred-plan.md) (🔵 captured), [Onboarding tour](🔵 onboarding-tour.md) (⚠️ deferred), and [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) (🔵 deferred).

---

## 📋 Plan Inventory

### Original Phase Plans (P1–P6)

| # | Plan File | What | Effort | Risk | Dependencies | IMPL Ref |
|---|---|---|---|---|---|---|
| P1 | [✅ APP_ICON.md](✅ APP_ICON.md) | Custom app icon + favicon (SVG, 8 sizes, PWA manifest, OG image) | 2-3 hrs | Low | None | Bonus |
| P2 | [✅ BONUS_DATA_QUALITY_SCORECARD.md](✅ BONUS_DATA_QUALITY_SCORECARD.md) | A-F data quality card (completeness, duplicates, outliers, date gaps) | 2-4 hrs | Low | None | Bonus ✅ |
| P3 | [p3-p4/🔵 THEME_TOGGLE.md](p3-p4/🔵 THEME_TOGGLE.md) | Light/dark theme toggle (CSS variables, JS sync, Plotly swap) | 3-5 days | High | None | [#18](../IMPLEMENTATION_PLAN.md) |
| P4 | [p3-p4/✅ STREAMING_RESPONSES.md](p3-p4/✅ STREAMING_RESPONSES.md) | Token-by-token streaming chat (generator, st.write_stream, error recovery) | 3-5 days | High | None | [#19](../IMPLEMENTATION_PLAN.md) |
| P5 | [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) | Split app.py into components/ package (7 new files) | 3-5 days | Medium | None | [#20](../IMPLEMENTATION_PLAN.md) |
| P6 | [p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](p5-p6/🔵 AI_DATA_ENHANCEMENTS.md) | 6 AI/data sub-items (chart tokens, JSON mapping, comparative mode, type detection, anomaly detection, smart sampling) | Varies | Medium-High | None | [#21](../IMPLEMENTATION_PLAN.md) |

### Sprint & Future-Phase Plans (derived from IMPLEMENTATION_PLAN.md)

| # | Plan File | What | Effort | Status |
|---|---|---|---|---|
| SP1 | [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md) | IMPL items #1–14 + OAuth redirect + download truncated slice (5 batches) | ~5.5 hrs | ✅ Done (12/13 items, 194 tests) |
| SP2 | [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md) | P4 Wave 1 + Streaming: #15–17, #19 (2 phases) | ~6-7 days | ✅ Done (4/4 items, 194 tests) |
| SP3 | [P4 deferred plan](📋 P4-deferred-plan.md) | Deferred: #18 Theme, #20 Component refactor, #21 AI/data (Batches C–F) | ~20-35 days | 🔵 Captured |
| SP4 | [Onboarding tour](🔵 onboarding-tour.md) | Standalone mini-spec for #8 onboarding tour | ~1 hr | ⚠️ Optional, deferred |
| SP5 | [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) | Standalone mini-spec for #20 component refactor | 3-5 days | 🔵 Deferred (after streaming + theming) |

### P6 Sub-Item Codes

Each sub-item code (21a–21f) maps to a specific ENHANCEMENTS.md item and an independent implementation:

| Code | ENH # | What | Effort |
|---|---|---|---|
| **P6a** | #20 | Chart token detection — Gemini appends `[CHART:line:sessions]` | 2-3 hrs |
| **P6b** | #23 | JSON chart mapping — Gemini outputs `{"chart_type":"bar",...}` | 2-3 hrs |
| **P6c** | #22 | Comparative analysis — split data, dual prompts, side-by-side charts | 4-6 hrs |
| **P6d** | #25 | Column type detection — auto-classify with CSS badges | 1-2 hrs |
| **P6e** | #26 | Anomaly detection — rolling Z-score, red markers | 2-3 hrs |
| **P6f** | #27 | Smart sampling — stratified for large datasets | 1 hr |

---

## 🏗️ Execution Order

```
Wave 1 — Quick Wins (parallel safe, ~5 hrs total):
  P1  App Icon ────────────── No dependencies
  P2  Data Quality Scorecard ── No dependencies

Wave 2 — Game Changers (sequential, ~10 days):
  P4  Streaming Responses ──── Changes response pipeline (do first — hardest)
  P3  Theme Toggle ─────────── CSS architecture change (do after streaming stable)

Wave 3 — Structural (sequential, ~5 days):
  P5  Component Refactor ───── Mechanical extraction (do after features stable)

Wave 4 — AI/Data Layer (parallel, ~8 days):
  P6a Chart Token Detection ── Replaces keyword heuristics
  P6b JSON Chart Mapping ───── Builds on P6a
  P6c Comparative Mode ─────── Largest scope
  P6d Column Type Detection ── Pure function, easiest
  P6e Anomaly Detection ────── Mathematical, well-scoped
  P6f Smart Sampling ───────── Pure function, small
```

### Why This Order

1. **P1 + P2 first** — Both are standalone visual improvements with no code dependencies on anything else. They make the app look and feel more polished immediately. Low risk, high reward.

2. **P4 before P3** — Streaming changes the response rendering pipeline (the most fundamental part of the app). Theming changes CSS (the most superficial part). If streaming breaks something, you want to know before you've spent 3 days on CSS.

3. **P5 after features stabilize** — Component refactoring is mechanical extraction. If you do it while P3 and P4 are still changing, every feature change requires updating both the original code AND the extracted component. Wait until features are stable, then refactor.

4. **P6 last and parallel** — The 6 sub-items are all independent. Do them in any order. The recommended sequence (6d → 6f → 6a → 6e → 6b → 6c) goes from easiest to hardest.

---

## 📐 Detailed Plans (Concise)

### P1: App Icon & Favicon

**Files:** New `assets/` directory, `app.py`, `pages/learn.py`, `utils/styles.py`

**Steps:**
1. Create `assets/icon.svg` — design the master SVG icon
2. Write `scripts/generate_icons.py` — rasterizer for 8 sizes
3. Run it once → generate all PNGs + ICO + OG image
4. Create `assets/site.webmanifest` — PWA manifest
5. Update `app.py` and `pages/learn.py` — swap emoji for `page_icon="assets/favicon.ico"`
6. Add `inject_favicon_meta()` to `utils/styles.py` — HTML meta tags for Apple, Android, OG
7. Call `inject_favicon_meta()` from both pages

**Key edge cases:** `cairosvg` installation (requires `libcairo2`), browser favicon caching, dark/light mode variants

**Test impact:** Smoke test visual verification, structural test for page_icon paths

---

### P2: Data Quality Scorecard

**Files:** `utils/data_loader.py`, `app.py`, `utils/prompt_templates.py`, `tests/test_data_quality.py`

**Steps:**
1. Add `DataQualityReport` dataclass + `assess_data_quality()` to `utils/data_loader.py`
2. Write `tests/test_data_quality.py` — ~10 tests (grade calculation, edge cases)
3. Add `render_quality_scorecard()` to `app.py` — styled A-F card
4. Wire into file processing + GA4 pull flows
5. Add quality section to `build_summary_prompt()` in `utils/prompt_templates.py`

**Key edge cases:** Empty DataFrame, no date column, no numeric columns, constant columns (std=0), 100% duplicates, single row, large datasets (sample for >100k rows)

**Test impact:** ~10 new tests in `test_data_quality.py`

---

### P3: Light/Dark Theme Toggle

**Files:** `utils/styles.py`, `app.py`, `pages/learn.py`

**Steps (5 phases):**
1. **5a:** Convert all hardcoded colors in `styles.py` to CSS custom properties — verify dark mode unchanged
2. **5b:** Add `[data-theme="light"]` block with inverted colors — test via devtools
3. **5c:** Add JS snippet + session state + sidebar toggle + `inject_custom_css(theme=...)`
4. **5d:** Update Plotly chart templates (`template="plotly_dark"|"plotly_light"`) + learn page CSS
5. **5e:** Edge case polish — flash fix, Plotly cache-busting, syntax highlighting, alert boxes

**Key edge cases:** Theme flash on load, Plotly iframe caching, Streamlit's own theme overrides, `!important` specificity, learn page code syntax highlighting, mobile sidebar toggle

**Test impact:** Visual smoke test only — no automated CSS tests

---

### P4: Streaming Token-by-Token Responses

**Files:** `utils/gemini_client.py`, `app.py`

**Steps (4 phases):**
1. **5a:** Add `generate_response_stream()` generator to `gemini_client.py` — write tests
2. **5b:** Rewrite chat handler in `app.py` to use `st.write_stream()` — append → rerun → stream pattern
3. **5c:** Add error recovery with accumulator wrapper for mid-stream failures
4. **5d:** Add Streamlit version check + fallback to non-streaming for <1.37

**Key edge cases:** Mid-stream network failure, mid-stream quota exhaustion, empty stream, message ordering (append→rerun→stream), past message rendering skip, Streamlit version <1.37

**Test impact:** 3 new tests in `test_gemini_client.py`, smoke test for progressive text rendering

---

### P5: Component Refactor

**Files:** New `components/` package (6 files), new `utils/charts.py`, rewritten `app.py` (~60 lines)

**Steps (7 phases):**
1. **5a:** Extract `_generate_chart`, `_find_column`, `_find_date_column` → `utils/charts.py`
2. **5b:** Extract `_render_hero()` → `components/hero.py`
3. **5c:** Extract metrics + preview → `components/data_preview.py`
4. **5d:** Extract summary card + button → `components/summary.py`
5. **5e:** Extract chat interface → `components/chat.py`
6. **5f:** Extract entire sidebar → `components/sidebar.py`
7. **5g:** Rewrite `app.py` as orchestrator + `components/__init__.py`

**Key edge cases:** Widget key collisions across components, `st.rerun()`/`st.stop()` scope, callback function references after moving, session state access across modules

**Test impact:** Structural tests for each new component file (~25 tests), update `test_app.py`

---

### P6: AI & Data Enhancements (6 sub-items)

**Files:** `utils/prompt_templates.py`, `app.py`, `utils/data_loader.py`

| Sub-item | What | Effort | Steps |
|---|---|---|---|
| **P6d: Type Detection** | Auto-classify columns (date, numeric, categorical, text) with CSS badges | 1-2 hrs | `detect_column_types()` + `render_type_badges()` |
| **P6f: Smart Sampling** | Stratified sampling for >10k rows, aggregate stats for >100k | 1 hr | `smart_sample()` — replace `df.head(10)` in prompts |
| **P6a: Chart Tokens** | Gemini appends `[CHART:line:sessions]` tokens — replace keyword heuristics | 2-3 hrs | New prompt instruction + `detect_chart_request()` update + fallback |
| **P6e: Anomaly Detection** | Rolling Z-score on numeric columns, red markers on charts | 2-3 hrs | `detect_anomalies()` + Plotly scatter overlay |
| **P6b: JSON Chart Mapping** | Gemini outputs `{"chart_type":"bar","x":"device","y":"users"}` — parse with `json.loads` | 2-3 hrs | New prompt instruction + `detect_chart_from_json()` + dynamic chart gen |
| **P6c: Comparative Mode** | "Compare Q2 vs Q1" — split data, dual prompts, side-by-side charts | 4-6 hrs | Sidebar toggle + `split_for_comparison()` + `build_comparison_prompt()` + `st.columns(2)` charts |

**Key edge cases:** Column hallucination (Gemini fabricates column names), invalid JSON, std=0 in Z-score, <7 rows for anomaly detection, empty comparison split

**Test impact:** ~20 new tests across modules

---

## 🚀 Sprint Plan

| Sprint | Items | Duration | Outcome |
|---|---|---|---|
| **Sprint P1-P2** | App Icon + Data Quality Scorecard | 1 day ✅ | Polished favicon, trust-building quality card |
| **Sprint P1-P3** | **IMPL items #1–14 + OAuth config** | **~5.5 hrs ✅** | **Guardrails, quick wins, docs, UX, infra — 12/13 done, 194 tests. See [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md)** |
| **Sprint P4 Wave 1** | **#15–17 + #19 Streaming** | **~6-7 days ✅** | **Streaming chat, column picker, conversation memory, export. See [P4 Wave 1 sprint spec](✅ P4-wave1-streaming-sprint-spec.md)** |
| **Sprint Deferred C** | Theme Toggle (#18) | 3-5 days 🔲 | Light/dark mode — after streaming stable. See [P4 deferred plan](📋 P4-deferred-plan.md) |
| **Sprint Deferred D** | Component Refactor (#20) | 3-5 days 🔲 | Clean 7-file architecture — after features stable. See [p5-p6/🔵 COMPONENT_REFACTOR.md](p5-p6/🔵 COMPONENT_REFACTOR.md) |
| **Sprint Deferred E** | P6d (Type Detection), P6f (Sampling), P6a (Chart Tokens) | ~3-5 hrs 🔲 | Three quick AI/data wins. See [P4 deferred plan](📋 P4-deferred-plan.md) |
| **Sprint Deferred F** | P6e (Anomaly), P6b (JSON Mapping), P6c (Comparative) | ~10-15 hrs 🔲 | Complex AI/data items. See [P4 deferred plan](📋 P4-deferred-plan.md) |

**P1–P3 done ✅. P4 Wave 1 + Streaming done ✅ (194 tests). Remaining deferred (~20-35 days).**

---

## 📊 Progress Tracking

### Original Phase Plans

| # | Plan | Files Touched | New Files | Tests | Status |
|---|---|---|---|---|---|
| P1 | App Icon | 5 | 13+ | 0 | ✅ Completed (commit `25ca2df`) |
| P2 | Data Quality Scorecard | 4 | 1 | 18 | ✅ Completed (commit `9842065`) |
| P3 | Theme Toggle | 3 | 0 | 0 | 🔲 Planned |
| P4 | Streaming Responses | 2 | 0 | 3 | ✅ Done (P4 Wave 1 sprint) |
| P5 | Component Refactor | 1 + 7 new | 7 | ~25 | 🔲 Planned |
| P6 | AI & Data Enhancements | 3 | 0 | ~20 | 🔲 Planned |
| **Total** | **6 plans** | **18 + 20 new** | **21+ new** | **~66 new** | **2/6 done** |

### Sprint & Future-Phase Plans

| # | Plan | Items | Est. Time | Status |
|---|---|---|---|---|
| SP1 | P1-P3 Sprint Spec | #1–14 + OAuth + download slice (13 items) | ~5.5 hrs | ✅ Done (12/13, 194 tests) |
| SP2 | P4 Wave 1 + Streaming Sprint | #15–17, #19 — 2 phases | ~6-7 days | ✅ Done (4/4 items, 194 tests) |
| SP3 | P4 Deferred Plan | #18, #20, #21 (Batches C–F), Wave 3 weaknesses | ~20-35 days | 🔵 Captured |
| SP4 | Onboarding Tour (#8) | Mini-spec | ~1 hr | ⚠️ Optional, deferred |
| SP5 | Component Refactor (#20) | Mini-spec | 3-5 days | 🔵 Deferred (after streaming + theming) |

---

## 🔗 How to Execute

Tell your AI agent (Buffy) which item to implement. The agent reads the plan file and follows the detailed steps within it.

| Command | What happens |
|---|---|
| **"Execute P1"** | Read `plans/p1-p2/✅ APP_ICON.md` → create SVG, generate icons, update page configs, smoke test |
| **"Execute P2"** | Read `plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md` → create dataclass, write tests, render scorecard UI |
| **"Execute the unified plan — start at P1"** | Begin with P1, continue through all waves in order |
| **"Skip to P4"** | Jump to streaming responses, skip P1–P3 |
| **"What's the status?"** | Agent reads this file, reports completed vs. planned items |

### Checking Progress

After each item, the agent will:
1. Mark the item as ✅ in the progress tracking table below
2. Run `python -m pytest tests/ -q` to verify no regressions
3. Run `scripts/smoke_test.sh` if the item touches `app.py`
4. Commit with a descriptive message referencing the plan

### Expected Outcomes Per Wave

| Wave | Outcome |
|---|---|
| **Wave 1 (P1–P2)** | Polished brand identity (custom favicon everywhere) + trust-building data quality card |
| **Wave 2 (P4 → P3)** | ChatGPT-like real-time chat + full light/dark theme support |
| **Wave 3 (P5)** | Clean 7-file component architecture from 400-line monolith |
| **Wave 4 (P6)** | 6 independent AI/data upgrades: chart token detection, JSON chart mapping, comparative analysis, column typing, anomaly detection, smart sampling |

---

*This unified plan consolidates all 6 plans in the `plans/` directory. Each plan has its own detailed file — this document is the master index, execution order, and progress tracker. For smaller, faster changes (under 1 hour each), see [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md).*
