<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# @GitHub @Google Analytics at this repo [https://github.com/griffinkelton/insights-explorer](https://github.com/griffinkelton/insights-explorer) I have a folder called [https://github.com/griffinkelton/insights-explorer/tree/main/braintree-evidence](https://github.com/griffinkelton/insights-explorer/tree/main/braintree-evidence). I'd like you to look at the files and assess the value to the client and create a deep research prompt to best answer questions it can't answer and the key ones from kickoff deck:

Q1) To what extent is BrainGuide reaching and equitably serving diverse populations, including priority populations (e.g., women, Black, and Hispanic communities), as well as users across age, geography, and concern level? additional information, or discussin coroces with a healtacare provider , including completing the questionnaire, seeking 03) Where do users move forward, stall, or disengage in the pathway from engagement to care? Q4) To what extent does BrainGuide influence users' awareness, attitudes, and understanding of cognitive health? Q5) What proportion of users, particularly those identified as moderate or high concern, go on to seek clinical care?

<span style="display:none">[^1_1][^1_2][^1_3][^1_4][^1_5][^1_6][^1_7]</span>

<div align="center">⁂</div>

[^1_1]: BrainGuide Q1 2026.xlsx

[^1_2]: BrainGuide Q2 2026_Updated.xlsx

[^1_3]: meeting-notes-072326.txt

[^1_4]: Report - BrainGuide 2025_Revised.xlsx

[^1_5]: Report - BrainGuide Q3 2025.xlsx

[^1_6]: Reports snapshot.xlsx

[^1_7]: transcript.txt


---

# @GitHub @Google Analytics yes


---

# @GitHub @Google Analytics yes

The evidence package is valuable as a **descriptive analytics foundation**, especially for reach, acquisition, questionnaire engagement, resource interest, and trial-connector activity. It cannot, by itself, credibly answer awareness change or completed clinical-care seeking; those require linked follow-up data and a participant survey/interview component.

## Evidence value

The GitHub folder is well structured for a reusable evidence base: a consolidated dataset/document, source reports, and a dedicated demographic-equity protocol, coverage snapshot, inputs, and disparity analysis. That organization is client-ready for transparency and repeatable analysis, although the GitHub connector returned file-download confirmations rather than the Markdown contents themselves, so the assessment of those files is based on their inventory plus the parallel project materials available here.[^3_1][^3_2]


| Evaluation area | What the current evidence can support | Main limitation |
| :-- | :-- | :-- |
| Q1. Equitable reach | Country/geography; GA-modelled age and gender; questionnaire self-reported demographic fields where completed; language/page usage; questionnaire concern/clinical characteristics. | Race and Hispanic ethnicity cannot be inferred reliably from GA; self-reported demographics apply only to questionnaire respondents who elect to answer, not all site visitors. |
| Q3. Forward movement, stalls, disengagement | A partial behavioral funnel: questionnaire start → finish → tailored results/resources → trial-related actions → form/account actions. Page-level engagement, acquisition source, device, and event counts can locate likely drop-off points. | GA alone cannot reliably reconstruct an individual’s complete cross-session path or explain *why* people leave. Current event definitions appear inconsistent or overly broad. |
| Q4. Awareness, attitudes, understanding | Exposure to educational pages, downloads, videos, and “talk with your doctor” content; survey recall and self-reported change once collected. | Exposure is not evidence of learning or changed attitudes; no documented pre/post measure or comparator. |
| Q5. Clinical-care seeking | Proxies: health-care resource views, provider-discussion content, contact requests, external clicks, trial connector/referral activity. | These are not confirmed clinical appointments, discussions, diagnoses, or care completion. A privacy-protective follow-up survey or consented linkage is needed. |

## Immediate findings

**Reach is broad but demographic interpretability is constrained.** From March 1–August 6, GA4 recorded 291,141 active users, of whom 214,275 (74%) were in the U.S. with age and gender both “unknown.” Among U.S. users with known modelled age/gender, women outnumbered men substantially—for example, women age 65+ numbered 9,940 versus 3,440 men, and women age 55–64 numbered 6,455 versus 3,240 men. This supports a *directional* finding of reach among women and older adults, not a population-representativeness claim. GA4 also marks this report as thresholded.[^3_2]

**There is a large, actionable questionnaire completion gap—but measurement needs validation first.** GA4 reports 128,034 active users who triggered `web_questionnaire_start` and 38,841 who triggered `web_questionnaire_finish` during the same period: an apparent 30.3% user-level completion ratio. However, start and finish event counts were 183,414 and 47,570 respectively, and the generic `Questionnaire` event was fired 2.55 million times and marked as a key event. That pattern makes it unsafe to treat generic event totals as a funnel until event semantics, deduplication, and bot/automation filtering are audited.[^3_1]

