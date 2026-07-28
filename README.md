# 📊 GA4 Insight Explorer

> Analyze de-identified Google Analytics 4 export data with natural language — powered by Gemini AI.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/streamlit-1.60+-red?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/AI-Gemini%202.5%20Flash-purple?logo=googlegemini" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

---

## ✨ Features

- **📂 Drag & Drop Upload** — CSV or XLSX GA4 exports with graceful column validation
- **🤖 AI Summary** — One-click plain-language overview of your entire dataset
- **💬 Natural Language Chat** — Ask questions like *"which pages have the highest drop-off?"*
- **📈 Auto-Chart Generation** — Bar charts, line charts, and tables generated automatically from answers
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

### 4. Launch

```bash
streamlit run app.py
```

Opens at **http://localhost:8501** 🎉

### 5. Run tests

```bash
python -m pytest tests/
```

74 tests covering data loading, prompt construction, chart detection, and Gemini API error handling.

---

## 📁 Project Structure

```
├── app.py                      # Streamlit app (UI + orchestration)
├── utils/
│   ├── __init__.py
│   ├── data_loader.py          # CSV/XLSX parsing, validation, stats
│   ├── gemini_client.py        # Gemini API wrapper (error handling)
│   ├── prompt_templates.py     # Prompt construction + chart detection
│   ├── ga4_client.py           # GA4 live connection (OAuth + Data API)
│   └── styles.py               # Custom CSS + keyboard shortcuts
├── tests/
│   ├── test_data_loader.py
│   ├── test_prompt_templates.py
│   └── test_gemini_client.py
├── .env.example                # API key template
├── requirements.txt            # Python dependencies
├── .gitignore
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
- ✅ No data used to train any AI model
- ✅ Click **Clear Data** to wipe everything instantly

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| AI | Gemini 2.5 Flash (via `google-genai`) |
| Testing | pytest (74 unit tests) |
| Data | Pandas |
| Charts | Plotly |
| Config | python-dotenv |

---

## 📝 License

MIT — experimental prototype, use at your own risk.
