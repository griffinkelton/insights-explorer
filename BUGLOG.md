# 🐛 Bug Log — GA4 Insight Explorer

> Every bug documented with: what went wrong, the root cause, how it was fixed, and what we learned.
> This is a living document — updated after every error found during development.
>
> **Motto:** *Bugs are tuition. This log is the textbook.*

---

## 📋 Bug Entry Template

```markdown
### BUG-###: [Short descriptive title]

**Date:** YYYY-MM-DD
**Severity:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low
**Found during:** [Development / Code Review / Testing / Production]
**Fixed:** ✅ | 🔲 Pending

**The Problem:**
What happened, observed behavior, error messages, reproduction steps.

**Root Cause:**
Why it happened — the underlying issue, not just the symptom.

**The Fix:**
What code changed. Link to the commit if available.

**How It Was Caught:**
What test, review, or observation caught this. Why didn't earlier checks catch it?

**Learnings:**
- For this project: [specific takeaway]
- For future projects: [general principle]
- Pattern alert: [is this part of a larger pattern?]
```

---

## 🐛 Bugs Found

### BUG-001: Error boundary caught Streamlit control flow exceptions

**Date:** 2026-07-28
**Severity:** 🔴 Critical
**Found during:** Code Review (code-reviewer-deepseek agent)
**Fixed:** ✅

**The Problem:**
After adding the global error boundary (`utils/error_boundary.py`), the empty state (hero page) showed a false error: "😣 Something went wrong while rendering the page." The hero was supposed to show when no data was loaded, but `st.stop()` triggered the error boundary.

Also: `st.rerun()` calls inside chat input handling would trigger false error cards on every chat message.

**Root Cause:**
Streamlit uses Python exceptions for internal control flow. `st.stop()` raises `StreamlitStopException` (or similar) and `st.rerun()` raises a `RerunException` — both inherit from `Exception`. The error boundary's `except Exception as e:` was catching these and treating them as unhandled errors rather than normal Streamlit behavior.

**The Fix:**
Added a guard clause in the `except` block to re-raise any exception whose module starts with `"streamlit"`:

```python
except Exception as e:
    if e.__class__.__module__.startswith("streamlit"):
        raise  # st.stop(), st.rerun() — let Streamlit handle these
    render_error_card(e, context="rendering the page")
```

**How It Was Caught:**
The code-reviewer-deepseek agent flagged this during review of the error boundary implementation. A smoke test would also have caught it (hero page failing to render).

**Learnings:**
- **For this project:** Streamlit's control flow is exception-based. Any `try/except Exception` at the top level MUST exempt Streamlit's internal exceptions. Consider adding a `_is_streamlit_control_flow(e)` helper for clarity.
- **For future projects:** When wrapping a framework's top-level execution in a try/except, audit what exceptions the framework uses internally. Many frameworks (Django, Flask, Streamlit) use exceptions for control flow, not just error handling.
- **Pattern alert:** This is part of a larger pattern — generic `except Exception` is dangerous at the top level. Always be specific about what you're catching, or at minimum filter out framework-internal exceptions.

---

### BUG-002: `_render_main()` called before it was defined

**Date:** 2026-07-28
**Severity:** 🔴 Critical
**Found during:** Code Review (code-reviewer-deepseek agent)
**Fixed:** ✅

**The Problem:**
During the error boundary refactor, `_render_main()` was called around line 270 but defined around line 278. This would cause a `NameError` at runtime on the first rerun — the app wouldn't start.

**Root Cause:**
The function definition (`def _render_main():`) was placed after the call site (`try: _render_main()`) during refactoring. Python executes statements top-to-bottom, and `def` is a runtime statement.

**The Fix:**
Moved the function definitions (`_render_main()`, `_render_hero()`) above the call site in the `try/except` block.

**How It Was Caught:**
The code-reviewer-deepseek agent noticed the suspicious ordering during review. Python's `ast.parse()` check (`python -c "import ast; ast.parse(open('app.py').read())"`) would NOT catch this — it only checks syntax, not runtime ordering. This is an argument for runtime smoke tests catching structural issues that static analysis misses.

**Learnings:**
- **For this project:** Always place function definitions before their first call site, even when refactoring existing code. The top-level execution order matters in Streamlit scripts (which run top-to-bottom on every rerun).
- **For future projects:** After refactoring function positions, run the app (or a smoke test) — don't rely on AST parsing alone. `ast.parse` is a syntax check, not a runtime check.
- **Pattern alert:** This is a common refactoring hazard — when extracting code into functions, the call site naturally ends up before the new function definition. Always check: "is the def above the call?"

---

