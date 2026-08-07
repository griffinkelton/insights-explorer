# Deep Research Prompt v2: BrainGuide Demographic Equity — Mechanism Validation & Benchmark Construction

> **Supersedes** `braintree-deep-research-prompt.md`, which was built before the actual `braintree-evidence/` package was located. This version is grounded in the real, already-audited evidence package at `griffinkelton/insights-explorer/braintree-evidence/`.
>
> **Edit (2026-08-07):** Added §0 below to reconcile the five SOW-level evaluation questions against the existing 25-question tactical framework, and added Task 3 to close the one genuine gap identified — concern-level segmentation of care-seeking.

## 0. Reconciliation: SOW-level questions vs. the 25-question framework

The engagement's core evaluation questions (client-facing, formal framing) are:

1. To what extent is BrainGuide reaching and equitably serving diverse populations, including priority populations (women, Black, Hispanic communities), as well as users across age, geography, and **concern level**?
2. To what extent do users progress through the platform — including completing the questionnaire, seeking additional information, or discussing concerns with a healthcare provider?
3. Where do users move forward, stall, or disengage in the pathway from engagement to care?
4. To what extent does BrainGuide influence users' awareness, attitudes, and understanding of cognitive health?
5. What proportion of users — particularly those identified as moderate or high concern — go on to seek clinical care?

These map onto the existing 25-question tactical framework (`braintree-reqs.md`, `BRAINTREE_CHECKLIST.md`) and the audited coverage matrix (`braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md`) as follows:

| SOW question | Maps to coverage-matrix question(s) | Status |
|---|---|---|
| 1 — reach/equity by population, age, geography | Q2 (`partial_now`), Q5 (`partial_now`), Q10 (`partial_now`) | Covered, except the **concern-level axis** — see gap below |
| 2 — questionnaire completion → info-seeking → provider discussion | Q3 (`partial_now`), Q15 (`partial_now`), Q17 (`blocked_external_input`), Q20 (`partial_now`) | Covered |
| 3 — forward/stall/disengage from engagement to care | Q4 (`blocked_external_input`), Q14 (`blocked_external_input`), Q19 (`blocked_external_input`) | Covered — and note the journey-explorer already surfaces two severe leaks: 98% AD8 abandonment at `W-B-AD-9`, 51%/89% SBC abandonment at `W-S1`/`W-D4-A-SBC` |
| 4 — awareness/attitude/understanding influence | Q24 (`blocked_external_input`) | Covered, blocked on survey data as already documented |
| 5 — proportion of moderate/high-concern users seeking clinical care | Closest existing: Q17, Q18 (both `blocked_external_input`/`partial_now`) | **Gap: neither question segments by AD8/MIS/SBC concern level** |

### The one genuine gap: concern-level segmentation

The coverage matrix and disparity analysis report **aggregate** reach, funnel, and resource-click data, and separately report **aggregate** AD8/MIS/SBC score distributions (Good/Poor/Moderate, Low/Medium/High Risk). It does not yet cross-tabulate the two: *do respondents who scored Poor (AD8/MIS) or High Risk (SBC) click through to provider/trial resources at a different rate than those who scored Good/Low Risk?* This is exactly what SOW Q5 asks, and it is answerable **now**, without new data collection, using data already captured in `Result Pages.pdf`, `Clinical Trials.pdf`, and `Find a Provider.pdf` — those reports already have persona/brain-health-label dimensions; they simply haven't been cross-tabulated against resource-click outcomes in the existing artifacts. This is added as Task 3 below.

## Role and context

You are extending a rigorous, already-audited descriptive equity assessment of BrainGuide, a public-facing brain-health screening/navigation platform associated with UsAgainstAlzheimer's, operated for AHSR (client lead: Dr. Kumbie Madondo; IT/analytics: Greg Magnuson). The engagement has already produced a complete semantic data contract, a disparity analysis with cited external mechanisms, a five-phase implementation protocol, and an auditable 25-question coverage matrix. **Your job is not to redo this work — it is to fill three specific gaps**, using only publicly available, citable sources for Tasks 1–2, and only the already-captured Evidence dashboard reports for Task 3.

