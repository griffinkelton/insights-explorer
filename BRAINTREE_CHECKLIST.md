# BrainGuide Analytics — Implementation Checklist

> Derived from `braintree-reqs.md` and the GA4 Insights Engine design sketch.
> Each checkbox requires linked evidence: a test result, PR, commit, or review note.

---

## Gate 0: Data Readiness (Next Priority)

| # | Task | Status |
|---|------|--------|
| 0.1 | Define a formal semantic metric registry (event → canonical name mapping) | - [ ] |
| 0.2 | Build event taxonomy audit (bot traffic, malformed URLs, key-event validation) | - [ ] |
| 0.3 | Create pre/post March 2026 relaunch crosswalk (page paths, event equivalence) | - [ ] |
| 0.4 | Add automated data quality gate (URL hygiene, completeness, schema drift, outliers) | - [ ] |
| 0.5 | Build feasibility matrix for all 25 analyses (grain, fields, sample, availability) | - [ ] |
| 0.6 | Add prompt-injection guard: sanitize UTM/campaign/page-path text before Gemini | - [ ] |

---

## Gate 1: GA4 Descriptive Insights (Auto-computed on connect)

| # | Task | Status |
|---|------|--------|
| 1.1 | **Reach**: total users, new vs returning, sessions, top acquisition channels | - [ ] |
| 1.2 | **Trends**: week-over-week change, day-of-week patterns | - [x] `_render_key_insights()` |
| 1.3 | **Top pages**: highest-traffic pages by sessions, best/worst engagement | - [x] `_render_key_insights()` |
| 1.4 | **Device split**: mobile vs desktop vs tablet with metric breakdown | - [x] `_render_key_insights()` |
| 1.5 | **Anomalies**: >2σ deviation days, engagement rate cliffs | - [x] anomaly detection |
| 1.6 | **Retention**: day-1/7/14/28 cohort retention (if GA4 retention data available) | - [ ] |
| 1.7 | **Funnel**: key event start-to-completion rates with step-by-step drop-off | - [x] funnel section |
| 1.8 | **Forecasting**: linear trend projection with AI narrative | - [x] forecast section |
| 1.9 | Pre-compute all insights into `st.session_state._ga4_insights` on data load | - [ ] |
| 1.10 | Inject structured insight block into every Gemini chat prompt | - [ ] |

---

## Gate 2: Evidence Overlay (requires evidence connector)

| # | Task | Status |
|---|------|--------|
| 2.1 | Build evidence connector for questionnaire/survey data | - [ ] |
| 2.2 | Add linkage coverage report (X% of questionnaire completers linkable to GA4) | - [ ] |
| 2.3 | **Equity reach**: demographic profile of completers vs all users vs benchmark | - [ ] |
| 2.4 | **Funnel equity**: completion/drop-off rates by age, gender, race/ethnicity, language | - [ ] |
| 2.5 | **Pathway equity**: which channels/content serve which populations | - [ ] |
| 2.6 | **Language access**: Spanish page views, starts, completions vs overall | - [ ] |
| 2.7 | Enforce small-cell suppression (< 10 individuals) in all demographic cuts | - [ ] |
| 2.8 | Add complementary suppression and difference-attack protection | - [ ] |

---

## Gate 3: Outcomes & Evaluation

| # | Task | Status |
|---|------|--------|
| 3.1 | Survey cohort reporting (awareness, confidence, satisfaction, care-seeking) | - [ ] |
| 3.2 | Dose-response analysis (deeper use → higher reported outcomes) | - [ ] |
| 3.3 | Content-to-outcome mapping (which content themes → next intended action) | - [ ] |
| 3.4 | Campaign evaluation (outreach → qualified completions → downstream action) | - [ ] |
| 3.5 | Return-journey analysis (returning users → provider/resource/trial actions) | - [ ] |

---

## Trust Layer Requirements (Cross-Cutting)

| # | Task | Status |
|---|------|--------|
| T.1 | Every surfaced insight must answer: what was measured, source, date range, limitations | - [ ] |
| T.2 | Label every insight: observed / associated / hypothesis / experiment-supported / not assessable | - [ ] |
| T.3 | Build Insights Inbox/dashboard: title, priority, evidence strength, caveats, drill-down | - [ ] |
| T.4 | Data quality gate runs automatically before insights are generated | - [ ] |
| T.5 | No raw PII, identifiers, or small-cell data sent to Gemini | - [x] |
| T.6 | Audit trail: query, source versions, insight IDs, prompt version, model version, response | - [ ] |
| T.7 | Failure behavior: when data incomplete/event taxonomy unvalidated, say so — don't fabricate | - [x] |
| T.8 | Refresh policy + stale-insight labeling + caching strategy | - [ ] |

---

## Top 25 Client Questions — Coverage Map

| # | Question | Gate | Status |
|---|----------|------|--------|
| 1 | Who is BrainGuide reaching overall? | 1 | - [ ] |
| 2 | Are we reaching priority populations equitably? | 2 | - [ ] |
| 3 | Who completes the questionnaire? | 2 | - [ ] |
| 4 | Who drops off, and where? | 2 | - [ ] |
| 5 | Does the platform reach intended age groups? | 2 | - [ ] |
| 6 | Are women reached and engaged differently? | 2 | - [ ] |
| 7 | Are Black users reached and supported effectively? | 2 | - [ ] |
| 8 | Are Hispanic/Latino users reached effectively? | 2 | - [ ] |
| 9 | Is Spanish-language access functional and used? | 2 | - [ ] |
| 10 | Where do users first encounter BrainGuide? | 1 | - [ ] |
| 11 | Which channels bring meaningful users? | 2 | - [ ] |
| 12 | Which search needs bring people to the site? | 1 | - [ ] |
| 13 | What content does each audience need? | 2 | - [ ] |
| 14 | Are users finding the right pathway? | 2 | - [ ] |
| 15 | Do users understand and act on tailored results? | 2 | - [ ] |
| 16 | Which patterns predict questionnaire completion? | 2 | - [ ] |
| 17 | Which patterns predict care-seeking? | 2 | - [ ] |
| 18 | Are users progressing toward clinical research? | 2 | - [ ] |
| 19 | Where does the research pathway leak? | 2 | - [ ] |
| 20 | Do local-resource features lead to action? | 2 | - [ ] |
| 21 | Does the experience work across devices/browsers? | 1 | - [ ] |
| 22 | Are users returning for continued guidance? | 2 | - [ ] |
| 23 | Did the March 2026 relaunch improve the experience? | 2 | - [ ] |
| 24 | Does BrainGuide increase awareness/confidence/action? | 3 | - [ ] |
| 25 | What actions should be prioritized next? | 2 | - [ ] |

**6 of 25 answerable with GA4 alone** (#1, 10, 12, 21, plus partial #5, #9).
The remaining 19 require demographic data from the evidence connector (Gate 2).

---

## Immediate Next Steps

1. **Gate 0.1-0.4**: Build the data quality gate — URL hygiene, bot detection, event taxonomy audit
2. **Gate 1.9**: Pre-compute all GA4 insights into `st.session_state._ga4_insights` on connect
3. **Gate 1.10**: Inject structured insight block into every Gemini chat prompt
4. **Gate T.3**: Build the Insights dashboard/inbox UI
