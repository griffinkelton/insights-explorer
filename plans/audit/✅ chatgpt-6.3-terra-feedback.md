# GPT-5.6 — Full Codebase Audit

> **Reviewer:** GPT-5.6 (Thinking) on Perplexity
> **Date:** July 30, 2026
> **Project:** Insights Explorer (Streamlit + Google Analytics 4 + Gemini AI)
> **Status:** ✅ ALL 12 BATCHES RECEIVED — Ready for synthesis

---

## Batch Index

| Batch | Status | Key Topics |
|-------|--------|------------|
| 1 | ✅ Received | Dependency manifests, CI inconsistency, session state, config hygiene |
| 2 | ✅ Received | Error boundary exposure, Drive scope, streaming failures, token accounting, OAuth hardening |
| 3 | ✅ Received | Forecasting accuracy, funnel validity, formula injection, export safety, chart error handling |
| 4 | ✅ Received | CSS fragility, Streamlit DOM coupling, accessibility, onboarding accuracy, Google Fonts privacy |
| 5 | ✅ Received | XSS/HTML injection, API telemetry double-count, fabricated context meter, DataFrame truthiness bug, stale state |
| 6 | ✅ Received | Learn page staleness, unsafe security teaching, dangerous pkill, EML converter risks, icon reproducibility |
| 7 | ✅ Received | GA4 pagination/truncation, test suite quality (structural vs behavioral), false test assurances, error disclosure in tests |
| 8 | ✅ Received | Committed Sphinx build artifacts, doc contradictions, unpinned deps, CI vs pre-commit gap, deployment posture |
| 9 | ✅ Received | ⚠️ CRITICAL: committed data artifacts, inaccurate privacy claims, BUGLOG inconsistency, changelog drift, .gitignore gaps |
| 10 | ✅ Received | DataFrame truthiness crash, Clear Data reload bug, summary ignores model, error text exposure, privacy inaccuracy |
| 11 | ✅ Received | DataFrame crash in preview, empty-filter stale data, filtered data inconsistency, funnel UX misleading, chart suppression |
| 12 | ✅ Received | OAuth redirect binding, state file permissions, custom-metric AST allowlist, formula injection, PDF escaping, funnel regex, quality scoring |

---

## Batch 1 — Dependency Manifests, CI, Session State & Config Hygiene

**Overall verdict:** Structurally solid, but has dependency-manifest drift and CI/pre-commit gaps that make clean installs less reliable than the repo suggests. No critical bootstrap vulnerabilities.

### Finding 1: Dependency manifests conflict 🔴 High

Two competing runtime manifests exist:
- Root `requirements.txt` includes runtime + test + asset-generation packages.
- `requirements/base.txt` claims to define runtime deps but omits `google-api-python-client`, `kaleido`, `CairoSVG`, `Pillow`.
- `requirements/dev.txt` extends `base.txt`, so devs and CI can get different environments from users running `pip install -r requirements.txt`.

**Recommendation:** Make `base.txt` the single runtime source of truth. Use `-r` references in both `requirements.txt` and `dev.txt`. Classify every package as runtime, optional-export, or dev-only.

### Finding 2: CI checks differ unnecessarily 🟡 Medium

GitHub Actions runs tests with no coverage. Cloud Build runs tests with coverage but only for `utils` and `pages`. Neither enforces a coverage threshold. Cloud Build comment says "171 tests" — actual count is 359.

**Recommendation:** Pick one authoritative CI system. Run the same command in both if both remain. Use `requirements/dev.txt` in CI. Add `--cov-fail-under`. Add pip caching. Pin GitHub Actions by commit SHA.

### Finding 3: `app.py` owns too much session-state setup 🟡 Medium

`app.py` manually initializes 20+ session keys inline, making it the implicit state schema. Project already has `utils/session.py`.

**Recommendation:** Move defaults into `DEFAULT_SESSION_STATE` dict in `utils/session.py` with an `initialize_session_state()` function using `deepcopy` for mutable defaults.

### Finding 4: Dead `REDIRECT_URI` in `app.py` 🟢 Low

`app.py` reads `OAUTH_REDIRECT_URI` into `REDIRECT_URI` but never uses it. Misleading.

**Recommendation:** Remove the constant or import/use a shared redirect-URI getter from `utils.ga4_client`. Document in `.env.example`.

### Finding 5: `.gitignore` and `.env.example` incomplete 🟢 Low

Missing: `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.coverage`, `htmlcov/`, `.streamlit/secrets.toml`. `.env.example` doesn't document `GEMINI_API_KEY` or `OAUTH_REDIRECT_URI`.

**Recommendation:** Add cache/coverage exclusions to `.gitignore`. Add all non-secret configurable env vars to `.env.example`.

### Finding 6: Pre-commit installability gap 🟢 Low

`pre-commit`, `ruff`, and `black` aren't listed in `requirements/dev.txt`. Add them. Also add `check-added-large-files`, `detect-private-key`, and `check-case-conflict` hooks.

### Recommended sequence
1. Consolidate dependency manifests + add missing dev tooling
2. Standardize GitHub Actions and Cloud Build around one test command
3. Move session-default init behind `utils.session.initialize_session_state()`
4. Remove or centralize unused `REDIRECT_URI`
5. Expand `.gitignore` and `.env.example`
6. Strengthen pre-commit with secret and large-file detection

---

## Batch 2 — Utility Layer: Error Boundary, Drive Scope, Streaming & OAuth

**Overall verdict:** Good separation and a thoughtful OAuth persistence improvement, but four high-priority issues: Drive access is still broader than the remediation narrative suggests, the error boundary exposes sensitive diagnostics, the context meter would measure the wrong thing, and streaming error handling can turn failures into apparent assistant output.

### Finding 1: `drive.readonly` preserves broad Drive access 🔴 High

The recent remediation replaced full `drive` with `drive.readonly` + `drive.file`. But `drive.readonly` still lets the app list and download all the user's Drive files. Google recommends `drive.file` (per-file picker) for apps that don't need to browse the entire Drive.

**Decision required:**
- Keep `drive.readonly` if a built-in Drive browser is a product requirement (but document it honestly).
- Remove `drive.readonly` and use Google Picker + `drive.file` for user-selected files only.
- Remove `drive.readonly` and Drive listing entirely if only app-created exports are needed.

The code comment "minimal blast radius" is materially misleading while `drive.readonly` remains.

### Finding 2: Error cards expose internals and possibly data 🔴 High

`render_error_card()` renders raw exception strings and full stack traces in the UI. This contradicts the README security claim. Raw exceptions can include local paths, library versions, API responses, OAuth details, and user data fragments. An expander is concealment, not access control.

**Fix:** Log full details server-side with a UUID error ID. Show users only a generic message + error ID. Gate debug details behind `SHOW_DEBUG_DETAILS=true` env var.

### Finding 3: Cumulative tokens ≠ context-window usage 🔴 High

`_track_usage()` accumulates tokens across the entire session. This is useful as session telemetry but is being used to drive a "context meter." A model's context window is per-request, not cumulative — adding all prior tokens and dividing by 1M would eventually show full even when each request is tiny.

**Fix:** Use two separate metrics:
- **Session usage:** cumulative counters (already implemented).
- **Context used:** current request's `prompt_token_count` / model's numeric context limit.
Display as: "Current request: 31.4K / 1M context tokens. Session total: 146.2K tokens."

