# Take a look at the research we've conducted. Build it out more in the context of @BrainTree and what you can find in @Google Analytics mybrainguide.org — GA4

Final result
The analysis is now coverage-complete as an auditable descriptive equity assessment and execution plan.
I validated it, found gaps, fixed them, and repeated the validation loop until no fixable critical issues remained.
What was added or improved

1. Complete question-by-question coverage matrix
Added:

- braintree-evidence/DEMOGRAPHIC_EQUITY_COVERAGE.md
- braintree-evidence/DEMOGRAPHIC_EQUITY_COVERAGE.json
The matrix covers all 25 client questions and records for each:
- current answer;
- evidence sources;
- limitations;
- status;
- exact requirements to unlock full support.
Statuses are now explicit:
- supported_now : bounded descriptive answer is supported;
- partial_now : useful evidence exists, but not enough for the full question;
- blocked_external_input : method is defined, but required external data, permissions, decisions, or intervention results are missing.
Current distribution:
- 2 supported now
- 14 partially answered
- 9 blocked pending external inputs
This is an honest reflection of the evidence rather than treating a detailed plan as if it were completed analysis.

2. Complete implementation-gate coverage
The matrix now covers:

- Gate 0: Data readiness;
- Gate 1: GA4 descriptive insights;
- Gate 2: Evidence/equity overlay;
- Gate 3: Outcomes and evaluation;
- Trust Layer requirements;
- the additional race/ethnicity coding-crosswalk decision.
The earlier omission of all Gate 1 rows was fixed.

3. Authoritative requirement validation
The validator now reads the actual question wording from  BRAINTREE_CHECKLIST.md  rather than validating against a duplicated hard-coded list.
It handles legitimate wording variants such as:

- “the intended age groups” vs. “intended age groups”;
- compound gate labels such as  2/3 ;
- “for themselves” wording differences.
This means future requirement drift is much less likely to go unnoticed.

4. JSON/Markdown synchronization enforcement
The Markdown coverage matrix is generated from the canonical JSON matrix.
Validation now fails if:

- the Markdown artifact is stale;
- a question is missing;
- a gate is missing;
- a gate has malformed fields;
- a gate has an unrecognized status;
- a question lacks evidence, limitations, or unlock criteria.

5. Stronger provenance
The coverage artifact now uses more auditable references, including:

- explicit  CONSOLIDATED.json  paths;
- PDF page references;
- companion artifact paths;
- stable coverage-matrix references.

6. Preserved statistical and privacy boundaries
The work still correctly refuses to claim more than the evidence supports:

- displayed respondent composition is not population representation;
- session/user counts are not people;
- Spanish usage is not Hispanic/Latino identity;
- clicks are not care outcomes;
- product result categories are not diagnoses;
- downstream scored respondents are not equivalent to all starters;
- sparse cells and unstable rates remain suppressed;
- aggregate data cannot prove causal mechanisms.
What the current artifacts support
They support:
- the observed White-heavy respondent composition;
- descriptive Black and Hispanic/Latino respondent counts;
- descriptive Spanish-language traffic and resource-path signals;
- device-friction signals;
- SBC’s severe operational completion problem;
- missingness and selection-bias identification;
- UX/UI, copy, accessibility, instrumentation, community, and outreach priorities;
- a complete five-phase plan for reaching stronger conclusions;
- a defensible explanation of what cannot yet be concluded.
They support the recommendation to prioritize:

1. SBC reliability and alternate completion paths;
2. first-class Spanish and language persistence;
3. mobile, tablet, accessibility, and low-bandwidth usability;
4. privacy-forward and non-diagnostic entry/result copy;
5. early-funnel instrumentation;
6. optional early demographic collection with governance;
7. Black and Hispanic/Latino community co-design;
8. trusted-messenger outreach only after the product baseline is fixed.
What remains intentionally blocked
These require new external inputs or live evaluation:

