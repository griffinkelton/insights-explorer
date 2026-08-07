# Additional BrainGuide Research Archive

> **Snapshot:** 2026-08-07
> **Status:** Supplemental, mixed-format research archive; not a replacement for the canonical evidence package.
> **Handling:** Internal/confidential evaluation material. Keep within the approved engagement, do not publish or reuse for model training, and do not add credentials, raw respondent data, or unapproved exports.

This folder contains additional BrainGuide/BrainTree analytics research, derived tables, research prompts, presentation exports, and conversation/context records collected after or alongside the canonical evidence package.

## What is authoritative?

The canonical semantic and equity artifacts remain in the parent package:

- [`../README.md`](../README.md) — package orientation and reading order
- [`../CONSOLIDATED.md`](../CONSOLIDATED.md) / [`../CONSOLIDATED.json`](../CONSOLIDATED.json) — semantic report registry and definitions
- [`../analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md`](../analysis/DEMOGRAPHIC_DISPARITY_ANALYSIS.md) — reviewed disparity findings and conclusions
- [`../analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md`](../analysis/DEMOGRAPHIC_EQUITY_PROTOCOL.md) — measurement and intervention protocol
- [`../analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md`](../analysis/DEMOGRAPHIC_EQUITY_COVERAGE.md) — question/gate coverage matrix

Nothing in `additional/` silently supersedes those artifacts. The files here are supporting inputs, later analyses, working prompts, derived extracts, presentation outputs, or provenance/context records. Any number reused in a client-facing deliverable must be reconciled to its source, date window, denominator, and status in the canonical package.

## Contents at a glance

| Group | Files | Role |
|---|---:|---|
| Supplemental analysis and execution | 5 | New GA4/equity findings, benchmark calculations, and protocol execution memo |
| Derived data extracts | 6 | Small CSV tables supporting funnel, campaign, benchmark, gap, and checklist analysis |
| Research prompts | 3 | Original prompt plus two distinct v2 drafts; the full v2 is the latest prompt |
| Presentations and visual exports | 7 | HTML/PPTX/PDF presentation artifacts and one-page comparison |
| Conversation/context records | 3 | Research provenance and prompt-development history |
| Placeholder/stub | 1 | Non-deliverable marker retained for provenance |
| **Source artifacts** | **23** | All pre-existing artifacts in this folder are indexed below; this README is the 24th file |

## Recommended reading order

1. Read this index and the [canonical package README](../README.md).
2. Read [`braintree-ga4-equity-supplement.md`](./braintree-ga4-equity-supplement.md) for the additive language × device and acquisition-channel GA4 cuts.
3. Read [`BrainGuide Equity Protocol — Phases 2–5 Execution Memo.md`](./BrainGuide%20Equity%20Protocol%20%E2%80%94%20Phases%202%E2%80%935%20Execution%20Memo.md) and [`md.md`](./md.md) for benchmark, funnel, concern-level, and coverage-gap execution.
4. Inspect the small CSV extracts that support those analyses.
5. Use the traffic reports and decks for presentation context, not as replacements for source-page evidence.
6. Read the v2 prompt only when planning additional research; read the conversation logs last, as provenance rather than evidence.

## 1. Supplemental analysis and execution artifacts

### [`braintree-ga4-equity-supplement.md`](./braintree-ga4-equity-supplement.md)

Additive GA4 analysis for **2026-01-01 through 2026-08-06**. It reports language × device engagement and acquisition-channel mix, including approximately 16,905 Spanish-browser-language sessions, approximately 91% Spanish mobile traffic, and a paid-media-dominated acquisition mix. It explicitly warns that browser language is not Hispanic/Latino identity, GA4 sessions/users are not people-level demographic counts, and the pull is not split pre/post the approximately March 2026 relaunch. Treat its proposed coverage-matrix changes as recommendations until reconciled with the canonical matrix.

### [`BrainGuide Equity Protocol — Phases 2–5 Execution Memo.md`](./BrainGuide%20Equity%20Protocol%20%E2%80%94%20Phases%202%E2%80%935%20Execution%20Memo.md)

Execution memo for Tasks 1–5 of the equity protocol. It adds an interim national ACS benchmark comparison, representation ratios and Wilson intervals, aggregate funnel/leak interpretation, campaign extremes, and an explicit list of remaining external inputs. Its benchmark is provisional: the service-area benchmark, race/ethnicity crosswalk, and all-eligible-visitor denominator remain unresolved.

### [`md.md`](./md.md)

