# GA4 Insights Engine — Design Sketch

> **Status:** 🔵 Sketch — not in any active sprint. Post-v0.3.0 candidate.
> **Cross-refs:** [`🔵 evidence-connector-design.md`](🔵%20evidence-connector-design.md) — demographic data bridge (opt-in survey only).
>
> **Paramount principle:** This engine is **not** "automatic Gemini insights." It is a
> **trust layer** that turns inconsistent web, questionnaire, and survey data into
> auditable, privacy-safe, statistically bounded insight objects that Gemini can
> communicate well. Every surfaced finding must answer: what was measured, how, on
> whom, with what uncertainty, and what action is justified.

---

## What this is

When a user authenticates GA4 in the app, the engine pre-computes validated,
deterministic metrics and surfaces them as **structured insight candidates** with
evidence, uncertainty labels, and provenance. Gemini's job is to prioritize,
explain, question assumptions, and draft recommendations — **not** to calculate,
validate, or test.

---

## Architecture: the trust layer

Gemini should interpret a constrained set of precomputed findings; it should not
be the primary calculator, funnel builder, statistical tester, or data-quality judge.

```
GA4 / Evidence / Survey sources
        ↓
Data normalization + semantic mapping (event → canonical metric)
        ↓
Deterministic metrics + quality tests + privacy/suppression rules
        ↓
Insight candidates with evidence, uncertainty, and provenance
        ↓
Gemini: prioritizes, explains, questions assumptions, drafts recommendations
        ↓
UI: findings, evidence, caveats, drill-down, user feedback
```

This five-layer pipeline means **no raw GA4 event name, page path, or UTM
parameter reaches Gemini without passing through a controlled semantic layer.**

---

## Three-layer measurement model

The engine reasons across three data tiers. GA4 is behavioral context, not the
sole ground truth:

| Layer | Source | What it answers | Join key | When available |
|---|---|---|---|---|
| **GA4 / GTM behavior** | `pull_ga4_report()` → `DataContext` | Acquisition, navigation, engagement, device, events, session funnel | GA4 session ID or anonymous user/session identifier | Immediately on OAuth connect |
| **Questionnaire / Evidence warehouse** | Drive import (v0.3.0) → `DataContext`, evidence connector (future) | Self-reported demographics, health context, user pathway, responses | De-identified session ID and/or questionnaire transaction ID | When evidence connector is live and questionnaire data is loaded |
| **SurveyMonkey follow-up** | CSV import or evidence connector | Awareness change, confidence, satisfaction, care-seeking, barriers | Privacy-approved survey/respondent linkage or cohort-level comparison | Opt-in only; separate cohort |

**Key principle:** GA4 demographic/geographic fields are behavioral context, not a
substitute for race, ethnicity, gender, or other equity variables. Questionnaire
demographics are self-reported and authoritative for equity analysis.

---

## Semantic metric registry (required before implementation)

`DataContext` needs a formal, versioned schema — not a generic container of
reports. The engine cannot reliably infer "funnel," "completion," "action," or
"meaningful engagement" from arbitrary GA4 event names.

Define with the team **before coding begins:**

| Needed object | Example fields |
|---|---|
| Metric definition | `questionnaire_completion_rate`, numerator event, denominator event, event scope, grain |
| Event mapping | Canonical `questionnaire_started` → property-specific `web_questionnaire_start` |
| Funnel specification | Ordered steps, allowed re-entry, time window, same-session vs cross-session rule |
| Action taxonomy | `care_navigation`, `resource_use`, `research_interest`, `contact_intent`, `referral_submitted` |
| Dimension dictionary | Canonical channel, language, device, page category, content topic, user role |
| Data-quality status | Validated, provisional, broken, unavailable, pre/post-incomparable |
| Provenance | Source, query/report ID, date range, refresh time, schema version |
| Interpretation limits | "Intent inferred," "descriptive only," "not causal," "small sample" |

Current GA4 events include repeated questionnaire events, starts, finishes,
tailored-page events, outbound clicks, resource visibility, and form activity —
without an event-level semantic contract, a generic "key event" or click count
can easily be misrepresented as an outcome.

---

## What the engine computes (deterministic, not LLM-reasoned)

When the user authenticates GA4 and data loads successfully, the engine runs a
deterministic analysis pass and stores results in `st.session_state._ga4_insights`.
**Gemini does not perform these calculations.**

