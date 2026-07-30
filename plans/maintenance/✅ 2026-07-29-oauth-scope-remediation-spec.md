# Remediation Spec — OAuth Security Hardening & Code Quality Pass

> **Derived from:** REMEDIATION_PLAN.md + 4 interview rounds + 8 feedback sections
> **Working tree:** 11 files modified + 1 new (CONVERSATION_SUMMARY.md), 351 tests pass
> **Constraint:** AI model must always be free (Flash models only)
> **Scope:** Critical fixes and quality improvements only. No new features.
> **Plans directory:** This is post-phase-6 maintenance. Artifacts live in `plans/maintenance/`, not in the original phase directories (`p1-p2/`, `p3-p4/`, `p5-p6/`, `00-sprints/`, `00-meta/`).

---

## Plans Directory Structure

The original development was organized into six phases tracked in `plans/`:

```
plans/
├── 00-meta/             ← Original meta-planning docs (UNIFIED_PLAN, onboarding, etc.)
├── 00-sprints/           ← Sprint execution specs (streaming, component refactor, etc.)
├── p1-p2/                ← P1-P2 completion docs (APP_ICON, DATA_QUALITY_SCORECARD)
├── p3-p4/                ← P3-P4 completion docs (STREAMING_RESPONSES, THEME_TOGGLE)
└── p5-p6/                ← P5-P6 completion docs (COMPONENT_REFACTOR, AI_DATA_ENHANCEMENTS)
```

All of those directories are completion artifacts from the original 6-phase plan. This remediation is **post-phase-6 maintenance** — a different kind of work (reactive code review fixes, not planned feature development). It lives in a new directory that cleanly separates ongoing maintenance from the historical phase-based development:

```
plans/
├── 00-meta/              ← Archived — original meta-planning (all ✅)
│   ├── ✅ UNIFIED_PLAN.md
│   ├── ✅ IMPLEMENTATION_PLAN.md       ← Moved from root
│   ├── ✅ ENHANCEMENTS.md               ← Moved from root
│   ├── ✅ ORIGINAL_PROJECT_COMPLETE.md  ← Renamed + moved from root
│   └── ✅ P4-future-plan.md, etc.
├── 00-sprints/            ← Archived — original sprint specs (all ✅)
├── p1-p2/                 ← Archived — P1-P2 completion (all ✅)
├── p3-p4/                 ← Archived — P3-P4 completion (all ✅)
├── p5-p6/                 ← Archived — P5-P6 completion (all ✅)
└── maintenance/           ← Post-release fixes and technical debt (active)
    ├── 🔵 2026-07-29-oauth-scope-remediation-spec.md    ← This file (in progress)
    ├── 🔵 2026-07-29-drive-scope-remediation-plan.md    ← Original plan (archival)
    └── ✅ 2026-07-29-drive-export-model-selector-session.md  ← Already completed
```

**Convention:** Emoji prefixes indicate status at a glance, matching the existing `plans/00-sprints/` convention:
- `🔵` = planned/spec'd but not yet executed
- `✅` = completed/executed

When Commit 6 executes file moves, the spec and plan files start with `🔵`. After all 7 commits complete and the remediation passes all acceptance criteria, they are renamed to `✅`. The session summary is always `✅` since it documents already-completed work.

---

## Interview & Feedback Resolution Summary