Execution report derived from the latest v2 research prompt. It covers the SOW-question reconciliation, Phase 1 benchmark construction, mechanism-research results, and the concern-level/resource-action cross-tab task. Treat every result according to the report's inference labels and limitations; in particular, resource clicks are handoff intent, not confirmed clinical care-seeking, and any partial PDF/report grain must remain explicit.

### [`site-traffic-overview.md`](./site-traffic-overview.md)

GA4 traffic and flow analysis for MyBrainGuide.org, including YTD 2026 traffic, acquisition channels, landing pages, malformed URL observations, year-over-year comparison, takeaways, and data-quality recommendations. The reported engagement-rate jump requires instrumentation validation before being presented as behavioral improvement.

### [`google-analytics-report.md`](./google-analytics-report.md)

Long-form research/report transcript that evaluates the evidence package, maps the client's questions, documents GA4 findings, and develops the deep-research prompt. It is useful as provenance for how the analysis evolved, but it is not a canonical metric registry and should not be treated as a clean final report.

## 2. Derived CSV extracts

These are compact, derived tables. They are useful for review and reproducibility but do not replace the captured PDFs or canonical JSON artifacts.

### [`race_benchmark_table.csv`](./race_benchmark_table.csv)

Displayed race-row counts, observed shares, Wilson confidence intervals, interim benchmark shares, representation ratios, and percentage-point gaps. The Black and Hispanic/Latino ratios are provisional/associated comparisons based on downstream displayed rows, not population-level estimates.

### [`funnel_table.csv`](./funnel_table.csv)

Selected questionnaire step volumes and step-loss percentages from the aggregate journey analysis. The unit is not a deduplicated person-level funnel unless the source report explicitly establishes that denominator.

### [`leak_table.csv`](./leak_table.csv)

High-severity funnel leaks: AD8 `W-B-AD-9` and SBC `W-S1`/`W-D4-A-SBC`. These are diagnostic leads for instrumentation and UX investigation, not causal explanations.

### [`campaign_table.csv`](./campaign_table.csv)

Selected campaign start counts and completion-rate tiers, including high-performing organic/partner examples and low-performing Display/campaign identifiers. Verify campaign definitions, date windows, and tracking before taking action.

### [`Yourquestion-Existingcoverage-Gap.csv`](./Yourquestion-Existingcoverage-Gap.csv)

Maps the five SOW-style questions to the existing 25-question coverage framework. It identifies concern-level segmentation as the principal gap for reach and care-seeking questions.

### [`Checklistitem-StatusinBRAINTREECHECKLISTmd-WhatmyG.csv`](./Checklistitem-StatusinBRAINTREECHECKLISTmd-WhatmyG.csv)

Maps selected checklist items to what the GA4 supplement adds: channel baseline, language/device traffic, and inference-label alignment. It is a compact crosswalk, not the authoritative checklist.

## 3. Research prompts

### [`braintree-deep-research-prompt.md`](./braintree-deep-research-prompt.md)

Original 114-line foundational prompt for the BrainGuide equity and outcomes analysis. It defines the three-layer measurement model, 25 client questions, Gate 0 data-quality requirements, privacy/statistical guardrails, required report structure, and explicit blocked claims. It is retained for provenance and is superseded for execution by the full v2 prompt.

### [`braintree-deep-research-prompt-v2.md`](./braintree-deep-research-prompt-v2.md)

Latest and most complete prompt. It adds SOW-question reconciliation, grounds the work in the actual evidence package, and includes three tasks: ACS benchmark construction, mechanism-literature extension, and concern-level-by-resource-action cross-tabulation. This is the preferred prompt for future research planning.

### [`braintree-deep-research-prompt-v2 (1).md`](./braintree-deep-research-prompt-v2%20%281%29.md)

Earlier v2 draft, not an exact duplicate of the full v2. It contains the benchmark and mechanism-literature tasks but omits the later SOW reconciliation and Task 3 concern-level cross-tab. Keep for provenance; use the unnumbered `v2.md` for new work.

## 4. Presentations and visual exports

These are presentation outputs derived from the traffic analysis. They are not independent sources of truth.

### [`ga4-overview.html`](./ga4-overview.html)

HTML traffic-review deck covering YTD KPIs, channel mix, year-over-year channel change, entry pages, flow, takeaways, and recommendations.

### [`ga4-narrative-deck.slides.html`](./ga4-narrative-deck.slides.html)

Slide-formatted HTML narrative review with the same broad traffic story and added explanations for channel reclassification, campaign activity, engagement-rate validation, and next steps.