- population-level Black or Hispanic/Latino representation ratios;
- completion/drop-off rates by race or ethnicity;
- demographic-by-device or demographic-by-language funnel rates;
- cause of the White-heavy respondent profile;
- Spanish functional equivalence;
- SBC demographic equity;
- validated acquisition-channel equity;
- content-to-outcome causality;
- provider appointment or clinical-trial enrollment outcomes;
- retention by demographic group;
- March 2026 relaunch impact;
- awareness, confidence, or behavior-change impact;
- UX, copy, and outreach intervention effectiveness.
The remaining blockers are now clearly named:
- owner-approved benchmark and geography/age eligibility;
- race/ethnicity coding crosswalk;
- event-level GA4/questionnaire linkage;
- optional early demographic capture;
- SBC failure-state telemetry;
- exact relaunch date and event/page crosswalk;
- downstream provider, research, and survey outcomes;
- privacy/ethics approvals;
- controlled intervention and outreach evaluation data.
Validation completed
- Coverage validator: passed.
- All 25 questions represented: passed.
- All required Gate 0/1/2/3/Trust rows represented: passed.
- Authoritative checklist parsing: passed.
- JSON/Markdown synchronization: passed.
- Snapshot calculator consistency: passed.
- Local Markdown links: passed.
- Privacy/suppression checks: passed.
- Ruff lint: passed.
- Targeted tests: 9 passed.
- Full non-browser test suite: 953 passed, 8 skipped.
- Independent final review: no remaining fixable critical issues.
Two frontend browser tests remain environment-dependent and previously failed only because the Vite server was not running at  localhost:5173 ; they are unrelated to the equity artifacts.
Bottom line
The repository now contains everything it can responsibly contain from the current evidence: a reproducible descriptive analysis, a complete question/gate coverage audit, an implementation-ready equity protocol, explicit statistical and privacy rules, and a precise list of external data and governance inputs required to make stronger claims.
It is now strong enough to guide decisions and implementation without misleading the reader about what has—and has not—actually been demonstrated.

<span style="display:none">[^45_1][^45_2][^45_3][^45_4][^45_5]</span>

<div align="center">⁂</div>

[^45_1]: meeting-notes-072326.txt

[^45_2]: transcript.txt

[^45_3]: Web Analytics  2026-07-23 15_30(GMT-4_00).md

[^45_4]: paste.txt

[^45_5]: paste.txt


---

# @Google Analytics Yes


---

# @Google Analytics yes

I pulled live GA4 data from `mybrainguide.org` and built a supplement to extend your equity coverage work — see the created markdown file. Two important caveats up front, then the highlights.

## Access limitation

I don't have direct access to `braintree-evidence/BRAINTREE_CHECKLIST.md`, `DEMOGRAPHIC_EQUITY_COVERAGE.md/json`, or `CONSOLIDATED.json` in this session — those aren't in this project's file list or reachable via GitHub/Drive from here. So rather than editing the canonical matrix directly, I pulled fresh GA4 evidence and packaged it as an **additive supplement** you can fold in, with explicit suggested status changes rather than assumed edits.

## What the live GA4 pull adds

**Language × device** (Jan–Aug 2026, ~373K sessions): Spanish-language sessions are 16,905 total (~4.5% of traffic) and **91% mobile** — a sharper mobile-dependency finding than the aggregate device-friction signal alone. More notably, that traffic volume dwarfs the ~9/year Spanish-language questionnaire completions already documented, surfacing a new gap: **high Spanish-browser traffic, very low Spanish-language questionnaire capture.**

**Acquisition channel**: ~90% of sessions come through paid media (Cross-network, Display, Paid Search). This matters directly for the "are we reaching the right populations?" question because paid targeting configuration is a client-controllable lever — distinct from, and not visible in, GA4 session data itself. I also flagged a 25% bounce rate on Direct traffic, which often represents offline/trusted-messenger referrals — worth checking before scaling that channel as an equity strategy.

## Boundaries maintained

Consistent with the space's confidentiality rules and your project's existing statistical discipline: GA4 `language` is browser setting, not ethnicity; no session-level or PII data was exported or retained beyond aggregate counts in the document; sparse-language rows are rolled up rather than reported individually; and I flagged that this pull spans pre/post the March 2026 relaunch without yet splitting it — it needs that split before any client-facing use, per this project's standing instruction to distinguish pre/post-relaunch data explicitly.

