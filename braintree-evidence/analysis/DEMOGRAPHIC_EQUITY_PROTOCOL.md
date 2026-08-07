# BrainGuide Demographic Equity Protocol

> **Status:** Implementation-ready specification; the current Evidence capture is a provisional descriptive snapshot.
> **Companion report:** [`DEMOGRAPHIC_DISPARITY_ANALYSIS.md`](./DEMOGRAPHIC_DISPARITY_ANALYSIS.md)
> **Reproducible snapshot:** [`DEMOGRAPHIC_EQUITY_SNAPSHOT.json`](./DEMOGRAPHIC_EQUITY_SNAPSHOT.json)
> **Calculator:** [`scripts/analyze_demographic_equity.py`](../../scripts/analyze_demographic_equity.py)
> **Coverage audit:** [`DEMOGRAPHIC_EQUITY_COVERAGE.md`](./DEMOGRAPHIC_EQUITY_COVERAGE.md) and [`DEMOGRAPHIC_EQUITY_COVERAGE.json`](./DEMOGRAPHIC_EQUITY_COVERAGE.json), validated by [`scripts/validate_demographic_equity_coverage.py`](../../scripts/validate_demographic_equity_coverage.py)
>
> This protocol is deliberately stricter than the current dashboard evidence. It defines what can be claimed now, what requires new data, and what must happen before a product or outreach intervention is called effective.

## 1. Coverage and decision standard

The coverage matrix is the authoritative answer-status map for the 25 client questions and implementation gates. It is intentionally not a claim that every question is answerable from the current snapshot: a question can be fully specified and still be blocked by missing event-level data, a benchmark decision, privacy approval, or intervention results.


The analysis must answer five separate questions, in order:

1. **Reach:** Who encounters BrainGuide, using a defined eligible visitor benchmark?
2. **Funnel equity:** At which step do groups progress or drop out differently?
3. **Mechanism:** Which product, language, trust, accessibility, or acquisition mechanisms plausibly explain the difference?
4. **Intervention:** Does a specific UX/UI, copy, technical, or outreach change improve the relevant step?
5. **Outcome:** Does improvement persist and lead to a meaningful, safe next action without widening gaps elsewhere?

A race-composition table among scored respondents answers none of these completely. It is a reach signal among a selected population.

### Required inference labels

Every finding must use one label:

- **Observed:** directly reported or deterministically calculated from a named source.
- **Descriptive comparison:** a difference between defined groups with compatible denominators; no causal claim.
- **Associated:** a model-adjusted relationship, with covariates and uncertainty reported.
- **Experiment-supported:** estimated from a prespecified randomized or quasi-experimental comparison.
- **Hypothesis:** plausible mechanism requiring qualitative, instrumentation, or experimental validation.
- **Not assessable:** blocked by missing grain, linkage, denominator, sample, or source validation.

Never use “caused,” “less interested,” “does not trust,” or “under-represented” without the benchmark and design needed to support that wording.

## 2. Estimands and denominators

### 2.1 Reach estimand

For group `g` and benchmark population `b`, use one declared unit throughout the analysis. The preferred web-reach unit is **eligible sessions** only when the benchmark is also session-based; the preferred questionnaire unit is **questionnaire transactions**. Do not compare session shares with person-population shares, call GA4 cookie/device `users` people, or switch between people, users, sessions, and transactions within one comparison. If a person-level population benchmark is required but only session-level reach exists, mark population reach **blocked** rather than mixing units.

For group `g` and benchmark population `b`:

```text
observed_share_g = eligible_BrainGuide_unit_g / eligible_BrainGuide_unit_all
benchmark_share_g = eligible_benchmark_unit_g / eligible_benchmark_unit_all

# `unit` must be identical on both sides (for example, sessions/session benchmark).
representation_ratio_g = observed_share_g / benchmark_share_g
percentage_point_gap_g = observed_share_g - benchmark_share_g
```

A group is not called under-represented until the report records:

- target population and eligibility definition;
- geography and age band;
- date window;
- campaign or service-area scope;
- race/ethnicity coding crosswalk;
- treatment of missing/unknown/refusal;
- benchmark source and version;
- uncertainty method.

**Recommended primary benchmark:** age- and geography-matched ACS 5-year population for the actual service area. Use a campaign-eligible audience for campaign questions and a comparable prior BrainGuide period for product-change questions. Report at least one sensitivity benchmark; never use a national percentage as a universal comparator.

### 2.2 Funnel estimand

The current snapshot does not satisfy this estimand: its demographic rows are downstream displayed rows, while starts and flow KPIs use different populations and date semantics. The calculator therefore reports composition only and blocks completion/drop-off comparisons.