### Always computed (GA4 data only, no demographics needed)

| Category | Specific findings |
|---|---|
| **Reach** | Total users, new vs returning, sessions, geography (country/region from GA4), top acquisition channels |
| **Trends** | Week-over-week session change (with incomplete-week handling, annotated interventions), day-of-week patterns |
| **Top pages** | Highest-traffic page paths, grouped by topic where possible; volume-adjusted engagement metrics |
| **Device** | Mobile vs desktop vs tablet split, device-specific engagement patterns |
| **Funnel** | Event-sequence completion rates with deduplication and temporal rules (versioned funnel definition) |
| **Anomalies** | Robust rolling median/MAD deviation flags with minimum-history and volume checks |
| **Retention** | Cohort return rates by acquisition channel (browser/device-based — not person-level) |

### Computed when demographics are available (via evidence connector, opt-in only)

| Category | Specific findings |
|---|---|
| **Equity reach** | Demographic profile of completers vs all users vs agreed benchmark; over/underrepresentation flags |
| **Funnel equity** | Completion and drop-off rates stratified by age, gender, race/ethnicity, language, device, role |
| **Pathway equity** | Which acquisition channels and content paths serve which populations effectively |
| **Intersectional cuts** | Combinations (e.g., women 45–64, Black caregivers) — only where cells pass both count and denominator thresholds |
| **Language access** | Spanish-language page views, starts, completions, resource clicks vs overall; descriptive only at current volume |

---

## AI should not calculate

These findings need deterministic statistical code, not LLM reasoning:

| Current feature idea | Gap | Recommended implementation |
|---|---|---|
| Week-over-week change | No treatment of incomplete weeks, seasonality, campaign launches | Date-completeness check, comparable-week logic, annotated interventions |
| `>2σ` anomalies | Fragile for sparse, seasonal, skewed data | Robust rolling median/MAD or forecasting residuals; minimum history and volume checks |
| Funnel drop-off | No rule for same session, repeat events, re-entry | Versioned funnel definition with deduplication and temporal rules |
| "Best/worst engagement" | Ambiguous; favors low-volume pages | Minimum denominator, confidence interval, traffic-quality flags, topic grouping |
| "3× more likely" | Sounds causal; ignores uncertainty | Relative + absolute difference, sample sizes, confidence intervals, descriptive wording |
| `p < 0.05` equity flags | No test selection, multiple-comparison correction | Statistical service with effect sizes, CIs, correction policy, suppression |
| "Predict completion" | Unspecified: correlation, model association, or causal? | Label as descriptive association; use held-out validation if predictive |

**Example:** a "social landing may have a language barrier" hypothesis should
never appear as a conclusion from observational GA4 patterns alone. The engine
should instead say: *"Spanish-language users had lower observed completion after
social entry; this is an association, with limited sample size, and should be
validated through landing-page review and qualitative feedback."*

---

## Inference labels (required on every insight)

Every surfaced finding carries exactly one inference label. This prevents
overly confident AI language:

| Label | Meaning | Example |
|---|---|---|
| **Observed** | Direct measurement, no comparison | "Completion was 50%." |
| **Associated** | Correlation or statistical relationship, adjusted where possible | "Mobile sessions were associated with lower completion after adjusting for channel and language." |
| **Hypothesis** | Plausible explanation requiring validation | "The mobile questionnaire flow may be contributing to abandonment." |
| **Experiment-supported** | Supported by controlled test | "An A/B test showed the revised flow increased completion." |
| **Not assessable** | Data or linkage insufficient for conclusion | "Care-seeking cannot be attributed because downstream linkage is unavailable." |

---

## Critical connections — the journey framework

The 7 C's are a **journey framework**, not causal chains. GA4 and questionnaire
data can establish ordering and correlation; they rarely establish causation.
The AI should surface connections and flag evidence strength:

1. **Acquisition → Intent:** What channel, campaign, or search query brought the
   user in, and what problem were they trying to solve? *(Intent is inferred; label as hypothesis.)*
2. **Intent → Pathway:** Did the landing page and early navigation route them
   into an appropriate questionnaire or content journey?
3. **Pathway → Completion:** Which interactions precede finishing, and which
   steps produce disproportionate abandonment?
4. **Questionnaire profile → Recommendations:** What self-reported concern,
   diagnosis stage, caregiving role, or location led to which tailored page?