Treat all client data, analytics, and files as confidential. Do not propose training models on this data or reusing it outside this engagement. Do not recommend exporting raw data externally or retaining client materials beyond project needs.

## What already exists (do not re-derive)

### Data architecture and semantics
GA4 (`analytics_257799278`), Google Ads, DynamoDB questionnaire records (`raw_dpn-chat-bot-content`, `raw_dpn-chat-bot-content-go365`), and Search Console feed dbt staging → marts → an Evidence dashboard at `dashboard.dev2.mybrainguide.org`. Three assessment flows exist with **incompatible scales that must never be merged**: AD8 (informant-reported, 0–8, lower=better, Good 0–1/Poor 2–8), MIS (self-administered recall, 0–8, higher=better, Good 5–8/Poor 0–4), and SBC (self-administered speech, 0–1 continuous, higher=lower risk, Low>0.5/Medium 0.2–0.5/High<0.2). A fourth path, flow `c`, returns content routing with no score (~24% of completions). Eight assessment personas plus three SBC personas route users to specific result pages based on Who (Self/Someone Else) × Diagnosed × Brain Health.

### Already-observed findings (treat as ground truth, cite by report/page when referencing)
- **Race/ethnicity composition** (displayed rows, `Results Overview.pdf` p.7, n=54,626): White/Caucasian 77.9% (42,556), Prefer not to answer 5.6%, Hispanic/Latino 4.9% (2,675), Black/African American 4.5% (2,433), Asian 2.6%, Mixed 2.3%, Other 1.0%, American Indian/Alaska Native 1.0%, Native Hawaiian/Pacific Islander 0.2%. White:Black ratio ≈17.5:1; White:Hispanic/Latino ratio ≈15.9:1.
- **Per-flow race composition** varies (AD8 White 70.5%, MIS 78.6%, SBC 73.9% among displayed rows) but is directionally consistent — the White concentration is not an artifact of one assessment type.
- **Demographic coverage**: gender ~79%, age ~77%, race ~75% of the Results Overview filtered population; demographics apply **from Received Score downward only** — anyone who abandons before a scored result is invisible to demographic analysis.
- **SBC has a severe operational completion problem**: 36,803 flow entries, only 1,751 scored results (4.8% completion). The journey-explorer synthesis independently corroborates this with step-level detail: 51% abandon at `W-S1`, 89% abandon at `W-D4-A-SBC` (16.3k→1.7k), and tablet users lose 71% at `W-S1` vs. 42% for desktop.
- **A separate, even more severe leak exists in the AD8 informant flow**: 98% abandonment at screen `W-B-AD-9` (19,600→369 continuing) — this is the single worst-performing step across the entire questionnaire per the journey-explorer "Insights" view.
- **Campaign quality varies enormously**: `(organic)` converts at 59% (41,225 starts); one specific paid campaign (`6592414342203`) converts at 0.1% (9,325 starts, near-total failure); two Display campaigns convert at 13–14% on tens of thousands of starts each.
- **Language**: Spanish is 5.5% of Top Content pageviews (28,531 of 516,480); Spanish Clinical Trials visit-to-click rate is 5.8% vs. English 18.0%; Spanish Find-a-Provider click cell is suppressed (n<10) against 194 visits.
- **Device**: page-sequence exit rates are Mobile 74.7%, Tablet 80.2%, Desktop 62.8% (not bounce rate — no next pageview in session).
- **Geographic reach**: 620,861 US users across 81 states/territories; top states by users are California, Florida, Texas, New York, Pennsylvania; 690,800 global users across 211 countries.
- **Known internal data contradictions** (already flagged, not yet resolved): AD8 outcome rows (10,170 Poor + 2,125 Good = 12,295) don't reconcile to the 12,330 completion KPI (35 missing); MIS outcome rows (21,159 Poor + 86,039 Good = 107,198) don't reconcile to 107,976 completions (778 missing).

