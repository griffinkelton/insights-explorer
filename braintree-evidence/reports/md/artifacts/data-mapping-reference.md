# Data & Mapping Reference

Source: https://dashboard.dev2.mybrainguide.org/reference/data-reference/

Reference page for data freshness, mapping files, and source table locations.

## Data Source Status

Last date of data available in each mart. A lag of 1-2 days is normal for daily sources — GA4 and Ads data typically land the following day. Questionnaire responses load weekly (Sunday), so a lag of up to ~9 days is expected there unless a manual export is kicked off. Status thresholds are cadence-aware.

| Source | Description | Last Date | Days Ago | Status |
|---|---|---|---|---|
| Core Web Metrics | Site traffic: users, sessions, bounce rate | 2026-08-04 | 1 | Current |
| GA4 Geography | Traffic by country, region, city | 2026-08-04 | 1 | Current |
| Top Content | Page views by content category and title | 2026-08-04 | 1 | Current |
| User Journeys | Page-to-page flows (next / previous page) | 2026-08-04 | 1 | Current |
| Outbound Clicks | External link click events from GA4 | 2026-08-04 | 1 | Current |
| Traffic Attribution | Sessions by channel, source, medium | 2026-08-04 | 1 | Current |
| Google Ads · Campaigns | Daily Google Ads cost + GA4 session data | 2026-08-03 | 2 | Current |
| Search Console | Google search: impressions, clicks, avg. position | 2026-08-03 | 2 | Current |
| Questionnaire Responses | Completed BrainGuide + Go365 responses (loads weekly, Sun) | 2026-08-02 | 3 | Current |

## Mapping Files (dbt Seeds)

All seeds live in BigQuery at `usa2-brainguide.reporting_seeds`. To update a mapping: edit the CSV in `seeds/`, then `dbt seed` (or let CI rebuild).

| File | Maps | Notes |
|---|---|---|
| seeds/content_page_map.csv | URL slug → category, canonical title, locale, is_active | 9 categories (Result, Hub, Factsheet, Article, Clinical Trials, Find a Provider, Legal, Other, Home). Tracks URL changes via is_active + superseded_by. Unmapped slugs surface as "Unmapped" in Top Content. Most frequently updated. |
| seeds/source_medium_map.csv | (source, medium) pair → channel, is_paid, campaign_target | ~73 rules; covers current GA4 naming (google/search, pmax, display) and legacy formats (cpc, paid, bing). Drives the Traffic Attribution and Channel pages. |
| seeds/persona_page_map.csv | Result-page slug → persona label, slug, audience, diagnosed, brain health, score_family | All 8 assessment personas, keyed by descriptive label/slug on three axes (Self/Someone Else, Diagnosed/Not Diagnosed, Good/Poor), plus 3 SBC personas. Legacy first-name labels retained in persona. English + Spanish slugs; Spanish rows carry en_slug for rollup. |
| seeds/campaign_name_map.csv | GA4 campaign name variant → canonical Ads campaign name | ~18 GA4 variants → 9 active campaigns. Needed because GA4 and Ads use different naming conventions. |
| seeds/campaign_target_map.csv | Campaign name prefix → business target label | Prefix match: CTC_ → Clinical Trials, FP- → Find a Provider, unmatched → BrainGuide General. |
| seeds/legacy_web_kpis.csv | Weekly web KPI history Mar 2021 – Dec 2024 | Frozen. Pre-daily-data era. Grain = weekly — do not sum with daily rows. |
| seeds/legacy_questionnaire_monthly.csv | Monthly questionnaire counts Mar 2021 – Jan 2024 | Frozen. Pre-DynamoDB era. DynamoDB supersedes from Jan 2024. |
| seeds/legacy_persona_traffic.csv | Weekly persona page traffic Mar 2021 – Aug 2023 | Frozen. Pre-SBC era. Reconstructed monotonic dates. |

## Raw BigQuery Source Tables

These tables are read by dbt. Evidence cannot query them directly.

| Group | BQ Dataset | Key Table(s) | What's In It | Notes |
|---|---|---|---|---|
| GA4 Events | analytics_257799278 | events_* (wildcard) | All GA4 events, event-level rows | Raw export began 2026-05-17 (first event date; earlier "Apr 30" was a misconception) |
| GA4 Backfill | reporting | ga4_page_historical, ga4_questionnaire_*_historical, ga4_geo_device_historical, ga4_outbound_clicks_historical, +6 more | Historical GA4 data pulled via Data API | Nov 2024 – Jun 2026 (batch pulls); session-level pulls stop Apr 29 2026; 18 tables |
| Google Ads | googleads | ads_Campaign_8328184535, ads_CampaignBasicStats_8328184535 | Daily campaign metrics + attributes (Ads Data Transfer views) | Customer ID 8328184535; cost in micros. Transfer data starts 2026-05-18; a Jan-May 2026 backfill was requested 2026-07-17 |
| DynamoDB Exports | MyBrainguide | raw_dpn-chat-bot-content, raw_dpn-chat-bot-content-go365 | Raw questionnaire responses (DynamoDB JSON) | Standard + Go365 flows; nested type tags |
| Search Console | searchconsole_brainguide | searchdata_site_impression, searchdata_url_impression | Daily search impressions, clicks, position | Live via the automatic BigQuery bulk export (migrated 2026-07). Incremental accumulator marts retain history beyond the export's 60-day partition expiry |

## dbt Model Layers

| Layer | BQ Dataset | Materialization | Purpose |
|---|---|---|---|
| Seeds | reporting_seeds | Table | Mapping CSVs loaded by dbt seed |
| Staging | reporting_staging | Views | Clean + normalize raw sources; no joins across source systems |
| Marts | reporting | Tables | Aggregate + join for Evidence queries |

Evidence SQL sources in `dashboard/sources/bigquery/` all query the `reporting` (marts) dataset.
