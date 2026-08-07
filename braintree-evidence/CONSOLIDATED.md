# BrainGuide Evidence Dashboard — Consolidated Semantic Guide

> **Snapshot:** 2026-08-06 · **Environment:** `dashboard.dev2.mybrainguide.org` · **Status:** provisional snapshot
>
> This document consolidates the 16 Evidence dashboard PDF captures in [`reports/`](./reports/) and [`journey-explorer.md`](./reports/journey-explorer.md) into one semantic guide. It explains **what the data is, what it measures, why it exists, how it is calculated, and what an LLM must not infer**. The companion [`CONSOLIDATED.json`](./CONSOLIDATED.json) contains the same contract in machine-readable form. **This is a semantic summary, not a complete row-level export:** selected tables, trends, campaign rows, geography rows, and graph edges are summarized rather than reproduced in full. The original PDFs remain the source for exhaustive row-level values.

## 1. Executive meaning

BrainGuide is a public-facing brain-health information and screening-navigation platform associated with UsAgainstAlzheimer's. People can learn about brain health, complete self- or informant-oriented screening flows, receive tailored guidance, and navigate to provider or clinical-trial resources.

The dashboard is not primarily answering “how many people visited?” Its analytic purpose is:

1. **Reach:** Who arrives, through which channels, devices, languages, and geographies?
2. **Need and pathway:** Is the visitor assessing themselves or someone else, and what content or questionnaire path do they take?
3. **Assessment routing:** What does the selected screening flow measure, and which result page does it produce?
4. **Friction:** Where do people stop progressing, especially in the questionnaire and SBC recording flow?
5. **Action:** Do visitors share results, seek a provider, or click toward clinical-trial resources?
6. **Equity and access:** Do content, language, device, and pathway patterns differ across self-reported groups?

### Clinical boundary

AD8, MIS, and SBC values are screening/routing measures used by this product. **Good, Poor, and Moderate are product result categories, not medical diagnoses.** A BrainGuide result is not a substitute for a clinical evaluation.

## 2. How to read any number

Before interpreting a number, identify these six things:

| Question | Why it matters |
|---|---|
| What is the population? | AD8 informants, MIS respondents, SBC entrants, scored SBC respondents, GA4 visitors, and result-page actions are different populations. |
| What is the grain? | A row may represent an event, pageview, session, user aggregate, respondent, or month. |
| What is the numerator and denominator? | “Completion,” “CTR,” “users,” and “opt-in rate” have report-specific denominators. |
| What is the date coverage? | Historical Data API aggregates and post-2026-05-17 raw GA4 events have different properties. |
| What is the source and refresh state? | Daily GA4/Ads data can lag 1–2 days; questionnaire data can lag about 9 days. |
| Is the statement observed or inferred? | A click is an observed engagement signal, not necessarily a completed care action or outcome. |

### Core count semantics

- **Users:** Usually distinct GA4 `user_pseudo_id` values in a period. A user can appear on multiple days; summing daily users can double-count.
- **Sessions:** GA4 sessions, not people.
- **Pageviews:** GA4 `page_view` events or the modeled pageview equivalent.
- **Started:** A questionnaire record/session that loaded or began a questionnaire; exact event semantics vary by report.
- **Received Score:** A respondent completed a scored `ad8`, `mis`, or `sbc` flow by reaching `GET_SCORE` or `GET_SBC`.
- **Got Information without Score:** A respondent completed the `c` / “Get Information” path without a calculated assessment score.
- **Not provided:** Missing, skipped, not collected for that flow, or no result URL. It is not automatically a negative answer.

## 3. Data architecture and lineage

```text
GA4 events ───────────────┐
GA4 historical backfill ──┤
Google Ads ────────────────┤──> dbt staging views ──> dbt marts ──> Evidence pages
DynamoDB questionnaire ───┤
Search Console ───────────┘
```

### Source layers

