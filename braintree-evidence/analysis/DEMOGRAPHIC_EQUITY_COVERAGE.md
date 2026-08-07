# BrainGuide Equity Coverage Matrix

> **Version:** 2026-08-07.1
> **Purpose:** Make every client question and implementation gate auditable: what the current evidence answers, what it only partially answers, and what remains blocked.
> **Important:** `blocked_external_input` means the method is defined but the required external data, owner decision, permission, or intervention result is not present in this repository snapshot.

## Status legend

| Status | Meaning |
|---|---|
| `supported_now` | The current captured evidence supports a bounded descriptive answer with explicit provenance and limitations. |
| `partial_now` | The current evidence supports useful descriptive context, but not the full client question or a stable comparative claim. |
| `blocked_external_input` | The method and acceptance criteria are defined, but required data, owner decisions, permissions, or intervention results do not exist in this repository snapshot. |
| `not_applicable_to_snapshot` | The question requires a live product/evaluation phase rather than additional interpretation of the captured PDFs. |

## Client questions

| # | Gate | Status | Question | Current answer / coverage | What remains to unlock full support |
|---:|---|---|---|---|---|
| 1 | 1 | `supported_now` | Who is BrainGuide reaching overall? | Aggregate web reach, geography, device, language, content, and questionnaire participation are described; race/ethnicity reach is not available at the all-visitor grain. | None for bounded aggregate description; benchmark and linked early-funnel demographics for equity reach. |
| 2 | 2 | `partial_now` | Are we reaching priority populations equitably? | White respondents are 77.9% of displayed race rows; Black respondents are 4.5%; Hispanic/Latino respondents are 4.9%. This is an observed composition signal, not a population representation ratio. | Owner-approved benchmark, compatible race/ethnicity crosswalk, all-eligible denominator, and sensitivity analysis. |
| 3 | 2 | `partial_now` | Who completes the questionnaire? | Overall starts, scored outcomes, information-only paths, and flow-specific completion snapshots are available, but demographic completion rates are not. | Versioned event-level funnel plus optional early demographics and linkage coverage. |
| 4 | 2 | `blocked_external_input` | Who drops off, and where? | Aggregate journey gaps and SBC's 4.8% scored-result rate identify operational friction, but true step-level abandonment and demographic drop-off cannot be isolated. | Event-level sequence, explicit abandonment/failure events, stable unit, and linkage. |
| 5 | 2 | `partial_now` | Does the platform reach intended age groups? | Some displayed age composition is reported, including under-45 and 45–54 counts, but the complete reconciled age distribution and intended-audience benchmark are unavailable. | Complete age distribution, intended age eligibility, and matched benchmark. |
| 6 | 2 | `partial_now` | Are women reached and engaged differently? | Displayed gender rows are female-heavy (70.1% of displayed gender rows), but there is no valid engagement or benchmark comparison by gender. | Validated gender dictionary, same-funnel denominators, benchmark or prespecified internal comparison. |
| 7 | 2 | `partial_now` | Are Black users reached and supported effectively? | Black respondents are 2,433 (4.5%) of displayed race rows; trusted-messenger, privacy, and UX hypotheses are documented, but reach, completion, resource-action, and outcome equity are not measurable by Black identity yet. | Early optional self-report, approved linkage, benchmark, Black community co-design, and evaluated intervention. |
| 8 | 2 | `partial_now` | Are Hispanic/Latino users reached effectively? | Hispanic/Latino respondents are 2,675 (4.9%) of displayed race rows; language, device, acquisition, and resource support hypotheses are documented, but effective reach and completion are not established. | Race/ethnicity crosswalk, benchmark, Spanish/English end-to-end funnel, and community validation. |
| 9 | 2 | `partial_now` | Is Spanish-language access functional and used? | Spanish is 5.5% of Top Content pageviews and is present in trial/provider pathways; the snapshot provides descriptive language signals but not functional equivalence. | Language-persistent event funnel, error telemetry, native-speaker review, and language-concordant resource testing. |
| 10 | 1 | `partial_now` | Where do users first encounter BrainGuide? | Top content, geography, and acquisition context identify major entry/reach surfaces, but unattributed `(none)` traffic prevents reliable channel attribution for most questionnaire responses. | Validated acquisition taxonomy, URL hygiene, and complete landing/session event data. |
| 11 | 2 | `blocked_external_input` | Which channels bring meaningful users? | The requirements identify the question, but current disparity artifacts do not establish channel-to-qualified-completion or downstream-action rates by demographic group. | Campaign/source map, qualified action taxonomy, event-level funnel, and approved linkage. |
| 12 | 1 | `partial_now` | Which search needs bring people to the site? | Search Console is identified as a source layer, but the disparity deliverable does not include a query-level analysis or demographic overlay. | Search Console query/page export, content taxonomy, and optional approved aggregate pathway join. |
| 13 | 2 | `partial_now` | What content does each audience need? | Content categories, locales, demographic-affinity context, and research-informed content gaps support an audit plan, but not a causal need or preference claim. | Maintained content taxonomy, validated group linkage, task research, and outcome/action mapping. |
| 14 | 2 | `blocked_external_input` | Are users finding the right pathway? | The product's persona/pathway model is documented, but pathway appropriateness and demographic routing cannot be evaluated from aggregate captures. | Intent and pathway events, task-comprehension research, and linked funnel cohorts. |
| 15 | 2 | `partial_now` | Do users understand and act on tailored results? | Result-page actions, provider/trial clicks, and share behavior are measurable as intent/engagement signals, but comprehension and downstream completion are not measured. | Comprehension task/survey, action definitions, downstream outcomes, and linkage. |
| 16 | 2 | `blocked_external_input` | Which patterns predict questionnaire completion? | The current artifacts define this as an association/prediction analysis, not a causal claim, but the required session-level event sequence is unavailable. | Session/event-level data, validated completion event, prespecified features, temporal split, and calibration/equity evaluation. |
| 17 | 2/3 | `blocked_external_input` | Which patterns predict care-seeking? | Provider clicks and trial clicks are observable handoff intent, but care-seeking prediction or downstream outcome is not supported. | Approved downstream outcome, validated action taxonomy, linked cohort, and predictive validation. |
| 18 | 2 | `partial_now` | Are users progressing toward clinical research? | Clinical-trial visits and clicks measure research-navigation activity, but matching, account creation, referral, and enrollment progression are not linked in this snapshot. | Event-level research funnel, approved downstream linkage, target population/eligibility definitions, and suppression. |
| 19 | 2 | `blocked_external_input` | Where does the research pathway leak? | The protocol defines the required research funnel, but current evidence has only visit/click endpoints. | Complete event-level research funnel and linked outcome states. |
| 20 | 2 | `partial_now` | Do local-resource features lead to action? | Provider-finder visits and clicks are observed handoff signals; the snapshot cannot establish completed local-resource use or equitable action. | Validated resource-action event, downstream outcome or approved proxy, and linked group cohorts. |
| 21 | 1 | `partial_now` | Does the experience work across devices/browsers? | Device-specific page exit rates show mobile/tablet friction signals, but browser compatibility, technical errors, accessibility success, and demographic intersections are not available. | Browser/error/performance telemetry, accessibility task testing, and device/language/group funnel. |
| 22 | 2 | `blocked_external_input` | Are users returning for continued guidance? | The current snapshot does not provide a validated person-level retention cohort or demographic return linkage. | Validated retention cohort definition, event/session/user grain decision, and privacy-approved linkage. |
| 23 | 2 | `blocked_external_input` | Did the March 2026 relaunch improve the experience? | A relaunch comparison is explicitly blocked until the exact date and page/event equivalence crosswalk are confirmed. | Exact date, crosswalk, complete periods, comparable control/time series, and subgroup analysis. |
| 24 | 3 | `blocked_external_input` | Does BrainGuide increase awareness/confidence/action? | The protocol separates follow-up survey outcomes from GA4 behavior and defines response-bias reporting, but no valid impact estimate exists in the snapshot. | Approved survey instrument/cohort, response-rate and nonresponse analysis, and credible comparison or pre/post design. |
| 25 | 2/3 | `supported_now` | What actions should be prioritized next? | The evidence supports prioritizing SBC reliability, Spanish/language parity, mobile/accessibility, privacy-forward copy, early-funnel instrumentation, community co-design, and only then measured outreach. | Owner capacity/effort estimates, intervention baselines, and controlled evaluation results. |