### Finding 4: Streaming failures emitted as normal assistant text 🔴 High

`generate_response_stream()` documents that it raises `RuntimeError` for API failures, but the broad `except` yields `"\n\n⚠️ ..."` as a string. The caller saves it as a legitimate chat response, chart detection runs on it, and the UI can't distinguish failure from answer.

**Fix:** Re-raise as `RuntimeError` so the caller can render an error state. If in-stream messaging is desired, use a structured `StreamEvent` dataclass with `kind: Literal["text", "error"]`.

### Finding 5: Drive XLSX loading doesn't work 🟡 Medium

`load_drive_file_as_df()` always uses `pd.read_csv()`, but the Drive picker can return Excel files. Route by MIME type: Google Sheets → CSV export, XLSX → `pd.read_excel()`, CSV → `pd.read_csv()`, else error.

### Finding 6: OAuth state writes aren't atomic 🟡 Medium

`chmod(0o600)` happens after `write_text()`, leaving a window where permissions depend on umask. Write to a temp file, set permissions, then `os.replace` atomically. Create state directory with `0o700`. Validate redirect_uri match on exchange.

### Finding 7: Token revocation doesn't log HTTP failures 🟡 Medium

`_revoke_token()` catches network exceptions but `requests.post()` doesn't raise on 4xx/5xx. Check `response.ok` and log the status code.

### Finding 8: Scope migration won't flag old broad grants 🟡 Medium

`needs_scope_migration()` uses `issubset()` which tolerates extra scopes. An old broad `drive` token won't be flagged. Add explicit detection of the broad `drive` scope if proactive revocation is desired.

### Finding 9: Prompt sanitization claims are misleading 🟡 Low

`_sanitize_question()` removes code fences and backticks — useful formatting cleanup, but doesn't prevent prompt injection. Rename docstring to "Normalize user question formatting."

### Finding 10: `build_summary_prompt()` cache key issue 🟡 Low

`@st.cache_data` with `quality_report: Any` — Streamlit tries to hash it despite the comment saying it's "not part of cache key." Either make it a serializable dict included in the key, or remove from the cached function.

### Finding 11: `clear_data()` reset boundary ambiguous 🟡 Low

Leaves model selection and token counters untouched. Docstring says it's called on GA4 disconnect but doesn't clear credentials. Document the contract precisely.

### Finding 12: Empty-stream bug in Gemini client 🟡 Low

After streaming loop, `chunk` may be unassigned if Gemini returns empty iterable → `UnboundLocalError`. Track `final_chunk` and only inspect when not None.

### Finding 13: Error classification uses string matching 🟡 Low

`_classify_api_error()` docstring says it uses HTTP status codes, but it does `if "429" in msg`. Prefer `getattr(e, "status_code", None)`.

### Batch 2 action order
1. Gate raw error details behind debug flag + server-side logging
2. Decide Drive scope strategy (browser vs picker vs export-only)
3. Fix streaming error semantics + empty-stream bug
4. Separate context measurement from cumulative tokens
5. Fix Drive XLSX loading + MIME-specific tests
6. Harden OAuth state writes + revocation logging
7. Correct prompt-sanitization language + cache-key handling
8. Add tests for all issues above

---

## Batch 3 — Analytical Layer: Forecasting, Funnels, Charts, Exports & Data Loading

**Overall verdict:** The strongest functional layer with good DataFrame-copy discipline. Main risks are analytical correctness — forecasting over irregular dates, funnel overcounting — and export safety with formula/markup injection.

### Finding 1: Forecasting assumes equally spaced dates 🔴 High

`forecast_metric()` treats row position as time (`np.arange(n)`) instead of actual elapsed days. Data jumping from Jan 1 to Jan 15 is treated as 1 day apart — distorting slope, intervals, and predictions. The module already recognizes date gaps elsewhere. Fix: convert dates to elapsed days from first observation.

### Finding 2: Funnel results aren't conversion funnels 🔴 High

`build_funnel_data()` sums rows where page path *contains* each step pattern — a page-volume sequence, not a conversion funnel. No user/session tracking. Same session can be counted multiple times. Patterns overlap. `str.contains()` treats steps as regex. Rename to "Page-path progression" or add session-level sequencing.

### Finding 3: Spreadsheet formula injection in Excel export 🔴 High

`build_excel_report()` writes raw data, user questions, and AI responses directly to Excel cells. Values starting with `=`, `+`, `-`, `@` can be interpreted as formulas. Prefix with `'` to escape. Apply to all data cells, summary lines, Q&A, data source, and column names.

### Finding 4: Invalid dates grouped before removal 🟡 Medium

`groupby()` on `NaT` works incidentally, but validation belongs *before* aggregation. Convert `metric_col` with `pd.to_numeric()` before summing, drop invalid rows first.

### Finding 5: `pd.eval()` security claim too strong 🟡 Medium

The denylist (`__`, `import`, `exec`, `eval(`, `open(`, `compile`) is brittle, case-sensitive, and incomplete. Use `ast.parse(mode="eval")` with a strict operator/identifier allowlist. Show visible errors when formulas are rejected.

### Finding 6: Upload size policy conflicts 🟡 Medium

Code caps at 100MB, `.streamlit/config.toml` at 200MB, README says 200MB. Effective limit is 100MB. Centralize one limit in a documented constant.

### Finding 7: `charts.py` swallows all exceptions 🟡 Medium

`except Exception: pass` converts every bug into "no chart." Narrow expected exceptions, log unexpected ones separately.

### Finding 8: Chart configuration mostly ignored 🟡 Medium

Only `chart_type` is used from the config dict. Selected metric, dimension, title, and intent are all discarded. Either simplify the signature or expand to a validated schema.

### Finding 9: Confidence labels overstate simple model 🟡 Medium

"Confidence is strong" when R² > 0.7, but R² is in-sample fit, not forecast accuracy. Hand-rolled t-critical approximation (`2.0 + 10.0/n`). Use `scipy.stats.t.ppf()` or label as approximate.

### Finding 10: PDF needs XML/HTML escaping 🟡 Medium

ReportLab Paragraph parses markup. User data containing `&`, `<`, `>` can break formatting. Escape all untrusted text with `xml.sax.saxutils.escape`.

### Finding 11: Export truncation undisclosed 🟡 Medium

Excel: 1,000 rows, 20 summary lines, 200-char questions, 500-char answers. PDF: 1,000-char answers. None of these limits are disclosed. Add prominent notes.

### Finding 12: Markdown report embeds huge base64 PNGs 🟡 Low

Creates unexpectedly large `.md` files, depends on Kaleido. Choose: text-only + linked PNGs, ZIP with assets folder, or HTML as the rich format.

### Finding 13: Commands are prompt templates, not features 🟡 Low

`/funnel`, `/forecast`, `/anomalies`, `/quality` send natural-language templates to Gemini, not deterministic calls to utils functions. Label them as "analysis prompt shortcuts."

### Batch 3 action order
1. Correct forecasting time-axis handling + numeric/date validation + confidence language
2. Rename or redesign funnel to not claim session/user conversion
3. Add Excel formula escaping + PDF text escaping
4. Replace custom-metric denylist with strict expression grammar
5. Stop swallowing unexpected chart exceptions
6. Make export truncation explicit + align file-size limit
7. Decide command shortcut semantics (deterministic vs prompt templates)

