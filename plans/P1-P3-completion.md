# 📋 P1–P3 Sprint — Completion Tracker

> **Tracks:** All 13 items from [P1-P3-sprint-spec.md](P1-P3-sprint-spec.md), plus the deferred #8 onboarding tour.
> **Status:** 🔴 Awaiting implementation — 0/13 complete, 1 deferred, 2 pre-done.
> **Test baseline:** 171 tests passing across 8 modules.

---

## 📊 Progress Summary

| Batch | Items | Complete | Pending | Optional |
|---|---|---|---|---|
| ✅ Pre-Done | #7, README test count | 2 | 0 | — |
| 🔴 Batch 1 — Safety | #4, #5 | 0 | 2 | — |
| 🔴 Batch 2 — Quick Wins | #1, NEW-A | 0 | 2 | — |
| 🔴 Batch 3 — Docs | #2, #3, #9 | 0 | 3 | — |
| ⚠️ Batch 4 — UX | #8 | 0 | 0 | 1 |
| 🔴 Batch 5 — Infra | #10–14 | 0 | 5 | — |
| ⏭️ Skipped | #6 | — | — | — |
| **Total** | **13 items** | **2 pre-done** | **12 pending** | **1 optional** |

---

## ✅ Pre-Done (No Work Required)

| Item | What | Status | Notes |
|------|------|--------|-------|
| **#7** | Loading spinner for summary button | ✅ Done | `st.spinner` wrapping `_generate_summary()` in `app.py` |
| **—** | Test count in README (171) | ✅ Done | Verified via `pytest tests/ -q` |

---

## 🔴 Batch 1 — Safety

| # | Item | Status | Commit | Date | Files Changed | Tests |
|---|---|---|---|---|---|---|
| **#4** | File size & row limits (+ download truncated slice) | ⬜ Pending | — | — | `utils/data_loader.py`, `app.py` | +3 new, ~6 updated |
| **#5** | Rate limiting on chat | ⬜ Pending | — | — | `app.py` | 0 (smoke test only) |

---

## 🔴 Batch 2 — Quick Wins

| # | Item | Status | Commit | Date | Files Changed | Tests |
|---|---|---|---|---|---|---|
| **#1** | Learn link in sidebar (`st.page_link`) | ⬜ Pending | — | — | `app.py` | 0 (covered by #13) |
| **NEW-A** | OAuth redirect configurability (`OAUTH_REDIRECT_URI` env var) | ⬜ Pending | — | — | `app.py`, `.env.example` | 0 |

---

## 🔴 Batch 3 — Docs

| # | Item | Status | Commit | Date | Files Changed | Tests |
|---|---|---|---|---|---|---|
| **#2** | Update learn page test count (92 → 171) | ⬜ Pending | — | — | `pages/learn.py`, `tests/test_learn_page.py` | 1 assertion changed |
| **#3** | Update docs (ENHANCEMENTS, ARCHITECTURE) | ⬜ Pending | — | — | `ENHANCEMENTS.md`, `ARCHITECTURE.md` | 0 |
| **#9** | Learn link in README | ⬜ Pending | — | — | `README.md` | 0 |

---

## ⚠️ Batch 4 — UX (Optional)

| # | Item | Status | Notes |
|---|---|---|---|
| **#8** | Onboarding tour | ⚠️ Deferred | Full implementation in [onboarding-tour.md](onboarding-tour.md). Pick up after Batches 1–3 are stable. |

---

## 🔴 Batch 5 — Infra

| # | Item | Status | Commit | Date | Files Changed | Tests |
|---|---|---|---|---|---|---|
| **#10** | pytest-cov coverage reporting | ⬜ Pending | — | — | `requirements.txt`, `README.md`, `cloudbuild.yaml` | 0 |
| **#11** | Split dev dependencies | ⬜ Pending | — | — | New `requirements/` dir, `requirements.txt`, `cloudbuild.yaml`, `README.md` | 0 |
| **#12** | Per-module test badges in README | ⬜ Pending | — | — | `README.md` | 0 |
| **#13** | app.py structural test | ⬜ Pending | — | — | New `tests/test_app.py` | ~18 new |
| **#14** | GitHub Actions CI | ⬜ Pending | — | — | New `.github/workflows/test.yml`, `README.md` | 0 |

---

## ⏭️ Skipped

| # | Item | Reason |
|---|---|---|
| **#6** | .streamlit/pages.toml | `st.page_link` (#1) provides sidebar navigation without version-compat concerns |

---

## 📈 Post-Completion Expected State

| Metric | Current | After P1-P3 |
|---|---|---|
| Test count | 171 | ~192 |
| Test modules | 8 | 9 (`test_app.py` added) |
| CI pipelines | 1 (Cloud Build) | 2 (+ GitHub Actions) |
| Dependencies | Flat `requirements.txt` | Split `requirements/base.txt` + `dev.txt` |
| Coverage reporting | None | `pytest-cov` with per-module percentages |
| OAuth redirect | Hardcoded `localhost:8501` | Configurable via `OAUTH_REDIRECT_URI` |
| File safety | No limits | 100MB size cap, 50k row limit with truncation + download |
| Rate limiting | None | 2-sec debounce + API call counter |

---

## 📖 Related Docs

- [P1-P3-sprint-spec.md](P1-P3-sprint-spec.md) — Full implementation details for each item
- [onboarding-tour.md](onboarding-tour.md) — Deferred #8 mini-spec
- [P4-future-plan.md](P4-future-plan.md) — Items beyond this sprint (#15–21, P3–P6)
- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) — Original 21-item blueprint
- [CHANGELOG.md](../CHANGELOG.md) — All changes tracked with commits and dates
