<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Generate top 25 things the client wants to understand from data in GA4 and how that would overlay with demographic data too? Are there more things to analyze? What questions do we need to answer and what connections need to be made in all the data?

The client’s central question is not simply “How many people used BrainGuide?” It is: **who is reached, what they need, how they move through the platform, whether experiences differ equitably across priority populations, and whether use progresses toward appropriate care or research action.** GA4 can describe site behavior, while questionnaire and survey data can add self-reported demographic, need, and outcome context—if linked through a de-identified session or transaction-level key.[^1_1][^1_2]

## Top 25 analyses

| \# | Client question | GA4 / platform measures | Demographic overlay |
| --: | :-- | :-- | :-- |
| 1 | Who is BrainGuide reaching overall? | Users, new users, sessions, geography, channel, device | Age, gender, race/ethnicity, language, ZIP/state, role |
| 2 | Are we reaching priority populations equitably? | Reach and questionnaire starts/completions | Compare women, Black, Hispanic/Latino users with all users and with defined benchmarks |
| 3 | Who completes the questionnaire? | Start-to-finish conversion, time to completion, exits | Completion rates by demographic group and language |
| 4 | Who drops off, and where? | Questionnaire step/event sequence, error/restart events, elapsed time | Drop-off by age, race/ethnicity, gender, language, device, and user role |
| 5 | Does the platform reach the intended age groups? | User volume and questionnaire participation | Age bands; distinguish person with concerns, caregiver, family member, and prevention-oriented users |
| 6 | Are women reached and engaged differently? | Content viewed, completion, resource clicks, referrals | Gender by age and pathway stage |
| 7 | Are Black users reached and supported effectively? | Acquisition source, questionnaire conversion, tailored-resource use | Black/African American respondents compared with overall respondents |
| 8 | Are Hispanic/Latino users reached and supported effectively? | Spanish entry pages, Spanish questionnaire starts/completions, language switching | Hispanic/Latino identity, Spanish preference, country/state where available |
| 9 | Is Spanish-language access functional and used? | Spanish page views, starts, finishes, resource and CTA clicks | Spanish-language users and Hispanic/Latino respondents; treat results as descriptive because current Spanish volume is very small |
| 10 | Where do users first encounter BrainGuide? | Landing page, source/medium, campaign, search query, referral | Entry routes by priority population |
| 11 | Which acquisition channels bring meaningful users rather than volume alone? | Channel-level engagement, completion, resource actions, downstream contact | Channel performance by demographic segment |
| 12 | Which search needs bring people to the site? | Google Search Console queries, landing pages, organic-search behavior | Compare search intent with questionnaire-reported concern or care stage |
| 13 | What content does each audience need? | Page paths, topic clusters, scroll depth, downloads, video progress, resource clicks | Topic interest by age, role, language, race/ethnicity, gender, condition/care stage |
| 14 | Are users finding the right pathway for themselves? | Journey-path events, tailored-page views, navigation sequences | “Myself” versus “someone else” / caregiver, concern type, diagnosis status |
| 15 | Do users understand and act on tailored results? | Tailored-page events, local-resource visibility, resource click-through | Results category and demographic segment |
| 16 | Which content or interaction patterns predict questionnaire completion? | Landing page, event sequence, time/scroll, device, source | Test whether predictors differ by priority population |
| 17 | Which content or interaction patterns predict care-seeking? | Provider-finder use, appointment/contact form, outbound clinical or care links | Demographic and questionnaire-need profiles of users who take action |
| 18 | Are users progressing toward clinical research? | Trial connector visits, questionnaire completion, matching, trial views, account creation, referral/Research Action Center submission | Eligibility-related questionnaire fields, age, condition stage, race/ethnicity, gender, geography |
| 19 | Where does the research pathway leak? | Start → finish → match → trial view → account → referral | Compare funnel loss by demographics and clinical profile |
| 20 | Do local-resource features lead to action? | Geographic-resource visibility, click-throughs, provider finder, outbound clicks | State/region, rurality if derivable, race/ethnicity, language, user role |
| 21 | Does the experience work across devices and browsers? | Mobile/desktop/tablet, browser, screen size, load/performance proxies, completion and error rates | Device access patterns by age, language, and priority populations |
| 22 | Are users returning for continued guidance? | Returning users, cohort retention, repeat questionnaire/resource use | Retention by user role, concern/diagnosis stage, demographic group |
| 23 | Did the March 2026 relaunch improve the experience? | Pre/post trends in reach, completion, engagement, downstream actions, page-path behavior | Pre/post differences by priority population, device, language, and pathway |
| 24 | Does BrainGuide increase awareness, confidence, and intended action? | GA4 identifies the behavioral exposure cohort | Survey pre/post or retrospective self-report by demographics and use intensity |
| 25 | What actions should be prioritized next? | Size of opportunity, funnel loss, content demand, technical friction, action rates | Prioritize inequities with sufficient sample size and clear practical remedies |

The available reports already show the raw components for much of this framework: acquisition and channel data, landing-page behavior, engagement, events, retention, country/device data, questionnaire starts and finishes, tailored-resource events, clinical-trial activity, and contact-center outcomes.[^1_3][^1_4][^1_5][^1_6][^1_2]