For each group `g` and step `k`:

```text
step_rate[g,k] = distinct_people_reaching_step_k / distinct_people_eligible_for_step_k
step_loss[g,k] = 1 - step_rate[g,k]
absolute_gap[k] = step_rate[priority,k] - step_rate[reference,k]
relative_rate[k] = step_rate[priority,k] / step_rate[reference,k]
```

The default funnel is:

```text
eligible visitor/session
→ landing page
→ questionnaire start
→ each versioned step
→ completed assessment or information path
→ scored result (where applicable)
→ result-page action
→ provider/trial/resource action
```

Rules:

- Use one date field and one cohort window for every step in a comparison.
- Define whether the unit is person, device, session, or questionnaire transaction.
- Deduplicate repeated events according to a versioned rule.
- Define same-session versus cross-session progression and maximum completion window.
- Keep AD8, MIS, SBC, and information-only `c` paths separate.
- Do not use score completion as the denominator for abandonment.

### 2.3 Outcome estimands

Primary product outcomes should be operational and safe:

- successful completion;
- successful recovery after an error;
- result comprehension;
- language-concordant resource access;
- provider/trial/resource action intent;
- optional follow-up awareness or confidence outcome.

A provider or trial click is an observed handoff signal, not an appointment, enrollment, diagnosis, or health outcome.

## 3. Five-phase execution plan

### Phase 1 — Measurement, benchmark, and data readiness

**Goal:** make the denominator and data contract trustworthy before ranking groups.

**Deliverables:**

1. Versioned demographic dictionary. Preserve raw categories; separate race and Hispanic/Latino ethnicity according to the approved standard; preserve multi-select, refusal, skipped, unknown, and not-collected states.
2. Metric registry with numerator, denominator, unit, grain, source, event mapping, date coverage, validation status, and interpretation limits.
3. Relaunch crosswalk for page paths/events, with the exact launch date confirmed by the owner. Do not mix pre- and post-relaunch measures until equivalence is documented.
4. Benchmark decision record using the reach estimand above.
5. Data-quality report covering freshness, partial periods, duplicate grain, URL taxonomy, bot/crawler risk, event drift, and source reconciliation.
6. Linkage feasibility report before any GA4/questionnaire overlay.
7. **Race/ethnicity crosswalk.** The current Results Overview table labels `Hispanic/Latino` as a displayed race row. Before any benchmark ratio, confirm whether rows are mutually exclusive, whether Hispanic/Latino is an ethnicity field or a combined display category, how multi-select `Mixed` is counted, and how the categories map to the selected ACS benchmark. Do not silently reinterpret this display table as OMB/HHS-compliant mutually exclusive race and ethnicity.

**Acceptance gates:**

- No “under-represented” label without a recorded benchmark.
- No funnel rate unless numerator and denominator share source, period, unit, and version.
- No person-level claim from aggregate GA4 and dashboard tables.
- Current Evidence snapshot remains `provisional` because it lacks linked all-user, starter, and completer denominators.

### Phase 2 — Funnel and missingness analysis

**Goal:** locate where the observed composition changes.

**Required cohorts:**

- all eligible visitors/sessions;
- questionnaire starters;
- each major step reached;
- completed information path;
- completed AD8/MIS/SBC assessment;
- scored SBC result;
- result-page action;
- provider/trial/resource handoff.

**Required cuts:** race/ethnicity, language, device, browser, flow, age band, gender, geography, acquisition source, and site version — only when the field is valid at that step.

**Missingness analysis:**

Compare known, refused, skipped, unavailable, and unknown demographic states by device, language, flow, date, acquisition, completion, and error state. Do not use complete-case filtering as the default. Report a missingness sensitivity range:

- **Observed-case:** unknowns excluded from the group denominator.
- **Inclusive:** unknowns retained in the denominator and shown separately.
- **Bounded scenario:** allocate unknowns across plausible group shares only as a sensitivity analysis, never as the primary estimate.

Do not impute race from name, geography, language, or imagery. If a formal imputation is ever considered, it requires a separate ethics/privacy review and must be labeled as modeled, not observed.

**Selection safeguard:** draw a directed acyclic graph before modeling. Demographics, language, device access, acquisition, trust, and eligibility may affect both entering and completing. Conditioning only on scored respondents can create selection/collider bias and survivor bias.

**Acceptance gates:**

- Linkage coverage is reported overall and by period, language, flow, device, and site version.
- A step is not compared by group unless each group has a valid denominator and stable event definition.
- SBC separates permission denied, unavailable hardware, recording failure, upload failure, scoring failure, abandonment, and scored completion.

