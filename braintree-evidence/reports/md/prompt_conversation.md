<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Scrape content on this page and put it in a MD file.

I've scraped the "Site Traffic Overview" page and saved it as a Markdown file . The file captures all the visible content from the dashboard, including the data availability table, combined totals across all sources, GA4 daily metrics, and the paginated daily/monthly/weekly data tables.[^1_1]

## Content Summary

The page tracks web analytics for a site called BrainGuide, blending legacy spreadsheet data (Mar 2021–Oct 2024) with GA4 API pulls and raw event exports (Nov 2024–present). Key sections captured include:[^1_1]

- **Data availability** — explains which metrics are available for each time period and data source
- **Combined totals** — 1.33M web users, 1.7M sessions, 2.75M pageviews across all history
- **Daily GA4 metrics** — 677K users, 715K sessions with a 69.8% engagement rate
- **Three data tables** — daily (32 pages), historical monthly (4 pages), and historical weekly (10 pages), each showing the first page of rows visible in the scraped content

Since the tables are paginated on the live dashboard (e.g., page 1 of 32 for daily data), the Markdown file only includes the rows visible on the initially loaded page rather than the full multi-year dataset. If you need the complete historical data across all pages, let me know and I can look into whether the underlying API can be queried directly for a full export.

<div align="center">⁂</div>

[^1_1]: https://dashboard.dev2.mybrainguide.org/acquisition/core-web-metrics/


---

# Do the same thing here

I've scraped the "Acquisition Channels" page and saved it as a Markdown file . It captures channel-level GA4 data available from November 2024 onward.[^2_1]

## Content Summary

The page covers **714,928 total sessions** with **87.2% paid traffic** and **11.1% organic/free** across 849 unique referring domains. Key sections in the file include:[^2_1]

- **Sessions by Channel** — Cross-network (32.7%), Paid Search (28.6%), and Display (24.1%) dominate traffic
- **Paid vs. Non-Paid Traffic** — breaks each channel down by paid/free/unmapped classification
- **Source/Medium Breakdown** — shows the underlying source-medium pairs (e.g., google/cpc, fb/paid), paginated across 5 pages, with page 1 captured
- **Referring Domains** — editorial referrers only (ad networks excluded), led by grizly.com and usagainstalzheimers.org, paginated across 4 pages, with page 1 captured

As with the previous page, the Source/Medium and Referring Domains tables are paginated on the live dashboard, so only the first page of each is included in the Markdown export. Let me know if you'd like me to page through and capture the remaining rows for either table.

<div align="center">⁂</div>

[^2_1]: https://dashboard.dev2.mybrainguide.org/acquisition/traffic-sources/


---

# Same here too

I've scraped the "Organic Search" page and saved it as a Markdown file . It covers Google Search Console performance for the site over the last 90 days (May 6 – Aug 3, 2026).[^3_1]

## Content Summary

The page shows **2,452 clicks** and **161,510 impressions** at a **1.5% CTR** and **avg. position 16.0**. Notable sections captured include:[^3_1]

- **By Device** — mobile drives the most clicks (1,638) with the best CTR (3.0%), while desktop gets more impressions but a weaker 0.7% CTR
- **Top Queries** — dominated by branded and unbranded dementia/Alzheimer's test-related searches (e.g., "dementia test online free"), though this table only reflects named queries and excludes anonymized long-tail terms, paginated across 8 pages
- **Top Landing Pages** — the homepage leads by far with 1,130 clicks, followed by content pages on financial behavior and Alzheimer's treatment, paginated across 7 pages
- **Search Surfaces** — virtually all traffic comes from standard "web" results, with no Discover, Image, News, or Video surface activity
- **Branded vs. Non-Branded** — branded queries convert far better (7.6% CTR) than non-branded (1.3% CTR)
- **By Country** — USA leads with 951 clicks, followed by Canada, UK, and Australia, paginated across 2 pages

As with the earlier pages, tables for Top Queries, Top Landing Pages, and By Country are paginated on the live dashboard, so only page 1 of each is included in this export.

<div align="center">⁂</div>

[^3_1]: https://dashboard.dev2.mybrainguide.org/acquisition/google-search/


---

# This page too

I've scraped the "Geographic Traffic" page and saved it as a complete Markdown file  — this page had no pagination, so the full dataset is captured.[^4_1]

