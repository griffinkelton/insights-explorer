# 📋 P1–P3 Sprint — Completion Tracker

> **Tracks:** All 13 items from [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md), plus the deferred #8 onboarding tour.
> **Status:** 🟢 Complete — 12/13 items done, 1 deferred, 2 pre-done.
> **Test baseline:** 194 tests passing across 9 modules (171 → 194).
> **Last updated:** 2026-07-28 (sprint executed)

---

## 📊 Progress Summary

| Batch | Items | Complete | Pending | Optional |
|---|---|---|---|---|
| ✅ Pre-Done | #7, README test count | 2 | 0 | — |
| ✅ Batch 1 — Safety | #4, #5 | 2 | 0 | — |
| ✅ Batch 2 — Quick Wins | #1, NEW-A | 2 | 0 | — |
| ✅ Batch 3 — Docs | #2, #3, #9 | 3 | 0 | — |
| ⚠️ Batch 4 — UX | #8 | 0 | 0 | 1 |
| ✅ Batch 5 — Infra | #10–14 | 5 | 0 | — |
| ⏭️ Skipped | #6 | — | — | — |
| **Total** | **13 items** | **12 done** | **0 pending** | **1 optional** |

---

## ✅ Batch 1 — Safety

| # | Item | Status | Files Changed | Tests |
|---|---|---|---|---|
| **#4** | File size & row limits (+ download truncated slice) | ✅ Done | `utils/data_loader.py`, `app.py` | +3 new, ~6 updated |
| **#5** | Rate limiting on chat | ✅ Done | `app.py` | 0 (smoke test) |

---

## ✅ Batch 2 — Quick Wins

| # | Item | Status | Files Changed | Tests |
|---|---|---|---|---|
| **#1** | Learn link in sidebar (`st.page_link`) | ✅ Done | `app.py` | 0 (covered by #13) |
| **NEW-A** | OAuth redirect configurability (`OAUTH_REDIRECT_URI` env var) | ✅ Done | `app.py` | 0 (covered by #13) |

---

## ✅ Batch 3 — Docs

| # | Item | Status | Files Changed | Tests |
|---|---|---|---|---|
| **#2** | Update learn page test count (92 → 171) | ✅ Done | `pages/learn.py`, `tests/test_learn_page.py` | 1 assertion changed |
| **#3** | Update docs (ENHANCEMENTS, ARCHITECTURE) | ✅ Done | `ENHANCEMENTS.md`, `ARCHITECTURE.md` | 0 |
| **#9** | Learn link in README + free-tier limits | ✅ Done | `README.md` | 0 |

---

## ⚠️ Batch 4 — UX (Optional)

| # | Item | Status | Notes |
|---|---|---|---|
| **#8** | Onboarding tour | ⚠️ Deferred | Full implementation in [Onboarding tour](✅ onboarding-tour.md). |

---

## ✅ Batch 5 — Infra

| # | Item | Status | Files Changed | Tests |
|---|---|---|---|---|
| **#10** | pytest-cov coverage reporting | ✅ Done | `requirements.txt`, `README.md`, `cloudbuild.yaml` | 0 |
| **#11** | Split dev dependencies | ✅ Done | New `requirements/base.txt`, `requirements/dev.txt` | 0 |
| **#12** | Per-module test badges in README | ✅ Done | `README.md` | 0 |
| **#13** | app.py structural test | ✅ Done | New `tests/test_app.py` | +20 new |
| **#14** | GitHub Actions CI | ✅ Done | New `.github/workflows/test.yml`, `README.md` | 0 |

---

## 📈 Post-Sprint State

| Metric | Before | After |
|---|---|---|
| Test count | 171 | **194** |
| Test modules | 8 | **9** (`test_app.py` added) |
| CI pipelines | 1 (Cloud Build) | **2** (+ GitHub Actions) |
| Dependencies | Flat `requirements.txt` | **Split** `base.txt` + `dev.txt` |
| Coverage reporting | None | `pytest-cov` with `--cov=utils --cov=pages` |
| OAuth redirect | Hardcoded `localhost:8501` | **Configurable** via `OAUTH_REDIRECT_URI` |
| File safety | No limits | **100MB size cap, 50k row limit** + truncation + download |
| Rate limiting | None | **2-sec debounce** + API call counter in sidebar |
| Learn page discovery | URL-only | **Sidebar link** via `st.page_link` |

---

## 📖 Related Docs

- [P1-P3 sprint spec](✅ P1-P3-sprint-spec.md) — Full implementation details
- [Onboarding tour](✅ onboarding-tour.md) — Deferred #8 mini-spec
- [P4 future plan](✅ P4-future-plan.md) — Remaining items
- [CHANGELOG.md](../CHANGELOG.md) — All changes tracked
