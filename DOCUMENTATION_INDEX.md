# 📚 Documentation Index — GA4 Insight Explorer

> Central index of all project documentation. Every MD file in the repo, what it covers, and how they relate to each other.

---

## 📖 Core Documentation

| File | Purpose | When to read |
|---|---|---|
| [README.md](README.md) | Setup guide, features, tech stack, security, quick start | First — before running the app |
| [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) | The initial project prompt + 26-item compliance checklist | To understand what was asked for vs what was built |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Design decisions, data flow, security model, dependencies, build log | To understand how the app is structured and why |
| [BUGLOG.md](BUGLOG.md) | Structured bug log — every error encountered, root cause, fix, and learnings | When debugging, after encountering an error, or reviewing patterns |

---

## 🗺️ Planning & Roadmap

| File | Purpose | When to read |
|---|---|---|
| [ENHANCEMENTS.md](ENHANCEMENTS.md) | 37-item enhancement roadmap across 7 categories (UX, Code, Security, AI, Data, DevOps, Docs) | To see what's been done and what's available |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Detailed 21-item execution blueprint with file-level precision, risk assessments, sprint plan | Before starting any implementation work |
| [IDEAS.md](IDEAS.md) | 25 bonus enhancements + 10 moonshot ideas (creative, not in the plan) | For inspiration and long-term vision |

---

## 📐 Detailed Phase Plans