If you can share the actual `braintree-evidence` files (GitHub, Drive, or attachment), I can reconcile these suggested matrix updates against the canonical JSON directly rather than proposing them provisionally.

---

## What's in the mega-prompt

The deep-research prompt is built directly from the actual repository content — not the unreachable `braintree-evidence` files — and includes:

- The full three-layer measurement model and all 25 client questions, tagged with their real Gate assignment and answerability status from `BRAINTREE_CHECKLIST.md`.
- The Gate 0 data-quality requirements and statistical/privacy guardrails (small-cell suppression, inference labeling, no-causal-language rule) pulled from the detailed gap-analysis in `braintree-reqs.md` — this analysis is unusually rigorous about where AI should and shouldn't calculate.
- My live GA4 findings folded in as **baseline evidence** rather than restated as a separate report — the Spanish-traffic-vs-completion gap, the paid-media-dominated acquisition mix, and the Direct-traffic bounce anomaly are now framed as open questions for the deep-research pass to investigate, not conclusions.
- An explicit list of what must stay blocked, with the exact external input named for each.


## One thing to flag

I could not locate any `braintree-evidence/` directory, `DEMOGRAPHIC_EQUITY_COVERAGE.md/json`, or `CONSOLIDATED.json` anywhere in `griffinkelton/insights-explorer` — I checked the root, `docs/`, `plans/`, and ran repository-wide searches. The real artifacts are `BRAINTREE_CHECKLIST.md` and `braintree-reqs.md` at the repo root, last touched in commit `f6d5ae6`. If the coverage-matrix work you described lives in a different repository or a local-only sandbox, point me to it and I'll reconcile directly; otherwise, this mega-prompt is grounded in what's actually committed and can serve as the spec for building that coverage matrix from scratch.

---

# @Google Analytics @GitHub Check the repo again. I had them in a different branch.

Keep in mind, the most important questions that should be answered are:

Q1) To what extent is BrainGuide reaching and equitably serving diverse populations, including priority populations (e.g., women, Black, and Hispanic communities), as well as users across age, geography, and concern level?
additional information, or discussin coroces with a healtacare provider
, including completing the questionnaire, seeking
03) Where do users move forward, stall, or disengage in the pathway from engagement to care?
Q4) To what extent does BrainGuide influence users' awareness, attitudes, and understanding of cognitive health?
Q5) What proportion of users, particularly those identified as moderate or high concern, go on to seek clinical care?

I checked every branch of `insights-explorer` (`main`, `feat/react-fastapi-migration`, `griffinkelton-patch-1`, `spike/drive-picker-transport`) and searched **all 9 repositories** on your GitHub account. There is no `braintree-evidence` directory or `DEMOGRAPHIC_EQUITY_COVERAGE.md/json` anywhere I can access — not in this repo, any branch, or any other repo you own (`website`, `tv-remote-app`, `griffin-kelton-resume`, `insights-whisperer-30`, `gk-app`, `sandbox`, `gk-app-td`, `griffinkelton.github.io`). If those files exist, they're in a location outside what this GitHub connection can see (local-only, a private org repo, or a different account).

I'm proceeding with what's real: `BRAINTREE_CHECKLIST.md` and `braintree-reqs.md`, now rebuilt around **your five refined priority questions**, which supersede the original 25-item brainstorm list.

---

## Summary

The v2 mega-prompt is grounded entirely in the real `braintree-evidence/` package — the semantic data contract (`CONSOLIDATED.json`), the actual displayed-row numbers with page citations, the journey-explorer's step-level funnel leaks (including the previously uncross-referenced 98% AD8 abandonment at `W-B-AD-9`, which is arguably a bigger finding than the SBC problem), and the protocol's own statistical rules. It supersedes my earlier draft, which was built before I found the real files.

Rather than asking a deep-research agent to redo work that's already done well, this prompt targets the **two specific gaps** that would move the most `partial_now`/`blocked_external_input` questions toward `supported_now`: constructing the actual Census/ACS benchmark for Task 1 (using the geographic data you already have — CA/FL/TX/NY/PA), and finding mechanism-specific literature for four findings your existing 12 citations don't quite cover (speech-assessment equity, trusted-messenger effect sizes, informant-flow abandonment, and Spanish functional-equivalence testing methodology).