---

## Batch 4 — UI Layer: Styles, Onboarding & Accessibility

**Overall verdict:** The onboarding utility is simple and low-risk, but `styles.py` has become a large, fragile, duplicated CSS/JavaScript blob that should be split and made more accessible. The UI polish is impressive, but the styling method treats Streamlit's implementation details as a stable API.

### Finding 1: Custom CSS relies on undocumented Streamlit internals 🔴 High

`styles.py` targets `[data-testid="stSidebar"]`, `[data-testid="stMetric"]`, `.streamlit-expanderHeader`, BaseWeb selectors, and `[class*="css"]` — none guaranteed stable by Streamlit. A version update can silently break theming. Risk amplified by heavy `!important` use. Prefer Streamlit's official theme config, keep custom CSS minimal and scoped to semantic classes you control.

### Finding 2: Global text selectors risk accessibility and widget breakage 🔴 High

Rules like `[data-theme="light"] p, span, div { color: var(--text-primary) }` and `html, body, [class*="css"]` are so broad they can override semantic colors on widgets, error states, disabled controls, and third-party components. Use scoped selectors targeting known app-owned content.

### Finding 3: Onboarding tour doesn't persist completion 🟡 Medium

Tour state is `st.session_state` only — reset on browser refresh. Session-only is fine for privacy, but document it and add a "Don't show again" / "Restart tour" control.

### Finding 4: Tour content overpromises feature behavior 🟡 Medium

Says summary provides "anomalies" (not guaranteed deterministic) and GA4 is "live via Google sign-in" (omits OAuth setup requirements). Use less absolute language.

### Finding 5: CSS is duplicated and difficult to evolve 🟡 Medium

One giant f-string with repeated light-mode rules, duplicate metric styling, and embedded JS. Split into named constants: `BASE_TOKENS_CSS`, `LIGHT_THEME_CSS`, `COMPONENT_CSS`, `LEARN_PAGE_CSS`, `ACCESSIBILITY_CSS`, `KEYBOARD_SHORTCUT_JS`.

### Finding 6: Motion ignores `prefers-reduced-motion` 🟡 Medium

Metrics and hero sections always animate. Add `@media (prefers-reduced-motion: reduce)` with `animation-duration: 0.01ms !important`.

### Finding 7: Google Fonts is an external privacy dependency 🟡 Medium

Imports Inter from `fonts.googleapis.com` — phones home to Google, conflicts with privacy-first README. Self-host or use system fonts.

### Finding 8: Keyboard listener can be registered repeatedly 🟡 Medium

Each Streamlit rerun adds another `keydown` listener. Add `window.__ga4ExplorerShortcutInstalled` guard. Don't hijack Cmd/Ctrl+K when focus is in an editable field.

### Finding 9: Missing `:focus-visible` styles 🟡 Medium

Hover states styled well, but keyboard focus limited to chat input. Add clear focus outlines for buttons, tabs, upload controls, sidebar navigation.

### Finding 10: `unsafe_allow_html=True` acceptable but needs boundary 🟡 Low

CSS/JS is static source-controlled content, so it's reasonable. Validate `theme` against a fixed enum before interpolation. Never interpolate user data.

### Finding 11: Favicon/meta may 404 locally 🟢 Low

Docstring admits injected meta tags may not resolve in local Streamlit. Keep `st.set_page_config(page_icon=...)` as the functional path.

### Finding 12: `render_tour_step()` trusts callers too much 🟢 Low

`TOUR_STEPS[step - 1]` assumes valid 1–3 index. Guard against invalid values from stale session state.

### Batch 4 action order
1. Split and reduce `styles.py`; remove broad `div`/`span`/`[class*="css"]` overrides
2. Add `prefers-reduced-motion`, `:focus-visible`, and contrast testing
3. Guard JS keyboard listener against duplicate registration
4. Remove Google Fonts network dependency or self-host/document it
5. Update onboarding claims + protect invalid tour-state values
6. Define onboarding persistence policy + add restart/dismiss control
7. Add visual-regression checklist for supported Streamlit versions/themes

---

## Batch 5 — UI Components: Chat, Data Preview, Sidebar, Summary & Hero

**Overall verdict:** The component split is a real improvement, but the UI layer has correctness and privacy problems: duplicated API accounting, unsafe HTML interpolation, unscoped session-state caches, and inconsistent error handling. Components should render from controlled state, not mutate or infer too much state during rendering.

### Finding 1: Untrusted content in `unsafe_allow_html=True` 🔴 High

Column names, custom metric names/formulas, model names, funnel step labels, and error messages are f-stringed into HTML with `unsafe_allow_html=True`. A CSV column named with HTML payload or a custom metric with malicious text would execute. Fix: `html.escape()` all dynamic values, or use safe Streamlit primitives (`st.caption()`, `st.code()`, `st.write()`).

### Finding 2: API-call accounting inconsistent and double-counts 🔴 High

`chat.py` increments `api_call_count` before streaming, `gemini_client._track_usage()` increments again after success. Chart retries increment manually. `summary.py` doesn't pre-increment. Result: "API calls this session" is wrong, rate-limit logic unreliable. Centralize all telemetry in the service layer.

### Finding 3: Context meter is fabricated, not measured 🔴 High

`_render_usage_stats()` computes `estimated_prompt_tokens = min(len(df) * len(df.columns) * 2, 500000)` then divides by 1M. This is a DataFrame-shape heuristic — not a token count. Omits system prompt, chat history, column values. Assumes all models have 1M window. Fix: use actual per-request prompt token count from Gemini metadata, divided by the selected model's real context limit. Don't show a meter without real data.

### Finding 4: `df = custom_metrics_df or df` is a runtime bug 🟡 Medium

DataFrames with >1 element raise `ValueError: The truth value of a DataFrame is ambiguous`. Occurs in `chat.py`, `data_preview.py`, and `summary.py`. Fix: `custom_df if custom_df is not None else st.session_state.df`.

### Finding 5: Streaming errors persisted as assistant answers 🟡 Medium

Error strings get saved into `entry["response"]`, fed to later prompts, exported to reports. Keep a separate `error` field, render as `st.error()`, exclude from history and exports.

### Finding 6: Chart-extraction retry hidden and unbounded 🟡 Medium

Second Gemini call for nearly every long response, bypasses rate limiting, swallows failures with `except Exception: pass`. Prefer single structured-response contract in first call.

### Finding 7: Filter state mutated during rendering, can go stale 🟡 Medium

`_render_data_filters()` writes `filtered_df` on every render. Loading new data doesn't clear it. Store filter *parameters*, derive filtered DataFrame fresh each render.

### Finding 8: Forecast/funnel cache keys too weak 🟡 Medium

Keyed by `forecast_{metric}_{periods}` — missing dataset identity, date column, filters, custom metrics. Old forecast can render against new data. Reset derived state on data load, or use `data_version` in keys.

### Finding 9: Privacy notice is inaccurate 🟡 Medium

"Data processed in-memory only, not stored" ignores OAuth temp files, Drive metadata, Gemini API data leaving the machine, and free-tier training terms. Rewrite precisely.

