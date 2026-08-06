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

> **Cross-reference (2026-08-06):** this sketch is the **deferred GA4 insights-engine workstream** — not part of the React/FastAPI migration's first slice. The prototype's `insights/engine.ts` + `InsightCandidates.tsx` are mock-driven prototypes of this design (quarantined; see `migration/master-plan.md` gate 8). The metric-status consumption policy for `validated` / `provisional` / `unavailable` rows lives in `plans/ga4-measurement-contract.md` (canonical); consult it before any engine calculation below is implemented.

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
| **GA4 / GTM behavior** | `pull_ga4_report()` → `DataContext` | Descriptive reach, pages, devices, aggregate trends. Channels if dimensions are added to the query. *(Event sequences, session funnels, and person-level retention require a new event-level query design — see warning below.)* | **None** in Gate 1. Gate 2 requires a separately approved, de-identified linkage key collected prospectively. | Immediately on OAuth connect |
| **Questionnaire / Evidence warehouse** | Drive import (v0.3.0) → `DataContext`, evidence connector (future) | Self-reported demographics, health context, user pathway, responses | De-identified session ID and/or questionnaire transaction ID | When evidence connector is live and questionnaire data is loaded |
| **SurveyMonkey follow-up** | CSV import or evidence connector | Awareness change, confidence, satisfaction, care-seeking, barriers | Privacy-approved survey/respondent linkage or cohort-level comparison | Opt-in only; separate cohort |

> **Crucial limitation:** `pull_ga4_report()` currently returns **aggregate rows only**
> (`date`, `pagePath`, `deviceCategory`, `sessions`, `users`, etc.). It contains
> **no event-level data, no session IDs, and no identifiers**. The current GA4
> aggregate report is sufficient for descriptive reach, page, device, and aggregate
> trend findings only. Session sequences, retention, funnel progression, and
> questionnaire linkage require a new event-level collection/query design and cannot
> be inferred from the current `DataContext`.

**Key principle:** GA4 demographic/geographic fields are behavioral context, not a
substitute for race, ethnicity, gender, or other equity variables. Questionnaire
demographics are self-reported and authoritative for equity analysis.

---

## Semantic metric registry (required before implementation)

`DataContext` needs a formal, versioned schema — not a generic container of
reports. The engine cannot reliably infer "funnel," "completion," "action," or
"meaningful engagement" from arbitrary GA4 event names.

Define with the team **before coding begins:**

| Needed object | Example fields | Owner |
|---|---|---|
| Metric definition | `questionnaire_completion_rate`, numerator event, denominator event, event scope, grain | Product/engineering + analytics owner |
| Event mapping | Canonical `questionnaire_started` → property-specific `web_questionnaire_start` | Product/engineering + analytics owner |
| Funnel specification | Ordered steps, allowed re-entry, time window, same-session vs cross-session rule | Product/engineering + analytics owner |
| Action taxonomy | `care_navigation`, `resource_use`, `research_interest`, `contact_intent`, `referral_submitted` | Program/evaluation lead |
| Dimension dictionary | Canonical channel, language, device, page category, content topic, user role | Product/engineering + analytics owner |
| Data-quality status | Validated, provisional, broken, unavailable, pre/post-incomparable | Analytics/evaluation owner |
| Provenance | Source, query/report ID, date range, refresh time, schema version | Analytics/evaluation owner |
| Interpretation limits | "Intent inferred," "descriptive only," "not causal," "small sample" | Analytics/evaluation owner |
| Privacy/suppression | Small-cell, denominator, complementary-suppression, difference-attack rules | Privacy/security owner |
| AI prompt/evidence rendering | Structured evidence contract, message-boundary rules | App owner |

**Governance hard rule:** No metric moves from `provisional` to `validated` without
named approval. "Completion," "resource action," and "care-seeking" each carry
different program meanings — the engine must not treat them as interchangeable.

Current GA4 events include repeated questionnaire events, starts, finishes,
tailored-page events, outbound clicks, resource visibility, and form activity —
without an event-level semantic contract, a generic "key event" or click count
can easily be misrepresented as an outcome.

### Required versioned schemas

Four schemas must exist before code touches the engine:

- **`MetricDefinition`** — numerator, denominator, event scope, grain, validation status.
- **`ReportContract`** — source, grain, dimensions, metrics, privacy status, known limitations, truncation behavior.
- **`InsightEvidence`** — structured evidence payload that Gemini receives (see below).
- **`SuppressionDecision`** — reason, rule applied, affected cells, timestamp.