| File | Covers | Effort |
|---|---|---|
| [plans/UNIFIED_PLAN.md](plans/UNIFIED_PLAN.md) | Master index of all plans — 6 phase plans (P1–P6) + 5 sprint/derived plans (SP1–SP5) + progress tracker | Reference |
| [plans/APP_ICON.md](plans/APP_ICON.md) | Custom app icon + favicon design and implementation (UNIFIED P1) | Small (2-3 hrs) ✅ Done |
| [plans/BONUS_DATA_QUALITY_SCORECARD.md](plans/BONUS_DATA_QUALITY_SCORECARD.md) | Data quality scorecard — A-F grading, styled card, prompt integration (UNIFIED P2) | Medium (2-4 hrs) ✅ Done |
| [plans/P1-P3-sprint-spec.md](plans/P1-P3-sprint-spec.md) | P1–P3 sprint: IMPL items #1–14 + OAuth redirect + download slice (5 batches, ~5.5 hrs) | ✅ Done (12/13, 194 tests) |
| [plans/P1-P3-completion.md](plans/P1-P3-completion.md) | Sprint completion tracker — checkbox progress for all 13 items | ✅ Complete |
| [plans/P4-wave1-streaming-sprint-spec.md](plans/P4-wave1-streaming-sprint-spec.md) | Active sprint: #15–17 Wave 1 + #19 Streaming (2 phases, ~6-7 days) | 🔵 Spec'd |
| [plans/P4-future-plan.md](plans/P4-future-plan.md) | Future phases: IMPL items #15–21 + P3–P6 + repo weaknesses (3 waves) — now split into active + deferred | 🔵 Partially spec'd |
| [plans/P4-deferred-plan.md](plans/P4-deferred-plan.md) | Deferred: #18 Theme, #20 Component refactor, #21 AI/data (Batches C–F, ~20-35 days) | 🔵 Captured |
| [plans/onboarding-tour.md](plans/onboarding-tour.md) | Standalone mini-spec for #8 onboarding tour (⚠️ Optional) | ⚠️ Deferred |
| [plans/component-refactor.md](plans/component-refactor.md) | Standalone mini-spec for #20 component refactor (⚠️ Deferred) | 🔵 Deferred |
| [plans/phase5/THEME_TOGGLE.md](plans/phase5/THEME_TOGGLE.md) | Light/dark theme toggle — CSS variables, JS sync, Plotly swap (IMPL #18, UNIFIED P3) | High (3-5 days) |
| [plans/phase5/STREAMING_RESPONSES.md](plans/phase5/STREAMING_RESPONSES.md) | Streaming token-by-token responses — generator, st.write_stream, error recovery (IMPL #19, UNIFIED P4) | High (3-5 days) |
| [plans/phase5/COMPONENT_REFACTOR.md](plans/phase5/COMPONENT_REFACTOR.md) | Refactor app.py into components/ package — 7 new files (IMPL #20, UNIFIED P5) | High (3-5 days) |
| [plans/phase5/AI_DATA_ENHANCEMENTS.md](plans/phase5/AI_DATA_ENHANCEMENTS.md) | 6 AI/data sub-items — chart tokens, JSON mapping, comparative mode, type detection, anomaly detection, smart sampling (IMPL #21, UNIFIED P6) | Medium-High (varies) |

---

## 🔗 How These Docs Connect

### Core Docs

```
ORIGINAL_SPEC.md ─── "What was asked for"
        │
        ▼
README.md ─── "How to run it"
        │
        ▼
ARCHITECTURE.md ─── "How it's built"
        │
        ├──► ENHANCEMENTS.md ── "What could be improved" (37 items, 22 done)
        ├──► BUGLOG.md ──────── "What broke and why" (8 bugs)
        ├──► IDEAS.md ───────── "What's beyond the roadmap" (25 + 10 moonshots)
        ├──► CHANGELOG.md ───── "Unified change history"
        └──► IMPLEMENTATION_PLAN.md ── "21-item execution blueprint"
```

### Plan Files

```
IMPLEMENTATION_PLAN.md
        │
        ├──► plans/P1-P3-sprint-spec.md ── "Sprint done ✅ (194 tests)"
        │           └──► plans/P1-P3-completion.md
        │
        ├──► plans/P4-wave1-streaming-sprint-spec.md ── "Active sprint 🔵"
        │
        ├──► plans/P4-deferred-plan.md ── "Deferred (Batches C–F)"
        │           └──► plans/component-refactor.md ── "#20 mini-spec"
        │
        ├──► plans/onboarding-tour.md ── "#8 mini-spec (deferred)"
        │
        ├──► plans/UNIFIED_PLAN.md ── "Master index"
        │
        ├──► plans/APP_ICON.md ✅
        ├──► plans/BONUS_DATA_QUALITY_SCORECARD.md ✅
        │
        └──► plans/phase5/
                 ├── THEME_TOGGLE.md
                 ├── STREAMING_RESPONSES.md
                 ├── COMPONENT_REFACTOR.md
                 └── AI_DATA_ENHANCEMENTS.md
```
```

---

## 📊 Document Status

| File | Status | Last Updated |
|---|---|---|
| README.md | ✅ Current (test counts 171→194, test_app.py added, CHANGELOG in structure) | Today |
| ORIGINAL_SPEC.md | ✅ Current | Today |
| ARCHITECTURE.md | ✅ Current (build log #41–52, test count 194) | Today |
| ENHANCEMENTS.md | ✅ Current (22/37 done, P1-P3 sprint reflected) | Today |
| IMPLEMENTATION_PLAN.md | ✅ Current (#6 skipped, #7 done, cross-refs to new plans) | Today |
| IDEAS.md | ✅ Current | Today |
| BUGLOG.md | ✅ Current (all 4 patterns CI-gated) | Today |
| DOCUMENTATION_INDEX.md | ✅ Current (all new plan files added) | Today |
| CHANGELOG.md | ✅ Current (43 commits tracked, P1-P3 sprint entries) | Today |
| plans/APP_ICON.md | ✅ Completed | Today |
| plans/BONUS_DATA_QUALITY_SCORECARD.md | ✅ Completed | Today |
| plans/UNIFIED_PLAN.md | ✅ Current (SP1–SP5 added, progress tracker updated) | Today |
| plans/P1-P3-sprint-spec.md | ✅ Done (12/13 implemented, 194 tests) | Today |
| plans/P1-P3-completion.md | ✅ Complete (all items tracked) | Today |
| plans/P4-wave1-streaming-sprint-spec.md | 🔵 Spec'd — awaiting implementation | Today |
| plans/P4-future-plan.md | 🔵 Partially spec'd (Wave 1+streaming active, rest deferred) | Today |
| plans/P4-deferred-plan.md | 🔵 Captured (Batches C–F deferred) | Today |
| plans/onboarding-tour.md | ⚠️ Optional, deferred | Today |
| plans/component-refactor.md | 🔵 Deferred (after streaming + theming stable) | Today |
| plans/phase5/THEME_TOGGLE.md | ✅ Current | Today |
| plans/phase5/STREAMING_RESPONSES.md | ✅ Current | Today |
| plans/phase5/COMPONENT_REFACTOR.md | ✅ Current | Today |
| plans/phase5/AI_DATA_ENHANCEMENTS.md | ✅ Current | Today |

---

*This index should be updated whenever a new MD file is added or an existing one is significantly revised.*
