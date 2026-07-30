# 📚 Documentation Index — GA4 Insight Explorer

> Central index of all project documentation. Every MD file in the repo, what it covers, and how they relate to each other.

---

## 📖 Core Documentation

| File | Purpose | When to read |
|---|---|---|
| [README.md](README.md) | Setup guide, features, tech stack, security, quick start | First — before running the app |
| [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) | The initial project prompt + 26-item compliance checklist | To understand what was asked for vs what was built |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Design decisions, data flow, security model, dependencies, build log | To understand how the app is structured and why |
| [BUGLOG.md](BUGLOG.md) | Structured bug log — every error encountered, root cause, fix, and learnings (10 bugs) | When debugging, after encountering an error, or reviewing patterns |
| [CHANGELOG.md](CHANGELOG.md) | Unified change history with commit hashes, dates, and related doc links | To see what changed in each release |
| [SECURITY.md](SECURITY.md) | Security policy and vulnerability reporting process | Before reporting a vulnerability |
| [LICENSE](LICENSE) | MIT License | To understand usage rights |
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | v0.1.0 release checklist with evidence and sign-off | Release verification |

---

## 🗺️ Planning & Roadmap

| File | Purpose | When to read |
|---|---|---|
| [ENHANCEMENTS.md](plans/00-meta/ENHANCEMENTS.md) | 37-item enhancement roadmap across 7 categories (UX, Code, Security, AI, Data, DevOps, Docs) | To see what's been done and what's available |
| [IMPLEMENTATION_PLAN.md](plans/00-meta/IMPLEMENTATION_PLAN.md) | Detailed 21-item execution blueprint with file-level precision, risk assessments, sprint plan | Before starting any implementation work |
| [IDEAS.md](IDEAS.md) | 25 bonus enhancements + 10 moonshot ideas (creative, not in the plan) | For inspiration and long-term vision |

---

## 📐 Detailed Phase Plans

