# BrainGuide Demographic Disparity Analysis

> **Snapshot analyzed:** Evidence dashboard capture dated 2026-08-06; source data has report-specific freshness dates through 2026-08-04.
> **Status:** Provisional descriptive analysis — not a population-representativeness study and not a clinical or causal evaluation.
> **Related sources:** [`CONSOLIDATED.md`](../CONSOLIDATED.md), [`CONSOLIDATED.json`](../CONSOLIDATED.json), [`DEMOGRAPHIC_EQUITY_PROTOCOL.md`](./DEMOGRAPHIC_EQUITY_PROTOCOL.md), [`DEMOGRAPHIC_EQUITY_SNAPSHOT.json`](./DEMOGRAPHIC_EQUITY_SNAPSHOT.json), [`braintree-reqs.md`](../../braintree-reqs.md), [`BRAINTREE_CHECKLIST.md`](../../BRAINTREE_CHECKLIST.md)
>
> **Provenance convention:** Key dashboard facts cite the source PDF and page below. Percentages labeled “displayed rows” are calculated from the visible rows in that PDF table; they are not silently treated as the dashboard’s complete population denominator.

## Evidence provenance quick index

| Evidence used | Source and page |
|---|---|
| Results Overview race rows and White count | `../reports/Results Overview.pdf`, p. 7; demographic/filter definitions are on pp. 4, 13–14 |
| AD8 race rows | `../reports/AD8 Analysis.pdf`, p. 5 |
| MIS race rows | `../reports/MIS Analysis.pdf`, p. 5 |
| SBC race rows | `../reports/SBC Analysis.pdf`, p. 4 |
| English/Spanish overall pageviews | `../reports/Top Content.pdf`, p. 3; locale mapping/definitions on pp. 1 and 8 |
| Clinical Trials English/Spanish visits and clicks | `../reports/Clinical Trials.pdf`, pp. 1–3 |
| Find a Provider English/Spanish visits and clicks | `../reports/Find a Provider.pdf`, pp. 1–3 |
| Device exit rates and exit-rate definition | `../reports/User Journeys.pdf`, pp. 2, 4–5 |

All page references refer to the captured PDFs in [`reports/`](../reports/), not to a live dashboard whose content may change.

## Benchmark decision required before publishing a disparity ratio

The recommended default for **population reach** is a service-area benchmark built from the U.S. Census Bureau ACS 5-year estimates, matched to BrainGuide's actual geographic reach and age eligibility. If the business question is campaign performance instead, use the campaign's eligible audience as the benchmark; if the question is retention or product change, use a prior-period BrainGuide cohort. The report owner must record the chosen benchmark, geography, age range, inclusion criteria, race/ethnicity coding, and date window before labeling a group “under-represented.”

For the eventual analysis, calculate representation ratios and percentage-point differences with 95% confidence intervals where appropriate, and run sensitivity analyses for missing/unknown race. Do not use one national benchmark for every product or campaign question.

## Operational privacy and stability rules

- Suppress any released cell with **n < 10**, consistent with the repository policy.
- Apply complementary suppression when a suppressed cell could be reconstructed from a subtotal or overlapping slice.
- Require a separate minimum denominator for rates; **n ≥ 10 is a privacy floor, not a stability guarantee**. The analytics owner should set and document a rate-stability threshold before publication.
- Suppress or aggregate intersectional cuts when either the numerator/denominator is unstable or repeated slicing could enable a difference attack.
- Keep race/ethnicity collection optional, explain purpose and retention, restrict access, and preserve access to results/resources when a user declines.
- Treat the race question itself as a potential selection effect: compare completion and nonresponse before and after any redesign.

## Executive conclusion

BrainGuide's questionnaire evidence shows a pronounced **White/Caucasian concentration** and much smaller observed Black/African American and Hispanic/Latino respondent groups:

- In the Results Overview race rows (`../reports/Results Overview.pdf`, p. 7), White/Caucasian respondents are **42,556**, Black/African American respondents **2,433**, and Hispanic/Latino respondents **2,675**.
- Among the displayed race rows, these are approximately **77.9% White, 4.5% Black, and 4.9% Hispanic/Latino**. White respondents outnumber the displayed Black and Hispanic/Latino rows by approximately **17.5:1** and **15.9:1**, respectively.
- The dashboard reports race information for approximately **75%** of the Results Overview filtered population. Demographics are primarily available from the scored-completion population downward, not from every visitor or every questionnaire starter.
- Spanish-language pageviews are **5.5%** of Top Content pageviews in the captured period (`../reports/Top Content.pdf`, p. 3). Spanish traffic is present and meaningful, but materially smaller than English traffic.
- The current evidence does **not** support a precise claim such as “Black users are X% underrepresented” because the analysis lacks a validated, like-for-like denominator: all eligible visitors, questionnaire starters, and scored completers are not currently linked and measured by the same race/ethnicity definition and time window.

The most defensible conclusion is therefore:

> **Observed reach is not demographically balanced, and the gap is important enough to treat as an equity risk. The size and location of the gap — acquisition, language access, device friction, questionnaire selection, or some combination — remain unconfirmed.**

This is still actionable. The first response should be to reduce avoidable UX, language, accessibility, trust, and measurement barriers while building a valid funnel denominator. Outreach should follow — and be evaluated — rather than substituting for product fixes.

## 1. Hardening pass and use of this artifact

