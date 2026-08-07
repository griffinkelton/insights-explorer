This report executes the three tasks defined in the v2 deep-research prompt, using the actual `braintree-evidence/` package on `main` (confirmed via repository tree: `CONSOLIDATED.json/md`, `analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md/json`, `analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md`, and `reports/md/artifacts/*.md`) plus new external sources. All claims are labeled `observed`, `associated`, `hypothesis`, or `not assessable` per the protocol's existing vocabulary.[^1]

## §0 reconciliation recap

The five SOW-level questions map onto the 25-question framework with one genuine gap: **concern-level segmentation of downstream action** (SOW Q5) does not exist as a cross-tab anywhere in the current coverage matrix, which reports AD8/MIS/SBC score distributions and resource-click counts separately but never joined. Task 3 below closes that gap using data already captured in `result-pages.md`.[^1]

## Task 1 — Phase 1 benchmark construction

### BrainGuide's own stated eligibility

BrainGuide's public FAQ states the tool "is designed for people of all ages and from all communities," and its Alzheimer's resource page frames the core audience around the projection that "12.7 million Americans 65 and older will have Alzheimer's by 2050". There is no published explicit age floor. Per the protocol default, this benchmark uses **two sensitivity bands: no age restriction (all ages) and 65+** — since BrainGuide markets to "all ages" but its core clinical framing centers on older adults and their caregivers.[^2][^3]

### Benchmark table (ACS-derived, 2024 vintage, all-ages)

Because BrainGuide states no explicit age floor, the primary benchmark below uses **all-ages ACS 2024 population shares** by race/ethnicity for the top-5 states by BrainGuide reach, sourced from Census Bureau ACS 1-year estimates as aggregated by KFF (citing Census ACS Table B03002-equivalent race/ethnicity distributions):[^4]

| State | White | Black | Hispanic | Asian | AIAN | NHPI | Multiracial | Source |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| California | 32.6% | 5.0% | 40.9% | 15.9% | 0.3% | 0.3% | 5.1% | ACS 2024, via KFF [^4] |
| Florida | 49.0% | 14.1% | 28.9% | 3.0% | 0.1% | 0.1% | 4.7% | ACS 2024, via KFF [^4] |
| Texas | 37.8% | 11.7% | 40.5% | 6.1% | 0.2% | 0.1% | 3.7% | ACS 2024, via KFF [^4] |
| New York | 52.1% | 13.1% | 20.3% | 9.4% | 0.2% | N/A | 4.9% | ACS 2024, via KFF [^4] |
| Pennsylvania | 72.1% | 9.9% | 9.4% | 4.2% | 0.1% | N/A | 4.3% | ACS 2024, via KFF [^4] |
| National (all 81 reached states/territories, unweighted proxy) | 56.4% | 11.6% | 20.1% | 6.2% | 0.5% | 0.2% | 5.1% | ACS 2024, US total [^4] |