### Phase 3 — Mechanism validation and community research

**Goal:** determine which explanations are supported rather than inferring them from race gaps.

Use mixed methods:

- moderated usability sessions in English and Spanish;
- cognitive interviews on privacy, stigma, result wording, and consequences;
- accessibility testing with older adults and assistive technology users;
- low-end mobile, tablet, Safari/Chrome, and low-bandwidth testing;
- community advisory review with compensated Black and Hispanic/Latino older adults, caregivers, bilingual users, and trusted messengers;
- review of translated copy by native Spanish speakers from relevant communities;
- technical log review for all funnel errors;
- campaign/partner interviews about audience, referral intent, and message fit.

Pre-register the mechanism map. Example hypotheses:

| Hypothesis | Evidence that would support it | Evidence that would weaken it |
|---|---|---|
| Spanish navigation or translation creates friction | Spanish-specific task errors, language switching, lower task completion after adjustment | Equivalent task success and no language-specific error pattern |
| Mobile/device constraints drive loss | Device-specific technical failures and recovery gains after fix | Gap persists on matched devices after fixing errors |
| Privacy/stigma suppresses entry | Interview/cognitive-test evidence plus improved start rate after transparent copy | No change after copy test and no qualitative concern |
| Acquisition misses priority audiences | Campaign/referral composition and benchmark mismatch | Priority audiences arrive but abandon at a specific step |
| Demographic question creates nonresponse/selection | Nonresponse rises at question and differs by group/flow | No step-specific nonresponse or group difference |

No single interview, click pattern, or literature source proves a BrainGuide mechanism.

### Phase 4 — UX/UI, technical, and copy interventions

**Goal:** improve the earliest avoidable barrier before scaling outreach.

Priority order:

1. Plain, non-diagnostic entry promise and accurate privacy explanation.
2. First-class English/Spanish choice with language persistence across assessment, result, PDF, and handoff.
3. Short mobile/tablet steps, large targets, progress state, keyboard/screen-reader support, captions/transcripts, and low-bandwidth performance.
4. SBC microphone preflight, explicit failure states, retry/recovery, and non-speech fallback.
5. Clear result meaning and next-action choices without implying diagnosis or inevitability.
6. Language-concordant provider/trial/resource destinations.
7. Assisted/non-digital alternatives for people who cannot complete online.

For every intervention, specify:

- target step and eligible population;
- treatment and control experience;
- primary metric and denominator;
- guardrails (error rate, abandonment, comprehension, privacy complaints, adverse effects);
- minimum detectable effect and run window;
- subgroup and intersectional reporting plan;
- stopping rule and owner.

Use randomized experiments when ethically and technically feasible. If not, use interrupted time series or matched-period comparisons with an explicit concurrent control and confounder review. Observational before/after changes are not experiments.

### Phase 5 — Outreach, outcomes, and continuous equity monitoring

**Goal:** test whether product improvements and community distribution produce durable, equitable benefit.

Outreach must be tagged by partner, audience, language, geography, creative, landing page, and target action. Evaluate:

```text
impression/referral
→ landing
→ start
→ progression
→ completion/recovery
→ result/resource action
→ optional downstream outcome
```

Compare outreach cohorts with a pre-specified eligible-audience benchmark and a comparable non-campaign period. Optimize for qualified completion and safe action, not clicks alone.

For follow-up surveys:

- report invited cohort, invitations delivered, response rate, field dates, and respondent-versus-invited composition;
- treat respondents as a self-selected cohort;
- keep awareness, confidence, satisfaction, intended action, and actual reported action distinct;
- do not claim population impact without a credible comparison design.

Monitor quarterly or at each major release, with a named owner, release/date boundary, and review decision:

- representation ratios and absolute gaps;
- step-specific gaps and uncertainty;
- missing/refusal rates;
- language/device/browser error rates;
- intersectional cells where safe;
- resource accessibility and language concordance;
- whether overall averages conceal priority-population regressions;
- implementation fidelity: whether the intervention was actually exposed, language-persistent, technically available, and delivered by the intended partner;
- unintended effects: privacy concerns, result misunderstanding, increased abandonment, or widening gaps for another group.

## 4. Statistical specification

### Minimum reporting