| File | Purpose (why read this?) | What it covers | Effort / Status |
|---|---|---|---|
| [plans/00-meta/✅ UNIFIED_PLAN.md](plans/00-meta/✅ UNIFIED_PLAN.md) | Understand the big picture: which plans exist, what order to run them, and overall progress | 6 phase plans (P1–P6) + 5 sprint/derived plans (SP1–SP5) + progress tracker | Reference |
| [plans/p1-p2/✅ APP_ICON.md](plans/p1-p2/✅ APP_ICON.md) | Polish the app's brand identity across browsers, PWA installs, and social sharing previews | Custom SVG icon + 8 PNG sizes + PWA manifest + OG image (UNIFIED P1) | Small (2-3 hrs) ✅ Done |
| [plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md](plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md) | Build user trust by showing data quality at a glance before running AI analysis | A-F grading on completeness, duplicates, outliers, and date gaps (UNIFIED P2) | Medium (2-4 hrs) ✅ Done |
| [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md) | See the step-by-step execution plan that shipped the first 13 improvements | IMPL items #1–14 + OAuth redirect + download slice (5 batches, ~5.5 hrs) | ✅ Done (12/13, 194 tests) |
| [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md) | Confirm exactly what was built and what was deferred in the first sprint | Checkbox tracker — progress for all 13 items | ✅ Complete |
| [plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md](plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md) | See how streaming chat, column filters, conversation memory, and export were built | #15–17 Wave 1 + #19 Streaming (2 phases, ~6-7 days) | ✅ Done (4/4 items, 194 tests) |
| [plans/00-meta/✅ P4-future-plan.md](plans/00-meta/✅ P4-future-plan.md) | Understand what comes next: medium features, large investments, and repo weaknesses | IMPL items #15–21 + P3–P6 + repo weaknesses (3 waves) | 🔵 Partially spec'd |
| [plans/00-meta/✅ P4-deferred-plan.md](plans/00-meta/✅ P4-deferred-plan.md) | See the full catalog of work still waiting: theme, refactor, and 6 AI/data items | #18 Theme, #20 Component refactor, #21 AI/data (Batches C–F, ~20-35 days) | 🔵 Captured |
| [plans/00-meta/✅ onboarding-tour.md](plans/00-meta/✅ onboarding-tour.md) | Eliminate the "cold start" problem — guide first-time users through the app in 30 seconds | 3-step guided tour: upload → summary → chat, with auto-dismiss | ⚠️ Deferred (~1 hr) |
| [plans/p5-p6/✅ COMPONENT_REFACTOR.md](plans/p5-p6/✅ COMPONENT_REFACTOR.md) | Clean up technical debt: turn the 809-line monolith into maintainable modules | Design decisions, target architecture, 7-phase extraction plan (IMPL #20, UNIFIED P5) | ✅ Done (78-line app.py, 228 tests) |
| [plans/00-sprints/✅ component-refactor-spec.md](plans/00-sprints/✅ component-refactor-spec.md) | The implementation spec derived from 5 interview rounds — exact decisions, code samples, test patterns | Full Phase 1-7 execution spec with design table, code samples, test impact, edge cases | ✅ Done (see plan above) |
| [plans/00-sprints/🔵 v0.2.0-implementation-spec.md](plans/00-sprints/🔵%20v0.2.0-implementation-spec.md) | The implementation spec for the post-hardening release — DataContext refactor, Learn page, styles, Gemini telemetry | 13 design decisions, 5 phases, frozen DataContext + replace(), 4-step migration, analysis-versioned cache keys, 8-section Learn page, keyboard fixes, focus-visible, Gemini informational-only, custom release checklist | 🔵 Spec'd (5 phases, ~10-16 days) |
| [plans/p3-p4/✅ THEME_TOGGLE.md](plans/p3-p4/✅ THEME_TOGGLE.md) | Give users a light mode option — the single most-requested visual improvement | CSS variables, JS sync, Plotly chart swapping (IMPL #18, UNIFIED P3) | ✅ Done (231 tests) |
| [plans/00-sprints/✅ theme-toggle-spec.md](plans/00-sprints/✅ theme-toggle-spec.md) | The implementation spec derived from 3 interview rounds — exact decisions, code samples, file-level changes | 4-phase plan executed: CSS → toggle → charts → polish | ✅ Done |
| [plans/p3-p4/✅ STREAMING_RESPONSES.md](plans/p3-p4/✅ STREAMING_RESPONSES.md) | Make chat feel real-time instead of waiting 3-5 seconds per response | Generator, st.write_stream, append→rerun→stream pattern (IMPL #19, UNIFIED P4) | High (3-5 days) ✅ Done |
| [plans/p5-p6/🔵 AI_DATA_ENHANCEMENTS.md](plans/p5-p6/🔵 AI_DATA_ENHANCEMENTS.md) | Upgrade the AI and data layer: smarter charts, anomaly detection, comparative mode | 6 sub-items: chart tokens, JSON mapping, type detection, sampling, anomalies, comparisons (IMPL #21, UNIFIED P6) | 3-4 days 🔵 Spec'd |
| [plans/00-sprints/✅ ai-data-enhancements-spec.md](plans/00-sprints/✅ ai-data-enhancements-spec.md) | The implementation spec derived from 3 interview rounds — exact decisions, code samples, 5-phase order | 6 sub-items: type detection → sampling → chart JSON → anomalies → compare mode. 239 tests. | ✅ Done (239 tests) |
| [plans/00-sprints/✅ drive-file-picker-spec.md](plans/00-sprints/✅ drive-file-picker-spec.md) | Add a Google Drive file picker to the sidebar — load CSVs/Sheets directly | 7 files changed, 2 new: drive_client.py + sidebar UI. Piggybacks on GA4 OAuth. 236 tests. | ✅ Done (236 tests) |
| [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) | Security hardening: OAuth scope reduction, token revocation, error handling refactor, model constraints | Post-phase-6 code review remediation — 7 commits, 359 tests, scope fix (drive→drive.readonly+drive.file), chmod hardening, scope migration banner, shared error classification, token tracking, dead code cleanup, BUG-009 & BUG-010 | ✅ Done (359 tests) |

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
        ├──► ENHANCEMENTS.md (→ plans/00-meta/) ── "What could be improved" (37 items, 22 done)
        ├──► BUGLOG.md ──────── "What broke and why" (10 bugs)
        ├──► IDEAS.md ───────── "What's beyond the roadmap" (25 + 10 moonshots)
        ├──► CHANGELOG.md ───── "Unified change history"
        └──► IMPLEMENTATION_PLAN.md (→ plans/00-meta/) ── "21-item execution blueprint"
```

### Plan Files

```
IMPLEMENTATION_PLAN.md (→ plans/00-meta/)
        │
        ├──► plans/00-sprints/✅ P1-P3-sprint-spec.md ── "Sprint done ✅ (194 tests)"
        │           └──► plans/00-sprints/✅ P1-P3-completion.md
        │
        ├──► plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md ── "Active sprint 🔵"
        │
        ├──► plans/00-meta/✅ P4-deferred-plan.md ── "Deferred (Batches C–F)"
        │           └──► plans/p5-p6/✅ COMPONENT_REFACTOR.md ── "#20 mini-spec"
        │
        ├──► plans/00-meta/✅ onboarding-tour.md ── "#8 mini-spec (deferred)"
        │
        ├──► plans/00-meta/✅ UNIFIED_PLAN.md ── "Master index"
        │
        ├──► plans/p1-p2/✅ APP_ICON.md ✅
        ├──► plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md ✅
        │
        ├──► plans/p3-p4/
        │        ├── ✅ THEME_TOGGLE.md
        │        └── ✅ STREAMING_RESPONSES.md
        │
        ├──► plans/p5-p6/
        │        ├── ✅ COMPONENT_REFACTOR.md
        │        └── 🔵 AI_DATA_ENHANCEMENTS.md
        │
        └──► plans/maintenance/
                 ├── ✅ 2026-07-29-oauth-scope-remediation-spec.md
                 ├── ✅ 2026-07-29-drive-scope-remediation-plan.md
                 └── ✅ 2026-07-29-drive-export-model-selector-session.md
        │
        ├──► plans/🔵 v0.2.0-plan.md ── "Post-hardening roadmap (d1–d7, 5 phases)"
        │           └──► plans/00-sprints/🔵 v0.2.0-implementation-spec.md ── "Detailed exec spec (13 decisions, 5 phases)"
        │
        └──► plans/audit/ (all ✅ — v0.1.0 hardening artifacts)
                 ├── ✅ v0.1.0-closeout.md ── "What v0.1.0 delivered + baseline"
                 ├── ✅ v0.1.0-hardening-spec.md
                 ├── ✅ v0.1.0-hardening-plan.md
                 └── ✅ chatgpt-6.3-terra-feedback.md
```
```

---

## 📊 Document Status

| File | Purpose | Status | Last Updated |
|---|---|---|---|
| README.md | First read: setup guide, features, tech stack, security, quick start | ✅ Current | 2026-07-29 |
| ORIGINAL_SPEC.md | The initial project requirements and 26-item compliance checklist | ✅ Current | 2026-07-29 |
| ARCHITECTURE.md | Design decisions, data flow, security model, dependencies, build log | ✅ Current | 2026-07-29 |
| ENHANCEMENTS.md (→ plans/00-meta/) | 37-item roadmap of what's been improved and what's still available | ✅ Current | 2026-07-29 |
| IMPLEMENTATION_PLAN.md (→ plans/00-meta/) | 21-item execution blueprint — the master implementation guide | ✅ Current | 2026-07-29 |
| IDEAS.md | Creative ideas beyond the roadmap: 25 bonus enhancements + 10 moonshots | ✅ Current | 2026-07-29 |
| BUGLOG.md | Structured bug history with root causes, fixes, and detection patterns (10 bugs) | ✅ Current | 2026-07-29 |
| DOCUMENTATION_INDEX.md | This file — central index connecting all project documentation | ✅ Current | 2026-07-29 |
| CHANGELOG.md | Unified change history with commit hashes and related doc links | ✅ Current | 2026-07-29 |
| plans/p1-p2/✅ APP_ICON.md | How to create a custom SVG favicon + PWA manifest (completed) | ✅ Completed | 2026-07-29 |
| plans/p1-p2/✅ BONUS_DATA_QUALITY_SCORECARD.md | How to add an A-F data quality grading card (completed) | ✅ Completed | 2026-07-29 |
| plans/00-meta/✅ UNIFIED_PLAN.md | Master index of all 11 plans with execution order and progress | ✅ Current | 2026-07-29 |
| plans/00-sprints/✅ P1-P3-sprint-spec.md | P1–P3 implementation spec for the first 13 quick wins (completed) | ✅ Done | 2026-07-29 |
| plans/00-sprints/✅ P1-P3-completion.md | Checkbox tracker: exactly what was done in the P1–P3 sprint | ✅ Complete | 2026-07-29 |
| plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md | P4 Wave 1 + Streaming sprint spec (completed) | ✅ Done | 2026-07-29 |
| plans/00-meta/✅ P4-future-plan.md | Future-phase plan for all deferred items | 🔵 Partially spec'd | 2026-07-29 |
| plans/00-meta/✅ P4-deferred-plan.md | Deferred items catalog: Batches C–F | 🔵 Captured | 2026-07-29 |
| plans/00-meta/✅ onboarding-tour.md | How to build a 3-step guided tour for first-time users | ⚠️ Deferred | 2026-07-29 |
| plans/p5-p6/✅ COMPONENT_REFACTOR.md | How to split app.py into 7 clean component files (merged from mini-spec) | ✅ Done | 2026-07-29 |
| plans/00-sprints/✅ component-refactor-spec.md | Interview-derived implementation spec with exact decisions and test patterns | ✅ Done | 2026-07-29 |
| plans/p3-p4/✅ THEME_TOGGLE.md | Light/dark mode plan: CSS variables, JS sync, Plotly chart swapping | ✅ Done | 2026-07-29 |
| plans/00-sprints/✅ theme-toggle-spec.md | Interview-derived spec: 9 design decisions, 4-phase plan, 7 files | ✅ Done | 2026-07-29 |
| plans/p3-p4/✅ STREAMING_RESPONSES.md | ChatGPT-style token-by-token streaming with error recovery (done) | ✅ Current | 2026-07-29 |
| plans/p5-p6/🔵 AI_DATA_ENHANCEMENTS.md | 6 independent AI/data upgrades: charts, anomalies, sampling | ✅ Current | 2026-07-29 |
| plans/00-sprints/✅ ai-data-enhancements-spec.md | Interview-derived spec: 9 design decisions, 5-phase order, 6 sub-items | ✅ Done | 2026-07-29 |
| plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md | Post-phase-6 OAuth security hardening & code quality remediation spec | ✅ Done | 2026-07-29 |
| plans/maintenance/✅ 2026-07-29-drive-scope-remediation-plan.md | Original remediation plan — predecessor to the spec above | ✅ Done | 2026-07-29 |
| plans/maintenance/✅ 2026-07-29-drive-export-model-selector-session.md | Session summary: Drive write-back, model selector, export formats, multimodal support | ✅ Done | 2026-07-29 |
| plans/🔵 v0.2.0-plan.md | Post-hardening roadmap: 7 deferred items (d1–d7), 5 phases, ~10-16 days | 🔵 Planning | 2026-07-30 |
| plans/00-sprints/🔵 v0.2.0-implementation-spec.md | Detailed implementation spec: frozen DataContext, 8-section Learn page, focus-visible, Gemini telemetry | 🔵 Spec'd | 2026-07-30 |
| plans/audit/✅ v0.1.0-closeout.md | v0.1.0 close-out: what was delivered, deferred items, audit baseline, release evidence | ✅ Final | 2026-07-30 |
| plans/audit/✅ v0.1.0-hardening-spec.md | Hardening implementation spec — PR 0–4 acceptance criteria, security gates | ✅ Done | 2026-07-30 |
| plans/audit/✅ v0.1.0-hardening-plan.md | GPT-5.6 full codebase audit + v0.1.0 hardening plan | ✅ Done | 2026-07-30 |
| plans/audit/✅ chatgpt-6.3-terra-feedback.md | Original GPT-6.3 audit feedback — 12 batches of findings | ✅ Done | 2026-07-30 |

---

*This index was last updated 2026-07-30 during the v0.2.0 DataContext refactor (458 tests, 0 warnings, 8 modules at 100% coverage).*
