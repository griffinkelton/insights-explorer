# BrainGuide Source Reports

This directory contains the captured source material used by the BrainGuide evidence package.

## Structure

- [`pdf/`](./pdf/) — 16 immutable dashboard PDF captures. These are the authoritative page-level sources for report values and citations.
- [`md/artifacts/`](./md/artifacts/) — Markdown transcriptions, report-specific summaries, and the questionnaire journey synthesis. These make source context searchable for reviewers and LLMs; they do not replace the PDFs when a page-level value must be verified.
- [`md/prompt_conversation.md`](./md/prompt_conversation.md) — capture context and scrape log for the supplemental Markdown artifacts.

## Supplemental Markdown artifacts

The Markdown artifacts include acquisition, organic search, site traffic, questionnaire results, report-specific analyses, mapping references, journey behavior, and resource-path summaries. They are aggregate research records and contain no intended raw respondent-level data, credentials, or secrets.

## Provenance rules

1. Cite the PDF filename and page for claims derived from the dashboard capture.
2. Treat Markdown artifacts as searchable context and transcription aids; verify material claims against the corresponding PDF or consolidated registry.
3. Keep report-specific date ranges and freshness dates attached to any reused metric.
4. Do not infer individual behavior, clinical status, causality, or population representativeness from aggregate captures.
5. Do not add raw exports, credentials, tokens, respondent identifiers, or unapproved small-cell data to this directory.

Start with the package-level [`README.md`](../README.md), [`CONSOLIDATED.md`](../CONSOLIDATED.md), and [`CONSOLIDATED.json`](../CONSOLIDATED.json). The demographic analysis and equity protocol are in [`../analysis/`](../analysis/).