| Layer | BigQuery location | Contents | Used for |
|---|---|---|---|
| GA4 raw events | `analytics_257799278.events_*` | Event-level website behavior | Journeys, events, content, outbound actions |
| GA4 historical backfill | `reporting.ga4_*_historical` | Older Data API-derived aggregates | Longer historical trends |
| Google Ads | `googleads.ads_Campaign_8328184535`, `ads_CampaignBasicStats_8328184535` | Campaign metrics, costs, attributes | Campaign context |
| Questionnaire exports | `MyBrainguide.raw_dpn-chat-bot-content`, `raw_dpn-chat-bot-content-go365` | BrainGuide Standard and Go365 records | Results, scoring, demographics |
| Search Console | `searchconsole_brainguide.searchdata_*` | Search impressions, clicks, position | Search context |
| dbt staging | `reporting_staging` | Cleaned/normalized views; no cross-source joins | Transformation layer |
| dbt marts | `reporting` | Tables aggregated/joined for Evidence | Dashboard queries |

Evidence pages query the reporting marts rather than raw BigQuery tables. The dashboard’s mapping seeds are part of the semantic layer:

- `content_page_map.csv`: URL slug → category, title, locale, active/superseded status.
- `source_medium_map.csv`: source + medium → channel, paid status, campaign target.
- `persona_page_map.csv`: result URL → persona, audience, diagnosis status, brain-health label, score family.
- `campaign_name_map.csv`: GA4 campaign variants → canonical Ads campaign.
- `campaign_target_map.csv`: campaign prefixes → Clinical Trials, Find a Provider, or BrainGuide General.
- Frozen legacy seeds preserve weekly/monthly pre-DynamoDB or pre-daily-data history.

### Refresh state at capture

| Mart/source | Latest date |
|---|---:|
| Core Web Metrics | 2026-08-04 |
| GA4 Geography | 2026-08-04 |
| Top Content | 2026-08-04 |
| User Journeys | 2026-08-04 |
| Outbound Clicks | 2026-08-04 |
| Traffic Attribution | 2026-08-04 |
| Google Ads Campaigns | 2026-08-03 |
| Search Console | 2026-08-03 |
| Questionnaire Responses | 2026-08-02 |

## 4. Scoring and result routing

These are separate scales. **Never average or compare their raw scores as though they were one measure.**

### AD8 — informant flow

- **Who:** A caregiver or family member answering about someone else.
- **What:** Eight observed changes in memory and daily functioning.
- **Formula:** `sum(Yes answers)`.
- **Answers:** Yes = 1; No = 0; Not sure = 0.
- **Range:** 0–8.
- **Direction:** Lower = less concern; higher = more concern.
- **Product bands:** Good = 0–1; Poor = 2–8; High Concern = 5–8.

Snapshot: **12,330 completions**, average score **4.17**, **17.3% Good**, **82.7% Poor**, **47.4% High Concern**, and **91.0% with demographics**.

The most frequently marked “Yes” AD8 item was Q8 (“Daily problems with thinking or memory,” 71.0%); the least frequent was Q5 (“Forgets correct month or year,” 25.8%). Demographics describe the **informant**, not the person they are concerned about.

### MIS — self-administered memory flow

- **Who:** Respondent in the MIS flow, generally self-administered.
- **What:** Four-word free and category-cued recall.
- **Formula:** `(2 × free-recalled words) + cued-recalled words`.
- **Range:** 0–8.
- **Direction:** Higher = better memory performance.
- **Product bands:** Good = 5–8; Poor = 0–4.

Snapshot: **107,976 completions**, average score **6.28**, **79.7% Good**, **19.6% Poor**, and **92.0% with demographics**. The dashboard contains 10 English word sets and 8 Spanish sets; small Spanish rows should not be compared with the large English sets without a prespecified analysis.

### SBC — speech-based flow

