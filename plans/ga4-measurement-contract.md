# GA4 Measurement Contract (v0.1 draft)

> Status: Draft — Gate 0A artifact for the GA4 Insights Engine. Cross-refs: 🔵 ga4-insights-sketch.md (engine design), 🔵 evidence-connector-design.md (demographic bridge).

## Purpose

This contract defines the first five metrics the GA4 Insights Engine is allowed to compute and surface, with explicit numerator/denominator, grain, event mapping, validation status, and known limitations. No metric may be consumed by the insights layer or referenced by Gemini until it has a row here with status `validated`.

## Governance

- Owner: Product/engineering + analytics owner (metric definition, event mapping, dimension dictionary)
- Approver for validated status: named analytics/evaluation owner (TBD)
- No metric moves from `provisional` to `validated` without named sign-off.

## Initial five rows

### 1. Daily reach

- Metric: `daily_reach`
- Numerator: distinct `totalUsers` (or `sessions`, TBD) per day
- Denominator: n/a (raw count)
- Grain: daily, property-wide
- Source: `pull_ga4_report()` aggregate report, dimensions `[date]`
- Event mapping: none required (session/user-level GA4 aggregate)
- Validation status: provisional
- Known limitations: no bot/crawler filtering yet; excludes incomplete current-day/week

### 2. Page/device engagement

- Metric: `page_device_engagement_rate`
- Numerator: `engagementRate` (or engaged sessions) per `pagePath` × `deviceCategory`
- Denominator: total sessions for that page/device slice
- Grain: daily, page path × device category
- Source: `pull_ga4_report()`, dimensions `[date, pagePath, deviceCategory]`
- Event mapping: none required
- Validation status: provisional
- Known limitations: no session identifier; asset/malformed URLs not yet filtered; small-cell suppression not yet applied

### 3. Questionnaire start

- Metric: `questionnaire_start_count`
- Numerator: count of canonical `questionnaire_started` event (property-specific event name TBD, e.g. `web_questionnaire_start`)
- Denominator: n/a (raw count), or `daily_reach` if reported as a rate
- Grain: daily, event-level
- Source: requires event-level GA4 query (not available from current aggregate report)
- Event mapping: canonical `questionnaire_started` → property-specific event name (must be confirmed against GA4 event list)
- Validation status: unavailable — blocked on event-level query design
- Known limitations: cannot currently be computed from `pull_ga4_report()`; requires new query/report contract

### 4. Questionnaire completion

- Metric: `questionnaire_completion_rate`
- Numerator: count of canonical `questionnaire_finished` event, same-session, within 24 hours of start (window TBD)
- Denominator: `questionnaire_start_count` for the same cohort/window
- Grain: daily or period, event-level, per-session
- Source: requires event-level GA4 query with session/user identifier
- Event mapping: canonical `questionnaire_finished` → property-specific event name (TBD); requires funnel specification (ordered steps, re-entry rule, time window)
- Validation status: unavailable — blocked on event-level query design and funnel specification sign-off
- Known limitations: cannot currently be computed; "completion" must not be conflated with generic key-event counts until taxonomy is validated

### 5. Meaningful post-questionnaire action

- Metric: `post_questionnaire_action_rate`
- Numerator: count of users/sessions triggering an approved action-taxonomy event after questionnaire completion (e.g. `care_navigation`, `resource_use`, `contact_intent`, `referral_submitted`) — exact event(s) TBD
- Denominator: `questionnaire_completion_count` for the same cohort/window
- Grain: daily or period, event-level, per-session/user
- Source: requires event-level GA4 query + action taxonomy sign-off (Program/evaluation lead)
- Event mapping: TBD — action taxonomy must be defined and approved before this row can move past `unavailable`
- Validation status: unavailable — blocked on action taxonomy definition and event-level data
- Known limitations: risk of conflating routine clicks with meaningful outcomes; requires explicit action taxonomy approval per ga4-insights-sketch.md

## Metric-status consumption policy

> Added 2026-08-06 (master-plan cross-cutting B / archive §4.18–4.20). Defines what each status **permits downstream systems to do** — dashboard display, deterministic insights, and Gemini/model context. This section is the canonical home; the master plan links here.

- **`validated`** — may drive deterministic calculations and model context.
- **`provisional`** — may be displayed and used **only for directional findings**; all UI and model outputs must carry an unvalidated/provisional label.
- **`unavailable`** — may be shown as a blocked or planned capability, but may **not** generate a rate, calculation, claim, chart value, or numeric model evidence.

**Implementation note (prototype hygiene):** the whisperer-30 prototype's `computableMetrics()` filters only `unavailable`, so it admits `provisional` rows into model-visible context — acceptable in a prototype, not in the product. Ports should use `modelVisibleMetrics()` / `nonUnavailableMetrics()` semantics (or drop the helper) so `provisional` rows are never treated as validated-quality.

## Next steps

1. Confirm exact GA4 event names for questionnaire start/finish and candidate action-taxonomy events (rows 3–5).
2. Decide whether an event-level GA4 query (vs. current aggregate-only report) is in scope for v0.3.0 follow-up or deferred to a dedicated milestone.
3. Get named sign-off to move rows 1–2 from `provisional` to `validated` (feasible today from the current aggregate report).
4. Draft `ReportContract` objects for each row per the schema in ga4-insights-sketch.md.
5. Once rows 1–2 are validated, scope Gate 1 (GA4 descriptive insights: reach, trends, top pages, device, data-quality flags) as the first buildable slice of the Insights Engine.