This report is the descriptive findings layer. The [`DEMOGRAPHIC_EQUITY_COVERAGE.md`](./DEMOGRAPHIC_EQUITY_COVERAGE.md) / [`DEMOGRAPHIC_EQUITY_COVERAGE.json`](./DEMOGRAPHIC_EQUITY_COVERAGE.json) matrix is the question-by-question audit: it records whether each of the 25 client questions is supported now, partial, or blocked and what unlocks full support. The companion [`DEMOGRAPHIC_EQUITY_PROTOCOL.md`](./DEMOGRAPHIC_EQUITY_PROTOCOL.md) is the implementation contract for the five phases: measurement/benchmark, funnel and missingness, mechanism validation, controlled UX/UI intervention, and outreach/outcome evaluation. The companion [`DEMOGRAPHIC_EQUITY_SNAPSHOT.json`](./DEMOGRAPHIC_EQUITY_SNAPSHOT.json) is generated by [`scripts/analyze_demographic_equity.py`](../../scripts/analyze_demographic_equity.py) and contains only calculations supported by the current aggregate snapshot. These artifacts intentionally distinguish **supported now** from **blocked pending new data**.

## 1. How this analysis separates fact from hypothesis

| Label | Meaning in this document |
|---|---|
| **Observed** | Directly reported by the captured Evidence dashboard or calculated from a displayed count. |
| **Comparative** | A descriptive difference between groups, periods, or flows using a stated denominator. |
| **Research-supported mechanism** | A plausible explanation documented in external literature; it is not proof that the mechanism caused BrainGuide's pattern. |
| **Hypothesis for BrainGuide** | A mechanism that should be tested with event data, UX review, interviews, or an experiment. |
| **Not assessable yet** | The required denominator, linkage, sample, or validated measure is unavailable. |

### What “under-represented” can mean

The word **under-represented** is ambiguous unless the comparator is specified. At least four different questions are possible:

1. **Population reach:** Do BrainGuide visitors resemble the population in the geographic service area?
2. **Audience reach:** Do visitors resemble the intended audience for a campaign or program?
3. **Funnel equity:** Once people arrive or start, do groups progress at comparable rates?
4. **Outcome equity:** Do groups receive comparable access to useful guidance and downstream resources?

The current dashboard primarily describes **scored questionnaire respondents** and aggregate website activity. It cannot yet answer all four questions. The benchmark must be agreed before publishing a disparity ratio: national Census, service-area Census/ACS, campaign audience, eligible older-adult population, prior-period BrainGuide users, or another defined population each answers a different question.

## 2. Observed demographic evidence

### 2.1 Results Overview race composition

The following calculations use the displayed race rows from the Results Overview capture (`../reports/Results Overview.pdf`, p. 7). The row sum is **54,626**. It should be treated as a **displayed-row denominator**, not automatically as the total number of eligible site users, questionnaire starters, or even all race-answered respondents, because the dashboard also reports report-specific demographic coverage and filters.

| Displayed race row | Count | Share of displayed race rows | Dashboard display / note |
|---|---:|---:|---|
| White/Caucasian | 42,556 | **77.9%** | Calculated from displayed rows; PDF table shows the underlying count |
| Prefer not to answer | 3,074 | 5.6% | Explicit response; do not merge with skipped/missing |
| Hispanic/Latino | 2,675 | **4.9%** | Calculated from displayed rows; PDF table shows the underlying count |
| Black/African American | 2,433 | **4.5%** | Calculated from displayed rows; PDF table shows the underlying count |
| Asian | 1,417 | 2.6% |  |
| Mixed | 1,272 | 2.3% | Multi-select handling is product-defined |
| Other/Not Listed | 573 | 1.0% |  |
| American Indian/Alaska Native | 536 | 1.0% |  |
| Native Hawaiian/Pacific Islander | 90 | 0.2% |  |
| **Displayed rows** | **54,626** | **100.0%** | Calculation denominator only |

**Observed comparison:**

- White : Black displayed-row ratio = **42,556 / 2,433 = 17.49**.
- White : Hispanic/Latino displayed-row ratio = **42,556 / 2,675 = 15.91**.
- Black and Hispanic/Latino displayed-row counts are close to one another in this view, but both are far below the White row.

**Conclusion:** The respondent composition is visibly White-heavy. This is a high-priority reach-equity signal, but it is not yet a valid population disparity estimate. A valid estimate needs the same race/ethnicity instrument, denominator, geography, eligibility criteria, date range, and missingness treatment on both sides of the comparison.

### 2.2 Race composition differs by questionnaire flow

The displayed race rows also vary by flow. The rows below do **not** always sum to the flow KPI, so percentages are explicitly labeled “among displayed rows.” They should not be treated as complete flow composition until the underlying query is reconciled.

| Flow | Flow KPI | Displayed race-row sum | White | Black | Hispanic/Latino | White share among displayed rows | Black share | Hispanic/Latino share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AD8 | 12,330 completions | 10,760 | 7,582 | 500 | 516 | 70.5% | 4.6% | 4.8% |
| MIS | 107,976 completions | 94,929 | 74,612 | 4,500 | 4,611 | 78.6% | 4.7% | 4.9% |
| SBC | 1,751 scored results | 1,679 | 1,241 | 119 | 94 | 73.9% | 7.1% | 5.6% |

**Important semantic differences:**

- **AD8 demographics describe the informant/caregiver**, not necessarily the person experiencing symptoms.
- **MIS is a self-administered memory flow.**
- **SBC demographics describe scored respondents**, a highly selected group because only **1,751 of 36,803 entries (4.8%)** produced a scored result.
- These populations should not be combined into one “BrainGuide user” category.

**Conclusion:** The White concentration is not solely a property of one assessment. It appears in each displayed flow, although the percentages vary. The variation is not interpretable as a racial difference in cognitive performance or risk: the flow populations, missingness, selection, and row completeness differ.

