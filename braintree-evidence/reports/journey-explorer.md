Based on the active web page you are viewing, here is a synthesis of what the **BrainGuide Questionnaire Explorer** is showing:

### High-Level Summary

This page is an interactive data visualization dashboard designed to map and analyze how users navigate through the "BrainGuide" assessment questionnaire. It provides a visual "Mind Map" of the user journey, tracking hundreds of thousands of events to show exactly where users go, what choices they make, and where they drop off.

### Key Components Visible on the Page:

**1. The "Mind Map" Visualization**

* **User Flows:** The core of the page is a complex, branching diagram showing different paths a user can take. The legend identifies five distinct flows:
* **Intro (A):** The starting point for users.
* **Myself (MIS):** A flow for users taking the assessment for themselves (includes memory, math, and recall tasks).
* **Someone Else (AD8):** A flow for users taking the assessment on behalf of someone else (the AD8 questionnaire).
* **Speech (SBC):** A speech-based assessment flow.
* **Results / Common (C):** The final stages where users receive their results or next steps.


* **Nodes and Connections:** Each dot (node) represents a specific question or stage in the assessment (e.g., "Welcome", "Demographic Questions", "Recall", "Math"). The lines connecting them show the transitions (choices made or next steps taken).
* **Volume Tracking:** The size of the nodes and the numbers attached to them (e.g., "26k", "18k") indicate the volume of users reaching that specific point, allowing analysts to easily spot high-traffic areas and drop-off points.

**2. Data Controls and Filters**
The top navigation bar allows the user to slice the data to get specific insights:

* **Date Range:** Currently set to look at data from July 4, 2026, to August 4, 2026.
* **Demographics & Tech:** Filters for Language (English/Spanish), Device type (Mobile, Tablet, Desktop), and specific marketing Campaigns.
* **Display Toggles:** Options to change the layout (Vertical vs. Horizontal) and toggle visual elements on or off, such as event counts, node text, and specific types of links.

**3. Scope of Data**
The metrics at the top indicate this is a large-scale analysis, currently displaying **117 nodes** and **163 transitions** based on **352,372 events** during the selected month. A note at the bottom indicates the backend has loaded over 537,000 rows of data spanning back to November 2024.

**In short:** This tool allows analysts or product managers to visually audit the performance of their cognitive assessment questionnaire, see which paths are most popular, and identify exactly where users might be abandoning the test.

Based on this new page, you are looking at the **Data & Mapping Reference** document.

While the previous page was a visual analysis tool for product managers, this page is essentially the "under the hood" documentation for the data engineering and analytics team. It serves as a data dictionary and health-monitor for the entire dashboard.

Here is a synthesis of what it tracks:

### 1. Data Freshness & Pipeline Health (Data Source Status)

This section acts as a status monitor for all the data pipelines feeding the dashboard.

