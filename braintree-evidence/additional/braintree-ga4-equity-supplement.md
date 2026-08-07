# BrainGuide GA4 Equity Supplement
**Prepared for:** AHSR / BrainTree engagement (Dr. Kumbie Madondo, project lead; Greg Magnuson, IT/analytics)
**Prepared by:** Griffin Kelton, subcontractor
**Data source:** Live GA4 property `mybrainguide.org` (properties/257799278), pulled 2026-08-07
**Window queried:** 2026-01-01 to 2026-08-06 (spans the ~March 2026 site relaunch — **not yet split pre/post** in this pull; see Limitations)

> **Scope note:** This supplement extends the previously produced Demographic Equity Coverage matrix (25-question audit, Gate 0–3 coverage, `supported_now` / `partial_now` / `blocked_external_input` statuses) with two live GA4 cuts — language × device, and acquisition channel. I do not have direct access to the `braintree-evidence` repository files referenced (`BRAINTREE_CHECKLIST.md`, `DEMOGRAPHIC_EQUITY_COVERAGE.md/json`, `CONSOLIDATED.json`) in this session, so this document is additive evidence to fold into that matrix, not a replacement for it.

---

## 1. What this data can and cannot say

GA4's `language` dimension reflects **browser/device language setting**, not self-reported ethnicity, race, or national origin. The client's own self-reported demographic data comes from the questionnaire tool, not GA4 (confirmed in the 2026-07-23 kickoff transcript: *"when we report demographics, it's not demographics from Google Analytics, it's users that have taken the questionnaire and chosen to provide us those details"*). Consistent with the coverage matrix's existing statistical boundaries:

- Spanish-language browser sessions are **not** a proxy for Hispanic/Latino identity.
- Session/user counts are **not** people-level demographic counts.
- No event-level linkage currently exists between GA4 sessions and questionnaire self-reported demographics (this is one of the named `blocked_external_input` items — event-level GA4/questionnaire linkage).

This supplement is therefore descriptive traffic/engagement evidence only, used to support the same UX/access-equity priorities already identified, not new demographic representation claims.

---

## 2. Language × device engagement (Jan 1 – Aug 6, 2026)

| Language | Device | Sessions | Users | Engagement rate | Bounce rate |
|---|---|---:|---:|---:|---:|
| English | Mobile | 249,252 | 212,647 | 94.8% | 5.2% |
| English | Tablet | 69,367 | 61,885 | 95.4% | 4.6% |
| English | Desktop | 39,563 | 31,442 | 86.2% | 13.8% |
| **Spanish** | **Mobile** | **15,394** | **12,807** | **95.9%** | **4.1%** |
| Spanish | Desktop | 778 | 679 | 96.0% | 4.0% |
| Spanish | Tablet | 733 | 619 | 96.0% | 4.0% |
| All other languages (~130 rows) | Mixed | ~3,900 combined | — | Mostly small-sample (n<300 each) | — |

**Total sessions in window:** ~373,000. Spanish-language sessions (all devices): **16,905** — about **4.5%** of total sessions in this window.

### Equity-focused observations

- Spanish-language traffic is **overwhelmingly mobile** (91% of Spanish-language sessions are mobile vs. 71% for English), reinforcing the prior mobile/device-friction priority — but with sharper stakes for Spanish-speaking users specifically. If SBC or other completion flows have mobile-specific friction, it disproportionately lands on the Spanish-language segment.
- Spanish-language sessions show **slightly higher engagement and lower bounce** than English desktop sessions, but this is descriptive only — GA4 "engaged session" (10+ seconds, a conversion event, or 2+ pageviews) does not indicate task success, comprehension, or satisfaction with content.
- This 16,905-session Spanish-language cohort is a much larger population than the previously cited "9 Spanish-language questionnaire respondents year-to-date" figure from the client meeting notes. That gap is itself a finding: **the vast majority of Spanish-browser-language visitors are not completing the self-reported demographic questionnaire in a way that surfaces as a distinguishable Spanish-language respondent** — consistent with the coverage matrix's existing note on small Spanish-language questionnaire samples (~9/year) requiring cautious interpretation. This traffic-vs-questionnaire-completion gap is worth flagging as its own equity signal: **high Spanish-language site traffic, very low Spanish-language questionnaire completion capture.**
- Non-English, non-Spanish languages (Chinese, Vietnamese, Arabic, French, Portuguese, etc.) are each under 1,000 sessions — too sparse for any reliable descriptive claim per the coverage matrix's suppression rules. These should stay aggregated as "other" for any external-facing reporting.

### What remains blocked

- Whether Spanish-language users experience **worse SBC completion, funnel drop-off, or task success** than English-language users — this requires event-level funnel-by-language analysis, which is standard GA4 capability but not yet built. This should be added as a **near-term unlock candidate** (Gate 1 scope) rather than staying purely `blocked_external_input`, since it does not require new external data — only a GA4 exploration/funnel report scoped by `language`.
- Whether Spanish-browser-language sessions correlate at all with Hispanic/Latino identity — they do not, and no proxy should be constructed from this.

---

## 3. Acquisition channel (Jan 1 – Aug 6, 2026)

