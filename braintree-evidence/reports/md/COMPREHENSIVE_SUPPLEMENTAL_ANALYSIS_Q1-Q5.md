# BrainGuide Supplemental Analysis: Reach, Equity, Pathways, Learning, and Care Progression

> **Prepared:** 2026-08-07
> **Evidence snapshot:** canonical dashboard package captured 2026-08-06, with report-specific freshness dates through 2026-08-04; supplemental GA4/equity material pulled or prepared 2026-08-07
> **Status:** comprehensive supplemental report; provisional, descriptive, and audit-oriented
> **Confidentiality:** internal evaluation material. Do not publish, train models on, or combine with identified respondent, provider, contact-center, or clinical records without approved governance.

## Executive conclusion

BrainGuide is reaching a substantial audience and is generating measurable movement from paid acquisition into brain-health, questionnaire, result, provider, and clinical-trial content. The current evidence also shows a pronounced composition imbalance among people who disclose demographics in the questionnaire: White/Caucasian respondents account for 77.9% of displayed race rows, compared with 4.5% Black/African American and 4.9% Hispanic/Latino. Women account for 70.1% of displayed gender rows, and 54.5% of displayed age rows are 65 or older. These are important signals about the population represented in the available questionnaire evidence, but they are **not yet population-level reach or disparity estimates** because race/ethnicity is observed after questionnaire participation, the all-visitor/start denominator is unavailable, the race taxonomy is not yet reconciled to an approved benchmark, and missingness is material.

The strongest product finding is not a demographic causal explanation. It is a **pathway and measurement opportunity**:

- The platform has high traffic but is heavily dependent on paid acquisition: approximately 91.5% of 2026 YTD sessions in one GA4 traffic pull came from Cross-network, Display, and Paid Search.
- Spanish-browser-language traffic is meaningful and overwhelmingly mobile: approximately 16,905 sessions, with about 91% on mobile in the 2026-01-01–2026-08-06 supplemental pull. Browser language is not Hispanic/Latino identity, but the contrast with the very small Spanish questionnaire-completion capture is a useful access signal.
- Questionnaire flow evidence shows severe aggregate leaks, including an inferred 98% loss at AD8 step `W-B-AD-9`, 51% at SBC `W-S1`, 89% at SBC `W-D4-A-SBC`, and approximately 48% at an early branch step. These are event-volume gaps, not confirmed individual abandonment or causal UX diagnoses.
- Users who reach result pages do take next-step actions. In the captured 90-day result-page table, Poor-labeled English result-page rows produced provider-click actions at 10.5% (76/725 recorded actions) versus 3.2% (73/2,290) for Good-labeled rows, an observed action-rate ratio of about 3.3×. These are **recorded action events, not unique users**, and represent **Good/Poor result-label proxy groups rather than a validated moderate/high-concern cohort**. This is handoff intent, not confirmed care-seeking.
- The package cannot answer whether BrainGuide increases awareness, understanding, confidence, or attitudes, and it cannot estimate what proportion of moderate/high-concern users obtain care. No approved follow-up outcome data, appointment confirmation, provider-side data, trial enrollment data, or consented longitudinal linkage is present.

The recommended strategy is therefore to improve the experience first at the points where the data already indicate friction—especially speech recording, informant flow, mobile interaction, language persistence, result-page action clarity, and campaign-to-landing-page fit—while building the measurement and privacy layer required to determine whether those changes improve equity and real-world outcomes.

## Direct answers to the five priority questions

| Question | Best supported answer now | Evidence status | What would make the answer definitive |
|---|---|---|---|
| **Q1. To what extent is BrainGuide reaching and equitably serving diverse populations, including women, Black, and Hispanic communities, and users across age, geography, and concern level?** | BrainGuide reaches a large, nationally distributed digital audience, but the available questionnaire evidence is disproportionately White, female, and older. Black and Hispanic/Latino respondents are present but small relative to provisional national reference shares. Spanish-language traffic is substantial and mobile-heavy, while Spanish questionnaire/result-action capture is much smaller. Equitable reach across the full visitor and start funnel is not yet measurable. | **Observed + partial / associated; not a population-level equity estimate.** | A service-area and eligibility-matched benchmark, race/ethnicity crosswalk, all-visitor/start denominator, event-level linkage, demographic funnel cuts, language QA, and small-cell-safe intersectional reporting. |
| **Q2. To what extent does the platform prompt action, including questionnaire completion, information-seeking, or discussing concerns with a provider?** | The platform prompts measurable digital actions: questionnaire starts and scored results, result-page PDF/email actions, provider-finder visits/clicks, and clinical-trial outbound clicks. Provider and trial clicks are observed handoff intent. Provider discussion, appointment booking, attendance, and care completion are not measured. | **Observed for digital actions; not assessable for actual provider discussion or care.** | Stable event definitions, same-session funnel logic, explicit CTA events, follow-up survey questions, and approved referral/provider outcome linkage. |
| **Q3. Where do users move forward, stall, or disengage from engagement to care?** | Forward movement is visible from paid acquisition to landing pages, questionnaire branches, result pages, provider/trial pages, and outbound handoffs. Stalls/leaks are concentrated in early branching, the AD8 informant flow, and SBC recording. A high homepage page-view exit rate is a page-sequence signal, not proof of disengagement. | **Observed aggregate pathway; partial causal interpretation.** | Raw event-level export, deduplicated session/person rules, explicit abandonment/error events, page/event crosswalk across the relaunch, and demographic/language/device funnel cuts. |
| **Q4. To what extent does BrainGuide influence awareness, attitudes, and understanding of cognitive health?** | Current data show exposure, content consumption, questionnaire use, result actions, and handoff intent. They do not show pre/post awareness, knowledge, attitudes, confidence, comprehension, or causal influence. | **Not assessable as an outcome; behavioral proxies only.** | An approved baseline/follow-up or comparison-cohort survey with validated items, response and nonresponse analysis, and qualitative comprehension/usability work. |
| **Q5. What proportion of users, particularly moderate/high-concern users, go on to seek clinical care?** | The current package supports a partial intent-tier answer: Poor-labeled result-page rows clicked “Locate a Healthcare Provider” at 10.5% (76/725) versus 3.2% (73/2,290) for Good-labeled rows in an English-only 90-day capture. It does not show appointments, discussions, attendance, treatment, or clinical-trial enrollment, so actual care-seeking is not estimable. | **Observed handoff intent; clinical care outcome not assessable.** | Concern-level-to-session linkage, explicit provider-discussion/appointment survey outcomes, and consented provider/referral/trial records with a defined observation window. |

## 1. Scope, source hierarchy, and interpretation rules

### 1.1 Sources used

This report layers the following material rather than treating every file as equally authoritative:

1. **Requirements and decision framework**
   - [`braintree-reqs.md`](../../../braintree-reqs.md): 25 client questions, three-layer measurement model, recommended cohort definitions, critical joins, privacy boundaries, and missing-input requirements.
   - [`BRAINTREE_CHECKLIST.md`](../../../BRAINTREE_CHECKLIST.md): Gate 0 data readiness, Gate 1 descriptive GA4 insights, Gate 2 evidence overlay, Gate 3 outcomes/evaluation, and cross-cutting trust-layer requirements.
2. **Canonical evidence package**
   - [`CONSOLIDATED.md`](../../CONSOLIDATED.md) and [`CONSOLIDATED.json`](../../CONSOLIDATED.json): semantic registry and definitions for the 16 dashboard captures and journey explorer.
   - [`DEMOGRAPHIC_DISPARITY_ANALYSIS.md`](../../analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md): prior reviewed disparity analysis, external literature, mechanisms, conclusions, and UX-first recommendations.
   - [`DEMOGRAPHIC_EQUITY_PROTOCOL.md`](../../analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md): measurement, intervention, outcome, suppression, and inference-label protocol.
   - [`DEMOGRAPHIC_EQUITY_COVERAGE.md`](../../analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md): question/gate status map.