**The evidence supports “intent” more than “care.”** There were 29 active users with `ctc_click`, 49 with the `Clinical Trials` event, and 3 with `form_submit`; these small counts should not be described as confirmed clinical-care seeking. Existing quarterly Evidence reports do add questionnaire completion, trial matching/viewing, account actions, request-a-call activity, contact-center inquiries, and referrals—useful downstream service indicators—but they do not establish a denominator-linked care-seeking rate for moderate/high-concern users.[^3_3][^3_1]

**The relaunch is a hard analytic boundary.** The new site launched around March 2026 in the same GA property, with changed UI/actions but broadly stable URLs. Report pre- and post-relaunch periods separately; use page path rather than page title/name, and do not frame changes as outcomes of the redesign without checking event continuity and campaign shifts.[^3_4]

## Key gaps to close

1. **Define the unit of analysis.** Establish whether each metric is an event, session, anonymous session ID, questionnaire transaction, unique person, contact-center record, or consented email respondent. Never mix these denominators in one funnel.
2. **Create a documented event dictionary and QA audit.** For every relevant event, specify trigger, parameter values, firing frequency, key-event status, page/context, whether duplicate firing is possible, and date implemented/changed. The unusually large `Questionnaire` count makes this urgent.[^3_1]
3. **Build a privacy-preserving linkage layer.** Use the existing anonymous session ID and questionnaire transaction ID to link questionnaire responses to in-session tailored-page/resource actions. Use a separate, consented research ID to link survey responses or follow-up outreach—never export or combine raw identifiers unnecessarily. The questionnaire reports already contain session and transaction identifiers.[^3_5][^3_3]
4. **Separate equity reach from equity experience.** Measure representation, completion, action, and reported benefit separately for women, Black participants, Hispanic/Latino participants, age groups, geography, language, concern level, and respondent role. Spanish-language volume is currently very small—meeting notes cite nine year-to-date Spanish completions—so report counts, suppress potentially identifying cells, and use qualitative inquiry rather than significance claims.[^3_4]
5. **Measure outcomes directly.** A follow-up survey needs items on awareness/understanding, confidence discussing concerns, provider discussion, appointment scheduling/completion, barriers, and whether BrainGuide contributed. Survey outreach had been planned to June questionnaire respondents (N=353), with an expectation of low response; response bias must be reported.[^3_6][^3_4]

## Deep research prompt

Use the following as a research/analysis prompt for the consolidated GitHub evidence, GA4, Evidence warehouse, questionnaire data, contact-center data, and follow-up survey.

