# Site Traffic Overview

Source: https://dashboard.dev2.mybrainguide.org/acquisition/core-web-metrics/

## Data Availability

| Period | Source | Grain | Users · Sessions · Pageviews | Pages/Session · % New/Returning · Bounce Rate | Avg. Session Duration · Engagement Time |
|---|---|---|---|---|---|
| Mar 2021 – Oct 2024 | Legacy spreadsheet | Monthly | ✓ | ✓ | — |
| Nov 2024 – present | GA4 Data API (Pull 3c) | Monthly | ✓ | ✓ | ✓ |
| Nov 6, 2024 – May 16, 2026 | GA4 Data API backfill | Daily | ✓ | ✓ | ✓ |
| May 17, 2026 – present | GA4 raw event export | Daily | ✓ | ✓ | ✓ |

Engagement metrics for the raw-export period (May 17, 2026+) are reconstructed from raw events (`session_engaged`, `engagement_time_msec`, session timestamps), matching GA4's definitions.

Date range selected: Mar 1, 2021 – Aug 4, 2026 (All Time)

## Combined Totals — All Sources

All data sources combined for the selected period. The grain adapts to the range: ranges that start on/after Nov 6, 2024 use daily GA4 data (exact for any window, including partial months); ranges reaching further back use monthly dedup (spreadsheet Mar 2021–Oct 2024 + GA4 API monthly pull), which matches GA4 UI unique-user counts across full history. Note: on daily grain, Sessions/Pageviews/engagement are exact, while Web Users can slightly overcount over long windows (a user active on multiple days counts once per day).

| Metric | Value |
|---|---|
| Web Users | 1,331,755 |
| Web Sessions | 1,695,800 |
| Pageviews | 2,748,879 |
| Pages / Session | 1.6 |
| New Visitors | 1,213,595 |
| Returning Visitors | 133,171 |
| New Visitors % | 91.1% |
| Returning Visitors % | 10.0% |
| Bounce Rate | 47.0% |
| Engagement Rate | 26.8% |
| Avg. Session Duration (min) | 3.1 |
| Avg. Engagement Time (min) | 1.6 |

## Daily Metrics (GA4)

Daily GA4 data only for the selected period.

| Metric | Value |
|---|---|
| Web Users | 677,506 |
| Web Sessions | 715,753 |
| Pageviews | 1,527,756 |
| Pages / Session | 2.1 |
| New Visitors | 622,773 |
| Returning Visitors | 54,733 |
| New Visitors % | 91.9% |
| Returning Visitors % | 8.1% |
| Bounce Rate | 30.2% |
| Engagement Rate | 69.8% |
| Avg. Session Duration (min) | 3.1 |
| Avg. Engagement Time (min) | 1.6 |

### Chart Sections (links on page)
- Users & Sessions
- Pageviews & Pages per Session
- New vs. Returning Visitors
- Session Quality

## Daily Data Table (most recent page shown)