## Data overlay model

Use a **three-layer measurement model**, not a direct GA4 demographics report.


| Layer | What it can answer | Primary join key |
| :-- | :-- | :-- |
| **GA4 / GTM behavior** | Acquisition, landing page, navigation, engagement, device, events, session funnel | GA4 session ID or anonymous user/session identifier |
| **Questionnaire / Evidence warehouse** | Self-reported age or birth year, health context, user pathway, responses, location, possible demographics | De-identified session ID and/or questionnaire transaction ID |
| **SurveyMonkey follow-up survey** | Awareness change, confidence, satisfaction, care-seeking since use, barriers, self-reported demographics | Privacy-approved survey/respondent linkage or cohort-level comparison |

Questionnaire demographics are self-reported and originate in the questionnaire rather than Google Analytics; GA4’s demographic/geographic fields should therefore be treated as behavioral context, not a substitute for race, ethnicity, gender, or other equity variables.  The 2026 Evidence extract includes both transaction and session IDs for online questionnaire answers, making a de-identified behavioral overlay technically plausible if the same session identifier can be reconciled with GA4/GTM events.[^1_2][^1_1]

### Recommended cohort definition

Define each equity analysis with the same denominator and time window:

- **All site visitors:** GA4 users or sessions.
- **Questionnaire starters:** Users with `web_questionnaire_start`.
- **Questionnaire completers:** Users with `web_questionnaire_finish`.
- **Action-takers:** Users with a meaningful post-result action—e.g., provider-finder use, local-resource click, clinical-trial view, contact form, referral submission, or relevant outbound click.
- **Survey respondents:** A separate, self-selected follow-up cohort; report response rate and nonresponse limitations.

This matters because the event inventory includes questionnaire starts and finishes, tailored-page interactions, geographic-resource visibility, provider/clinical-trial-oriented events, downloads, and outbound clicks, but event counts alone are not outcomes unless their definitions and denominators are explicit.[^1_6][^1_3]

## Critical connections

The analysis should make these connections explicitly:

1. **Acquisition → intent:** What channel, campaign, referral partner, or search query brought a user in, and what problem were they trying to solve?
2. **Intent → pathway:** Did the landing page and early navigation route the person into an appropriate questionnaire or content journey?
3. **Pathway → completion:** Which interactions precede finishing the questionnaire, and which steps generate disproportionate abandonment?
4. **Questionnaire profile → recommendations:** What self-reported concern, diagnosis stage, caregiving role, risk factor, or location led to which tailored page or resource set?
5. **Recommendations → action:** Did users click local resources, seek a provider, view trial information, contact BrainGuide, or submit a research-related request?
6. **Action → downstream outcome:** Where possible, reconcile website events with contact-center activity, trial matches, referrals, and enrollments in aggregate or via approved de-identified IDs.
7. **Every connection → equity:** Repeat the pathway for women, Black users, Hispanic/Latino users, Spanish-language users, older users, caregivers, people with concerns about themselves, and other agreed priority groups.

The Evidence reports already contain a downstream clinical-research funnel—questionnaire starts and completions, trial matches, trial views, account creation, and Research Action Center submissions—so the platform can be evaluated beyond web traffic if the definitions and data linkage are validated.[^1_2]

## Additional analyses

Beyond the top 25, I would add the following workstreams.

### Measurement validity

- **Audit the event taxonomy.** Confirm what counts as a “key event,” whether `Questionnaire` is a repeated instrumentation event, and whether key-event rates should be interpreted as conversions. The export shows very high key-event rates across acquisition channels, suggesting that the current designation may capture routine or repeated activity rather than a meaningful outcome.[^1_4][^1_6]
- **Check for bot, crawler, and malformed-path traffic.** Landing-page reports include numerous asset URLs, malformed URLs, and anomalous entries, which can distort engagement, entry-page, and channel findings unless filtered or separately classified.[^1_7]
- **Build a pre/post relaunch crosswalk.** The site was relaunched around March 2026 in the same GA4 property, with changes to interface actions and potentially page names; use page path rather than page title where possible, establish the exact launch date, and analyze equivalent pathways separately before and after launch.[^1_8]
- **Distinguish anonymous from identified/contactable users.** Most platform use is anonymous; email or contact-center data should not be joined to GA4 absent explicit permission, a documented purpose, and appropriate privacy controls.[^1_8]


### Equity and access

- **Representativeness analysis:** Compare the demographic profile of questionnaire completers with starters, all users where valid, outreach recipients, and the priority-population benchmark agreed by AHSR.
- **Intersectional analysis:** Examine combinations such as older Hispanic/Latino users, Black caregivers, women ages 45–64, and Spanish-language users—only where cell sizes permit.
- **Geographic access analysis:** Evaluate state/metro/rural proxy, provider-finder use, local-resource availability, and clinical-trial availability against subsequent clicks or contact.
- **Digital-access analysis:** Test mobile versus desktop completion and abandonment by age/language group; this may reveal access barriers not visible in aggregate metrics.
- **Small-cell policy:** Suppress or aggregate small groups, avoid causal claims, and flag unstable percentages. Spanish-language questionnaire/contact volume is currently only about nine year-to-date, so it should be analyzed qualitatively or descriptively rather than as a reliable comparative rate.[^1_1]