```text
Act as a mixed-methods health-services evaluation team supporting Access Health Services Research’s evaluation of BrainGuide (mybrainguide.org). Produce a rigorous, equity-centered evaluation of BrainGuide’s reach, user experience, behavior change, and progression toward clinical care.

CONTEXT AND GUARDRAILS
- BrainGuide is an Alzheimer’s/cognitive-health awareness, guidance, resources, and clinical-trial navigation platform.
- The site relaunched in approximately March 2026. The old and new sites share one GA4 property. Treat pre-relaunch and post-relaunch periods as separate analytic eras; do not pool them without proving event and page-path comparability.
- Data sources may include GA4, Google Tag Manager event specifications, Evidence warehouse extracts, questionnaire transactions and answers, contact-center records, referral/trial-connector data, follow-up survey data, and qualitative interview data.
- Use only de-identified, minimum-necessary client data. Do not expose raw email addresses, session IDs, transaction IDs, or small potentially identifying cells.
- Do not infer race, ethnicity, Hispanic identity, diagnosis, or clinical care from geography, language, browsing behavior, or GA-modelled demographics.
- Clearly label all findings as: observed behavior, self-reported outcome, administrative/service record, proxy, association, or causal evidence. Do not make causal claims from observational data.

FIRST: DATA AUDIT AND HARMONIZATION
1. Produce a source inventory with: source owner, date coverage, unit of analysis, unique identifier, fields, inclusion criteria, missingness, known changes, and linkage feasibility.
2. Produce a GA4/GTM event dictionary for every event used in analysis: event name, trigger, event parameters, page/context, first/last valid dates, known duplicates, key-event designation, and intended behavior.
3. Validate the core funnel events:
   - questionnaire landing/view
   - questionnaire start
   - each questionnaire question/step, if available
   - questionnaire completion
   - concern classification/result generation
   - tailored-resource display
   - local-resource interaction
   - provider-discussion resource interaction
   - clinical-trial view/click/referral
   - request-a-call/contact action
   - follow-up survey invitation, open, click, completion
4. Investigate implausible or high-frequency generic events. Compare event count, sessions with event, active users with event, and distinct anonymous session IDs. Flag duplicate firing, instrumentation changes, bot traffic, paid-campaign anomalies, and impossible sequences.
5. Create a data-quality appendix and assign each analysis a confidence rating: high, moderate, low, or insufficient.

ANALYTIC QUESTIONS

Q1. EQUITABLE REACH AND SERVICE
Question: To what extent is BrainGuide reaching and equitably serving women, Black communities, Hispanic/Latino communities, users by age and geography, and users at varying concern levels?

Methods:
- Report a reach cascade for all site users, questionnaire starters, completers, users receiving tailored results, resource interactors, clinical-trial/contact users, and follow-up survey respondents.
- For questionnaire respondents who voluntarily provide data, tabulate age, gender, race, ethnicity/Hispanic identity, language, geography, role (person/caregiver/family), and concern level.
- Report both numerator and denominator for every percentage, plus missing/prefer-not-to-answer rates.
- Compare each priority group’s progression at each stage against the overall rate. Use risk difference and risk ratio only when denominators are adequate; otherwise report descriptive counts and confidence intervals.
- Define “equitable service” as comparable completion, tailored-resource access, action uptake, and reported usefulness after accounting for available concern level, age, role, language, geography, and acquisition channel.
- Treat GA age/gender as modelled, incomplete, and descriptive only. Do not use it for race/ethnicity conclusions.
- For Spanish-language users and other small groups, report counts and combine quantitative descriptive results with interview findings; do not overinterpret small samples.

Deliverables:
- Equity reach cascade table.
- Equity funnel table by priority group.
- Geographic map or state-level table only after small-cell suppression.
- Missingness table and equity-data limitations.
- 3–5 equity-focused recommendations, each tied to an observed barrier or gap.

Q3. PATHWAY PROGRESSION, STALLS, AND DISENGAGEMENT
Question: Where do users move forward, stall, or disengage between initial engagement and care-oriented action?

Methods:
- Build a de-duplicated, session-level and anonymous-user-level funnel using validated events.
- Primary sequence:
  acquisition/landing page → questionnaire start → questionnaire completion → result/concern level → tailored resources displayed → resource interaction → provider-discussion or local-resource action → clinical-trial/contact action → verified downstream action where available.
- Calculate volume, conversion rate from previous step, cumulative conversion rate, median time between steps, and top exit pages/steps.
- Segment by pre- vs. post-March-2026 relaunch, acquisition channel/campaign, device, language, geography, questionnaire type, respondent role, concern level, and available voluntary demographics.
- Use path exploration or sequence analysis to identify common journeys, but distinguish observed sequences from causal explanations.
- Investigate questionnaire abandonment by question order, time spent, branching logic, errors, mobile/desktop, page-load/performance issues, and accessibility barriers.
- Reconcile GA counts with Evidence warehouse counts. Where they differ, explain the measurement definitions rather than choosing one source arbitrarily.

Deliverables:
- Validated funnel with data-quality notes.
- Sankey/pathway visualization.
- Drop-off diagnostic table, ranked by potential impact and confidence.
- Pre/post-relaunch comparability appendix.
- Prioritized UX, content, and measurement recommendations.

Q4. AWARENESS, ATTITUDES, AND UNDERSTANDING
Question: To what extent does BrainGuide influence users’ awareness, attitudes, and understanding of cognitive health?

Methods:
- Do not treat page views, scrolls, downloads, videos, or resource clicks as evidence of learning; classify them as exposure or engagement proxies.
- Analyze follow-up survey results using a clearly described sampling frame, invitations delivered, response rate, completion rate, time since BrainGuide use, and nonresponse limitations.
- Measure self-reported changes in:
  a) awareness of cognitive-health risk and warning signs,
  b) understanding of available resources and next steps,
  c) confidence discussing concerns with a health-care professional,
  d) perceived stigma and willingness to seek help,
  e) ability to identify a personally relevant next action.
- Where baseline data are unavailable, report perceived change and attribution as self-reported, not causal.
- Compare results by concern level, respondent role, priority population, language, and whether the respondent completed the questionnaire/tailored pathway.
- Code open-ended responses and interviews using a structured thematic framework; include barriers, confusion, trust, cultural relevance, accessibility, and recommended improvements.

Deliverables:
- Survey flow and response-bias table.
- Outcome table with counts, percentages, confidence intervals where appropriate, and missingness.
- Integrated quantitative/qualitative findings matrix.
- Explicit statement of what BrainGuide can and cannot claim regarding impact.

Q5. CLINICAL-CARE SEEKING, ESPECIALLY MODERATE/HIGH CONCERN
Question: What proportion of moderate- or high-concern users go on to seek clinical care?

Methods:
- Establish and document the concern-level algorithm and whether it is generated from questionnaire answers, self-reported diagnosis/severity, or another rule.
- Define nested outcome levels:
  Level 1: intention to discuss concerns or seek care.
  Level 2: provider-discussion resource engagement or appointment intent.
  Level 3: self-reported provider discussion, appointment scheduled, or appointment completed.
  Level 4: verified service/contact-center action, referral, or care-navigation outcome, where consented linkage is available.
- Report each level separately. Do not label trial clicks, resource views, contact requests, or referral matches as clinical care.
- For moderate/high concern users, estimate the proportion at every outcome level with explicit denominators, elapsed follow-up time, and unknown/lost-to-follow-up category.
- Assess barriers among those who did not seek care: cost, access, insurance, transportation, fear/stigma, caregiver burden, uncertainty, language, distrust, digital access, and lack of perceived urgency.
- Use multivariable exploratory models only if sample size and data completeness are adequate. State that associations are not causal.

Deliverables:
- Moderate/high-concern care-progression cascade.
- Care-seeking outcomes table with follow-up windows.
- Barrier analysis and qualitative themes.
- Recommendations distinguishing platform changes, outreach/navigation supports, and measurement improvements.

REPORTING REQUIREMENTS
- Begin with an executive overview, followed by methods/data sources, findings, equity observations, recommendations, and limitations.
- Show raw n and denominator beside every percentage.
- Suppress or aggregate small cells; flag all small samples prominently.
- Present pre- and post-March-2026 results separately unless comparability is demonstrated.
- Include a “what we know / what we cannot know” box for each evaluation question.
- Include a measurement roadmap: immediate fixes (0–30 days), near-term analysis upgrades (30–90 days), and longer-term outcome measurement.
- End with a concise implementation backlog identifying owner, required data, expected decision value, privacy considerations, and priority.
```