- **Who:** Self-administered respondent speaking about themselves.
- **What:** Continuous speech-based score from 0 to 1.
- **Direction:** Higher = lower risk in this product’s routing.
- **Bands:**
  - Low Risk / Good: `> 0.5` → `/navigate-next-steps-1/`
  - Medium Risk / Moderate: `0.2–0.5` → `/navigate-next-steps-2/`
  - High Risk / Poor: `< 0.2` → `/navigate-next-steps-3/`

Snapshot: **36,803 flow entries**, only **1,751 scored results**, a **4.8% entry-to-scored-result rate**. Among scored results: 31.8% Low Risk, 25.2% Medium Risk, and 43.0% High Risk.

Most SBC entrants do not produce a score. The dashboard does not distinguish recording failure from abandonment, so the 4.8% rate is an operational completion signal, not a clinical-risk estimate for all entrants. At exact boundaries, use the routed result page rather than recomputing from a rounded score.

### Flow `c` — information without score

The `c` flow is the “Get Information” path. It returns content/result routing but no assessment score and collects no scored-flow demographics. It represents approximately 24% of completions in the Scoring Reference. It must not be combined with AD8, MIS, or SBC score distributions.

### Persona routing

Assessment personas use three axes: **Who** (Self vs Someone Else), **Diagnosed**, and **Indicating Brain Health**. The eight assessment personas are:

| Persona | Slug | Legacy label | Result URL |
|---|---|---|---|
| Self · Not Diagnosed · Good | `self-undx-good` | Julia | `/maintain-brain-health-1/` |
| Self · Not Diagnosed · Poor | `self-undx-poor` | Ben | `/address-memory-concerns-1/` |
| Self · Diagnosed · Good | `self-dx-good` | Meredith | `/understand-next-steps-2/` |
| Self · Diagnosed · Poor | `self-dx-poor` | Carol | `/understand-next-steps-1/` |
| Someone Else · Not Diagnosed · Good | `other-undx-good` | Nicole | `/guide-loved-ones-4/` |
| Someone Else · Not Diagnosed · Poor | `other-undx-poor` | Anson | `/guide-loved-ones-3/` |
| Someone Else · Diagnosed · Good | `other-dx-good` | Olivia | `/guide-loved-ones-2/` |
| Someone Else · Diagnosed · Poor | `other-dx-poor` | Farah | `/guide-loved-ones-1/` |

SBC has three separate personas: `self-sbc-low`, `self-sbc-med`, and `self-sbc-high`.

## 5. Consolidated report catalog

### 5.1 Questionnaire Journey Explorer ([`journey-explorer.md`](./reports/journey-explorer.md))

- **Measures:** A branching questionnaire map, qCurrent screen-arrival events, directed transitions, node volumes, and inferred step loss.
- **Why:** Shows how visitors move through Intro, MIS, AD8, SBC, and Results/Common flows, and where progression falls between screens.
- **Grain:** Event-level questionnaire transitions and qCurrent arrivals summarized as nodes/edges. A node volume is not automatically a unique-user count.
- **Captured view:** July 4–August 4, 2026 selected window; the backend load is described as 537,573 rows spanning November 2024 onward.
- **Snapshot:** 117 nodes, 163 transitions, 352,372 events in the selected view. Example: `W-A1` 26,221 → `W-A2` 21,734.
- **qCurrent rule:** qCurrent records arrival at a screen via a button click. With no explicit exit event, abandonment is inferred as the gap between one step’s volume and the next step’s volume.
- **Caveats:** Inferred abandonment is not observed exit; event counts may not be unique users; this markdown is a synthesis, not a complete graph export.

### 5.2 Results Overview

