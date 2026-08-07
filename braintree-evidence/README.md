# BrainGuide Evidence Package

> **Snapshot:** 2026-08-06 dashboard capture, with report-specific freshness dates through 2026-08-04
> **Package status:** provisional, descriptive, and audit-oriented

This directory is the evidence package for the BrainGuide analytics and demographic-equity work. It preserves the captured dashboard reports, provides a consolidated semantic data guide, and documents what the current evidence can—and cannot—support.

## Start here

1. **[Consolidated semantic guide](./CONSOLIDATED.md)** — explains what each report measures, its grain and denominator, why it exists, how to interpret it, and what an LLM must not infer. The machine-readable companion is [CONSOLIDATED.json](./CONSOLIDATED.json).
2. **[Demographic disparity analysis](./analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md)** — analyzes the observed White-heavy questionnaire composition, Black and Hispanic/Latino reach signals, Spanish-language access, possible mechanisms, external research, and recommendations beginning with UX/UI and copy.
3. **[Equity protocol](./analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md)** — the implementation contract for measurement, funnel repair, mechanism validation, controlled UX/UI intervention, and outreach/outcome evaluation.
4. **[Question and gate coverage matrix](./analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md)** — the auditable answer-status map for all 25 client questions and the implementation gates. The canonical machine-readable source is [DEMOGRAPHIC_EQUITY_COVERAGE.json](./analysis/DEMOGRAPHIC_EQUITY_COVERAGE.json).
5. **[Comprehensive supplemental Q1–Q5 report](./reports/md/COMPREHENSIVE_SUPPLEMENTAL_ANALYSIS_Q1-Q5.md)** — the latest cross-source synthesis answering reach/equity, action, pathways, awareness, and care-progression questions with external research and explicit evidence limits.
6. **[Captured source reports](./reports/)** — the original PDF captures and the [journey explorer synthesis](./reports/md/artifacts/journey-explorer.md).
7. **[Additional research archive](./additional/README.md)** — supplemental GA4 analysis, benchmark/funnel extracts, research prompts, presentation exports, and provenance conversations; mixed authority and confidential handling applies.

## What the client wants answered

The client’s central question is broader than “how many people used BrainGuide?” The requested analysis asks:

- **Reach:** Who encounters BrainGuide, through which channels, devices, languages, and geographies?
- **Pathway:** Who starts and completes each questionnaire, where do people drop off, and do users find the right route for themselves or someone else?
- **Support and action:** Do tailored results, provider resources, clinical-trial resources, and other content lead to meaningful next-step activity?
- **Equity:** Are women, Black/African American users, Hispanic/Latino users, Spanish-language users, older adults, caregivers, and other agreed priority groups reached and supported equitably?
- **Learning:** Did the March 2026 relaunch, UX/UI changes, copy, language access, or outreach improve completion and useful action without widening gaps?
- **Outcomes:** Does use relate to awareness, confidence, care-seeking, or research action when approved downstream data exists?

The complete source requirement is [braintree-reqs.md](../braintree-reqs.md), and the implementation checklist is [BRAINTREE_CHECKLIST.md](../BRAINTREE_CHECKLIST.md). The equity matrix maps each of the 25 questions to its current evidence, limitations, and unlock conditions.

## Evidence boundaries

The current package supports a **reproducible descriptive assessment**, not a population-representativeness or causal evaluation. In particular:

- The displayed White, Black/African American, and Hispanic/Latino rows describe selected questionnaire evidence; they are not automatically the composition of all eligible visitors, starters, or the service-area population.
- A valid “under-representation” claim requires an agreed benchmark, matching eligibility and geography, a consistent race/ethnicity definition, the same time window, and explicit missingness treatment.
- Demographic data is primarily available after scored completion. The current capture cannot locate a race/ethnicity disparity at acquisition, questionnaire start, step progression, recording, or result action.
- Spanish pageviews and resource-path counts are descriptive. Spanish language is not a substitute for Hispanic/Latino identity, and small cells must not be turned into stable comparative rates.
- AD8, MIS, and SBC are screening/routing measures; Good, Moderate, and Poor are product result categories, not diagnoses.
- Clicks, page exits, and event counts indicate behavior or intent unless a validated downstream outcome definition says otherwise.
- Aggregate evidence cannot establish why the White-heavy profile occurs or whether a UX, copy, or outreach intervention caused improvement.

The analysis therefore labels claims as supported, partial, or blocked rather than treating a proposed method as completed evidence. Privacy floors, rate-stability thresholds, complementary suppression, and difference-attack protections are part of the protocol.

## Package structure

```text
braintree-evidence/
├── README.md                         # This orientation and navigation guide
├── CONSOLIDATED.md                   # Human-readable semantic contract
├── CONSOLIDATED.json                 # Machine-readable semantic contract
├── analysis/
│   ├── DEMOGRAPHIC_DISPARITY_ANALYSIS.md
│   ├── DEMOGRAPHIC_EQUITY_PROTOCOL.md
│   ├── DEMOGRAPHIC_EQUITY_COVERAGE.md
│   ├── DEMOGRAPHIC_EQUITY_COVERAGE.json
│   ├── DEMOGRAPHIC_EQUITY_INPUTS.json
│   └── DEMOGRAPHIC_EQUITY_SNAPSHOT.json
└── reports/
    ├── README.md                     # Source-report index and provenance notes
    ├── pdf/                          # 16 captured dashboard PDFs
    └── md/
        ├── artifacts/               # Markdown report transcriptions/syntheses
        └── prompt_conversation.md   # Capture context and scrape log
```