The key client message should be: BrainGuide has evidence of substantial reach and meaningful digital engagement, but the evaluation should not yet claim equitable service, awareness impact, or clinical-care conversion until measurement definitions are validated and direct outcome data are collected.

<div align="center">⁂</div>

[^3_1]: BrainGuide Q2 2026_Updated.xlsx

[^3_2]: transcript.txt

[^3_3]: BrainGuide Q1 2026.xlsx

[^3_4]: meeting-notes-072326.txt


---

# @GitHub @Google Analytics Act as a mixed-methods health-services evaluation team supporting Access Health Services Research’s evaluation of BrainGuide (mybrainguide.org). Produce a rigorous, equity-centered evaluation of BrainGuide’s reach, user experience, behavior change, and progression toward clinical care.

CONTEXT AND GUARDRAILS

- BrainGuide is an Alzheimer’s/cognitive-health awareness, guidance, resources, and clinical-trial navigation platform.
- The site relaunched in approximately March 2026. The old and new sites share one GA4 property. Treat pre-relaunch and post-relaunch periods as separate analytic eras; do not pool them without proving event and page-path comparability.
- Data sources may include GA4, Google Tag Manager event specifications, Evidence warehouse extracts, questionnaire transactions and answers, contact-center records, referral/trial-connector data, follow-up survey data, and qualitative interview data.
- Use only de-identified, minimum-necessary client data. Do not expose raw email addresses, session IDs, transaction IDs, or small potentially identifying cells.
- Do not infer race, ethnicity, Hispanic identity, diagnosis, or clinical care from geography, language, browsing behavior, or GA-modelled demographics.
- Clearly label all findings as: observed behavior, self-reported outcome, administrative/service record, proxy, association, or causal evidence. Do not make causal claims from observational data.

FIRST: DATA AUDIT AND HARMONIZATION

1. Produce a source inventory with: source owner, date coverage, unit of analysis, unique identifier, fields, inclusion criteria, missingness, known changes, and linkage feasibility.
2. Produce a GA4/GTM event dictionary for every event used in analysis: event name, trigger, event parameters, page/context, first/last valid dates, known duplicates, key-event designation, and intended behavior.
3. Validate the core funnel events:
    - questionnaire landing/view
    - questionnaire start
    - each questionnaire question/step, if available
    - questionnaire completion
    - concern classification/result generation
    - tailored-resource display
    - local-resource interaction
    - provider-discussion resource interaction
    - clinical-trial view/click/referral
    - request-a-call/contact action
    - follow-up survey invitation, open, click, completion
