# 📊 GA4 Insight Explorer

> Analyze de-identified Google Analytics 4 export data with natural language — powered by Gemini AI.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/streamlit-1.60+-red?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/AI-Gemini%202.5%20Flash-purple?logo=googlegemini" alt="Gemini 2.5 Flash">
  <img src="https://img.shields.io/badge/tests-passing-success?logo=pytest" alt="Tests passing">
  <img src="https://github.com/griffinkelton/insights-explorer/actions/workflows/test.yml/badge.svg" alt="GitHub Actions">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

---

## ✨ Features

- **📂 Drag & Drop Upload** — CSV or XLSX GA4 exports with column validation and data quality scoring
- **📂 Google Drive Import** — Select one CSV, XLSX, or Google Sheets file through Google Picker; the app fetches only the selected file for this import and does not browse or list your Drive
- **🔗 GA4 Live Connection** — OAuth sign-in + Analytics Data API for real-time data pulls with pagination (500k row cap)
- **🤖 AI Summary** — One-click plain-language overview of your entire dataset
- **💬 Natural Language Chat** — Streaming token-by-token responses with conversation memory
- **📈 Chart Generation** — Auto-generated charts with opt-in extraction from AI responses
- **📑 Export** — Download reports as Markdown, Excel, or PDF; export to Google Sheets/Drive
- **📚 Learn Page** — Interactive, analyst-first learning experience at `/learn` with challenges, progressive disclosure, and verification checklists
- **🔒 Privacy-First** — Data processed in session; AI calls sent to Gemini API; exports only when you choose
- **🔐 Security** — [SECURITY.md](SECURITY.md) with full security model documentation

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

> 📚 **Learn Page:** Visit `/learn` in the app for an interactive, analyst-first learning experience — predict, inspect, and verify your way through the app's workflows.

### 4. Build the Drive Picker frontend (optional)

```bash
cd components/drive_picker_component_frontend
npm install && npm run build
cd ../..
```

> If you skip this step, the app runs fine — only the Drive import feature
> is unavailable. The app fails fast with a clear error if the Picker
> component is imported without a built frontend bundle.

### 5. Launch

```bash
streamlit run app.py
```

Opens at **http://localhost:8501** 🎉

### 6. Run tests

```bash
python -m pytest tests/ -v
```

---

## 📁 Project Structure

```
├── app.py                      # App entry point (78 lines — session init + render)
├── pages/
│   └── learn.py                # Interactive analyst-first learning experience
├── components/                 # UI components (extracted from app.py)
│   ├── __init__.py             # Orchestrator: renders all sections
│   ├── sidebar.py              # File upload, GA4 connect, filters, metrics
│   ├── hero.py                 # Empty-state hero card
│   ├── data_preview.py         # Metrics, filters, quality scorecard, forecast, funnel
│   ├── summary.py              # AI-generated dataset summary
│   └── chat.py                 # Chat interface, streaming, chart rendering
├── utils/                      # Shared utilities (no UI)
│   ├── data_loader.py          # CSV/XLSX parsing, validation, quality scoring
│   ├── gemini_client.py        # Gemini API wrapper (key validation, telemetry)
│   ├── prompt_templates.py     # Prompt construction + chart detection
│   ├── ga4_client.py           # GA4 OAuth + Analytics Data API + pagination
│   ├── drive_client.py         # Drive import (Picker-selected file download) + Sheets/Drive exports (drive.file scope)
│   ├── report_exporter.py      # Markdown, Excel, PDF report generation
│   ├── charts.py               # Plotly chart generation (line, bar, forecast, funnel)
│   ├── forecasting.py          # Linear trend projection with prediction intervals
│   ├── funnels.py              # Page-path aggregation (literal matching, capped at 8)
│   ├── commands.py             # Chat command shortcuts (/summary, /top, etc.)
│   ├── onboarding_tour.py      # Browser-persisted onboarding tour (localStorage)
│   ├── session.py              # Session state management (active_dataframe, clear_data)
│   ├── error_boundary.py       # Global error boundary with debug mode
│   ├── sanitize.py             # Formula injection + PDF XML escaping
│   └── styles.py               # Custom CSS + keyboard shortcuts + theme
├── assets/                     # Favicons, icons, PWA manifest
├── tests/                      # Test suite (666+ tests, 0 warnings)
├── .github/workflows/          # GitHub Actions CI (Python + frontend + Playwright)
├── cloudbuild.yaml             # GCP Cloud Build CI
├── requirements/               # base.txt (runtime), dev.txt (dev+test)
├── requirements.txt            # → requirements/base.txt
├── .env.example                # Template with all configurable vars
├── .pre-commit-config.yaml     # Pre-commit hooks (lint, format, secrets, large files)
├── plans/                      # Planning archive (meta, sprints, phases, maintenance, audit)
├── LICENSE                     # MIT
├── SECURITY.md                 # Security policy + model
├── RELEASE_CHECKLIST.md        # v0.3.0 release checklist
├── BUGLOG.md                   # Structured bug history
├── CHANGELOG.md                # Unified change history
├── ARCHITECTURE.md             # Architecture & design decisions
├── IDEAS.md                    # Future enhancement ideas
├── DOCUMENTATION_INDEX.md      # Central docs index
└── README.md
```