3. **Captured dashboard reports**
   - Results Overview, User Journeys, Questionnaire Explorer/Journey Explorer, Result Pages, Clinical Trials, Find a Provider, Top Content, Top Content by Demographic, AD8, MIS, SBC, Scoring Reference, Result Sharing, and Site Events under [`../../reports/md/artifacts/`](../../reports/md/artifacts/).
4. **New supplemental material in `additional/`**
   - [`braintree-ga4-equity-supplement.md`](../../additional/braintree-ga4-equity-supplement.md): language × device and acquisition-channel GA4 cuts.
   - [`BrainGuide Equity Protocol — Phases 2–5 Execution Memo.md`](../../additional/BrainGuide%20Equity%20Protocol%20%E2%80%94%20Phases%202%E2%80%935%20Execution%20Memo.md): provisional benchmark, funnel, leak, campaign, and unlock analysis.
   - [`md.md`](../../additional/md.md): SOW reconciliation, mechanism research, and concern-level-to-resource-action cross-tab.
   - [`site-traffic-overview.md`](../../additional/site-traffic-overview.md): YTD traffic, acquisition, landing-page, year-over-year, and data-quality analysis.
   - [`google-analytics-report.md`](../../additional/google-analytics-report.md), [`research-conversation.md`](../../additional/research-conversation.md), and [`master-perplexity-conversation.md`](../../additional/master-perplexity-conversation.md): provenance/context only, not canonical metric sources. These raw/internal records are linked for repository traceability only and must be access-controlled or removed before any client/external distribution.
   - CSV extracts: [`race_benchmark_table.csv`](../../additional/race_benchmark_table.csv), [`funnel_table.csv`](../../additional/funnel_table.csv), [`leak_table.csv`](../../additional/leak_table.csv), and [`campaign_table.csv`](../../additional/campaign_table.csv).
