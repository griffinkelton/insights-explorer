# Remediation Plan — GA4 Insight Explorer

**Status:** Planning only. No code changes yet.
**Working tree:** 11 files modified + 1 new (CONVERSATION_SUMMARY.md), 351 tests pass.

---

## Current State Assessment

| File | Changes | Risk | Verdict |
|------|---------|------|---------|
| `utils/ga4_client.py` | OAuth persistence, scope expansion | **🔴 Critical** | Scope over-privileged; needs fix |
| `utils/report_exporter.py` | Excel + PDF export | ✅ Verified | Lazy imports already correct |
| `utils/gemini_client.py` | Model selector, token tracking, multimodal | 🟡 Medium | Duplicated error handling |
| `utils/drive_client.py` | Write-back + Sheets | 🟡 Medium | No tests |
| `components/chat.py` | Export buttons, usage stats | 🟢 Low | Solid; missing Sheets button |
| `components/sidebar.py` | Model selector, UI tweaks | 🟢 Low | Solid |
| `components/__init__.py` | OAuth callback update | 🟢 Low | Solid |
| `app.py` | Session state additions | 🟢 Low | Solid |
| `utils/styles.py` | Light mode CSS | 🟢 Low | Solid |
| `pages/learn.py` | Light mode fixes | 🟢 Low | Solid |
| `tests/test_ga4_client.py` | OAuth state store tests | 🟢 Low | Good discipline |

### Verified: ReportLab Import Already Safe ✅

The feedback flagged a "ReportLab import contradiction" claiming `report_exporter.py` crashes on import without ReportLab. **This is already handled correctly:**

```python
# utils/report_exporter.py (lines 26-37) — already in working tree
try:
    from reportlab.lib import colors
    ...
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
```

`build_pdf_report()` then checks `if not HAS_REPORTLAB: raise RuntimeError(...)`. This is identical to the OpenPyXL pattern. **No fix needed.** Confirmed via `python -c "from utils.report_exporter import HAS_REPORTLAB"` → no crash.

---

## P1: Critical — Fix Before Commit

### 1. OAuth Scope: `drive` → `drive.readonly` + `drive.file`

**File:** `utils/ga4_client.py`, line 23-26

**Problem:** `SCOPES = ["...analytics.readonly", "...drive"]` grants full read/write to the user's *entire* Drive — photos, tax documents, everything. The blast radius if a token is compromised is the whole Drive.

**Analysis:** The Drive file picker (`list_drive_files`, `download_drive_file`) needs **read** access to arbitrary existing files. The write-back functions (`write_drive_file`, `create_google_sheet`) need **write** access only to files the app creates. The `drive.file` scope restricts write access to app-created files; the `drive.readonly` scope grants read access without write. Using both together is the principle of least privilege.

**Change:**
```python
# Before:
SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/drive",
]

# After:
SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]
```

**Side effect:** Users with cached credentials from the old `drive` scope will need to re-authenticate. Their `scopes` field won't match → `credentials_from_dict` will see expired/wrong scope → they'll be prompted to sign in again. This is expected OAuth behavior when scopes change.