One thing worth a quick look on your end: the AD8 flow's 98% abandonment at `W-B-AD-9` (from `journey-explorer.md`'s Insights view) doesn't appear to be cross-referenced in the coverage matrix's Q4 entry yet, even though it's arguably a more severe single-step leak than the SBC 4.8% completion rate that Q4 does cite.

---

# [Batch Inline Edit Request]

The user queued multiple inline edits for the open asset. Apply the edits in the order listed. If two edits conflict, the later edit should win.

Metadata JSON:
{"edits":[{"type":"document","instruction":"Does this include these questions needing answers as well has data from braintree-reqs.md and BRAINTREE_CHECKLIST.md:  Q1) To what extent is BrainGuide reaching and equitably serving diverse populations, including priority populations (e.g., women, Black, and Hispanic communities), as well as users across age, geography, and concern level? additional information, or discussin coroces with a healtacare provider , including completing the questionnaire, seeking 03) Where do users move forward, stall, or disengage in the pathway from engagement to care? Q4) To what extent does BrainGuide influence users' awareness, attitudes, and understanding of cognitive health? Q5) What proportion of users, particularly those identified as moderate or high concern, go on to seek clinical care?","filename":"","selectedTextPreview":"Deep Research Prompt v2: BrainGuide Demographic Equity — Mechanism Validation \& Benchmark Construction\nSupersedes braintree-deep-research-prompt.md, which was built before the actual braintree-evidence/ package was located. This version is grounded in the real, already-audited evidence package at griffinkelton/insights-explorer/braintree-evidence/.\n\nRole and context\nYou are extending a rigorous, already-audited descriptive equity assessment of BrainGuide, a public-facing brain-health screening/n..."}]}

Edits:
Edit 1: Document text edit
Selected text:
Deep Research Prompt v2: BrainGuide Demographic Equity — Mechanism Validation \& Benchmark Construction
Supersedes braintree-deep-research-prompt.md, which was built before the actual braintree-evidence/ package was located. This version is grounded in the real, already-audited evidence package at griffinkelton/insights-explorer/braintree-evidence/.

Role and context
You are extending a rigorous, already-audited descriptive equity assessment of BrainGuide, a public-facing brain-health screening/navigation platform associated with UsAgainstAlzheimer's, operated for AHSR (client lead: Dr. Kumbie Madondo; IT/analytics: Greg Magnuson). The engagement has already produced a complete semantic data contract, a disparity analysis with cited external mechanisms, a five-phase implementation protocol, and an auditable 25-question coverage matrix. Your job is not to redo this work — it is to fill the two highest-value gaps that block moving from partial_now/blocked_external_input to supported_now on the highest-priority questions, using only publicly available, citable sources.

Treat all client data, analytics, and files as confidential. Do not propose training models on this data or reusing it outside this engagement. Do not recommend exporting raw data externally or retaining client materials beyond project needs.

What already exists (do not re-derive)
Data architecture and semantics
GA4 (analytics_257799278), Google Ads, DynamoDB questionnaire records (raw_dpn-chat-bot-content, raw_dpn-chat-bot-content-go365), and Search Console feed dbt staging → marts → an Evidence dashboard at dashboard.dev2.mybrainguide.org. Three assessment flows exist with incompatible scales that must never be merged: AD8 (informant-reported, 0–8, lower=better, Good 0–1/Poor 2–8), MIS (self-administered recall, 0–8, higher=better, Good 5–8/Poor 0–4), and SBC (self-administered speech, 0–1 continuous, higher=lower risk, Low>0.5/Medium 0.2–0.5/High<0.2). A fourth path, flow c, returns content routing with no score (~24% of completions). Eight assessment personas plus three SBC personas route users to specific result pages based on Who (Self/Someone Else) × Diagnosed × Brain Health.

Already-observed findings (treat as ground truth, cite by report/page when referencing)
Race/ethnicity composition (displayed rows, Results Overview.pdf p.7, n=54,626): White/Caucasian 77.9% (42,556), Prefer not to answer 5.6%, Hispanic/Latino 4.9% (2,675), Black/African American 4.5% (2,433), Asian 2.6%, Mixed 2.3%, Other 1.0%, American Indian/Alaska Native 1.0%, Native Hawaiian/Pacific Islander 0.2%. White:Black ratio ≈17.5:1; White:Hispanic/Latino ratio ≈15.9:1.

