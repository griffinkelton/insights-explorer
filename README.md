# 📊 GA4 Insight Explorer

> Analyze de-identified Google Analytics 4 export data with natural language — powered by Gemini AI.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/streamlit-1.60+-red?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/AI-Gemini%202.5%20Flash-purple?logo=googlegemini" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/tests-194%20passed-success?logo=pytest" alt="194 tests">
  <img src="https://github.com/griffinkelton/insights-explorer/actions/workflows/test.yml/badge.svg" alt="GitHub Actions">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

---

## ✨ Features

- **📂 Drag & Drop Upload** — CSV or XLSX GA4 exports with graceful column validation
- **🔗 GA4 Live Connection** — OAuth sign-in + Analytics Data API for real-time data pulls
- **🤖 AI Summary** — One-click plain-language overview of your entire dataset
- **💬 Natural Language Chat** — Ask questions like *"which pages have the highest drop-off?"*
- **📈 Auto-Chart Generation** — Bar charts, line charts, and tables generated automatically from answers
- **⌨️ Keyboard Shortcuts** — `Cmd/Ctrl+K` to focus the chat input
- **📚 Learn Page** — Interactive Python tutorials at `/learn`
- **🔒 Privacy-First** — Everything stays in-memory; nothing is stored or used for training

---

## 🚀 Quick Start

### 1. Clone & enter the project

```bash
git clone https://github.com/griffinkelton/insights-explorer.git
cd insights-explorer
```

### 2. Set up a virtual environment & install dependencies