### 2.3 Spanish-language reach

The overall locale totals below come from `../reports/Top Content.pdf`, p. 3; the Clinical Trials and Find a Provider figures come from their respective PDFs, pp. 1–2.

Observed language and locale signals:

| Measure | English | Spanish | Spanish relative to English / total |
|---|---:|---:|---:|
| Top Content pageviews | 487,949 | 28,531 | Spanish **5.5%** of total; English 94.5% |
| Clinical Trials visits | 44,450 | 5,972 | Spanish 11.8% of these page visits |
| Clinical Trials clicks | 7,984 | 347 | Visit-based click rate: English 18.0%, Spanish 5.8% |
| Find a Provider visits | 15,974 | 194 | Spanish 1.2% of these page visits |
| Find a Provider clicks | 1,227 | **<10 (source cell suppressed in hardened artifact)** | Spanish rate suppressed: denominator below the 50-session stability floor |

These calculations use visit-based dashboard counts; a visit can generate multiple clicks, so these are not unique-person conversions. The Spanish questionnaire/contact volume in the project requirements is considered exceptionally small for reliable comparative rates, and the consolidated registry separately warns that small Spanish word-set rows are unstable.

**Conclusion:** Spanish content is being used, but Spanish reach is low relative to English across the overall site and especially the provider pathway. The lower observed Spanish Clinical Trials click rate is a **hypothesis-generating signal**, not proof that Spanish users find the content less useful. The Spanish Find a Provider click cell is suppressed in the hardened artifact because its source count is below the release floor and its denominator is below the rate-stability floor. Possible explanations include language friction, different intent, incomplete translation, different resource availability, campaign mix, device mix, small-sample instability, or tracking differences.

### 2.4 Device and journey friction

The User Journeys capture (`../reports/User Journeys.pdf`, p. 5) reports page-level exit rates of:

- Mobile: **74.7%**
- Tablet: **80.2%**
- Desktop: **62.8%**

This is a descriptive page-sequence exit measure, not bounce rate and not a demographic metric. It is nevertheless important because smartphone-only access, older-adult technology use, limited bandwidth, and device constraints can intersect with race, ethnicity, age, income, language, and disability.

**Conclusion:** Mobile and tablet experience deserve immediate attention. We cannot say from this capture that Black or Hispanic users have higher mobile exit rates because the demographic-by-device funnel is not available. But if priority groups disproportionately depend on mobile or lower-bandwidth access, a high mobile exit rate can amplify an existing reach gap.

### 2.5 Missingness and selection

The Results Overview capture (`../reports/Results Overview.pdf`, p. 4) reports approximately:

- Gender information: **79%**
- Age information: **77%**
- Race information: **75%**

The dashboard's demographic fields apply from **Received Score downward**. This means a person who visits, starts, abandons, chooses the information-only path, or fails to produce an SBC score may be absent from the race denominator altogether.

**Conclusion:** Missingness is not a footnote; it is a likely source of disparity bias. If people who abandon earlier differ by race, language, age, device, or trust, then the observed respondent composition can substantially misrepresent the composition of people who attempted to use BrainGuide. “Prefer not to answer” must remain separate from skipped, unavailable, or technically missing data.

### 2.6 Gender, age, education, acquisition, and geography

The broader demographic and reach tables add context, but they do not by themselves establish equity:

- **Gender:** Results Overview p. 7 shows 39,889 female, 14,740 male, 2,013 Prefer not to answer, and 243 non-binary/gender-fluid/other responses. Among these displayed gender rows, female respondents are approximately **70.1%** and male respondents **25.9%**. This may reflect the audience and caregiving role of the product, but it should not be interpreted as a sex/gender-specific need or outcome without a benchmark and flow-specific denominator.
- **Age:** Results Overview p. 7 shows at least 6,721 respondents under 45 (12.1%) and 5,957 ages 45–54 (10.7%). The captured excerpt does not provide a complete, reconciled age distribution for all older buckets, so it cannot answer whether BrainGuide reaches its intended older-adult audience adequately. AD8 informants and MIS/SBC self-respondents also have different roles, making flow-specific age analysis necessary.
- **Education:** Results Overview p. 7 shows 2,095 respondents with less than high school (3.8%) and 16,959 with high school/equivalent (30.4%). Education is both a possible access determinant and a potential selection variable; it should be used to test readability and digital-literacy friction, not to infer cognitive ability.
- **Acquisition:** Results Overview pp. 8–9 attributes 60,670 responses (70.9%) to `(none)`. This is an unattributed/UTM-none bucket, not proof of organic search or direct traffic. It limits the ability to identify which outreach channels reach Black and Hispanic/Latino audiences.
- **Geography:** Geographic Traffic p. 1 reports **620,861 U.S. users**, 570,877 sessions, and 81 states/territories reached; California, Florida, Texas, New York, and Pennsylvania are among the leading states (pp. 5–6). This value is reconciled to the consolidated registry and is the value used in the current artifact. Geography is useful for selecting a service-area benchmark and community partners, but it is not a substitute for self-reported race/ethnicity and is not yet joined to questionnaire completion by group.
- **Demographic content:** Top Content by Demographic is a small, post-questionnaire attribution sample. It can identify within-group page affinity after approved linkage, but it cannot establish that a page caused a group to convert or that raw counts are comparable across groups.

**Conclusion:** The overall audience appears female-heavy and includes substantial younger respondents, but age, education, gender, acquisition, and geography currently describe composition rather than disparity. The most urgent missing cross-dimensional cuts are **race/ethnicity × language × device × funnel step**, with sufficient denominators and suppression. Avoid interpreting gender, age, or education differences as biological or cognitive differences.

