# 🎓 Onboarding Tour — Implementation Summary

> **Status:** ✅ Done — implemented across 6 files, 239 tests pass.
> **From:** [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) #8, [ENHANCEMENTS.md](ENHANCEMENTS.md) #5
> **Mini-spec:** [✅ onboarding-tour.md](✅ onboarding-tour.md)
> **Date:** 2026-07-28

---

## 🎯 What

A 3-step guided tour for first-time users. When no data is loaded, a "🎓 Quick Tour" button appears in the hero section. Clicking it walks the user through:

| Step | Icon | Message |
|---|---|---|
| 1 | 📂 | Upload a CSV/XLSX or connect live via Google sign-in |
| 2 | ✨ | Click **Generate Summary** for an instant AI overview |
| 3 | 💬 | Ask natural language questions in the chat box |

Each step has Back, Skip Tour, and Next/Finish buttons with a progress bar.

---

## 🏗️ Architecture

| File | Change |
|---|---|
| `utils/onboarding.py` | **New** — `TOUR_STEPS` data + `render_tour_step(step)` function. Tour card rendered in centering `[1, 2, 1]` columns matching the hero layout. Each button has a unique dynamic key (`tour_back_{step}`, `tour_skip_{step}`, `tour_next_{step}`). |
| `app.py` | Added `tour_step` session state (`0`=not started, `1`-`3`=active steps, `4`=done). |
| `components/hero.py` | "🎓 Quick Tour" button rendered when `tour_step == 0` and no data is loaded. Uses `st.button` + `st.rerun()` (BUG-005 compliant). |
| `components/__init__.py` | Imported `render_tour_step`. In `_render_main_content()`, before the hero check: if `tour_step in (1,2,3)` and `df is None`, renders the tour card + `st.stop()` — replacing the hero with the tour. |
| `utils/session.py` | `clear_data()` resets `tour_step = 0` so the Quick Tour button reappears when the user clears their data. |
| `components/sidebar.py` | `_populate_data_state()` auto-dismisses the tour (`tour_step = 4`) when data is loaded through any path: file upload, GA4 pull, or Drive. |

---

## 🔀 Edge Cases

| Scenario | Behavior |
|---|---|
| User uploads data mid-tour | Tour auto-dismisses via `_populate_data_state()` — data takes priority |
| User connects GA4 mid-tour | Same auto-dismiss (shared data-loading entry point) |
| User loads from Drive mid-tour | Same auto-dismiss |
| User clears data after tour | `clear_data()` resets `tour_step = 0`, button reappears |
| User reloads the page | Session state resets, tour restarts from step 0 |
| Tour on narrow viewport | `[1, 2, 1]` centering columns work responsively |
| Rapid button clicks | Streamlit processes one interaction at a time; dynamic keys prevent collisions |

---

## 📊 Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Where to place auto-dismiss** | `_populate_data_state()` in `sidebar.py` | Single choke point for all 3 data-loading paths (file, GA4, Drive) |
| **Tour persistence** | Per-session only (`st.session_state`) | Resets on reload — matches prototype nature; no JS complexity |
| **Tour reset on clear data** | `tour_step = 0` in `clear_data()` | Tour button reappears for the next dataset |
| **Module placement** | `utils/onboarding.py` (not `components/`) | Tour has rendering but no component-level state management |
| **Button pattern** | `if st.button()` + `st.rerun()` | BUG-005 compliant — no `on_click` callbacks |
| **Tour card layout** | Centering columns `[1, 2, 1]` | Matches hero section for visual consistency on wide screens |

---

## 🧪 Test Impact

No new tests (UI state machine, not logic). All 239 existing tests pass. Minor reviewer suggestion: a structural AST test for `utils/onboarding.py` would match project conventions but is not required.

---

## 📖 Related Docs

- [Implementation Plan](IMPLEMENTATION_PLAN.md) #8
- [Enhancement Roadmap](ENHANCEMENTS.md) #5
- [Onboarding Tour Mini-Spec](✅ onboarding-tour.md) — original deferred plan
- [CHANGELOG.md](../../CHANGELOG.md)