### Finding 10: Raw OAuth/API errors leak into sidebar UI 🟡 Medium

`st.error(f"Failed to pull GA4 data: {e}")` etc. Use generic message + logged error ID.

### Finding 11: `REDIRECT_URI` duplicated across modules 🟡 Low

Defined in `sidebar.py`, used from `components/__init__.py`. Move to `utils.ga4_client` as single source of truth.

### Finding 12: Summary generation bypasses rate limiting 🟡 Low

Calls `generate_response()` directly without 2-second guard. Centralize rate limiting in the service layer.

### Finding 13: Export buttons require two clicks 🟡 Low

Generate → rerun → Download. State not persisted so rerun can kill the second button. Store generated exports in session state.

### Finding 14: Error boundary catches too broadly 🟡 Low

Module-name matching to avoid swallowing Streamlit control-flow exceptions is fragile. Log unexpected exceptions before showing generic card.

### Batch 5 action order
1. Replace every dynamic `unsafe_allow_html` interpolation with safe rendering or escaping
2. Fix DataFrame truth-value runtime bug in chat, preview, and summary
3. Centralize Gemini attempt/success/failure telemetry and rate limiting in `gemini_client.py`
4. Replace estimated context percentage with actual per-request prompt-token data (or remove meter)
5. Separate chat/API failure state from assistant response history and exports
6. Reset/version all derived UI state when data, filters, metrics, or source changes
7. Correct privacy language and remove raw exception details from sidebar/callback
8. Move redirect-URI config out of sidebar, standardize Drive/XLSX capability messaging

---

## Batch 6 — Learn Page & Development Scripts

**Overall verdict:** The icon generator is sound, but the Learn page is substantially stale and teaches patterns the codebase has already outgrown. The smoke test is useful but dangerous on shared machines because it can terminate unrelated Streamlit processes.

### Finding 1: Learn page is materially out of date 🔴 High

Describes old monolithic architecture saying `app.py` owns everything — but project now has full component split (`components/chat.py`, `sidebar.py`, `data_preview.py`, etc.). Claims 171 tests (actually 359). References stale line numbers, file locations, and function signatures. Teaches obsolete `st.session_state` OAuth flow instead of current PKCE temp-file persistence. Treat as versioned documentation updated with every architectural change.

### Finding 2: Learn page teaches unsafe security concepts 🔴 High

Says code-fence removal and `SECURITY` prompt instructions make prompt injection "much harder." Batch 2 proved `_sanitize_question()` is formatting cleanup, not security. Also claims Gemini 2.5 Flash is sole model (now has model selector). Claims "every file is documented and tested" — unsubstantiated and likely inaccurate. Replace with honest, bounded statements.

### Finding 3: `pkill -f "streamlit run"` is too broad 🔴 High

Can terminate every Streamlit app under the current user, including unrelated work. Dangerous on shared machines. Fix: track specific PID via `$!` and kill only that process on cleanup. Use dynamic port allocation instead of assuming 8501 is free.

### Finding 4: EML converter operates on committed sensitive files 🟡 Medium

Reads from `email/` directory containing potentially confidential material. Should require explicit `--input-dir` and `--output-dir` arguments. Default output to an ignored directory.

### Finding 5: EML converter has Markdown injection risk 🟡 Medium

Email subjects, headers, and body placed directly into Markdown. Subject starting with `#` or containing markup can alter output structure. Escape Markdown-sensitive characters or use fenced/plain-text sections.

### Finding 6: EML HTML stripping is regex-only 🟡 Low

Can produce malformed text, mishandle nested tags, retain hidden content, lose links. Use `html.parser` or document limitations.

### Finding 7: EML ignores attachments and multipart edge cases 🟡 Low

Only selects first plain/HTML part. Doesn't filter by `Content-Disposition`. Can select unintended body parts in complex emails.

### Finding 8: Icon generator needs reproducibility 🟡 Low

Add `--check` mode to verify committed assets match generated output. Declare CairoSVG/Pillow as dev extras. Handle system-font variance for OG text rendering. Add source-existence check before calling CairoSVG.

### Finding 9: Smoke test checks HTTP status, not app readiness 🟡 Low

Streamlit can return 200 while having rendering errors. Grepping for generic strings like `NameError` can flag harmless log text. Search only for structured `Traceback` patterns. Add grace period after first 200 response.

### Finding 10: Smoke test assumes venv path 🟡 Low

Hardcodes `./venv/bin/activate` while README has users create venv manually and project has multiple dependency manifests. Use `PYTHON_BIN` env var.

### Batch 6 action order
1. Rewrite Learn page to reflect componentized architecture, current OAuth persistence, test suite, model behavior, and features
2. Remove inaccurate prompt-injection claims; teach application-enforced security boundaries
3. Replace global `pkill` with PID-only cleanup and dynamic port allocation
4. Convert EML tool to explicit input/output directories; keep plaintext out of tracked sensitive dirs
5. Add source validation and CI `--check` mode to icon generation
6. Add tests for scripts (EML parsing/escaping, icon-output verification)
7. Add documentation-review item to release checklist

---

## Batch 7 — Test Suite Quality & GA4/Drive Client Deep Dive

**Overall verdict:** The suite provides broad module coverage across 25 test modules, but a meaningful share is structural/string-based testing rather than behavioral verification. The most important product risks are GA4 data truncation, misleading funnel calculations, and error handling that exposes raw exception details.

### Finding 1: GA4 retrieval silently truncates at 100k rows 🔴 High

`pull_ga4_report()` requests one page with `limit=100000`, no `offset` pagination, no warning when limit is reached. High-cardinality reports can silently produce incomplete datasets. Fix: paginate until fewer rows than page size returned, add hard max with explicit truncation warning. Test multiple mocked pages, empty later pages, exact-limit response.

### Finding 2: Test suite is dominantly structural, not behavioral 🔴 High

Tests in `test_chat.py`, `test_data_preview.py`, `test_hero.py`, `test_sidebar.py`, `test_summary.py` rely on source-string assertions (parsing Python syntax, searching for function names, scanning for `on_click=`). These catch regression patterns but don't verify rendering, state changes, or control behavior. Renaming a function breaks tests even when behavior is unchanged. Retain a few static-policy tests for known regressions, make the majority behavior-focused with mocked Streamlit controls.

### Finding 3: `test_session.py` has mock-based false positives 🟡 Medium

Patches `st.session_state` with `MagicMock`, asserts attributes are "not None." Unconfigured MagicMock attributes are themselves mocks — assertions pass regardless of what `clear_data()` does. Fix: use real dict with sentinel values, assert exact identity/value preservation.

### Finding 4: Static analysis scans only `app.py` 🟡 Medium

`on_click` regression check only scans `app.py`, but interaction logic has moved into `components/`. Expand to actual source roots or replace with targeted runtime tests.

### Finding 5: Error boundary tests lock in disclosure behavior 🔴 High (reinforced)

Tests explicitly require raw type/message and stack trace to be rendered — locking the unsafe disclosure into the product. Test that production mode does NOT render raw tracebacks. (Reinforces Batch 2, Finding 2)

### Finding 6: Funnel still not a conversion funnel 🔴 High (reinforced)

`str.contains()` without `regex=False`. Patterns like `(` or `.*` can error or match wildly. Tests reinforce substring matching but don't distinguish approximation from journey-based funnel. (Reinforces Batch 3, Finding 2)

