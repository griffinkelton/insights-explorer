# Scoring Reference

Source: https://dashboard.dev2.mybrainguide.org/questionnaire/scoring/

This page defines how BrainGuide questionnaire scores are calculated, how result pages map to user personas, and what those results indicate about brain health. Use this as the key for interpreting the Questionnaire Responses dashboard.

## Web Personas

### Persona Naming

Personas are identified by three routing axes — Who (Self vs. Someone Else), Diagnosed, and Indicating Brain Health — rather than the legacy first-name labels. Every dashboard now shows the descriptive label; the slug is the compact key used in data columns and filters.

| Persona (label) | Slug | Who | Diagnosed | Indicating Brain Health | Legacy Name |
|---|---|---|---|---|---|
| Self · Not Diagnosed · Good | self-undx-good | Self | Not Diagnosed | Good | Julia |
| Self · Not Diagnosed · Poor | self-undx-poor | Self | Not Diagnosed | Poor | Ben |
| Self · Diagnosed · Good | self-dx-good | Self | Diagnosed | Good | Meredith |
| Self · Diagnosed · Poor | self-dx-poor | Self | Diagnosed | Poor | Carol |
| Someone Else · Not Diagnosed · Good | other-undx-good | Someone Else | Not Diagnosed | Good | Nicole |
| Someone Else · Not Diagnosed · Poor | other-undx-poor | Someone Else | Not Diagnosed | Poor | Anson |
| Someone Else · Diagnosed · Good | other-dx-good | Someone Else | Diagnosed | Good | Olivia |
| Someone Else · Diagnosed · Poor | other-dx-poor | Someone Else | Diagnosed | Poor | Farah |

The three SBC result pages route by risk level rather than diagnosis: `self-sbc-low` (Self · Low Risk), `self-sbc-med` (Self · Moderate Risk), `self-sbc-high` (Self · High Risk).

### Routing & Scoring Detail

| Persona (label) | Result URL | Summary | Concerned About Brain Health | AD8 Score Range |
|---|---|---|---|---|
| Self · Not Diagnosed · Good | /maintain-brain-health-1/ | Worried well — Actively protecting brain health | Yes / No / Not Sure | 5–7, 8, No Q |
| Self · Not Diagnosed · Poor | /address-memory-concerns-1/ | Experiencing memory problems | Yes / No / Not Sure | 0, 1–4, No Q |
| Self · Diagnosed · Good | /understand-next-steps-2/ | Actively learning how to live with Alzheimer's | Yes / Not Sure | 5–7, 8 |
| Self · Diagnosed · Poor | /understand-next-steps-1/ | Recently diagnosed with Alzheimer's | Yes / Not Sure | 0, 1–4, No Q |
| Someone Else · Not Diagnosed · Good | /guide-loved-ones-4/ | Worried well — Concerned about recently diagnosed mother | Yes / No / Not Sure | 0–1, No Q |
| Someone Else · Not Diagnosed · Poor | /guide-loved-ones-3/ | Emerging caregiver, starting from zero | Yes / No / Not Sure | 2–8, No Q |
| Someone Else · Diagnosed · Good | /guide-loved-ones-2/ | Concerned about her recently diagnosed mother | Yes / Not Sure | 0–1 |
| Someone Else · Diagnosed · Poor | /guide-loved-ones-1/ | Care partner for Alzheimer's patient | Yes / Not Sure | 2–8, No Q |

"No Q" means the respondent reached this result without completing a scored questionnaire (e.g. via SBC flow or by skipping scoring). Diagnosed respondents always answer "Yes / Not Sure" to concern — no diagnosed persona reaches a result page having answered "No."

## Questionnaire Scoring Systems

### AD8 — Alzheimer's Disease 8-Item Informant Interview

Lower score = less concern. Higher score = more concern. 8 yes/no questions about memory and function changes. Yes = 1 point, No/Not sure = 0 points. Score range: 0–8.

| Score | Interpretation |
|---|---|
| 0–1 | Good — unlikely significant cognitive impairment |
| 2–8 | Poor — possible cognitive impairment; follow-up recommended |

### MIS — Memory Impairment Screen

Higher score = better memory performance. MIS Score = (2 x Free Recall) + Cued Recall. Free Recall = words remembered without prompting (x2 weight); Cued Recall = words recalled after a category cue. Score range: 0–8.

| Score | Interpretation |
|---|---|
| 5–8 | Good — normal memory performance |
| 0–4 | Poor — possible memory impairment |

Raw fields: `numWordsFreeRecalled`, `numWordsCueRecalled`, `misWordList`.

### SBC — Speech Based Cognition

Higher score = lower risk. Continuous 0–1 value for respondents in the `sbc` flow type who don't complete a memory screen.

| Score | Risk Level | Result URL |
|---|---|---|
| > 0.5 | Low Risk | /navigate-next-steps-1/ |
| 0.2 – 0.5 | Medium Risk | /navigate-next-steps-2/ |
| < 0.2 | High Risk | /navigate-next-steps-3/ |

All SBC respondents in the navigate-next-steps-* result URLs are Self. Boundary scores (exactly 0.2 or 0.5) may route to either adjacent tier; tier is taken from the routed result page rather than recomputed from the score.

## Flow Types in the Data

| flow_type | Description | Has Demographics | Scoring |
|---|---|---|---|
| ad8 | Full AD8 memory concern screen | Yes | AD8 (0–8) |
| mis | Memory Impairment Screen | Yes | MIS formula |
| sbc | Speech Based Cognition assessment | Yes | SBC (0–1) |
| c | User clicked "Get Information" — no scored result | No | None |

The `c` flow represents users who clicked "Get Information" rather than completing a scored assessment. They receive a result page/persona routing but no calculated score, no demographics collected. They make up ~24% of completions and are excluded from score calculations by default.

## Result URL to Persona Quick Reference

| Result URL | Persona | Brain Health | Who |
|---|---|---|---|
| /maintain-brain-health-1/ | Julia | Good | Self |
| /address-memory-concerns-1/ | Ben | Poor | Self |
| /guide-loved-ones-3/ | Anson | Poor | Someone Else |
| /understand-next-steps-1/ | Carol | Poor | Self |
| /understand-next-steps-2/ | Meredith | Good | Self |
| /guide-loved-ones-1/ | Farah | Poor | Someone Else |
| /guide-loved-ones-4/ | Nicole | Good | Someone Else |
| /guide-loved-ones-2/ | Olivia | Good | Someone Else |
| /navigate-next-steps-1/ | (SBC Low Risk) | Good | Self |
| /navigate-next-steps-2/ | (SBC Medium Risk) | Moderate | Self |
| /navigate-next-steps-3/ | (SBC High Risk) | Poor | Self |