### Already-cited external mechanism literature (12 sources, do not duplicate — extend/update instead)
Lin et al. 2020 (dementia-status awareness disparity), Lin et al. 2021 (diagnosis delay disparity), Portacolone et al. 2020 (Black community trust/research), Epps et al. 2021 (congregation-based education), Stites et al. 2024 (Black adults and biomarker stigma), Philpot et al. 2024 (Spanish-preferred digital health literacy), Light et al. 2024 (Latino dementia knowledge review), Gutiérrez et al. 2022 (Latinx online ADRD recruitment barriers), Siette et al. 2023 (dementia stigma in diverse communities), Chau et al. 2023 (CBOs as trusted messengers), Wilson et al. 2024 (digital health equity systematic review).

### The five-phase protocol and statistical rules (already specified, use as-is)
Phase 1 (measurement/benchmark/crosswalk) → Phase 2 (funnel/missingness) → Phase 3 (mechanism validation/community research) → Phase 4 (controlled UX/copy/technical intervention) → Phase 5 (outreach/outcome evaluation). Statistical rules already locked: Wilson intervals for single proportions, Newcombe's Wilson interval for two-proportion differences, release floor n≥10, rate-stability floor denominator≥50, no demographic parity imposed on clinical screening results, no causal language without experimental design, race/ethnicity must never be imputed from name/geography/language/imagery.

## Your three research tasks

### Task 1 — Construct the Phase 1 benchmark (unlocks Q2, Q7, Q8 from `partial_now` toward `supported_now`)

The protocol specifies the benchmark decision but has not yet executed it. Using the **already-known geographic footprint** (top states: California, Florida, Texas, New York, Pennsylvania; 81 states/territories reached; 620,861 US users), do the following:

1. Pull current U.S. Census Bureau **ACS 5-year estimates** (most recent vintage) for these top-5 states, broken out by the same race/ethnicity categories used in the questionnaire (White alone, Black/African American alone, Hispanic/Latino of any race, Asian alone, American Indian/Alaska Native alone, Native Hawaiian/Pacific Islander alone, Two or more races).
2. Restrict the age band to whatever eligibility criteria BrainGuide actually targets — search for and cite BrainGuide's own stated target audience (older adults, caregivers) from `mybrainguide.org` or `usagainstalzheimers.org` public materials; if no explicit age floor is published, default to 45+ and 65+ as two sensitivity bands.
3. Produce a benchmark table: for each of the top-5 states and a population-weighted aggregate across all 81 reached states/territories, report the ACS race/ethnicity share for the chosen age band, with source citation (Census table ID, vintage year) for each figure.
4. Explicitly flag the unit mismatch risk already noted in the protocol: GA4 reach is session/user-based (device-level), while ACS is person-based. State this limitation prominently rather than silently presenting a ratio as precise.
5. Using this benchmark, compute a **provisional, clearly-labeled-as-provisional** representation ratio for Black and Hispanic/Latino groups (observed displayed-row share ÷ benchmark share), and report it as `associated`, not `observed`, per the protocol's inference-label vocabulary — because the observed share is a downstream-completer share, not an all-visitor share.

### Task 2 — Update and extend the mechanism literature for the four most consequential findings (supports Phase 3, Q7/Q8/Q9/Q4)

For each of the following four specific BrainGuide findings, find current (published within the last 3 years where possible) peer-reviewed or gray-literature evidence that speaks to the *specific mechanism*, not just general disparity framing already covered by the 12 existing citations:

