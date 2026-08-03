# Roadmap — GA4 Insights Engine

> **Single source of truth** for what we're building, in what order, and why.
> Cross-references: `braintree-reqs.md` (client questions), `🔵 ga4-insights-sketch.md` (engine design), `ga4-measurement-contract.md` (metric governance), `🔵 evidence-connector-design.md` (demographic bridge), `BRAINTREE_CHECKLIST.md` (task tracker).

---

## Versions → Gates

| Version | Gate | What ships | Key dependency | Status |
|---------|------|------------|---------------|--------|
| **v0.3.0** | — | Drive Import, Picker UX, Playwright CI, test-mode seam | — | 🟡 Release verification (manual matrix pending) |
| **v0.4.0** | 0A + 0B | Measurement contract sign-off, data feasibility report, evidence connector (Phase A: manual sync, session-only) | Named metric owner approves rows 1–2; event-level GA4 data decision | 🔵 Planning |
| **v0.5.0** | 1 | GA4 descriptive insights: validated reach, trends, pages, devices, data-quality alerts. Structured evidence objects injected into Gemini prompt. | Gates 0A–0B complete; rows 1–2 `validated` in measurement contract | 🔵 Planning |
| **v0.6.0** | 2 | Evidence overlay: demographic linkage, equity reach, funnel equity, pathway equity, language access, small-cell suppression | Event-level GA4 data + validated linkage protocol + evidence connector Phase B (local encrypted persistence) | 🔵 Planning |
| **v0.7.0** | 3 | Outcomes & evaluation: survey cohort reporting, dose-response, content-to-outcome mapping, campaign evaluation | Survey data + selection-bias protocol + outcome definitions approved | 🔵 Planning |

---

## The Hard Blocker: Event-Level Data

`pull_ga4_report()` returns **aggregate rows only** (`date`, `pagePath`, `deviceCategory`, `sessions`, `users`, etc.). It has **no event-level data, no session IDs, and no identifiers.** This is the single most important constraint in the entire roadmap.

| What's computable TODAY | What requires event-level data |
|--------------------------|-------------------------------|
| Daily reach (total users, sessions) | Funnel step-by-step drop-off |
| Page/device engagement rates | Session sequences → "which path leads to completion?" |
| Week-over-week trends | Cohort retention (day 1/7/14/28) |
| Top pages, device split | Questionnaire start/completion counts |
| Anomaly detection on aggregate metrics | Any demographic-stratified analysis |
| Data-quality flags (missing days, row caps) | Person-level linkage to questionnaire/survey |

**Gate 0B must answer:** Do we add an event-level GA4 query? Or accept that v0.5.0 is aggregate-only?