5. **Recommendations → Action:** Did users click local resources, seek a
   provider, view trial information, or submit a referral?
6. **Action → Downstream outcome:** Where possible, reconcile website events
   with contact-center activity, trial matches, referrals (aggregate only,
   de-identified).
7. **Every connection → Equity:** Repeat the pathway for each priority
   population and flag differences with appropriate inference labels.

---

## Cohort definitions (shared denominator for all analysis)

| Cohort | Definition | Source |
|---|---|---|
| **All site visitors** | GA4 users or sessions | `pull_ga4_report()` |
| **Questionnaire starters** | Users with `web_questionnaire_start` event | GA4 events |
| **Questionnaire completers** | Users with `web_questionnaire_finish` event | GA4 events |
| **Action-takers** | Users with a meaningful post-result action (provider finder, local-resource click, trial view, contact form, referral) | GA4 events + action taxonomy |
| **Survey respondents** | Separate, self-selected follow-up cohort | Evidence connector (future) |

---

## Feasibility matrix (required for every proposed analysis)

For each of the 25 target analyses (below), store before implementation:

| Feasibility field | Description |
|---|---|
| **Required grain** | Aggregate daily, event-level, session-level, user-level, or linked questionnaire/session |
| **Required fields** | Exact events, dimensions, and join IDs |
| **Minimum sample** | Denominator threshold and cell threshold |
| **Current availability** | Available, partial, unavailable, or needs instrumentation |
| **Inference type** | Descriptive, comparative, predictive, or causal |
| **Confidence level** | High, moderate, low, or unusable |

Several intended cross-layer analyses must initially be marked **partial/unavailable**
because session persistence of questionnaire demographics remains unresolved.
Page views by device can run from ordinary GA4 aggregates; "which interaction
sequence predicts completion" requires consistent session/event sequence data;
"did tailored recommendations lead to care-seeking?" requires a valid definition
and downstream observation window.

---

## Linkage protocol (required before evidence overlay)

The evidence connector is framed as the demographic bridge, but the design needs
a dedicated linkage specification. Define before Gate 2:

- Stable, de-identified `session_id`, `questionnaire_transaction_id`, and event/session timestamps.
- Source-system timestamp standard, time zone, and allowable time mismatch.
- One-to-one, one-to-many, and unmatched-link handling.
- Linkage success rate: "X% of questionnaire completers were linkable to GA4 behavior."
- A join-coverage table by period, site version, language, and questionnaire version.
- Explicit rule for pre-questionnaire behavior, post-questionnaire behavior, and return sessions.
- A prohibition on joining email/contact records to GA4 unless explicit consent, purpose limitation, and approved governance permit it.

**Demographic persistence across a session is an open technical question.**
The engine must surface this as a **linkage coverage warning** whenever it renders
demographic funnels, rather than burying it in a methodology note.

---

## Data quality gate (automated, runs before insights)

Build a gate that detects quality issues before insight generation begins:

- **Event-volume continuity:** Sudden zeroes, spikes, duplicate firing, renamed events.
- **URL hygiene:** Assets, malformed paths, query-string fragmentation, redirects, `404`, `undefined`, `(not set)` entries.
- **Bot/crawler heuristic:** Anomalous geography/device/engagement combinations, asset-heavy page paths.
- **Reporting completeness:** Partial day, partial week, API sampling/thresholding, delayed processing.
- **Schema drift:** Missing dimensions, altered custom events, changed campaign taxonomy.
- **Pre/post relaunch comparability:** Page/path and event equivalence matrix.
- **Outlier review:** Label suspected instrumentation changes separately from behavioral anomalies.
- **Data freshness:** Source refresh timestamp and period through which data are complete.

The exact relaunch date remains an open item; all trend and before/after logic
must remain blocked until the date and a page/event crosswalk are confirmed.

---

## Measurement validity requirements

The engine must qualify findings against these known concerns:

| Concern | Mitigation |
|---|---|
| **Event taxonomy** | Confirm what counts as a "key event" — current key-event rates appear very high across channels, suggesting the designation may capture routine activity rather than meaningful outcomes |
| **Bot/crawler traffic** | Landing-page reports include asset URLs and anomalous entries that distort engagement findings unless filtered |
| **Pre/post relaunch** | The site was relaunched ~March 2026 in the same GA4 property. Use page path (not title), establish the exact launch date, and analyze equivalent pathways separately before/after |
| **Anonymous vs identified** | Most use is anonymous. Email or contact-center data must not be joined to GA4 absent explicit permission and privacy controls |
| **Retention limitations** | Browser/device-based return measures do not establish person-level longitudinal records |

