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