- **Measures:** Starts, scored completions, non-scored information completions, result routing, demographics, campaigns, and trends.
- **Why:** Primary operational view of questionnaire participation and outcomes by product route.
- **Population/grain:** Modeled respondent record summarized by date, questionnaire, flow, language, campaign/source, result, persona, and demographics. Pre-2024 history is monthly aggregate only.
- **Coverage:** BrainGuide Standard January 2024 onward; Go365 February 2025 onward; legacy trend back to March 2021.
- **Snapshot:** 93,203 starters; score completion rate 77.7%; Good 39,463; Moderate 168; Poor 15,142; Not provided 17,646. The largest persona is Self · Not Diagnosed · Good: 35,168 (48.6%).
- **Critical definitions:** Demographic filters apply from Received Score downward. Started uses `started_date`; outcome/demographic analysis uses `completed_date`, so totals may not reconcile exactly.
- **Do not infer:** Brain-health labels are result-page routing labels, not clinical diagnoses.

### 5.3 AD8 Analysis

- **Measures:** Informant-reported changes across eight questions.
- **Why:** Understand caregiver concern, score distribution, respondent profile, campaign composition, and trend.
- **Grain:** Completed AD8 respondent summarized by question, score, persona, informant demographics, campaign, and month.
- **Snapshot:** 12,330 completions; average 4.17; 82.7% Poor.
- **Caveats:** Informant demographics are not subject demographics; Not Sure scores as 0; product bands are not diagnoses.

### 5.4 MIS Analysis

- **Measures:** Weighted free/cued recall performance.
- **Why:** Understand memory-screen distribution, word-set behavior, self-reported context, demographics, campaign mix, and trends.
- **Grain:** Completed MIS respondent summarized by word set, score, persona, demographics, campaign, and month.
- **Snapshot:** 107,976 completions; average 6.28; 79.7% Good.
- **Caveats:** Small word-set rows are unstable; screen category is not a diagnosis.

### 5.5 SBC Analysis

- **Measures:** Entry-to-scored-result completion and risk distribution among scored speech assessments.
- **Why:** Separates operational recording/completion friction from risk composition.
- **Grain:** SBC entrants for completion; scored SBC respondents for risk/demographic/campaign analysis.
- **Snapshot:** 36,803 entries; 1,751 scored; 4.8% completion.
- **Caveats:** Abandonment and recording failure are not separated; scored respondents are selected.

### 5.6 Scoring Reference

- **Measures:** No population metric; this is the semantic key for formulas, thresholds, flow types, result URLs, and personas.
- **Why:** Prevents incompatible scales and routes from being conflated.
- **Critical rule:** `c` has a result route but no score; SBC boundary categories follow the routed result URL.

### 5.7 Top Content

- **Measures:** Pageviews, users, sessions, unique pages, categories, locales, and unmapped slugs.
- **Why:** Shows what content attracts traffic and where URL taxonomy needs maintenance.
- **Grain:** GA4 page-level aggregate by page path/title/category/locale and date.
- **Coverage:** Historical Data API estimates before 2026-05-17; raw export thereafter.
- **Snapshot:** 516,480 pageviews; 174,486 users; 182,074 sessions; 430 unmapped pages; English 94.5% of pageviews and Spanish 5.5%.
- **Top categories:** Home 267,120 pageviews; Result 111,261; Hub 54,560; Clinical Trials 50,422; Find a Provider 16,168.
- **Caveats:** Unmapped pages reflect taxonomy gaps; pageviews are not unique people; historical API metrics can have small inconsistencies.

### 5.8 Top Content by Demographic

- **Measures:** Pages viewed by self-reported questionnaire demographic groups.
- **Why:** Supports within-group content affinity and access analysis.
- **Grain:** Page path × demographic group, using the dashboard's demographic-attribution model over GA4 user records. This should not be interpreted as validated person-level linkage unless the underlying join/coverage is separately approved.
- **Coverage:** Approximately 2026-05-24 onward.
- **Snapshot:** 9,600 pageviews; 1,964 users; 2,279 sessions; 155 unique pages. Category shares: Hub 29%, Journey 16%, Clinical Trials 15%, Resources 14%, Find a Provider 9%.
- **Caveats:** Self-selected subset only; compare within-group shares rather than raw counts; demographic answers are rolled to pages viewed during the export window, not causal page effects.

### 5.9 Geographic Traffic