For every rate, report `n/N`, percentage, absolute percentage-point difference, and date range. Add 95% confidence intervals for group rates and differences when the design supports them. Default to Wilson intervals for a single binomial proportion and Newcombe's Wilson interval for an unadjusted difference of two independent proportions. A benchmark comparison must use the benchmark's published uncertainty or a declared design-based interval; do not treat the benchmark point estimate as noiseless without documenting that assumption. For adjusted comparisons, default to logistic regression with average marginal predictions and bootstrap 95% intervals, using a prespecified seed and resampling unit. Do not report a p-value without an effect size and interval. If a denominator is below 50, suppress the rate; if a released cell is below 10, suppress the count as well.

### Modeling

After data quality and linkage are validated:

- Use logistic regression for binary step outcomes, with prespecified covariates such as language, device, flow, age band, acquisition, geography, and site version.
- Report adjusted marginal probabilities and absolute differences, not only odds ratios.
- Consider multilevel models when geography/partner/site clusters are meaningful.
- Use interaction terms or carefully defined intersectional groups for race × language, race × device, and role × flow; do not rely only on additive adjustment.
- Use inverse-probability weighting or sensitivity analysis when selection into the observed cohort is material and the required predictors are measured.
- Correct or control false discovery when many subgroup/step comparisons are explored; label exploratory analyses.
- Do not adjust away mediators when estimating a total access disparity. State whether the estimand is total or direct/conditional.

### Fairness and decision rules

Do not impose demographic parity on clinical screening results. For product access, evaluate equal opportunity to complete, recover from technical failure, understand results, and reach appropriate resources. For score distributions, restrict analysis to instrument validity and measurement-equivalence questions; do not treat subgroup score differences as proof of biological or clinical disparity.

## 5. Privacy and governance

- Minimum released cell: `n >= 10` privacy floor, from repository policy.
- Apply the locked default rate-stability rule used by the reproducible snapshot: do not publish a percentage rate when its numerator is `<10` or its denominator is `<50`; report `n/N` and an interval when both conditions are met. The analytics owner may approve a stricter threshold, but any change must be versioned before analysis. This is a stability rule, not a claim that n=50 guarantees precision.
- Apply complementary suppression to prevent subtraction attacks.
- Restrict repeated slicing of date × race × language × device × campaign combinations.
- Do not expose raw rows, identifiers, emails, exact timestamps, or sparse combinations to an LLM.
- Keep demographic collection optional, purpose-limited, access-controlled, and non-gating.
- Preserve results and resources when users decline demographics.
- Use a de-identified key only after owner/privacy approval; document one-to-one, one-to-many, unmatched, timestamp, and pre/post-questionnaire rules.
- Store proprietary extracts only through the approved local staging policy; never in Git, browser storage, logs, or ordinary AI prompts.
- Retain an audit record of source versions, metric versions, suppression policy, analysis code version, model version, and reviewer approval.

## 6. Current evidence disposition

| Claim | Current status | What unlocks it |
|---|---|---|
| White/Black/Hispanic displayed-row composition | **Supported, descriptive** | Current PDFs and reproducible snapshot calculator |
| Population-level Black or Hispanic under-representation | **Blocked** | Defined benchmark + all-eligible denominator + compatible coding |
| Completion/drop-off by race/ethnicity | **Blocked** | Early demographic context + event-level linkage + shared funnel contract |
| Spanish functional equivalence | **Partial, hypothesis-generating** | Same-flow Spanish starts, completions, errors, resource actions |
| SBC demographic equity | **Blocked** | Failure-state events + early demographic context + device linkage |
| Cause of the White-heavy respondent profile | **Not assessable** | Phase 2 funnel and Phase 3 mixed methods |
| UX/copy intervention effectiveness | **Not assessable** | Phase 4 controlled evaluation |
| Outreach effectiveness | **Not assessable** | Tagged campaigns + benchmark + comparable control |
| Awareness/confidence/behavior change | **Not assessable** | Approved follow-up design with response-bias analysis |

## 7. Exact next inputs

To move from provisional descriptive analysis to a defensible disparity study, obtain:

1. Owner-approved benchmark population, geography, age eligibility, and date window.
2. Exact questionnaire demographic schema and coding/version history.
3. Event-level GA4 export or query with stable pseudonymous session/transaction key, timestamps, event parameters, device, browser, language, flow, and site version.
4. Start/step/finish/error event definitions and deduplication rules.
5. SBC technical failure telemetry.
6. Approved linkage feasibility and coverage extract, including unmatched reasons.
7. Exact relaunch date and page/event crosswalk.
8. Campaign/referral taxonomy and partner audience definitions.
9. Privacy/ethics approval for early optional demographic collection and community research.
10. Prespecified intervention metric owners, experiment windows, and guardrails.

Until these inputs exist, the current report is appropriately a high-value descriptive equity risk assessment—not a population disparity, causal, or outcome evaluation.