4. Investigate implausible or high-frequency generic events. Compare event count, sessions with event, active users with event, and distinct anonymous session IDs. Flag duplicate firing, instrumentation changes, bot traffic, paid-campaign anomalies, and impossible sequences.
5. Create a data-quality appendix and assign each analysis a confidence rating: high, moderate, low, or insufficient.

ANALYTIC QUESTIONS

Q1. EQUITABLE REACH AND SERVICE
Question: To what extent is BrainGuide reaching and equitably serving women, Black communities, Hispanic/Latino communities, users by age and geography, and users at varying concern levels?

Methods:

- Report a reach cascade for all site users, questionnaire starters, completers, users receiving tailored results, resource interactors, clinical-trial/contact users, and follow-up survey respondents.
- For questionnaire respondents who voluntarily provide data, tabulate age, gender, race, ethnicity/Hispanic identity, language, geography, role (person/caregiver/family), and concern level.
- Report both numerator and denominator for every percentage, plus missing/prefer-not-to-answer rates.
- Compare each priority group’s progression at each stage against the overall rate. Use risk difference and risk ratio only when denominators are adequate; otherwise report descriptive counts and confidence intervals.
- Define “equitable service” as comparable completion, tailored-resource access, action uptake, and reported usefulness after accounting for available concern level, age, role, language, geography, and acquisition channel.
- Treat GA age/gender as modelled, incomplete, and descriptive only. Do not use it for race/ethnicity conclusions.
- For Spanish-language users and other small groups, report counts and combine quantitative descriptive results with interview findings; do not overinterpret small samples.

Deliverables:

- Equity reach cascade table.
- Equity funnel table by priority group.
- Geographic map or state-level table only after small-cell suppression.
- Missingness table and equity-data limitations.
- 3–5 equity-focused recommendations, each tied to an observed barrier or gap.

Q3. PATHWAY PROGRESSION, STALLS, AND DISENGAGEMENT
Question: Where do users move forward, stall, or disengage between initial engagement and care-oriented action?

Methods:

- Build a de-duplicated, session-level and anonymous-user-level funnel using validated events.
- Primary sequence:
acquisition/landing page → questionnaire start → questionnaire completion → result/concern level → tailored resources displayed → resource interaction → provider-discussion or local-resource action → clinical-trial/contact action → verified downstream action where available.
- Calculate volume, conversion rate from previous step, cumulative conversion rate, median time between steps, and top exit pages/steps.
- Segment by pre- vs. post-March-2026 relaunch, acquisition channel/campaign, device, language, geography, questionnaire type, respondent role, concern level, and available voluntary demographics.
- Use path exploration or sequence analysis to identify common journeys, but distinguish observed sequences from causal explanations.
- Investigate questionnaire abandonment by question order, time spent, branching logic, errors, mobile/desktop, page-load/performance issues, and accessibility barriers.
- Reconcile GA counts with Evidence warehouse counts. Where they differ, explain the measurement definitions rather than choosing one source arbitrarily.

Deliverables:

- Validated funnel with data-quality notes.
- Sankey/pathway visualization.
- Drop-off diagnostic table, ranked by potential impact and confidence.
- Pre/post-relaunch comparability appendix.
- Prioritized UX, content, and measurement recommendations.

Q4. AWARENESS, ATTITUDES, AND UNDERSTANDING
Question: To what extent does BrainGuide influence users’ awareness, attitudes, and understanding of cognitive health?

Methods:

- Do not treat page views, scrolls, downloads, videos, or resource clicks as evidence of learning; classify them as exposure or engagement proxies.
- Analyze follow-up survey results using a clearly described sampling frame, invitations delivered, response rate, completion rate, time since BrainGuide use, and nonresponse limitations.
- Measure self-reported changes in:
a) awareness of cognitive-health risk and warning signs,
b) understanding of available resources and next steps,
c) confidence discussing concerns with a health-care professional,
d) perceived stigma and willingness to seek help,
e) ability to identify a personally relevant next action.
- Where baseline data are unavailable, report perceived change and attribution as self-reported, not causal.
- Compare results by concern level, respondent role, priority population, language, and whether the respondent completed the questionnaire/tailored pathway.
- Code open-ended responses and interviews using a structured thematic framework; include barriers, confusion, trust, cultural relevance, accessibility, and recommended improvements.

Deliverables:

- Survey flow and response-bias table.
- Outcome table with counts, percentages, confidence intervals where appropriate, and missingness.
- Integrated quantitative/qualitative findings matrix.
- Explicit statement of what BrainGuide can and cannot claim regarding impact.