## Content Summary

The site reached **620,461 US users** across **81 states/territories** and **694,800 total users** across **211 countries** since November 2024. Key sections include:[^4_1]

- **US State Detail** — full 51-row table with population-normalized reach; California, Florida, and Texas lead in raw users, but Kentucky (1,700.6) and DC (3,051.4) top the users-per-100k-seniors metric, which is most relevant for BrainGuide's older-adult audience
- **Top Cities** — New York, Los Angeles, and Chicago lead US city-level traffic
- **All Countries** — full 211-country breakdown, with the US, Canada, and India as the top three
- **Trend Over Time** — monthly US and total users from Nov 2024 through Aug 2026, showing a major traffic surge in Nov–Dec 2025 and Apr 2026 (83,015 US users)

Since this page loaded all rows without pagination, the Markdown export is comprehensive rather than a partial first page like the previous three dashboard pages.

<div align="center">⁂</div>

[^4_1]: https://dashboard.dev2.mybrainguide.org/acquisition/geography/


---

# This page too

I've scraped the "Top Content" page and saved it as a Markdown file . This covers page-level traffic across the site for the last 90 days (May 7 – Aug 4, 2026).[^5_1]

## Content Summary

The site logged **516,480 pageviews** and **174,486 users** across **584 unique pages**, though **430 of those remain unmapped** to a content category. Key sections captured include:[^5_1]

- **Pageviews by Category** — Home dominates at 51.7% of traffic, followed by Result pages (21.5%), Hub pages (10.6%), and Clinical Trials (9.8%)
- **English vs. Spanish** — English content drives 94.5% of pageviews, with Spanish at 5.5%
- **Top Pages** — the homepage leads by far, followed by "Maintain Brain Health 1" and "Clinical Trial Connector" (both in English and Spanish versions), paginated across 4 pages
- **Unmapped Pages** — mostly Spanish-language content pieces and some malformed/duplicated clinical-trials URL slugs that still need to be added to the category mapping file, paginated across 8 pages

Two chart sections ("Pageviews by Category" and "Category Trend (Monthly)") appear as visual elements on the live dashboard rather than extractable table data, so they aren't included in the text export. Let me know if you'd like me to continue through additional Content-section pages, like Clinical Trials or Find a Provider.

<div align="center">⁂</div>

[^5_1]: https://dashboard.dev2.mybrainguide.org/content/top-content/


---

# This page too

I've scraped the "Clinical Trials" page and saved it as a complete Markdown file  — no pagination here, so this capture is fully comprehensive.[^6_1]

## Content Summary

The Clinical Trial Connector logged **50,422 total visits** over the last 90 days, with English (44,450) far outpacing Spanish (5,972). Key findings include:[^6_1]

- **Outbound engagement** — 8,331 total clicks to external trial-matching links, yielding a strong 16.5% click-through rate
- **Click destinations** — nearly all outbound clicks go to careboxhealth.com, split between a general "find a clinical trial" link (71.8%) and a specific investigational drug study for Alzheimer's-related hallucinations and delusions (28.2%)

The "Visits Over Time" section appears as a chart on the live dashboard rather than an extractable data table, so it isn't included in this text export. Let me know if you'd like me to continue through the remaining Content-section pages, such as Find a Provider or Result Pages.

<div align="center">⁂</div>

[^6_1]: https://dashboard.dev2.mybrainguide.org/content/clinical-trials/


---

# This page too

I've scraped the "Find a Provider" page and saved it as a complete Markdown file .[^7_1]

## Content Summary

The Find a Provider tool logged **16,168 total visits** over the last 90 days, overwhelmingly in English (15,974) versus Spanish (194). Key findings include:[^7_1]

- **Outbound engagement** — 1,232 total clicks to external provider-referral links, a 7.6% click-through rate
- **Click destinations** — Medicare.gov leads with nearly half of clicks (49.5%), followed by Isaac Health (33.1%) and Synapticure (17.4%), all connecting users to actual care providers or specialists

I noticed this page's navigation menu also revealed several other Content-section pages (Result Pages, User Journeys, Site Events, Top Content By Demographic) as well as a full Questionnaire section (Results Overview, Journey Explorer, AD8/MIS/SBC Analysis, Result Sharing) — let me know if you'd like me to scrape any of those next.