```bash
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Add your Gemini API key

```bash
cp .env.example .env
```

Then edit `.env` and paste your key:

```
GEMINI_API_KEY=your_api_key_here
```

> 🔑 **Get a free key in 10 seconds:** [Google AI Studio → Get API Key](https://aistudio.google.com/apikey)

> ⚠️ **Free tier limits:** 1,500 requests/day, 10 requests/min, 250K tokens/min. Google may use free-tier API inputs/outputs to train/improve their models. If you're analyzing sensitive data, consider upgrading to a [paid tier](https://ai.google.dev/pricing). This app processes data in-memory only and does not store anything, but Google's free-tier ToS still applies to API calls.

> 📚 **Learn Page:** Visit `/learn` in the app (click **📚 Learn Python** in the sidebar, or navigate to [http://localhost:8501/learn](http://localhost:8501/learn)) for interactive Python tutorials covering every library and pattern used in the app.

### 4. Launch

```bash
streamlit run app.py
```

Opens at **http://localhost:8501** 🎉

### 5. Run tests

```bash
python -m pytest tests/ --cov=utils --cov=pages --cov-report=term -v
```

194 tests across 9 test modules covering data loading, prompt construction, chart detection, sanitization, Gemini API error handling, OAuth flow, GA4 report pulling, learn page structure, error boundary rendering, data quality scoring, static analysis guards, and app structure.

### Test breakdown

| Module | Tests | Covers |
|---|---|---|
| `test_prompt_templates.py` | 58 | `build_summary_prompt`, `build_chat_prompt`, `_sanitize_question`, `detect_chart_request` |
| `test_app.py` | 23 | Syntax, imports, structure, session state (app.py structural tests) |
| `test_data_loader.py` | 20 | `load_file`, `validate_columns`, `get_dataset_stats` |
| `test_ga4_client.py` | 18 | `get_auth_url`, `exchange_code`, credentials serialization, `pull_ga4_report` |
| `test_data_quality.py` | 18 | Grade calculation, edge cases, `assess_data_quality` |
| `test_learn_page.py` | 19 | Syntax, structure, tab content, stale detection |
| `test_gemini_client.py` | 14 | `generate_response`, `validate_api_key` |
| `test_error_boundary.py` | 14 | `render_error_card` rendering scenarios |
| `test_static_analysis.py` | 10 | All 4 BUGLOG patterns CI-gated: def-before-call, file I/O, Streamlit guard, on_click |
| **Total** | **194** | All util modules + pages + app structure + static analysis |

---

## 📁 Project Structure

```
├── app.py                      # Streamlit app (UI + orchestration)
├── pages/
│   └── learn.py                # Interactive Python tutorials (8 topics)
├── utils/
│   ├── __init__.py
│   ├── data_loader.py          # CSV/XLSX parsing, validation, stats
│   ├── gemini_client.py        # Gemini API wrapper (error handling, key validation)
│   ├── prompt_templates.py     # Prompt construction + sanitization + chart detection
│   ├── ga4_client.py           # GA4 live connection (OAuth + Analytics Data API)
│   ├── styles.py               # Custom CSS + favicon meta tags + keyboard shortcuts
│   └── error_boundary.py       # Global error boundary (friendly error cards)
├── assets/
│   ├── icon.svg                # Master SVG icon
│   ├── favicon.ico             # Multi-res browser favicon
│   ├── og-image.png            # Social share preview (1200×630)
│   ├── site.webmanifest        # PWA manifest
│   └── icons/                  # 8 PNG sizes (16–512px)
├── scripts/
│   ├── smoke_test.sh           # Headless startup smoke test
│   └── generate_icons.py       # One-time SVG → PNG/ICO/OG rasterizer
├── tests/
│   ├── test_data_loader.py
│   ├── test_prompt_templates.py
│   ├── test_gemini_client.py
│   ├── test_ga4_client.py
│   ├── test_learn_page.py
│   ├── test_error_boundary.py
│   ├── test_data_quality.py
│   └── test_static_analysis.py
├── .streamlit/
│   └── config.toml             # Secure defaults (headless, XSRF, CORS)
├── cloudbuild.yaml             # CI/CD — auto-run tests on push
├── .env.example                # API key template
├── requirements.txt            # Python dependencies
├── .gitignore
├── BUGLOG.md                   # Structured bug log (8 bugs, patterns, rules)
├── ORIGINAL_SPEC.md            # Initial spec + 26-item compliance checklist
├── ENHANCEMENTS.md             # 37-item enhancement roadmap
├── IMPLEMENTATION_PLAN.md      # 21-item execution blueprint
├── IDEAS.md                    # 25 bonus enhancements + 10 moonshots
├── DOCUMENTATION_INDEX.md      # Central index of all docs
├── ARCHITECTURE.md             # Architecture & design decisions
├── CHANGELOG.md                # Unified change history with commit links
└── README.md
```

---

## 🔗 GA4 Live Connection Setup

Skip the file upload entirely — connect directly to your Google Analytics 4
property via OAuth. This is a one-time setup that takes about 10 minutes.

### What you're setting up

```
┌─────────────────────────────────────────────────────┐
│                  Google Cloud Console               │
│  ┌───────────┐   ┌──────────────┐   ┌────────────┐ │
│  │ 1. Create │ → │ 2. Enable    │ → │ 3. Create  │ │
│  │ Project   │   │ Analytics    │   │ OAuth      │ │
│  │           │   │ Data API     │   │ Client ID  │ │
│  └───────────┘   └──────────────┘   └──────┬─────┘ │
│                                            │        │
│                         4. Download JSON ──┘        │
│                         5. Set redirect URI          │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              Google Analytics (GA4)                 │
│  ┌─────────────────┐   ┌──────────────────────────┐│
│  │ 6. Copy         │   │ 7. Grant test user       ││
│  │ Property ID     │   │ access (if using         ││
│  │ (Admin →        │   │ External user type)      ││
│  │ Property        │   │                          ││
│  │ Settings)       │   │                          ││
│  └─────────────────┘   └──────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

### Step 1: Create a Google Cloud Project