| Channel | Sessions | Users | Engagement rate | Bounce rate |
|---|---:|---:|---:|---:|
| Cross-network | 184,666 | 166,564 | 96.1% | 3.9% |
| Display | 95,508 | 85,095 | 93.9% | 6.1% |
| Paid Search | 61,556 | 56,137 | 94.7% | 5.3% |
| Direct | 11,217 | 9,070 | 75.0% | 25.0% |
| Organic Search | 8,413 | 6,713 | 89.9% | 10.1% |
| Unassigned | 7,187 | 5,888 | 86.3% | 13.7% |
| Referral | 4,225 | 2,362 | 85.6% | 14.4% |
| Organic Social | 471 | 412 | 73.7% | 26.3% |
| Paid Social | 132 | 106 | 100.0% | 0.0% |
| AI Assistant | 20 | 9 | 70.0% | 30.0% |
| Email | 14 | 13 | 85.7% | 14.3% |
| Paid Other | 11 | 11 | 9.1% | 90.9% |
| Organic Video | 3 | 3 | 100.0% | 0.0% |

**Total: ~373,423 sessions.** Paid channels (Cross-network + Display + Paid Search + Paid Social + Paid Other) account for **~90% of all sessions.** Organic, referral, direct, and email combined are roughly **8%**.

### Equity-focused observations

- This is a **paid-media-dominated acquisition model.** That matters directly for the client's core evaluation question — *"are we reaching the right populations?"* — because paid-media targeting parameters (platforms, ad creative, geographic/demographic targeting settings, budget allocation) are themselves a lever that can widen or narrow reach into priority populations (women, Black, Hispanic/Latino communities), and they are **fully within the client's control**, unlike organic/referral patterns.
- Organic Social and "AI Assistant" channels show meaningfully lower engagement and higher bounce (73.7% / 70.0% engagement) than paid channels — small samples, but worth watching if community-based or trusted-messenger outreach (a recommended future priority) is expected to route primarily through organic/social/referral paths rather than paid media.
- **Direct traffic bounce rate (25.0%) is notably higher than paid-channel bounce.** Direct traffic often includes users returning from an offline referral (e.g., a provider, community organization, or word-of-mouth) — exactly the trusted-messenger pathway the equity plan recommends prioritizing later. A 25% bounce rate on that pathway, even descriptively, is worth investigating before scaling trusted-messenger outreach, since it may indicate landing-page mismatch with what an offline referral led the visitor to expect.

### What remains blocked

- Whether paid-media targeting settings (platform, geography, demographic ad parameters) have been configured to reach — or inadvertently exclude — priority populations. This requires the ad platform configuration itself (Google Ads / Display targeting settings), which sits outside GA4 and outside this engagement's current data access.
- Channel-by-outcome equity (does a paid-search visitor complete SBC and reach a provider referral at the same rate as a direct/referral visitor?) — blocked on the same event-level linkage gap noted for language.

---

## 4. Recommended additions to the coverage matrix

Given this GA4 evidence, I'd suggest two matrix status changes and one new near-term recommendation, subject to your and the team's review:

1. **Move "language-segmented funnel/completion rates" from a pure external-input blocker to a Gate 1 near-term item.** It does not require new consent, new instrumentation, or client decisions — only a GA4 exploration scoped by `language` against existing funnel/event definitions. This is lower-hanging fruit than most of the 9 `blocked_external_input` items.
2. **Add a new descriptive finding**: "High Spanish-language site traffic (~16,900 sessions YTD) coexists with very low Spanish-language questionnaire-completion capture (~9/year self-reported)." This gap itself supports the existing recommendation priority of "first-class Spanish and language persistence" with a concrete traffic baseline behind it, not just a qualitative rationale.
3. **Add acquisition-channel configuration** (not just acquisition-channel *outcomes*) as an explicit item under the existing "validated acquisition-channel equity" blocked item — specifically, request the paid-media platform's targeting/audience configuration as a distinct evidence source, separate from GA4 session data.

---

## 5. Limitations of this supplement specifically

- **Pre/post relaunch split not performed in this pull.** Both queries span the full Jan–Aug 2026 window, which includes both the old and new (~March 2026) site. Per this project's standing instruction, any metric reported externally should distinguish pre- vs. post-relaunch data explicitly — this supplement does not yet do that and should be re-run with a date split before inclusion in a client-facing deliverable.
- **Small-sample suppression not fully applied here.** Language rows below roughly 100 sessions are shown only in a rolled-up "all other languages" line above to avoid drawing conclusions from single-digit or low-double-digit session counts; the full 141-row GA4 response includes many such sparse rows and should not be reported at that granularity externally.
- **This is aggregate GA4 data only** — no user-level, session-level, or PII-adjacent data was exported or is retained beyond this document. Per the engagement's confidentiality terms, this data should be treated as confidential client analytics and not used, retained, or repurposed outside this evaluation.
- I could not verify or cross-reference this against the actual `braintree-evidence/DEMOGRAPHIC_EQUITY_COVERAGE.json` you described, since that repository/file path is not accessible to me in this session. If you can share it (via GitHub, Drive, or as an attachment), I can directly reconcile this supplement's suggested status changes against the canonical matrix rather than proposing them provisionally as above.