**Population-weighted aggregate across the top-5 states** (weighted by each state's 2024 ACS total population — CA 38.60M, FL 22.84M, TX 30.56M, NY 19.34M, PA 12.64M; total 123.98M):[^4]

- White: ~44.4%
- Black: ~9.9%
- Hispanic/Latino: ~30.9%
- Asian: ~8.7%
- AIAN: ~0.2%
- NHPI: ~0.2%
- Multiracial: ~4.7%

This is a **five-state weighted proxy, not a true 81-state weighted aggregate** — BrainGuide's reach spans all 81 US states/territories, and states outside the top 5 (which together hold the bulk of the remaining ~620,861−(CA+FL+TX+NY+PA users) reach) are not included in this weighting. Building the full 81-state weighted benchmark would require the actual per-state GA4 user counts, which are not present in `geographic-traffic.md`'s captured excerpt at the needed grain — only the top-5 ranking is stated, not the full distribution. This is flagged as a **data-completeness gap**, not filled by assumption.[^1]

### Unit mismatch — stated prominently

GA4 reach is **session/user-based** (device-level, deduplicated by GA4's identity resolution, not by person). ACS estimates are **person-based** counts of state residents. Additionally, the questionnaire's displayed race/ethnicity rows (`Results Overview.pdf` p.7, n=54,626) reflect only respondents who **reached and completed a scored result** — not all visitors, and not all questionnaire starters. A GA4 "user" traveling from Texas is not equivalent to a "Texas resident" in the ACS sense (tourists, out-of-state caregivers researching a parent, VPN traffic, and multi-device users all break the identity mapping). This mismatch means any ratio below must be read as a rough order-of-magnitude signal, not a precise representation statistic.[^1]

### Provisional representation ratio (labeled `associated`)

Using the national all-ages ACS shares as a first-pass reference point (since the exact 81-state weighted denominator is unavailable), and the displayed-row shares from `Results Overview.pdf` p.7 (Black 4.5%, Hispanic/Latino 4.9%):[^1]

| Group | Observed displayed-row share | ACS national benchmark share | Provisional ratio (observed ÷ benchmark) | Inference label |
|---|---:|---:|---:|---|
| Black/African American | 4.5% | 11.6% | **0.39** | `associated` |
| Hispanic/Latino | 4.9% | 20.1% | **0.24** | `associated` |

**This ratio is provisional and likely understates the true underrepresentation, for one specific reason**: the numerator is a *downstream completer* share (respondents who finished the questionnaire and reached a scored result), while the denominator is an *all-resident* share. Because demographic data only exists from "Received Score" downward, any race/ethnicity-differential drop-off earlier in the funnel — before demographics are even captured — is invisible to this ratio and could push the true all-visitor representation closer to, or further from, parity in either direction. The ratio is also sensitive to the five-state proxy issue above. **Do not present this ratio as a precise disparity magnitude in any client-facing materials** — it is directional evidence supporting the already-`partial_now` status of the reach-equity questions, not a `supported_now` upgrade on its own.[^1]

## Task 2 — Mechanism literature update (5 new sources)

### 1. Speech-based cognitive assessment equity

**Koenecke et al. 2020, "Racial disparities in automated speech recognition," PNAS**. Tested five commercial ASR systems (Amazon, Apple, Google, IBM, Microsoft) against a large corpus of sociolinguistic interviews; found average word error rate of 35% for Black speakers versus 19% for White speakers, attributing the gap to acoustic-model training-data insufficiency for African American Vernacular English phonology rather than vocabulary. **Modifies Phase 3**: this is direct mechanistic evidence — not adjacent-disparity framing — that the SBC flow's 4.8% completion rate and any accuracy issues within completed SBC assessments could carry a race-differential technical failure mode distinct from the trust/stigma mechanisms already cited (Portacolone, Stites). Add as a new Phase 3 mechanism-table row specific to SBC, separate from the AD8/MIS trust-based rows.[^5]

**Porta-Mas et al. 2026, "Predictors associated with the rate of completion of a remote [cognitive] assessment"**. Found higher digital literacy significantly associated with higher response/completion rates in remote cognitive assessments generally. **Modifies Phase 3**: supports treating SBC's completion crisis as partially digital-literacy-driven rather than purely a technical/UX bug, reinforcing the existing device-friction finding (Tablet 71% loss at W-S1) with a literature-backed mechanism.[^6]

### 2. Trusted-messenger effect sizes

No study located in this pass reports a directly quantified before/after completion-rate lift specifically for a *digital cognitive-screening tool* referred via CBO/faith-based/community-health-worker channel versus paid digital advertising. This sub-question should be labeled **`not assessable`** from current public literature — the existing citations (Portacolone, Epps, Chau) establish the mechanism and plausibility but no effect-size number exists in the sources retrieved. **This is itself a finding**: recommend Phase 3 include a note that trusted-messenger effect-size evidence must come from the engagement's own controlled Phase 5 outreach pilot (already planned) rather than from external literature, since none with the needed specificity exists yet.

### 3. Informant/caregiver-reported instrument abandonment

**Win et al. 2025 (Tan Tock Seng Hospital), "Utility of Self-Rated vs. Informant-Rated AD8"**. Found AD8-Self has a distinct factor structure, lower reliability, and inferior diagnostic performance versus AD8-Informant — establishing that the two administration modes are functionally different instruments, not interchangeable. **Modifies Phase 3**: this doesn't directly explain the 98% `W-B-AD-9` abandonment mechanism (no study located specifically measures caregiver emotional/time burden mid-questionnaire), but it is important context: BrainGuide cannot simply reroute AD8 abandoners to a self-rated substitute without acknowledging a validity trade-off. Label the caregiver-burden abandonment mechanism itself **`hypothesis`** pending qualitative research (already planned in Phase 3's community-research track) — no published study was found quantifying emotional or time-burden-driven mid-survey abandonment specific to informant-based dementia screening.[^7]

### 4. Spanish-language functional equivalence methodology

**Eremenco et al. 2005, "A Comprehensive Method for the Translation and Cross-Cultural Adaptation of Health Status Questionnaires" (FACIT methodology)**. Establishes the decentered double-translation/back-translation/cognitive-debriefing methodology aimed specifically at equivalence of *meaning and measurement* between language versions, not just translation accuracy — still the field-standard reference for functional-equivalence testing. **Modifies Phase 3**: gives Phase 3's planned native-speaker review a concrete, citable methodology (decentered translation + cognitive debriefing interviews with target-population Spanish speakers) rather than an ad hoc review.[^8]

**Carrillo-León et al. 2026, "Spanish Version of the mHealth App Usability Questionnaire"**  and **Van Cleave et al. 2025, "Using content validity index methodology for cross-cultural adaptation"**. Both are recent (2025–2026) applied case studies of validating a Spanish digital-health instrument using content-validity-index scoring and usability-equivalence testing — directly relevant precedents for validating BrainGuide's Spanish flow, not just its static content pages. **Modifies Phase 3**: recommend Phase 3 adopt a CVI-based validation step (per Van Cleave) specifically for the Spanish questionnaire flow, in addition to translation review of static content.[^9][^10]

## Task 3 — Concern-level cross-tab (SOW Q5)

### Data available

`result-pages.md` already reports resource-click actions **segmented by Brain Health label (Good/Moderate/Poor)** and by Result Page persona (Self/Someone Else × Diagnosed/Not Diagnosed × Good/Poor), for the most recent 90-day window (May 7–Aug 4, 2026; n=3,286 total actions across 12 result pages). This is joinable at the needed grain — Task 3 step 4's fallback is **not triggered**; the join is possible using already-captured data.[^1]

### Click-through rate to "Locate a Healthcare Provider" by brain-health label (90-day window, English pages only — Spanish result-page rows are not broken out in the captured table)

| Brain-health label | Persona rows summed | "Locate a Healthcare Provider" clicks | Total actions on those rows | Rate | Wilson 95% CI | Label |
|---|---|---:|---:|---:|---|---|
| Poor | Self·NotDiag·Poor, Self·Diag·Poor, SomeoneElse·NotDiag·Poor, SomeoneElse·Diag·Poor | 34+13+18+11 = 76 | 277+91+31+103+54+10+60+56+11+23+9 = 725 | 10.5% | 8.4%–13.0% | `observed` |
| Good | Self·NotDiag·Good, Self·Diag·Good | 53+20 = 73 | 1,299+528+89+233+125+16 = 2,290 | 3.2% | 2.5%–4.0% | `observed` |

**Rate ratio (Poor vs. Good click-through to provider resource): 10.5% ÷ 3.2% ≈ 3.3×.** Both cell denominators clear the n≥10 release floor and the ≥50 rate-stability floor. This is a real, computable finding not previously surfaced in the coverage matrix.[^1]

### Critical limitation — this does not answer SOW Q5 as literally worded

This is a **click-through rate on a result page**, not a measure of "proportion of users who go on to seek clinical care." Per the protocol's existing inference-label discipline, clicking "Locate a Healthcare Provider" is `observed` handoff intent — it is **`not assessable`** whether the user actually booked, attended, or completed an appointment, because BrainGuide's GA4 instrumentation stops at outbound click and does not capture provider-side confirmation. The Find a Provider and Clinical Trials reports independently confirm this same handoff-only visibility: e.g., total Find a Provider outbound clicks are 1,232 against 16,168 page visits (7.6% CTR), with no downstream appointment data anywhere in the evidence package.[^1]

### Proposed new coverage-matrix row

```json
{
  "id": "Q26",
  "sow_mapping": "SOW Q5",
  "question": "What proportion of moderate/high-concern users click through to a provider or clinical-trial resource, and how does this compare to low-concern users?",
  "status": "partial_now",
  "evidence": [
    "reports/md/artifacts/result-pages.md — Brain Health x Action table, May-Aug 2026",
    "reports/pdf/Result Pages.pdf p.1-2"
  ],
  "current_answer": "Poor-labeled result-page visitors click 'Locate a Healthcare Provider' at ~10.5% (76/725) vs. 3.2% (73/2290) for Good-labeled visitors, a ~3.3x rate ratio, English pages only, 90-day window.",
  "limitations": [
    "Click is observed handoff intent, not confirmed care-seeking (no appointment/enrollment data)",
    "Spanish-language result-page action rows not broken out at this grain in current capture",
    "SBC Low/Medium/High Risk mapped to Good/Moderate/Poor per report methodology note, not independently verified",
    "90-day window only; no longitudinal trend"
  ],
  "unlock_criteria": "Provider-side or clinical-trial-side confirmation data (appointment booked/attended, trial enrollment) linked back to originating BrainGuide session or persona label; without this, status cannot advance past partial_now regardless of click-rate precision."
}
```

## Independent validation of `reports/` PDFs and MDs

Cross-checked `result-pages.md`, `clinical-trials.md`, and `find-a-provider.md` against the corresponding PDF page structure referenced in their headers. `result-pages.md` explicitly notes its own table is "Page 1 of 2" and that a "By Action & Device" section exists on the live dashboard but "not rendered in extracted content (likely chart-based)"  — meaning the full result-pages dataset (page 2, plus device cut) is **not fully captured** in the current markdown artifact. This is a real gap worth closing before finalizing any client-facing concern-level table: page 2 of the Result Page action table could contain additional Moderate-labeled or SBC-specific rows not reflected in the Task 3 cross-tab above, which currently only reflects assessment-family (AD8/MIS) rows with visible Good/Poor labels — no Moderate-labeled or `sbc` score-family rows appear in the captured excerpt at all, despite the filter panel showing "Brain Health 4 Selected" and "Score Family (none), assessment, sbc" as active filters. Recommend re-pulling page 2 of Result Pages before treating the Task 3 table as complete.[^1]

---

## References

1. [paste.txt](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/131801701/472e344e-5a66-4157-9ee2-f6716c20656f/paste.txt?AWSAccessKeyId=ASIA2F3EMEYEZ3XYCOK6&Signature=fUHElMSVcvbG2QP%2Bo5lOYnBEC%2FU%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEIz%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJIMEYCIQCbrMxBrxul2BqoovWyi6A4se%2Bj50ZMNRcf%2BurDfSpaKwIhALI55jAY23XA%2BVCXpPlfbrNApXhUWVWjrfQSToJCyhgEKvMECFUQARoMNjk5NzUzMzA5NzA1IgxaJb6tALIfdp%2B68gUq0ASY9AZgV%2BzQsMzyL4qeVjBUHC1vMS%2F5xDYjTS3n%2F27EXJn8gTl0Y57AcP%2BqyWLs93g9%2B2Dwi0GH6EUMTwOuQUTY2%2FvstYbS0avDyBZi%2B6CdLp9IsqxA%2FN4sBmBdXkdtQq5KtGDJ5NPPDwWcr09rP4wi2N0nuU2Jltd2uBStT3fXSrRvmb3USyxIckQUtROySYCIHz6fcRTiFEmdisVHog%2BjuKWg1x4zNttmQaZZnro3HzfhlL40dOCQPf7diDcvqFRlf7ehM%2FZcgD9hgqMWtMaXcMwj6eA3p5coQQV%2B9xpXeNqFUoz15uPgZ2Moz4x22dVhHz7Slw%2FB2H0XFrg436hICgtOg6HntRnPopxXejGGZul9q%2FlT6qwg5iwEAUR%2B6gYVoLkr3DAf0pqd6ngcsBwhtmN1oKs3P6OeNluK22cnCxvjOKA91R7%2FsANygWqVPnp6%2BEl7S%2BcqoBPnYWut6p0vs2NwFoluwCFRReatORlhj7aZW6qHlNPbT2meW2iCvyGCpekQicVazU6EWVbmjlpoy%2FyHWgW%2BZ0r2YALc98COqIWNOoEISqVnW1TKQnZ%2BcI4wI%2FrdmsIDj6fjtPmLkrePWQP05Mxk26RwSD9m80cHebo4oMpVm3i0fhJMvbtdlniYr03Qq6qCLaj489MNE%2FRKhrHcXZGu3A1iMYPSsHNOwH9cIJ0eLTfCTpNu%2BhFyllUeb1k0pAR%2FVlE6bNAoPDMkp9ZKoEfi57TNro5ykNT8PAXIL7MobdYJrj%2FzY%2FRRVXlItFZ8GgzYotbz5w%2B63Z%2FRMPSJ19MGOpcBSprSvjIP0fU7Dw5ny%2BcI%2B%2Bx5LNXwtvbZd355a8KltvILhWGpLxUUUsJniRNZpnT%2F30d8UltC3dVvReXzpk3USb86g%2Bko57uV%2BNe3lJzxZqI1iEhHIWCxqkBWyFLJXUHo2yuSMWqYjqh6vsy%2B%2Ft%2Bfci1UKhdwZChgkEbTeCozxgMI7fjw3BaX2GHAnNYLwjllwOOMSmTxoQ%3D%3D&Expires=1786106567)

2. [BrainGuide: Memory Questionnaire and Brain Health Resources](https://mybrainguide.org/) - Are you concerned about brain health, early signs of Alzheimer's, or dementia? Take the memory quest...

3. [Resources to understand Alzheimer's - BrainGuide](https://mybrainguide.org/about-alzheimers-brain-guide/) - 12.7 million Americans 65 and older will have Alzheimer's by 2050. BrainGuide has developed a memory...

4. [Population Distribution by Race/Ethnicity](https://www.kff.org/state-health-policy-data/state-indicator/distribution-by-raceethnicity/) - the Census Bureau's American Community Survey (ACS) Persons of Hispanic origin may be of any race; v...

5. [Racial disparities in automated speech recognition](https://www.pnas.org/doi/10.1073/pnas.1915768117) - by A Koenecke · 2020 · Cited by 1254 — We found that all five ASR systems exhibited substantial raci...

6. [Predictors associated with the rate of completion of a remote ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12790586/) - by C Porta‐Mas · 2026 — Higher digital literacy was significantly associated with higher response ra...

7. [Utility of Self-Rated vs. Informant-Rated Ascertain Dementia-8 ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC13054566/) - The Ascertain Dementia 8-item Questionnaire (AD8) is a validated informant-based interview for early...

8. [A Comprehensive Method for the Translation and Cross ...](https://journals.sagepub.com/doi/10.1177/0163278705275342) - by SL Eremenco · 2005 · Cited by 973 — The FACIT translation methodology aims to establish equivalen...

9. [Using content validity index methodology for cross-cultural ...](https://www.frontiersin.org/journals/health-services/articles/10.3389/frhs.2025.1582127/full) - by JH Van Cleave · 2025 · Cited by 5 — Further, this method evaluates the cultural relevance and tra...

10. [Spanish Version of the mHealth App Usability Questionnaire ...](https://mhealth.jmir.org/2026/1/e64787) - by AL Carrillo-León · 2026 — The objective of this study was to translate and validate the English v...