### Finding 7: Forecasting date spacing 🟡 Medium (reinforced)

Still treats irregular dates as evenly spaced via `np.arange(n)`. No reindex to daily calendar. Confidence based only on R². (Reinforces Batch 3, Finding 1)

### Finding 8: OAuth `redirect_uri` not validated on exchange 🟡 Medium (reinforced)

`exchange_code()` accepts caller-provided `redirect_uri` but never compares to stored value. Makes persistence ineffective as integrity check. (Reinforces Batch 2, Finding 6)

### Finding 9: Drive loader is CSV-only 🟡 Medium (reinforced)

Always calls `pd.read_csv()`. XLSX from Drive picker will fail. Route by MIME type/filename extension. (Reinforces Batch 2, Finding 5)

### Batch 7 action order
1. Add GA4 pagination with truncation detection and user-visible warning
2. Shift test suite from structural assertions to behavioral tests with mocked Streamlit controls
3. Fix test_session.py MagicMock false positives with real dict + sentinel values
4. Expand static-analysis scan to `components/`, `utils/`, `pages/`
5. Update error-boundary tests to verify production mode hides tracebacks
6. Add literal-matching and malformed-regex funnel tests
7. Add forecasting tests for missing dates, nonnumeric metrics, constant series
8. Add OAuth redirect_uri validation and tests for URI mismatch, expired state, concurrent attempts

---

## Batch 8 — CI, Documentation & Build Reproducibility

**Overall verdict:** The repository's automation and local security defaults are a credible baseline, but the release process is not reproducible and the documentation is internally inconsistent. The largest maintenance issue is committed Sphinx build output combined with README and documentation-index claims that no longer match the repository.

### Finding 1: Generated Sphinx output committed to repo 🔴 High

Full `docs/_build/` tree is tracked: rendered HTML, static assets, search indexes, `.doctrees`, intersphinx caches, and a ~6MB `environment.pickle`. These are build artifacts, not source — they create noisy diffs, repo bloat, merge conflicts, and risk of stale docs being published. Fix: add `docs/_build/` to `.gitignore`, `git rm -r --cached`, build in CI as artifact or deployment output.

### Finding 2: Documentation claims contradict the repository 🔴 High

README says "194 tests across 9 modules" in one place and "359 tests across 19 modules" in another. Security table says error details are hidden (they're not — Batch 7) and prompt injection is handled by code-block stripping (it isn't — Batch 2). Architecture description shows old monolithic structure. "Everything stays in-memory" wording ignores OAuth temp file persistence. Make README the current operational contract, remove hardcoded counts, add CI check for drift.

### Finding 3: Builds are not reproducible 🔴 High

`requirements.txt` uses broad `>=` minimum versions for everything (Streamlit, pandas, Plotly, Google clients, pytest, CairoSVG, Pillow, OpenPyXL). Clean build today ≠ build next week. No lockfile, hash verification, CI dependency cache, or Python version matrix. Fix: split runtime/dev deps, generate pinned lockfile with hashes, add Dependabot/Renovate.

### Finding 4: Documentation index has broken/stale links 🟡 Medium

Links to removed `🔵 onboarding-tour.md`. Describes completed plans as "partially spec'd" or "deferred." Conflicting completion counts: "37/37 complete" in commit metadata vs "22 done" in index. Add markdown-link checker in CI, delete dead references, normalize plan-status vocabulary.

### Finding 5: CI validates too little vs local pre-commit 🟡 Medium

Pre-commit runs AST checks, YAML validation, Ruff, Black. GitHub Actions only runs pytest. Contributor can skip hooks and merge formatting/lint issues. Cloud Build and GitHub Actions have divergent behavior. Make CI the authoritative gate: add ruff, black --check, sphinx -W, and unified test command.

### Finding 6: Actions and hooks not pinned defensively 🟡 Medium

GitHub Actions referenced by major tags (`@v4`, `@v5`) not immutable commit SHAs. Pre-commit hook revisions are version tags. For a project handling OAuth, Drive, and Gemini credentials, immutable pinning is low-effort defense-in-depth.

### Finding 7: "Local-only" config needs explicit enforcement 🟡 Medium

`address = "localhost"` isn't an access-control boundary for production. A deployment override, reverse proxy, or hosted platform can supersede it. Add separate configs, startup warning when production flag is set but localhost-only assumptions remain, authenticated ingress layer for hosted deployments.

### Finding 8: `requirements.txt` references non-existent `dev.txt` 🟡 Low

Comment says "For development, use `requirements/dev.txt`" but the file layout doesn't match the description. Also includes pytest, CairoSVG, Pillow in the runtime list. Correct the comment, split dependencies by purpose.

### Batch 8 action order
1. Remove `docs/_build/` from tracking, add to `.gitignore`, set up CI doc build
2. Rewrite README to reflect current architecture, test counts, security posture, and privacy model
3. Clean up DOCUMENTATION_INDEX: remove dead links, normalize status vocabulary, add link checker
4. Split deps into runtime/dev, generate pinned lockfile with hashes, add Dependabot
5. Align CI with pre-commit: add ruff, black --check, sphinx -W to workflow
6. Pin GitHub Actions by commit SHA, add pip caching
7. Add explicit deployment guardrails and separate config for hosted vs local
8. Fix `requirements.txt` dev comment

---

## Batch 9 — Data Governance, Privacy Claims & Documentation Integrity

**Overall verdict:** The planning and postmortem culture is unusually strong, but the documentation system is now its own source of operational risk. The public repository also appears to contain real-looking analytics files and email artifacts — a priority data-governance issue.

### Finding 1: Committed data artifacts may contain sensitive material ⚠️ CRITICAL

The public repo includes `email/` with `BrainGuide Q1 2026.xlsx`, `BrainGuide Q2 2026_Updated.xlsx`, `FW_ Clinical Trials Data Q2.eml`, and `Report - BrainGuide 2025_Revised.xlsx`. Even if de-identified, names indicate potentially sensitive healthcare/business material and reveal client/project context. Conflicts with "de-identified GA4 data" and "privacy-first" framing.

**Immediate actions:**
1. Make repo private or remove public access during audit
2. Inspect every binary/email artifact for PII, PHI, credentials, message headers, internal URLs, proprietary metrics
3. Remove sensitive files from current branch AND git history using `git filter-repo`
4. Rotate any exposed secrets
5. Replace with clearly-labeled synthetic fixtures under `tests/fixtures/`
6. Add explicit ignore rules for real input/export artifacts; allowlist `tests/fixtures/**` only

### Finding 2: "In-memory only" claim is now inaccurate 🔴 High

Original spec says uploaded data stays only in `session_state`, never written to disk. OAuth remediation explicitly writes temp JSON files (PKCE material, redirect URI, state) to survive the Google redirect. Blanket claim needs precise qualification distinguishing uploaded analytics data from authentication state. Document: what data goes to Gemini, OAuth state-file location/retention/cleanup, that "not used to train" is a vendor-policy claim linking to Google terms.

### Finding 3: BUGLOG metadata is inconsistent 🔴 High

