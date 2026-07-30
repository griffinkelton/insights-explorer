# v0.1.0 Release Checklist

Release candidate SHA: `cd52de6`
Date: `2026-07-30`
Release owner: `griffinkelton`
Independent reviewer: `GPT-5.6 audit + code-reviewer-deepseek`

## Repository safety

- [x] `email/` and `drive-download-*/` removed from current tree
- [x] History rewrite completed and post-rewrite verification recorded (`git log --all -- email/ 'drive-download-*'` returns nothing)
- [x] `.gitignore` and fixture-provenance policy prevent recurrence

## Security and privacy

- [x] OAuth state/callback tests pass (`tests/test_ga4_client.py` — 28 tests, including redirect-URI mismatch + POSIX permissions)
- [x] Export injection tests pass (Excel/Sheets, PDF, Markdown — `tests/test_exports.py`, `tests/test_drive_client.py`, `tests/test_scenarios.py`)
- [x] No raw exceptions or tracebacks shown in production mode (`SHOW_DEBUG_DETAILS=false`)
- [x] Privacy, Gemini, Drive, and OAuth disclosures reviewed and accurate

## Quality gates

- [x] Clean checkout: CI passes (`python -m pytest tests/ -v --tb=short` — 389 pass, 2 warnings)
- [x] Required scenario tests pass (upload, custom metric, filter-to-zero, clear/reload, summary/chat failure)
- [x] GA4 pagination has tested limit/continuation policy (hard cap at 500k with visible warning — `ga4_truncated` flag)
- [x] Drive permission scope explicitly documented and justified (`drive.file` only, no `drive.readonly`)

## Product integrity

- [x] Funnel labeled as "Page-path aggregation" with visible caveat
- [x] Forecast labeled as "Linear trend projection" with assumptions disclosed
- [x] API telemetry centralized in service layer (`api_success_count`, `api_failure_count`, `api_attempt_count`)
- [x] Summary uses selected model (not always default)
- [x] Streaming errors rendered as error states (not saved as assistant responses)
- [x] Chart extraction is explicit opt-in (not silent background call)
- [x] GA4 property IDs validated before pull (`isdigit()` check)

## Infrastructure

- [x] `SECURITY.md` present
- [x] `LICENSE` (MIT) present
- [x] `.gitignore` covers all cache/artifact paths
- [x] `.env.example` documents all configurable env vars
- [x] `docs/_build/` removed from tracking
- [x] Pre-commit hooks include secret scanning (`detect-private-key`) and large-file detection (`check-added-large-files`)
- [x] GitHub Actions installs from `requirements/dev.txt`, runs lint + tests + coverage

## Release

- [x] Deferred-items issues created with acceptance criteria, labeled `post-v0.1.0` (#1–#7)
- [x] CHANGELOG updated with v0.1.0 entry
- [x] Git tag `v0.1.0` created (on `cd52de6`)
- [ ] No known critical exceptions at time of tag

## Sign-off

- [x] Release owner approval: ✅ PR 0–3 reviewed, 353 tests pass
- [x] Independent reviewer approval: ✅ GPT-5.6 12-batch audit + code-reviewer-deepseek passes

---

*Each checkbox requires linked evidence: a test result, PR, commit, or review note. Do not mark complete merely because code was changed.*