### Outcomes and learning

- **Dose-response analysis:** Does deeper use—completed questionnaire, tailored-page viewing, multiple resource clicks—correlate with higher reported awareness, confidence, or care-seeking?
- **Content-to-outcome analysis:** Which content themes, such as early signs, caregiver guidance, prevention, diagnosis, local resources, or clinical trials, are associated with the next intended action?
- **Return-journey analysis:** Are users who return more likely to move from awareness content to provider, resource, or trial actions? GA4 retention is available but should be interpreted carefully because browser/device-based return measures do not establish a person-level longitudinal record.[^1_5]
- **Campaign evaluation:** Use campaign-tagged links and matched comparison periods to assess whether outreach drives qualified questionnaire completion and downstream action—not merely visits.
- **Qualitative synthesis:** Code survey open-text responses and interviews alongside behavioral segments to explain *why* friction or inequity appears in the data.


## Questions to settle now

Before running the full analysis, the team should answer these measurement-design questions:

1. **What are the 3–5 formal primary outcomes?** Recommended candidates: questionnaire completion, tailored-resource action, care-navigation action, clinical-research action, and self-reported awareness/behavior change.
2. **What is the exact definition of “reaching” a priority population?** Site visit, questionnaire start, questionnaire completion, meaningful action, or successful downstream connection are different standards.
3. **Which demographic fields are collected, optional, and consistently coded?** Confirm race, ethnicity, gender, language, age, ZIP/state, caregiving role, and diagnosis/concern stage.
4. **Can a de-identified session ID connect questionnaire records to GA4 events for the full session, including activity before the questionnaire begins?** This is the key technical feasibility question; current documentation indicates that persistence across the session was still uncertain.[^1_1][^1_8]
5. **Which event definitions are trustworthy enough for outcome reporting?** Validate event firing, duplicates, zero-count events, key-event configuration, and whether clicks represent completed external actions or only intent.
6. **What is the official relaunch date and which pathways changed?** No unqualified year-over-year or pre/post comparison should be made until this is fixed.[^1_8][^1_1]
7. **What comparison benchmark will define equitable reach?** Census/service-area population, target audience composition, campaign audience, or a prior-period baseline each answers a different question.
8. **What downstream records can be linked ethically and reliably?** Contact center, referral, and research outcomes should be connected only through approved, minimum-necessary de-identified methods.
9. **How will survey selection bias be handled?** The survey is being sent to a June contact cohort of roughly 353 people, not a probability sample of all site users; report response rate, respondent profile, and limits to generalization.[^1_1]
10. **What reporting thresholds and privacy rules apply?** Establish small-cell suppression, aggregation, and role-based access before reviewing demographic cuts.

## Recommended deliverable structure

For the September report, I would structure findings as:

1. **Reach and equity profile** — Who used the platform, who completed the questionnaire, and which priority groups are underrepresented or overrepresented.
2. **Journey and friction** — Acquisition source, landing page, questionnaire funnel, tailored results, and drop-off points.
3. **Need-to-resource fit** — Self-reported situation versus content, local resources, provider navigation, and research pathways used.
4. **Outcomes and care progression** — Survey-reported awareness/behavior change plus observed care/research actions.
5. **Relaunch and measurement implications** — Clearly separated pre- versus post-March 2026 findings, tracking limitations, and prioritized improvements.
6. **Action plan** — Equity-focused content, UX, outreach, and instrumentation recommendations, ranked by evidence strength and feasibility.