Says 10 bugs, 8 fixed, 2 pending, "all 4 patterns" CI-gated. But BUG-008 appears after summary, Root Cause Category table omits BUG-008/009/010. Top Patterns says all 4 patterns CI-gated but Rule 7 requires runtime checks and Rule 8 says only statically detectable patterns should be CI-gated. Make structured and machine-checkable (YAML schema per bug, auto-generated summary tables in CI).

### Finding 4: Bug lessons are overstated or misleading 🟡 Medium

BUG-005: "never use `on_click` for >100ms" — overly absolute. BUG-006: `getvalue()` "consumes buffer" — not universally true for `BytesIO`. BUG-007: Streamlit <1.44 "silently ignores `pages.toml`" — unverified. Rewrite all three with precise guidance.

### Finding 5: Changelog blends archival history with live notes 🟡 Medium

Starts with remediation section (359 tests), then historical sections (171/194/228/231/236/239). Future-tense language for completed sprints. `v1.5.0`/`v1.6.0` appended after summary rather than chronologically integrated. Adopt `[Unreleased]` + versioned releases format. Use actual git tags.

### Finding 6: Broken links and retired-file references 🟡 Medium

Multiple docs link to root-level `ENHANCEMENTS.md`, `IMPLEMENTATION_PLAN.md`, plan paths that were reorganized. `IDEAS.md` footer links to old paths. Add markdown-link validation to CI.

### Finding 7: IDEAS.md proposals lack privacy/security design 🟡 Medium

Proposals for shareable URLs (base64 in URL ≠ encryption — leaks through browser history, server logs, referrer headers), Slack webhooks, local-network collaboration, BigQuery execution, real-time alerts. Add required "data-flow and threat-model" section to every enhancement: what data leaves the device, who can access it, how revocable, what's logged/retained.

### Finding 8: `.gitignore` too narrow for current architecture 🟡 Medium

Missing: OAuth temp state files, `docs/_build/`, generated reports, user downloads, Drive exports, coverage output, test caches, alternate credential names. Add: Gitleaks pre-commit secret scanner, CI secret scanning, dependency vulnerability scanning, `SECURITY.md` with private reporting channel, GitHub branch protection rules, a `LICENSE` file.

### Batch 9 action order
1. **IMMEDIATE:** Audit and remove committed data/email artifacts from repo and git history
2. Rewrite privacy documentation to distinguish analytics data from auth state
3. Make BUGLOG structured (YAML schema) with CI-generated summaries
4. Correct overstated bug lessons (BUG-005/006/007)
5. Restructure CHANGELOG as `[Unreleased]` + versioned releases
6. Add markdown-link checker to CI
7. Add data-flow/threat-model requirement to IDEAS.md enhancement process
8. Expand `.gitignore`, add secret scanning, create `SECURITY.md` and `LICENSE`

---

## Batch 10 — Orchestration, State Handling & Workflow Defects

**Overall verdict:** The main orchestration is readable, but several Streamlit-state and DataFrame-handling defects can break normal workflows. Most urgent: invalid DataFrame truth-value checks, inability to reload a cleared file, and inconsistent Gemini model/error behavior between chat and summaries.

### Finding 1: DataFrame truth-value checks will raise at runtime 🔴 High

`df = st.session_state.get("custom_metrics_df") or st.session_state.df` in both `chat.py` and `summary.py`. Populated DataFrame cannot be evaluated as boolean — pandas raises `ValueError`. Once custom metrics exist, chat and summary generation fail before any Gemini call. Fix: `custom_df if custom_df is not None else st.session_state.get("df")`. Add regression tests. (Reinforces B5-F4)

### Finding 2: Clear Data prevents reloading the same upload 🔴 High

`clear_data()` sets `df = None` and `data_cleared = True` but leaves `last_file_id` unchanged. Uploader guard rejects the still-selected file because it's "not new." User must pick a different file to recover. Fix: reset `last_file_id = None` on clear. Test: load file A, clear, reload A successfully.

### Finding 3: Internal/provider error text still exposed 🔴 High

`_classify_api_error()` falls back to `f"Unexpected error: {e}"`. `validate_api_key()` returns `API key rejected: {e}`. Rendered in banners, chat, sidebar, summary. Log privately, return stable contextual messages. (Reinforces B2-F2, B7-F5)

### Finding 4: Privacy message in sidebar is materially inaccurate 🔴 High

"In-memory only," "not stored," "not used to train any model." Data goes to Gemini API, Drive access is supported, exports are generated, OAuth state is written to temp files. Rewrite with precise disclosure linking to Gemini API data-use terms. (Reinforces B5-F9, B9-F2)

### Finding 5: Summary disregards selected AI model 🟡 Medium

Chat uses `selected_model` from session state; `_generate_summary()` calls `generate_response()` without a model argument, always using `DEFAULT_MODEL`. Also doesn't increment `api_call_count`. Pass `selected_model` consistently.

### Finding 6: Streaming failures presented as model output 🟡 Medium

`generate_response_stream()` yields error strings instead of raising. `st.write_stream()` treats as normal text, stores in history, runs chart extraction on it. Raise the classified exception instead. (Reinforces B2-F4)

### Finding 7: Error classification still substring-based 🟡 Medium

`if "429" in str(e)` despite docstring claiming HTTP status codes. Can misclassify unrelated errors. Prefer structured exception status/code attributes. (Reinforces B2-F13)

### Finding 8: Upload identity is too weak 🟡 Medium

Uses `f"{name}-{size}"` as file ID. Two different files with same name+size treated as identical. Hash content: `hashlib.sha256(uploaded_file.getvalue()).hexdigest()`.

### Finding 9: Session initialization scattered across files 🟡 Medium

`app.py` initializes 25+ keys directly. Utilities/components independently create additional keys (funnel, forecast, Drive, custom-metric, tour, comparison, token). Consolidate into `initialize_session_state()` with defaults dict. (Reinforces B1-F3)

### Finding 10: GA4 property IDs unvalidated 🟡 Medium

Accepts arbitrary text, passes to retrieval path. Invalid IDs get remote errors. Validate `property_id.isdigit()` before enabling pull. Disable button while request in progress.

### Finding 11: Custom-metric errors reveal implementation detail 🟡 Medium

Renders `Invalid formula: {e}` exposing pandas parser internals and column details. Return generic message, log diagnostics.

### Finding 12: Chart-extraction retry silent and unbounded 🟡 Medium

Second Gemini call silently ignored on exception, counter incremented only after success, uses prior response as prompt. Surprises users about token usage. Make chart generation explicit opt-in. (Reinforces B5-F6)

### Batch 10 action order
1. Fix DataFrame `or` → explicit `None` check in chat.py, summary.py, data_preview.py
2. Reset `last_file_id` on clear + add reload regression test
3. Pass `selected_model` into summaries + centralize Gemini call accounting
4. Stop displaying raw exceptions; make streamed failures raise RuntimeError
5. Correct privacy notice in sidebar + validate GA4 property IDs
6. Consolidate session-state defaults into single `initialize_session_state()`
7. Strengthen upload identity with content hashing
8. Add behavior-level tests for all fixes above

---

## Batch 11 — Data Preview, Filters, Forecast UI, Funnel UI & Charts

**Overall verdict:** Several user-facing analytics features have state-consistency problems around filtering, forecasts, and funnels. Chart rendering is polished but suppresses failures too broadly and labels approximate analytics more confidently than the implementation supports.