If the answer is "no event-level data," then:
- v0.5.0 (Gate 1) ships ~4 of the 25 analyses (#1, 10, 12, 21 — descriptive reach/pages/devices)
- Gates 2–3 are not buildable from GA4 data alone
- The evidence connector becomes the primary source for outcome data, not GA4

---

## 25 Analyses — Feasibility Matrix

> From `braintree-reqs.md` § Top 25. Feasibility per `ga4-measurement-contract.md` and `🔵 ga4-insights-sketch.md`.

| # | Question | Needs demographics? | Current data | Required gate | Target version | Status |
|---|----------|---------------------|-------------|---------------|----------------|--------|
| 1 | Who is the platform reaching overall? | No | ✅ Aggregate GA4 | Gate 1 | v0.5.0 | Available |
| 2 | Are we reaching priority populations equitably? | Yes | ❌ Needs linkage + demographics | Gate 2 | v0.6.0 | Unavailable |
| 3 | Who completes the questionnaire? | Yes | ❌ Needs event-level data + linkage | Gate 2 | v0.6.0 | Unavailable |
| 4 | Who drops off, and where? | Yes | ❌ Needs event-sequence data + linkage | Gate 2 | v0.6.0 | Unavailable |
| 5 | Does the platform reach intended age groups? | Yes | ❌ Needs linkage | Gate 2 | v0.6.0 | Unavailable |
| 6 | Are women reached and engaged differently? | Yes | ❌ Needs linkage | Gate 2 | v0.6.0 | Unavailable |
| 7 | Are Black users reached and supported effectively? | Yes | ❌ Needs linkage | Gate 2 | v0.6.0 | Unavailable |
| 8 | Are Hispanic/Latino users reached effectively? | Yes | ❌ Needs linkage | Gate 2 | v0.6.0 | Unavailable |
| 9 | Is Spanish-language access functional and used? | Partial | ❌ Needs event-level + linkage (~9 YTD — qualitative only) | Gate 2 | v0.6.0 | Unavailable |
| 10 | Where do users first encounter the platform? | No | ✅ Aggregate GA4 | Gate 1 | v0.5.0 | Available |
| 11 | Which channels bring meaningful users? | Yes | ⚠️ Partial (needs channel dims in query) | Gate 1 | v0.5.0 | Partial |
| 12 | Which search needs bring people to the site? | No | ✅ Aggregate GA4 | Gate 1 | v0.5.0 | Available |
| 13 | What content does each audience need? | Yes | ❌ Needs linkage | Gate 2 | v0.6.0 | Unavailable |
| 14 | Are users finding the right pathway? | Yes | ❌ Needs event-sequence + linkage | Gate 2 | v0.6.0 | Unavailable |
| 15 | Do users understand and act on tailored results? | Yes | ❌ Needs event-data + linkage | Gate 2 | v0.6.0 | Unavailable |
| 16 | Which patterns predict completion? | Yes | ❌ Needs session-level event sequence | Gate 2 | v0.6.0 | Unavailable |
| 17 | Which patterns predict care-seeking? | Yes | ❌ Needs downstream linkage | Gate 2 | v0.6.0 | Unavailable |
| 18 | Are users progressing toward clinical research? | Yes | ❌ Needs event-data + linkage | Gate 2 | v0.6.0 | Unavailable |
| 19 | Where does the research pathway leak? | Yes | ❌ Needs event-sequence + linkage | Gate 2 | v0.6.0 | Unavailable |
| 20 | Do local-resource features lead to action? | Yes | ❌ Needs event-data + linkage | Gate 2 | v0.6.0 | Unavailable |
| 21 | Does the experience work across devices/browsers? | Partial | ✅ Aggregate GA4 | Gate 1 | v0.5.0 | Available |
| 22 | Are users returning for continued guidance? | Yes | ❌ Needs session-level data | Gate 2 | v0.6.0 | Unavailable |
| 23 | Did the March 2026 relaunch improve experience? | Yes | ⚠️ Partial (date unconfirmed; aggregate pre/post possible) | Gate 1 | v0.5.0 | Partial |
| 24 | Does the platform increase awareness/confidence/action? | Yes | ❌ Needs survey data | Gate 3 | v0.7.0 | Unavailable |
| 25 | What actions should be prioritized next? | Yes | ❌ Needs most above analyses | Gate 2+3 | v0.7.0 | Unavailable |

**Summary:** 4 available · 2 partial · 19 unavailable

---

## Immediate Next Action (Gate 0A)

The measurement contract (`ga4-measurement-contract.md`) defines 5 rows. Two are `provisional` (computable today), three are `unavailable`.

**Before v0.4.0 code is written:**

1. Get named approval to move rows 1–2 (daily reach, page/device engagement) from `provisional` → `validated`
2. Confirm exact GA4 event names for questionnaire start/finish (rows 3–5)
3. Decide: do we add an event-level GA4 query, or accept v0.5.0 is aggregate-only?
4. If event-level data is in scope, define the query contract (dimensions, metrics, session identifier, grain)

---

## Document Index

| Document | Purpose | When to read |
|----------|---------|-------------|
| **ROADMAP.md** ← you are here | Version→gate mapping, 25-analysis feasibility | First |
| `braintree-reqs.md` | Client-facing: what questions must we answer | Understanding the "why" |
| `🔵 ga4-insights-sketch.md` | Engineering design for the Insights Engine | Before coding Gate 1 |
| `ga4-measurement-contract.md` | Metric governance: what's valid, what's not | Gate 0A sign-off |
| `🔵 evidence-connector-design.md` | Evidence connector implementation spec | Before coding v0.4.0 |
| `BRAINTREE_CHECKLIST.md` | Task tracker: what's done, what's left | Sprint planning |
| `RELEASE_CHECKLIST.md` | v0.3.0 release gates | Current sprint |