Per-flow race composition varies (AD8 White 70.5%, MIS 78.6%, SBC 73.9% among displayed rows) but is directionally consistent — the White concentration is not an artifact of one assessment type.

Demographic coverage: gender ~79%, age ~77%, race ~75% of the Results Overview filtered population; demographics apply from Received Score downward only — anyone who abandons before a scored result is invisible to demographic analysis.

SBC has a severe operational completion problem: 36,803 flow entries, only 1,751 scored results (4.8% completion). The journey-explorer synthesis independently corroborates this with step-level detail: 51% abandon at W-S1, 89% abandon at W-D4-A-SBC (16.3k→1.7k), and tablet users lose 71% at W-S1 vs. 42% for desktop.

A separate, even more severe leak exists in the AD8 informant flow: 98% abandonment at screen W-B-AD-9 (19,600→369 continuing) — this is the single worst-performing step across the entire questionnaire per the journey-explorer "Insights" view, and it is not yet cross-referenced in the coverage matrix's Q4 ("who drops off, and where") entry.

Campaign quality varies enormously: (organic) converts at 59% (41,225 starts); one specific paid campaign (6592414342203) converts at 0.1% (9,325 starts, near-total failure); two Display campaigns convert at 13–14% on tens of thousands of starts each.

Language: Spanish is 5.5% of Top Content pageviews (28,531 of 516,480); Spanish Clinical Trials visit-to-click rate is 5.8% vs. English 18.0%; Spanish Find-a-Provider click cell is suppressed (n<10) against 194 visits.

Device: page-sequence exit rates are Mobile 74.7%, Tablet 80.2%, Desktop 62.8% (not bounce rate — no next pageview in session).

Geographic reach: 620,861 US users across 81 states/territories; top states by users are California, Florida, Texas, New York, Pennsylvania; 690,800 global users across 211 countries.

Known internal data contradictions (already flagged, not yet resolved): AD8 outcome rows (10,170 Poor + 2,125 Good = 12,295) don't reconcile to the 12,330 completion KPI (35 missing); MIS outcome rows (21,159 Poor + 86,039 Good = 107,198) don't reconcile to 107,976 completions (778 missing).

Already-cited external mechanism literature (12 sources, do not duplicate — extend/update instead)
Lin et al. 2020 (dementia-status awareness disparity), Lin et al. 2021 (diagnosis delay disparity), Portacolone et al. 2020 (Black community trust/research), Epps et al. 2021 (congregation-based education), Stites et al. 2024 (Black adults and biomarker stigma), Philpot et al. 2024 (Spanish-preferred digital health literacy), Light et al. 2024 (Latino dementia knowledge review), Gutiérrez et al. 2022 (Latinx online ADRD recruitment barriers), Siette et al. 2023 (dementia stigma in diverse communities), Chau et al. 2023 (CBOs as trusted messengers), Wilson et al. 2024 (digital health equity systematic review).

The five-phase protocol and statistical rules (already specified, use as-is)
Phase 1 (measurement/benchmark/crosswalk) → Phase 2 (funnel/missingness) → Phase 3 (mechanism validation/community research) → Phase 4 (controlled UX/copy/technical intervention) → Phase 5 (outreach/outcome evaluation). Statistical rules already locked: Wilson intervals for single proportions, Newcombe's Wilson interval for two-proportion differences, release floor n≥10, rate-stability floor denominator≥50, no demographic parity imposed on clinical screening results, no causal language without experimental design, race/ethnicity must never be imputed from name/geography/language/imagery.

Your two research tasks
Task 1 — Construct the Phase 1 benchmark (unlocks Q2, Q7, Q8 from partial_now toward supported_now)
The protocol specifies the benchmark decision but has not yet executed it. Using the already-known geographic footprint (top states: California, Florida, Texas, New York, Pennsylvania; 81 states/territories reached; 620,861 US users), do the following:

Pull current U.S. Census Bureau ACS 5-year estimates (most recent vintage) for these top-5 states, broken out by the same race/ethnicity categories used in the questionnaire (White alone, Black/African American alone, Hispanic/Latino of any race, Asian alone, American Indian/Alaska Native alone, Native Hawaiian/Pacific Islander alone, Two or more races).

Restrict the age band to whatever eligibility criteria BrainGuide actually targets — search for and cite BrainGuide's own stated target audience (older adults, caregivers) from mybrainguide.org or usagainstalzheimers.org public materials; if no explicit age floor is published, default to 45+ and 65+ as two sensitivity bands.

Produce a benchmark table: for each of the top-5 states and a population-weighted aggregate across all 81 reached states/territories, report the ACS race/ethnicity share for the chosen age band, with source citation (Census table ID, vintage year) for each figure.

Explicitly flag the unit mismatch risk already noted in the protocol: GA4 reach is session/user-based (device-level), while ACS is person-based. State this limitation prominently rather than silently presenting a ratio as precise.

Using this benchmark, compute a provisional, clearly-labeled-as-provisional representation ratio for Black and Hispanic/Latino groups (observed displayed-row share ÷ benchmark share), and report it as associated, not observed, per the protocol's inference-label vocabulary — because the observed share is a downstream-completer share, not an all-visitor share.

Task 2 — Update and extend the mechanism literature for the four most consequential findings (supports Phase 3, Q7/Q8/Q9/Q4)
For each of the following four specific BrainGuide findings, find current (published within the last 3 years where possible) peer-reviewed or gray-literature evidence that speaks to the specific mechanism, not just general disparity framing already covered by the 12 existing citations:

Speech-based cognitive assessment equity: Is there published evidence on differential completion, accuracy, or comfort with speech/voice-based (as opposed to text-based) cognitive or health screening tools by race, ethnicity, age, or digital literacy? This directly bears on the SBC 4.8% completion crisis and whether it disproportionately affects priority populations.

Trusted-messenger intervention effect sizes: The existing citations (Portacolone, Epps, Chau) establish trust as a barrier and CBOs as a plausible bridge, but do not report quantified before/after effect sizes for trusted-messenger-based digital health tool adoption specifically. Find studies that measure actual completion-rate or adoption-rate lift from CBO/faith-based/community-health-worker referral versus general digital advertising, ideally in dementia, cognitive health, or adjacent chronic-disease screening contexts.

Informant/caregiver-reported instrument abandonment: The AD8 flow shows a 98% abandonment at one specific screen (W-B-AD-9). Search for research on why informant-reported (as opposed to self-administered) cognitive screening tools see high abandonment — is there a documented emotional, time-burden, or trust-related reason caregivers stop partway through reporting on a loved one's symptoms?

Spanish-language health-tool functional equivalence testing methodology: Beyond the general Spanish digital-literacy barrier literature already cited (Philpot et al.), find methodological guidance or case studies on how organizations have specifically tested and validated "functional equivalence" (not just translation accuracy) of a Spanish-language digital health screening tool — this will directly inform Phase 3's planned native-speaker review and Phase 4's Spanish UX intervention design.

Output format
Produce a report with two sections mirroring the two tasks above. For Task 1, include the full benchmark table with citations and the provisional ratio with its inference label and stated limitations. For Task 2, produce a short annotated bibliography (5–10 new sources across the four sub-questions) with: full citation, 2–3 sentence summary of the specific finding, and one sentence on how it should modify or extend the existing DEMOGRAPHIC_EQUITY_PROTOCOL.md Phase 3 mechanism table. Do not restate findings already in DEMOGRAPHIC_DISPARITY_ANALYSIS.md — only add what is new or updates a stale citation. Label every claim observed, associated, hypothesis, or not assessable per the existing protocol vocabulary. Do not draw a population disparity conclusion beyond what the constructed benchmark and cited literature actually support.
User instruction: Does this include these questions needing answers as well has data from braintree-reqs.md and BRAINTREE_CHECKLIST.md:  Q1) To what extent is BrainGuide reaching and equitably serving diverse populations, including priority populations (e.g., women, Black, and Hispanic communities), as well as users across age, geography, and concern level? additional information, or discussin coroces with a healtacare provider , including completing the questionnaire, seeking 03) Where do users move forward, stall, or disengage in the pathway from engagement to care? Q4) To what extent does BrainGuide influence users' awareness, attitudes, and understanding of cognitive health? Q5) What proportion of users, particularly those identified as moderate or high concern, go on to seek clinical care?