**Minimal `ReportContract` for the current query:**

```yaml
report_id: ga4_page_device_daily_v1
source: ga4_data_api
grain: daily_page_path_device
dimensions: [date, pagePath, deviceCategory]
metrics: [sessions, totalUsers, activeUsers, engagementRate, bounceRate]
privacy_status: aggregate_only
known_limitations:
  - no session identifier
  - no event sequence
  - no demographic linkage
truncation_behavior: hard_cap_500000_rows
```

The current `GA4RequestMetadata` already captures dimensions, metrics, limit, and
truncation — evolve it toward an explicit report contract rather than letting the
insight layer infer capability from a `DataFrame`.

---

## What the engine computes (deterministic, not LLM-reasoned)

When the user authenticates GA4 and data loads successfully, the engine runs a
deterministic analysis pass and stores results in `st.session_state._ga4_insights`.
**Gemini does not perform these calculations.**

### Always computed (GA4 data only, no demographics needed)

These are computable from the current `pull_ga4_report()` aggregate output:

| Category | Specific findings | Notes |
|---|---|---|
| **Reach** | Total users, new vs returning, sessions, geography (country/region from GA4), top acquisition channels | Channel breakdown requires adding channel dimensions to the base query |
| **Trends** | Week-over-week session change (with incomplete-week handling, annotated interventions), day-of-week patterns | Exclude incomplete periods |
| **Top pages** | Highest-traffic page paths, grouped by topic where possible; volume-adjusted engagement metrics | — |
| **Device** | Mobile vs desktop vs tablet split, device-specific engagement patterns | — |
| **Anomalies** | Robust rolling median/MAD deviation flags with minimum-history and volume checks | — |
| **Data-quality flags** | Missing days, anomalous zeroes, suspicious paths, row-cap/truncation status, sampling/thresholding warnings | Runs before any insight generation |

### Deferred: requires event-level data or new query design

These are **not computable** from the current aggregate query and require a
separate event-level collection/query design:

| Category | Why deferred |
|---|---|
| **Funnel** | Event-sequence completion with deduplication and temporal rules — requires event-level data, not aggregate rows |
| **Retention** | Cohort return rates — requires `CohortSpec` querying or session-level data, not derivable from the current date/page/device table |
| **Acquisition analysis** | Requires adding channel/source dimensions to the base query — feasible with a query change, not a data gap |

### Computed when demographics are available (via evidence connector, opt-in only)

All remain blocked until linkage is validated in Gate 0B and the evidence
connector is live:

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

## Threshold handling (three separate controls)

### Hard rule

**If GA4 reports sampling, thresholding, withheld rows, or an incomplete report,
the engine emits a `DataQualityFinding` and does NOT create comparative, equity,
anomaly, or ranking insights from that affected slice.**

### Three distinct controls — never share a generic "low confidence" label

| Control | Source | Behavior |
|---|---|---|
| **GA4 thresholding** | Google has withheld/limited data (e.g., demographics, interests, audience fields) | Emit `DataQualityFinding`; block affected insights |
| **App suppression** | Internal rules: small-cell, denominator threshold, complementary suppression, difference-attack protection | Suppress findings; surface `suppression_reason` not raw counts |
| **Statistical uncertainty** | Valid aggregate estimate is too imprecise to interpret confidently | Show confidence interval; flag as "imprecise" not "unavailable" |

---

## Inference labels (composable, two fields)

Every surfaced finding carries two independent labels. A measurement can be
**observed** while its explanation is a **hypothesis** — these are separate
dimensions:

| `evidence_level` | Meaning | Example |
|---|---|---|
| **observed** | Direct measurement, no comparison | "Completion was 50%." |
| **comparative** | Measured difference between groups or periods | "Completion was 6.2 pp lower on mobile." |
| **associated** | Statistical relationship, adjusted where possible | "Mobile use associated with lower completion after adjusting for channel." |
| **experiment_supported** | Supported by controlled test | "An A/B test showed the revised flow increased completion." |
| **not_assessable** | Data or linkage insufficient | "Care-seeking cannot be attributed." |

| `interpretation_status` | Meaning | Example |
|---|---|---|
| **none** | Pure measurement, no explanation claimed | (Default for observed metrics) |
| **hypothesis** | Plausible explanation requiring validation | "The mobile questionnaire flow may be contributing to abandonment." |
| **action_recommendation** | Specific, evidence-grounded next step | "Review mobile landing page with 3 users; consider simplified layout." |

