# 🔵 Interstitial Light-Mode Polish — Implementation Spec (Workstream B)

> **Status:** 🔵 In design — implementation not started
> **Date:** 2026-08-03
> **Based on:** [`plans/🔵 interstitial-ui-polish-design.md`](../🔵%20interstitial-ui-polish-design.md) §3 (Workstream B); deferred from [`plans/00-sprints/🔵 interstitial-ui-polish-spec.md`](./🔵%20interstitial-ui-polish-spec.md) (D1, D11)
> **Scope:** Full light-mode redesign of the app UI. **Standalone** — no dependency on Workstream A/C (which already cover B1 component theming + B6 dialog light styling).
> **Delivery:** Incremental PRs per item, unversioned on `main` (no tag).
> **Effort:** ~2–3 days.

---

## 1. Overview

The theme toggle works and `LIGHT_THEME_CSS` has broad coverage (buttons, metrics, expanders, dataframes, chat, alerts, uploader, inputs, tabs, code, scrollbar, tooltips, Learn cards), but the light theme is unfinished: several components hard-code dark-palette values with **no light overrides**, accent colors are low-contrast on white, and `LIGHT_THEME_CSS` itself scatters raw hexes instead of using tokens. This spec audits every surface, fixes the broken ones, consolidates tokens, and verifies the full toggle cycle.

**Companion scope already handled elsewhere (do NOT duplicate):**
- **B1** (component `index.html` theming) and **B6** (dialog container light rules) → implemented in the A+C spec (§5.5).
- This spec assumes those landed; its verification includes the new surfaces.

## 2. Decisions (interview-derived + audit findings)

| # | Decision | Choice |
|---|---|---|
| L1 | Independence | B is CSS/token-only (`utils/styles.py` + inline styles + Plotly templates) — no shared implementation surface with A/C; ship independently, any time after A+C |
| L2 | Fidelity | Match the established dark-mode *design language* (cards, borders, radii, gradients) in light — not a redesign, a faithful light translation |
| L3 | Token-first | All new light values flow from CSS variables (`--bg-*`, `--text-*`, `--accent-*`); no new raw hexes except where iframes/inline styles can't reach vars |
| L4 | Contract frozen | `VALID_THEMES`, `build_theme_css()` signature, `inject_custom_css()` (uses `st.html()`) unchanged; FOUC-prevention preemptive style preserved |
| L5 | No component dark regression | Dark mode must remain pixel-identical after each PR (guard rail) |
| L6 | Testing | Extend existing theme tests (`test_styles.py`, `test_theme_propagates_to_iframe_body`) + a manual toggle checklist; no new heavyweight browser suite |

## 3. Audit inventory (from source review 2026-08-03)

### 3.1 Broken in light mode (no overrides — must fix)

| # | File: line | Problem | Fix |
|---|---|---|---|
| A1 | `components/hero.py:27–63` | Whole empty-state hero hard-codes dark: `#9898b0` paragraph, `#1a1a26` feature cards, `#f0f0f5` titles, `#686880` captions, `rgba(255,255,255,0.06)` borders; h2 gradient `#c4b5fd,#818cf8,#6366f1` | Convert to CSS vars + a `.hero-*` class set; add light overrides (cards → `--bg-card`/`--border`, text → `--text-*`) |
| A2 | `components/learning_challenge.py:72–77` | `#ffffff10` border and `#0a2a0a20` background are white-on-white / near-invisible in light mode | Theme-branch the border/bg values (or CSS vars) per solved/attempted state |
| A3 | `components/data_preview.py:206,228,245` | Insight accent `#c4b5fd` (light purple) is low-contrast on white; `#818cf8`/`#fbbf24` borderline | Per-tone light variants (e.g., `#6366f1`, `#d97706` for light) via a small theme-aware helper |
| A4 | `components/data_preview.py:413–430` | Quality-grade colors `#34d399/#818cf8/#fbbf24/#f59e0b/#f87171` + `#686880` captions — some low-contrast on white | Add light-mode grade palette; captions → `--text-muted` |

### 3.2 Correct but should consolidate (token hygiene — L3)

| # | Location | Issue | Fix |
|---|---|---|---|
| B2a | `utils/styles.py` `LIGHT_THEME_CSS` | Raw hexes scattered: `#e5e7eb`, `#e0e0eb`, `#d1d5db`, `#9ca3af`, `#f5f5fa`, `#f3f4f6` | Introduce a small set of light-mode semantic vars (`--hover`, `--code-bg`, `--scroll-thumb`…) used by those rules |
| B2b | `components/sidebar.py:167–176, 196, 343, 537, 625` | `section_color`/`title_color`/`subtitle_color` theme-branched inline, repeated 5× | Single `_section_header()` helper using CSS vars (reduces drift; optional) |
| B2c | `components/sidebar.py:210–212` | OAuth redirect captions hard-code `#9898b0/#686880/#818cf8` (dark-optimized) | Switch to `--text-*`/`--accent` vars |
| B2d | `components/sidebar.py:491–499` (B3 from design doc) | Privacy card inline theme-branched `rgba` | Replace with a `.privacy-card` class in `COMPONENT_CSS` using `--bg-card`/`--border`/`--text-secondary` |
| B2e | `utils/styles.py` light global `p, span, div { color: var(--text-primary) }` (line ~75) | Aggressive blanket rule can override intended muted text | Scope to `.stMarkdown`/specific containers; verify no contrast regressions |

### 3.3 Already theme-aware — verify only