Please identify the relevant content or code for each queued edit and make all requested changes in one update.

Edit applied. Summary of what changed in the document:

- **New §0** at the top explicitly reconciles your five SOW-level questions against the 25-question tactical framework and the coverage matrix, with a table showing exactly which existing question(s) each one maps to.
- **Confirmed**: four of your five questions are already substantively covered (Q2/Q3/Q4 pathway-and-disengagement questions map to existing coverage-matrix Q3/Q4/Q14/Q15/Q17/Q19/Q20; the awareness question maps directly to Q24).
- **Flagged the real gap**: "concern level" as a segmentation axis — specifically, whether users who score Poor (AD8/MIS) or High Risk (SBC) seek clinical care at a different rate than Good/Low-Risk users — doesn't exist anywhere in the current 25-question list or coverage matrix. This is precisely what your Q5 and part of Q1 ask for.
- **New Task 3** added to the research prompt, which doesn't require external research at all — it's a re-extraction task against data you already have (`Result Pages.pdf`, `Clinical Trials.pdf`, `Find a Provider.pdf`, cross-referenced against the persona/brain-health labels already in `Results Overview.pdf`/`AD8`/`MIS`/`SBC Analysis.pdf`). It includes an explicit fallback: if the current PDF captures don't support that join at a usable grain, the task requires saying so and specifying exactly what new Evidence dashboard view would be needed, rather than fabricating a number.

The garbled middle portion of your Q2 ("additional information, or discussin coroces with a healtacare provider... including completing the questionnaire, seeking") — I read that as "seeking additional information, or discussing concerns with a healthcare provider, including completing the questionnaire" and mapped it accordingly. Let me know if that reconstruction is wrong and I'll correct the mapping.

---

## Summary

