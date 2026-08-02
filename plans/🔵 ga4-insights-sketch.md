# GA4 Insights Engine — Design Sketch

> **Status:** 🔵 Sketch — not in any active sprint. Post-v0.3.0 candidate.
> **Cross-refs:** [`🔵 evidence-connector-design.md`](🔵%20evidence-connector-design.md) — demographic data bridge (opt-in survey only).

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
|---|---|---|---|---|
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
|---|---|
| **Reach** | Total users, new vs returning, sessions, geography (country/region from GA4), top acquisition channels |
| **Trends** | Week-over-week session change, day-of-week patterns, top/bottom performing days |
| **Top pages** | Highest-traffic page paths by sessions, pages with best/worst engagement rate |
| **Device** | Mobile vs desktop vs tablet split, device-specific bounce/engagement patterns |
| **Funnel** | Key event start-to-completion rates, step-by-step drop-off, time to completion |
| **Anomalies** | Days with >2σ deviation from rolling mean on sessions, engagement rate cliffs, bounce-rate spikes |
| **Retention** | Day-1/7/14/28 cohort retention, return rate by acquisition channel |

### Computed when demographics are available (via evidence connector, opt-in only)

| Category | Specific findings |
|---|---|
| **Equity reach** | Demographic profile of completers vs all users vs benchmark; over/underrepresentation by priority population |
| **Funnel equity** | Completion and drop-off rates stratified by age, gender, race/ethnicity, language, device, role |
| **Pathway equity** | Which acquisition channels and content paths serve which populations effectively |
| **Intersectional cuts** | Combinations (e.g. women 45–64, Black caregivers) — only where cell sizes ≥ defined threshold |
| **Language access** | Spanish-language page views, starts, completions, resource clicks vs overall |**Small-cell rule:** suppress or aggregate any group with < 10 individuals. Flag
unstable percentages. Spanish-language volume is currently ~9 year-to-date and
must be treated qualitatively.

**Validity caveats apply:** every auto-computed finding is accompanied by its
measurement-validity qualification — e.g., key-event rates are descriptive only
until the event taxonomy is audited, retention is browser/device-based (not
person-level), and pre/post-March 2026 comparisons are separated or flagged.
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
|---|---|---|
| **All site visitors** | GA4 users or sessions | `pull_ga4_report()` |
| **Questionnaire starters** | Users with `web_questionnaire_start` event | GA4 events |
| **Questionnaire completers** | Users with `web_questionnaire_finish` event | GA4 events |
| **Action-takers** | Users with a meaningful post-result action (provider finder, local-resource click, trial view, contact form, referral) | GA4 events |
| **Survey respondents** | Separate, self-selected follow-up cohort | Evidence connector (future) |

---

## Measurement validity requirements

The AI must qualify its analysis against these known data quality concerns:

| Concern | Mitigation |
|---|---|
| **Event taxonomy** | Confirm what counts as a "key event" — current key-event rates appear very high across channels, suggesting the designation may capture routine activity rather than meaningful outcomes |
| **Bot/crawler traffic** | Landing-page reports include asset URLs and anomalous entries that distort engagement findings unless filtered |
| **Pre/post relaunch** | The site was relaunched ~March 2026 in the same GA4 property. Use page path (not title), establish the exact launch date, and analyze equivalent pathways separately before/after |
| **Anonymous vs identified** | Most use is anonymous. Email or contact-center data must not be joined to GA4 absent explicit permission and privacy controls |
| **Retention limitations** | Browser/device-based return measures do not establish person-level longitudinal records |

---

## Privacy & ethics constraints

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

## Pre-implementation decisions

These measurement-design questions must be settled by the team **before**
building the auto-analysis engine:

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
   Validate event firing, duplicates, zero-count events, key-event
   configuration, and whether clicks represent completed external actions.
6. **What is the official relaunch date and which pathways changed?** No
   unqualified pre/post comparison should be made until this is fixed.
7. **What comparison benchmark will define equitable reach?** Census/
   service-area population, target audience composition, campaign audience,
   or a prior-period baseline each answers a different question.
8. **What downstream records can be linked ethically and reliably?** Contact
   center, referral, and research outcomes should be connected only through
   approved, minimum-necessary de-identified methods.
9. **How will survey selection bias be handled?** The survey cohort (~353
   people) is not a probability sample; report response rate, respondent
   profile, and limits to generalization.
10. **What reporting thresholds and privacy rules apply?** Establish small-cell
    suppression, aggregation, and role-based access before reviewing
    demographic cuts.

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
```The AI sees this context on every turn and can reference it immediately without
the user having to ask "what's in my data?" These blocks consume ~200–500 tokens
of the 1M-token Gemini 2.5 Flash context window — negligible for typical datasets.
---

## Phasing — when to build this

| Phase | What | Depends on |
|---|---|---|
| **v0.3.0** | Nothing — Drive import is the focus. Keep Gemini as the single provider. | — |
| **Post-v0.3.0 (candidate)** | Auto-analysis on GA4 connect: trends, top pages, anomalies, device split, retention. Stored in `st.session_state._ga4_insights`. Injected into every Gemini prompt. | `pull_ga4_report()`, existing `DataContext`, Gemini client |
| **When evidence connector is live** | Demographic overlay: equity reach, funnel equity, pathway equity, intersectional cuts. Opt-in only, small-cell enforced. | Evidence connector, questionnaire data loaded via Drive import or direct upload |
| **When survey data exists** | Survey cohort analysis: awareness change, confidence, satisfaction. Separate from GA4 — no individual join. | SurveyMonkey export, opt-in consent |

---

## Top 25 analyses — aspirational use cases

These are the questions the AI should be able to answer (from the BrainGuide
analysis framework). They are **not** implementation tasks — they define the
capability target for the insights engine.

| # | Question | Needs demographics? |
|---|---|---|
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

Of the 25, **6 are answerable with GA4 alone** (#1, 10, 12, plus patterns in
#21 and others). The remaining 19 require demographic data from the evidence
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