---

## Survey population separation

Three non-interchangeable populations. The engine must never mix them:

| Population | What it can support | Cannot support |
|---|---|---|
| **GA4 visitors** | Behavior and aggregate reach | Self-reported demographics, awareness change, person-level outcomes |
| **Questionnaire respondents** | Self-reported profile and in-session pathway, if linkage succeeds | Representation of all site visitors without response-rate context |
| **Follow-up survey respondents** (~353 June contacts, not a probability sample) | Reported awareness, confidence, satisfaction, and intended/actual action | Generalized causal claims about all BrainGuide users |

The engine must always present survey response rate, invitation cohort, field
dates, and respondent-vs-invited comparison before reporting outcomes.

---

## Privacy & ethics constraints

- **Demographic data is opt-in only.** No GA4 demographic fields are treated as
  authoritative for race, ethnicity, or gender analysis.
- **The evidence connector** is the **only** path for questionnaire/survey
  demographic data to enter the system.
- **No identified individual data** is sent to Gemini. Prompts contain
  structured evidence objects — not raw rows, PII, or identifiers.
- **Prompt injection protection:** Page titles, paths, UTMs, campaign names,
  search terms, and custom event parameters may contain attacker-controlled or
  malformed strings. Before any text reaches Gemini: normalize/encode untrusted
  labels, never allow source data to define system instructions, use structured
  JSON inputs instead of interpolating raw values into prose, strip or quarantine
  suspicious values, limit field lengths and cardinality, and keep system prompt,
  data context, and user prompt in separate message roles.
- **Survey selection bias** is disclosed: the survey cohort is not a probability
  sample. Response rates, respondent profiles, and generalization limits are
  reported alongside any findings.

---

## Equity analysis gaps

The small-cell rule (`< 10`) is necessary but insufficient. Add:

| Gap | Mitigation |
|---|---|
| **Denominator threshold** | A subgroup can have 10 people but still yield an unstable rate — require minimum denominator for any percentage |
| **Intersectional-combination limit** | Prevent iterative slicing until small cells become identifiable |
| **Complementary suppression** | Hide related totals that allow a suppressed subgroup to be calculated by subtraction |
| **Difference attack protection** | Prevent prompts from requesting two near-identical cuts that reveal a small group |
| **Missingness analysis** | Report who declines demographic questions; self-reported demographics are not representative by default |
| **Benchmark definition** | "Underrepresentation" requires an explicit comparator — service area, campaign audience, expected user population, or another agreed benchmark |
| **Fairness review** | Test whether the model produces stronger recommendations for high-volume populations while systematically treating low-volume priority populations as "insufficient data" |

The Spanish-language segment is currently exceptionally small (~9 year-to-date).
The engine must default to a qualitative/data-collection recommendation, not
comparative performance ranking.

---

## Pre-implementation decisions

These measurement-design questions must be settled **before** building the engine:

1. **What are the 3–5 formal primary outcomes?** Recommended: questionnaire
   completion, tailored-resource action, care-navigation action,
   clinical-research action, self-reported awareness/behavior change.
2. **What is the exact definition of "reaching" a priority population?** Site
   visit, questionnaire start, questionnaire completion, meaningful action,
   or successful downstream connection are different standards.
3. **Which demographic fields are collected, optional, and consistently coded?**
   Confirm race, ethnicity, gender, language, age, ZIP/state, caregiving role,
   and diagnosis/concern stage.
4. **Can a de-identified session ID connect questionnaire records to GA4
   events?** This is the key technical feasibility question.
5. **Which event definitions are trustworthy enough for outcome reporting?**
   Validate event firing, duplicates, key-event configuration, and whether
   clicks represent completed external actions.
6. **What is the official relaunch date and which pathways changed?** No
   unqualified pre/post comparison until this is fixed.
7. **What comparison benchmark will define equitable reach?** Census/
   service-area population, target audience composition, campaign audience,
   or prior-period baseline each answers a different question.
8. **What downstream records can be linked ethically and reliably?** Contact
   center, referral, and research outcomes through approved, minimum-necessary
   de-identified methods only.
9. **How will survey selection bias be handled?** Report response rate,
   respondent profile, and generalization limits.
