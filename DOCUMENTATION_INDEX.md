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
| [plans/UNIFIED_PLAN.md](plans/UNIFIED_PLAN.md) | Master index of all plans — 6 phase plans (P1–P6) + 3 sprint/derived plans (SP1–SP3) + progress tracker | Reference |
| [plans/APP_ICON.md](plans/APP_ICON.md) | Custom app icon + favicon design and implementation (UNIFIED P1) | Small (2-3 hrs) ✅ Done |
| [plans/BONUS_DATA_QUALITY_SCORECARD.md](plans/BONUS_DATA_QUALITY_SCORECARD.md) | Data quality scorecard — A-F grading, styled card, prompt integration (UNIFIED P2) | Medium (2-4 hrs) ✅ Done |
| [plans/P1-P3-sprint-spec.md](plans/P1-P3-sprint-spec.md) | Current sprint: IMPL items #1–14 + OAuth redirect + download slice (5 batches, ~5.5 hrs) | ~5.5 hrs |
| [plans/P4-future-plan.md](plans/P4-future-plan.md) | Future phases: IMPL items #15–21 + P3–P6 + repo weaknesses (3 waves, ~26 days) | ~26 days |
| [plans/onboarding-tour.md](plans/onboarding-tour.md) | Standalone mini-spec for #8 onboarding tour (⚠️ Optional, ~60 min) | ~1 hr |
| [plans/phase5/THEME_TOGGLE.md](plans/phase5/THEME_TOGGLE.md) | Light/dark theme toggle — CSS variables, JS sync, Plotly swap (IMPL #18, UNIFIED P3) | High (3-5 days) |
| [plans/phase5/STREAMING_RESPONSES.md](plans/phase5/STREAMING_RESPONSES.md) | Streaming token-by-token responses — generator, st.write_stream, error recovery (IMPL #19, UNIFIED P4) | High (3-5 days) |
| [plans/phase5/COMPONENT_REFACTOR.md](plans/phase5/COMPONENT_REFACTOR.md) | Refactor app.py into components/ package — 7 new files (IMPL #20, UNIFIED P5) | High (3-5 days) |
| [plans/phase5/AI_DATA_ENHANCEMENTS.md](plans/phase5/AI_DATA_ENHANCEMENTS.md) | 6 AI/data sub-items — chart tokens, JSON mapping, comparative mode, type detection, anomaly detection, smart sampling (IMPL #21, UNIFIED P6) | Medium-High (varies) |

---

## 🔗 How These Docs Connect

```
ORIGINAL_SPEC.md ─── "What was asked for"
        │
        ▼
README.md ─── "How to run it"
        │
        ▼
ARCHITECTURE.md ─── "How it's built"
        │
        ├──► ENHANCEMENTS.md ─── "What could be improved" (37 items, 15 done)
        │           │
        │           └──► IMPLEMENTATION_PLAN.md ─── "How to build the next 21 items"
        │                       │
        │                       ├──► plans/P1-P3-sprint-spec.md ─── "Current sprint (13 items)"
        │                       │           │
        │                       │           └──► plans/onboarding-tour.md ─── "#8 mini-spec"
        │                       │
        │                       ├──► plans/P4-future-plan.md ─── "Deferred items (16 items)"
        │                       │
        │                       ├──► plans/APP_ICON.md
        │                       ├──► plans/BONUS_DATA_QUALITY_SCORECARD.md
        │                       └──► plans/phase5/
        │                               ├── THEME_TOGGLE.md
        │                               ├── STREAMING_RESPONSES.md
        │                               ├── COMPONENT_REFACTOR.md
        │                               └── AI_DATA_ENHANCEMENTS.md
        │
        ├──► BUGLOG.md ─── "What broke and why" (8 bugs, all 4 patterns CI-gated)
        │
        ├──► IDEAS.md ─── "What's beyond the roadmap" (25 enhancements + 10 moonshots)
        │
        └──► plans/UNIFIED_PLAN.md ─── "Master execution plan" (9 plans, 2/6 done, 3 derived)
```

---

## 📊 Document Status

| File | Status | Last Updated |
|---|---|---|
| README.md | ✅ Current (test counts, project structure updated) | Today |
| ORIGINAL_SPEC.md | ✅ Current | Today |
| ARCHITECTURE.md | ✅ Current (build log, test counts, project structure updated) | Today |
| ENHANCEMENTS.md | ✅ Current (v2 rewrite) | Today |
| IMPLEMENTATION_PLAN.md | ✅ Current (#6 skipped, #7 done, cross-refs to new plans) | Today |
| IDEAS.md | ✅ Current | Today |
| BUGLOG.md | ✅ Current (all 4 patterns CI-gated) | Today |
| DOCUMENTATION_INDEX.md | ✅ Current (new plan files added) | Today |
| plans/APP_ICON.md | ✅ Completed | Today |
| plans/BONUS_DATA_QUALITY_SCORECARD.md | ✅ Completed | Today |
| plans/UNIFIED_PLAN.md | ✅ Current (P1–P2 complete, SP1–SP3 added, progress tracker updated) | Today |
| plans/P1-P3-sprint-spec.md | ✅ Current (spec complete, awaiting implementation) | Today |
| plans/P4-future-plan.md | ✅ Current (captured, awaiting P1–P3 completion) | Today |
| plans/onboarding-tour.md | ✅ Current (⚠️ Optional, deferred) | Today |
| plans/phase5/THEME_TOGGLE.md | ✅ Current | Today |
| plans/phase5/STREAMING_RESPONSES.md | ✅ Current | Today |
| plans/phase5/COMPONENT_REFACTOR.md | ✅ Current | Today |
| plans/phase5/AI_DATA_ENHANCEMENTS.md | ✅ Current | Today |

---

*This index should be updated whenever a new MD file is added or an existing one is significantly revised.*