### [`ga4-executive-narrative-deck (3).html`](./ga4-executive-narrative-deck%20%283%29.html)

Full HTML executive narrative and analytics-maturity deck. This is the substantive executive-deck export among the similarly named files.

### [`ga4-overview.pptx`](./ga4-overview.pptx)

PowerPoint export corresponding to the GA4 overview presentation. Embedded metadata identifies it as a Perplexity/PptxGenJS presentation created on 2026-08-07. Review slide claims against the underlying Markdown/CSV/PDF sources.

### [`mybrainguide_ytd_2026_vs_2025.pdf`](./mybrainguide_ytd_2026_vs_2025.pdf)

One-page visual YTD 2026-versus-2025 comparison artifact. It is a presentation of selected metrics, not a substitute for the underlying GA4 extraction or measurement-contract review.

### [`ga4-executive-narrative-deck.html`](./ga4-executive-narrative-deck.html)

Placeholder stub containing only `PLACEHOLDER`; it is retained to preserve the source archive but is not a usable presentation.

### [`ga4-executive-narrative-deck (2).html`](./ga4-executive-narrative-deck%20%282%29.html)

Stub marker containing only `__FULL_HTML__`; it is not a substantive HTML deck. The substantive related export is [`ga4-executive-narrative-deck (3).html`](./ga4-executive-narrative-deck%20%283%29.html).

## 5. Conversation and provenance records

### [`research-conversation.md`](./research-conversation.md)

Conversation record documenting the earlier coverage-completeness work, validation loop, evidence boundaries, and the GA4 supplement. It explains how the canonical analysis and prompts evolved. Treat it as provenance/context, not as a clean evidence artifact.

### [`google-analytics-report.md`](./google-analytics-report.md)

Conversation/report record covering repository access, GA4 traffic findings, rationale hypotheses, industry context, and the request to build a Playwright scraper. It contains useful provenance but should not be used as the sole citation for a metric.

### [`master-perplexity-conversation.md`](./master-perplexity-conversation.md)

Large raw multi-turn conversation archive covering research prompts, migration/evidence context, and analysis development. It is the least curated artifact in this folder and may contain internal names, repository references, and discussion of credential/configuration concepts. Automated scanning found credential-shaped/API-key-related references but no confirmed live secret, private-key block, bearer token, email address, or phone number; manual review and client approval are still required before any external sharing. Treat it as confidential and never use it as a source of truth.

## Relationship map

```text
braintree-deep-research-prompt.md
          │ superseded by
          ▼
braintree-deep-research-prompt-v2 (1).md ── earlier v2 draft
          │ refined into
          ▼
braintree-deep-research-prompt-v2.md
          ├── informs ──► md.md
          ├── informs ──► BrainGuide Equity Protocol — Phases 2–5 Execution Memo.md
          └── frames ───► Yourquestion-Existingcoverage-Gap.csv

GA4 pulls / source reports ──► CSV extracts
         ├──► braintree-ga4-equity-supplement.md
         ├──► site-traffic-overview.md
         └──► HTML / PPTX / PDF presentation exports

research-conversation.md ──► google-analytics-report.md
                         └──► master-perplexity-conversation.md
```

## Privacy, provenance, and use rules

- Treat all content as confidential internal analytics/evaluation material.
- GA4 language, device, channel, session, and user fields are behavioral context; they are not race, ethnicity, or clinical-outcome fields.
- Do not treat the interim ACS comparisons as population-representation proof without an approved service-area benchmark, age/eligibility definition, and race/ethnicity crosswalk.
- Do not treat a pageview, engagement event, click, or resource handoff as a completed care, enrollment, or awareness outcome.
- Preserve source date windows and denominators. The additional reports span different pulls and may not reconcile without a defined measurement contract.
- Keep small cells suppressed and do not reconstruct suppressed values by subtraction or repeated slicing.
- Do not use raw conversation text, prompts, presentation markup, or derived CSVs as replacements for the canonical semantic registry.
- Before external sharing, perform a fresh secrets, PII, small-cell, and client-approval review.

## Validation checklist

Before using or publishing an artifact from this folder:

- [ ] Reconcile the claim to the canonical evidence package and source page/query.
- [ ] Confirm the date window, grain, numerator, denominator, and inference label.
- [ ] Confirm the claim is not based on GA4 language as a proxy for ethnicity.
- [ ] Check small-cell and rate-stability rules.
- [ ] Re-run a secrets/PII scan and obtain approval for external use.
- [ ] For decks, verify that visualized numbers match the underlying report or CSV.