10. **What reporting thresholds and privacy rules apply?** Establish small-cell
    suppression, aggregation, and role-based access before reviewing
    demographic cuts.

---

## Structured evidence objects (not free-text summary)

Gemini does not receive ad-hoc bullet lists. Every finding is a **structured
evidence object** with explicit fields. Example:

```yaml
insight_id: funnel.questionnaire.v2
statement: "Observed completion was 50.0%."
metric:
  numerator: 500
  denominator: 1000
  unit: users
  cohort_definition: "same-session start-to-finish within 24 hours"
comparison:
  prior_period: 47.1%
  absolute_change_pp: 2.9
  confidence_interval: [46.8, 53.2]
quality:
  status: provisional
  checks: ["event taxonomy validated", "partial current week excluded"]
limitations:
  - "Completion does not indicate downstream care-seeking."
inference_label: observed
provenance:
  source: ga4
  report: funnel_report_v2
  period: "2026-01-01/2026-07-31"
  generated_at: "..."
```

These objects are injected into every chat prompt's system context as a
structured `[insights]` block. Gemini receives only these validated objects —
never raw GA4 event names, page paths, or UTM parameters. The format allows
Gemini to cite a specific insight ID, describe what it knows, disclose what
it does not know, and avoid recalculating. It also makes UI drill-down, audit
logging, evaluation, and future model-provider changes significantly easier.

---

## Insights dashboard (not invisible injection)

The engine is not an invisible auto-analysis pass. It surfaces findings through
an **Insights inbox** or dashboard:

- Finding title, priority, evidence strength, and affected cohort.
- Plain-language explanation plus "Why am I seeing this?"
- Metric definition, denominator, date range, and comparison.
- Caveat badges: small sample, partial data, relaunch break, inferred intent,
  unvalidated event, linkage gap.
- Drill-down to the relevant report/table (no raw PII).
- User controls: save, dismiss, mark inaccurate, investigate, create follow-up question.
- Feedback capture: "useful," "not useful," "wrong because…"
- Recommendation status: proposed, accepted, tested, implemented, outcome unknown.

This turns the engine into a learning workflow rather than a stream of
AI-generated observations.

---

## Operational design

Explicit decisions needed on:

| Area | Requirement |
|---|---|
| **Refresh policy** | OAuth-connect snapshot vs daily refresh vs on-demand; stale-insight labeling |
| **Cost and latency** | Avoid rerunning full analysis and injecting all findings on every chat turn |
| **Caching** | Cache deterministic summaries by property, date range, and schema version — not just `st.session_state` |
| **Multi-property isolation** | Scope every query and cache key to the authenticated GA4 property and workspace |
| **Permission model** | Who can view equity cuts, survey results, linkage diagnostics, and evidence data? |
| **Audit trail** | Store the query, source versions, generated insight IDs, prompt version, model version, and rendered response |
| **Evaluation set** | Build a labeled set of expected findings, non-findings, false-positive traps, privacy cases, and relaunch-break cases |
| **Failure behavior** | If data are incomplete or event taxonomy is unvalidated, the engine must say so and offer a data-quality task — not fabricate a pattern |

---

## Phasing: 4 gates (replacing "post-v0.3.0 candidate")

| Gate | Deliverable | AI role |
|---|---|---|
| **0. Data readiness** | Data dictionary, event taxonomy, relaunch crosswalk, quality checks, metric registry | None or limited explanation |
| *(Gate 1 depends on Gate 0 — the semantic registry must exist before validated metrics can be computed.)* | | |
| **1. GA4 descriptive insights** | Validated trends, channels, pages, device, basic funnels, data-quality alerts | Summarize and prioritize precomputed findings |
| **2. Evidence overlay** | Linkage coverage, demographic completeness, suppression, equity descriptive comparisons | Explain approved aggregates; never infer missing demographics |
| **3. Outcomes and evaluation** | Survey cohort reporting, downstream aggregate outcomes, hypothesis/experiment workflow | Synthesize mixed-method findings and recommend next tests |

Gate 0 is the current blocker: questionnaire demographics are self-reported, the
platform is largely anonymous, and the feasibility of persistent custom
demographic variables is not yet confirmed. Gate 2 requires the evidence
connector to be live and the linkage protocol to be validated.

---

## Top 25 analyses — aspirational use cases