- **Measures:** GA4 users/sessions by country, US state/territory, and city, plus users per 100,000 residents and per 100,000 adults 65+.
- **Why:** Describes geographic reach and helps prioritize regional access questions.
- **Grain:** GA4 user/session aggregates by geography and month.
- **Coverage:** From 2024-11-06 onward.
- **Snapshot:** US 620,861 users and 570,877 sessions across 81 states/territories; global 690,800 users and 680,393 sessions across 211 countries.
- **Formulas:** `users / total population × 100,000`; `users / (population × 65+ share) × 100,000`.
- **Caveats:** Cookie/device-based users can recur across days; geography is not self-reported equity data or service need.

### 5.10 User Journeys

- **Measures:** Immediate previous/next pageviews, arrivals, departures, exits, and device-specific exit rates.
- **Why:** Shows page navigation and where another pageview stops occurring.
- **Grain:** Within-session page-view sequence, not an individual longitudinal journey.
- **Coverage:** Raw GA4 event export from 2026-05-17.
- **Home snapshot:** 64,626 sessions arriving; 58,021 landed directly; 48,300 exits; 74.9% exit rate. Next page: Maintain Brain Health 1 with 10,220 sessions.
- **Device exit rates:** Mobile 74.7%; tablet 80.2%; desktop 62.8%.
- **Caveat:** Exit rate is not bounce rate. Event interactions can occur without another pageview.

### 5.11 Site Events

- **Measures:** Event-name inventory, total volumes, first/last seen dates, and derived categories.
- **Why:** Establishes what is instrumented and what requires semantic validation.
- **Coverage:** Raw GA4 export; captured event table spans 2026-06-06 to 2026-08-04.
- **Snapshot:** 1,760,403 events across 17 event names. Largest: `Questionnaire` 676,341; `page_view` 493,035; `userId` 164,668; `session_start` 145,262; `web_questionnaire_start` 47,172; `web_questionnaire_finish` 13,642; `outbound_click` 9,563; `tailored_page_events` 2,862.
- **Caveat:** Event volume is not unique users or completion. `Questionnaire` is repeated and cannot automatically be used as a completion metric.

### 5.12 Result Pages

- **Measures:** Save PDF, Email Results, audio, provider navigation, and other tailored-page actions.
- **Why:** Measures engagement with result guidance and next-step options.
- **Grain:** Action event aggregate by persona, score family, brain-health label, language, device, and action. The mart name in the consolidated JSON is a dashboard-lineage label inferred from the report's source descriptions; confirm the exact SQL table name before building against it.
- **Coverage:** November 2024 onward; Data API through 2026-05-17, raw export after.
- **Snapshot:** 3,286 actions; 7 action types; 12 result pages with activity.
- **Caveat:** An action indicates engagement/intent unless its event definition explicitly represents completion. Historical API portion lacks session deduplication.

### 5.13 Result Sharing

- **Measures:** Share-PDF clicks and explicit keep-in-touch consent at sharing time.
- **Why:** Separates sharing behavior from contactability consent without displaying email addresses.
- **Grain:** One row per share click, summarized by result page, questionnaire, language, and month.
- **Coverage:** June 2022 onward.
- **Snapshot:** 3,113 filtered shares; 225 opted in; 7.2% opt-in. BrainGuide Standard: 2,689 shares/135 opt-ins (5.0%); Go365: 422/89 (21.1%).
- **Caveat:** Sharing is not consent. Email addresses are deliberately excluded; contact requires an authorized process outside the dashboard.

### 5.14 Clinical Trials

- **Measures:** Visits to English/Spanish Clinical Trial Connector pages and outbound trial-matching clicks.
- **Why:** Measures research-navigation interest and the external handoff.
- **Coverage:** Visits from June 2025; outbound custom dimensions from May 2026.
- **Snapshot:** 50,422 visits; 8,331 clicks; 16.5% visit-based CTR.
- **Caveat:** CTR is clicks divided by visits, not unique-person conversion, enrollment, or trial matching.

