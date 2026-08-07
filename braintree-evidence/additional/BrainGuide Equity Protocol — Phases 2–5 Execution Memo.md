## Executive Summary

Task 1 (benchmark decision record) can be executed now using publicly available ACS/Census data and the repository's curated race and gender rows, and is completed below with representation ratios, percentage-point gaps, and 95% confidence intervals. Tasks 2–5 remain **partially executable at best**: the repository's `journey-explorer.md` and `CONSOLIDATED.md` contain aggregate funnel and event-inventory summaries that support a directional read of drop-off, but none of the five tasks can be fully closed without raw GA4/GTM event-level exports, an approved race/ethnicity-to-funnel linkage, survey execution, and contact-center/referral data — none of which exist in this repository snapshot. This memo documents what moves to `supported_now`, what remains `partial_now` or `blocked_external_input`, and exactly what is missing for each.

## Task 1 — Benchmark Decision Record (Unlocks Q1/Q2/Q6/Q7/Q8)

### Benchmark selection

The recommended primary benchmark is the **2023 American Community Survey (ACS) 5-year national population distribution**, used here as a first-pass national reference pending an agreed service-area-matched benchmark. National 2023 estimates: non-Hispanic White 57.22%, Black or African American (alone) 11.64% (Black population 42.3 million of ~333 million), Hispanic or Latino (any race) 19.55% (65.2 million, 19.5% of the population), and roughly 18.0% of the population age 65 and older as of 2024. National gender split is approximately 50.5% female / 49.5% male. A **service-area-matched ACS benchmark restricted to BrainGuide's actual geographic footprint and the platform's intended age-eligible audience is still required before publishing any disparity claim**; the calculations below use the national benchmark only as an interim, clearly labeled reference point, consistent with the protocol's instruction to report at least one sensitivity benchmark and never treat a national percentage as a universal comparator.[^1][^2][^3]

### Race/ethnicity crosswalk decision

The Results Overview race rows are **not** a mutually exclusive OMB/HHS-standard race-and-ethnicity breakdown: "Hispanic/Latino" appears as a display row alongside single-race categories (White/Caucasian, Black/African American, Asian, etc.), meaning respondents who identify as both, e.g., White and Hispanic, are represented in the Hispanic/Latino row rather than double-counted in White/Caucasian. "Mixed" is a separate self-reported multi-select category and is not decomposed into constituent races. This means direct comparison against ACS categories (which separately report "Hispanic or Latino, any race" as an ethnicity crosscutting all race categories) is **not a clean crosswalk** — the repository's race rows should be treated as a single combined self-identification taxonomy, not remapped silently into ACS race/ethnicity cells. Any benchmark ratio calculated here is therefore approximate and should be flagged as pending a validated crosswalk decision by the data owner.

### Representation ratios and percentage-point gaps

| Group | Observed n | Observed share (%) | 95% CI | Benchmark share (%) | Representation ratio | PP gap |
|---|---:|---:|---|---:|---:|---:|
| White/Caucasian | 42,556 | 77.90 | 77.55–78.25 | 57.22 | 1.36 | +20.68 |
| Black/African American | 2,433 | 4.45 | 4.28–4.63 | 11.64 | 0.38 | −7.19 |
| Hispanic/Latino | 2,675 | 4.90 | 4.72–5.08 | 19.55 | 0.25 | −14.65 |
| Asian | 1,417 | 2.59 | 2.46–2.73 | — | — | — |
| Mixed | 1,272 | 2.33 | 2.21–2.46 | — | — | — |
| American Indian/Alaska Native | 536 | 0.98 | 0.90–1.07 | — | — | — |
| Native Hawaiian/Pacific Islander | 90 | 0.16 | 0.13–0.20 | — | — | — |
| Other/Not Listed | 573 | 1.05 | 0.97–1.14 | — | — | — |
| Prefer not to answer | 3,074 | 5.63 | 5.44–5.82 | — | — | — |



| Group | Observed n | Observed share (%) | 95% CI | Benchmark share (%) | Representation ratio | PP gap |
|---|---:|---:|---|---:|---:|---:|
| Female | 39,889 | 70.12 | 69.74–70.50 | 50.5 | 1.39 | +19.62 |
| Male | 14,740 | 25.91 | 25.55–26.27 | 49.5 | 0.52 | −23.59 |
| Non-binary/gender-fluid/other | 243 | 0.43 | 0.38–0.48 | — | — | — |
| Prefer not to answer | 2,013 | 3.54 | 3.39–3.69 | — | — | — |

