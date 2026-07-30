# v0.1.0 Release Checklist

Release candidate SHA: `________________`
Date: `________________`
Release owner: `________________`
Independent reviewer: `________________`

## Repository safety

- [ ] `email/` and `drive-download-*/` removed from current tree
- [ ] History rewrite completed and post-rewrite verification recorded (`git log --all -- email/ 'drive-download-*'` returns nothing)
- [ ] `.gitignore` and fixture-provenance policy prevent recurrence

## Security and privacy

- [ ] OAuth state/callback tests pass (`tests/test_ga4_client.py`)
- [ ] Export injection tests pass (Excel/Sheets, PDF, Markdown — `tests/test_exports.py`, `tests/test_drive_client.py`)
- [ ] No raw exceptions or tracebacks shown in production mode (`SHOW_DEBUG_DETAILS=false`)
- [ ] Privacy, Gemini, Drive, and OAuth disclosures reviewed and accurate

## Quality gates

- [ ] Clean checkout: CI passes (`python -m pytest tests/ -v --tb=short`)
- [ ] Required scenario tests pass (upload, custom metric, filter-to-zero, clear/reload, summary/chat failure)
- [ ] GA4 pagination has tested limit/continuation policy (hard cap at 500k with visible warning)
- [ ] Drive permission scope explicitly documented and justified (`drive.file` only, no `drive.readonly`)

## Product integrity

- [ ] Funnel labeled as "Page-path aggregation" with visible caveat
- [ ] Forecast labeled as "Linear trend projection" with assumptions disclosed
- [ ] API telemetry centralized in service layer
- [ ] Summary uses selected model (not always default)
- [ ] Streaming errors rendered as error states (not saved as assistant responses)
- [ ] Chart extraction is explicit opt-in (not silent background call)
- [ ] GA4 property IDs validated before pull

## Infrastructure

- [ ] `SECURITY.md` present
- [ ] `LICENSE` (MIT) present
- [ ] `.gitignore` covers all cache/artifact paths
- [ ] `.env.example` documents all configurable env vars
- [ ] `docs/_build/` removed from tracking
- [ ] Pre-commit hooks include secret scanning and large-file detection
- [ ] GitHub Actions installs from `requirements/dev.txt`, runs lint + tests + coverage

## Release

- [ ] Deferred-items issues created with acceptance criteria, labeled `post-v0.1.0`
- [ ] CHANGELOG updated with v0.1.0 entry
- [ ] Git tag `v0.1.0` created
- [ ] No known critical exceptions at time of tag

## Sign-off

- [ ] Release owner approval: ___________
- [ ] Independent reviewer approval: ___________

---

*Each checkbox requires linked evidence: a test result, PR, commit, or review note. Do not mark complete merely because code was changed.*