1. Go to **[console.cloud.google.com](https://console.cloud.google.com)**
2. In the top nav bar, click the project dropdown → **New Project**
3. Name it (e.g. `ga4-insight-explorer`) and click **Create**
4. Wait a few seconds for the project to be provisioned. Select it from the
dropdown once it appears.

> 💡 **Already have a project?** Skip this step and select your existing project.

---

### Step 2: Enable the Analytics Data API

1. Go to **[APIs & Services → Library](https://console.cloud.google.com/apis/library)**
2. Search for **"Google Analytics Data API"**
3. Click the result and hit **Enable**

```
Search: "Google Analytics Data API"
┌──────────────────────────────────────────┐
│ Google Analytics Data API                │
│ Google                                       [ ENABLE ]
│ Access report data in Google Analytics   │
└──────────────────────────────────────────┘
```

---

### Step 3: Create OAuth 2.0 Credentials

1. Go to **[APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted to configure the consent screen:
   - Choose **External** user type (unless you're on a Google Workspace org)
   - Click **Create**
   - Fill in:
     - App name: `GA4 Insight Explorer`
     - User support email: your email
     - Developer contact: your email
   - Click **Save and Continue** (skip scopes, skip test users for now)
   - Click **Back to Dashboard**
4. Now create the OAuth client ID:
   - Application type: **Web application**
   - Name: `GA4 Insight Explorer` (or anything)
   - **Authorized redirect URIs** → click **+ ADD URI** → enter:
     ```
     http://localhost:8501
     ```
   - Click **Create**

```
┌──────────────────────────────────────────────────┐
│ Create OAuth client ID                           │
│                                                  │
│ Application type: [Web application  ▾]           │
│ Name: [GA4 Insight Explorer              ]       │
│                                                  │
│ Authorized redirect URIs:                        │
│ ┌──────────────────────────────────────────┐     │
│ │ http://localhost:8501                    │ [×] │
│ └──────────────────────────────────────────┘     │
│ [+ ADD URI]                                      │
│                                                  │
│                        [ CREATE ]                │
└──────────────────────────────────────────────────┘
```

---

### Step 4: Download the Client Secret

1. After creating the OAuth client, a popup shows your **Client ID** and
**Client Secret**. Click **DOWNLOAD JSON**.
2. Rename the downloaded file to `client_secrets.json`
3. Move it to the **project root** (same folder as `app.py`)

```
insights-explorer/
├── app.py
├── client_secrets.json    ← put it here
├── .env
├── ...
```

> 🔒 `client_secrets.json` is in `.gitignore` — it will never be committed.

---

### Step 5: Add Yourself as a Test User

If you chose **External** user type in Step 3, you need to add yourself as
a test user before Google will issue tokens:

1. Go to **[APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)**
2. Scroll to **Test users** → click **+ ADD USERS**
3. Enter your email address → click **Save**

```
┌──────────────────────────────────────────────────┐
│ OAuth consent screen                             │
│                                                  │
│ ...                                              │
│ Test users                                       │
│ ┌──────────────────────────────────────────┐     │
│ │ you@gmail.com                            │ [×] │
│ └──────────────────────────────────────────┘     │
│ [+ ADD USERS]                                    │
│                                                  │
│                        [ SAVE ]                  │
└──────────────────────────────────────────────────┘
```

---

### Step 6: Find Your GA4 Property ID

1. Go to **[analytics.google.com](https://analytics.google.com)**
2. Select the GA4 property you want to analyze
3. Go to **Admin** (gear icon, bottom-left)
4. Under **Property**, click **Property Settings**
5. Copy the **Property ID** (a numeric string like `123456789`)

```
Admin → Property Settings
┌──────────────────────────────────────┐
│ Property Settings                    │
│                                      │
│ Property name: My Website            │
│ Property ID: 123456789  ← copy this │
│ ...                                  │
└──────────────────────────────────────┘
```

> ⚠️ Use the **numeric Property ID**, not the Measurement ID (`G-XXXXXXXXXX`).

---

### Step 7: Launch & Connect

1. Start the app:
   ```bash
   streamlit run app.py
   ```
2. In the sidebar, under **🔗 Google Analytics 4 (Live)**, click
**🔐 Sign in with Google**
3. Grant read-only Analytics access when prompted
4. After redirecting back, enter your **Property ID** and click **📥 Pull Data**

```
┌─ Sidebar ──────────────────────────┐
│                                    │
│ 🔗 Google Analytics 4 (Live)       │
│ ┌──────────────────────────────┐   │
│ │  🔐 Sign in with Google      │   │  ← Step 2
│ └──────────────────────────────┘   │
│                                    │
│  ...after auth...                  │
│                                    │
│ ┌──────────────────────────────┐   │
│ │ GA4 Property ID              │   │  ← Step 4
│ │ [123456789              ]    │   │
│ └──────────────────────────────┘   │
│ ┌──────────┐ ┌────────────────┐   │
│ │ 📥 Pull  │ │ ✕ Disconnect   │   │  ← Step 4
│ │ Data     │ │                │   │
│ └──────────┘ └────────────────┘   │
└────────────────────────────────────┘
```

---

### Troubleshooting

| Problem | Fix |
|---|---|
| "invalid\_grant" or "Bad Request" | Your `client_secrets.json` is malformed. Re-download from GCP. |
| "redirect\_uri\_mismatch" | The redirect URI in GCP doesn't match `http://localhost:8501`. Check Step 3. |
| "access\_denied" or "app not verified" | You're not added as a test user. See Step 5. |
| "Analytics Data API has not been used" | The API isn't enabled. See Step 2. |
| "Property ID not found" | Double-check it's the numeric ID from Step 6, not `G-XXXXXXXXXX`. |
| No data returned | Your property might have no data in the last 90 days. Try a property with active traffic. |

---

## 📋 Expected Data Format

Your GA4 export should include columns like:

| Column | Description |
|---|---|
| `date` | Date of the data point |
| `page_path` | URL path of the page |
| `sessions` | Number of sessions |
| `engagement_rate` | Engagement rate |
| `users` | Number of users |

> Missing columns? No problem — the app warns you and works with whatever you have.

---

## 🔒 Privacy

- ✅ All data processed **in-memory only**
- ✅ Nothing written to disk or any database
- ✅ Click **Clear Data** to wipe everything instantly

> ⚠️ **Google free-tier notice:** When using a free Gemini API key from Google AI Studio, Google may use your API inputs and outputs to train and improve their models. This app itself never stores or trains on your data, but the API calls pass through Google's infrastructure under their [terms of service](https://ai.google.dev/terms). If this is a concern, use a paid API tier or a different LLM provider.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| AI | Gemini 2.5 Flash (via `google-genai`) |
| Auth | OAuth 2.0 + Google Analytics Data API |
| Testing | pytest (171 unit tests across 8 modules) |
| CI/CD | Google Cloud Build (`cloudbuild.yaml`) |
| Data | Pandas |
| Charts | Plotly |
| Config | python-dotenv |

---

## 🔒 Security

| Setting | Value |
|---|---|
| API key | `.env` file, never committed |
| Prompt injection | Code block & backtick stripping + security guardrails |
| Key validation | Startup check with persistent error banner |
| Data storage | In-memory only, wiped on "Clear Data" |
| XSRF | Enabled via `config.toml` |
| CORS | Disabled — localhost only |
| Error details | Hidden — prevents source leakage |
| Max upload | 200 MB capped |

---

## 📚 Learn Page

Visit `/learn` in the app for interactive tutorials covering:

- 🏗️ **Streamlit** — UI framework, session state, chat components
- 🐼 **Pandas** — DataFrames, column validation, date parsing
- 📈 **Plotly** — Line/bar charts, dark theme, chart detection
- 🤖 **Gemini API** — Client init, prompt construction, sanitization
- 🔐 **OAuth + GA4** — Flow diagram, auth URL, code exchange
- 🏷️ **Type Hints** — Python 3.10+ union syntax, project usage
- ⚡ **Caching** — `@st.cache_data` with TTL
- 🧪 **Testing** — pytest structure, mocking patterns, edge cases

---

## 📝 License

MIT — experimental prototype, use at your own risk.

---

## 📖 Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) — Full architecture, design decisions, build log
- [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) — The initial project prompt + 26-item compliance checklist
- [ENHANCEMENTS.md](ENHANCEMENTS.md) — 37-item enhancement roadmap across 7 categories
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — Detailed 21-item execution blueprint with sprint plan
- [IDEAS.md](IDEAS.md) — 25 bonus enhancements + 10 moonshot ideas
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central index of all project documentation
- [BUGLOG.md](BUGLOG.md) — Structured bug log with root causes, fixes, and learnings
- [Learn Page](http://localhost:8501/learn) — Interactive Python tutorials (app must be running)