**Example:** `evidence_level=comparative`, `interpretation_status=hypothesis` →
*"Observed completion was 6.2 pp lower on mobile (comparative). The mobile
questionnaire flow may be contributing to abandonment (hypothesis)."* This
prevents a real measured difference from being downgraded just because its
explanation remains unproven.

---

## Critical connections — the journey framework

The 7 C's are a **journey framework**, not causal chains. GA4 and questionnaire
data can establish ordering and correlation; they rarely establish causation.
The AI should surface connections and flag evidence strength:

1. **Acquisition → Intent:** What channel, campaign, or search query brought the
   user in, and what problem were they trying to solve? *(Intent is inferred;
   `interpretation_status=hypothesis`.)*
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
   population and flag differences with appropriate evidence levels.

---

## Cohort definitions (shared denominator for all analysis)

| Cohort | Definition | Source |
|---|---|---|
| **All site visitors** | GA4 users or sessions | `pull_ga4_report()` |
| **Questionnaire starters** | Users with `web_questionnaire_start` event | GA4 events (requires event-level data) |
| **Questionnaire completers** | Users with `web_questionnaire_finish` event | GA4 events (requires event-level data) |
| **Action-takers** | Users with a meaningful post-result action (provider finder, local-resource click, trial view, contact form, referral) | GA4 events + action taxonomy (requires event-level data) |
| **Survey respondents** | Separate, self-selected follow-up cohort | Evidence connector (future) |

> **Note:** Cohorts defined by GA4 events (starters, completers, action-takers)
> cannot be identified from the current aggregate query. They are aspirational
> definitions awaiting event-level data access.

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

Several intended cross-layer analyses must initially be marked **unavailable**
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
evidence_level: observed
interpretation_status: none
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
provenance:
  source: ga4
  report: funnel_report_v2
  period: "2026-01-01/2026-07-31"
  generated_at: "..."
  analysis_run_id: "run_20260802_001"
  registry_version: "0.1.0"
  quality_gate_version: "0.1.0"
  suppression_policy_version: "0.1.0"