Confidence intervals use the Wilson score method against the displayed-row denominator (n=54,626 race, n=56,885 gender) and describe only the precision of the observed composition within that population, not sampling uncertainty relative to a broader eligible-visitor population. Under the interim national benchmark, Black respondents show a representation ratio of 0.38 (62% below national share) and Hispanic/Latino respondents show a ratio of 0.25 (75% below national share), while White respondents show a ratio of 1.36. These figures should be treated as provisional signals pending the service-area benchmark and crosswalk validation described above — per the protocol, no "under-represented" label should be finalized without that record.

### What remains blocked in Task 1

The all-eligible-visitor denominator (i.e., race/ethnicity at first contact rather than only among scored-completion respondents) is still unavailable, so this benchmark comparison applies only to the ~75% of the Results Overview population with recorded race data, not to the full visitor base. A service-area ACS pull matched to BrainGuide's actual state/metro reach and to the platform's intended age-eligible audience has not been executed and is needed before this moves fully to `supported_now`.

## Task 2 — Event-Level Funnel and Abandonment Analysis (Unlocks Q3/Q4/Q16)

The repository's `journey-explorer.md` synthesis (drawn from the Questionnaire Explorer's Insights and Analytics views, covering November 2024–August 2026, with a focused July 4–August 4, 2026 window) provides an aggregate, pre-built version of much of what Task 2 requests, though not at raw event-log grain.

### Funnel volumes and step loss (July 4 – August 4, 2026 window)

| Step | Users reaching step | Step loss from prior step | Flag |
|---|---:|---:|---|
| Landing (W-A1) | 26,221 | — | — |
| W-A2 | 21,734 | ~17.0% | — |
| W-A5-A | 17,903 | ~17.6% | — |
| W-A3-B | 9,327 | ~47.9% | HIGH |
| MIS entry (W-B-MIS-1) | 8,126 | — | Myself flow start |
| MIS step 9 (W-B-MIS-9) | 6,876 | ~15.4% | Stable progression |



### Highest-severity leaks flagged by the platform's own anomaly detector

| Step | Flow | Users in | Users out | Drop-off | Severity |
|---|---|---:|---:|---:|---|
| W-B-AD-9 | Informant (AD8) | 19,600 | 369 | 98% | HIGH |
| W-S1 | Speech (SBC) | 35,600 | 17,300 | 51% | HIGH |
| W-D4-A-SBC | Speech (SBC) | 16,300 | 1,700 | 89% | HIGH |



Platform-wide, total questionnaire starts across the full captured history are 514,561, with an overall completion rate to the final demographic step of 34% and an average step loss of 2.1%, against a single worst step loss of 98%. Tablet users showed materially worse Speech-flow (SBC) drop-off than desktop at the same step (71% vs. 42% at W-S1), which is a device-segmented signal the protocol explicitly asked for, though it does not yet extend to demographic or language segmentation.

### Campaign-level completion extremes

| Campaign | Starts | Completion rate | Tier |
|---|---:|---:|---|
| (organic) | 41,225 | 59% | High performer |
| bg_July2025_ad4 | 8,138 | 57% | High performer |
| go365landing-en | 18,402 | 54% | High performer |
| Website traffic-Display-October 30 | 78,601 | 13% | Low performer |
| Website traffic-Display-revamp | 20,111 | 14% | Low performer |
| Campaign 6592414342203 | 9,325 | 0.1% | Critical failure |



### What remains blocked in Task 2

The unit of analysis in `journey-explorer.md` is inferred arrival-event volume ("qCurrent" fires on arrival, with abandonment inferred from the volume gap between consecutive steps), not a deduplicated person- or session-level funnel with an explicit exit/abandonment event; this is exactly the ambiguity the protocol warns against. AD8, MIS, and SBC flows are already kept structurally separate in this data, satisfying that protocol rule, but demographic and language segmentation of the drop-off table (beyond the device cut already shown) has not been produced, and the March 2026 relaunch date has not been confirmed against a page/event equivalence crosswalk, so no pre/post comparison can be certified. This task should be reclassified from `blocked_external_input` to `partial_now` — closer to resolution than previously assessed, but still short of `supported_now` because the raw GA4 event-level export needed for true deduplication and demographic overlay is not in this repository.

## Task 3 — Mechanism Validation for the Observed Disparity (Unlocks Q7/Q8/Q9)

No new event telemetry, error logs, native-speaker content review, or interview/co-design data were located in the repository beyond what `DEMOGRAPHIC_DISPARITY_ANALYSIS.md` already documents as hypotheses. The disparity analysis's Spanish-language figures — 5.5% of Top Content pageviews, an 18.0% English vs. 5.8% Spanish clinical-trials visit-to-click rate, and a suppressed (n<10) Spanish Find-a-Provider click rate — describe volume and click-through only, not functional equivalence, task completion, or error rates by language. This task remains `blocked_external_input`; execution requires product/engineering access to error telemetry and a native-speaker UX review that sits outside the analytics evidence package.