These define the capability target. They are **not** implementation tasks.

| # | Question | Demographics needed? | Current availability | Min. sample concern |
|---|---|---|---|---|
| 1 | Who is the platform reaching overall? | No | ✅ Available | — |
| 2 | Are we reaching priority populations equitably? | Yes | ⚠️ Partial (linkage unconfirmed) | — |
| 3 | Who completes the questionnaire? | Yes | ⚠️ Partial | — |
| 4 | Who drops off, and where? | Yes | ⚠️ Partial | — |
| 5 | Does the platform reach intended age groups? | Yes | ⚠️ Partial | — |
| 6 | Are women reached and engaged differently? | Yes | ⚠️ Partial | — |
| 7 | Are Black users reached and supported effectively? | Yes | ⚠️ Partial | Small cell risk |
| 8 | Are Hispanic/Latino users reached effectively? | Yes | ⚠️ Partial | Small cell risk |
| 9 | Is Spanish-language access functional and used? | Partial (language + questionnaire) | ⚠️ Partial | ~9 YTD — qualitative only |
| 10 | Where do users first encounter the platform? | No | ✅ Available | — |
| 11 | Which channels bring meaningful users? | Yes | ⚠️ Partial | — |
| 12 | Which search needs bring people to the site? | No | ✅ Available | — |
| 13 | What content does each audience need? | Yes | ⚠️ Partial | — |
| 14 | Are users finding the right pathway? | Yes | ⚠️ Partial | — |
| 15 | Do users understand and act on tailored results? | Yes | ⚠️ Partial | — |
| 16 | Which patterns predict completion? | Yes | ❌ Unavailable (needs session-level event sequence) | — |
| 17 | Which patterns predict care-seeking? | Yes | ❌ Unavailable (needs downstream linkage) | — |
| 18 | Are users progressing toward clinical research? | Yes | ⚠️ Partial | — |
| 19 | Where does the research pathway leak? | Yes | ⚠️ Partial | Small cell risk at later steps |
| 20 | Do local-resource features lead to action? | Yes | ⚠️ Partial | — |
| 21 | Does the experience work across devices/browsers? | Partial | ✅ Available | — |
| 22 | Are users returning for continued guidance? | Yes | ⚠️ Partial | — |
| 23 | Did the March 2026 relaunch improve experience? | Yes | ⚠️ Partial (date unconfirmed) | — |
| 24 | Does the platform increase awareness/confidence/action? | Yes (survey required) | ❌ Unavailable | Survey cohort selection bias |
| 25 | What actions should be prioritized next? | Yes | ⚠️ Partial | — |

Of the 25, **~6 are available with GA4 alone** (#1, 10, 12, 21). The remaining
19 need demographics, linkage, or both — and several (#16, 17, 24) are currently
unavailable pending infrastructure or data.

---

## Recommended deliverable structure (when this ships)

1. **Reach and equity profile** — Who used the platform, who completed, which
   groups are under/overrepresented.
2. **Journey and friction** — Acquisition → landing → questionnaire funnel →
   tailored results → drop-off points.
3. **Need-to-resource fit** — Self-reported situation vs content, local
   resources, provider navigation, and research pathways used.
4. **Outcomes and care progression** — Survey-reported awareness/behavior change
   + observed care/research actions.
5. **Relaunch and measurement implications** — Pre/post March 2026 findings
   separated, tracking limitations documented.
6. **Action plan** — Equity-focused content, UX, outreach, and instrumentation
   recommendations ranked by evidence strength and feasibility.

The **first artifact** must be a **data dictionary and linkage map** — each
event, questionnaire field, downstream outcome, its owner, grain, timeframe,
join key, privacy status, and whether it is valid for pre/post-relaunch
comparison.

---

## Definition of done

Do not call the Insights Engine ready when it can write plausible observations.
Call it ready when every surfaced insight can answer:

1. **What exactly was measured?**
2. **What is the numerator, denominator, unit, and date range?**
3. **Which source and event definitions produced it?**
4. **Is the comparison valid across the relaunch boundary?**
5. **What data-quality checks passed or failed?**
6. **What population does it represent — and who is missing?**
7. **Is this descriptive, associated, hypothesized, or experimentally supported?**
8. **What uncertainty, suppression, or privacy constraint applies?**
9. **Can the user inspect the evidence without seeing identifiers?**
10. **What next action is justified, and what would validate it?**