Q5. CLINICAL-CARE SEEKING, ESPECIALLY MODERATE/HIGH CONCERN
Question: What proportion of moderate- or high-concern users go on to seek clinical care?

Methods:

- Establish and document the concern-level algorithm and whether it is generated from questionnaire answers, self-reported diagnosis/severity, or another rule.
- Define nested outcome levels:
Level 1: intention to discuss concerns or seek care.
Level 2: provider-discussion resource engagement or appointment intent.
Level 3: self-reported provider discussion, appointment scheduled, or appointment completed.
Level 4: verified service/contact-center action, referral, or care-navigation outcome, where consented linkage is available.
- Report each level separately. Do not label trial clicks, resource views, contact requests, or referral matches as clinical care.
- For moderate/high concern users, estimate the proportion at every outcome level with explicit denominators, elapsed follow-up time, and unknown/lost-to-follow-up category.
- Assess barriers among those who did not seek care: cost, access, insurance, transportation, fear/stigma, caregiver burden, uncertainty, language, distrust, digital access, and lack of perceived urgency.
- Use multivariable exploratory models only if sample size and data completeness are adequate. State that associations are not causal.

Deliverables:

- Moderate/high-concern care-progression cascade.
- Care-seeking outcomes table with follow-up windows.
- Barrier analysis and qualitative themes.
- Recommendations distinguishing platform changes, outreach/navigation supports, and measurement improvements.

REPORTING REQUIREMENTS

- Begin with an executive overview, followed by methods/data sources, findings, equity observations, recommendations, and limitations.
- Show raw n and denominator beside every percentage.
- Suppress or aggregate small cells; flag all small samples prominently.
- Present pre- and post-March-2026 results separately unless comparability is demonstrated.
- Include a “what we know / what we cannot know” box for each evaluation question.
- Include a measurement roadmap: immediate fixes (0–30 days), near-term analysis upgrades (30–90 days), and longer-term outcome measurement.
- End with a concise implementation backlog identifying owner, required data, expected decision value, privacy considerations, and priority.

I now have a thorough understanding of the evidence package. This is enough to write the full assessment plus a scoped, non-duplicative research prompt.

## Bottom line

This GitHub evidence package is unusually mature: it already contains a self-auditing 25-question coverage matrix, a five-phase equity implementation protocol, and a disparity analysis with full source provenance — essentially the deliverable structure I would otherwise have needed to build from scratch. The remaining research gap is narrower and more targeted than a fresh, from-scratch evaluation: it's about *executing* the protocol's blocked phases (event-level linkage, benchmark selection, mechanism validation, outcome survey) rather than *designing* them.

## What the repo already delivers

The package is organized as a semantic contract (`CONSOLIDATED.md`), an equity findings layer (`DEMOGRAPHIC_DISPARITY_ANALYSIS.md`), an implementation contract (`DEMOGRAPHIC_EQUITY_PROTOCOL.md`), and an auditable status matrix (`DEMOGRAPHIC_EQUITY_COVERAGE.md`), backed by 16 captured dashboard PDFs and machine-readable JSON snapshots.

**Key findings already captured, with provenance:**

- Race composition among displayed Results Overview rows (n=54,626): White/Caucasian 77.9% (42,556), Hispanic/Latino 4.9% (2,675), Black/African American 4.5% (2,433) — a White:Black ratio of ~17.5:1 and White:Hispanic ratio of ~15.9:1.
- Demographics are only available from ~75% of the scored-completion population downward — not from all visitors or all questionnaire starters — so this is a composition signal, not a representativeness ratio.
- Spanish-language pageviews are 5.5% of Top Content pageviews, present but far smaller than English traffic.
- SBC scored-result rate is 4.8%, flagged as an operational-friction signal.
- Gender rows skew female-heavy (70.1% of displayed rows).

**Status of the 25 client questions:** the matrix explicitly marks each as `supported_now`, `partial_now`, `blocked_external_input`, or `not_applicable_to_snapshot`. Most equity, funnel drop-off, prediction, relaunch-comparison, and outcome questions are marked `partial_now` or `blocked_external_input` — meaning the method is defined but requires data, linkage, or decisions not yet in the repository (event-level sequences, an approved benchmark, downstream outcome definitions, survey results).

## Assessment: value to the client