I found the real `braintree-evidence/` tree on `main` via the GitHub API (it wasn't showing up through search/get_url_content, but a direct tree query worked) and grounded the deep-research deliverable in the actual captured PDFs/MDs rather than the earlier speculative version.

**Task 1 (benchmark):** Confirmed via `mybrainguide.org`'s own FAQ that BrainGuide states no explicit age floor ("designed for people of all ages and from all communities"), so I built both an all-ages ACS 2024 benchmark and flagged that a true 81-state weighted aggregate isn't buildable from currently captured data — only a 5-state proxy is. The provisional representation ratios (Black ~0.39×, Hispanic/Latino ~0.24× of population share) are explicitly labeled `associated`, not `observed`, with the unit-mismatch and downstream-completer caveats stated prominently rather than buried.

**Task 2 (mechanism literature):** Found a strong, previously-uncited direct hit — Koenecke et al. 2020 (PNAS) on racial disparities in automated speech recognition — which is genuinely new mechanistic evidence for the SBC completion crisis, distinct from the trust/stigma citations already in the analysis. I was honest about the gap on sub-question 2: no study exists quantifying trusted-messenger effect sizes for digital cognitive-screening tools specifically, so I labeled that `not assessable` from literature rather than forcing a citation to fit.

**Task 3 (concern-level cross-tab):** This is the one genuinely new computed finding: using `result-pages.md`'s already-captured Brain Health × Action table, Poor-labeled visitors click "Locate a Healthcare Provider" at ~10.5% vs. 3.2% for Good-labeled visitors (~3.3× rate ratio, both cells clearing the release/stability floors). But I flagged something important during independent validation: `result-pages.md` explicitly says it's only "Page 1 of 2" and is missing a device breakdown — meaning Moderate-labeled and SBC-specific rows aren't in the current capture at all. The Task 3 table should be treated as partial until page 2 is pulled.

I also proposed a concrete new coverage-matrix row (Q26) with the correct `partial_now` status and unlock criteria, since a click is documented as handoff intent, not confirmed care-seeking.
<span style="display:none">[^52_1][^52_10][^52_11][^52_12][^52_13][^52_14][^52_15][^52_16][^52_17][^52_18][^52_19][^52_2][^52_20][^52_21][^52_22][^52_23][^52_24][^52_25][^52_26][^52_27][^52_28][^52_29][^52_3][^52_30][^52_31][^52_32][^52_33][^52_34][^52_35][^52_36][^52_37][^52_38][^52_39][^52_4][^52_40][^52_41][^52_5][^52_6][^52_7][^52_8][^52_9]</span>

<div align="center">⁂</div>

[^52_1]: paste.txt

[^52_2]: https://mybrainguide.org/

[^52_3]: https://mybrainguide.org/about-alzheimers-brain-guide/

[^52_4]: https://www.kff.org/state-health-policy-data/state-indicator/distribution-by-raceethnicity/

[^52_5]: https://www.pnas.org/doi/10.1073/pnas.1915768117

[^52_6]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12790586/

[^52_7]: https://pmc.ncbi.nlm.nih.gov/articles/PMC13054566/

[^52_8]: https://journals.sagepub.com/doi/10.1177/0163278705275342

[^52_9]: https://www.frontiersin.org/journals/health-services/articles/10.3389/frhs.2025.1582127/full

[^52_10]: https://mhealth.jmir.org/2026/1/e64787

[^52_11]: paste.txt

[^52_12]: https://www.usagainstalzheimers.org/sites/default/files/2022-04/BrainHealthEquity_PracticalGuide_Final_Digital.pdf

[^52_13]: https://mybrainguide.org/frequently-asked-questions/

[^52_14]: https://www.usagainstalzheimers.org/sites/default/files/2024-04/Integrating Family Caregivers of People With Alzheimer’s Disease and Dementias into Clinical Appointments Identifying 1018.pdf

[^52_15]: https://mybrainguide.org/types-of-local-resources/

[^52_16]: https://mybrainguide.org/brain-health-for-all-communities/

[^52_17]: https://mybrainguide.org/future-proof-your-mind-brain-health-in-your-30s/

[^52_18]: https://mybrainguide.org/alzheimers-screening-detection-and-diagnosis/

[^52_19]: https://mybrainguide.org/financial-behavior-early-alzheimers-signs/

[^52_20]: https://mybrainguide.org/guide-loved-ones-2/

[^52_21]: https://assets.mybrainguide.org/en/BrainGuide-Provider-Toolkit-EN.pdf

[^52_22]: https://www.census.gov/data/developers/data-sets/acs-5year.html

[^52_23]: https://nationalskillscoalition.org/resource/publications/applying-a-racial-equity-lens-to-digital-literacy/

[^52_24]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10905785/

[^52_25]: http://catalog.data.gov/dataset/american-community-survey-5-year-estimates-detailed-tables-5-year

[^52_26]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10017937/

[^52_27]: https://dof.ca.gov/reports/demographic-reports/american-community-survey/

[^52_28]: https://mybrainguide.org/healthcare-provider-alzheimers-awareness-toolkit/

[^52_29]: https://journals.sagepub.com/doi/10.1177/20552076231171967

[^52_30]: https://www.youtube.com/watch?v=3Ji7Iyb4Xy0

[^52_31]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12804577/

[^52_32]: https://www.sciencedirect.com/science/article/pii/S1578219018300052

[^52_33]: https://www.frontiersin.org/journals/neurology/articles/10.3389/fneur.2026.1870463/full

[^52_34]: https://pure.johnshopkins.edu/en/publications/translation-and-validation-of-a-spanish-language-genetic-health-l-4

[^52_35]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0291291

[^52_36]: https://geriatricsontario.ca/wp-content/uploads/2023/06/2023-Mar-23-Caregiver-screening-and-Ax-tools-rapid-review_FinalOCAW.pdf

[^52_37]: https://knightadrc.wustl.edu/professionals-clinicians/ad8-instrument/

[^52_38]: https://angulobrunet.es/publication/hernandez2024spanish/

[^52_39]: https://www.cgakit.com/p-3-ad8

[^52_40]: https://www.apunts.org/en-download-pdf-S0001731024006471

[^52_41]: https://www.alzheimersla.org/for-professionals/screening-and-assessment-tools/