* It lists every major dataset (e.g., [Core Web Metrics](https://dashboard.dev2.mybrainguide.org/acquisition/core-web-metrics), [Google Ads](https://dashboard.dev2.mybrainguide.org/reference/data-reference/#data-source-status), Questionnaire Responses).
* It shows exactly when the data was last updated ("Last Date" and "Days Ago") to assure stakeholders that the numbers they are looking at are current.
* It sets expectations for latency (e.g., web traffic lags by 1-2 days, while questionnaire data is loaded in weekly batches).

### 2. Business Logic & Translation (Mapping Files)

Raw data is often messy. This section catalogs the lookup tables (managed as `dbt Seeds` via CSVs) used to translate raw tracking data into the clean categories you see on the dashboard. Examples include:

* **[content_page_map.csv](https://dashboard.dev2.mybrainguide.org/reference/data-reference/#mapping-files-dbt-seeds):** Groups hundreds of individual URLs into 9 clean categories (like "Clinical Trials" or "Find a Provider").
* **source_medium_map.csv:** Translates 73 different raw Google Analytics tracking tags into standard marketing channels (like "Paid Search" or "Display").
* **persona_page_map.csv:** Maps the results of the questionnaire into specific user "personas" (e.g., taking it for themselves vs. someone else, diagnosed vs. undiagnosed).

### 3. Data Architecture & Storage

The bottom half of the page explains exactly where the data lives and how it gets to the dashboard:

* **[Raw Sources](https://dashboard.dev2.mybrainguide.org/reference/data-reference/#raw-bigquery-source-tables):** Documents the raw tables in **Google BigQuery** where data is ingested from Google Analytics 4 (GA4), Google Ads, Google Search Console, and DynamoDB (where the actual questionnaire answers are stored).
* **[dbt Model Layers](https://dashboard.dev2.mybrainguide.org/reference/data-reference/#dbt-model-layers):** Explains the transformation process. It notes that the dashboard (built on Evidence) cannot query the raw data directly. Instead, a tool called `dbt` (data build tool) cleans the raw data in "Staging" views and aggregates it into final "Marts," which are what the dashboard actually reads.

**In short:** This page is a technical health-check and transparency document, ensuring that anyone using the dashboard knows exactly where the numbers come from, how they are calculated, and how up-to-date they are.

You are now viewing the **Analytics** tab of the **BrainGuide Questionnaire Explorer**, specifically focusing on the **qCurrent Event Counts** breakdown.

While the previous tab showed the visual network map, this view provides the exact, underlying event numbers used to quantify user progression and drop-off through each step of the questionnaire.

---

### Key Synthesis & Insights from This View

#### 1. Drop-off & Measurement Methodology

* **What `qCurrent` Measures:** Each `qCurrent` event logs when a user **arrives** at a specific screen via a button click.
* **Inferred Abandonment:** Because there is no explicit "exit" event, drop-off between Step A and Step B is calculated by comparing the volume gap. If 26k users reach Step A but only 21k reach Step B, approximately 4.5k users abandoned the questionnaire while viewing **Screen A**.

#### 2. Funnel Step Volumes (Jul 4 – Aug 4, 2026)

* **Top-of-Funnel Entry (`W-A1`):** **26,221 users** started the initial landing step.
* **Initial Funnel Attrition:**
* **`W-A1` $\rightarrow$ `W-A2`:** Volume drops to **21,734** (~17% drop-off).
* **`W-A2` $\rightarrow$ `W-A5-A`:** Volume drops to **17,903** (~17.6% drop-off).
* **`W-A5-A` $\rightarrow$ `W-A3-B`:** Volume drops sharply to **9,327** (~48% drop-off), highlighting a major point of friction or exit early in the flow.


* **Core Task Progression (`W-B-MIS` Series):**
* Once users commit to the "Myself" assessment flow (`W-B-MIS-1` at **8,126**), retention stabilizes significantly.
* From step `W-B-MIS-1` down to `W-B-MIS-9` (**6,876**), completion rates remain remarkably high, showing steady user progression across consecutive memory and cognitive tasks.



---

### Dashboard Controls Available in This View

* **Filters & Sort:** You can filter for specific step codes (e.g., `W-B-MIS`), sort by count or step ID, and adjust the display from 25 up to 100 rows or all.
* **Comparison Mode:** The `Compare by` dropdown allows you to segment these counts across **Device**, **Language**, or **Top Campaigns** to see if drop-off spikes on specific screen types or user segments.

Based on the **Insights** view you are currently looking at, this page provides an automated analysis of the questionnaire's drop-off points, highlighting the most severe "leaks" in the user journey between November 2024 and August 2026.

Here is a breakdown of the key data pulled from this page:

### 1. Funnel Health Overview

At a high level, the dashboard summarizes the overall performance of the questionnaire:

* **Total Starts:** 514,561 users started the questionnaire.
* **Completion Rate:** 34% of users reached the final demographic step.
* **Typical Step Loss:** On average, 2.1% of users drop off at any given step.
* **Biggest Leak:** The single worst-performing step sees a massive 98% drop-off.

*(Note on Measurement: The system calculates abandonment by inferring the gap between clicks. If a user reaches Step A but never fires the event for Step B, they are counted as abandoning the questionnaire while viewing Step A).*

### 2. "What Stands Out" (Highest Severity Leaks)

The system flags 9 specific anomalies where abandonment is unusually high compared to the 2.1% baseline. The most critical "HIGH" severity issues are:

* **Informant Flow (AD8):** 98% of users abandon the questionnaire on screen `W-B-AD-9`. Over 19,600 users reached this point, but only 369 continued to the next step.
* **Speech Flow (SBC) - Step S1:** 51% of users abandon on screen `W-S1` (dropping from 35.6k to 17.3k).
* **Speech Flow (SBC) - Step D4-A:** 89% of users abandon on screen `W-D4-A-SBC` (dropping from 16.3k to 1.7k).
* **Device Discrepancy:** Tablet users are struggling significantly on the Speech flow. On screen `W-S1`, 71% of tablet users drop off, compared to only 42% of desktop users.

### 3. Campaign Performance Extremes

The dashboard also automatically surfaces which marketing channels are driving the highest and lowest quality traffic based on completion rates (compared to the 34% average):

* **High Performers:**
* **(organic):** 59% completion rate (41,225 starts).
* **(bg_July2025_ad4):** 57% completion rate (8,138 starts).
* **go365landing-en:** 54% completion rate (18,402 starts).


* **Low Performers:**
* **Campaign "6592414342203":** Almost total failure to convert. Out of 9,325 starts, only **0.1%** finish.
* **Website traffic-Display-October 30:** 13% completion rate (78,601 starts).
* **Website traffic-Display-revamp:** 14% completion rate (20,111 starts).



This view is highly actionable, specifically pointing product managers and engineers to investigate the `W-B-AD-9` and `W-S1` screens to figure out why users are getting stuck or leaving, and to pause or review the severely underperforming ad campaigns.

---

[Say Hello to BrainGuide by UsAgainstAlzheimer's](https://www.youtube.com/watch?v=mxIOs3LYBH0)
This video provides helpful background context on what the BrainGuide platform is and how the questionnaire is intended to be used by the public.

You are currently viewing the **Scoring & Personas** tab of the BrainGuide Questionnaire Explorer. This section acts as the master key for how the platform interprets user answers and decides what resources to show them at the end of the assessment.

Here is a breakdown of the rules and mappings it defines:

### 1. Assessment Scoring Logic

The platform administers three different types of cognitive assessments, each with its own specific math and risk thresholds:

* **MIS (Memory Impairment Screen - Self):** Higher scores are better. It calculates a weighted score based on memory tasks: `(2 × Free Recall correct) + Cued Recall correct`.
* **AD8 (Informant Flow - Someone Else):** Lower scores are better. It measures observed changes (Yes = 1, No = 0). A higher score indicates a higher risk of cognitive decline.
* **SBC (Speech-Based Cognitive Assessment):** Higher scores are better. It stratifies users into three risk bands: Low Risk (>0.5), Medium Risk (0.2–0.5), and High Risk (<0.2).

### 2. The 8 User Personas

Instead of just giving users a raw number, the system categorizes them into one of eight distinct "Personas." This mapping dictates the specific results page and tone they receive. It breaks users down by **Who** they are taking it for, their **Score**, and inferred **Brain Health** (Good vs. Poor):

* **Self-Takers:**
* **Ben:** Experiencing memory problems (Poor health / Low score).
* **Carol:** Recently diagnosed with Alzheimer's (Poor health).
* **Julia:** "Worried well" – actively protecting brain health (Good health / High score).
* **Meredith:** Actively learning how to live with Alzheimer's (Good health / High score).
* **Nicole:** "Worried well" – concerned about a diagnosed mother (Good health).


* **Caregivers / Taking for Someone Else:**
* **Farah:** Active care partner for an Alzheimer's patient (Poor health).
* **Anson:** Emerging caregiver, starting from zero (Poor health).
* **Olivia:** Concerned about a recently diagnosed mother (Good health / Low AD8 score).



### 3. Speech (SBC) Result Routing

Finally, the page outlines the specific URL routing for the Speech-Based assessment. Depending on the decimal score output, users are automatically directed to tailored next-step pages:

* `/navigate-next-steps-1` (Low risk)
* `/navigate-next-steps-2` (Medium risk)
* `/navigate-next-steps-3` (High risk)

**In short:** This tab translates raw tracking events and questionnaire clicks into human-centric profiles, ensuring analysts understand exactly why a user was sent to a specific customized result page.

Based on the **Data & Uploads** tab you are currently viewing, this section serves as the administrative backend for the Questionnaire Explorer. It allows data analysts or engineers to manually upload and update the underlying logic and analytics data that power all the other visual tabs (like the Mind Map and Drop-off views).

Here is a synthesis of what this tab manages:

### 1. Flow Code Files (Questionnaire Logic)

This section controls the structural mapping of the questionnaire.

* **How it works:** If the product team changes the questions, adds new paths, or translates the flow, they upload new JSON configuration files here (`en.json` for English, `es.json` for Spanish).
* **Current Flows:** It shows that the tool is currently tracking five distinct flows based on these files: Intro (`flow-a`), Myself (`flow-mis`), Someone Else (`flow-ad8`), Speech (`flow-sbc`), and Results/Common (`flow-c`). Once uploaded, these files instantly rebuild the visual "Mind Map" on the first tab.

### 2. Google Analytics (GA4) Export Data

This is where the actual user volume and drop-off numbers are fed into the dashboard.

* **Preferred Format:** The system requests a specific GA4 CSV export that breaks down "Event count" by four dimensions: Campaign, Device category, Language, and `qCurrent` (the specific questionnaire step).
* **Current Load Status:** The dashboard has successfully auto-detected and loaded a massive dataset containing **537,573 rows** of data, spanning from November 2024 to August 2026. It encompasses 128 different marketing campaigns across all major devices and both English and Spanish languages.

### 3. Top Campaigns Snapshot

To verify the data has loaded correctly, it provides a preview table of the highest-volume traffic sources driving events:

* **Performance Max-2:** Leading by a wide margin with ~2.8 million events.
* **(organic):** The second highest driver with ~1 million events.
* **Search Test 1:** Closely following organic traffic with ~1 million events.
* Other notable drivers include display campaigns, "go365landing-en", and direct traffic.

### 4. System Reset

At the bottom, there is a **Reset** function. If an uploaded CSV or JSON file breaks the visualization, this button quickly clears any manual uploads and safely reverts the dashboard back to the embedded, default data stored in the data warehouse.