### 5.15 Find a Provider

- **Measures:** Visits to English/Spanish provider-finder pages and outbound provider-referral clicks.
- **Why:** Measures care-navigation interest and external referral handoff.
- **Coverage:** Visits from April 2026; outbound custom dimensions from May 2026.
- **Snapshot:** 16,168 visits; 1,232 clicks; 7.6% visit-based CTR. Click destinations: Medicare 49.5%, Isaac Health 33.1%, Synapticure 17.4%.
- **Caveat:** Click is referral intent, not an appointment or care outcome. Spanish volume is very small.

### 5.16 Data & Mapping Reference

- **Measures:** No user population; documents freshness, seeds, raw tables, and dbt layers.
- **Why:** Establishes lineage and semantics for every other report.
- **Key rule:** Evidence queries marts; it does not query raw tables directly. Mapping changes can change categories without changing underlying events.

### 5.17 Monthly Report Generator

- **Measures:** Report-ready monthly/YTD web sessions, visitors, questionnaire starts, profiles, and demographics.
- **Why:** Produces recurring management-report summaries and PowerPoint output.
- **Selected July 2026 snapshot:** 1,536 web sessions vs 4,901 in July 2025; 256,338 web sessions YTD; 25,581 questionnaire starts in July 2026; 213,005 starts YTD; 688,964 all-time starts.
- **Caveat:** Presentation totals use report-specific current/historical rules; PowerPoint generation is a delivery workflow, not a separate source of truth.

## 6. Cross-report interpretation

### Reconciliation flags

The source dashboards themselves contain two score-distribution mismatches that must remain explicit:

- **AD8:** 10,170 Poor + 2,125 Good = 12,295 outcome rows versus 12,330 completion KPI, leaving 35 records not represented in the two outcome categories.
- **MIS:** 21,159 Poor + 86,039 Good = 107,198 outcome rows versus 107,976 completion KPI, leaving 778 records not represented in the two outcome categories.

The source does not expose a definitive “unclassified score” rule for these remainders in the captured outcome tables. Do not assign the remainder to Good or Poor until the mart logic is checked.



### What stands out safely

1. **Different flows have different denominators.** SBC has 36,803 entries but only 1,751 scored results; MIS and AD8 are completed-assessment populations. Raw counts must not be ranked without cohort context.
2. **SBC has an operational completion problem.** The observed 4.8% entry-to-scored-result rate is the strongest direct signal, but the dashboard cannot separate abandonment from recording failure.
3. **Result labels are routing outcomes.** Good/Poor/Moderate describe the product’s guidance route, not medical diagnoses.
4. **English dominates web traffic.** Spanish pageviews are 5.5% in Top Content, while Spanish provider/trial page volumes are also much smaller. This warrants language-access investigation, not a stable Spanish-vs-English quality ranking.
5. **Care and research handoffs are measurable but incomplete.** Provider and trial clicks show intent; they do not prove appointments, enrollment, or downstream outcomes.
6. **The raw event boundary matters.** Page journeys and site-event semantics rely on the raw export from 2026-05-17. Historical Data API aggregates are not identical measurements.
7. **Content taxonomy is an active data-quality concern.** 430 unmapped pages appear in the Top Content snapshot, so category-level conclusions can change as mappings are maintained.

## 7. Known contradictions and reconciliation rules

| Issue | Rule |
|---|---|
| PDF extraction showed broken digits under `pypdf` | Use PyMuPDF extraction; the values here were re-extracted and spot-checked. |
| Capture time differs from source latest date | Use each report’s freshness/coverage, not the PDF timestamp alone. |
| Results Overview totals do not perfectly reconcile | Funnel counts use `started_date`; outcomes use `completed_date`. |
| SBC boundaries may look inconsistent | Use the routed result URL at exact 0.2/0.5 boundaries. |
| Journey exit rate looks like bounce rate | It is only “no next pageview,” not GA4 bounce rate. |
| Historical and current GA4 metrics differ | Data API backfill and raw export have different deduplication and dimensionality. |
| Not provided vs Prefer not to answer | Not provided can mean skipped/not collected/no result; explicit refusal is a separate questionnaire option where preserved. |
| Demographic content attribution looks person-specific | It is a within-group descriptive attribution over pages viewed in the export window, not a causal page effect. |