<div align="center">⁂</div>

[^7_1]: https://dashboard.dev2.mybrainguide.org/content/find-a-provider/


---

# This page too

I've scraped the "Result Pages" page and saved it as a Markdown file .[^8_1]

## Content Summary

Visitors took **3,286 total actions** across **12 active result pages**, spanning **7 distinct action types** in the last 90 days. Key findings include:[^8_1]

- **Save PDF dominates** — the "Self · Not Diagnosed · Good" persona alone drove 1,299 Save PDF actions (65.6% of that page's activity), the single largest action recorded
- **Email opt-ins are strong too** — the same "Good" outcome persona saw 528 email checkbox opt-ins (26.7%)
- **Poor outcomes drive provider lookups** — "Locate a Healthcare Provider" clicks appear more frequently on Poor-outcome pages (e.g., 12.3% for "Someone Else · Not Diagnosed · Poor") than Good-outcome pages, suggesting users with concerning results seek care more actively

The "By Brain Health Indicator" chart and "By Action \& Device" breakdown render as visual charts on the live dashboard rather than extractable tables, so they aren't included in this export. The By Result Page table is paginated (page 1 of 2) — let me know if you'd like the second page captured as well.

<div align="center">⁂</div>

[^8_1]: https://dashboard.dev2.mybrainguide.org/content/result-pages/


---

# This page too

I've scraped the "User Journeys" page and saved it as a Markdown file .[^9_1]

## Content Summary

This page defaults to analyzing the **Home page**, tracking where the **64,626 arriving sessions** go next and where they came from. Since page-flow analysis relies on GA4's raw event export (available only from May 17, 2026 onward), this journey data covers a shorter window than the other dashboard pages.[^9_1]

Key findings for the Home page:

- **High exit rate** — 74.9% of sessions end at Home, though the note clarifies this doesn't equate to GA4's bounce rate, since PDF saves, audio plays, and other on-page actions fire events without a new page load
- **Top next step** — when users don't exit, they most often go to "Maintain Brain Health 1" (15.8% of departures), a Result page
- **Most arrivals are direct** — 89.8% land on Home as their entry point, with the rest arriving from Result and Clinical Trials pages
- **Device differences** — desktop has the lowest exit rate (62.8%) versus tablet (80.2%) and mobile (74.7%), suggesting more engaged desktop sessions

Both the "Where They Go Next" and "How They Arrived" tables are paginated on the live dashboard (5 and 6 pages respectively), so only page 1 of each is captured. Let me know if you'd like me to select a different page (like a Result page) to see what happens after someone gets their brain-health result.

<div align="center">⁂</div>

[^9_1]: https://dashboard.dev2.mybrainguide.org/content/user-journeys/


---

# This page too

I've scraped the "Site Events" page and saved it as a complete Markdown file  — this page had no pagination, so the full event inventory is captured.[^10_1]

## Content Summary

The site tracked **1,760,403 total GA4 events** across **17 distinct event names** between June 6 and August 4, 2026. Key findings include:[^10_1]

- **Questionnaire is the top event** — 676,341 events, nearly 38% of all tracked activity, reflecting the site's core brain-health assessment tool
- **Page views follow** — 493,035 page_view events, the second-most common activity
- **Funnel drop-off is visible** — 47,172 users started the questionnaire (web_questionnaire_start) but only 13,642 finished it (web_questionnaire_finish), roughly a 29% completion rate
- **Engagement signals** — outbound_click (9,563) and click (5,052) events show moderate interaction, while media events (video, file downloads) are comparatively rare

This page's navigation also revealed additional sections you haven't visited yet — Top Content By Demographic, and the full Questionnaire suite (Results Overview, Journey Explorer, AD8/MIS/SBC Analysis, Scoring Reference, Result Sharing) — let me know if you'd like any of those scraped next.

<div align="center">⁂</div>

[^10_1]: https://dashboard.dev2.mybrainguide.org/content/site-events/


---

# This page too

I've scraped the "Top Content by Demographic" page and saved it as a complete Markdown file . Unlike most other pages, this content wasn't truncated, so the full data was captured directly.[^11_1]

## Content Summary

This view isolates the small, self-selected slice of users (**1,964 users, 2,279 sessions**) who answered demographic questions on the questionnaire, tracking what they viewed afterward. Key findings include:[^11_1]

- **Clinical Trials leads** — `/clinical-trials` is the single most-viewed page in this segment (13.8% of pageviews), followed by Find a Provider and two Hub pages on prevention and dementia symptoms
- **Hub content dominates by category** — Hub pages account for 29.1% of pageviews in this segment, followed by Journey (16.7%) and Clinical Trials (15.2%)
- **Race/ethnicity patterns vary sharply by page** — White/Caucasian users show the highest share visiting `/clinical-trials` (18.4%) and `/signs-of-dementia-alzheimers-symptoms` (13.0%), while Asian and "Prefer not to answer" groups over-index on `/find-a-provider` (21.5% and 22.8% respectively)
- **Small-group volatility** — some group/page combinations (like Native Hawaiian/Pacific Islander on prevention or symptom pages) show striking percentages (40-50%) but are based on very small raw counts, so should be read cautiously

The live dashboard's "Compare groups side by side" section lets you pivot by other demographics (gender, age, education) beyond race/ethnicity — let me know if you'd like one of those views captured as well.

<div align="center">⁂</div>

[^11_1]: https://dashboard.dev2.mybrainguide.org/content/top-content-by-demographic/


---

# And this page

I've scraped the "Results Overview" page (questionnaire data) and saved it as a Markdown file .[^12_1]

## Content Summary

For year-to-date 2026, **93,203 questionnaires were started**, with **72,419 receiving a score** — a 77.7% score completion rate. Key findings include:[^12_1]

- **Outcomes skew positive** — 72.0% Good vs. 27.6% Poor brain health outcomes among scored respondents, with MIS as the dominant scoring flow (38,251 Good vs 10,621 Poor)
- **Respondent demographics** — 70.1% female, and the largest age brackets are 65-74 (29.4%) and 75+ (25.1%), consistent with BrainGuide's senior-focused audience; 77.9% identify as White/Caucasian
- **Memory concern behavior** — 35.3% expressed a memory concern and 75.4% specifically wanted an assessment, mostly for themselves (68.1%) rather than someone else (7.4%)
- **Campaign performance** — the largest traffic source has no UTM campaign tagged (83.8% of responses), but tagged campaigns like "go365landing-en" show notably higher Good-outcome rates (83.6%)
- **Monthly trend** — April 2026 saw a massive spike in Started (74,947) and Received Score (20,469) for BrainGuide Standard, roughly 3x a typical month

Two chart-based sections ("Current Period Funnel" for both questionnaires and "Legacy Web Language Breakdown") aren't extracted as tables — the latter shows "No Records" for current filters. The UTM Campaign table is paginated (page 1 of 2); let me know if you'd like the remaining campaigns captured too.

<div align="center">⁂</div>

[^12_1]: https://dashboard.dev2.mybrainguide.org/questionnaire/results/


---

# and this page

I've scraped the "AD8 Analysis" page and saved it as a complete Markdown file  — this page loaded with no pagination, so it's fully comprehensive.[^13_1]

## Content Summary

The AD8 test — completed by caregivers/family members about someone they're concerned about — logged **12,330 completions** with an **average score of 4.17**. Since 2-8 indicates "Poor," the vast majority (82.7%) score in that range, and nearly half (47.4%) hit "High Concern" (5-8).[^13_1]

- **Most-flagged symptoms** — daily thinking/memory problems (71.0% Yes) and judgment/decision-making issues (69.1% Yes) are the top-reported concerns, while forgetting the month/year is least common (25.8% Yes)
- **Respondent patterns** — the caregiver, not the patient, answers this test; 59.4% of respondents are concerned about someone else who isn't yet diagnosed and scores Poor
- **Demographic skew** — Poor outcomes are fairly consistent across gender and race groups (all 80-90%+), but respondents with lower education report notably higher Poor rates (88.7% for less-than-high-school vs. 81.5% for post-graduate)
- **Campaign effect stands out** — the "go365landing-en" campaign shows a dramatically lower Poor rate (38.3%) versus the overall average (82.7%), suggesting a very different, less-concerned audience segment
- **Volume surge** — monthly completions jumped sharply from under 200/month through most of 2024-2025 to over 1,000/month by late 2025 and April 2026 (1,566)

Let me know if you'd like me to continue with the MIS Analysis or SBC Analysis pages next, since those follow in the Questionnaire navigation.

<div align="center">⁂</div>

[^13_1]: https://dashboard.dev2.mybrainguide.org/questionnaire/ad8/


---

# Yes, lets do MIS Analysis first.

I've scraped the "MIS Analysis" page and saved it as a complete Markdown file  — the full page content loaded without truncation this time.[^14_1]

## Content Summary

The Memory Impairment Screen (MIS), a self-administered test, logged **107,976 completions** with an **average score of 6.28**, and **79.7% scored Good** (5-8). Unlike AD8, this is answered only by the person concerned about themselves — 100% "Self."[^14_1]

- **Word set consistency** — all 10 English word sets perform similarly (avg scores 6.13-6.52), suggesting no major difficulty bias between lists; Spanish word sets show smaller sample sizes and more variable, generally lower scores
- **Strong age gradient** — Good outcome rates drop steadily with age, from 89.6% (Under 45) to just 62.5% (75 and Older), the clearest demographic pattern on this page
- **Education correlates with score** — Post-Graduate respondents show the highest Good rate (87.1%) vs. Less than High School (67.6%)
- **Campaign variance** — "bg_in_house_traff_v5_October_30" produced unusually poor outcomes (60.5% Good) compared to the baseline (~80%), while smaller newsletter campaigns like "newsletter_axioslocal_nw_arkansas" show near-perfect Good rates (97.3%)
- **Volume trend** — monthly completions grew from roughly 300-1,000/month in 2024 to over 13,000 in April 2026, mirroring the broader traffic surge seen elsewhere on the dashboard

Ready to move on to SBC Analysis whenever you'd like.

<div align="center">⁂</div>

[^14_1]: https://dashboard.dev2.mybrainguide.org/questionnaire/mis/


---

# Now SBC analysis

I've scraped the "SBC Analysis" page and saved it as a complete Markdown file .[^15_1]

## Content Summary

The Speech Based Cognitive assessment (SBC) is a niche, high-abandonment flow — only **1,751 completions out of 36,803 flow entries**, a **4.8% completion rate**, far lower than AD8 or MIS. Among those who finish:[^15_1]

- **High risk dominates** — 43.0% of scored respondents land in High Risk (score under 0.2), more than Low Risk (31.8%) or Medium Risk (25.2%)
- **Age is the strongest predictor, but inverted from MIS** — younger respondents (Under 45) show much higher High Risk rates (63.4%) than older respondents (75 and Older, 22.7%), likely reflecting speech-test mechanics or self-selection rather than true cognitive risk
- **Education correlates cleanly** — Less than High School shows 78.9% High Risk vs. 28.7% for Post-Graduate, the widest spread of any demographic cut on this page
- **Race/ethnicity gaps are stark** — American Indian/Alaska Native (78.3%) and Native Hawaiian/Pacific Islander (66.7%) show much higher High Risk rates than White/Caucasian (38.0%), though several groups have very small sample sizes
- **Volume stays low and volatile** — monthly completions never exceed ~200, unlike the exponential growth seen in AD8 and MIS, consistent with SBC's low completion rate limiting scale

Since this test has a much smaller sample and highly skewed distributions, per-group figures for smaller cells (like Native Hawaiian/Pacific Islander at n=6) should be read with caution. Let me know if you'd like to continue with Scoring Reference or Result Sharing next.

<div align="center">⁂</div>

[^15_1]: https://dashboard.dev2.mybrainguide.org/questionnaire/sbc/


---

# Let's also do this scoring reference page

I've scraped the "Scoring Reference" page and saved it as a complete Markdown file  — this loaded fully without truncation and serves as the interpretive key for all the questionnaire dashboards you've already reviewed.[^16_1]

## Content Summary

This is a reference/documentation page rather than a metrics page, defining how BrainGuide's three scoring systems map to the 8 user personas and result pages seen throughout the earlier dashboards.[^16_1]

- **Persona structure** — each persona is defined by three axes: Who (Self vs. Someone Else), Diagnosed status, and Brain Health outcome (Good/Poor), replacing legacy first-name labels like "Julia" or "Ben" with descriptive slugs (e.g., self-undx-good)
- **Scoring formulas clarified** — AD8 (0-8, lower=better, informant-administered), MIS (0-8, higher=better, self-administered word recall), and SBC (0-1 continuous, higher=lower risk, speech-based) each have distinct interpretation thresholds
- **The "c" flow type** — explains a previously unmentioned category: users who click "Get Information" without completing a scored assessment, representing ~24% of completions and excluded from score calculations by default — this explains the "Got Information w/o Score" metric seen on the Results Overview page
- **Result URL mapping** — provides the direct crosswalk between the actual page URLs (like /maintain-brain-health-1/) and their persona/outcome meaning, useful for interpreting the Top Content and User Journeys pages you scraped earlier

This page ties together concepts referenced across the AD8, MIS, SBC, and Results Overview pages. Let me know if you'd like to continue with Result Sharing or the Journey Explorer next.

<div align="center">⁂</div>

[^16_1]: https://dashboard.dev2.mybrainguide.org/questionnaire/scoring/


---

# and result sharing

I've scraped the "Result Sharing" page and saved it as a complete Markdown file  — this loaded fully with no truncation.[^17_1]

## Content Summary

Year-to-date 2026, users clicked "Share PDF via Email" **3,113 times**, with only **225 (7.2%) opting in** to be contacted again. No email addresses are ever surfaced in this report — only share/opt-in signals.[^17_1]

- **Good-outcome pages dominate volume** — "Self · Not Diagnosed · Good" (/maintain-brain-health-1/) drives 2,063 shares (66% of all shares), but its opt-in rate is a modest 5.0%
- **Diagnosed users opt in far more** — "Self · Diagnosed · Good" (/understand-next-steps-2/) has a much higher opt-in rate (22.9%) despite far fewer shares (301), suggesting people already navigating a diagnosis are more open to follow-up contact
- **SBC result pages show the highest opt-in rates overall** — Low Risk (30.8%) and High Risk (30.0%) SBC personas both exceed 30%, though on small volumes (13-20 shares each)
- **Go365 shares convert much better** — 21.1% opt-in rate vs. just 5.0% for BrainGuideStandard, despite Go365 having far fewer total shares (422 vs. 2,689)
- **A data anomaly appears** — April through June 2026 show zero "Opted In" despite hundreds of shares each month, which is worth flagging to the data team as a likely tracking gap rather than a genuine behavior shift

This wraps up the Questionnaire section. Let me know if you'd like to continue to the Journey Explorer, or move into the Reference section (Monthly Report Generator, Data \& Mapping Reference).

<div align="center">⁂</div>

[^17_1]: https://dashboard.dev2.mybrainguide.org/questionnaire/sharing/


---

# Same for this page

I've scraped the "Monthly Report Generator" page and saved it as a complete Markdown file . This page is a report-building tool rather than a pure metrics dashboard, currently configured for the July 2026 report month.[^18_1]

## Content Summary

The generator pulls together key headline figures for the selected report month, comparing year-over-year web sessions and questionnaire starts.[^18_1]

- **Year-over-year comparison** — Questionnaire Starts jumped dramatically from 2,314 (Jul 2025) to 25,581 (Jul 2026), an over 10x increase, while Web Sessions for Jul 2026 (1,536) actually appear far lower than Jul 2025 (4,901) — worth double-checking on the live dashboard, as this seems inconsistent with the strong traffic growth seen on other pages
- **Cumulative totals** — 256,338 web sessions and 213,005 questionnaire starts YTD 2026, against all-time totals of 1,331,755 web visitors and 688,964 questionnaire starts
- **Export functionality** — the tool can generate a PowerPoint deck for the selected month, though this requires a local report server (`python3 scripts/report_server.py`) and saves the file to the user's Desktop rather than being downloadable from the dashboard itself

The "Monthly Trends," "Questionnaire Profile (YTD)," and "Demographics (YTD)" sections render as charts on the live dashboard rather than extractable tables, so they aren't captured in this export. Let me know if you'd like to move on to the Data \& Mapping Reference page next.

<div align="center">⁂</div>

[^18_1]: https://dashboard.dev2.mybrainguide.org/reference/report-generator/


---

# And this page

I've scraped the "Data \& Mapping Reference" page and saved it as a complete Markdown file  — this page loaded with full content, no truncation needed.[^19_1]

## Content Summary

This is the technical backbone documentation explaining data freshness, mapping logic, and the underlying BigQuery architecture powering every dashboard page you've reviewed.[^19_1]

- **All sources are current** — every data mart (Core Web Metrics, Geography, Top Content, User Journeys, Outbound Clicks, Traffic Attribution) is up to date as of Aug 4, 2026, with Google Ads and Search Console lagging 2 days and Questionnaire Responses lagging 3 days (loads weekly on Sundays)
- **Mapping files explain earlier "Unmapped" data** — `content_page_map.csv` is the file responsible for the "Unmapped Pages" you saw on the Top Content page; it's flagged as the most frequently updated seed
- **Persona logic confirmed** — `persona_page_map.csv` is the exact source behind the persona structure detailed on the Scoring Reference page, including the legacy first-name labels (Julia, Ben, etc.)
- **Legacy vs. modern data boundaries** — three "frozen" legacy seed files define the pre-2024 weekly/monthly historical data seen on the Site Traffic Overview and Results Overview pages, explicitly warned not to be summed with daily-grain rows
- **Raw table lineage** — GA4's raw event export only actually began 2026-05-17 (correcting an earlier misconception that it started April 30), which explains the "May 17, 2026" cutoffs referenced on the Top Content, User Journeys, and Site Events pages

This effectively closes out the full dashboard tour — you've now covered Acquisition, Content, Questionnaire, and Reference sections. Let me know if you'd like me to combine all these files into a single consolidated report, or if there's a Campaigns section you'd like to explore next.

<div align="center">⁂</div>

[^19_1]: https://dashboard.dev2.mybrainguide.org/reference/data-reference/


---

# Lastly, comprehensively navigate this tool and capture everything into an in-depth MD file.

I've comprehensively navigated the **BrainGuide Questionnaire Explorer** tool across all six tabs (Mind Map, Journey/Drop-off, Analytics, Insights, Scoring \& Personas, and Data \& Uploads) and saved everything into an in-depth Markdown file.

## Content Summary

This tool is a visual/analytical explorer of the questionnaire's internal flow logic, built from **117 nodes, 163 transitions, and 5 flows**, backed by **537,573 warehouse rows** (Nov 6, 2024 – Aug 4, 2026).

**Mind Map** — Visualizes the 5 flows (Intro/A, Myself/MIS, Someone Else/AD8, Speech/SBC, Results/Common) as a node graph, with node size reflecting event volume and edge styles denoting NEXT/CHOICE/cross-flow/inferred-MIS-link relationships. All 87 qCurrent node IDs and their event counts for the selected period are captured.

**Journey/Drop-off** — A funnel builder with 6 preset paths (Intro funnel, MIS full/key-steps, Informant AD8, Speech SBC, Top entry path). The default Intro funnel shows a steep 84% drop at the W-A3-A step, the sharpest decline in the path.

**Analytics** — Full qCurrent event-count table (87 rows) rankable by count/ID, filterable by device/language/campaign, confirming W-A1 (26,221) as the top entry node down to W-S6 (16) as the rarest.

**Insights** — The standout section: lifetime funnel health (514,561 starts, only 34% reach the final demographic step, 2.1% typical per-step loss, but a 98% single-step leak on W-B-AD-9→W-B-AD-10). Nine flagged anomalies include tablet-specific abandonment spikes on SBC/MIS/AD8 screens and stark campaign performance gaps — campaign "6592414342203" converts at just 0.1% vs. a 34% average, while "(organic)" hits 59%.

**Scoring \& Personas** — Documents the exact scoring formulas (MIS = 2×Free Recall + Cued Recall; AD8 lower-is-better; SBC risk bands), the 8-persona mapping table (Ben, Farah, Julia, Carol, Anson, Olivia, Meredith, Nicole) linking scores to result URLs, and SBC's 3-tier result routing.

**Data \& Uploads** — Reveals the tool's technical architecture: it's powered by uploadable flow JSON files (en/es per flow) and a GA4 CSV export (currently 537,573 rows, 128 campaigns, 5 device types), with a reset-to-defaults option.

This completes the full dashboard tour across Acquisition, Content, Questionnaire, Reference, and now the Questionnaire Explorer tool itself.