## 3. Issue-by-issue analysis and conclusions

### Issue 1 — White respondents dominate the observed questionnaire evidence

**Observed:** White/Caucasian is 77.9% of the displayed Results Overview race rows (`../reports/Results Overview.pdf`, p. 7); Black/African American is 4.5%; Hispanic/Latino is 4.9%. Similar White-heavy patterns appear in the displayed AD8, MIS, and SBC rows (`../reports/AD8 Analysis.pdf`, p. 5; `../reports/MIS Analysis.pdf`, p. 5; `../reports/SBC Analysis.pdf`, p. 4).

**Why this matters:** The groups of greatest interest to the client are not appearing in the respondent evidence at a level that would support confident subgroup learning, culturally specific content optimization, or equitable reach claims. The gap also matters because external literature documents higher dementia burden and lower awareness/diagnosis timeliness among Black and Hispanic older adults.

**Research-supported mechanisms, not BrainGuide findings:**

- Lin et al. found lower reported awareness of dementia status among non-Hispanic Black and Hispanic older adults than non-Hispanic White adults in a Health and Retirement Study cohort ([JAGS 2020, PMC7552114](https://pmc.ncbi.nlm.nih.gov/articles/PMC7552114/)).
- Lin et al. found higher proportions of missed or delayed claims-based dementia diagnosis among non-Hispanic Black and Hispanic older adults than non-Hispanic White adults, with longer estimated delays ([Medical Care 2021, PMC8263486](https://pmc.ncbi.nlm.nih.gov/articles/PMC8263486/)).
- Portacolone et al. found that African American older adults and caregivers described both a strong desire for dementia education/research and historically rooted institutional distrust; participants emphasized that trust must be earned through sustained community partnership ([Ethnicity & Disease 2020, PMC7683027](https://pmc.ncbi.nlm.nih.gov/articles/PMC7683027/)).
- Epps et al. observed that a dementia-education workshop delivered through predominantly African American congregations shifted immediate attitudes toward more hopeful and action-oriented language ([Journal of Applied Gerontology 2021, PMC8302664](https://pmc.ncbi.nlm.nih.gov/articles/PMC8302664/)). This supports testing trusted-messenger education, not assuming it will change BrainGuide behavior.
- Stites et al. found that Black adults expressed concerns about discrimination and downstream consequences when presented with Alzheimer’s biomarker information ([Ethnicity & Health 2024, PMC11560502](https://pmc.ncbi.nlm.nih.gov/articles/PMC11560502/)). This supports privacy-forward, non-diagnostic copy; it does not show that BrainGuide users hold the same concerns.
- These findings suggest a plausible **awareness, trust, and care-pathway mechanism**: people who have not been informed, recognized symptoms, or entered formal care may be less likely to seek a self-guided cognitive tool, while people who fear downstream consequences may hesitate to disclose concerns. They do not prove that these mechanisms explain BrainGuide's composition.

**Alternative explanations:** acquisition targeting; referral network composition; Census/service-area mismatch; language; device; missingness; campaign attribution; trust/privacy concerns; different rates of caregiving vs self-concern; and technical drop-off.

**Conclusion:** **High-priority observed reach gap; population under-representation not yet quantified.** Do not frame the result as a racial difference in interest or need.

### Issue 2 — The current funnel cannot locate the disparity

**Observed:** Demographics are available primarily after scored completion; SBC has a 95.2% entry-to-scored-result gap; the information-only flow does not carry assessment demographics in the same way.

**Why this matters:** A low share of Black or Hispanic scored respondents could result from low acquisition, low start rate, early form abandonment, language switching, recording failure, result-page loss, or a combination. The current data cannot distinguish these.

**Research-supported mechanisms:** A Latinx online ADRD education recruitment study found that only 8 of 209 invited participants attended; attendance was shaped by education, cognitive impairment, language preference, and age (Gutiérrez et al., [2022, PMC8891594](https://pmc.ncbi.nlm.nih.gov/articles/PMC8891594/)). This is not a BrainGuide study and was conducted during COVID-era online programming, but it demonstrates why “online availability” is not equivalent to equitable participation.

**Conclusion:** **The first analytical priority is funnel instrumentation, not subgroup score comparison.** The product needs race/language/device visibility at starts and each major step, with consent and privacy protections, before it can identify where the gap occurs.

### Issue 3 — Spanish access is present but may not be functionally equivalent

**Observed:** Spanish is 5.5% of overall Top Content pageviews (`../reports/Top Content.pdf`, p. 3). Spanish Clinical Trials and Find a Provider visits and clicks are much smaller than English; the simple visit-based CTRs are also lower in this snapshot (`../reports/Clinical Trials.pdf`, pp. 1–2; `../reports/Find a Provider.pdf`, pp. 1–2).

**Research-supported mechanisms:**

- Among Spanish-preferred patients, Philpot et al. found that 73.6% reported discomfort reading or writing English; Spanish-speaking LEP respondents reported more difficulty learning new technology, evaluating online health information, identifying quality information, and accessing online services ([Frontiers in Public Health 2024, PMC11666482](https://pmc.ncbi.nlm.nih.gov/articles/PMC11666482/)).
- A systematic review of U.S. Latino adults found mixed knowledge of brain health and consistent recognition of memory loss but limited recognition of other cognitive symptoms and protective factors (Light et al., [Aging & Mental Health 2024, PMC10983845](https://pmc.ncbi.nlm.nih.gov/articles/PMC10983845/)).
- Gutiérrez et al. found that online ADRD education recruitment barriers intersected with age, language preference, education, and cognitive impairment ([PMC8891594](https://pmc.ncbi.nlm.nih.gov/articles/PMC8891594/)).

**BrainGuide hypotheses to test:** Spanish navigation is harder to discover; translation is incomplete or not culturally/native-language reviewed; Spanish assessment instructions or word sets are less comfortable; language switching loses progress; English-first links or forms interrupt the journey; Spanish users have different acquisition intent; or tracking misses some Spanish events.

**Conclusion:** **Spanish access is measurable but not yet demonstrated to be functionally equivalent.** Treat it as a product-quality and reach-equity issue, not merely a translation task.

### Issue 4 — Trust, privacy, and stigma may suppress self-directed use

**Observed:** The dashboard does not directly measure trust, stigma, fear of diagnosis, concern about data disclosure, or prior negative healthcare experiences.

**Research-supported mechanisms:**

- A review of dementia stigma in culturally and linguistically diverse communities identifies cultural beliefs, language barriers, limited awareness, migration, and stigmatizing terminology as contributors to delayed help-seeking and disclosure (Siette et al., [Frontiers in Psychiatry 2023, PMC10765564](https://pmc.ncbi.nlm.nih.gov/articles/PMC10765564/)). Its context is broader than U.S. Black and Hispanic populations, so it should guide questions, not be treated as a direct estimate.
- Chau et al. describe how historical abuse, structural racism, privacy concerns, and negative healthcare encounters can shape institutional trust, and how community-based organizations can act as trusted messengers ([Hastings Center Report 2023, PMC10939007](https://pmc.ncbi.nlm.nih.gov/articles/PMC10939007/)).

**BrainGuide hypotheses to test:** Users may not understand what the assessment does with answers; “screening” or result labels may feel diagnostic; users may fear that a result affects insurance, family, immigration, employment, or care; and the brand may not be visibly connected to trusted local messengers.

**Conclusion:** **Trust and stigma are plausible barriers with strong external support but no direct BrainGuide measurement.** Improve transparent, non-alarming copy and test with community members before assuming a particular cause.

### Issue 5 — Device and accessibility friction may amplify demographic gaps

**Observed:** Mobile and tablet exit rates are higher than desktop (`../reports/User Journeys.pdf`, p. 5). SBC produces a scored result for only 4.8% of entries (`../reports/SBC Analysis.pdf`, pp. 2–3), and the current report does not distinguish abandonment from microphone permission failure, recording failure, browser incompatibility, network failure, or server-side scoring failure.

**Research-supported mechanisms:** Digital health equity research identifies device/connectivity, ease of navigation, culture, age, socioeconomic status, education, residence, and supportive infrastructure as interacting factors. Wilson et al.'s systematic review recommends user-friendly interfaces, compatibility with existing devices, culturally appropriate content, non-digital options, and educational support ([npj Digital Medicine 2024, PMC11217442](https://pmc.ncbi.nlm.nih.gov/articles/PMC11217442/)).

**Conclusion:** **High-confidence product opportunity, low-confidence demographic attribution.** Fix measurable device friction now, then stratify the resulting funnel by language and voluntarily supplied demographic groups.

### Issue 6 — Content may be discoverable unevenly across groups

**Observed:** Top Content includes large English traffic and a smaller Spanish stream; the demographic-content report is a self-selected post-questionnaire attribution sample, not a general population sample. It attributes a user's demographic to pages viewed during the export window and should be used for within-group descriptive affinity only.

**Possible mechanisms:** search language and terminology; referral partnerships; content imagery and examples; reading level; page speed; URL and locale mapping; resource relevance; and whether a visitor sees a clear “what to do next” path.

**Conclusion:** **Content affinity can guide audits, but it cannot prove that a page caused completion or that a group preferred it.** Prioritize audits of high-volume entry pages, Spanish equivalents, result pages, provider/trial pages, and pages with unclear next actions.

### Issue 7 — Assessment result differences must not be interpreted as racial disparities in cognition

The observed assessment rows cannot support a conclusion that one race has better or worse memory, AD8 concern, or SBC risk because:

- AD8 is informant/caregiver-reported, while MIS and SBC are self-administered.
- SBC scored respondents are only 4.8% of entrants.
- Race rows are incomplete relative to flow KPIs in the captured tables.
- Age, education, language, device, diagnosis status, caregiving role, and selection into the flow are not adjusted.
- These instruments and product result categories are screening/routing tools, not diagnoses.

**Conclusion:** Use scores to improve flow completion and explain results responsibly, not to make racial or clinical claims from these aggregate captures.

## 4. What external research does — and does not — explain

The research supports a **multi-mechanism model**:

```text
Structural access + language + digital literacy + trust/stigma
                 ↓
   probability of finding and trusting BrainGuide
                 ↓
       start / step progression / completion
                 ↓
      observed demographic respondent profile
```

The model is useful because it prevents a common mistake: assuming that a White-heavy respondent table means Black and Hispanic people do not need brain-health information. Existing dementia literature indicates the opposite possibility — higher burden alongside lower awareness or later diagnosis — but BrainGuide's data cannot determine which mechanism dominates.

The research does not establish that:

- a specific BrainGuide page caused a group to drop off;
- Black or Hispanic users distrust this product;
- Spanish users cannot use the current site;
- a demographic group has a particular screening result distribution;
- a targeted campaign will improve equitable reach without product and trust work;
- national population proportions are the correct benchmark for this product.

## 5. Recommendations, prioritized from UX/UI and copy outward

### P0 — Make the journey safe, understandable, and finishable

#### 1. Rewrite the entry promise
Use plain, non-diagnostic, choice-preserving copy above every assessment entry:

> **Learn more about memory and brain health.** This short activity is for information and discussion — it does not diagnose dementia. You can stop at any time, skip questions, and choose what resources to view next.

Add a visible privacy explanation:

> **Your answers are used to show your results and improve this experience. We will not contact you unless you explicitly choose to hear from us.**

The exact data-retention and sharing statement must match the approved privacy policy. Do not promise anonymity or deletion unless technically true.

#### 2. Make language selection first-class
- Put English / Español at the top of the first page, not only in a footer or after a user begins.
- Persist the language through the entire questionnaire, result page, PDF, resource links, and outbound handoff.
- Preserve progress when switching languages where the content and scoring contract allows it.
- Ensure the Spanish path is not a partial translation of an English-first flow.
- Have native Spanish speakers from relevant communities review wording, tone, examples, audio, and action labels; do not rely only on literal machine translation.
- Keep Spanish resource destinations language-concordant where available.

#### 3. Reduce mobile and tablet friction
- Use large tap targets, short screens, high contrast, and persistent progress.
- Test on low-end Android devices, iPhones, tablets, Safari, Chrome, and low-bandwidth connections.
- Avoid long paragraphs before the first action.
- Make keyboard focus, screen readers, captions/transcripts, and zoom behavior work throughout.
- Offer a non-speech alternative when SBC recording cannot work.

#### 4. Repair SBC as a product funnel before interpreting SBC risk
Add explicit states and recovery paths:

- microphone permission not granted;
- microphone unavailable;
- recording started;
- recording too short;
- recording uploaded;
- scoring in progress;
- scoring failed;
- user abandoned;
- user completed without score.

Provide a microphone test, a clear retry button, a text or alternate assessment path, and an explanation that no score is not a personal failure. The current 4.8% scored-result rate makes this a major operational opportunity.

### P1 — Build culturally responsive content and trusted access points

#### 5. Co-design with Black and Hispanic/Latino users
Recruit compensated participants who include:

- Black/African American older adults and caregivers;
- Hispanic/Latino older adults and caregivers;
- Spanish-preferred and bilingual users;
- people with different education and digital-literacy levels;
- users on mobile-only connections;
- community health workers, faith/community organizations, and local service providers.

Ask them to test language, privacy, imagery, result labels, navigation, caregiver/self pathways, and perceived consequences of completing the tool. Do not ask participants to speak for an entire racial or ethnic group.

#### 6. Use trusted messengers, not only paid digital acquisition
Develop landing pages and referral kits for community-based organizations, Federally Qualified Health Centers, libraries, senior centers, faith organizations, caregiver groups, and bilingual community health workers. Give messengers:

- a two-minute explanation of what BrainGuide does and does not do;
- privacy and data-use answers;
- a Spanish and English handout;
- a QR code plus short URL;
- a non-digital alternative or assisted-completion option;
- a way to report language or usability problems.

Chau et al. support CBOs as trusted messengers, while dementia-specific CHW literature supports community-level education as a promising bridge. Treat this as an evaluated partnership strategy, not an assumption that any organization is trusted by every subgroup.

#### 7. Expand content beyond memory loss
The Latino dementia-knowledge review found that memory loss is recognized more consistently than other cognitive signs and protective factors. Add plain-language, culturally reviewed content on:

- changes in planning, judgment, language, or daily tasks;
- what is and is not typical aging;
- how to start a conversation with a clinician or family member;
- caregiver support;
- prevention and brain-health actions;
- what to do after a concerning result;
- how to find local and language-concordant help.

Avoid fatalistic language and avoid implying that a result predicts a person's future.

### P1 — Instrument the equity funnel correctly

#### 8. Define a shared funnel contract
For every demographic analysis, publish the same date range and denominators:

1. eligible site visitors or sessions;
2. questionnaire starts;
3. each major step reached;
4. completed assessment or information path;
5. scored result;
6. result-page action;
7. provider/trial/resource click.

Do not use a race distribution among completers as a substitute for completion rates by race.

#### 9. Add event-level failure reasons
At minimum, instrument:

- `language_selected`;
- `questionnaire_start`;
- `questionnaire_step_view`;
- `questionnaire_continue`;
- `questionnaire_back`;
- `questionnaire_validation_error`;
- `questionnaire_abandon`;
- `language_switch`;
- `microphone_permission_prompted`;
- `microphone_permission_denied`;
- `recording_started`;
- `recording_failed`;
- `recording_uploaded`;
- `score_returned`;
- `score_failed`;
- `result_action`;
- `provider_click`;
- `trial_click`.

Every event needs a stable definition, source, version, date coverage, grain, and approved denominator. The event inventory currently contains repeated and ambiguous event names; a formal metric registry is required before AI-generated equity conclusions.

#### 10. Capture voluntary demographic context earlier — carefully
The current post-score-only demographic design creates selection bias. Consider an optional, separate “help us improve access” module near the beginning or after a low-friction information path. It should:

- be optional and skippable;
- explain why the data is collected;
- allow multiple race/ethnicity identities under the approved data standard;
- keep Hispanic/Latino ethnicity analytically distinct from race where appropriate;
- include Prefer not to answer and Unknown/Not collected as separate states;
- never gate results, care resources, or participation;
- be subject to privacy review, retention limits, small-cell suppression, and access controls.

Do not silently infer race from name, geography, language, or imagery. GA4 geography and language are behavioral context, not substitutes for self-reported race/ethnicity.

#### 11. Establish a privacy-safe linkage protocol
If questionnaire and GA4 data are joined, document:

- de-identified session or transaction key;
- timestamp and timezone rules;
- one-to-one, one-to-many, and unmatched behavior;
- linkage coverage by date, site version, language, device, and flow;
- whether the join covers pre-questionnaire, questionnaire, post-result, and return sessions;
- consent and purpose limitation;
- prohibition on joining email/contact records to GA4 without approved governance.

Report linkage coverage before reporting demographic funnel differences. Never send raw identifiers or sparse demographic cells to an LLM.

### P2 — Outreach and acquisition after the product baseline is fixed

#### 12. Run targeted, measurable outreach
Use community-specific, bilingual campaigns only after entry and completion paths are usable. Tag each campaign with:

- partner/source;
- audience intent;
- language;
- geography;
- creative version;
- landing page;
- campaign target: education, questionnaire, provider, or trial.

Measure starts, step progression, completions, and meaningful actions — not only clicks. Compare the campaign cohort with a pre-specified benchmark and a comparable non-campaign period.

#### 13. Offer assisted and non-digital pathways
Digital equity cannot be solved by a better interface alone. Provide printable materials, phone/community navigation, assisted completion, audio support, and clear referral pathways for people without reliable connectivity, compatible devices, or comfort using online tools.

## 6. Measurement and evaluation plan

### Phase A — Baseline and data repair

- Freeze a date range after confirming source freshness.
- Create the race/ethnicity dictionary and preserve raw response categories.
- Reconcile Results Overview race rows to the race-answered denominator.
- Separate missing, skipped, Prefer not to answer, and not collected.
- Add a start-level language and device funnel.
- Add SBC failure-state events.
- Produce a linkage coverage report.
- Suppress cells below the repository minimum of 10 and apply complementary suppression where needed.

### Phase B — UX and content evaluation

Use a mixed-method evaluation:

- moderated usability sessions in English and Spanish;
- cognitive interviews for privacy, stigma, and result wording;
- accessibility audit with older adults and assistive technology users;
- performance testing on low-end/mobile devices;
- task completion by pathway, not only satisfaction;
- community partner feedback before launch.

### Phase C — Controlled product tests

Prioritize tests that do not withhold essential health information:

1. privacy/non-diagnostic explanation vs current entry copy;
2. first-class language choice vs current language discovery;
3. shorter mobile step layout;
4. SBC microphone test and fallback path;
5. Spanish resource navigation and language persistence;
6. trusted-messenger landing pages vs generic landing page.

Primary metrics should be completion and successful recovery, with guardrails for error rate, time to complete, result comprehension, and downstream resource clicks. Report absolute rates and percentage-point differences, confidence intervals where sample sizes support them, and dates/denominators for every comparison.

### Recommended reporting table

| Question | Required numerator | Required denominator | Status now |
|---|---|---|---|
| Are Black users reached? | Black visitors or sessions | All eligible visitors/sessions | Not assessable; race is not available in GA4 reach |
| Are Black users completing? | Black completions | Black starts | Not assessable; start-level linkage missing |
| Are Hispanic/Latino users completing? | Hispanic/Latino completions | Hispanic/Latino starts | Not assessable; denominator and linkage missing |
| Is Spanish access functional? | Spanish successful step/completion/action | Spanish starts or visits for the same flow | Partial descriptive evidence only |
| Is SBC equitable? | Scored result or successful recovery by group | SBC entrants by group | Not assessable until early demographic context and failure events exist |
| Does content lead to action? | Defined action event | Same-group eligible page/session cohort | Partial; attribution is descriptive and not causal |

## 7. Guardrails against misleading conclusions

1. Do not compare respondent race percentages to national Census percentages without agreeing on geography, age, eligibility, time window, and race/ethnicity coding.
2. Do not call GA4 geography “race.”
3. Do not equate Spanish language with Hispanic/Latino identity.
4. Do not merge Black, Hispanic/Latino, Mixed, Other, Unknown, and Prefer not to answer into a convenient “non-White” category.
5. Do not treat missing race as random.
6. Do not calculate completion rates from different date fields or source systems without a crosswalk.
7. Do not interpret AD8/MIS/SBC product categories as diagnoses.
8. Do not interpret a lower click rate as lower need or lower value.
9. Do not publish sparse intersectional cuts, even when the aggregate group is large enough.
10. Do not send raw questionnaire rows, identifiers, email addresses, or sparse demographic combinations to an LLM.

## 8. Alignment with the client requirements and checklist

The complete auditable matrix is maintained in [`DEMOGRAPHIC_EQUITY_COVERAGE.md`](./DEMOGRAPHIC_EQUITY_COVERAGE.md) and validated by [`scripts/validate_demographic_equity_coverage.py`](../../scripts/validate_demographic_equity_coverage.py). The summary below highlights the priority questions; the matrix covers all 25 client questions and every Gate 0, Gate 2, Gate 3, and Trust Layer requirement.

This analysis directly addresses the requested and listed questions:

- **Question 2 — priority-population reach:** observed composition is available; valid benchmark comparison remains pending.
- **Question 7 — Black users:** observed respondent count is 2,433 in Results Overview displayed race rows; acquisition, conversion, and tailored-resource support are not yet measurable by Black identity with a shared denominator.
- **Question 8 — Hispanic/Latino users:** observed respondent count is 2,675 in displayed race rows; language, geography, and funnel linkage are incomplete.
- **Question 9 — Spanish access:** Spanish pageviews and resource-path counts are available descriptively; questionnaire start/finish and stable comparative rates remain limited.
- **Gate 2.2:** linkage coverage report is still required.
- **Gate 2.3:** equity reach requires a defined benchmark and all-user/completer denominators.
- **Gate 2.4:** funnel equity requires event-level race/language/device linkage.
- **Gate 2.5:** pathway equity requires validated attribution and campaign mapping.
- **Gate 2.6:** language access needs Spanish starts, finishes, and resource clicks under one consistent cohort definition.
- **Gate 2.7–2.8:** small-cell, denominator, complementary-suppression, and difference-attack protections are mandatory.

## 9. Final conclusion by priority population

### Black/African American populations

**Conclusion:** Black respondents are clearly a small minority of the displayed questionnaire race rows (**2,433; 4.5% of displayed rows**), and the White-to-Black displayed-row ratio is approximately **17.5:1**. This is an important observed reach imbalance, especially in light of external evidence of lower dementia awareness and delayed diagnosis among Black older adults. It is not yet possible to say how much of the gap occurs before the site, at questionnaire start, during completion, or through demographic missingness. The immediate response should be trusted-messenger co-design, non-stigmatizing and privacy-forward copy, mobile/accessibility improvements, and a valid start-to-completion denominator.

### Hispanic/Latino populations

**Conclusion:** Hispanic/Latino respondents are also a small minority of displayed questionnaire race rows (**2,675; 4.9% of displayed rows**), with a White-to-Hispanic/Latino displayed-row ratio of approximately **15.9:1**. Spanish content is used but represents only **5.5%** of overall pageviews, and provider/trial pathways show lower observed Spanish volume and visit-based click rates. External research supports language, digital-health literacy, awareness, and online recruitment barriers as plausible mechanisms. The product should treat Spanish as a complete, culturally reviewed experience with trusted community distribution — not as a secondary translation layer.

### White/Caucasian populations

**Conclusion:** White respondents make up the large majority of the displayed race rows. This indicates that the current evidence base is best suited to understanding the experience of the population already completing BrainGuide, not to assuming the needs or performance of populations who are absent earlier in the funnel. White-heavy data can also make overall averages look healthy while concealing barriers for smaller groups. Report overall metrics alongside subgroup coverage and never use the majority group's performance as a universal baseline without testing.

### Spanish-preferred users

**Conclusion:** Spanish usage is real but not yet demonstrably equivalent to English usage. The key risk is not simply low translation volume; it is the possibility that language choice, literacy, trust, device constraints, and resource handoff all compound. Fix the language journey and measure it end-to-end before ranking Spanish performance.

## Sources and further reading

### Primary disparity and dementia sources

1. Lin, P.-J. et al. (2020). “Racial and Ethnic Differences in Knowledge about One’s Dementia Status.” *Journal of the American Geriatrics Society*. [PMC7552114](https://pmc.ncbi.nlm.nih.gov/articles/PMC7552114/)
2. Lin, P.-J. et al. (2021). “Dementia Diagnosis Disparities by Race and Ethnicity.” *Medical Care*. [PMC8263486](https://pmc.ncbi.nlm.nih.gov/articles/PMC8263486/)
3. Light, S. W. et al. (2024). “Perceptions, beliefs, attitudes, and knowledge of US Latino adults pertaining to dementia and brain health: A Systematic Review.” *Aging & Mental Health*. [PMC10983845](https://pmc.ncbi.nlm.nih.gov/articles/PMC10983845/)
4. Gutiérrez, Á. et al. (2022). “The Digital Divide Exacerbates Disparities in Latinx Recruitment for Alzheimer’s Disease and Related Dementias Online Education During COVID-19.” [PMC8891594](https://pmc.ncbi.nlm.nih.gov/articles/PMC8891594/)
5. Siette, J. et al. (2023). “Breaking the barriers: overcoming dementia-related stigma in minority communities.” *Frontiers in Psychiatry*. [PMC10765564](https://pmc.ncbi.nlm.nih.gov/articles/PMC10765564/)

### Digital equity, language, and trusted-messenger sources

6. Philpot, L. M. et al. (2024). “Digital health literacy and use of patient portals among Spanish-preferred patients in the United States.” *Frontiers in Public Health*. [PMC11666482](https://pmc.ncbi.nlm.nih.gov/articles/PMC11666482/)
7. Wilson, S. et al. (2024). “Recommendations to advance digital health equity: a systematic review of qualitative studies.” *npj Digital Medicine*. [PMC11217442](https://pmc.ncbi.nlm.nih.gov/articles/PMC11217442/)
8. Chau, M. M. et al. (2023). “Community-Based Organizations as Trusted Messengers in Health.” *Hastings Center Report*. [PMC10939007](https://pmc.ncbi.nlm.nih.gov/articles/PMC10939007/)
9. Portacolone, E. et al. (2020). “Earning the Trust of African American Communities to Increase Representation in Dementia Research.” *Ethnicity & Disease*. [PMC7683027](https://pmc.ncbi.nlm.nih.gov/articles/PMC7683027/)
10. Epps, F. et al. (2021). “Perceptions and Attitudes Toward Dementia in Predominantly African American Congregants.” *Journal of Applied Gerontology*. [PMC8302664](https://pmc.ncbi.nlm.nih.gov/articles/PMC8302664/)
11. Stites, S. D. et al. (2024). “A Survey Study of Alzheimer’s Stigma among Black Adults.” *Ethnicity & Health*. [PMC11560502](https://pmc.ncbi.nlm.nih.gov/articles/PMC11560502/)
12. U.S. Census Bureau. Population and demographic benchmark data. [Census data](https://www.census.gov/data.html)

The external sources provide context and intervention evidence. They do not replace a BrainGuide-specific funnel study, usability study, or community-partner evaluation.