---

## 🔗 GA4 Live Connection Setup

See the full GA4 setup guide in the [GA4 Live Connection Setup](README.md#-ga4-live-connection-setup) section.

### OAuth Scopes

- `analytics.readonly` — for GA4 data pulls
- `drive.file` — supports files selected or created through the app; the app does not list, browse, or bulk-read Drive

### Google Drive Import

Select one CSV, XLSX, or Google Sheets file through Google Picker. The app fetches only the selected file for this import; it does not browse or list your Drive. Google Sheets imports use the first sheet exported as CSV.

**Supported formats:** CSV, XLSX, native Google Sheets (first-sheet CSV export).

**Privacy & error model:** No raw API errors, Drive IDs, or Picker metadata are displayed to the user. The server-authoritative filename and MIME type are used for display. Import failure preserves existing data.

**Picker setup:** Requires a Google Cloud project with the Picker API enabled, a Picker API key, and an OAuth 2.0 client ID with `drive.file` scope. See `.streamlit/secrets.example.toml` for the required configuration keys.

**Browser support:** Chrome (macOS, Windows), Safari (macOS), Firefox (macOS, Windows). See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for the full cross-browser acceptance matrix.

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

- ✅ All data processed **in the active session only**
- ✅ AI features send prompt and data context to Google's Gemini API
- ✅ OAuth uses temporary authorization state stored briefly to complete sign-in
- ✅ Exports and Drive actions occur only when you choose them
- ✅ Click **Clear Data** to wipe everything instantly

> ⚠️ **Google free-tier notice:** When using a free Gemini API key from Google AI Studio, Google may use your API inputs and outputs to train and improve their models. This app itself never stores or trains on your data, but the API calls pass through Google's infrastructure under their [terms of service](https://ai.google.dev/terms). If this is a concern, use a paid API tier or a different LLM provider.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| AI | Gemini 2.5 Flash (via `google-genai`) |
| Auth | OAuth 2.0 + Google Analytics Data API |
| Testing | pytest (666+ tests) |
| CI/CD | GitHub Actions + Google Cloud Build |
| Data | Pandas |
| Charts | Plotly |
| Config | python-dotenv |

---

## 🔒 Security

| Setting | Value |
|---|---|
| API key | `.env` file, never committed |
| Error details | Hidden in production — logged server-side with incident IDs |
| Data storage | Session-only, wiped on "Clear Data" |
| OAuth scopes | Least-privilege: `analytics.readonly` + `drive.file` |
| Export safety | Formula injection prevention + PDF XML escaping |
| XSRF | Enabled via `config.toml` |
| CORS | Disabled — localhost only |
| Max upload | 100 MB capped |

See [SECURITY.md](SECURITY.md) for the full security model.

---

## 📝 License

MIT — see [LICENSE](LICENSE).

---

## 📖 Further Reading

- [SECURITY.md](SECURITY.md) — Security policy and model
- [ARCHITECTURE.md](ARCHITECTURE.md) — Full architecture, design decisions, build log
- [ORIGINAL_SPEC.md](ORIGINAL_SPEC.md) — Initial project requirements + 26-item compliance checklist
- [CHANGELOG.md](CHANGELOG.md) — Unified change history
- [BUGLOG.md](BUGLOG.md) — Structured bug log (10 bugs)
- [IDEAS.md](IDEAS.md) — Future enhancement ideas
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central docs index
- [plans/audit/✅ v0.1.0-hardening-spec.md](plans/audit/✅%20v0.1.0-hardening-spec.md) — v0.1.0 hardening implementation spec
- [plans/audit/✅ v0.2.0-closeout.md](plans/audit/✅%20v0.2.0-closeout.md) — v0.2.0 closeout (all 5 phases complete)
- [plans/audit/✅ v0.3.0-phase-1-closeout.md](plans/audit/✅%20v0.3.0-phase-1-closeout.md) — v0.3.0 Phase 1 closeout
- [plans/00-sprints/✅ v0.2.0-implementation-spec.md](plans/00-sprints/✅%20v0.2.0-implementation-spec.md) — v0.2.0 implementation spec
- [plans/00-sprints/🔵 v0.3.0-drive-import-spec.md](plans/00-sprints/🔵%20v0.3.0-drive-import-spec.md) — v0.3.0 Drive Import specification
- [plans/🔵 v0.3.0-drive-import-design.md](plans/🔵%20v0.3.0-drive-import-design.md) — v0.3.0 Drive Import design