### Finding 1: Data preview repeats the DataFrame boolean crash 🔴 High

`render_data_preview()` uses `custom_metrics_df or st.session_state.df` in two places plus `custom_metrics_df or display_df` in `detect_column_types()`. Custom-metric users crash before preview, badges, filters, or analytics render. Fix with shared `active_dataframe()` helper. (Reinforces B5-F4, B10-F1)

### Finding 2: Empty filters restore stale unfiltered data 🔴 High

When filters return zero rows, `filtered_df = None` is set. Metrics, preview, and components interpret `None` as "no active filter" and fall back to complete DataFrame. User sees empty-result warning while dashboard shows unfiltered values. Fix: keep empty DataFrame as result, render explicit empty state.

### Finding 3: Filtered data not used consistently across analytics 🔴 High

Preview/metrics use `display_df` (potentially filtered). But anomaly detection, forecast, and funnel all receive `base_df = st.session_state.df` — bypassing filters AND custom metrics. User narrows date range, generates forecast that silently uses full dataset. Fix: analytics use the active filtered/augmented dataset, or prominently label raw-data features.

### Finding 4: AI forecast narrative failures silently hidden 🟡 Medium

Catches every exception from `generate_response()` and silently replaces with deterministic summary. Hides API outages, auth failures, rate limits, programming defects. Catch expected errors narrowly, log, render neutral note: "AI commentary temporarily unavailable."

### Finding 5: Forecast cache keys don't identify the data 🟡 Medium

Cached under `forecast_{metric}_{periods}` only — missing file identity, filters, date column, custom metrics. Later upload with same metric name displays old forecast. Use `data_version` counter in keys. (Reinforces B5-F8)

### Finding 6: Forecast wording overstates certainty 🟡 Medium

UI says "Metric Forecast" with "95% prediction intervals" and AI narrative. Underlying model is linear regression without seasonality, backtesting, or irregular date handling. Use "Linear trend projection" with calibrated caveats and model context. (Reinforces B3-F1, B3-F9)

### Finding 7: Funnel UI implies a journey it can't establish 🔴 High

Interface describes "conversion path" and visualizes "drop-off at each step." Underlying analysis is independent page-pattern aggregation, not user/session sequencing. Rename to "Page-path funnel approximation" with visible caveat. Also preserve selected page/metric columns and data version with funnel_data. (Reinforces B3-F2, B7-F6)

### Finding 8: Funnel step handling needs normalization 🟡 Medium

Duplicate detection compares before stripping whitespace. No limit on step count/length. Normalize before comparison, cap at 6-8 steps. Validate dataset has data before calculation.

### Finding 9: `generate_chart()` suppresses every failure 🟡 Medium

`try/except Exception: pass` with no log, no message, no test-visible failure. Catch expected data errors narrowly, log unexpected exceptions. Show note: "A chart could not be generated for this dataset." (Reinforces B3-F7)

### Finding 10: Model chart configuration largely ignored 🟡 Medium

Only uses `chart_config["chart_type"]`, ignores dimension, metric, title, aggregation, question context. "Revenue by campaign" may render as sessions by page. Either simplify contract to "automatic default visualization" or validate constrained config against `df.columns`. (Reinforces B3-F8)

### Finding 11: Chart hover templates malformed 🟢 Low

Labels concatenated without separator: `123Actual`, `95% CI ... Forecast`. Use `<br>` and `<extra></extra>` for clean tooltips. (Reinforces B3-F3)

### Finding 12: Static HTML with `unsafe_allow_html=True` 🟢 Low

Hero and preview use it for spacer markup. Not immediate injection risk (values static) but expands attack surface. Use `st.divider()`, `st.caption()`, or ordinary Markdown. (Reinforces B4-F10, B5-F1)

### Batch 11 action order
1. Fix all DataFrame `or` expressions with shared `active_dataframe()` helper
2. Keep empty filtered DataFrame as result; render explicit empty state
3. Route filtered/augmented DataFrame into anomaly, forecast, and funnel
4. Make forecast narrative failures observable; use narrow exception handling
5. Key forecast/funnel caches with `data_version` + full parameter set
6. Rename funnel to "Page-path funnel approximation" with visible caveat
7. Normalize funnel steps, add limits, validate data before calculation
8. Stop suppressing chart exceptions; log unexpected errors
9. Validate chart config against df.columns; fall back with notification
10. Fix hover templates and replace unnecessary `unsafe_allow_html`

---

## Batch 12 — OAuth Integrity, Custom Metrics, Quality Scoring & Export Safety

**Overall verdict:** The utility layer has solid structure, but contains a serious OAuth state-validation gap, formula-evaluation policy weaknesses, misleading quality/forecast calculations, and export paths that permit spreadsheet/PDF markup injection. Highest priority: securing OAuth callback binding and treating all user/model-supplied text as untrusted in exports and errors.

### Finding 1: OAuth callback doesn't bind to stored redirect URI 🔴 High

`save_oauth_state()` persists PKCE verifier AND `redirect_uri`, but `exchange_code()` ignores the stored value and rebuilds the flow with whatever the caller passes. Defeats the purpose of persisting it. Validate incoming URI against stored one, use stored URI for flow reconstruction.

### Finding 2: OAuth state files inherit unsafe directory permissions 🔴 High

Files chmod'd to `0600` after writing, but directory created with default permissions (could be world-readable). Create with `0o700` before use, write atomically with `NamedTemporaryFile` + `os.replace()`, fail closed if permissions can't be secured.

### Finding 3: Custom metric evaluation needs real AST allowlist 🔴 High

Current denylist (`__`, `import`, `exec`, `eval(`, `open(`, `compile`) is case-sensitive, incomplete — uppercase tokens not caught. Invalid formulas silently skipped. Implement AST-based parser allowing only: numeric literals, column identifiers, arithmetic operators (`+`, `-`, `*`, `/`, `//`, `%`, `**`), parentheses. Return structured per-metric results with visible errors. (Reinforces B3-F5)

### Finding 4: Excel/Sheets exports allow formula injection 🔴 High

Dataset values, questions, summaries, AI responses written directly to cells. Values starting with `=`, `+`, `-`, `@` interpreted as formulas — could make external requests or manipulate workbook. Escape with `'` prefix. Test with `=HYPERLINK(...)` and `@SUM(1+1)`. (Reinforces B3-F3)

### Finding 5: PDF generation passes unescaped text to ReportLab markup 🔴 High

User questions, AI answers, summaries injected into `Paragraph()` without escaping. `<`, `>`, `&` cause malformed documents or markup interpretation. Escape with `xml.sax.saxutils.escape()` at every Paragraph boundary. (Reinforces B3-F10)

### Finding 6: Funnel steps interpreted as regexes, not literals 🔴 High

`str.contains(step.lower())` uses regex by default. `/product?ref=ad`, `.`, `[` in path can error (`re.error`) or match wildly. Use `regex=False` for literal matching. If regex is intentional, make it explicit + validate + cap. (Reinforces B3-F2, B7-F6, B11-F7)

### Finding 7: Forecasting compresses irregular time into sequential observations 🔴 High

`x = 0, 1, ..., n-1` regardless of actual date gaps. Two-week gap = one time step. Reindex to complete daily calendar, use elapsed days from first date. Choose explicit missing-day policy. (Reinforces B3-F1, B7-F7, B11-F6)