| Dimension | Value |
| :-- | :-- |
| Descriptive reach/composition | High — reusable, well-cited, ready for client presentation |
| Methodological rigor and governance | High — privacy floors (n<10 suppression), benchmark discipline, explicit fact-vs-hypothesis labeling prevent premature equity claims |
| Funnel/drop-off (Q3) | Low currently — blocked pending event-level sequencing and a validated abandonment definition |
| Awareness/attitude change (Q4) | Low currently — protocol defines a survey approach, but no results exist yet |
| Clinical care-seeking (Q5) | Low currently — only visit/click "handoff intent" signals exist; no linked downstream outcome |
| Reusability by AHSR/IT staff | High — scripts, tests, and JSON snapshots make it auditable and regenerable, not just a one-off report |

The package's stated boundary is accurate and important to preserve in the final client report: it supports a reproducible **descriptive** assessment, not a population-representativeness or causal evaluation.

## Deep research prompt (scoped to close the actual gaps)

Given the protocol already defines *how* to close these gaps, the highest-value research prompt is narrower than a from-scratch evaluation — it should execute Phases 2–5 of the existing protocol and answer the residual portions of Q1, Q3, Q4, Q5.

```text
ROLE: Mixed-methods health-services evaluators executing Phases 2–5 of AHSR's existing
BrainGuide Demographic Equity Protocol (braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md)
and closing the `partial_now` / `blocked_external_input` rows in the Equity Coverage Matrix
(braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md).

DO NOT re-derive what CONSOLIDATED.md, DEMOGRAPHIC_DISPARITY_ANALYSIS.md, and the coverage
matrix already establish. Treat those as ground truth inputs. Your job is to produce the
missing linkage, benchmark, and outcome evidence they identify as blocking.

TASK 1 — Benchmark decision record (unlocks Q1/Q2/Q6/Q7/Q8)
- Select and document the ACS 5-year population benchmark matched to BrainGuide's actual
  geographic reach and age eligibility (per Section 2.1 of the protocol).
- Record race/ethnicity crosswalk decisions: are Results Overview race rows mutually
  exclusive, is Hispanic/Latino ethnicity or a combined display category, how is "Mixed"
  counted, how do categories map to ACS/OMB standards.
- Calculate representation_ratio and percentage_point_gap for each priority group with
  95% CIs, plus one sensitivity benchmark. Never use a single national percentage.

TASK 2 — Event-level funnel and abandonment analysis (unlocks Q3/Q4/Q16)
- Using GA4/GTM event-level data (not aggregate dashboard rows), build the funnel:
  eligible visitor/session → landing → questionnaire start → each versioned step →
  completed assessment/information path → scored result → result-page action →
  provider/trial/resource action.
- Fix the unit of analysis (person/device/session/questionnaire transaction) and
  deduplication rule before computing any rate.
- Separate AD8, MIS, SBC, and information-only paths; never use scored completion as
  the denominator for abandonment.
- Report step_rate, step_loss, and top exit points by device, language, and (where
  linkable) demographic group, flagging any cell n<10.
- Confirm the exact March 2026 relaunch date and build a page/event equivalence
  crosswalk before comparing pre/post periods.

TASK 3 — Mechanism validation for the observed disparity (unlocks Q7/Q8/Q9)
- Test the protocol's documented hypotheses (trusted-messenger gaps, privacy concern,
  UX/copy friction, device/language barriers) against event telemetry, error logs,
  and where available, user interviews or community co-design sessions.
- Evaluate Spanish-language functional equivalence: error rates, task completion,
  and native-speaker content review — not just pageview share.

TASK 4 — Outcome survey execution and analysis (unlocks Q4/Q24)
- Execute the protocol's defined follow-up survey instrument on the approved cohort.
- Report invitations sent, response rate, completion rate, and nonresponse bias.
- Measure self-reported awareness, confidence discussing concerns with a provider,
  and perceived next-step clarity, segmented by concern level and priority group.
- Label all results self-reported and non-causal; do not infer diagnosis or care
  completion from GA4 behavior.

TASK 5 — Clinical care-seeking outcome linkage (unlocks Q5/Q17/Q18/Q19)
- Define the nested outcome levels (intent → provider-discussion engagement →
  self-reported discussion/appointment → verified contact-center/referral action)
  per the protocol's outcome estimands section.
- For moderate/high-concern users specifically, report each level's proportion with
  explicit denominators and an "unknown/lost-to-follow-up" category.
- Do not label a trial click, resource view, or referral match as clinical care.

DELIVERABLE: An update to DEMOGRAPHIC_EQUITY_COVERAGE.md moving each `partial_now`/
`blocked_external_input` row to `supported_now` where possible, with full provenance,
plus a short memo listing rows that remain blocked and exactly what is still missing.
```

This prompt is designed to slot directly into the existing repo structure (updating the coverage matrix rather than creating a parallel report), which matches the engagement's emphasis on auditability and avoids re-litigating work already completed to a high standard.

---