5. **External and official research**
   - Peer-reviewed and public sources listed in [Section 10](#10-external-research-and-how-it-applies).
   - Official Google Analytics documentation listed in [Section 11](#11-ga4-measurement-implications).

### 1.2 Inference vocabulary

Every conclusion in this report uses one of the following labels:

- **Observed:** directly represented in a captured table, event inventory, or derived calculation with a stated denominator.
- **Associated:** two observed characteristics occur together; the evidence does not establish cause.
- **Hypothesis:** a plausible mechanism that should be tested through QA, qualitative research, instrumentation, or controlled intervention.
- **Experiment-supported:** a change produced a measured difference under a credible comparison or experiment. No BrainGuide finding in this package currently reaches this status.
- **Not assessable:** the required source, denominator, linkage, or outcome does not exist in the current package.

### 1.3 Core denominator rule

A “visitor,” “session,” “questionnaire starter,” “scored respondent,” “result-page action,” and “survey respondent” are different units. They must not be substituted for one another.

The minimum reporting header for every future metric is:

```text
population / unit / numerator / denominator / date window / source / definition /
inference label / limitations
```

### 1.4 Coverage of all new `additional/` material

All 23 pre-existing artifacts in `braintree-evidence/additional/` were reviewed for role, provenance, authority, and sensitivity. Only the items marked **quantitative synthesis** contribute numbers to this report; presentation, prompt, and conversation artifacts were used as context and cross-checks rather than independent sources.

| Artifact(s) | Treatment in this report |
|---|---|
| `braintree-ga4-equity-supplement.md` | Quantitative synthesis: language/device and acquisition-channel context |
| `BrainGuide Equity Protocol — Phases 2–5 Execution Memo.md` | Quantitative synthesis: interim benchmark, funnel, leak, and unlock status |
| `md.md` | Quantitative synthesis: Q5 action-event proxy and coverage reconciliation |
| `site-traffic-overview.md` | Quantitative synthesis: YTD traffic, landing, year-over-year, and data-quality caveats |
| `google-analytics-report.md` | Context/provenance only; not a clean metric source |
| `research-conversation.md` | Context/provenance only |
| `master-perplexity-conversation.md` | Raw confidential provenance only; never a source of truth; external sharing requires review |
| `race_benchmark_table.csv` | Quantitative synthesis: interim displayed-row benchmark extract |
| `funnel_table.csv` | Quantitative synthesis: selected aggregate step-volume gaps |
| `leak_table.csv` | Quantitative synthesis: severe aggregate leak extract |
| `campaign_table.csv` | Context/cross-check: campaign completion extremes; not used for causal claims |
| `Yourquestion-Existingcoverage-Gap.csv` | Context: maps the five SOW questions to coverage gaps |
| `Checklistitem-StatusinBRAINTREECHECKLISTmd-WhatmyG.csv` | Context: supplemental-to-checklist crosswalk |
| `braintree-deep-research-prompt.md` | Planning/provenance: superseded foundational research prompt |
| `braintree-deep-research-prompt-v2.md` | Planning/provenance: preferred latest research prompt |
| `braintree-deep-research-prompt-v2 (1).md` | Planning/provenance: earlier v2 draft, superseded |
| `ga4-overview.html` | Presentation-only; claims require source verification |
| `ga4-narrative-deck.slides.html` | Presentation-only; claims require source verification |
| `ga4-executive-narrative-deck (3).html` | Presentation-only; substantive executive deck export |
| `ga4-overview.pptx` | Presentation-only; claims require source verification |
| `mybrainguide_ytd_2026_vs_2025.pdf` | Presentation-only one-page comparison |
| `ga4-executive-narrative-deck.html` | Placeholder/stub; excluded from analysis |
| `ga4-executive-narrative-deck (2).html` | Placeholder/stub; excluded from analysis |

The folder README remains the authoritative index for archive handling and the parent package remains authoritative for semantic definitions.

## 2. Q1 — Reach and equitable service

### 2.1 Overall digital reach and acquisition

**Observed.** One YTD traffic pull for 2026-01-01 through 2026-08-06 reports approximately 369,900 sessions, 1.02 million page views, and 348,526 engaged sessions. The source’s channel table reports:

| Channel | Sessions | Share of reported sessions | Engagement rate |
|---|---:|---:|---:|
| Cross-network | 183,055 | 49.5% | 96.2% |
| Display | 94,137 | 25.5% | 93.9% |
| Paid Search | 61,100 | 16.5% | 94.7% |
| Direct | 11,198 | 3.0% | 75.0% |
| Organic Search | 8,383 | 2.3% | 89.7% |
| Unassigned | 7,162 | 1.9% | 86.2% |
| Referral | 4,216 | 1.1% | 85.5% |

Cross-network, Display, and Paid Search together account for 338,292 sessions, or 91.5% of the reported total. **Inference label: observed.**

**Interpretation.** BrainGuide is reaching many users, but its reach is structurally dependent on paid media and its targeting/configuration. That is both an opportunity and an equity risk: paid campaigns can intentionally support priority-population reach, but high aggregate engagement can conceal a mismatch between campaign audience, landing-page promise, questionnaire completion, and downstream action.

**Data-quality caution.** Another supplemental GA4 pull for the same broad period reports approximately 373,000 sessions and slightly different channel totals. These are not necessarily contradictory—pull timing, report filters, property processing, and connector definitions may differ—but they must be reconciled before a single headline is published. The 43.0% to 94.2% year-over-year engagement-rate change in the traffic overview is especially unsafe to interpret as a behavioral improvement until event, consent, and engagement definitions are audited.

### 2.2 Who appears in the questionnaire evidence?

The Results Overview capture reports the following YTD questionnaire snapshot:

- **Started:** 93,203.
- **Received a score:** 72,419.
- **Rendered score completion rate:** 77.7%.
- **Race recorded:** 75% of the relevant displayed population.
- **Gender recorded:** 79%.
- **Age recorded:** 77%.
- **Female:** 39,889 (70.1% of displayed gender rows).
- **Male:** 14,740 (25.9%).
- **Under 45:** 6,721 (12.1% of displayed age rows).
- **65–74:** 16,342 (29.4%).
- **75 and older:** 13,943 (25.1%).
- **65 or older combined:** 30,285, or 54.5% of displayed age rows.
- **White/Caucasian:** 42,556 (77.9% of displayed race rows).
- **Black/African American:** 2,433 (4.5%).
- **Hispanic/Latino:** 2,675 (4.9%).
- **Prefer not to answer:** 3,074 (5.6%).

**Inference label: observed composition of displayed questionnaire rows.** The display rows are not the full site audience. Demographics apply only after the relevant questionnaire stages, and the current capture does not show race/ethnicity at acquisition, questionnaire start, each step, or result action. The rows also require a validated race/ethnicity crosswalk before comparison with an external benchmark.

### 2.3 Interim benchmark signal for Black and Hispanic/Latino populations

The supplemental execution memo uses a 2023 national ACS reference as an interim benchmark:

| Group | Displayed questionnaire rows | Observed share | Interim national reference | Provisional representation ratio |
|---|---:|---:|---:|---:|
| White/Caucasian | 42,556 | 77.90% | 57.22% | 1.36 |
| Black/African American | 2,433 | 4.45% | 11.64% | 0.38 |
| Hispanic/Latino | 2,675 | 4.90% | 19.55% | 0.25 |

The ratios are calculated as displayed-row share divided by the reference share. The interim reference values are reproduced from the execution memo and should be treated as **memo-provided provisional references**, not as independently recomputed values in this report. The appropriate official comparison source is the U.S. Census Bureau **2023 ACS 5-year national table B03002, Hispanic or Latino Origin by Race**, universe “Total population,” geography United States ([data.census.gov table B03002](https://data.census.gov/table/ACSDT5Y2023.B03002?g=010XX00US); [official B03002 variable metadata](https://api.census.gov/data/2023/acs/acs5/variables/B03002_003E.json)). The exact benchmark percentages must be recomputed from the selected ACS product, universe, mutually exclusive coding, and numerator/denominator definitions before publication. They are **not population-level estimates of BrainGuide reach**. The comparison is provisional because:

1. the platform’s displayed race rows are self-reported and not a clean mutually exclusive OMB/HHS race-plus-ethnicity crosswalk;
2. the denominator is questionnaire demographic rows, not all eligible visitors, starters, or campaign-reached people;
3. BrainGuide’s service area and intended age/role mix may differ from the national population;
4. missingness and “prefer not to answer” are not random by assumption; and
5. the captured questionnaire population includes self-takers and informants, which should not automatically be benchmarked identically.

**Conclusion — Q1 Black and Hispanic/Latino reach:** **Observed and important, but not yet definitive.** Black and Hispanic/Latino respondents are markedly smaller shares of the available questionnaire evidence than the interim national reference. The evidence supports prioritizing access and recruitment work; it does not establish whether the gap originates in media reach, landing-page fit, trust, language, questionnaire start, step friction, demographic disclosure, or the benchmark itself.

### 2.4 Spanish-language access is a separate but related signal

The GA4 equity supplement reports approximately 16,905 Spanish-browser-language sessions in the 2026-01-01–2026-08-06 pull, around 4.5% of that pull’s sessions. Approximately 91% of Spanish-browser-language sessions were mobile. The Top Content capture reports 28,531 Spanish pageviews, or 5.5% of pageviews in its May 7–August 4 90-day window.

The same package reports much smaller Spanish volumes in downstream questionnaire/resource captures. These figures must not be read as one sequential funnel because they come from different reports, windows, units, and cohorts:

| Source/report | Window | Unit | Spanish value | Interpretation |
|---|---|---|---:|---|
| GA4 equity supplement | 2026-01-01–2026-08-06 | browser-language sessions | ~16,905 | Aggregate traffic context |
| Top Content | 2026-05-07–2026-08-04 | pageviews | 28,531 | Aggregate content consumption |
| Find a Provider | 2026-05-07–2026-08-04 | page visits / outbound clicks | 194 / 5 | Feature-level handoff context |
| Clinical Trials | 2026-05-07–2026-08-04 | page visits / outbound clicks | 5,972 / 347 | Feature-level handoff context |
| Top Content by Demographic | 2026-06-06–2026-08-04 | self-reported demographic-slice pageviews | 132 clinical-trial; 85 community; 71 provider | Selected post-questionnaire slice |

No row above is a Hispanic/Latino identity count or a complete language funnel.

**Observed.** Spanish-browser-language traffic is not negligible and is mobile-heavy. **Observed.** Spanish downstream volumes vary substantially by feature. **Not assessable.** These figures do not establish Hispanic/Latino identity, language preference, comprehension, functional equivalence, or care outcomes.

**Important interpretation:** The gap between Spanish-browser-language traffic and Spanish questionnaire/result-action capture is a useful measurement and access signal, not proof of a Spanish UX failure. It could reflect browser language not matching user preference, mixed-language households, campaign composition, anonymous users not completing demographics, incomplete language persistence, questionnaire instrumentation, or genuine task friction. It should trigger a language-persistence and task-completion audit.

### 2.5 Gender, age, geography, and concern level

#### Women

**Observed.** Women comprise 70.1% of displayed gender rows. The platform therefore has strong reach into women who disclose gender in the questionnaire. The current data do not show whether women are overrepresented at initial acquisition, whether men drop out earlier, whether campaign targeting differs, or whether women have different provider/trial action rates.

**Hypothesis.** Women may be more likely to engage with caregiving, prevention, or health-information pathways, but the current evidence cannot distinguish social role, campaign targeting, age, caregiving status, or access effects. This should be tested with start-to-score and result-action rates by gender, not explained from completion rows alone.

#### Age

**Observed.** The available questionnaire population is older-skewing: 54.5% of displayed age rows are 65 or older, while 12.1% are under 45. This may be appropriate for a platform centered on cognitive health and caregivers, but BrainGuide also describes a broad audience. The current evidence cannot determine whether younger people are less reached, less interested, less likely to disclose age, or routed into a different campaign/pathway.

**Recommendation.** Report two distinct views: (a) all-age reach and task completion, and (b) an agreed older-adult/caregiver service-area benchmark. Do not use one age distribution to judge both objectives.

#### Geography

The evidence package includes country/geography reports and traffic by landing/channel, but the current report set does not provide a validated state/metro/rurality denominator tied to eligible population, provider availability, campaign targeting, or questionnaire outcomes. Geography can describe where traffic occurs; it cannot by itself establish equitable access or care availability.

**Needed:** state/ZIP3 or metro geography under an approved privacy rule; rurality proxy; campaign/service area; local provider/trial availability; and downstream resource/action rates. Avoid publishing small-area cells.

#### Concern level

The questionnaire evidence shows distinct populations and scoring systems:

- **AD8:** informant/caregiver or family-member flow; 0–1 Good, 2–8 Poor; 47.4% High Concern (5–8) in the all-time AD8 capture.
- **MIS:** self-administered memory screen; 5–8 Good, 0–4 Poor; 79.7% Good in the all-time MIS capture.
- **SBC:** self-administered speech-based flow; Low/Medium/High Risk tiers; 1,751 scored completions from 36,803 flow entries in the captured report, approximately 4.8% entry-to-score based on those displayed totals.

These cannot be compared as if they measured the same population. AD8 concerns an informant’s report about another person; MIS is a self-memory task; SBC has a severe pre-score attrition problem and different technical demands. “Good,” “Moderate,” “Poor,” and “High Risk” are product routing categories, not diagnoses.

### 2.6 Q1 action recommendations, starting with UX/UI and copy

1. **Make language a first-class experience, not only a translated page.** Persist language selection across landing page, questionnaire, result page, provider page, trial page, PDF/email, and outbound CTA. Test Spanish and English flows for equivalent content, controls, error states, recording instructions, and CTA destinations.
2. **Design for mobile-first Spanish access.** Prioritize thumb-reachable controls, readable type, low-bandwidth assets, visible progress, short screens, clear audio/recording permissions, and a recovery path when recording fails.
3. **Add an early “What brings you here?” router.** Offer plain-language choices such as “I’m concerned about myself,” “I’m concerned about someone else,” “I want to learn,” and “I’m looking for care.” Make the route and expected time clear before commitment.
4. **Use trust-forward, non-stigmatizing copy.** State who operates the tool, what is and is not stored, that results are not diagnoses, and what happens after a result. Avoid language implying that a concerning score labels a person.
5. **Use campaign-matched landing pages.** Paid creative for Spanish, Black communities, caregivers, and prevention audiences should land on the relevant culturally reviewed content or route, not default to a generic homepage unless that is intentional.
6. **Do not make demographic disclosure feel like a tollgate.** Explain why optional demographic questions are asked, allow “prefer not to answer,” and ensure that useful guidance is available without disclosure.
7. **Recruit through trusted partners while preserving choice.** Test community-based organizations, faith communities, memory clinics, libraries, senior centers, promotor/a networks, and caregiver organizations as distribution partners. Measure qualified starts and useful actions—not traffic alone.
8. **Create a non-digital and assisted path.** Offer printable guidance, phone/support options where appropriate, and caregiver/partner materials so digital access is not the only route to information or referral.

## 3. Q2 — Action prompting and progression toward a next step

### 3.1 Questionnaire and information actions

The Results Overview capture reports 93,203 starts, 72,419 received scores, and a displayed score completion rate of 77.7% under its selected filters. The Scoring Reference documents a `c` flow in which users choose “Get Information” without a scored assessment and receive a result/information route without a score. The current capture does not provide a fully reconciled, event-level split of:

```text
all visitors → questionnaire start → flow selection → scored completion
             → information-only path → result page → CTA action
```

**Conclusion:** The platform clearly prompts questionnaire and information behavior, but the exact completion and information-seeking rates depend on which source, period, and denominator are used. The 77.7% Results Overview figure should not be substituted for the GA4 `web_questionnaire_start` to `web_questionnaire_finish` event ratio because the reports have different filters, grain, and likely legacy inclusion.

### 3.2 Result-page actions

The captured Result Pages report covers May 7–August 4, 2026 and records 3,286 total actions across 12 active result pages. Actions include Save PDF, Email Results, Audio Play, and Locate a Healthcare Provider.

Examples:

- Self · Not Diagnosed · Good: 1,299 Save PDF actions and 528 Email Results actions in the captured rows.
- Self · Not Diagnosed · Poor: 277 Save PDF, 91 Email Results, and 34 provider-location clicks.
- Someone Else · Not Diagnosed · Poor: 60 Save PDF, 56 Email Results, and 18 provider-location clicks.
- Diagnosed and SBC result pages show smaller but sometimes higher action shares; small cells require caution.

The Result Sharing report separately records 3,113 PDF shares, 225 opt-ins to be contacted, and a 7.2% overall opt-in rate under its YTD filters. This is an explicit consent signal, not proof that the email was opened, discussed with a provider, or led to care.

**Conclusion:** Results do prompt information preservation, sharing, audio use, and provider-resource exploration. The next product question is not merely “does a CTA exist?” but whether the CTA is understandable, trusted, accessible, relevant to the result, and completed without avoidable friction.

### 3.3 Provider and clinical-trial handoffs

| Pathway | Visits | Outbound clicks | Observed click-through |
|---|---:|---:|---:|
| Find a Provider, English + Spanish | 16,168 | 1,232 | 7.6% |
| Clinical Trials, English + Spanish | 50,422 | 8,331 | 16.5% |

These are meaningful digital handoff signals. They are not appointments, attendance, treatment, enrollment, or provider discussion. External destination tracking ends at the click in the captured package.

### 3.4 Q2 recommendations

- Replace generic CTA labels with action-specific, expectation-setting language: “Find nearby care options,” “Prepare questions for a clinician,” “Learn what this result can and cannot mean,” and “Explore research opportunities.”
- Place the next step above the fold on result pages, but maintain a non-alarmist choice architecture for Good, Moderate, Poor, and High Risk routes.
- Add a short “why this next step?” explanation and a low-friction alternative such as saving a care-conversation checklist.
- Measure CTA visibility, impression, focus, click, destination load, return-to-BrainGuide, and completion where legally and technically appropriate; do not name a click a conversion unless the outcome is defined.
- Provide Spanish-equivalent CTA destinations and verify that external providers/trial pages retain language and context where possible.
- Test whether users can identify the difference between information, screening/routing, and clinical diagnosis after viewing a result.

## 4. Q3 — Where users move forward, stall, or disengage

### 4.1 High-level flow

The YTD traffic overview describes a broad path of paid acquisition → homepage → clinical-trial, community, provider, or result experiences. The User Journeys capture provides a more specific Home-page sequence for June 6–August 4, 2026:

| Home journey measure | Value |
|---|---:|
| Sessions arriving | 64,626 |
| Landed directly | 58,021 (89.8%) |
| Left the site from Home in page-view sequence | 48,300 (74.9%) |
| Next: Maintain Brain Health 1 | 10,220 (15.8%) |
| Next: Address Memory Concerns 1 | 1,836 (2.8%) |
| Next: Clinical Trial Connector | 731 (1.1%) |
| Next: Find a Provider | 114 (0.2%) |

Device-specific Home page-view exit rates were 74.7% mobile, 80.2% tablet, and 62.8% desktop.

**Critical interpretation:** The report explicitly distinguishes this page-sequence exit rate from GA4 bounce/engagement. A user can save a PDF, play audio, fire an outbound click, or complete an in-page questionnaire interaction without creating another page view. Therefore, a Home “exit” is not automatically failure or disengagement.

### 4.2 Questionnaire leaks

The Questionnaire Explorer/Journey Explorer reports aggregate event-volume gaps for July 4–August 4, 2026 and a broader history. The largest observed gaps include:

| Step | Flow | In | Out | Inferred gap | Interpretation status |
|---|---|---:|---:|---:|---|
| `W-A5-A` → `W-A3-B` | early branch | 17,903 | 9,327 | ~47.9% | **Observed volume gap** |
| `W-B-AD-9` | AD8 informant | 19,600 | 369 | ~98% | **Observed volume gap; highest priority investigation** |
| `W-S1` | SBC speech | 35,600 | 17,300 | ~51% | **Observed volume gap** |
| `W-D4-A-SBC` | SBC speech | 16,300 | 1,700 | ~89% | **Observed volume gap** |

The full-history Explorer summary reports 514,561 questionnaire starts, a 34% final-demographic completion rate, 2.1% average step loss, and a 98% worst step loss. These figures do not use the same window or necessarily the same unit as the YTD Results Overview; they must not be combined into one funnel.

### 4.3 Likely mechanisms, stated as hypotheses

The data identify where to investigate, not why the leak occurs. Plausible mechanisms include:

- unclear or threatening copy at a sensitive informant question;
- an unusually long or repetitive sequence;
- loss of trust when asked about diagnosis, demographics, or data use;
- mobile layout, touch-target, keyboard, or viewport problems;
- audio permissions, microphone access, browser support, recording latency, or failure recovery in SBC;
- language persistence or translation mismatch;
- campaign promise not matching the first questionnaire screen;
- event instrumentation failure rather than user abandonment;
- duplicated or non-deduplicated events; and
- different populations entering the AD8, MIS, and SBC flows.

No one of these should be reported as the cause without error logs, replay/QA evidence, qualitative research, or an intervention comparison.

### 4.4 Q3 UX/UI and instrumentation response

**First 30 days — repair and observe**

1. Reproduce `W-B-AD-9`, `W-S1`, and `W-D4-A-SBC` on current mobile, tablet, and desktop browsers in English and Spanish.
2. Add explicit events for screen view, CTA impression, CTA click, validation error, permission prompt, permission denied, recording started, recording failed, recording retried, timeout, back navigation, restart, and completed transition.
3. Add a visible progress indicator with number of steps or an honest range; explain approximate time and the option to pause/save information.
4. Add “I’m not sure” and “Prefer not to answer” where clinically and methodologically appropriate, without making users feel judged.
5. Add a recovery path after an SBC recording failure: retry, switch supported input method if available, or continue to non-speech information without losing progress.
6. Confirm that event-volume gaps are not caused by renamed screens, missing `qCurrent`, duplicate firing, or cross-domain navigation.

**Next 60–90 days — test improvements**

- Randomize or phase a shorter introduction, clearer trust copy, progressive disclosure, and recording guidance.
- Compare completion, error, and action rates by device, language, flow, and campaign with pre-specified minimum denominators.
- Add qualitative intercepts at abandonment-prone screens: “What made you stop?” with privacy-safe response options.
- Use a holdout or stepped-wedge design for trusted-messenger landing pages rather than attributing improvement to partner traffic alone.

## 5. Q4 — Awareness, attitudes, understanding, and influence

### 5.1 What the package can observe

The current package can describe exposure and behavior proxies:

- pageviews and sessions by content category, language, device, channel, and geography;
- content interest, including Clinical Trials, Find a Provider, brain-health hubs, and result pages;
- questionnaire starts, scores, result routing, and page actions;
- PDF shares, email opt-in, audio play, provider clicks, and trial clicks; and
- search queries/landing-page demand where the captured Search Console report is available.

These measures can support statements such as “users reached the information page” or “users clicked the provider resource.” They cannot support “users understood the content,” “attitudes improved,” or “BrainGuide caused care-seeking.”

### 5.2 Why clicks are not awareness outcomes

An awareness outcome requires an outcome measure with a time relation to exposure and a defensible comparison. A pageview may reflect curiosity, accidental loading, campaign targeting, or repeated use. An engaged session is an Analytics construct, not comprehension. A PDF save indicates preservation intent, not reading or understanding. A provider click indicates handoff intent, not care.

The evidence package contains no approved follow-up survey instrument, invitation log, response file, baseline, comparison cohort, or qualitative comprehension study. Therefore:

> **Q4 conclusion: not assessable as an influence question from the current evidence.** The platform demonstrates exposure and action proxies, but no estimate of awareness, attitudes, knowledge, confidence, comprehension, or change attributable to BrainGuide is currently valid.

### 5.3 Recommended outcome design

Use a short, accessible, multilingual follow-up design with three distinct populations:

1. **All invited users:** denominator for response and nonresponse reporting.
2. **Responding BrainGuide users:** self-reported experience and outcomes, clearly labeled as a self-selected cohort.
3. **Comparison or baseline group:** users measured before exposure or a credible matched/stepped-wedge comparison, if ethically and operationally feasible.

Recommended measures:

- recognition and understanding of cognitive-health concepts;
- perceived ability to identify when to seek help;
- confidence preparing for a healthcare conversation;
- understanding that BrainGuide results are not diagnoses;
- perceived trust, privacy, cultural relevance, and language fit;
- intended next action immediately after use; and
- action actually taken at follow-up: discussed with a provider, scheduled, attended, sought information, or chose not to act, with reasons.

Pretest all measures with Black and Hispanic/Latino users, older adults, caregivers, Spanish-preferred users, and people with lower digital literacy. Report item nonresponse, response rate, time from use to follow-up, mode, language, and whether respondents differ from invitees.

## 6. Q5 — Moderate/high concern and clinical care

### 6.1 What is available now: handoff intent

The supplemental `md.md` analysis joins captured **result-page action-event rows** by Brain Health label for the May 7–August 4, 2026 English-only 90-day window:

| Brain-health label proxy | Provider-click actions | All recorded actions in summed rows | Observed action-event rate | Wilson 95% CI |
|---|---:|---:|---:|---:|
| Poor | 76 | 725 | 10.5% | 8.4%–13.0% |
| Good | 73 | 2,290 | 3.2% | 2.5%–4.0% |

The observed action-rate ratio is approximately 3.3× (10.5% ÷ 3.2%). The cells clear the local release floor and rate-stability floor used in the supplemental analysis. Because the denominator is all recorded actions on summed result-page rows, repeated actions may be included; this is not a user-level provider-seeking rate.

**Inference label: observed handoff intent, using a provisional result-label proxy.** The result is consistent with users receiving a more concerning result label being more likely to produce a provider-resource action event. It does not directly estimate moderate/high-concern users across AD8, MIS, and SBC, which use different constructs and thresholds. It does not show that anyone sought, booked, attended, or completed clinical care. It also does not prove that concern level caused the action; persona, diagnosis status, age, campaign, language, device, and page content may differ.

The current capture does not provide a concern-level split for all Clinical Trials clicks, and the English-only result-page table does not support a Spanish comparison at this grain. The table uses Good/Poor result labels as a proxy; it is not a validated direct estimate of moderate/high concern. SBC Low/Medium/High mapping into Good/Moderate/Poor requires independent verification against the routed result-page definition.

### 6.2 What cannot be estimated

The following are **not assessable** from the current package:

- proportion of moderate/high-concern users who discuss concerns with a clinician;
- proportion who schedule or attend an appointment;
- time from BrainGuide use to care;
- clinical diagnosis, treatment, or outcomes;
- clinical-trial screening, enrollment, or retention;
- whether provider clicks are unique users or repeated actions;
- whether the same person used BrainGuide across sessions/devices; and
- whether action rates differ equitably by race/ethnicity, language, age, gender, geography, or caregiver role after valid adjustment.

### 6.3 Care-seeking measurement plan

Define the Q5 outcome ladder before collecting data:

| Tier | Outcome | Current status | Minimum evidence |
|---|---|---|---|
| 0 | Result-page CTA shown | Not consistently reported | CTA impression event and denominator |
| 1 | Provider/trial page visited | Available in aggregate | Page visit with source/result context |
| 2 | Outbound provider/trial click | Available in aggregate | Deduplicated click and source/result context |
| 3 | User reports discussing concern | Not available | Approved follow-up survey/interview |
| 4 | Appointment scheduled | Not available | Consent-based referral/provider data or verified self-report |
| 5 | Appointment attended / clinical connection | Not available | Approved downstream record or verified self-report |
| 6 | Trial screening/enrollment | Not available | Consent-based trial partner linkage |

For a future Q5 table, use a session/person-level join only if approved and validated:

```text
concern level × flow × result label × language × device × campaign
→ CTA impression → provider/trial click → reported discussion → appointment outcome
```

Report both absolute risk and relative differences, with denominators, observation windows, missingness, and linkage coverage. Never label Tier 2 as “care-seeking.”

### 6.4 Q5 product recommendations

- Give Poor/Moderate/High Risk users a calm, prominent “what to do next” sequence: understand the result, prepare questions, identify care options, and decide what fits.
- Give Good/Low Risk users prevention and monitoring actions without implying that no further care is ever appropriate.
- Include a printable or saveable provider-conversation guide before the outbound click.
- Use result-specific CTA copy rather than a generic “Find a Provider” label.
- Make the external handoff transparent: destination, privacy boundary, cost/eligibility caveat where known, and what BrainGuide will not know afterward.
- Preserve language and context across the handoff; test Spanish provider/trial routes independently.
- Add an optional, consented follow-up: “Did you discuss this with a healthcare professional?” with time intervals and “not yet / prefer not to answer.”

## 7. Cross-question synthesis: the most likely opportunity areas

### 7.1 Reach is not the same as equitable service

The platform can reach a large volume through paid media while still failing to reach or retain priority populations at the right stages. The most important equity denominator is not only “who completed demographics”; it is:

```text
eligible reach → landing → questionnaire start → branch choice →
step progression → score/result → useful action → downstream connection
```

A White-heavy completion population can reflect acquisition, trust, language, device, content, questionnaire burden, or disclosure patterns. It cannot be interpreted without stage-specific denominators.

### 7.2 Aggregate engagement may conceal technical or definitional change

The 2026 engagement rate is unusually high relative to the prior period in the traffic overview, and the site/relaunch/event environment changed. The report also includes malformed URLs, unmapped paths, event-name ambiguity, and differing date windows. Before optimizing based on “high engagement,” validate:

- what fires `user_engagement`;
- whether conversion/key-event settings changed;
- whether consent-mode modeling changed;
- whether sessions are inflated by campaign or cross-domain behavior;
- whether bots/assets/malformed URLs are included; and
- whether page and event definitions changed across the relaunch.

### 7.3 The highest-value immediate product work is friction repair

The 98% AD8 and 89% SBC event-volume gaps are larger and more actionable than broad audience averages. If the instrument is working, these points may be where trust, burden, accessibility, or comprehension fail. If the instrument is not working, the same gaps are data-quality defects. Both possibilities justify QA and telemetry before more speculative demographic modeling.

### 7.4 Handoff intent is promising but incomplete

Poor-labeled result-page users click provider resources more often than Good-labeled users in the observed 90-day table. That is directionally appropriate and suggests result-page routing can prompt a next step. The central missing link is what happens after the click. The product should optimize for informed handoff and then measure whether the handoff becomes a conversation or connection.

## 8. Prioritized recommendations

### Priority 0 — protect interpretation and privacy

1. Adopt the inference labels in this report across dashboard, AI, and client deliverables.
2. Put population, unit, numerator, denominator, date, source, and limitation beside every key metric.
3. Keep GA4 language/device/channel data separate from self-reported race/ethnicity and gender.
4. Apply small-cell suppression, complementary suppression, and difference-attack protection before demographic cuts reach an analyst or LLM.
5. Keep raw conversation archives, prompts, identifiers, and internal engagement details out of client-facing outputs unless approved.

### Priority 1 — repair the funnel users already encounter

1. Investigate and instrument `W-B-AD-9`, `W-S1`, and `W-D4-A-SBC`.
2. Add explicit error, permission, retry, restart, and abandonment-proxy events.
3. Make the experience mobile-first and Spanish-equivalent.
4. Add progress, time expectation, pause/recovery, and trust copy.
5. Test CTA clarity and provider/trial handoff comprehension.

### Priority 2 — create the evidence connector and semantic contract

1. Define a versioned metric registry: canonical event, source event, numerator, denominator, unit, time rule, and status.
2. Confirm whether a de-identified session or transaction key can link questionnaire and GA4 behavior, including pre-questionnaire activity.
3. Produce linkage coverage by period, flow, language, device, and demographic completeness.
4. Build the page/event crosswalk for the March 2026 relaunch and block invalid pre/post comparisons.
5. Run a GA4 quality gate for URL hygiene, bots, schema drift, delayed data, sampling, thresholding, and duplicate events.

### Priority 3 — measure awareness and care outcomes

1. Field an approved multilingual follow-up survey with response and invitation logs.
2. Measure comprehension and confidence, not only satisfaction or clicks.
3. Collect self-reported provider discussion and appointment action with time windows.
4. Establish consented provider/referral/trial linkage where feasible.
5. Evaluate outreach via controlled or stepped-wedge comparisons, not before/after anecdotes.

### Priority 4 — diversify and qualify reach

1. Audit Google Ads/Display targeting, creative, geography, and landing assignments.
2. Test trusted-messenger distribution with Black and Hispanic/Latino community partners.
3. Expand organic and referral pathways that show deeper observed sessions, while validating traffic quality.
4. Compare qualified starts, completion, useful result action, and downstream outcomes by channel—not traffic alone.

## 9. Measurement blueprint mapped to the checklist

| Checklist area | Current evidence | Required next artifact | Gate/status implication |
|---|---|---|---|
| **0.1 Metric registry** | Report names and event inventory exist, but canonical mappings are incomplete | Versioned registry for start, finish, score, information, result, CTA, handoff, and outcome | Gate 0.1 open |
| **0.2 Taxonomy audit** | Site Events lists 17 events; questionnaire event is much larger than start/finish events; malformed URLs exist | Event QA, duplicate/bot/URL review, key-event validation | Gate 0.2 open |
| **0.3 Relaunch crosswalk** | Relaunch is approximate (~March 2026) and same property spans periods | Confirmed date plus page/event equivalence table | Gate 0.3 open |
| **0.4 Data-quality gate** | Known thresholding, sparse cells, mixed grains, malformed paths, and inconsistent totals | Automated completeness/schema/URL/outlier tests | Gate 0.4 open |
| **0.5 Feasibility matrix** | Requirements and coverage matrix define most inputs/gaps | Grain/fields/sample/availability/inference matrix for Q1–Q25 | Gate 0.5 open |
| **0.6 Prompt-injection guard** | Raw campaign/page labels are untrusted text | Sanitization and structured insight objects before LLM use | Gate 0.6 open |
| **1.1–1.8 GA4 descriptive insights** | The checklist marks trends, pages, device, anomalies, funnel, and forecasting as implemented in the application; this report validates only the evidence-package boundaries | Reconcile implementation outputs to source definitions and freshness | Application-implemented for marked items; evidence/release validation remains open |
| **1.9–1.10 automatic insight context** | Design exists; no validated structured insight contract | Deterministic precompute and provenance-bearing context | Open |
| **2.1 connector** | Questionnaire data and GA4 data exist separately | Approved de-identified connector | Open |
| **2.2 linkage coverage** | Explicitly absent | Join success/missingness report | Open; blocks equitable funnel claims |
| **2.3–2.6 equity/pathway/language** | Questionnaire composition and aggregate language/content cuts exist | Stage-specific linked rates and approved benchmark | Partial now; not complete |
| **2.7–2.8 suppression** | Protocol specifies small-cell safeguards | Enforced implementation and audit tests | Open |
| **3.1 survey cohort** | No survey instrument/results in package | Approved survey, invitation log, response/nonresponse analysis | Open; blocks Q4 |
| **3.2–3.5 outcomes** | Click/handoff proxies only | Follow-up, downstream linkage, campaign design | Open; blocks definitive Q4/Q5 |
| **Trust layer T.1–T.8** | Boundaries are documented, but automated enforcement/audit trail/refresh policy are incomplete | Insight object schema, quality gate, provenance, feedback, cache/refresh policy | Open except privacy/no-fabrication principles |

## 10. External research and how it applies

The complete citations below are intentionally concise. The linked peer-reviewed articles are mechanism and design evidence, not BrainGuide estimates. Proposed instruments and outcome measures in this report are design recommendations requiring owner and research-methodologist approval; no validated instrument has been selected or fielded in the current package.

The sources below should modify hypotheses and study design; they should not be used as direct estimates of BrainGuide’s audience or effects.

### Equity, awareness, and care-seeking mechanisms

1. **Lin et al. (2020), dementia-status awareness in U.S. older adults.** [PMC7552114](https://pmc.ncbi.nlm.nih.gov/articles/PMC7552114/) reports lower awareness of dementia status among non-Hispanic Black and Hispanic older adults than non-Hispanic White adults in a Health and Retirement Study cohort. **Application:** BrainGuide should test whether awareness and disclosure barriers occur before questionnaire entry or at result interpretation; do not infer the mechanism from composition alone.
2. **Lin et al. (2021), missed/delayed diagnosis.** [PMC8263486](https://pmc.ncbi.nlm.nih.gov/articles/PMC8263486/) reports higher missed or delayed claims-based dementia diagnosis among non-Hispanic Black and Hispanic older adults, with longer estimated delays. **Application:** care-navigation content should be measured for comprehension and actual follow-through, not merely exposure.
3. **Light et al. (2024), Latino dementia and brain-health knowledge review.** [PMC10983845](https://pmc.ncbi.nlm.nih.gov/articles/PMC10983845/) finds mixed knowledge among U.S. Latino adults, with recognition of memory loss stronger than recognition of other symptoms and protective factors. **Application:** Spanish content should explain symptoms, prevention, and next steps in culturally reviewed, plain language.
4. **Gutiérrez et al. (2022), Latinx online ADRD education recruitment.** [PMC8891594](https://pmc.ncbi.nlm.nih.gov/articles/PMC8891594/) describes very low attendance in an online education recruitment effort and barriers intersecting with education, language preference, cognitive impairment, and age. **Application:** online availability is not equivalent to equitable participation; measure invitation-to-start and start-to-completion separately.
5. **Siette et al. (2023), dementia stigma in culturally and linguistically diverse communities.** [PMC10765564](https://pmc.ncbi.nlm.nih.gov/articles/PMC10765564/) identifies cultural beliefs, language barriers, awareness, migration, and stigmatizing terminology as possible contributors to delayed help-seeking and disclosure. **Application:** use non-stigmatizing copy and qualitative testing; treat this as mechanism guidance, not a BrainGuide estimate.
6. **Philpot et al. (2024), Spanish-preferred patients and digital health literacy.** [PMC11666482](https://pmc.ncbi.nlm.nih.gov/articles/PMC11666482/) reports substantial discomfort reading/writing English among Spanish-preferred patients and greater difficulty with technology and online health-information tasks. **Application:** test Spanish functional equivalence, navigation, comprehension, and support—not only page translation.
7. **Wilson et al. (2024), digital health equity systematic review.** [PMC11217442](https://pmc.ncbi.nlm.nih.gov/articles/PMC11217442/) identifies device/connectivity, navigation, culture, age, socioeconomic status, education, residence, and support infrastructure as interacting determinants, recommending user-friendly interfaces, device compatibility, culturally appropriate content, non-digital options, and education. **Application:** organize the intervention around technical, cultural, and support barriers together.
8. **Portacolone et al. (2020), African American community perspectives.** [PMC7683027](https://pmc.ncbi.nlm.nih.gov/articles/PMC7683027/) describes a desire for dementia education/research alongside historically rooted institutional distrust and the need to earn trust through sustained partnership. **Application:** trusted-messenger outreach should be co-designed and evaluated, not assumed to work because a partner is present.
9. **Epps et al. (2021), congregation-based dementia education.** [PMC8302664](https://pmc.ncbi.nlm.nih.gov/articles/PMC8302664/) observed immediate shifts toward more hopeful/action-oriented language after a workshop in predominantly African American congregations. **Application:** this supports testing community education and measuring attitude/comprehension change; it does not provide a BrainGuide effect size.
10. **Stites et al. (2024), Black adults and biomarker information.** [PMC11560502](https://pmc.ncbi.nlm.nih.gov/articles/PMC11560502/) reports concerns about discrimination and downstream consequences in responses to Alzheimer’s biomarker information. **Application:** privacy-forward, non-diagnostic, consequence-aware result copy is necessary; do not assume identical attitudes among BrainGuide users.
11. **Chau et al. (2023), community-based organizations and trust.** [PMC10939007](https://pmc.ncbi.nlm.nih.gov/articles/PMC10939007/) discusses historical abuse, structural racism, privacy, negative healthcare experiences, and CBOs as potential trusted messengers. **Application:** build long-term partnerships with governance and feedback, not one-off traffic campaigns.

### Measurement and outcome interpretation

- A click is not a care outcome. The report should follow an outcome ladder from CTA exposure to click, reported discussion, appointment, attendance, and trial enrollment.
- Awareness and attitudes require baseline/follow-up or a credible comparison; retrospective satisfaction alone is not causal evidence.
- Nonresponse must be reported because a small opt-in follow-up cohort may differ systematically from invited users.
- Usability and accessibility tests should include older adults, caregivers, Black users, Hispanic/Latino users, Spanish-preferred users, lower-literacy users, and mobile/tablet users.

## 11. GA4 measurement implications

Official Google documentation establishes the following constraints:

- [GA4 sessions and users](https://support.google.com/analytics/answer/9191807): sessions are event-based and users depend on available identity signals such as User-ID or device/browser identifiers. **Implication:** session counts are not unique people, and cross-device stitching is incomplete without an approved identity design.
- [GA4 funnels and path exploration](https://support.google.com/analytics/answer/6318439): event/page sequences can describe progression and drop-off. **Implication:** BrainGuide needs unique, stable step events and explicit rules for re-entry, repeats, back navigation, and time windows.
- [BigQuery export](https://support.google.com/analytics/answer/9358801): raw event-level export is the appropriate basis for reproducible sequence analysis, subject to export delays, consent/modeling gaps, schema changes, and event-collection quality. **Implication:** the dashboard summaries are useful diagnostics, but a demographic funnel and linkage analysis require raw event/session grain.
- [GA4 data thresholds and sampling](https://support.google.com/analytics/answer/9383630): privacy thresholds can suppress low-user rows and complex explorations can be subject to sampling. **Implication:** small demographic and language cuts need suppression/uncertainty rules and should not be reverse-engineered.
- [GA4 user identity](https://support.google.com/analytics/answer/9213390): identity spaces determine how Analytics stitches activity. **Implication:** do not present a cross-session “user journey” as person-level care progression without a validated identity/linkage basis.
- [GA4 consent and behavioral modeling](https://support.google.com/analytics/answer/10710245): modeled behavior can support aggregate traffic estimation where enabled but does not create self-reported demographic or clinical outcomes. **Implication:** modeled totals must be labeled and kept separate from questionnaire outcomes.

## 12. Reconciliation and data-quality register

| Issue | Why it matters | Required resolution |
|---|---|---|
| AD8 score distribution rows total 12,295 versus 12,330 completion KPI | 35 records are not represented in the two displayed outcome rows | Reconcile filters, missing score rows, date scope, and report grain |
| MIS Good + Poor rows total 107,198 versus 107,976 completions | 778 records are not represented in the two displayed outcome rows | Reconcile missing/unknown scores and filters |
| GA4 YTD pulls report approximately 369,900 versus 373,000 sessions | Headline reach and channel shares may differ by pull/filter timing | Preserve query metadata and choose one certified snapshot |
| Engagement rate rose 43.0% to 94.2% year-over-year | Could reflect implementation, consent, audience, or definition change | Audit events, key events, consent, and campaign configuration |
| Same GA4 property spans relaunch | Page/event semantics may not be comparable | Confirm relaunch date and build equivalence crosswalk |
| Site Events lists 676,341 `Questionnaire` events versus 47,172 starts and 13,642 finishes | Generic event may capture repeated/low-specificity activity | Define event taxonomy and deduplication rules |
| Journey Explorer infers abandonment from next-step volume | No explicit exit event; gaps may include errors, re-entry, or instrumentation loss | Add screen/error/exit events and validate with raw event data |
| Top Content has 430 unmapped pages of 584 unique pages | Category and content-demand totals may be distorted | Maintain URL mapping seed and quarantine malformed/assets paths |
| Spanish browser language is not ethnicity | Proxy could misstate Hispanic/Latino reach | Keep language and self-report analyses separate |
| Result-page click table is English-only at concern/action grain | No language-equitable Q5 comparison | Produce approved Spanish/English concern-action table with stable cells |
| “Poor,” “Moderate,” “High Risk,” and “Good” differ by flow | Cross-flow comparisons can be misleading | Use flow-specific score definitions and a validated routing crosswalk |

## 13. Minimum data request to close the five questions

### Required from analytics/engineering

- Raw GA4/BigQuery event export for approved periods, including session ID, event timestamp, device, language, campaign, page path, questionnaire flow/step, CTA event, result/persona, and error/recording parameters.
- Event dictionary and change history, including key-event configuration and `Questionnaire` semantics.
- Confirmed relaunch date and page/event equivalence map.
- URL/content mapping seed and bot/malformed-path rules.
- Validated de-identified join key between questionnaire transaction/session and GA4 behavior, with linkage coverage and unmatched handling.

### Required from product/UX

- English/Spanish content and interaction inventory.
- Accessibility and browser/device support matrix.
- Reproduction results for AD8/SBC leak screens.
- Error, permission, recording, and retry telemetry.
- CTA impression-to-click definitions and destination ownership.

### Required from research/outcomes

- Approved multilingual awareness/knowledge/confidence instrument.
- Invitation and response logs for any follow-up survey.
- Self-reported provider-discussion and appointment measures.
- Consent-approved referral/provider/trial outcome linkage, including time window and matching quality.
- Community co-design and qualitative usability protocol.

### Required governance decisions

- Service-area and age/role benchmark.
- Race/ethnicity crosswalk and missingness treatment.
- Minimum cell and rate-stability thresholds.
- Permitted uses, access roles, retention, and external-sharing approval.
- Whether and how a de-identified linkage may be used for evaluation.

## 14. Final answer in plain language

1. **Reach and equity:** BrainGuide reaches a large audience and a majority-female, older questionnaire population, but the available evidence is White-heavy and contains relatively few Black and Hispanic/Latino respondents. Spanish-language traffic is real and mobile-heavy, yet downstream Spanish capture is much smaller. We can identify an equity risk and prioritize action; we cannot yet quantify equitable reach across the entire funnel.
2. **Action prompting:** BrainGuide clearly prompts questionnaires, results, PDF/email sharing, provider-resource exploration, and clinical-trial clicks. It does not yet measure provider discussion, appointments, or completed care.
3. **Pathway:** Users move from paid acquisition into the homepage, result/content, provider, and trial pathways. The largest observed stalls are early branching, AD8 informant step `W-B-AD-9`, and SBC recording steps. These are high-priority investigation points, not proven causes.
4. **Awareness and attitudes:** The package measures exposure and digital behavior, not changes in knowledge, attitudes, comprehension, or confidence. Influence is not assessable yet.
5. **Clinical care:** Poor-labeled result users show higher observed provider-click intent than Good-labeled users (10.5% vs. 3.2% in the captured English result-page table), but actual care-seeking—especially among moderate/high-concern users—is not measurable until BrainGuide adds approved follow-up and downstream linkage.

The most effective next move is not to produce a more confident narrative from the same aggregate data. It is to repair the highest-friction screens, make Spanish/mobile and trust copy genuinely equivalent, instrument every meaningful step, establish a safe evidence connector, and measure the transition from result to informed care conversation. That sequence directly improves the user experience while creating the evidence needed to answer the client’s questions credibly.

## Appendix A — Local source map

| Claim area | Primary local source |
|---|---|
| Semantic definitions and boundaries | [`CONSOLIDATED.md`](../../CONSOLIDATED.md) |
| Requirements and 25-question framework | [`braintree-reqs.md`](../../../braintree-reqs.md) |
| Implementation gates | [`BRAINTREE_CHECKLIST.md`](../../../BRAINTREE_CHECKLIST.md) |
| Prior equity conclusions and research | [`DEMOGRAPHIC_DISPARITY_ANALYSIS.md`](../../analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md) |
| Measurement/intervention protocol | [`DEMOGRAPHIC_EQUITY_PROTOCOL.md`](../../analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md) |
| Coverage status | [`DEMOGRAPHIC_EQUITY_COVERAGE.md`](../../analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md) |
| YTD questionnaire demographics/outcomes | [`questionnaire-results-overview.md`](../../reports/md/artifacts/questionnaire-results-overview.md) |
| AD8 concern and informant profile | [`ad8-analysis.md`](../../reports/md/artifacts/ad8-analysis.md) |
| MIS self-screen profile | [`mis-analysis.md`](../../reports/md/artifacts/mis-analysis.md) |
| SBC risk/flow profile | [`sbc-analysis.md`](../../reports/md/artifacts/sbc-analysis.md) |
| Flow and severe leaks | [`journey-explorer.md`](../../reports/md/artifacts/journey-explorer.md), [`funnel_table.csv`](../../additional/funnel_table.csv), [`leak_table.csv`](../../additional/leak_table.csv) |
| Home journey and device exit signal | [`user-journeys.md`](../../reports/md/artifacts/user-journeys.md) |
| Result actions and concern-level provider cross-tab | [`result-pages.md`](../../reports/md/artifacts/result-pages.md), [`md.md`](../../additional/md.md) |
| Provider and trial handoffs | [`find-a-provider.md`](../../reports/md/artifacts/find-a-provider.md), [`clinical-trials.md`](../../reports/md/artifacts/clinical-trials.md) |
| Result sharing/opt-in | [`result-sharing.md`](../../reports/md/artifacts/result-sharing.md) |
| Site event inventory | [`site-events.md`](../../reports/md/artifacts/site-events.md) |
| Language/device and channel pull | [`braintree-ga4-equity-supplement.md`](../../additional/braintree-ga4-equity-supplement.md) |
| Interim benchmark | [`BrainGuide Equity Protocol — Phases 2–5 Execution Memo.md`](../../additional/BrainGuide%20Equity%20Protocol%20%E2%80%94%20Phases%202–5%20Execution%20Memo.md), [`race_benchmark_table.csv`](../../additional/race_benchmark_table.csv) |
| Traffic/YTD caveats | [`site-traffic-overview.md`](../../additional/site-traffic-overview.md) |

## Appendix B — Deliverable status

This report is a **supplemental synthesis**, not a replacement for the canonical evidence package. It does not change the checklist status by itself. It recommends moving some questions from “blocked” to “partial” where aggregate evidence now exists, while keeping Q4 influence and definitive Q5 care outcomes blocked until external inputs are available.