```

**Message-boundary rule:** Evidence objects are supplied as a structured
`data`/`context` message — **not** injected into the system prompt. The system
prompt remains fixed (role, privacy rules, inference-label behavior, response
schema). Gemini receives only objects relevant to the user's current question.
It cites `insight_id`; the UI resolves it to full provenance and drill-down.

Gemini receives only these validated objects — never raw GA4 event names,
page paths, or UTM parameters. The format allows Gemini to cite a specific
insight ID, describe what it knows, disclose what it does not know, and avoid
recalculating. It also makes UI drill-down, audit logging, evaluation, and
future model-provider changes significantly easier.

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

## Phasing: 5 gates

| Gate | Deliverable | AI role | Exit criterion |
|---|---|---|---|
| **0A: Measurement contract** | Metric registry, event dictionary, relaunch crosswalk, primary outcomes, suppression policy, inference labels, governance ownership | None | Stakeholders approve definitions and ownership |
| **0B: Data feasibility** | GA4 API/BigQuery capability inventory, event/session grain decision, linkage prototype, coverage report, data-quality baseline | None | Every proposed Gate 1 metric has documented source/query/grain and status |
| **1: GA4 descriptive insights** | Validated aggregate trends, channels (after query adds dims), pages, device, data-quality alerts | Summarize and prioritize precomputed findings | Gate 0B confirms each chosen insight is actually computable |
| **2: Evidence overlay** | Linkage coverage, demographic completeness, suppression, equity descriptive comparisons | Explain approved aggregates; never infer missing demographics | Privacy review and validated de-identified linkage |
| **3: Outcomes and evaluation** | Survey cohort reporting, downstream aggregate outcomes, hypothesis/experiment workflow | Synthesize mixed-method findings and recommend next tests | Selection-bias protocol and outcome definitions approved |

Gates 0A and 0B are the current blockers: questionnaire demographics are
self-reported, the platform is largely anonymous, and the feasibility of
persistent custom demographic variables is not yet confirmed. The existing
`pull_ga4_report()` is merely **one input** to Gate 0B — it is not the
implicit engine for the entire roadmap. Gate 2 requires the evidence
connector to be live and the linkage protocol to be validated.

---

## Top 25 analyses — aspirational use cases

These define the capability target. They are **not** implementation tasks.

| # | Question | Demographics needed? | Current availability | Min. sample concern |
|---|---|---|---|---|
| 1 | Who is the platform reaching overall? | No | ✅ Available (aggregate only) | — |
| 2 | Are we reaching priority populations equitably? | Yes | ❌ Unavailable (needs linkage + demographics) | — |
| 3 | Who completes the questionnaire? | Yes | ❌ Unavailable (needs event-level data + linkage) | — |
| 4 | Who drops off, and where? | Yes | ❌ Unavailable (needs event-sequence data + linkage) | — |
| 5 | Does the platform reach intended age groups? | Yes | ❌ Unavailable (needs linkage) | — |
| 6 | Are women reached and engaged differently? | Yes | ❌ Unavailable (needs linkage) | — |
| 7 | Are Black users reached and supported effectively? | Yes | ❌ Unavailable (needs linkage) | — |
| 8 | Are Hispanic/Latino users reached effectively? | Yes | ❌ Unavailable (needs linkage) | — |
| 9 | Is Spanish-language access functional and used? | Partial (language + questionnaire) | ❌ Unavailable (needs event-level + linkage) | ~9 YTD — qualitative only |
| 10 | Where do users first encounter the platform? | No | ✅ Available (aggregate only) | — |
| 11 | Which channels bring meaningful users? | Yes | ⚠️ Partial (needs channel dims in query) | — |
| 12 | Which search needs bring people to the site? | No | ✅ Available (aggregate only) | — |
| 13 | What content does each audience need? | Yes | ❌ Unavailable (needs linkage) | — |
| 14 | Are users finding the right pathway? | Yes | ❌ Unavailable (needs event-sequence + linkage) | — |
| 15 | Do users understand and act on tailored results? | Yes | ❌ Unavailable (needs event-data + linkage) | — |
| 16 | Which patterns predict completion? | Yes | ❌ Unavailable (needs session-level event sequence) | — |
| 17 | Which patterns predict care-seeking? | Yes | ❌ Unavailable (needs downstream linkage) | — |
| 18 | Are users progressing toward clinical research? | Yes | ❌ Unavailable (needs event-data + linkage) | — |
| 19 | Where does the research pathway leak? | Yes | ❌ Unavailable (needs event-sequence + linkage) | Small cell risk at later steps |
| 20 | Do local-resource features lead to action? | Yes | ❌ Unavailable (needs event-data + linkage) | — |
| 21 | Does the experience work across devices/browsers? | Partial | ✅ Available (aggregate only) | — |
| 22 | Are users returning for continued guidance? | Yes | ❌ Unavailable (needs session-level data) | — |
| 23 | Did the March 2026 relaunch improve experience? | Yes | ⚠️ Partial (date unconfirmed; aggregate pre/post possible) | — |
| 24 | Does the platform increase awareness/confidence/action? | Yes (survey required) | ❌ Unavailable | Survey cohort selection bias |
| 25 | What actions should be prioritized next? | Yes | ❌ Unavailable (needs most above analyses) | — |

Of the 25, **~4 are available with the current GA4 aggregate query alone**
(#1, 10, 12, 21 — descriptive reach, pages, devices). The remaining 21 need
event-level data, demographics, linkage, or survey infrastructure — and most
are currently unavailable. Several that were previously marked "Partial"
have been downgraded to "Unavailable" because the current `pull_ga4_report()`
returns aggregate rows, not session-level or event-level records.

---

## Immediate next step: measurement contract

Before coding the Insights Engine, create one short companion document:

```
plans/ga4-measurement-contract.md
```

Start with **five rows only:**

1. Daily reach
2. Page/device engagement
3. Questionnaire start
4. Questionnaire completion
5. One meaningful post-questionnaire action

For each of the five, record:

- Exact data source, query/report ID, grain
- Numerator, denominator, event rules
- Validation owner, privacy status, known limitations
- Current feasibility (available, needs query changes, needs event-level data, unavailable)

**Do not start the 25 analyses until these five pass Gates 0A and 0B.**
This turns the sketch from a north-star document into a testable, governed
data product plan.

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
7. **What is the evidence level (observed/comparative/associated/experiment-supported)?**
8. **What uncertainty, suppression, or privacy constraint applies?**
9. **Can the user inspect the evidence without seeing identifiers?**
10. **What next action is justified, and what would validate it?**