### Human-readable documentation

- [Consolidated semantic guide](./CONSOLIDATED.md)
- [Demographic disparity analysis](./analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md)
- [Demographic equity protocol](./analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md)
- [Equity coverage matrix](./analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md)
- [Journey explorer](./reports/md/artifacts/journey-explorer.md)
- [Comprehensive supplemental Q1–Q5 report](./reports/md/COMPREHENSIVE_SUPPLEMENTAL_ANALYSIS_Q1-Q5.md)

### Machine-readable artifacts and reproducibility

- [Consolidated semantic contract](./CONSOLIDATED.json)
- [Coverage matrix source](./analysis/DEMOGRAPHIC_EQUITY_COVERAGE.json)
- [Curated calculator inputs](./analysis/DEMOGRAPHIC_EQUITY_INPUTS.json)
- [Calculated descriptive snapshot](./analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json)
- [Snapshot calculator](../scripts/analyze_demographic_equity.py)
- [Coverage validator and Markdown renderer](../scripts/validate_demographic_equity_coverage.py)
- [Coverage tests](../tests/test_demographic_equity_coverage.py) and [snapshot tests](../tests/test_demographic_equity_snapshot.py)

Regenerate and validate the equity artifacts from the repository root:

```bash
python scripts/analyze_demographic_equity.py \
  --json-out braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_SNAPSHOT.json
python scripts/validate_demographic_equity_coverage.py \
  --markdown-out braintree-evidence/analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md
python -m pytest -q \
  tests/test_demographic_equity_coverage.py \
  tests/test_demographic_equity_snapshot.py
```

## Source reports

The original captures are preserved under [reports/](./reports/). The consolidated guide and analysis cite the report name and page so a reviewer can trace a claim back to its source. The source set includes:

- [Results Overview.pdf](./reports/pdf/Results%20Overview.pdf)
- [AD8 Analysis.pdf](./reports/pdf/AD8%20Analysis.pdf)
- [MIS Analysis.pdf](./reports/pdf/MIS%20Analysis.pdf)
- [SBC Analysis.pdf](./reports/pdf/SBC%20Analysis.pdf)
- [Scoring Reference.pdf](./reports/pdf/Scoring%20Reference.pdf)
- [Top Content.pdf](./reports/pdf/Top%20Content.pdf)
- [Top Content by Demographic.pdf](./reports/pdf/Top%20Content%20by%20Demographic.pdf)
- [Geographic Traffic.pdf](./reports/pdf/Geographic%20Traffic.pdf)
- [User Journeys.pdf](./reports/pdf/User%20Journeys.pdf)
- [Site Events.pdf](./reports/pdf/Site%20Events.pdf)
- [Clinical Trials.pdf](./reports/pdf/Clinical%20Trials.pdf)
- [Find a Provider.pdf](./reports/pdf/Find%20a%20Provider.pdf)
- [Result Pages.pdf](./reports/pdf/Result%20Pages.pdf)
- [Result Sharing.pdf](./reports/pdf/Result%20Sharing.pdf)
- [Data & Mapping Reference.pdf](./reports/pdf/Data%20%26%20Mapping%20Reference.pdf)
- [Monthly Report Generator.pdf](./reports/pdf/Monthly%20Report%20Generator.pdf)
- [User Journeys / journey-explorer.md](./reports/md/artifacts/journey-explorer.md)

## Related planning and governance

- [Client requirements](../braintree-reqs.md)
- [Implementation checklist](../BRAINTREE_CHECKLIST.md)
- [GA4 measurement contract](../plans/ga4-measurement-contract.md)
- [GA4 insights design sketch](../plans/🔵%20ga4-insights-sketch.md)
- [Evidence connector design](../plans/🔵%20evidence-connector-design.md)
- [Data retention policy](../migration/policies/data-retention-policy.md)

## Recommended reading order for an LLM or reviewer

1. Read this README for scope and boundaries.
2. Read [CONSOLIDATED.md](./CONSOLIDATED.md) for the semantic contract and report catalog.
3. Read [DEMOGRAPHIC_DISPARITY_ANALYSIS.md](./analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md) for observed findings, research context, conclusions, and UX-first recommendations.
4. Read [DEMOGRAPHIC_EQUITY_COVERAGE.md](./analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md) to distinguish answered, partial, and blocked questions.
5. Read [DEMOGRAPHIC_EQUITY_PROTOCOL.md](./analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md) for the implementation and evaluation plan.
6. Consult the PDFs in [reports/](./reports/) when a claim requires source-page verification.

When producing a new answer, name the population, grain, numerator, denominator, date window, source, inference level, and limitations before recommending action.