## Implementation gates

| Gate | Requirement | Status | Evidence / implementation note |
|---|---|---|---|
| 1.1 | Reach: total users, new vs returning, sessions, top acquisition channels | `partial_in_snapshot; product_metric_contract_provisional` | braintree-evidence/CONSOLIDATED.json reports.top_content; braintree-evidence/CONSOLIDATED.json reports.geographic_traffic; plans/ga4-measurement-contract.md daily_reach |
| 1.2 | Trends: week-over-week change and day-of-week patterns | `implemented_elsewhere_but_not_validated_in_this_snapshot` | BRAINTREE_CHECKLIST.md Gate 1.2; braintree-reqs.md |
| 1.3 | Top pages: traffic and engagement | `partial_in_snapshot; existing_app_surface_not_validated_here` | braintree-evidence/CONSOLIDATED.json reports.top_content |
| 1.4 | Device split with metric breakdown | `partial_now; exit rates only` | braintree-evidence/reports/User Journeys.pdf p. 5; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json device_exit_rates |
| 1.5 | Anomalies: deviation days and engagement cliffs | `implemented_elsewhere_but_not_validated_in_this_snapshot` | BRAINTREE_CHECKLIST.md Gate 1.5; plans/🔵 ga4-insights-sketch.md |
| 1.6 | Day-1/7/14/28 retention | `blocked_external_input` | braintree-evidence/CONSOLIDATED.json cohort_definitions; plans/ga4-measurement-contract.md |
| 1.7 | Funnel start-to-completion with step drop-off | `blocked_external_input_for_demographic_equity; aggregate journey gaps are descriptive` | braintree-evidence/reports/journey-explorer.md; DEMOGRAPHIC_EQUITY_COVERAGE.json questions[4] |
| 1.8 | Forecasting with AI narrative | `implemented_elsewhere_but_not_validated_in_this_snapshot` | BRAINTREE_CHECKLIST.md Gate 1.8 |
| 1.9 | Pre-compute insights on data load | `not_implemented_in_this_artifact` | BRAINTREE_CHECKLIST.md Gate 1.9 |
| 1.10 | Inject structured insight block into every Gemini chat prompt | `not_implemented_in_this_artifact` | BRAINTREE_CHECKLIST.md Gate 1.10; plans/🔵 ga4-insights-sketch.md |
| 0.1 | Semantic metric registry | `method_defined_but_not_implemented_in_product` | plans/ga4-measurement-contract.md; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md §3 Phase 1 |
| 0.2 | Event taxonomy/bot/URL audit | `partially_described; automated_gate_not_in_this_artifact` | braintree-evidence/CONSOLIDATED.md §5.7/§5.11; braintree-reqs.md |
| 0.3 | Pre/post-March-2026 relaunch crosswalk | `blocked_external_input` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md Phase 1 |
| 0.4 | Automated data-quality gate | `not_implemented_in_this_artifact` | plans/🔵 ga4-insights-sketch.md |
| 0.5 | Feasibility matrix | `supported_by_this_artifact` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_COVERAGE.json |
| 0.6 | Prompt-injection guard for source labels | `not_implemented_in_this_artifact` | plans/🔵 ga4-insights-sketch.md |
| 2.1 | Evidence connector | `design_only; current PDF snapshot is manually curated` | plans/🔵 evidence-connector-design.md |
| 2.2 | Linkage coverage report | `blocked_external_input` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md Phase 1/2 |
| 2.3 | Equity reach | `partial_now` | DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[1]; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json $.displayed_race_rows |
| 2.3-RACE | Race/ethnicity coding crosswalk and mutually-exclusive-category decision | `blocked_external_input` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md §3 Phase 1; DEMOGRAPHIC_EQUITY_COVERAGE.json questions[2], questions[7], questions[8] |
| 2.4 | Funnel equity | `blocked_external_input` | DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[2]; DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[3] |
| 2.5 | Pathway equity | `blocked_external_input` | DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[13]; DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[14] |
| 2.6 | Language access | `partial_now` | questions[9]; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json language_and_resource_rates |
| 2.7 | Small-cell suppression | `implemented_in_snapshot_calculator` | scripts/analyze_demographic_equity.py; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json |
| 2.8 | Complementary suppression/difference attacks | `protocol_defined; product_enforcement_not_implemented` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md §5 |
| 3.1 | Survey cohort reporting | `blocked_external_input` | DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[23] |
| 3.2 | Dose-response | `blocked_external_input` | DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[23] |
| 3.3 | Content-to-outcome mapping | `blocked_external_input` | questions[13]; questions[15] |
| 3.4 | Campaign evaluation | `blocked_external_input` | questions[11]; questions[25] |
| 3.5 | Return-journey analysis | `blocked_external_input` | DEMOGRAPHIC_EQUITY_COVERAGE.json $.questions[21] |
| T.1 | Insight evidence/limitations | `implemented_in_report_protocol_snapshot` | braintree-evidence/analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json |
| T.2 | Inference labels | `implemented_in_protocol_and_report` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md §1 |
| T.3 | Insights inbox/dashboard | `not_implemented_in_this_artifact` | BRAINTREE_CHECKLIST.md |
| T.4 | Automated data-quality gate | `not_implemented_in_this_artifact` | BRAINTREE_CHECKLIST.md |
| T.5 | No raw PII/small cells to LLM | `implemented_for_snapshot_artifacts; product-wide enforcement remains separate` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md §5 |
| T.6 | Audit trail | `partial_in_snapshot_provenance; product audit trail absent` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_INPUTS.json; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md §5 |
| T.7 | Failure behavior | `implemented_in_blocked_claims_and_protocol` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json; braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md §6 |
| T.8 | Refresh/stale labeling/caching | `snapshot freshness labeled; product policy absent` | braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json; braintree-evidence/CONSOLIDATED.json data_architecture.refresh_expectations |

## Decision boundary

The current artifacts support a defensible descriptive equity-risk assessment and a complete execution specification. They do not manufacture population representation ratios, demographic funnel rates, causal mechanisms, intervention effects, or awareness impact where the required denominator, linkage, benchmark, or evaluation design is absent.