### Finding 8: Quality outliers counted per cell, not per row 🟡 Medium

One anomalous row affecting 3 metrics counts as 3 outliers. Build boolean row mask, count unique rows. Also: quality grade penalizes valid GA4 structure (exact duplicate rows, missing expected columns from product-specific schema). Separate file integrity from feature compatibility.

### Finding 9: "95% prediction interval" and confidence labels too strong 🟡 Medium

Hand-rolled t-critical, no validation of distributional assumptions, autocorrelation, seasonality, heteroscedasticity. R² mapped to "strong"/"moderate"/"weak." Call it "approximate model-based interval," show R² as diagnostic not confidence score. Fix zero-slope labeled as "decline." (Reinforces B3-F9)

### Finding 10: OAuth state cleanup is best-effort, not bounded 🟡 Medium

Only runs on save/load, ignores filesystem errors, doesn't verify `created_at` timestamp. Quiet app accumulates abandoned states. Use periodic cleanup, verify both filesystem age and parsed timestamp, set max state-file count.

### Finding 11: File-parser exceptions exposed verbatim 🟡 Medium

`load_file()` returns `Failed to parse file: {str(e)}` exposing pandas/openpyxl internals. Return stable public error, log original. (Reinforces B3-F3)

### Finding 12: DataFrame caching may be costly/fragile 🟡 Medium

`st.cache_data` on DataFrames up to 50k rows; hashing is expensive. Store lightweight values under data-versioned keys.

### Finding 13: Markdown report embeds huge base64 data URIs 🟡 Medium

Chart PNGs as data URIs create huge files, inconsistently supported by Markdown viewers. Prefer ZIP with separate `charts/*.png` or omit from Markdown. (Reinforces B3-F12)

### Batch 12 action order
1. Bind OAuth code exchange to saved redirect URI; secure state store directory atomically
2. Remove raw exception/traceback display from normal users; add debug flag
3. Replace custom-metric denylist with strict AST allowlist + explicit per-metric errors
4. Escape spreadsheet values and PDF/Markdown text before every export
5. Fix literal funnel matching (`regex=False`); relabel as page-pattern aggregate
6. Correct irregular-date forecasting with calendar reindex + elapsed days
7. Separate data integrity from schema-feature compatibility; count outliers by unique row
8. Consolidate local and Drive parsing into one byte-to-DataFrame parser

---

## Final Synthesis & Recommendation — "Fix Before Features"

> **GPT-5.6's closing recommendation:** Pause feature development. Run a focused hardening pass to produce a clean, narrow, defensible `v0.1.0` release. The current `main` branch is not a trustworthy release candidate.

### The Core Diagnosis: Contract Drift

The recurring problem across all 12 batches is not isolated bugs — it's **contract drift**. Product claims, UI labels, implementation details, test counts, and documentation no longer consistently describe the same system. The app evolved from a local CSV prototype into a multi-service system (Gemini, OAuth, GA4, Drive, exports, forecasting, custom expressions, AI charts) without a corresponding upgrade in data-flow design, security controls, release discipline, or user disclosure.

### Release Readiness Assessment

| Use case | Verdict |
|---|---|
| Personal/local experimentation with non-sensitive test data | Reasonable after fixing the currently failing CI run |
| Demonstrations using synthetic data | Reasonable, with forecast/funnel caveats visible |
| Public open-source prototype | Possible after repository-data audit, documentation corrections, and clean CI |
| Real client, healthcare, regulated, or confidential analytics | **Do not use yet** |
| Shared/multi-user deployment | **Do not deploy yet** — redesign auth/session/data isolation first |

### P0: Block Release (must fix before v0.1.0)

1. **Audit and remove sensitive committed artifacts** — email files, spreadsheets, git history scrub, rotate exposed secrets, replace with documented synthetic fixtures
2. **Repair the failing GitHub Actions workflow** — require passing CI before merge to `main`
3. **Fix all DataFrame boolean-context crashes** — `custom_metrics_df or df` → explicit `is not None` checks everywhere
4. **Correct empty-filter behavior** — zero-row filter must not silently revert to full dataset
5. **Secure OAuth state** — bind callback to stored redirect URI, atomic writes, `0o700` directory, bounded cleanup
6. **Escape exports** — formula injection prevention in Excel/Sheets, XML escaping in PDFs, Markdown safety
7. **Stop exposing raw errors to users** — tracebacks, parser internals, provider error text → logged server-side only

### P1: Correct User Trust

8. **Rewrite privacy claims** — replace "in-memory only" / "not stored" / "not used for training" with precise disclosure of Gemini transmission, OAuth temp files, and user-initiated exports/Drive actions
9. **Rename funnel** → "Page-pattern aggregation" unless user/session-level sequencing is implemented
10. **Rename forecast** → "Linear trend projection" with assumptions, data range, and non-validated interval labeling
11. **Make secondary Gemini calls visible** — chart extraction should be included in token/call accounting

### The Data Contract: One Immutable DataContext

The most valuable engineering move: formalize a single `DataContext` dataclass:
- `source_id` (content hash or GA4 fingerprint)
- `version` (incremented on data/filter/metric changes)
- `raw_df` and `active_df` (custom metrics + filters applied)
- `filters` and `provenance`

Require every analysis function to accept `DataContext` explicitly rather than reading arbitrary `st.session_state` keys. Derive every cache key from `source_id` + `version` + parameters. This addresses stale forecast/funnel state, raw-vs-filtered inconsistencies, custom-metric crashes, upload identity collisions, and untestable session initialization.

### Product Boundary Decision

| Direction | Keep | Defer/Remove |
|---|---|---|
| **Local analytics assistant** | CSV/XLSX upload, quality checks, summaries, safe charts, local exports | Drive writing, sharing, webhooks, collaboration, URL state, external APIs |
| **Hosted analytics product** | GA4 OAuth, accounts, managed storage, audited exports | "In-memory only" positioning; anonymous single-session assumptions |

Trying to keep both identities leads to confusing claims and fragile architecture. The local route is much easier to make safe and credible quickly.

### Release Gates for v0.1.0

1. Unit + integration tests pass from clean environment
2. Smoke test: upload, clear/reload, filtered empty state, custom metric, chat failure, summary, export, OAuth callback rejection
3. Static type checking + linting pass
4. Secret scanning + dependency vulnerability scanning pass
5. Markdown link checker + documentation claim verification pass
6. Test that README/UI disclosures match actual data-flow inventory
7. Human release checklist: privacy language, known limitations, changelog, git tag

### Required Documentation

- `SECURITY.md` — reporting instructions, supported deployment assumptions
- `PRIVACY.md` — data-flow diagrams, AI/Google disclosures, retention, exports, OAuth state
- `THREAT_MODEL.md` — local vs hosted usage
- `LICENSE` file matching intended MIT license
- Versioned releases/tags + conventional changelog

### Final Verdict

**"Your strongest next deliverable is not Batch 13 — it is a clean, narrow, defensible v0.1.0 release."**

Make it a local GA4-export analysis tool with explicit AI data transmission, safe exports, accurate analytics language, clean CI, a tested data-context model, and no sensitive repository artifacts. Once that foundation is stable, add GA4/Drive integration and broader features behind a redesigned hosted-product security model.