## Task 4 — Outcome Survey Execution and Analysis (Unlocks Q4/Q24)

No survey instrument, invitation log, or response data were found in the repository. The equity protocol defines the intended design (response-rate and nonresponse reporting, self-reported non-causal framing), but no results exist to analyze. This task remains `blocked_external_input`; it requires AHSR/BrainGuide to actually field the survey to an approved cohort before any outcome table can be produced.

## Task 5 — Clinical Care-Seeking Outcome Linkage (Unlocks Q5/Q17/Q18/Q19)

The repository evidence supports only the lowest outcome tier — visit and click counts for Clinical Trials and Find a Provider pages, split by language — which the protocol explicitly classifies as observed handoff intent, not care-seeking. No moderate/high-concern segmentation, no self-reported provider-discussion or appointment data, and no contact-center/referral linkage were found. This task remains `blocked_external_input`; it requires (a) the concern-level scoring output linked to session identifiers, (b) survey or interview data on self-reported provider discussion, and (c) consented contact-center or referral records — none of which are present in this snapshot.

## Coverage Matrix Update Recommendation

| Row (Q#) | Prior status | Recommended update | Rationale |
|---|---|---|---|
| Q1, Q2 | `supported_now` / `partial_now` | `partial_now`, refined | Interim national benchmark and CI calculations added; service-area benchmark and crosswalk validation still pending |
| Q6 (gender) | `partial_now` | `partial_now`, refined | Representation ratio (0.52 male, 1.39 female vs. national) now calculated; no engagement/funnel-by-gender linkage yet |
| Q3, Q4, Q16 | `blocked_external_input` | `partial_now` | Aggregate step-loss and device-segmented drop-off now documented from `journey-explorer.md`; raw event-level dedup and demographic overlay still missing |
| Q7, Q8, Q9 | `partial_now` | No change | No new mechanism-validation evidence found; still requires telemetry/UX/interview access outside this repository |
| Q23 (relaunch) | `blocked_external_input` | No change | Exact relaunch date and event/page crosswalk still unconfirmed |
| Q4 (awareness), Q24 | `blocked_external_input` | No change | No survey data exists to analyze |
| Q5, Q17, Q18, Q19 | `partial_now` / `blocked_external_input` | No change | Only visit/click handoff-intent signals exist; no linked downstream outcome data |

## What Remains Blocked and Exactly What Is Missing

- **Service-area ACS benchmark and race/ethnicity crosswalk decision record** — needed to finalize Task 1 beyond the interim national reference used here; requires the data owner to select geography, age band, and crosswalk method.
- **Raw GA4/GTM event-level export with a defined unit of analysis and deduplication rule** — needed to convert the aggregate `journey-explorer.md` funnel into a validated, demographic-linkable step-rate table; the current evidence is dashboard-level, not raw event rows.
- **Confirmed March 2026 relaunch date and page/event equivalence crosswalk** — needed before any pre/post-relaunch comparison can be certified.
- **Error telemetry, native-speaker content review, and interview/co-design data** — needed to test the mechanism hypotheses behind the observed disparity; not available in this analytics-only repository.
- **Executed follow-up survey with invitation and response logs** — needed for any awareness/confidence outcome table; no survey has been fielded yet per available files.
- **Concern-level-to-session linkage, self-reported provider-discussion data, and consented contact-center/referral records** — needed to move beyond visit/click "intent" signals to any defensible care-seeking outcome estimate.

None of these five gaps can be closed through further analysis of the existing repository files; each requires a new data collection, decision, or access step from AHSR, BrainGuide's engineering team, or the survey/outreach process itself.

---

## References

1. [New Estimates Highlight Differences in Growth Between the U.S. Hispanic ...](https://www.census.gov/newsroom/press-releases/2024/population-estimates-characteristics.html) - Between 2022 and 2023, the Hispanic population accounted for just under 71% of the overall growth of...

2. [Older Adults Outnumber Children in 11 States and Nearly Half of U.S. Counties](https://www.census.gov/newsroom/press-releases/2025/older-adults-outnumber-children.html) - The U.S. population age 65 and older rose by 3.1% (to 61.2 million) while the population under age 1...

3. [United States Population by Gender - 2025 Update](https://www.neilsberg.com/insights/united-states-population-by-gender/) - According to the ACS survey, of the total United States population of 332.39 million, 49.50% percent...