| Date | Users | Sessions | Pageviews | Pg/Session | New | Returning | New % | Ret. % | Bounce | Eng. Rate | Avg. Dur. (min) | Eng. Time (min) | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-04 | 4,873 | 5,352 | 14,032 | 2.6 | 4,140 | 733 | 85.0% | 15.0% | 34.4% | 65.6% | 3.6 | 0.7 | raw_export |
| 2026-08-03 | 4,587 | 5,031 | 14,698 | 2.9 | 3,895 | 692 | 84.9% | 15.1% | 33.5% | 66.5% | 3.8 | 0.7 | raw_export |
| 2026-08-02 | 4,478 | 4,866 | 13,050 | 2.7 | 3,867 | 611 | 86.4% | 13.6% | 34.7% | 65.3% | 3.7 | 0.6 | raw_export |
| 2026-08-01 | 5,203 | 5,700 | 14,419 | 2.5 | 4,566 | 637 | 87.8% | 12.2% | 34.9% | 65.1% | 3.1 | 0.6 | raw_export |
| 2026-07-31 | 4,614 | 4,977 | 12,656 | 2.5 | 4,068 | 546 | 88.2% | 11.8% | 35.2% | 64.8% | 3.6 | 0.6 | raw_export |
| 2026-07-30 | 4,554 | 5,026 | 11,758 | 2.3 | 4,009 | 545 | 88.0% | 12.0% | 37.0% | 63.0% | 2.9 | 0.5 | raw_export |
| 2026-07-29 | 4,946 | 5,424 | 12,574 | 2.3 | 4,382 | 564 | 88.6% | 11.4% | 38.1% | 61.9% | 3.0 | 0.5 | raw_export |
| 2026-07-28 | 5,312 | 5,761 | 13,777 | 2.4 | 4,839 | 473 | 91.1% | 8.9% | 36.1% | 63.9% | 2.8 | 0.6 | raw_export |
| 2026-07-27 | 5,121 | 5,509 | 13,755 | 2.5 | 4,641 | 480 | 90.6% | 9.4% | 37.1% | 62.9% | 3.1 | 0.6 | raw_export |
| 2026-07-26 | 4,616 | 5,015 | 11,839 | 2.4 | 4,318 | 298 | 93.5% | 6.5% | 38.0% | 62.0% | 3.3 | 0.6 | raw_export |
| 2026-07-25 | 4,756 | 5,129 | 11,744 | 2.3 | 4,600 | 156 | 96.7% | 3.3% | 39.3% | 60.7% | 2.6 | 0.5 | raw_export |
| 2026-07-24 | 2,256 | 2,359 | 7,265 | 3.1 | 2,108 | 148 | 93.4% | 6.6% | 33.2% | 66.8% | 2.5 | 1.0 | raw_export |
| 2026-07-23 | 2,216 | 2,298 | 7,589 | 3.3 | 2,071 | 145 | 93.5% | 6.5% | 34.8% | 65.2% | 2.6 | 1.1 | raw_export |
| 2026-07-22 | 2,335 | 2,442 | 7,558 | 3.1 | 2,198 | 137 | 94.1% | 5.9% | 32.6% | 67.4% | 2.4 | 1.0 | raw_export |
| 2026-07-21 | 2,819 | 2,944 | 9,365 | 3.2 | 2,678 | 141 | 95.0% | 5.0% | 32.5% | 67.5% | 2.0 | 1.0 | raw_export |
| 2026-07-20 | 2,121 | 2,211 | 6,421 | 2.9 | 2,038 | 83 | 96.1% | 3.9% | 36.3% | 63.7% | 1.7 | 1.0 | raw_export |
| 2026-07-19 | 2,096 | 2,167 | 8,002 | 3.7 | 2,026 | 70 | 96.7% | 3.3% | 32.5% | 67.5% | 2.4 | 1.1 | raw_export |
| 2026-07-18 | 1,681 | 1,740 | 6,330 | 3.6 | 1,611 | 70 | 95.8% | 4.2% | 38.0% | 62.0% | 1.7 | 1.2 | raw_export |
| 2026-07-17 | 1,732 | 1,780 | 6,616 | 3.7 | 1,660 | 72 | 95.8% | 4.2% | 37.3% | 62.7% | 2.0 | 1.1 | raw_export |
| 2026-07-16 | 1,686 | 1,744 | 6,365 | 3.6 | 1,589 | 97 | 94.2% | 5.8% | 35.5% | 64.5% | 2.0 | 1.2 | raw_export |

*(Table paginated: Page 1 of 32 on live dashboard)*

## Historical Monthly (2021 – Present)

Monthly view across full history. Mar 2021–Oct 2024 uses spreadsheet monthly GA4 UI pulls; Nov 2024+ uses the automated GA4 monthly API pull (Pull 3c). All months reflect monthly unique users deduplicated within each month. Engagement metrics available for Nov 2024+.

| Month | Users | Sessions | Pageviews | Pg/Session | New | Returning | New % | Ret. % | Bounce |
|---|---|---|---|---|---|---|---|---|---|
| 2021-03-01 | 42,911 | 56,254 | 75,283 | 1.3 | 36,303 | 6,608 | 84.6% | 15.4% | 81.7% |
| 2021-04-01 | 37,480 | 46,573 | 63,094 | 1.4 | 32,533 | 4,947 | 86.8% | 13.2% | 70.2% |
| 2021-05-01 | 47,343 | 61,171 | 92,357 | 1.5 | 39,815 | 7,528 | 84.1% | 15.9% | 43.1% |
| 2021-06-01 | 50,672 | 64,373 | 100,664 | 1.6 | 43,375 | 7,297 | 85.6% | 14.4% | 46.2% |
| 2021-07-01 | 13,903 | 17,677 | 30,865 | 1.7 | 11,679 | 2,224 | 84.0% | 16.0% | 50.3% |
| 2021-08-01 | 33,184 | 51,016 | 81,714 | 1.6 | 25,552 | 7,632 | 77.0% | 23.0% | 56.5% |
| 2021-09-01 | 25,071 | 37,201 | 59,795 | 1.6 | 19,129 | 5,942 | 76.3% | 23.7% | 54.2% |
| 2021-10-01 | 28,825 | 42,063 | 67,669 | 1.6 | 22,311 | 6,514 | 77.4% | 22.6% | 55.1% |
| 2021-11-01 | 7,840 | 10,851 | 18,287 | 1.7 | 6,303 | 1,537 | 80.4% | 19.6% | 55.6% |
| 2021-12-01 | 3,618 | 5,276 | 9,264 | 1.8 | 2,902 | 716 | 80.2% | 19.8% | 65.1% |
| 2022-01-01 | 4,801 | 6,655 | 14,127 | 2.1 | 3,937 | 864 | 82.0% | 18.0% | 38.0% |
| 2022-02-01 | 2,226 | 3,187 | 6,088 | 1.9 | 1,836 | 412 | 82.5% | 18.5% | 55.6% |
| 2022-03-01 | 1,773 | 2,669 | 6,134 | 2.3 | 1,479 | 300 | 83.4% | 16.9% | 57.2% |
| 2022-04-01 | 2,856 | 3,853 | 7,516 | 2.0 | 2,408 | 448 | 84.3% | 15.7% | 57.7% |
| 2022-05-01 | 14,513 | 19,524 | 32,374 | 1.7 | 12,002 | 2,511 | 82.7% | 17.3% | 52.3% |
| 2022-06-01 | 15,799 | 21,954 | 37,108 | 1.7 | 12,671 | 3,128 | 80.2% | 19.8% | 47.3% |
| 2022-07-01 | 38,537 | 51,542 | 78,913 | 1.5 | 31,793 | 6,744 | 82.5% | 17.5% | 56.9% |
| 2022-08-01 | 42,746 | 60,667 | 87,267 | 1.4 | 33,684 | 9,062 | 78.8% | 21.2% | 65.8% |
| 2022-09-01 | 32,540 | 43,683 | 60,722 | 1.4 | 25,934 | 6,606 | 79.7% | 20.3% | 62.1% |
| 2022-10-01 | 31,068 | 40,568 | 47,956 | 1.2 | 25,507 | 5,561 | 82.1% | 17.9% | 41.1% |