## 8. What an LLM should and should not do

### Before answering

1. Name the report and population.
2. State metric, numerator, denominator, unit, grain, and period.
3. Keep AD8, MIS, SBC, and `c` flow semantics separate.
4. Check raw-export vs historical-API boundaries.
5. Mention missingness, small cells, suppression, and selection bias.
6. Use “observed,” “associated,” or “hypothesis” rather than “caused.”
7. Treat Good/Poor/Moderate as product routing labels, not diagnoses.

### Safe answer structure

```text
Finding: what was observed.
Measure: numerator, denominator, unit, grain, and period.
Population: included and excluded groups.
Why it matters: operational/product relevance.
Caveats: source, freshness, sample size, linkage, and clinical limits.
Next action: a validation or product action justified by the evidence.
```

### Example

> **Observed:** SBC scored-result completion was 4.8% (1,751 / 36,803 entrants) in the captured selection. **Why it matters:** the largest operational signal is entry-to-recording completion, not the risk distribution among people who received a score. **Caveat:** the dashboard does not distinguish abandonment from recording failure, and scored respondents are a selected subset. **Next action:** validate recording errors and step-level events by device and language.

## 9. Recommended next implementation plan

This consolidation should become the semantic foundation for future analytics/AI work:

### Phase 1 — Registry and quality gate

- Convert the JSON into versioned `ReportContract` / `MetricDefinition` objects.
- Record source, grain, numerator, denominator, date coverage, refresh time, and validation status.
- Add checks for missing days, schema drift, duplicated grain, unmapped URLs, incomplete periods, and event spikes.
- Keep historical Data API and raw-export periods explicitly labeled.

### Phase 2 — Deterministic insight objects

- Compute findings in code, not in the LLM.
- Attach `evidence_level` (`observed`, `comparative`, `associated`, `experiment_supported`, `not_assessable`).
- Attach `interpretation_status` (`none`, `hypothesis`, `action_recommendation`).
- Include provenance, denominator, quality checks, suppression decisions, and limitations in every finding.

### Phase 3 — Evidence overlay

- Validate whether a consented, de-identified session or transaction key actually links questionnaire data to GA4.
- Report linkage coverage by period, language, questionnaire, and site version.
- Enforce small-cell, denominator, complementary-suppression, and difference-attack protections.
- Compare demographic groups within the same cohort and period, not against an undefined “overall” population.

### Phase 4 — LLM explanation layer

- Give the LLM approved aggregate evidence objects, not raw confidential rows.
- Let it explain, prioritize, ask clarifying questions, and suggest validation steps.
- Do not let it calculate funnels, infer causal effects, reinterpret score bands, or treat arbitrary event names as outcomes.

## 10. Source inventory

- `AD8 Analysis.pdf`
- `Clinical Trials.pdf`
- `Data & Mapping Reference.pdf`
- `Find a Provider.pdf`
- `Geographic Traffic.pdf`
- `MIS Analysis.pdf`
- `Monthly Report Generator.pdf`
- `Result Pages.pdf`
- `Result Sharing.pdf`
- `Results Overview.pdf`
- `SBC Analysis.pdf`
- `Scoring Reference.pdf`
- `Site Events.pdf`
- `Top Content by Demographic.pdf`
- `Top Content.pdf`
- `User Journeys.pdf`
- `journey-explorer.md`

For the full metric registry, report snapshots, source tables, routing map, and machine-readable fields, use [`CONSOLIDATED.json`](./CONSOLIDATED.json). See [`README.md`](./README.md) for the package map, direct source links, and equity-analysis reading order.