| # | Location | Status | Action |
|---|---|---|---|
| C1 | `components/onboarding_tour.py:83–99` | Has its own `:root` dark vars **and** a `[data-theme="light"]` block | Verify it actually switches with the app toggle (it may use independent detection); align accent tokens if cheap |
| C2 | `pages/learn.py:31` | `_hero_color` theme-branched ✅; Learn cards/tip-boxes have light overrides in `LIGHT_THEME_CSS` | Visual pass only |
| C3 | `utils/charts.py:27–28, 140–141, 243–244` (B5) | `plotly_dark/plotly_light` templates + `font_color = "#9898b0" if dark else "#4b5563"` ✅ | Verify accent legibility (`#fbbf24` amber, `#c4b5fd`); adjust light font to `--text-secondary` equivalent if needed |

### 3.4 New surfaces from A+C (already themed there — verify in-context)
- Dialog container + component iframe light rules (B6/B1) — visual check inside the dialog with toggle.

---

## 4. Phased plan

| Phase | Scope | Effort | PR |
|---|---|---|---|
| 1 | **B2a/B2e token consolidation + blanket-rule fix** in `styles.py`; `test_styles.py` updated | 0.5d | PR-L1 |
| 2 | **B2b–B2d**: sidebar helpers, OAuth captions, privacy-card class | 0.5d | PR-L2 |
| 3 | **A1 hero** light overrides (`.hero-*` classes) | 0.5d | PR-L3 |
| 4 | **A2–A4**: learning-challenge borders, data-preview accents + grade palette | 0.5d | PR-L4 |
| 5 | **C1–C3 verification** + any required tweaks (onboarding tour, charts light font) | 0.5d | PR-L5 |
| 6 | Docs: CHANGELOG (interstitial heading) + `RELEASE_CHECKLIST.md` interstitial row "Light mode design polish" checked off | — | PR-L6 |

Order rationale: token foundation first (everything else consumes it), then shared sidebar, then the three broken surfaces, then verification-only items.

## 5. Testing & verification

- **Unit:** `tests/test_styles.py` — assert light rules reference the new vars (no raw hex regression where vars expected); keep `build_theme_css()` contract tests intact.
- **Browser (existing, extended):** `test_theme_propagates_to_iframe_body` already checks `data-theme` in the component iframe for both themes — extend to assert the dialog surface (post-A+C) and that toggling light→dark→light doesn't error.
- **Manual toggle checklist (Chrome/macOS):** dark→light→dark across: main empty state (hero), loaded data view (metrics, preview table, insights, quality card), sidebar (logo, sections, privacy card, model card, footer), chat, Learn page, and the Picker dialog (post-A+C). No white-on-white text, no dark-on-dark cards, focus rings visible.
- **Guard rail (L5):** each PR must show no dark-mode visual regression (screenshot compare or manual).

## 6. Delivery & versioning

- Incremental PRs (PR-L1 … PR-L6), each with passing `test_styles.py` + full pytest, unversioned on `main`.
- Landed any time after A+C (independent); CHANGELOG under the same interstitial heading as A+C.

## 7. Definition of Done

| Item | Pass criteria | Verified by |
|---|---|---|
| Token consolidation (B2a/B2e) | Light rules use semantic vars; blanket `div` color rule scoped; `test_styles.py` green | PR-L1 |
| Sidebar + privacy card (B2b–d) | Section headers/privacy card render correctly in both themes; no inline rgba for privacy | PR-L2 |
| Hero light (A1) | Empty-state hero legible on white: cards on `--bg-card`, text `--text-*`, gradient contrast OK | PR-L3 + manual |
| Component surfaces (A2–A4) | Challenge borders/bg visible in light; insight + grade accents ≥ WCAG AA-ish on white | PR-L4 |
| Charts + tour (C1–C3) | Plotly light templates legible; tour switches with toggle; no changes needed or documented | PR-L5 |
| Regression guard | Dark mode pixel-identical after all PRs; manual toggle checklist passes both directions | PR-L6 |

**Overall gate:** full pytest green (672 + updated `test_styles.py`), Playwright smoke 19 (14 existing + 5 A+C) unaffected, frontend `npm run check && npm run build` clean, credential guard exit 0, manual toggle pass.

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Aggressive light overrides regress dark mode | L5 guard rail per PR; change `LIGHT_THEME_CSS` only, never `COMPONENT_CSS` base tokens |
| Inline hard-coded colors drift again | Token helper + `.hero-*`/`.privacy-card` classes become the canonical pattern; note in component docstrings |
| Plotly template mismatch with brand palette | C3 sweep; light font/accents tuned to `--text-*` equivalents |
| Duplication with A+C (B1/B6) | Explicit "do not duplicate" boundary in §1; B spec verifies those surfaces, doesn't re-theme them |

## 9. Reference files

- Design doc: [`plans/🔵 interstitial-ui-polish-design.md`](../🔵%20interstitial-ui-polish-design.md) §3
- A+C spec (B1/B6 ownership): [`plans/00-sprints/🔵 interstitial-ui-polish-spec.md`](./🔵%20interstitial-ui-polish-spec.md)
- Implementation: `utils/styles.py`, `components/hero.py`, `components/sidebar.py`, `components/data_preview.py`, `components/learning_challenge.py`, `components/onboarding_tour.py`, `pages/learn.py`, `utils/charts.py`
- Tests: `tests/test_styles.py`, `tests/test_drive_import_smoke.py` (`test_theme_propagates_to_iframe_body`)
- Parent deferral: [`RELEASE_CHECKLIST.md`](../../RELEASE_CHECKLIST.md) — "Light mode design polish"