### BUG-003: `st.code(r"""...""")` — raw double-quote delimiters collided with Python docstring syntax

**Date:** 2026-07-28
**Severity:** 🟡 Medium
**Found during:** Code Review (test_learn_page.py structural test)
**Fixed:** ✅

**The Problem:**
In `pages/learn.py`, several `st.code()` blocks used raw double-quote triple delimiters (`r"""..."""`). When the code content inside the block contained `"""` (common in Python docstrings and f-string delimiters), it prematurely closed the outer string, causing a `SyntaxError`.

The app parsed fine until the learn page was loaded — then it crashed. This was a latent bug that only surfaced when users navigated to `/learn`.

**Root Cause:**
`r"""..."""` treats the content as a raw string, but `"""` still terminates the triple-quoted string. Python's lexer always terminates on `"""` regardless of the `r` prefix. The fix requires using single-quote triple delimiters (`'''`) so that `"""` in the code content doesn't collide.

**The Fix:**
Switched all `st.code(r"""...""")` calls to `st.code('''...''')` in `pages/learn.py`. No functional change — single-quote triples work identically to double-quote triples for string literals.

Also added a structural test (`test_no_raw_string_double_quote_collisions`) in `test_learn_page.py` that scans for `st.code(r"""` patterns and fails if any are found.

**How It Was Caught:**
The structural test suite for the learn page explicitly checks for this pattern. This test was added because the developer had already encountered the issue during initial learn page development.

**Learnings:**
- **For this project:** `st.code('''...''')` is the safe default for all code blocks in the learn page. The structural test prevents regressions.
- **For future projects:** When embedding code that itself contains code (code in code), always use the opposite quote type. If the inner code uses `"""`, the outer delimiter should be `'''`. This applies to any language with string interpolation, not just Python.
- **Pattern alert:** "Meta-code" (writing code that contains code examples) always requires careful delimiter management. Make it a project convention to use single-quote triples for all embedded code blocks. Test for violations automatically.

---

### BUG-004: Deprecated `google-generativeai` SDK

**Date:** 2026-07-28
**Severity:** 🟡 Medium (warning-level, not breaking)
**Found during:** Development (deprecation warnings in console output)
**Fixed:** ✅

**The Problem:**
The original project specification called for `google-generativeai` SDK. This SDK was deprecated in favor of `google-genai`. Using it produced deprecation warnings on every import and API call, and would eventually stop working.

**Root Cause:**
Google deprecated the older SDK and released `google-genai` with a new API surface (`genai.Client` instead of `generativeai.configure()`).

**The Fix:**
- Replaced `google-generativeai` with `google-genai` in `requirements.txt`
- Rewrote `gemini_client.py` to use `genai.Client(api_key=...)` and `client.models.generate_content()`
- Maintained identical `generate_response()` interface — no callers changed
- Kept `DEFAULT_MODEL = "gemini-2.5-flash"` — the new SDK supports the same models

**How It Was Caught:**
Deprecation warnings in the console during development. Would have been caught eventually when the SDK was removed from PyPI.

**Learnings:**
- **For this project:** Pin SDK versions in `requirements.txt` to avoid silent upgrades. The migration to `google-genai` was clean because the interface was similar — consider adding an abstraction layer (`generate_response()`) that insulates callers from SDK changes.
- **For future projects:** When scaffolding a project from a specification that names specific libraries, check if those libraries are still maintained/current before installing. Deprecation happens faster in the AI/ML ecosystem than in most other areas.
- **Pattern alert:** SDK deprecations are common in the AI space. Always wrap third-party API clients in a thin adapter layer (like `generate_response()`) so that SDK migrations only touch one file.

---

### BUG-005: `on_click` callback froze UI during summary generation

**Date:** 2026-07-28
**Severity:** 🟠 High (UX-blocking, but not data-loss)
**Found during:** Development (manual testing)
**Fixed:** ✅

**The Problem:**
The "✨ Generate Summary" button used `st.button(on_click=lambda: _generate_summary(df, stats))`. When clicked, the UI froze for 3-5 seconds during the Gemini API call with no feedback — no spinner, no progress indicator. Users thought the app had crashed.

**Root Cause:**
Streamlit's `on_click` callbacks run synchronously inside the event loop. While the callback is executing, no UI updates are rendered. The `_generate_summary()` function makes a synchronous API call that blocks for 3-5 seconds.

**The Fix:**
Replaced the `on_click` pattern with a `st.spinner()` wrapper:

```python
# Before (bad):
st.button("✨ Generate Summary", on_click=lambda: _generate_summary(df, stats))

# After (good):
if st.button("✨ Generate Summary"):
    with st.spinner("🤖 Analyzing your dataset with Gemini..."):
        _generate_summary(df, stats)
    st.rerun()
```

**How It Was Caught:**
Manual testing — the developer noticed the UI freeze and identified the root cause by reviewing the Streamlit documentation on async patterns.

**Learnings:**
- **For this project:** Never use `on_click` callbacks for operations that take >100ms. Always use `if st.button(...)` with `st.spinner()` for async operations. The `st.rerun()` after the spinner ensures the new state renders immediately.
- **For future projects:** Streamlit has three patterns for responding to user actions: `on_click` (synchronous, fast-only), `if st.button` (synchronous but render-safe), and `on_change` (for input widgets). Use `on_click` only for instant operations (clearing state, setting flags). Use `if st.button` + `st.spinner()` for anything that touches the network or disk.
- **Pattern alert:** This is a common Streamlit anti-pattern. Any button that triggers an API call, database query, or file operation should use `if st.button` + `st.spinner()`, never `on_click`.

---

### BUG-006: XLSX file buffer consumption in file size check

**Date:** 2026-07-28
**Severity:** 🟡 Medium (caught in plan review before implementation)
**Found during:** Plan Review (IMPLEMENTATION_PLAN.md review)
**Fixed:** 🔲 Fixed in plan, not yet implemented

**The Problem:**
The original plan for file size limits (#4 in IMPLEMENTATION_PLAN.md) proposed checking `file.size` and falling back to `len(file.getvalue())`. If the fallback was used for XLSX files, `file.getvalue()` would consume the entire file buffer. When `pd.read_excel(file)` tried to read the same file object, it would find an empty buffer — causing a parse error or silent empty DataFrame.

**Root Cause:**
`UploadedFile` objects from Streamlit behave like standard file objects — once you read from them, the read pointer advances. `getvalue()` reads the entire buffer into memory and leaves the pointer at the end. Any subsequent read (by pandas) gets zero bytes.

**The Fix (in plan):**
Read the file into bytes once, then pass `BytesIO(file_bytes)` to pandas:

```python
file_bytes = file.read()
file_size = len(file_bytes)
if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
    return None, f"File too large..."

# Parse from bytes, not from file object
df = pd.read_csv(BytesIO(file_bytes))  # or pd.read_excel(BytesIO(file_bytes))
```

**How It Was Caught:**
Code review of the IMPLEMENTATION_PLAN.md during a systematic review session. The reviewer noticed that `getvalue()` + `pd.read_excel()` on the same file object would fail. This is a classic Python file-I/O bug.

**Learnings:**
- **For this project:** When reading a Streamlit `UploadedFile`, always read it entirely once and pass a `BytesIO` (or `StringIO`) wrapper to downstream consumers. Never rely on the file object being re-readable.
- **For future projects:** `file.read()`, `file.getvalue()`, and `file.seek(0)` are not interchangeable across all file-like objects. Streamlit's `UploadedFile` is a `BytesIO` subclass but may behave differently in edge cases. The safest pattern is: read once, wrap in `BytesIO`, discard the original.
- **Pattern alert:** This is a general Python I/O pattern — file objects are one-shot consumers. Always read into bytes/string and pass a fresh wrapper to each downstream function.

---

### BUG-007: IMPLEMENTATION_PLAN.md proposed bumping streamlit from >=1.28 to >=1.44 for pages.toml

**Date:** 2026-07-28
**Severity:** 🟡 Medium (would have broken users on older Streamlit versions)
**Found during:** Plan Review
**Fixed:** 🔲 Fixed in plan, not yet implemented

**The Problem:**
The original plan for adding `.streamlit/pages.toml` (#6) included bumping the Streamlit minimum version from `>=1.28` to `>=1.44`. This would prevent users on Streamlit 1.28-1.43 from installing the app — all for a cosmetic sidebar label change.

**Root Cause:**
The plan tied the `pages.toml` feature (requires 1.44+) to the requirements.txt version pin, assuming all users needed the feature. But `pages.toml` is optional — Streamlit gracefully ignores it on older versions.

**The Fix (in plan):**
Keep `streamlit>=1.28`. Create `pages.toml` anyway. On Streamlit < 1.44, it's silently ignored and the sidebar shows "learn" instead of "📚 Learn Python" — a harmless fallback. On >=1.44, the polished name appears.

**How It Was Caught:**
Code review of the plan. The reviewer asked: "Does this cosmetic feature justify breaking 16 minor versions of Streamlit compatibility?"

**Learnings:**
- **For this project:** Prefer additive features over version bumps. If a feature is optional, make it gracefully degrade on older versions rather than blocking the entire app.
- **For future projects:** When adding a feature that depends on a newer version of a dependency, ask: "Is this feature essential for the app to function, or can it silently degrade?" Essential → bump the version. Cosmetic → let it degrade.
- **Pattern alert:** Version floor creep is real. Every "minor" version bump removes users. Defend the floor aggressively.

---

## 📊 Summary

### By Severity

| Severity | Count | Fixed | Planned |
|---|---|---|
| 🔴 Critical | 2 | 2 | 0 |
| 🟠 High | 1 | 1 | 0 |
| 🟡 Medium | 5 | 3 | 2 |
| **Total** | **8** | **6** | **2** |

### By Root Cause Category

| Category | Bugs | Pattern |
|---|---|---|
| **Framework abstraction leak** | BUG-001, BUG-005 | Streamlit's internal behavior (exception-based control flow, synchronous callbacks) wasn't obvious from the API surface |
| **Refactoring hazard** | BUG-002, BUG-003 | Moving code around (function position, delimiter changes) introduced runtime errors that static analysis missed |
| **SDK lifecycle** | BUG-004 | Third-party SDK was deprecated between spec and implementation |
| **Python I/O semantics** | BUG-006, BUG-007 | File object consumption and version pinning — classic Python gotchas |

### Top Patterns (What Keeps Happening)

1. **Streamlit's control flow is exception-based.** `st.stop()`, `st.rerun()`, and `st.spinner()` all use exceptions internally. Any top-level `try/except` must filter these out. ✅ **Gated:** `tests/test_static_analysis.py::TestStreamlitExceptionGuard` — AST-based check that every `except Exception` wrapping Streamlit control flow has the re-raise guard.

2. **`on_click` callbacks are for instant operations only.** Any network, disk, or compute operation in an `on_click` callback freezes the UI. Use `if st.button(...)` + `st.spinner()`. ✅ **Gated:** `tests/test_static_analysis.py::TestOnClickAntiPattern` — string-based check that `on_click` callbacks don't reference slow functions or use lambda for non-instant ops.

3. **File objects are one-shot.** Streamlit's `UploadedFile` is a file-like object — read once into bytes, then pass `BytesIO` wrappers to downstream consumers. ✅ **Gated:** `tests/test_static_analysis.py::TestFileIOGuard` — prevents `file.read()` + `pd.read_csv()` without `BytesIO`.

4. **Static analysis isn't enough — but it can be.** `ast.parse()` catches syntax errors but not ordering errors (function defined after call). ✅ **Gated:** `tests/test_static_analysis.py::TestDefBeforeCall` — AST linter catches module-level calls before their `def` statements. Synthetic tests prove detection inside `try:`/`if:`/`with:` blocks.

### Rules for Future Development

- **Rule 1:** After any refactor that moves functions, run `bash scripts/smoke_test.sh`
- **Rule 2:** Any `try/except Exception` at the top level MUST exempt Streamlit control flow
- **Rule 3:** Any button that triggers an API call uses `if st.button` + `st.spinner`, never `on_click`
- **Rule 4:** Every `st.code()` block in the learn page uses single-quote triples
- **Rule 5:** Plan review sessions check for file I/O bugs (buffer consumption, re-reading)
- **Rule 6:** Version bumps require justification — prefer graceful degradation
- **Rule 7:** Every new bug pattern gets a CI gate — if it can be detected statically (Patterns 3 & 4), add it to `test_static_analysis.py`. If it needs runtime (Patterns 1 & 2), document the rule and enforce in code review.
- **Rule 8:** All 4 BUGLOG patterns are now CI-gated via `test_static_analysis.py`. When adding a new bug pattern, ask: "Can I write a static test for this?" If yes, add it. If no, add a runtime smoke check.

---

*Last updated: 2026-07-28 after Patterns 1 & 2 linter implementation. 8 bugs documented, 6 fixed, 2 pending implementation. All 4 BUGLOG patterns now CI-gated via tests/test_static_analysis.py (7 linter tests across 4 pattern classes).*

---

### BUG-008: `except Exception` audit — 11 instances, 2 silent swallowers

**Date:** 2026-07-28
**Severity:** 🟡 Medium (documentation/risk, not an active bug)
**Found during:** Systematic codebase audit (triggered by BUG-001 pattern review)
**Fixed:** ✅ Documented (no code changes needed)

**The Problem:**
BUG-001 established that generic `except Exception` at the top level can catch Streamlit control flow exceptions. This prompted a full audit of every `except Exception` in the codebase (11 instances across 5 files).

**Findings:**

| # | File | Line | Context | Risk |
|---|---|---|---|---|
| 1 | `app.py` | 450 | Error boundary — catches all, re-raises Streamlit | ✅ Safe (BUG-001 fix in place) |
| 2 | `app.py` | 87 | OAuth callback — catches auth failures, shows `st.error` | ✅ Safe (no Streamlit IO in try block) |
| 3 | `app.py` | 208 | GA4 pull — catches API errors, shows `st.error` | ✅ Safe (no Streamlit IO in try block) |
| 4 | `app.py` | 274 | Date parsing — `except Exception: pass` | ⚠️ Silently swallows all errors |
| 5 | `app.py` | 540 | Chart generation — `except Exception: pass` | ⚠️ Silently swallows all errors |
| 6 | `gemini_client.py` | 34 | Key validation — catches API errors, returns (False, msg) | ✅ Safe (utility, no Streamlit) |
| 7 | `gemini_client.py` | 75 | `generate_response()` — converts to RuntimeError | ✅ Safe (utility, no Streamlit) |
| 8 | `data_loader.py` | 31 | `load_file()` — catches parse errors, returns error string | ✅ Safe (utility, no Streamlit) |
| 9 | `data_loader.py` | 75 | `get_dataset_stats()` — date parse fallback | ✅ Safe (utility, no Streamlit) |
| 10 | `prompt_templates.py` | 90 | `describe()` fallback for empty DataFrames | ✅ Safe (utility, no Streamlit) |
| 11 | `pages/learn.py` | 481 | Learn page error display | ✅ Safe (no Streamlit IO in try block) |

**Key distinction:** "Safe" instances are in utility modules (no Streamlit imports) or in try blocks that don't contain Streamlit control flow calls (`st.stop`, `st.rerun`). The two "⚠️" instances use bare `except Exception: pass` which silently swallows errors — not a bug, but makes debugging chart/date issues harder.

**Decision — no code changes needed:** The two silent swallowers are intentional design choices:
- **Date parsing (line 274):** If `pd.to_datetime` fails, the app continues with unparsed dates. Better than crashing on a malformed CSV.
- **Chart generation (line 540):** If chart generation fails, the chat message renders without a chart. Better than crashing on a single chart error.

**How It Was Caught:**
Systematic `ripgrep` search for `except Exception` across all `.py` files, triggered by the BUG-001 pattern review asking "are there other instances of this pattern?"

**Learnings:**
- **For this project:** 9 of 11 instances are safe. The 2 silent swallowers trade debuggability for resilience — a fair trade for a prototype. Consider adding `st.warning(f"Chart generation failed: {e}")` inside the chart exception handler (not just `pass`) to surface errors without crashing.
- **For future projects:** Audit `except Exception` patterns after every significant feature. The risk is always Streamlit control flow (BUG-001) or swallowed errors that hide bugs (lines 274, 540). A `grep except Exception *.py` takes 5 seconds.
- **Pattern alert:** "Silently pass" (`except Exception: pass`) is the most dangerous exception pattern. It hides all errors, including syntax errors in the try block itself. Every `pass` should be justified with a comment: `# If date parsing fails, continue without dates — not worth crashing.`

---

## 📖 Related Docs

- [README.md](README.md) — Setup guide, features, quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) — Design decisions, data flow, security model
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — Central index of all project docs
- [BUGLOG.md](BUGLOG.md) — Structured bug log (8 bugs, patterns, rules)
- [ENHANCEMENTS.md](ENHANCEMENTS.md) — 37-item enhancement roadmap
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — 21-item execution blueprint
- [plans/00-meta/✅ UNIFIED_PLAN.md](plans/00-meta/✅ UNIFIED_PLAN.md) — Master execution plan (6 phase plans + 5 derived plans)
- [plans/00-sprints/✅ P1-P3-sprint-spec.md](plans/00-sprints/✅ P1-P3-sprint-spec.md) — P1–P3 sprint spec ✅
- [plans/00-sprints/✅ P1-P3-completion.md](plans/00-sprints/✅ P1-P3-completion.md) — Sprint completion tracker
- [plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md](plans/00-sprints/✅ P4-wave1-streaming-sprint-spec.md) — Active sprint spec
- [plans/00-meta/✅ P4-future-plan.md](plans/00-meta/✅ P4-future-plan.md) — Future-phase plan
- [plans/00-meta/✅ P4-deferred-plan.md](plans/00-meta/✅ P4-deferred-plan.md) — Deferred items plan
- [plans/p5-p6/✅ COMPONENT_REFACTOR.md](plans/p5-p6/✅ COMPONENT_REFACTOR.md) — #20 mini-spec
- [CHANGELOG.md](CHANGELOG.md) — Unified change history
