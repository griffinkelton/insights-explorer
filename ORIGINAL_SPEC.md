# 📜 Original Specification — GA4 Insight Explorer

> This is the **initial prompt** that started the entire project. It was given to the AI agent on Day 1 as the complete specification for what to build.
>
> **Date:** July 2026
> **Status:** ✅ Built and significantly expanded upon (see "Evolution Beyond Spec" below)

---

## The Original Prompt

```
Build a Streamlit web app called "GA4 Insight Explorer" for analyzing 
de-identified Google Analytics 4 export data using the Gemini API. 
This is an experimental prototype, so prioritize simplicity and working 
functionality over polish.

TECH STACK:
- Python 3.11+, Streamlit for the UI
- google-generativeai SDK for Gemini API calls
- pandas for data handling
- plotly for charts
- python-dotenv for API key management (never hardcode keys)

PROJECT STRUCTURE:
- app.py (main Streamlit entrypoint)
- utils/data_loader.py (CSV parsing and validation)
- utils/gemini_client.py (Gemini API wrapper)
- utils/prompt_templates.py (prompt construction logic)
- .env.example (placeholder for GEMINI_API_KEY)
- requirements.txt
- README.md (setup and run instructions)

CORE FEATURES:

1. File Upload
   - Sidebar file uploader accepting CSV or XLSX
   - Validate that required columns exist (e.g., date, page_path, 
     sessions, engagement_rate, users) but handle missing columns 
     gracefully with a warning, not a crash
   - Show a preview table (first 10 rows) and basic stats (row count, 
     date range, column list) after upload

2. Data Summary Panel
   - Auto-generate a plain-language summary of the uploaded dataset 
     using Gemini (row count, date range, top pages by sessions, 
     any obvious anomalies like sudden drops)
   - Display this summary in a card/expander above the chat

3. Chat Interface
   - A text input box where the user can ask natural language 
     questions about the uploaded data (e.g., "which pages have the 
     highest drop-off?")
   - On submit, construct a prompt that includes: the user's question, 
     a compact representation of the relevant data (aggregate 
     statistics or a sample, NOT the full raw dataset if it's large), 
     and instructions for Gemini to answer concisely and flag any 
     data limitations (e.g., small sample sizes)
   - Send this to Gemini 2.5 Flash via the API
   - Display the response in a chat-style message thread that 
     persists across multiple questions in the session (use 
     st.session_state)

4. Auto-Chart Generation
   - After each Gemini response, attempt to detect if the answer 
     references a specific metric or comparison that could be 
     visualized (e.g., "sessions over time," "top 5 pages")
   - If so, generate a corresponding Plotly chart (line, bar, or 
     table) below the chat response using the actual uploaded data, 
     not fabricated numbers
   - If no chart is applicable, skip this step silently

5. Session Data Handling (IMPORTANT — privacy requirement)
   - Do NOT persist uploaded data to disk or any database
   - Store the dataframe only in Streamlit's in-memory session_state 
     for the duration of the session
   - Add a "Clear Data" button that wipes the session state and 
     uploaded file from memory
   - Add a visible disclaimer in the sidebar: "Data is processed 
     in-memory only and is not stored or used to train any model."

6. Gemini API Configuration
   - Read GEMINI_API_KEY from environment variable, never hardcode
   - Use the gemini-2.5-flash model by default, exposed as a 
     configurable constant at the top of gemini_client.py so it's 
     easy to swap models later
   - Wrap API calls in try/except with a user-friendly error message 
     if the key is missing or a rate limit is hit
   - Set generation parameters conservatively (temperature 0.3) for 
     more consistent analytical responses

7. Error Handling and Empty States
   - If no file is uploaded, show a friendly placeholder message and 
     disable the chat input
   - If the CSV fails to parse, show a specific error (not a raw 
     Python traceback)

DOCUMENTATION:
- In README.md, include: how to get a free Gemini API key from Google 
  AI Studio, how to install dependencies (pip install -r 
  requirements.txt), how to set the .env file, and how to run the 
  app (streamlit run app.py)
- Add inline comments only where logic is non-obvious (e.g., prompt 
  construction, chart-detection logic)

CONSTRAINTS:
- Do not add authentication, user accounts, or any database — this 
  is a local single-user prototype
- Do not add any analytics/telemetry SDKs to this app itself
- Keep the entire app runnable with a single `streamlit run app.py` 
  command after dependency install
```

---

## 📋 Spec Compliance Checklist