The immediate priority is a **data dictionary and linkage map**: each event, questionnaire field, downstream outcome, owner, grain of data, timeframe, join key, privacy status, and whether it is valid for pre/post-relaunch comparison. That artifact will prevent the final report from mixing incompatible measures and will make the GA4-demographic overlay defensible.[^1_6][^1_2][^1_8]
<span style="display:none">[^1_10][^1_11][^1_12][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: Web Analytics  2026-07-23 15_30(GMT-4_00).md

[^1_2]: BrainGuide Q2 2026_Updated.xlsx

[^1_3]: Engagement overview.xlsx

[^1_4]: User acquisition_ First user primary channel group (Default Channel Group).xlsx

[^1_5]: Retention overview.xlsx

[^1_6]: Events_ Event name.xlsx

[^1_7]: Landing page_ Landing page.xlsx

[^1_8]: transcript.txt

[^1_9]: meeting-notes-072326.txt

[^1_10]: Demographic details_ Country.xlsx

[^1_11]: Audiences_ Audience name.xlsx

[^1_12]: Report - BrainGuide Q3 2025.xlsx


---

# where are the gaps in this feature for AI do to it's best at this?

# GA4 Insights Engine — Design Sketch

> **Status:** 🔵 Sketch — not in any active sprint. Post-v0.3.0 candidate.
> **Cross-refs:** [`🔵 evidence-connector-design.md`](%F0%9F%94%B5%20evidence-connector-design.md) — demographic data bridge (opt-in survey only).

---

## What this is

When a user authenticates GA4 in the app, the AI (Gemini via `utils/gemini_client.py`)
should already understand the data well enough to surface useful patterns immediately —
not wait for the user to ask the right question. This sketch defines what that looks like,
when to build it, and how it connects to questionnaire/survey data once the evidence
connector is implemented.

---

## Three-layer measurement model

The app's AI insight layer should reason across three data tiers, not treat GA4
as the sole ground truth:


| Layer | Source | What it answers | Join key | When available |
| :-- | :-- | :-- | :-- | :-- |
| **GA4 / GTM behavior** | `pull_ga4_report()` → `DataContext` | Acquisition, navigation, engagement, device, events, session funnel | GA4 session ID or anonymous user/session identifier | Immediately on OAuth connect |
| **Questionnaire / Evidence warehouse** | Drive import (v0.3.0) → `DataContext`, evidence connector (future) | Self-reported demographics, health context, user pathway, responses | De-identified session ID and/or questionnaire transaction ID | Post-v0.3.0 — when Drive import is live and questionnaire data is loaded |
| **SurveyMonkey follow-up** | CSV import or evidence connector | Awareness change, confidence, satisfaction, care-seeking, barriers | Privacy-approved survey/respondent linkage or cohort-level comparison | Opt-in only; separate cohort |

**Key principle:** GA4 demographic/geographic fields are behavioral context, not a
substitute for race, ethnicity, gender, or other equity variables. Questionnaire
demographics are self-reported and authoritative for equity analysis.

---

## What the AI would learn (on-connect, automatic)

When the user authenticates GA4 and data loads successfully, the app runs a
lightweight analysis pass that pre-computes these findings and stores them in
`st.session_state._ga4_insights`:

### Always computed (no demographics needed)

| Category | Specific findings |
| :-- | :-- |
| **Reach** | Total users, new vs returning, sessions, geography (country/region from GA4), top acquisition channels |
| **Trends** | Week-over-week session change, day-of-week patterns, top/bottom performing days |
| **Top pages** | Highest-traffic page paths by sessions, pages with best/worst engagement rate |
| **Device** | Mobile vs desktop vs tablet split, device-specific bounce/engagement patterns |
| **Funnel** | Key event start-to-completion rates, step-by-step drop-off, time to completion |
| **Anomalies** | Days with >2σ deviation from rolling mean on sessions, engagement rate cliffs, bounce-rate spikes |
| **Retention** | Day-1/7/14/28 cohort retention, return rate by acquisition channel |

### Computed when demographics are available (via evidence connector, opt-in only)

| Category | Specific findings |
| :-- | :-- |
| **Equity reach** | Demographic profile of completers vs all users vs benchmark; over/underrepresentation by priority population |
| **Funnel equity** | Completion and drop-off rates stratified by age, gender, race/ethnicity, language, device, role |
| **Pathway equity** | Which acquisition channels and content paths serve which populations effectively |
| **Intersectional cuts** | Combinations (e.g. women 45–64, Black caregivers) — only where cell sizes ≥ defined threshold |
| **Language access** | Spanish-language page views, starts, completions, resource clicks vs overall |

**Small-cell rule:** suppress or aggregate any group with < 10 individuals. Flag
unstable percentages. Spanish-language volume is currently ~9 year-to-date and
must be treated qualitatively.

---

## Critical connections — the 7 C's

The AI should reason along these causal chains, not report metrics in isolation:

1. **Acquisition → Intent:** What channel, campaign, or search query brought the
user in, and what problem were they trying to solve?
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
population and flag statistically meaningful differences.

The AI should surface these connections explicitly in its responses — e.g.
*"Users arriving via organic search are 3× more likely to complete the
questionnaire than social referrals, but this gap disappears for Spanish-language
users — suggesting the social landing experience may have a language barrier."*

---

## Cohort definitions (shared denominator for all analysis)

| Cohort | Definition | Source |
| :-- | :-- | :-- |
| **All site visitors** | GA4 users or sessions | `pull_ga4_report()` |
| **Questionnaire starters** | Users with `web_questionnaire_start` event | GA4 events |
| **Questionnaire completers** | Users with `web_questionnaire_finish` event | GA4 events |
| **Action-takers** | Users with a meaningful post-result action (provider finder, local-resource click, trial view, contact form, referral) | GA4 events |
| **Survey respondents** | Separate, self-selected follow-up cohort | Evidence connector (future) |


---

## Measurement validity requirements

The AI must qualify its analysis against these known data quality concerns:


| Concern | Mitigation |
| :-- | :-- |
| **Event taxonomy** | Confirm what counts as a "key event" — current key-event rates appear very high across channels, suggesting the designation may capture routine activity rather than meaningful outcomes |
| **Bot/crawler traffic** | Landing-page reports include asset URLs and anomalous entries that distort engagement findings unless filtered |
| **Pre/post relaunch** | The site was relaunched ~March 2026 in the same GA4 property. Use page path (not title), establish the exact launch date, and analyze equivalent pathways separately before/after |
| **Anonymous vs identified** | Most use is anonymous. Email or contact-center data must not be joined to GA4 absent explicit permission and privacy controls |
| **Retention limitations** | Browser/device-based return measures do not establish person-level longitudinal records |


---

## Privacy \& ethics constraints

- **Demographic data is opt-in only.** No GA4 demographic fields are treated
as authoritative for race, ethnicity, or gender analysis.
- **The evidence connector** (`plans/🔵 evidence-connector-design.md`) is the
**only** path for questionnaire/survey demographic data to enter the system.
- **No identified individual data** is sent to Gemini. Prompts contain
aggregate statistics and safe patterns, not raw rows, PII, or identifiers.
- **Small-cell suppression** (< 10 individuals) is enforced in code before
any demographic cut reaches the AI or the user.
- **Survey selection bias** is disclosed: the survey cohort (~353 people) is
not a probability sample of all site users. Response rates, respondent
profiles, and generalization limits are reported alongside any findings.

---

## AI prompt contract

When the insights engine is built, Gemini receives a structured context block
appended to every chat prompt:

```
[ga4_insights]
- period: 2026-01-01 to 2026-07-31
- total_sessions: X
- total_users: X (X% new, X% returning)
- top_channel: organic_search (X%), direct (X%), social (X%), referral (X%)
- week_over_week_change: +X%
- top_pages: [path1 (X sessions), path2, path3]
- device_split: mobile X%, desktop X%, tablet X%
- engagement_rate: X% (mobile: X%, desktop: X%)
- anomalies: [2026-06-15: +X% sessions (search spike for "early signs")]
- questionnaire_starts: X, completions: X (X% completion rate)
- top_dropoff_step: step_3 (X% abandon)


[demographics] (when available via evidence connector, opt-in only)
- completeness: X questionnaire respondents of X total users
- top_self_reported: gender=F(X%), M(X%), race/ethnicity=..., age_band=...
- equity_flags: [Black users X% less likely to complete vs overall (p<0.05)]
```

The AI sees this context on every turn and can reference it immediately without
the user having to ask "what's in my data?"

---

## Phasing — when to build this

| Phase | What | Depends on |
| :-- | :-- | :-- |
| **v0.3.0** | Nothing — Drive import is the focus. Keep Gemini as the single provider. | — |
| **Post-v0.3.0 (candidate)** | Auto-analysis on GA4 connect: trends, top pages, anomalies, device split, retention. Stored in `st.session_state._ga4_insights`. Injected into every Gemini prompt. | `pull_ga4_report()`, existing `DataContext`, Gemini client |
| **When evidence connector is live** | Demographic overlay: equity reach, funnel equity, pathway equity, intersectional cuts. Opt-in only, small-cell enforced. | Evidence connector, questionnaire data loaded via Drive import or direct upload |
| **When survey data exists** | Survey cohort analysis: awareness change, confidence, satisfaction. Separate from GA4 — no individual join. | SurveyMonkey export, opt-in consent |


---

## Top 25 analyses — aspirational use cases

These are the questions the AI should be able to answer (from the BrainGuide
analysis framework). They are **not** implementation tasks — they define the
capability target for the insights engine.


| \# | Question | Needs demographics? |
| :-- | :-- | :-- |
| 1 | Who is the platform reaching overall? | No (GA4 counts suffice) |
| 2 | Are we reaching priority populations equitably? | Yes |
| 3 | Who completes the questionnaire? | Yes |
| 4 | Who drops off, and where? | Yes |
| 5 | Does the platform reach intended age groups? | Yes |
| 6 | Are women reached and engaged differently? | Yes |
| 7 | Are Black users reached and supported effectively? | Yes |
| 8 | Are Hispanic/Latino users reached effectively? | Yes |
| 9 | Is Spanish-language access functional and used? | Partial (language from GA4 + questionnaire) |
| 10 | Where do users first encounter the platform? | No |
| 11 | Which channels bring meaningful users? | Yes |
| 12 | Which search needs bring people to the site? | No |
| 13 | What content does each audience need? | Yes |
| 14 | Are users finding the right pathway? | Yes |
| 15 | Do users understand and act on tailored results? | Yes |
| 16 | Which content/interaction patterns predict completion? | Yes |
| 17 | Which patterns predict care-seeking? | Yes |
| 18 | Are users progressing toward clinical research? | Yes |
| 19 | Where does the research pathway leak? | Yes |
| 20 | Do local-resource features lead to action? | Yes |
| 21 | Does the experience work across devices/browsers? | Partial (device from GA4) |
| 22 | Are users returning for continued guidance? | Yes |
| 23 | Did the March 2026 relaunch improve the experience? | Yes |
| 24 | Does the platform increase awareness/confidence/action? | Yes (survey required) |
| 25 | What actions should be prioritized next? | Yes |

Of the 25, **6 are answerable with GA4 alone** (\#1, 10, 12, plus patterns in
\#21 and others). The remaining 19 require demographic data from the evidence
connector. This is a strong argument for building the evidence connector before
attempting the full insights engine.

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

The **first artifact** should be a **data dictionary and linkage map** — each
event, questionnaire field, downstream outcome, its owner, grain, timeframe,
join key, privacy status, and whether it is valid for pre/post-relaunch
comparison. That prevents incompatible measures from being mixed in the final
output.

The sketch is strong on **what the engine should answer** and appropriately treats demographics as opt-in, self-reported data. Its largest gaps are in the layer *between data and Gemini*: deterministic metric computation, semantic validation, linkage-quality checks, statistical guardrails, and operational/security design need to be specified before an AI can safely make reliable claims.[^2_1]

## Main design gap

The current design jumps from `pull_ga4_report()` to an LLM-ready insight block, but it does not define a **reproducible analytics service** that calculates, validates, and labels every metric before Gemini sees it. Gemini should interpret a constrained set of precomputed findings and explain implications; it should not be the primary calculator, funnel builder, statistical tester, or data-quality judge.

A better division is:

```text
GA4 / Evidence / Survey sources
        ↓
Data normalization + semantic mapping
        ↓
Deterministic metrics + quality tests + privacy rules
        ↓
Insight candidates with evidence, uncertainty, and provenance
        ↓
Gemini: prioritizes, explains, questions assumptions, drafts recommendations
        ↓
UI: findings, evidence, caveats, drill-down, user feedback
```

The real session-level linkage is not yet confirmed: the project notes say demographic persistence through GA4 was still an open technical question, and that it may not cover activity occurring before the questionnaire.  That makes the deterministic linkage layer—not the prompt—your main product risk.[^2_1]

## Missing data contract

`DataContext` needs a formal, versioned schema rather than a generic container of reports. The engine cannot reliably infer “funnel,” “completion,” “action,” or “meaningful engagement” from arbitrary GA4 event names.

Define a **semantic metric registry** for each property:


| Needed object | Example fields |
| :-- | :-- |
| Metric definition | `questionnaire_completion_rate`, numerator event, denominator event, event scope, grain |
| Event mapping | Canonical `questionnaire_started` → property-specific `web_questionnaire_start` |
| Funnel specification | Ordered steps, allowed re-entry, time window, same-session versus cross-session rule |
| Action taxonomy | `care_navigation`, `resource_use`, `research_interest`, `contact_intent`, `referral_submitted` |
| Dimension dictionary | Canonical channel, language, device, page category, content topic, user role |
| Data-quality status | Validated, provisional, broken, unavailable, pre/post-incomparable |
| Provenance | Source, query/report ID, date range, refresh time, schema version |
| Interpretation limits | “Intent inferred,” “descriptive only,” “not causal,” “small sample” |

This is especially important because BrainGuide’s current GA4 events include repeated questionnaire events, starts, finishes, tailored-page events, outbound clicks, resource visibility, and form activity; without an event-level semantic contract, a generic “key event” or click count can easily be misrepresented as an outcome.[^2_1]

### Add a feasibility matrix

For every proposed analysis, store:

- **Required grain:** aggregate daily, event-level, session-level, user-level, or linked questionnaire/session-level.
- **Required fields:** exact events, dimensions, and join IDs.
- **Minimum sample:** denominator threshold and cell threshold.
- **Current availability:** available, partial, unavailable, or needs instrumentation.
- **Inference type:** descriptive, comparative, predictive, or causal—not inferred from natural-language wording.
- **Confidence level:** high, moderate, low, or unusable.

For example, page views by device can run from ordinary GA4 aggregates; “which interaction sequence predicts completion” requires a consistent session/event sequence; “did tailored recommendations lead to care-seeking?” requires a valid definition and a downstream observation window. The current material indicates that session persistence of questionnaire demographics remains unresolved, so several intended cross-layer analyses must initially be marked **partial/unavailable**, rather than merely “future.”[^2_1]

## AI should not calculate

Several proposed findings need deterministic statistical code, not LLM reasoning.


| Current feature | Gap | Recommended implementation |
| :-- | :-- | :-- |
| Week-over-week change | No treatment of incomplete weeks, seasonality, campaign launches, or denominator changes | Date-completeness check, comparable-week logic, annotated interventions |
| `>2σ` anomalies | Fragile for sparse, seasonal, skewed, or changing-traffic data | Robust rolling median/MAD or forecasting residuals, minimum history and volume checks |
| Funnel drop-off | No rule for same session, repeat events, re-entry, or step ordering | Versioned funnel definition with deduplication and temporal rules |
| “Best/worst engagement” | “Engagement” is ambiguous and can favor low-volume pages | Minimum denominator, confidence interval, traffic-quality flags, topic grouping |
| “3× more likely” | Can sound causal and ignores uncertainty | Relative and absolute difference, sample sizes, confidence intervals, descriptive wording |
| `p < 0.05` equity flags | No test selection, multiple-comparison correction, or pre-specified hypothesis | Statistical service with effect sizes, confidence intervals, correction policy, and suppression |
| “Predict completion” | Not specified whether correlation, model association, or causal effect | Clearly label as descriptive association; use held-out validation if building a predictive model |

The sketch’s example—“social landing experience may have a language barrier”—is a useful **hypothesis**, but it should never appear as a conclusion from observational GA4 patterns alone. The engine should instead say: “Spanish-language users had lower observed completion after social entry; this is an association, with limited sample size, and should be validated through landing-page review and qualitative feedback.”

## Causal claims need guardrails

The “7 C’s” are excellent as a **journey framework**, but calling them “causal chains” is too strong for most available data. GA4 and questionnaire data can establish ordering, correlation, and drop-off patterns; they rarely establish that a page, channel, or content element *caused* completion or care-seeking.

Use an inference label on every insight:

- **Observed:** “Completion was lower for mobile sessions.”
- **Associated:** “Mobile sessions were associated with lower completion after adjusting for channel and language where available.”
- **Hypothesis:** “The mobile questionnaire flow may be contributing to abandonment.”
- **Experiment-supported:** “An A/B test showed the revised flow increased completion.”
- **Not assessable:** “Care-seeking cannot be attributed because downstream linkage is unavailable.”

This protects the product from overly confident AI language while still making findings useful.

## Linkage is underspecified

The evidence connector is framed as the demographic bridge, but the design needs a dedicated **linkage protocol**.

### Specify these fields

- Stable, de-identified `session_id`, `questionnaire_transaction_id`, and event/session timestamps.
- Source-system timestamp standard, time zone, and allowable time mismatch.
- One-to-one, one-to-many, and unmatched-link handling.
- Linkage success rate: “X% of questionnaire completers were linkable to GA4 behavior.”
- A join-coverage table by period, site version, language, and questionnaire version.
- Explicit rule for pre-questionnaire behavior, post-questionnaire behavior, and return sessions.
- A prohibition on joining email/contact records to GA4 unless explicit consent, purpose limitation, and approved governance permit it.

The project documentation distinguishes anonymous platform sessions from people who voluntarily provide email, and it records that demographic persistence across a session needs investigation.  The product should surface this as a **linkage coverage warning** whenever it renders demographic funnels, rather than burying it in a methodology note.[^2_1]

## Equity analysis gaps

The small-cell rule is a good start, but `<10` alone is not enough.

Add:

- **Denominator threshold:** A subgroup can have 10 people but still yield an unstable rate.
- **Intersectional-combination limit:** Prevent users from iteratively slicing cells until a person becomes identifiable.
- **Complementary suppression:** Hide related totals that allow a suppressed subgroup to be calculated by subtraction.
- **Difference attack protection:** Prevent user prompts from requesting two near-identical cuts that reveal a small group.
- **Missingness analysis:** Report who declines demographic questions; self-reported demographics are not representative by default.
- **Benchmark definition:** “Underrepresentation” requires an explicit comparator—service area, campaign audience, expected user population, or another agreed benchmark.
- **Fairness review:** Test whether the model produces stronger recommendations for high-volume populations while systematically treating low-volume priority populations as “insufficient data.”

The Spanish-language segment is currently exceptionally small—approximately nine people year-to-date in the project notes—so the engine should default to a qualitative/data-collection recommendation, not comparative performance ranking.[^2_1]

## Survey logic needs separation

“SurveyMonkey follow-up” is correctly separated as opt-in, but the design should formalize **three non-interchangeable populations**:


| Population | What it can support | Cannot support |
| :-- | :-- | :-- |
| GA4 visitors | Behavior and aggregate reach | Self-reported demographics, awareness change, person-level outcomes |
| Questionnaire respondents | Self-reported profile and in-session/questionnaire pathway, if linkage succeeds | Representation of all site visitors without response-rate context |
| Follow-up survey respondents | Reported awareness, confidence, satisfaction, and intended/actual action | Generalized causal claims about all BrainGuide users |

The current survey outreach is to approximately 353 June questionnaire contacts, not a probability sample of all site visitors, so the engine should always present survey response rate, invitation cohort, field dates, and respondent-vs-invited comparison before reporting outcomes.[^2_1]

## Data quality needs automation

The design identifies major concerns but does not say how the system will detect and prevent them from contaminating insight generation.

Build an automated **data quality gate** that runs before insights are generated:

- Event-volume continuity checks: sudden zeroes, spikes, duplicate firing, and renamed events.
- URL hygiene: assets, malformed paths, query-string fragmentation, redirects, `404`, `undefined`, and `(not set)` entries.
- Bot/crawler heuristic: anomalous geography/device/engagement combinations and asset-heavy page paths.
- Reporting completeness: partial day, partial week, API sampling/thresholding, delayed processing.
- Schema drift: missing dimensions, altered custom events, changed campaign taxonomy.
- Pre/post relaunch comparability: page/path and event equivalence matrix.
- Outlier review: label suspected instrumentation changes separately from actual behavioral anomalies.
- Data freshness: source refresh timestamp and period through which data are complete.

The exact relaunch date remains an open item in the project documentation, even though the new site is estimated to have launched in early March; all trend and before/after logic should therefore remain blocked until that date and a page/event crosswalk are confirmed.[^2_1]

## Prompt contract gaps

The proposed prompt block is compact but too lossy for trustworthy follow-up questions. It needs **structured evidence objects**, not only summary bullets.

Instead of:

```yaml
questionnaire_starts: 1000
completions: 500
top_dropoff_step: step_3
```

use:

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
provenance:
  source: ga4
  report: funnel_report_v2
  period: "2026-01-01/2026-07-31"
  generated_at: "..."
```

Then Gemini can cite a specific insight ID, describe what it knows, disclose what it does not know, and avoid recalculating. This also makes UI drill-down, audit logging, evaluation, and future model-provider changes much easier.

### Protect against prompt injection

GA4 data is not automatically trustworthy text. Page titles, page paths, UTMs, campaign names, search terms, and custom event parameters can contain attacker-controlled or malformed strings.

Before any text reaches Gemini:

- Normalize and encode untrusted labels.
- Never allow source data to define system instructions.
- Use structured JSON/tool inputs instead of interpolating raw values into prose.
- Strip or quarantine suspicious values.
- Limit field lengths and cardinality.
- Keep the system prompt, data context, and user prompt in separate message roles.
- Log whether a finding arose from raw label text versus a controlled taxonomy.


## Product interaction gaps

The design is currently an invisible auto-analysis pass plus chat injection. That risks making findings feel authoritative but unauditable.

Add an **Insights inbox** or dashboard with:

- Finding title, priority, evidence strength, and affected cohort.
- Plain-language explanation plus “Why am I seeing this?”
- Metric definition, denominator, date range, and comparison.
- Caveat badges: small sample, partial data, relaunch break, inferred intent, unvalidated event.
- Drill-down to the relevant report/table, but not raw PII.
- User controls: save, dismiss, mark inaccurate, investigate, and create follow-up question.
- Feedback capture: “useful,” “not useful,” “wrong because…”
- Recommendation status: proposed, accepted, tested, implemented, outcome unknown.

This turns the engine into a learning workflow rather than a stream of AI-generated observations.

## Operational gaps

You also need explicit decisions on:

- **Refresh policy:** OAuth-connect snapshot versus daily refresh versus on-demand; stale-insight labeling.
- **Cost and latency:** Avoid rerunning full analysis and injecting all findings on every chat turn.
- **Caching:** Cache deterministic summaries by property, date range, and schema version—not just in `st.session_state`.
- **Multi-property isolation:** Scope every query and cache key to the authenticated GA4 property and workspace.
- **Permission model:** Who can view equity cuts, survey results, linkage diagnostics, and evidence data?
- **Audit trail:** Store the query, source versions, generated insight IDs, prompt version, model version, and rendered response.
- **Evaluation set:** Build a labeled set of expected findings, non-findings, false-positive traps, privacy cases, and relaunch-break cases.
- **Failure behavior:** If data are incomplete or event taxonomy is unvalidated, the engine should say so and offer a data-quality task—not fabricate a pattern.


## Recommended phase change

I would split the current “post-v0.3.0 candidate” into four smaller gates:


| Gate | Deliverable | AI role |
| :-- | :-- | :-- |
| **0. Data readiness** | Data dictionary, event taxonomy, relaunch crosswalk, quality checks, metric registry | None or limited explanation |
| **1. GA4 descriptive insights** | Validated trends, channels, pages, device, basic funnels, data-quality alerts | Summarize and prioritize precomputed findings |
| **2. Evidence overlay** | Linkage coverage, demographic completeness, suppression, equity descriptive comparisons | Explain approved aggregates; never infer missing demographics |
| **3. Outcomes and evaluation** | Survey cohort reporting, downstream aggregate outcomes, hypothesis/experiment workflow | Synthesize mixed-method findings and recommend next tests |

The project already has a clear need for this first gate: questionnaire demographics are self-reported rather than GA4-derived, the platform is largely anonymous, and the feasibility of persistent custom demographic variables is not yet confirmed.[^2_1]

## Definition of done

Do not call the Insights Engine ready when it can write plausible observations. Call it ready when every surfaced insight can answer:

1. **What exactly was measured?**
2. **What is the numerator, denominator, unit, and date range?**
3. **Which source and event definitions produced it?**
4. **Is the comparison valid across the relaunch boundary?**
5. **What data-quality checks passed or failed?**
6. **What population does it represent—and who is missing?**
7. **Is this descriptive, associated, hypothesized, or experimentally supported?**
8. **What uncertainty, suppression, or privacy constraint applies?**
9. **Can the user inspect the evidence without seeing identifiers?**
10. **What next action is justified, and what would validate it?**

The concept is worth building, but the highest-leverage feature is not “automatic Gemini insights.” It is a **trust layer** that turns inconsistent web, questionnaire, and survey data into auditable, privacy-safe, statistically bounded insight objects that Gemini can communicate well.
<span style="display:none">[^2_2]</span>

<div align="center">⁂</div>

[^2_1]: Web Analytics  2026-07-23 15_30(GMT-4_00).md

[^2_2]: meeting-notes-072326.txt