## Summary

I executed as much of the Phase 2–5 protocol as the repository and public data allow, and produced a memo distinguishing what genuinely moves to `supported_now` versus what stays blocked.

**Task 1 (benchmark) — now executable and completed.** Using 2023 ACS national estimates as an interim benchmark, I calculated representation ratios and 95% Wilson CIs for the race/gender rows: Black respondents show a 0.38 representation ratio (4.45% observed vs. 11.64% national) and Hispanic/Latino respondents show 0.25 (4.90% vs. 19.55% national), while White respondents show 1.36. I also flagged the crosswalk problem explicitly: the repo's race rows are a combined self-identification taxonomy, not OMB-standard mutually exclusive race/ethnicity, so this is a provisional signal, not a final disparity claim — a service-area-matched benchmark and crosswalk decision are still owner actions.

**Task 2 (funnel) — upgraded from `blocked_external_input` toward `partial_now`.** The repo's `journey-explorer.md` already contains an aggregate step-loss funnel (26,221 → 9,327 users, ~48% single-step drop), platform-wide 34% completion rate, and three flagged high-severity leaks (including a 98% drop-off at AD8 step W-B-AD-9), plus device-segmented and campaign-segmented drop-off. This is real, useful evidence I hadn't fully extracted before — but it's dashboard-level, not raw deduplicated event data, so it can't reach `supported_now`.

**Tasks 3–5 — remain blocked.** No mechanism-validation telemetry, no survey data, and no care-seeking linkage data exist anywhere in the repository; closing these requires new data collection or access outside the analytics package, not further analysis of existing files.

I've shared four CSV tables (benchmark ratios, funnel steps, leak diagnostics, campaign performance) and a full markdown memo with the coverage-matrix update recommendations and an explicit list of what's still missing for each blocked item.
<span style="display:none">[^5_1][^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_18][^5_19][^5_2][^5_20][^5_21][^5_22][^5_23][^5_3][^5_4][^5_5][^5_6][^5_7][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://www.census.gov/newsroom/press-releases/2024/population-estimates-characteristics.html

[^5_2]: https://www.census.gov/newsroom/press-releases/2025/older-adults-outnumber-children.html

[^5_3]: https://www.neilsberg.com/insights/united-states-population-by-gender/

[^5_4]: https://www.usagainstalzheimers.org/learn/alzheimers-crisis

[^5_5]: https://www.usagainstalzheimers.org/videos

[^5_6]: https://www.usagainstalzheimers.org/sites/default/files/2019-10/USPSTF COMMENTS 10.7.19 .pdf

[^5_7]: https://www.usagainstalzheimers.org/sites/default/files/Brain Injury and Dementia Slide Deck.pdf

[^5_8]: https://www.usagainstalzheimers.org/sites/default/files/UA2_SocialMediaToolkit_Jan2024_FINAL.pdf

[^5_9]: https://www.usagainstalzheimers.org/sites/default/files/2019-10/fiu_paper_10.18.19%20(1).pdf

[^5_10]: https://www.usagainstalzheimers.org/sites/default/files/2019-10/USPSTF 2019 Public Comment letter on cognitive screening (LEAD Coalition 10-7-2019).pdf

[^5_11]: https://www.usagainstalzheimers.org/sites/default/files/2025-11/07222025-FDA_Patient_Listening_Session-APOE4_Homozygosity_Summary_Final.pdf

[^5_12]: https://www.census.gov/programs-surveys/acs.html

[^5_13]: https://en.wikipedia.org/wiki/Demographics_of_the_United_States

[^5_14]: https://www.statista.com/statistics/183489/population-of-the-us-by-ethnicity-since-2000/

[^5_15]: https://www.americashealthrankings.org/explore/measures/pct_65plus

[^5_16]: https://www.facebook.com/pewresearch/posts/as-of-2024-the-us-black-population-has-grown-to-492-million-up-from-362-million-/1277063117623079/

[^5_17]: https://www.consumeraffairs.com/homeowners/elderly-population-by-state.html

[^5_18]: https://www.reddit.com/r/dataisbeautiful/comments/18mzbeq/cumulative_difference_in_male_vs_female/

[^5_19]: https://www.kff.org/state-health-policy-data/state-indicator/distribution-by-raceethnicity/

[^5_20]: https://www.census.gov/topics/population/older-aging.html

[^5_21]: https://www.statista.com/statistics/241495/us-population-by-sex/

[^5_22]: https://www.pewresearch.org/short-reads/2026/02/05/key-facts-about-black-americans/

[^5_23]: https://acl.gov/news-and-events/announcements/acl-releases-2023-profile-older-americans