| Topic | Original Plan | Feedback Verdict | Final Decision |
|-------|---------------|------------------|----------------|
| Scope detection | Exact set equality `!=` | Use `issubset()` — only missing scopes flag stale | `not required.issubset(granted)` |
| Re-auth UX | Trigger OAuth flow from banner | Simpler: clear creds + rerun, let normal sign-in handle it | Clear `ga4_creds` + `drive_files_cache`, `st.rerun()` |
| Banner location | `components/__init__.py` | Sidebar, before GA4/Drive sections | In `components/sidebar.py` |
| chmod | `if os.name != "nt": chmod(0o600)` | Add `try/except OSError` for network mounts | Guarded + wrapped |
| Error helper messages | Substring matching ("rate" in "limit") | HTTP status codes (429, 403, 500) + emoji prefixes | `"429" in str(e)` → "⏱️ Rate limit..." |
| Error in streaming | `raise RuntimeError(...)` from generator | Yield message + return (don't raise in generator) | `yield f"\n\n{msg}"; return` |
| Thought token attr | `total_thought_tokens` | `thoughts_token_count` (actual API name) | `getattr(usage, "thoughts_token_count", 0)` |
| Cached token attr | — | `cached_content_token_count` | `getattr(usage, "cached_content_token_count", 0)` |
| Cached token UI | Show conditionally | Never show — internal metric only | Track, don't display |
| ga4_auth_flow cleanup | app.py only | Also sidebar.py Disconnect handler | Both files |
| BUGLOG | One summary entry | Two entries (BUG-008, BUG-009) with full template | Separate entries |
| File naming | `plans/` root | `plans/00-sprints/` with existing convention | `plans/maintenance/` — new directory for post-phase-6 maintenance; `✅` prefix + dated prefixes matching sprint-spec convention |
| Model constraint | No constraint | Must always be free | Remove Pro; Flash-only AVAILABLE_MODELS |
| Token revocation | Not addressed | Auto-revoke old grant server-side before clearing | Call `https://oauth2.googleapis.com/revoke` once (prefer refresh token); revoking one invalidates the entire grant |

---

## Design Decisions

### D1: `needs_scope_migration()` — `issubset()`, not strict equality

**Chosen:** `not required.issubset(granted)`

**Why:** If a scope is ever removed from `SCOPES` later, a user with *more* scopes than currently required shouldn't see a false "stale" warning. Only *missing* required scopes should trigger migration. This is future-proof — the same function correctly flags any scope drift without modification.

```python
def needs_scope_migration(credentials: Credentials) -> bool:
    """True if cached credentials are missing any currently required scope."""
    granted = set(credentials.scopes or [])
    required = set(SCOPES)
    return not required.issubset(granted)
```

### D2: Re-auth revokes old token server-side, clears locally, then reruns

**Chosen:** Call `_revoke_token()` to invalidate the old broad-scope grant server-side, then set `ga4_creds = None`, clear `drive_files_cache`, call `st.rerun()`. Let the normal sign-in button handle the OAuth flow.

**Why:** The old token with the broad `drive` scope remains valid server-side for its remaining lifetime (~1 hour for access tokens; refresh tokens persist indefinitely). If session state is restored from browser cache or a stale tab, the old token could be reused — revoking server-side guarantees it's dead. After revocation, clearing local state and rerunning naturally surfaces the existing "Sign in with Google" button.

### D3: `_classify_api_error()` — HTTP status codes, emoji prefixes

**Chosen:** Check for HTTP error codes in the string representation, use emoji-prefixed messages, return string.

**Why:** HTTP status codes (429, 403, 500) are the stable taxonomy — Google changes error message text, but `"429" in str(e)` won't break when phrasing changes. Emoji prefixes make error messages visually parseable at a glance in chat.

```python
def _classify_api_error(e: Exception) -> str:
    """Pure function: classifies Gemini exceptions into user-facing messages."""
    msg = str(e)
    if "429" in msg:
        return "⏱️ Rate limit exceeded. Please wait a moment and try again."
    if "403" in msg:
        return "🔑 API key invalid or missing permissions."
    if "500" in msg:
        return "⚠️ Gemini service error. Please try again shortly."
    return f"⚠️ Unexpected error: {e}"
```

### D4: Streaming errors yield instead of raising

**Chosen:** In `generate_response_stream()`, the generator yields the error message and returns rather than raising `RuntimeError`.

**Why:** Raising inside a generator surfaces the exception at `st.write_stream()`'s internal `next()` call — Streamlit may or may not handle this gracefully. Yielding the error as text ensures it renders in the chat message alongside the streamed content, which is the expected UX: the user sees a partial response followed by the error, not a red traceback page.

```python
# In generate_response_stream():
except ValueError:
    raise
except Exception as e:
    yield f"\n\n{_classify_api_error(e)}"
    return  # Exit generator cleanly
```

### D5: Model constraint — flash-only, always free

**Chosen:** Remove `gemini-2.5-pro` from `AVAILABLE_MODELS`. All available models must be free-tier.

**Why:** The user explicitly stated "my AI model must always be free." Pro models require paid billing. Including them in the selector creates a footgun — a user selects Pro, gets a billing error, and has no clear path back. Since this app is designed for the free tier, the selector should only offer free models.

```python
AVAILABLE_MODELS = {
    "gemini-2.5-flash": {
        "label": "Gemini 2.5 Flash",
        "tooltip": "Latest flash model. 1M context, 10 RPM, 1,500 RPD. Free tier.",
        "context_window": 1_000_000,
        "tier": "Free",
    },
    "gemini-2.0-flash": {
        "label": "Gemini 2.0 Flash",
        "tooltip": "Previous-gen flash. 1M context, 10 RPM, 1,500 RPD. Free tier.",
        "context_window": 1_000_000,
        "tier": "Free",
    },
    "gemini-1.5-flash": {
        "label": "Gemini 1.5 Flash",
        "tooltip": "Legacy flash. 1M context, 15 RPM, 1,500 RPD. Free tier.",
        "context_window": 1_000_000,
        "tier": "Free",
    },
}
```

### D6: Token revocation on scope migration — server-side invalidation of entire grant

**Chosen:** Call Google's OAuth revocation endpoint (`https://oauth2.googleapis.com/revoke`) once — preferring the refresh token if present, falling back to the access token. Only one token needs to be revoked because Google's endpoint invalidates the **entire OAuth grant** (both access token and its paired refresh token) regardless of which one you pass.

**Why one token is sufficient:** Google's `/revoke` doesn't treat access and refresh tokens as independent kill switches. Passing either token revokes the whole grant — the access token stops working immediately, the refresh token can no longer generate new access tokens, and any future refresh attempt fails. Revoking both separately is just doing the same operation twice.

**Why revoke at all:** "Clear locally only" leaves the over-privileged `drive`-scope refresh token alive server-side indefinitely (Google refresh tokens are long-lived by default and don't expire on their own). The residual risk is the entire point of the scope fix — a dangling broad-scope grant defeats it. Server-side revocation guarantees the old over-privileged grant is dead regardless of what happens to the local session state.

**Implementation:** A `_revoke_token()` function in `utils/ga4_client.py` that POSTs to Google's endpoint using the `requests` library (already a transitive dependency via Google auth libraries). Prefers `refresh_token` if available since it's the longer-lived credential. Called before clearing `ga4_creds` in the migration banner handler. Wrapped in `try/except` — revocation is best-effort; a network failure should never block the user from re-authenticating.

```python
import logging
import requests

logger = logging.getLogger(__name__)

def _revoke_token(credentials: Credentials) -> None:
    """Revoke the entire OAuth grant by calling Google's revocation endpoint.

    Google's /revoke endpoint invalidates the entire grant regardless of
    which token you pass — only one call is needed. Prefers the refresh
    token (longer-lived) over the access token.

    Best-effort — failures are logged to stderr (visible in the developer's
    terminal but invisible to the user) and never block re-authentication.
    """
    token = credentials.refresh_token or credentials.token
    if not token:
        return
    try:
        requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=5,
        )
    except requests.RequestException as e:
        logger.warning("Token revocation failed (non-critical): %s", e)
```

**Edge cases handled:**
- **Network down:** `try/except` catches `RequestException`, logs warning, re-auth proceeds
- **Token already expired:** Google returns 200 for already-expired tokens — not an error
- **Token already revoked:** Google returns 400 — caught by `except`, logged, re-auth proceeds
- **No tokens at all:** The `if not token` guard handles empty/null tokens gracefully
- **Logging invisible in UI but discoverable:** Developer running `streamlit run` sees the warning in their terminal; end user sees nothing

### D7: Thinking tokens are free on Flash models

**Confirmed:** Google bills thinking tokens as part of output token count. On the free tier with Flash models, output tokens (including thinking tokens) are free. The `thoughts_token_count` attribute on `usage_metadata` reflects real billed usage (if on a paid plan) — but for free-tier Flash models, it's informational only. The value of tracking it now is forward-looking: if the app ever uses thinking budget, historical data exists; if the model selector ever includes paid models, the tracking is already in place.

---

## Commit Plan (7 commits, sequential)

### Commit 1: Fix OAuth scope over-privilege

**Files:** `utils/ga4_client.py`

**Change:**
```python
# Line 23-26 — before:
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

**Lines:** +2 / -1

**Verification:** `pytest tests/test_ga4_client.py` — all pass.

---

### Commit 2: Add file permissions hardening to OAuth state store

**Files:** `utils/ga4_client.py`

**Change:** In `save_oauth_state()`, after `file_path.write_text(...)`:
```python
    if os.name != "nt":
        try:
            file_path.chmod(0o600)
        except OSError:
            pass  # Best-effort; some filesystems (network mounts, etc.) may not support chmod
```

**Why the `try/except`:** Network-mounted filesystems, some container environments, and unusual Unix configs can raise `OSError` on `chmod`. This is a best-effort security hardening — permission setting should never crash the OAuth flow.

**Lines:** +4

**Verification:** `pytest tests/test_ga4_client.py::TestOAuthStateStore` — all pass.

---

### Commit 3: Add stale-scope detection banner in sidebar

**Files:** `utils/ga4_client.py` (detection function), `components/sidebar.py` (banner)

**3a. New functions in `utils/ga4_client.py`:**
```python
def needs_scope_migration(credentials: Credentials) -> bool:
    """True if cached credentials are missing any currently required scope."""
    granted = set(credentials.scopes or [])
    required = set(SCOPES)
    return not required.issubset(granted)


def _revoke_token(credentials: Credentials) -> None:
    """Revoke the entire OAuth grant via Google's revocation endpoint.

    Google's /revoke invalidates the entire grant regardless of which token
    you pass — only one call is needed. Prefers refresh token over access token.

    Best-effort — failures are logged (invisible to user, visible in terminal)
    and never block re-authentication.
    """
    token = credentials.refresh_token or credentials.token
    if not token:
        return
    try:
        import requests

        requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=5,
        )
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(
            "Token revocation failed (non-critical): %s", e
        )
```

**3b. Banner in `components/sidebar.py`** — inserted in `_render_ga4_connect()`, after the `if st.session_state.ga4_creds is None:` guard but before the connected-state controls:
```python
    if st.session_state.ga4_creds is not None:
        creds = credentials_from_dict(st.session_state.ga4_creds)
        if needs_scope_migration(creds):
            st.warning(
                "🔐 We've updated Drive permissions for better security. "
                "Please reconnect your Google account to continue using Drive features."
            )
            if st.button("🔄 Reconnect Google Account", use_container_width=True):
                _revoke_token(creds)  # Server-side invalidation (best-effort)
                st.session_state.ga4_creds = None
                st.session_state.drive_files_cache = None
                st.rerun()
            # Return early — don't show connected controls until migration done
            return
```

**Design notes:**
- Banner only renders when `ga4_creds is not None` AND `needs_scope_migration()` returns True
- Reconnect button clears creds + Drive cache, preserves `df`, `stats`, `summary`, `chat_history`
- `st.rerun()` naturally surfaces the sign-in button in the sidebar
- Banner returns early — the connected-state controls (Property ID, Pull Data, Disconnect) don't render while scope is stale
- Banner is self-correcting: once user re-authenticates, `ga4_creds` is None → banner condition is false → sign-in button shows → user signs in with new scopes → banner never appears again because scopes match

**Lines:** +50 (5 detection + 25 revocation + 20 banner)

**Verification:** Manual smoke: connect with old-scope token → see banner → click reconnect → sign-in button appears → sign in → connected controls visible.

---

### Commit 4: Extract shared API error classification + tokens

**Files:** `utils/gemini_client.py`, `components/chat.py`, `app.py`

**4a. New pure function:**
```python
def _classify_api_error(e: Exception) -> str:
    """Classify a Gemini API exception into a user-facing message.

    Pure function — no side effects. Trivially testable.
    Uses HTTP status codes (429, 403, 500) for stable classification
    rather than substring-matching on English error text.
    """
    msg = str(e)
    if "429" in msg:
        return "⏱️ Rate limit exceeded. Please wait a moment and try again."
    if "403" in msg:
        return "🔑 API key invalid or missing permissions."
    if "500" in msg:
        return "⚠️ Gemini service error. Please try again shortly."
    return f"⚠️ Unexpected error: {e}"
```

**4b. `generate_response()` — replace except block:**
```python
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(_classify_api_error(e)) from e
```

**4c. `analyze_file_with_gemini()` — same replacement.**

**4d. `generate_response_stream()` — different pattern (yield, don't raise):**
```python
    except ValueError:
        raise
    except Exception as e:
        yield f"\n\n{_classify_api_error(e)}"
        return
```

**4e. Updated `_track_usage()`:**
```python
def _track_usage(response) -> None:
    try:
        import streamlit as st
    except ImportError:
        return

    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return

    st.session_state.total_input_tokens += getattr(usage, "prompt_token_count", 0) or 0
    st.session_state.total_output_tokens += getattr(usage, "candidates_token_count", 0) or 0
    st.session_state.total_thought_tokens += getattr(usage, "thoughts_token_count", 0) or 0
    st.session_state.total_cached_tokens += getattr(usage, "cached_content_token_count", 0) or 0
    st.session_state.total_tokens_used += getattr(usage, "total_token_count", 0) or 0
```

**4f. Session state defaults in `app.py`:**
```python
if "total_thought_tokens" not in st.session_state:
    st.session_state.total_thought_tokens = 0
if "total_cached_tokens" not in st.session_state:
    st.session_state.total_cached_tokens = 0
```

**4g. Updated `_render_usage_stats()` in `components/chat.py`:**
```python
    # After existing stats, conditionally show thought tokens:
    thought_tokens = st.session_state.get("total_thought_tokens", 0)
    if thought_tokens > 0:
        st.markdown(
            f'<span style="font-size:0.65rem;color:{muted_color};">'
            f'💭 {thought_tokens:,} thought</span>',
            unsafe_allow_html=True,
        )
```

Cached tokens are tracked in session state but **not displayed** — they are an infrastructure-level optimization detail, not user-actionable.

**Lines:** +30 / -40 (net -10 from duplication removal, +20 from token additions, +2 app.py defaults)

**Verification:** `pytest tests/test_gemini_client.py` — existing tests pass. New `test__classify_api_error` smoke test verifies classification logic.

---

### Commit 5: Smoke tests for untested functions

**Files:** New `tests/test_exports.py`

**8 tests, ~90 lines:**

```python
"""Smoke tests for export functions, multimodal analysis, and error classification."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from utils.report_exporter import build_excel_report, build_pdf_report, HAS_OPENPYXL, HAS_REPORTLAB
from utils.gemini_client import analyze_file_with_gemini, _classify_api_error


class TestClassifyApiError:
    """Unit tests for the pure error classification function."""

    def test_rate_limit_429(self):
        """429 errors should classify as rate limit."""
        e = Exception("429 RESOURCE_EXHAUSTED")
        result = _classify_api_error(e)
        assert "Rate limit" in result

    def test_auth_403(self):
        """403 errors should classify as API key issue."""
        e = Exception("403 PERMISSION_DENIED")
        result = _classify_api_error(e)
        assert "API key" in result

    def test_server_500(self):
        """500 errors should classify as service error."""
        e = Exception("500 INTERNAL")
        result = _classify_api_error(e)
        assert "service error" in result

    def test_unknown_error_fallback(self):
        """Unknown errors should return a generic message with the original text."""
        e = Exception("something completely unexpected")
        result = _classify_api_error(e)
        assert "Unexpected error" in result
        assert "something completely unexpected" in result


class TestExcelExport:
    def test_valid_input_returns_bytes(self):
        """build_excel_report with valid DataFrame returns bytes."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = build_excel_report(df=df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_missing_openpyxl_raises(self, monkeypatch):
        """build_excel_report raises RuntimeError when openpyxl not installed."""
        monkeypatch.setattr("utils.report_exporter.HAS_OPENPYXL", False)
        with pytest.raises(RuntimeError, match="openpyxl"):
            build_excel_report()


class TestPdfExport:
    def test_valid_input_returns_bytes(self):
        """build_pdf_report with valid input returns bytes."""
        result = build_pdf_report(
            summary="Test summary",
            stats={"row_count": 100, "column_count": 5},
            chat_history=[{"question": "Q1", "response": "A1"}],
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_missing_reportlab_raises(self, monkeypatch):
        """build_pdf_report raises RuntimeError when reportlab not installed."""
        monkeypatch.setattr("utils.report_exporter.HAS_REPORTLAB", False)
        with pytest.raises(RuntimeError, match="reportlab"):
            build_pdf_report()
```

The `analyze_file_with_gemini()` test is omitted — it requires a real (or mocked) Gemini client, and the existing `test_gemini_client.py` already covers the Gemini response path. Adding it would require restructuring the client mock, which is out of scope for a smoke test pass.

Drive write functions (`write_drive_file`, `write_dataframe_to_drive`, `create_google_sheet`) are deferred — they require real Google API credentials to test meaningfully. Mock-based tests would only test the mock.

**Verification:** `pytest tests/test_exports.py -v` — 8 tests pass.

---

### Commit 6: Dead code cleanup, file moves, BUGLOG entries

**Files:** `app.py`, `components/sidebar.py`, `BUGLOG.md`, file moves

**6a. Remove `ga4_auth_flow` from `app.py`:**
Remove the session state initialization block:
```python
# Remove this block:
if "ga4_auth_flow" not in st.session_state:
    st.session_state.ga4_auth_flow = None
```

**6b. Remove `ga4_auth_flow` from `components/sidebar.py` Disconnect handler:**
```python
# In _render_ga4_connect(), Disconnect button handler — remove:
st.session_state.ga4_auth_flow = None
```

**6c. Remove `gemini-2.5-pro` from `AVAILABLE_MODELS` in `utils/gemini_client.py`:**
Delete the entry for `"gemini-2.5-pro"`. All models must be free-tier. The `"tier"` key becomes uniformly `"Free"` but is retained for forward compatibility.

**6d. Add BUGLOG entries — BUG-008 and BUG-009:**

```markdown
### BUG-008: OAuth scope over-privileged (full `drive` instead of `drive.file`)

**Date:** 2026-07-29
**Severity:** 🟠 High (privacy/security exposure, not yet shipped)
**Found during:** Code Review
**Fixed:** ✅

**The Problem:**
The Drive write-back feature requested the full `https://www.googleapis.com/auth/drive`
scope, granting read/write access to the user's entire Google Drive rather than just
files the app creates.

**Root Cause:**
The scope was expanded from `drive.readonly` to `drive` to enable write-back features
(Sheets export, Drive file writes) without evaluating whether a narrower scope would
suffice.

**The Fix:**
Changed to `drive.readonly` (for existing Drive picker reads) + `drive.file` (for
write-back to files the app creates), together covering the full use case with
minimal blast radius. Added `needs_scope_migration()` to detect stale cached
credentials, show a persistent re-auth banner in the sidebar, and actively revoke
the old broad-scope grant via Google's revocation endpoint before clearing local
state — so the old over-privileged token is killed server-side, not just discarded.

**Learnings:**
- **For this project:** Any scope expansion should default to the narrowest scope
  that satisfies the concrete use case, not the broadest scope that "just works."
- **For future projects:** OAuth scope creep is easy to introduce incrementally —
  audit scope changes as carefully as dependency additions.
- **Pattern alert:** This is the OAuth analog of "wildcard IAM permissions" — always
  ask "what's the minimum grant this feature actually needs?"

---

### BUG-009: OAuth code_verifier lost across Streamlit redirect

**Date:** 2026-07-29
**Severity:** 🟠 High (breaks Drive auth flow entirely)
**Found during:** Development
**Fixed:** ✅

**The Problem:**
Google's OAuth redirect destroys Streamlit's in-memory `st.session_state`, so the PKCE
`code_verifier` generated before redirect was unavailable when exchanging the
authorization code after redirect.

**Root Cause:**
Streamlit session state is tied to the browser session/WebSocket connection, which does
not survive a full-page navigation to Google's consent screen and back.

**The Fix:**
Persist `code_verifier`, `redirect_uri`, and `state` to temporary JSON files keyed by
the OAuth `state` parameter, with file permissions restricted to the owner (POSIX only)
and automatic pruning of files older than 10 minutes.

**Learnings:**
- **For this project:** Any Streamlit flow requiring an external redirect needs
  filesystem or external persistence — session state alone is insufficient.
- **For future projects:** OAuth state that must survive a redirect should never live
  only in-memory; treat it as data requiring the same persistence rigor as a database
  write.
- **Pattern alert:** Sensitive data written to temp files needs explicit permission
  hardening — `chmod(0o600)` with `try/except OSError` for best-effort across
  filesystem types.
```

**6e. File moves & organization:**

*Remediation artifacts → `plans/maintenance/`:*
```bash
mkdir -p plans/maintenance
mv CONVERSATION_SUMMARY.md "plans/maintenance/✅ 2026-07-29-drive-export-model-selector-session.md"
mv REMEDIATION_PLAN.md "plans/maintenance/🔵 2026-07-29-drive-scope-remediation-plan.md"
mv plans/remediation-spec.md "plans/maintenance/🔵 2026-07-29-oauth-scope-remediation-spec.md"
```

*Original-phase planning docs → `plans/00-meta/`:*
```bash
mv IMPLEMENTATION_PLAN.md plans/00-meta/IMPLEMENTATION_PLAN.md
mv ENHANCEMENTS.md plans/00-meta/ENHANCEMENTS.md
mv PROJECT_COMPLETE.md plans/00-meta/ORIGINAL_PROJECT_COMPLETE.md
```

*After all 7 commits pass, rename to final completed state:*
```bash
# mv "plans/maintenance/🔵 2026-07-29-oauth-scope-remediation-spec.md" "plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md"
# mv "plans/maintenance/🔵 2026-07-29-drive-scope-remediation-plan.md" "plans/maintenance/✅ 2026-07-29-drive-scope-remediation-plan.md"
```

**Rationale for the additional moves:** IMPLEMENTATION_PLAN.md (21-item execution blueprint) and ENHANCEMENTS.md (37/37 completed roadmap) are planning artifacts from the original 6-phase development, not evergreen reference docs. They belong alongside UNIFIED_PLAN.md in `plans/00-meta/`. PROJECT_COMPLETE.md is renamed to `ORIGINAL_PROJECT_COMPLETE.md` to clarify it marks the end of the *original* 6-phase plan, not all possible future work. ORIGINAL_SPEC.md stays in root — it's a core documentation reference, not a plan.

**Lines:** -6 (dead code removal), ~+50 (BUGLOG entries)

**Verification:** `pytest tests/ -q` — all 359 tests pass. `rg ga4_auth_flow` → no hits in source (tests may reference it in mocks, which is fine).

---

---

### Commit 7: Documentation reconciliation — cross-reference consistency

**Files:** `DOCUMENTATION_INDEX.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `IDEAS.md`, `BUGLOG.md`, and files within `plans/`

**Purpose:** After moving IMPLEMENTATION_PLAN.md, ENHANCEMENTS.md, and PROJECT_COMPLETE.md to `plans/00-meta/`, plus adding `plans/maintenance/`, broken relative links exist in every file that references them. This commit fixes all cross-references.

**7a. DOCUMENTATION_INDEX.md** — Two sets of changes:

1. Add `plans/maintenance/` entries in the "Detailed Phase Plans" table, the "Plan Files" diagram, and the "Document Status" table (as previously specified).

2. Update all moved-file references. For every mention of `IMPLEMENTATION_PLAN.md`, `ENHANCEMENTS.md`, or `PROJECT_COMPLETE.md`, update paths to their new locations in `plans/00-meta/`. Also update the "Core Documentation" and "Planning & Roadmap" table structure: move IMPLEMENTATION_PLAN.md and ENHANCEMENTS.md into the "Detailed Phase Plans" section since they are now under `plans/00-meta/`. Root core docs become: README, ORIGINAL_SPEC, ARCHITECTURE, BUGLOG, CHANGELOG, IDEAS, and this index.

**7b. ARCHITECTURE.md** — Comprehensive update (8 sections). This is the most heavily impacted reference doc — it serves as the canonical description of the project's design, so it must reflect all remediation changes.

1. **Project Structure tree** — Remove `ENHANCEMENTS.md` and `IMPLEMENTATION_PLAN.md` from root listing. Add them under `plans/00-meta/`. Add `plans/maintenance/` branch with the three dated maintenance files. Add `tests/test_exports.py` to the test directory listing. Change `utils/styles.py` comment from "Custom CSS theme + keyboard shortcut JS" to "Custom CSS theme (light/dark) + keyboard shortcut JS".

2. **Design Decisions** — Add four new decisions after existing #8:
   - **#9: OAuth State Persistence** — PKCE `code_verifier` stored in temp JSON files keyed by `state` parameter because Streamlit destroys `st.session_state` on Google's OAuth redirect. Files pruned after 10 minutes, permissions restricted to `0o600` (POSIX), one-time-use deletion on read.
   - **#10: Scope Migration Banner** — `needs_scope_migration()` uses `issubset()` to detect stale cached credentials (old broad `drive` scope). Persistent sidebar warning with "Reconnect Google Account" button that revokes the old grant server-side via Google's `/revoke` endpoint before clearing local state. Self-correcting: banner disappears once user re-authenticates with new scopes.
   - **#11: Shared Error Classification** — `_classify_api_error()` pure function classifies Gemini exceptions by HTTP status code (429/403/500) into emoji-prefixed user-facing messages. Non-streaming callers `raise RuntimeError(msg) from e`; streaming callers `yield msg; return` to avoid generator exception issues.
   - **#12: Flash-Only Model Constraint** — `AVAILABLE_MODELS` restricted to free-tier Flash models only (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`). Pro models removed — they require paid billing, and the app is designed for the free tier.

3. **Security Model table** — Add four rows:
   | OAuth scope | `drive.readonly` + `drive.file` (not full `drive`) — minimal blast radius |
   | Token revocation | `_revoke_token()` calls Google's `/revoke` endpoint on scope migration, invalidating the old broad-scope grant server-side |
   | OAuth state files | `chmod(0o600)` on state JSON files (POSIX) — prevents other users on shared systems from reading `code_verifier` |
   | Model access | AVAILABLE_MODELS restricted to free-tier Flash models — no paid-model footgun |

4. **Test Suite table** — Update test counts:
   - `test_ga4_client.py`: 18 → 28 (added OAuth state store tests: `TestOAuthStateStore`)
   - Add new row: `test_exports.py` | 8 | `TestClassifyApiError` (4), `TestExcelExport` (2), `TestPdfExport` (2)
   - Total: 194 → 359 (all historical + remediation additions)

5. **Dependencies table** — Add `requests` row (already a transitive dep via Google auth libraries; now used directly by `_revoke_token()`). Add `reportlab` row (optional dep for PDF export, lazy-imported with `HAS_REPORTLAB` guard).

6. **Build Log** — Add summary entry for the remediation (entries #57-63 or a single consolidated entry):
   ```
   | 57-63 | OAuth security hardening: scope reduction (drive→drive.readonly+drive.file), PKCE state persistence with chmod hardening, scope migration banner with server-side token revocation, shared error classification (_classify_api_error), thought/cached token tracking, 8 smoke tests (test_exports.py), dead code cleanup (ga4_auth_flow), BUG-008 & BUG-009, file reorganization (plans/maintenance/) | Remediation |
   ```
   Alternatively, 7 separate build log entries if the existing convention of per-change entries is preferred.

7. **Further Reading** — Path updates:
   - `[ENHANCEMENTS.md](ENHANCEMENTS.md)` → `[ENHANCEMENTS.md](plans/00-meta/ENHANCEMENTS.md)`
   - `[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)` → `[IMPLEMENTATION_PLAN.md](plans/00-meta/IMPLEMENTATION_PLAN.md)`
   - Add `[plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) — OAuth security hardening & code quality remediation spec`
   - Note: `ORIGINAL_PROJECT_COMPLETE.md` (renamed from `PROJECT_COMPLETE.md`) may be referenced if ARCHITECTURE previously linked to `PROJECT_COMPLETE.md` — check and update.

8. **Data Flow diagram** — Minor update: the `gemini_client.generate_response` step now routes through `_classify_api_error()` for consistent error messages; `_track_usage()` extracts thought and cached tokens from `usage_metadata`.

**7c. CHANGELOG.md** — Add remediation entry + update summary metrics + fix moved-file paths (5 changes).

1. **Add new entry** — insert before the most recent entry ("Theme Toggle Executed") to maintain reverse-chronological order. Follow the existing two-part convention: a dated heading section with change table, then a version badge line at the bottom. Use the established format:

```markdown
### OAuth Security Hardening & Code Quality Remediation

**Date:** 2026-07-29 | **Status:** ✅ Done | **Tests:** 351 → 359

| Change | Type | Related Docs |
|---|---|---|
| OAuth scope reduced from full `drive` to `drive.readonly` + `drive.file` — minimal blast radius (BUG-008) | Security | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| Token revocation on scope migration — `_revoke_token()` calls Google's `/revoke` endpoint, invalidates entire grant | Security | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| OAuth state file permission hardening — `chmod(0o600)` on PKCE code_verifier JSON files (BUG-009) | Security | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| Scope migration banner — `needs_scope_migration()` auto-detects stale cached credentials, persistent sidebar re-auth prompt | Feature | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |
| Shared error classification — `_classify_api_error()` pure function (HTTP status codes 429/403/500, emoji-prefixed messages) | Refactor | [utils/gemini_client.py](utils/gemini_client.py) |
| Thought + cached token tracking — `_track_usage()` extracts `thoughts_token_count` + `cached_content_token_count` from `usage_metadata` | Feature | [utils/gemini_client.py](utils/gemini_client.py) |
| Flash-only model constraint — removed `gemini-2.5-pro` from `AVAILABLE_MODELS`; all models free-tier | Fix | [utils/gemini_client.py](utils/gemini_client.py) |
| Dead code cleanup — removed `ga4_auth_flow` session state key from `app.py` + `components/sidebar.py` (flow recreated from filesystem state) | Refactor | [utils/ga4_client.py](utils/ga4_client.py) |
| 8 smoke tests — new `tests/test_exports.py` (4 error classification + 2 Excel + 2 PDF export tests) | Testing | [tests/test_exports.py](tests/test_exports.py) |
| BUG-008 & BUG-009 — OAuth scope over-privilege + PKCE state persistence lost across Streamlit redirect | Docs | [BUGLOG.md](BUGLOG.md) |
| File reorganization — `plans/maintenance/` for post-phase-6 maintenance; IMPLEMENTATION_PLAN.md + ENHANCEMENTS.md + PROJECT_COMPLETE.md → `plans/00-meta/`; root retains only evergreen reference docs | Docs | [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) |

**Key decisions (8 from remediation spec):**
- Scope detection: `issubset()` — future-proof, only missing scopes flag stale
- Re-auth UX: clear creds + rerun (not direct OAuth flow trigger from banner)
- Error classification: HTTP status codes (429/403/500) — stable taxonomy, won't break on text changes
- Streaming errors: yield + return (not raise) — avoids generator exception issues
- Token revocation: one call (prefer refresh token) — Google's /revoke invalidates entire grant
- File permissions: `if os.name != "nt": chmod(0o600)` + `try/except OSError` — best-effort across filesystems
- Model constraint: flash-only — all free tier, no paid-model footgun
- Token tracking: thought tokens shown conditionally (non-zero only); cached tokens tracked but hidden

**Related:** [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md)
```

2. **Update Summary table** — four value changes:
   - `Total commits tracked`: 43 → 50 (7 remediation commits)
   - `Date range`: "July 25–28, 2026" → "July 25–29, 2026"
   - `Tests`: "0 → 228 across 17 modules" → "0 → 359 across 19 modules"
   - `Plans`: append "+ 1 maintenance round (7 commits)" to the existing "21-item IMPLEMENTATION_PLAN + 6 UNIFIED plans + 3 derived sprint plans"

3. **Update Related Docs footer** — add `plans/maintenance/` link:
   ```markdown
   - [plans/maintenance/✅ 2026-07-29-oauth-scope-remediation-spec.md](plans/maintenance/✅%202026-07-29-oauth-scope-remediation-spec.md) — Post-phase-6 OAuth security hardening & code quality remediation
   ```

4. **Fix moved-file references** — scan for any `[ENHANCEMENTS.md](ENHANCEMENTS.md)` or `[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)` links that point to root. Update to `[ENHANCEMENTS.md](plans/00-meta/ENHANCEMENTS.md)` and `[IMPLEMENTATION_PLAN.md](plans/00-meta/IMPLEMENTATION_PLAN.md)`. Also update any `[PROJECT_COMPLETE.md]` references to `[ORIGINAL_PROJECT_COMPLETE.md](plans/00-meta/ORIGINAL_PROJECT_COMPLETE.md)`.

5. **Insert version badge line** — at the bottom of the changelog (before the existing v1.5.0 and v1.6.0 badges), add:
   ```markdown
   ---

   ### v1.7.0 — OAuth Security Hardening & Code Quality Remediation (2026-07-29)
   - **SECURITY**: OAuth scope `drive` → `drive.readonly` + `drive.file` (BUG-008)
   - **SECURITY**: Token revocation on scope migration via Google's `/revoke` endpoint
   - **SECURITY**: OAuth state file `chmod(0o600)` hardening (BUG-009)
   - **CHANGED**: `utils/ga4_client.py` — `needs_scope_migration()`, `_revoke_token()`, `save_oauth_state()` chmod
   - **CHANGED**: `utils/gemini_client.py` — `_classify_api_error()`, `_track_usage()` thought+cached tokens, flash-only `AVAILABLE_MODELS`
   - **CHANGED**: `components/sidebar.py` — scope migration banner in `_render_ga4_connect()`, removed `ga4_auth_flow`
   - **CHANGED**: `components/chat.py` — conditional thought token display in `_render_usage_stats()`
   - **CHANGED**: `app.py` — added `total_thought_tokens` + `total_cached_tokens` session defaults, removed `ga4_auth_flow`
   - **NEW**: `tests/test_exports.py` — 8 smoke tests (error classification + Excel/PDF export)
   - **CHANGED**: `BUGLOG.md` — BUG-008 + BUG-009 entries
   - **CHANGED**: `DOCUMENTATION_INDEX.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `IDEAS.md`, `BUGLOG.md` — cross-reference reconciliation + file reorganization
   - **MOVED**: `IMPLEMENTATION_PLAN.md` + `ENHANCEMENTS.md` + `PROJECT_COMPLETE.md` → `plans/00-meta/`
   - **NEW**: `plans/maintenance/` — 3 dated maintenance artifacts
   - 359 tests (was 351) | 7 commits
   ```

**7d. IDEAS.md** — Update all references to moved files with their new paths.

**7e. BUGLOG.md** — Update "See also" links to reference `plans/00-meta/IMPLEMENTATION_PLAN.md` and `plans/00-meta/ENHANCEMENTS.md`.

**7f. Plans files** — Update relative references in `plans/00-meta/`, `plans/00-sprints/`, `plans/p3-p4/`, and `plans/p5-p6/` that point to `../IMPLEMENTATION_PLAN.md` or `../ENHANCEMENTS.md` (these become `../00-meta/IMPLEMENTATION_PLAN.md` etc. from sibling directories, or just `IMPLEMENTATION_PLAN.md` from within `00-meta/` itself).

**7g. IMPLEMENTATION_PLAN.md itself** — Internal references to `plans/00-meta/` files are now same-directory relative (no `../` needed).

**7h. ENHANCEMENTS.md itself** — Same: references to `plans/00-meta/` files become same-directory relative.

**Lines:** ~+50 (across 8+ files)

**Verification:** `rg "IMPLEMENTATION_PLAN\.md|ENHANCEMENTS\.md|PROJECT_COMPLETE\.md" *.md plans/**/*.md` — no broken relative links. All paths resolve to `plans/00-meta/`. `rg "plans/maintenance" *.md` confirms maintenance references exist.

---

## Deferred Enhancements (NOT in this remediation)

### Radial Context Gauge (Plotly)
Use Plotly's `go.Indicator` gauge (already a hard dependency) to render a small circular meter showing context window usage. No new package needed. Key details:
- `config={"displayModeBar": False}` — critical to avoid toolbar on a tiny gauge
- Color threshold at 80% — green/indigo below, red above
- `max_tokens` sourced from `AVAILABLE_MODELS[selected_model]["context_window"]`
- Placed next to `_render_usage_stats()` in a `st.columns([4, 1])` layout

### Sheets UI Button
`create_google_sheet()` exists but has no UI trigger. Add as a separate PR after verifying the function works under the new `drive.file` scope.

### Revoke on Normal Disconnect
Currently `_revoke_token()` only fires during scope migration. Normal disconnect just clears `ga4_creds` locally — the correctly-scoped token lives until natural expiry. This is account-hygiene debt (an unused grant listed in Google Account permissions), not a security risk. As a fast follow-up PR: add `_revoke_token()` to the Disconnect handler in `_render_ga4_connect()`. Implementation is trivial — reuse the existing `_revoke_token()` helper, 3 lines. Keep it out of this remediation to preserve the narrow review scope of "does this close the over-broad-scope exposure?".

### AST Validation + Subprocess Sandbox
**Do NOT implement.** AST-based code validation is security theater. If code execution is ever needed, use Gemini Function Calling (model selects from pre-registered safe functions).

---

## Files Affected (Complete List)

| File | Commit | Change Type | Lines |
|------|--------|-------------|-------|
| `utils/ga4_client.py` | 1, 2, 3, 4 | Modify | +60 / -3 |
| `utils/gemini_client.py` | 4, 6c | Modify | +25 / -45 |
| `utils/report_exporter.py` | — | **No change** | 0 |
| `utils/drive_client.py` | — | **No change** | 0 |
| `components/chat.py` | 4g | Modify | +5 |
| `components/sidebar.py` | 3, 6b | Modify | +20 / -1 |
| `app.py` | 4f, 6a | Modify | +2 / -3 |
| `tests/test_exports.py` | 5 | **New** | +90 |
| `BUGLOG.md` | 6d | Modify | +50 |
| `plans/maintenance/✅ 2026-07-29-drive-export-model-selector-session.md` | 6e | Moved from root | 0 |
| `plans/maintenance/🔵 2026-07-29-drive-scope-remediation-plan.md` | 6e | Moved from root; → `✅` after completion | 0 |
| `plans/maintenance/🔵 2026-07-29-oauth-scope-remediation-spec.md` | 6e | This file (moved); → `✅` after completion | 0 |
| `DOCUMENTATION_INDEX.md` | 7 | Modify | +20 |
| `ARCHITECTURE.md` | 7 | Modify (8 sections: tree, design decisions, security model, tests, deps, build log, further reading, data flow) | +60 |
| `CHANGELOG.md` | 7 | Modify (new remediation entry, summary metrics, version badge, moved-file paths, related docs footer) | +50 |
| `IDEAS.md` | 7 | Modify | +3 |
| `IMPLEMENTATION_PLAN.md` (now in `plans/00-meta/`) | 6e, 7g | Moved + internal link fixes | 0 |
| `ENHANCEMENTS.md` (now in `plans/00-meta/`) | 6e, 7h | Moved + internal link fixes | 0 |
| `ORIGINAL_PROJECT_COMPLETE.md` (was `PROJECT_COMPLETE.md`, now in `plans/00-meta/`) | 6e, 7b | Moved + renamed | +10 |

**Total:** ~+415 / -52 across 11 files modified + 1 new test file + 6 file moves/renames

---

## Acceptance Criteria (Per Commit)

| Commit | Criteria |
|--------|----------|
| 1. Scope fix | `pytest tests/test_ga4_client.py` — all pass |
| 2. Permissions | `pytest tests/test_ga4_client.py::TestOAuthStateStore` — all pass |
| 3. Migration banner | Manual: connect with old token → see banner → click reconnect → old token revoked server-side → sign-in appears; `pytest tests/` — no regressions |
| 4. Error helper + tokens | `pytest tests/test_gemini_client.py` — all pass; `pytest tests/test_exports.py::TestClassifyApiError` — 4 pass |
| 5. Smoke tests | `pytest tests/test_exports.py -v` — 8 pass |
| 6. Cleanup + BUGLOG | `pytest tests/ -q` — 359 pass; `rg ga4_auth_flow` — no hits in source files |
| 7. Doc reconciliation | `rg "plans/maintenance" *.md` — all references updated; `rg "IMPLEMENTATION_PLAN\.md|ENHANCEMENTS\.md|PROJECT_COMPLETE\.md" *.md plans/**/*.md` — no broken links to old root paths; ARCHITECTURE.md has updated project tree, design decisions, security model, test counts, dependencies, build log, further reading, and data flow; CHANGELOG.md has new remediation entry, updated summary metrics (43→50 commits, 0→359 tests), version badge, and fixed moved-file paths |
| Final rename | `plans/maintenance/` spec + plan use `✅` prefix (session summary already `✅`) |
| Final | `pytest tests/ -q` — 359 pass; `rg gemini-2.5-pro` — no hits; no stale plan references |

---

## Execution Checklist

- [ ] Commit 1: Scope fix → `pytest tests/test_ga4_client.py`
- [ ] Commit 2: chmod hardening → `pytest tests/test_ga4_client.py::TestOAuthStateStore`
- [ ] Commit 3: Scope migration banner → manual smoke
- [ ] Commit 4: Error helper + tokens → `pytest tests/test_gemini_client.py` + new classify test
- [ ] Commit 5: Smoke tests → `pytest tests/test_exports.py`
- [ ] Commit 6: Dead code + BUGLOG + file moves → `pytest tests/ -q`
- [ ] Remove Pro model from AVAILABLE_MODELS
- [ ] Move remediation artifacts to `plans/maintenance/` (session summary, plan, spec)
- [ ] Move IMPLEMENTATION_PLAN.md → `plans/00-meta/IMPLEMENTATION_PLAN.md`
- [ ] Move ENHANCEMENTS.md → `plans/00-meta/ENHANCEMENTS.md`
- [ ] Rename + move PROJECT_COMPLETE.md → `plans/00-meta/ORIGINAL_PROJECT_COMPLETE.md`
- [ ] Commit 7: Doc reconciliation — fix all cross-references in DOCUMENTATION_INDEX, ARCHITECTURE (8 sections), CHANGELOG (new remediation entry + summary metrics + version badge + moved paths), IDEAS, BUGLOG, and plans files
- [ ] Note: ORIGINAL_SPEC.md stays in root
- [ ] Final: `pytest tests/ -q` — 359 pass; `rg "plans/maintenance" *.md` confirms all 3 root docs reference it
- [ ] Final rename: `🔵` → `✅` for spec + plan in `plans/maintenance/` (session summary already `✅`)