1. **Speech-based cognitive assessment equity**: Is there published evidence on differential completion, accuracy, or comfort with speech/voice-based (as opposed to text-based) cognitive or health screening tools by race, ethnicity, age, or digital literacy? This directly bears on the SBC 4.8% completion crisis and whether it disproportionately affects priority populations.
2. **Trusted-messenger intervention effect sizes**: The existing citations (Portacolone, Epps, Chau) establish trust as a barrier and CBOs as a plausible bridge, but do not report quantified before/after effect sizes for trusted-messenger-based digital health tool adoption specifically. Find studies that measure actual completion-rate or adoption-rate lift from CBO/faith-based/community-health-worker referral versus general digital advertising, ideally in dementia, cognitive health, or adjacent chronic-disease screening contexts.
3. **Informant/caregiver-reported instrument abandonment**: The AD8 flow shows a 98% abandonment at one specific screen (`W-B-AD-9`). Search for research on why informant-reported (as opposed to self-administered) cognitive screening tools see high abandonment — is there a documented emotional, time-burden, or trust-related reason caregivers stop partway through reporting on a loved one's symptoms?
4. **Spanish-language health-tool functional equivalence testing methodology**: Beyond the general Spanish digital-literacy barrier literature already cited (Philpot et al.), find methodological guidance or case studies on how organizations have specifically tested and validated "functional equivalence" (not just translation accuracy) of a Spanish-language digital health screening tool — this will directly inform Phase 3's planned native-speaker review and Phase 4's Spanish UX intervention design.

### Task 3 — Cross-tabulate concern level against downstream action (answers SOW Q5, using only already-captured data)

This task does not require new external research — it requires reprocessing data already visible in the captured Evidence dashboard PDFs, and it directly answers the client's Q5 ("what proportion of moderate/high concern users go on to seek clinical care?").

1. From `Results Overview.pdf`, `AD8 Analysis.pdf`, `MIS Analysis.pdf`, and `SBC Analysis.pdf`, extract the persona/brain-health-label distribution (Good/Poor/Moderate for AD8/MIS/flow-routing; Low/Medium/High Risk for SBC) alongside whatever campaign, language, and device breakdowns are already reported per persona.
2. From `Result Pages.pdf`, `Clinical Trials.pdf`, and `Find a Provider.pdf`, extract resource-click and result-page-action counts **segmented by persona or brain-health label**, if the underlying PDF tables support that cut (check pages beyond what was already excerpted in `CONSOLIDATED.json`/`CONSOLIDATED.md` — the existing consolidation may not have pulled every available dimension from these reports).
3. If personas/brain-health labels are joinable to resource-action counts within the same report, compute: `(Poor/High-Risk respondents who click a provider or trial resource) / (all Poor/High-Risk respondents who reached a result page)`, and the equivalent rate for Good/Low-Risk respondents. Report both as `n/N` with a Wilson interval, per the protocol's existing statistical rules, and apply the release floor (n≥10) and rate-stability floor (denominator≥50).
4. If the underlying PDFs do **not** support this join at the available grain, say so explicitly and specify exactly what additional query or dashboard view (e.g., a new Evidence report cutting Result Pages actions by `brain_health` label) would be needed — this becomes a new, precisely-scoped Gate 1/2 addition to `DEMOGRAPHIC_EQUITY_COVERAGE.json` rather than a fabricated answer.
5. Do not conflate "clicked a provider/trial resource" with "sought clinical care" — per the existing protocol, a click is observed handoff intent, not a confirmed appointment or care action. Label this finding accordingly (`observed` for the click-through rate itself, `not assessable` for actual care-seeking without downstream provider/enrollment data).

## Output format

Produce a report with three sections mirroring the three tasks above, preceded by a short summary of the §0 reconciliation table. For Task 1, include the full benchmark table with citations and the provisional ratio with its inference label and stated limitations. For Task 2, produce a short annotated bibliography (5–10 new sources across the four sub-questions) with: full citation, 2–3 sentence summary of the specific finding, and one sentence on how it should modify or extend the existing `DEMOGRAPHIC_EQUITY_PROTOCOL.md` Phase 3 mechanism table. For Task 3, produce the concern-level-by-action-rate table (or the explicit "not joinable at current grain" finding plus the precise data request needed to unlock it) and a proposed new coverage-matrix row for SOW Q5. Do not restate findings already in `DEMOGRAPHIC_DISPARITY_ANALYSIS.md` — only add what is new or updates a stale citation. Label every claim `observed`, `associated`, `hypothesis`, or `not assessable` per the existing protocol vocabulary. Do not draw a population disparity conclusion beyond what the constructed benchmark and cited literature actually support.