*(Table paginated: Page 1 of 4 on live dashboard)*

## Historical Weekly (2021 – 2024)

Legacy data from the BrainGuide KPI tracking spreadsheet. Engagement time metrics are not available for this period. New/Returning visitor counts are estimated from user totals × percentage columns.

| Week Start | Week End | Users | Sessions | Pageviews | Pg/Session | New % | Ret. % | Bounce |
|---|---|---|---|---|---|---|---|---|
| 2021-03-03 | 2021-03-09 | 199 | 301 | 896 | 3.0 | 72.7% | 27.3% | 69.4% |
| 2021-03-07 | 2021-03-13 | 389 | 695 | 2,265 | 3.3 | 74.5% | 25.5% | 64.5% |
| 2021-03-14 | 2021-03-20 | 1,084 | 1,432 | 2,550 | 1.8 | 83.9% | 16.1% | 80.7% |
| 2021-03-21 | 2021-03-27 | 32,550 | 40,589 | 53,501 | 1.3 | 84.6% | 15.4% | 80.2% |
| 2021-03-28 | 2021-04-03 | 17,471 | 21,182 | 25,472 | 1.2 | 81.9% | 18.1% | 87.4% |
| 2021-04-04 | 2021-04-10 | 10,371 | 23,357 | 15,167 | 1.2 | 85.3% | 14.7% | 87.5% |
| 2021-04-11 | 2021-04-17 | 8,358 | 10,014 | 14,963 | 1.5 | 84.4% | 15.6% | 65.6% |
| 2021-04-18 | 2021-04-24 | 8,868 | 10,369 | 14,801 | 1.4 | 86.8% | 13.2% | 51.7% |
| 2021-04-25 | 2021-05-01 | 5,540 | 6,539 | 9,736 | 1.5 | 85.2% | 14.8% | 50.6% |
| 2021-05-02 | 2021-05-08 | 5,745 | 6,775 | 10,025 | 1.5 | 86.3% | 13.7% | 50.4% |
| 2021-05-09 | 2021-05-15 | 6,028 | 7,083 | 10,792 | 1.5 | 86.0% | 14.0% | 53.1% |
| 2021-05-16 | 2021-05-22 | 5,399 | 6,414 | 10,182 | 1.6 | 86.8% | 13.2% | 49.9% |
| 2021-05-23 | 2021-05-29 | 27,944 | 36,812 | 55,084 | 1.5 | 81.9% | 18.1% | 38.1% |
| 2021-05-30 | 2021-06-05 | 9,892 | 12,129 | 19,200 | 1.6 | 83.4% | 16.6% | - |
| 2021-06-06 | 2021-06-12 | 11,945 | 14,503 | 24,049 | 1.2 | 85.4% | 14.6% | - |
| 2021-06-13 | 2021-06-19 | 12,153 | 15,022 | 22,579 | 1.2 | 83.9% | 16.1% | - |
| 2021-06-20 | 2021-06-26 | 14,182 | 17,337 | 26,216 | 1.2 | 83.4% | 16.6% | - |
| 2021-06-27 | 2021-07-03 | 12,312 | 15,013 | 23,543 | 1.2 | 83.4% | 16.6% | - |
| 2021-07-04 | 2021-07-10 | 5,104 | 6,220 | 10,004 | 1.2 | 81.7% | 18.3% | - |
| 2021-07-11 | 2021-07-17 | 1,820 | 2,254 | 4,535 | 2.0 | 84.8% | 15.2% | - |

*(Table paginated: Page 1 of 10 on live dashboard)*