| # | Requirement | Status | Notes |
|---|---|---|---|
| 1 | File upload (CSV/XLSX) | ✅ Done | Accepts both formats via sidebar uploader |
| 2 | Column validation with graceful warnings | ✅ Done | `validate_columns()` returns missing list; warning shown, no crash |
| 3 | Preview table + basic stats | ✅ Done | Metrics row (rows, columns, date range) + expandable preview table |
| 4 | AI data summary panel | ✅ Done | "✨ Generate Summary" button with Gemini API |
| 5 | Summary in card/expander above chat | ✅ Done | `st.container(border=True)` with markdown |
| 6 | Natural language chat interface | ✅ Done | `st.chat_input()` + `st.chat_message()` with thread persistence |
| 7 | Compact data representation in prompts | ✅ Done | `df.head(10)` + `describe()` stats, never full raw data |
| 8 | Gemini 2.5 Flash integration | ✅ Done | Via `google-genai` SDK (migrated from deprecated `google-generativeai`) |
| 9 | Chat message thread persistence | ✅ Done | `st.session_state.chat_history` survives reruns |
| 10 | Auto-chart generation | ✅ Done | Keyword-based chart detection → Plotly line/bar charts |
| 11 | Charts use actual data, not AI fabrication | ✅ Done | All charts built from `df.groupby()` on real DataFrame |
| 12 | No chart when not applicable | ✅ Done | `detect_chart_request()` returns `None` → silent skip |
| 13 | In-memory only (no disk/database) | ✅ Done | All data in `st.session_state`; cleared on demand |
| 14 | "Clear Data" button | ✅ Done | Sidebar button wipes all session state |
| 15 | Privacy disclaimer in sidebar | ✅ Done | "Data is processed in-memory only" card |
| 16 | API key from environment variable | ✅ Done | `python-dotenv` loads `.env` → `os.getenv("GEMINI_API_KEY")` |
| 17 | Model config as constant | ✅ Done | `DEFAULT_MODEL = "gemini-2.5-flash"` in `gemini_client.py` |
| 18 | API error handling (try/except) | ✅ Done | `ValueError` for missing key, `RuntimeError` for rate limits/quota |
| 19 | Conservative generation parameters | ✅ Done | `temperature=0.3`, `max_output_tokens=2048` |
| 20 | Friendly empty state + disable chat input | ✅ Done | Hero section with feature cards; `st.stop()` prevents chat from rendering |
| 21 | Specific CSV parse errors | ✅ Done | `load_file()` returns descriptive error strings |
| 22 | README with setup instructions | ✅ Done | Complete quick start, GA4 OAuth setup guide, learn page docs |
| 23 | Inline comments on non-obvious logic | ✅ Done | Prompt construction, chart detection, sanitization commented |
| 24 | No authentication/user accounts | ✅ Done | Local single-user only |
| 25 | No analytics/telemetry SDKs | ✅ Done | Zero tracking |
| 26 | Single-command run | ✅ Done | `streamlit run app.py` |

**26/26 requirements met.** ✅

---

## 🚀 Evolution Beyond the Original Spec

The project grew significantly beyond the initial prompt. Here's what was added:

| Category | What was added | Why |
|---|---|---|
| **SDK Migration** | `google-generativeai` → `google-genai` | Original SDK was deprecated; migrated to the newer `genai.Client` API |
| **GA4 Live Connection** | OAuth 2.0 + Google Analytics Data API | Users can pull live data directly instead of uploading CSVs |
| **Date Range Selector** | 7/30/90 day presets for GA4 pulls | Control how much data to fetch from the API |
| **Keyboard Shortcuts** | `Cmd/Ctrl+K` to focus chat input | Power-user efficiency |
| **API Key Validation** | Startup check with persistent error banner | Catch bad keys immediately, not on first use |
| **Prompt Injection Hardening** | `_sanitize_question()` + security guardrails | Strip code blocks, backticks, excessive newlines |
| **Global Error Boundary** | `utils/error_boundary.py` | Friendly error cards instead of red Python tracebacks |
| **Secure Config** | `.streamlit/config.toml` | Headless mode, XSRF protection, CORS disabled, 200MB upload cap |
| **CSS Architecture** | `utils/styles.py` with 200+ lines of custom CSS | Dark theme, font imports, component styling, animations |
| **Type Hints** | `X \| None` syntax across all modules | Modern Python 3.10+ annotations for readability |
| **Streamlit Caching** | `@st.cache_data` on 3 functions | 10-min TTL for data functions, 5-min for summary prompts |
| **Learn Page** | `/learn` — 8 interactive Python tutorials | Teach users the code behind the app |
| **CI/CD** | `cloudbuild.yaml` + `scripts/smoke_test.sh` | Auto-run tests on every push; headless boot verification |
| **Test Suite** | 129 unit tests across 5 modules | Data loader, prompts, Gemini client, GA4 client, learn page |
| **Documentation** | `ARCHITECTURE.md`, `ENHANCEMENTS.md` (37 items), `IMPLEMENTATION_PLAN.md` (21 items), `IDEAS.md` (25+10 ideas) | Full architecture, roadmap, and creative exploration |
| **Phase Plans** | `plans/phase5/` — 4 detailed implementation documents | Streaming, theming, component refactor, AI enhancements |

### Project structure then vs now

| Original Spec | Actual Project |
|---|---|
| `app.py` | `app.py` (~400 lines) |
| `utils/data_loader.py` | `utils/data_loader.py` (file limits + filtering planned) |
| `utils/gemini_client.py` | `utils/gemini_client.py` (new SDK + key validation) |
| `utils/prompt_templates.py` | `utils/prompt_templates.py` (sanitization + chart detection) |
| `.env.example` | `.env.example` (GA4 vars added) |
| `requirements.txt` | `requirements.txt` (9 dependencies) |
| `README.md` | `README.md` (GA4 setup guide + learn page docs) |
| — | `pages/learn.py` (8-tab Python tutorial) |
| — | `utils/styles.py` (custom CSS + JS) |
| — | `utils/ga4_client.py` (OAuth + Analytics Data API) |
| — | `utils/error_boundary.py` (global error handling) |
| — | `tests/` (5 files, 129 tests) |
| — | `.streamlit/config.toml` (secure defaults) |
| — | `cloudbuild.yaml` (CI/CD) |
| — | `scripts/smoke_test.sh` (headless boot test) |
| — | `ARCHITECTURE.md`, `ENHANCEMENTS.md`, `IMPLEMENTATION_PLAN.md`, `IDEAS.md` |
| — | `plans/phase5/` (4 detailed implementation docs) |

**Original: 7 files. Current: 24+ files.** The spec asked for "an experimental prototype." It became a production-quality tool with tests, CI/CD, security hardening, live API integration, and an interactive learn page.

---

*This document is preserved for historical reference. It shows what was asked for (26 requirements, all met) and how the project grew organically beyond the initial scope.*