**Verify:** Existing `test_ga4_client.py` tests pass (they mock SCOPES via the `Flow` mock and don't hardcode scope values). The OAuth state store tests are scope-agnostic.

**Lines changed:** 1 (one list element → two list elements)

---

### 2. OAuth State File Permissions

**File:** `utils/ga4_client.py`, `save_oauth_state()` function

**Problem:** `code_verifier` is written to a temp JSON file but file permissions are the default (world-readable on many temp directory configurations). On shared/multi-user systems, another user could read the code verifier.

**Change:** Add one line after `file_path.write_text(...)`:
```python
file_path.chmod(0o600)
```

**State parameter predictability:** Confirmed safe — `flow.authorization_url()` uses Google's OAuth library which generates cryptographically random state via `secrets.token_urlsafe()`. No fix needed.

**Lines changed:** 1

---

## P2: Important — Should Fix Before Commit

### 3. Extract Shared API Error Classification

**File:** `utils/gemini_client.py`

**Problem:** `generate_response()`, `generate_response_stream()`, and `analyze_file_with_gemini()` all repeat the same 10-line try/except block:
```python
except ValueError:
    raise
except Exception as e:
    error_msg = str(e).lower()
    if "rate" in error_msg and "limit" in error_msg:
        raise RuntimeError("Rate limit hit...") from e
    elif "quota" in error_msg:
        raise RuntimeError("API quota exceeded...") from e
    else:
        raise RuntimeError(f"Gemini API error: {str(e)}") from e
```

This is the drift risk flagged in earlier audits — if rate limit handling changes, all three functions must be updated identically.

**Approach:** `generate_response_stream()` is a generator, so decorators won't work. A context manager would require restructuring. Simplest correct approach: extract a `_classify_api_error(e: Exception) -> str` helper that returns the error message string. Each function then does `raise RuntimeError(msg) from e`. This reduces 30 duplicated lines to 3.

**Before (in each function):**
```python
    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "rate" in error_msg and "limit" in error_msg:
            raise RuntimeError("Rate limit hit. Please wait a moment and try again.") from e
        elif "quota" in error_msg:
            raise RuntimeError("API quota exceeded. Check your Google Cloud quota or try again later.") from e
        else:
            raise RuntimeError(f"Gemini API error: {str(e)}") from e
```

**After (helper function + simplified call sites):**
```python
def _classify_api_error(e: Exception) -> str:
    """Classify a Gemini API exception into a human-readable message."""
    error_msg = str(e).lower()
    if "rate" in error_msg and "limit" in error_msg:
        return "Rate limit hit. Please wait a moment and try again."
    if "quota" in error_msg:
        return "API quota exceeded. Check your Google Cloud quota or try again later."
    return f"Gemini API error: {str(e)}"

# In each function:
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e
```

**Lines changed:** ~30 removed, ~10 added (net -20)

---

### 4. Track Thought Tokens

**File:** `utils/gemini_client.py`, `_track_usage()` function

**Problem:** Newer Gemini responses expose `total_thought_tokens` in `usage_metadata`. If "Dynamic Thinking Budget" is on the roadmap, capturing this now avoids retrofitting historical totals later.

**Change:** Add one attribute access and one session state field:
```python
thought_tokens = getattr(usage, "total_thought_tokens", 0) or 0

if "total_thought_tokens" not in st.session_state:
    st.session_state.total_thought_tokens = 0
st.session_state.total_thought_tokens += thought_tokens
```

Not shown in the usage stats UI yet — just collected for now. Add UI display when thinking budget is implemented.

**Lines changed:** ~4

---

### 5. Smoke Tests for Untested Functions

**Files:** New test file(s) in `tests/`

**Problem:** Six new functions with real external side effects (Drive API, file generation, Gemini multimodal) have zero test coverage:
- `write_drive_file()` → `tests/test_drive_client.py`
- `write_dataframe_to_drive()` → `tests/test_drive_client.py`
- `create_google_sheet()` → `tests/test_drive_client.py`
- `build_excel_report()` → new `tests/test_report_exporter.py`
- `build_pdf_report()` → new `tests/test_report_exporter.py`
- `analyze_file_with_gemini()` → `tests/test_gemini_client.py`

**Minimum smoke tests (6 tests, ~60 lines):**

| Function | Test | What it verifies |
|----------|------|------------------|
| `build_excel_report()` | Valid input returns bytes | Doesn't crash on normal data |
| `build_excel_report()` | `HAS_OPENPYXL=False` raises RuntimeError | Lazy import guard works |
| `build_pdf_report()` | Valid input returns bytes | Doesn't crash on normal data |
| `build_pdf_report()` | `HAS_REPORTLAB=False` raises RuntimeError | Lazy import guard works |
| `analyze_file_with_gemini()` | Valid bytes + mime type returns str | Doesn't crash on valid input |
| `analyze_file_with_gemini()` | Empty bytes handled gracefully | Doesn't crash on edge case |

The three Drive write functions (`write_drive_file`, `write_dataframe_to_drive`, `create_google_sheet`) need real Google API credentials to test meaningfully — mock-based smoke tests would just test the mock. These are better deferred to integration tests with a real credential.

---

## P3: Optional Enhancements

### 6. Sheets UI Button

**File:** `components/chat.py`, export section

The `create_google_sheet()` function exists but has no UI trigger. Add a 4th column in the export section:

```python
col_md, col_xl, col_pdf, col_sheets = st.columns(4)
# ...existing 3 columns...
with col_sheets:
    if st.session_state.get("ga4_creds") is not None:
        if st.button("📊 Save to Sheets", use_container_width=True, key="export_sheets"):
            from utils.ga4_client import credentials_from_dict
            from utils.drive_client import create_google_sheet

            creds = credentials_from_dict(st.session_state.ga4_creds)
            with st.spinner("Creating Google Sheet..."):
                try:
                    _, sheet_url = create_google_sheet(
                        credentials=creds,
                        title=f"GA4 Analysis — {pd.Timestamp.now():%Y-%m-%d %H:%M}",
                        df=st.session_state.df,
                        summary=st.session_state.summary,
                        chat_history=st.session_state.chat_history,
                    )
                    st.success(f"✅ [Open in Google Sheets]({sheet_url})")
                except Exception as e:
                    st.error(f"⚠️ Sheets export failed: {e}")
    else:
        st.button("📊 Save to Sheets", disabled=True, use_container_width=True,
                   help="Sign in with Google to enable Sheets export")
```

**Design notes:** Uses `if st.button` pattern (BUG-005 compliant), gated on `ga4_creds`, wraps in try/except for inline error handling.

---

## Explicitly Deprioritized / Removed

### ❌ AST Validation + Subprocess Sandbox — Do NOT implement

The feedback and security literature are clear: AST-based code validation is a "glass sandbox" — it looks restrictive but shatters under determined probing. Python's object model provides too many indirect paths to dangerous functionality (`__builtins__`, `__class__.__bases__`, `__subclasses__()`) that a deny-list of `import os` or `eval()` simply won't catch. `subprocess.run()` provides no OS-level isolation either.

**The right approach if code execution is ever needed:** Gemini **Function Calling** — register pre-approved Python functions as tools, and let the model choose which to call with what arguments. The model never writes arbitrary code; it only selects from your safe, fixed-signature functions. This delivers the "dynamic formula" value with none of the sandbox-escape risk.

**Verdict:** Remove this from the roadmap entirely. Function Calling is the safe replacement.

---

## Commit Organization

Do **not** bundle all fixes into one commit. Sequence as:

| Commit | Contents | Files | ~Lines |
|--------|----------|-------|--------|
| 1. Scope fix | `drive` → `drive.readonly` + `drive.file` | `utils/ga4_client.py` | +2/-1 |
| 2. Permissions hardening | `chmod(0o600)` on OAuth state files | `utils/ga4_client.py` | +1 |
| 3. Error handling refactor | Extract `_classify_api_error()` helper | `utils/gemini_client.py` | +10/-30 |
| 4. Thought token tracking | Add `total_thought_tokens` tracking | `utils/gemini_client.py` | +4 |
| 5. Smoke tests | Tests for export + multimodal functions | `tests/test_report_exporter.py` (new), `tests/test_gemini_client.py` | ~60 |
| 6. Sheets UI button | 4th export column in chat.py | `components/chat.py` | ~25 |

Each commit is independently verifiable:
- Commit 1: `pytest tests/test_ga4_client.py` (already passing)
- Commit 2: `pytest tests/test_ga4_client.py` (OAuth state tests)
- Commit 3: `pytest tests/test_gemini_client.py` (existing tests verify error paths)
- Commit 4: Existing tests + manual smoke
- Commit 5: New tests themselves verify the new code
- Commit 6: App renders correctly (browser smoke)

---

## Summary: What Changes vs. What Stays

| Action | File(s) | Lines |
|--------|---------|-------|
| **Fix** scope | `utils/ga4_client.py` | +2/-1 |
| **Add** chmod | `utils/ga4_client.py` | +1 |
| **Extract** error helper | `utils/gemini_client.py` | +10/-30 |
| **Add** thought tokens | `utils/gemini_client.py` | +4 |
| **Add** smoke tests | `tests/` (new files) | ~60 |
| **Add** Sheets button | `components/chat.py` | ~25 |
| **Keep as-is** | `utils/report_exporter.py` (ReportLab already fixed), `utils/drive_client.py`, `utils/styles.py`, `components/sidebar.py`, `components/__init__.py`, `app.py`, `pages/learn.py`, `CONVERSATION_SUMMARY.md` | 0 |
| **Remove** from plan | AST validation + subprocess sandbox | N/A (never implemented) |

**Total planned diff:** ~+102/-31 across ~6 commits.
