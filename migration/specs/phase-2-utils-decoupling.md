# Phase 2 — Decouple `utils/` from Streamlit (executable)

> ✅ **DONE** (2026-08-06) — Gate closed. Implemented on branch **`feat/react-fastapi-migration`** (commit `8c66eea`). Full regression **794 passed**, guard exit 0, hooks green. See [Gate table](#gate-table--phase-2-gate) for closure evidence.
> **Shipped:** `utils/caching.py` content-fingerprint LRU memo (`RLock`-guarded, bounded 32-entry default, injectable sizing, test-reset hook) + `tests/test_caching.py` (content identity, LRU eviction, byte-budget behavior, reset, concurrent access) · framework-neutral `utils/gemini_client.py` with structured `UsageEvent` + injected `usage_sink` · Streamlit-owned usage accounting wired from `chat.py`/`summary.py`/`data_preview.py` · Streamlit cache removed from shared modules; forecasting migrated to the fingerprint cache · `load_file()` adapter swap + structured upload truncation warnings · Streamlit-only quarantine banners + dynamic-import boundary guard (`tests/test_utils_import_boundary.py`).
> All four decisions confirmed with upgrades (thread-safe memo, safe-field `UsageEvent`, structured `DatasetWarning`, quarantine banner + guard): see [Confirmed decisions](#confirmed-decisions-2026-08-06-product-owner). **Branch-state note:** implementation lives on `feat/react-fastapi-migration`; `main` carries the reconciled planning/documentation record until migration merge.

## Purpose

Remove Streamlit coupling from the shared `utils/` domain layer so FastAPI and the
future React backend call the **same** parsing, quality, prompt, forecasting, and
Gemini code as the legacy Streamlit app — without importing Streamlit. This is a
**framework-decoupling refactor**, not a feature build. Streamlit behavior stays
identical (feature freeze, `../policies/branch-and-freeze-policy.md`); it simply stops
being a dependency of the shared layer.

Phase 1 shipped temporary adapters (`api/services/dataset_service.parse_uploaded_file`,
`api/services/quality_service.build_quality_report`) that point at the decoupled targets
(`utils/data_loader.load_file()`, `utils.data_loader.assess_data_quality`). Phase 2 makes
those targets truly Streamlit-free and replaces the temporary adapter.

## Verified coupling audit (2026-08-06, mechanical)

`grep -l 'import streamlit' utils/*.py` on `eaa6ac5`:

| Module | Imports `streamlit`? | Coupling detail | Disposition |
|---|---|---|---|
| `utils/data_loader.py` | ✅ | `import streamlit` L9; `@st.cache_data(ttl=600)` on `validate_columns` (L107) + `get_dataset_stats` (L122) | **Decouple** (Task 2) |
| `utils/forecasting.py` | ✅ | `import streamlit` L6; `@st.cache_data(ttl=600)` on `forecast_metric` (L30) | **Decouple** (Task 3) |
| `utils/prompt_templates.py` | ✅ | `import streamlit` L7; `@st.cache_data(ttl=300)` on `build_summary_prompt` (L38) | **Decouple** (Task 4) |
| `utils/gemini_client.py` | ✅ | Lazy `import streamlit as st` inside `_track_usage` (L156) — accumulates `total_*_tokens`, `api_success_count`, and attaches usage to `chat_history[-1]` | **Decouple** (Task 5) |
| `utils/session.py` | ✅ | `import streamlit` L3; `clear_data()` writes 44-key session state directly | **Quarantine** (Task 6) — Streamlit-only |
| `utils/error_boundary.py` | ✅ | `import streamlit` L8; `render_error_card()` renders `st.error`/`st.expander` UI | **Quarantine** (Task 6) — Streamlit-only |
| `utils/styles.py` | ✅ | `import streamlit` L10; `inject_custom_css`/`inject_favicon_meta`/`build_theme_css` are presentation-only | **Quarantine** (Task 6) — Streamlit-only |
| `utils/data_context.py` | ❌ | Already pure (pandas + hashlib only) — 112 tests transfer untouched | **Verify only** (Task 8) |
| `utils/ga4_client.py` | ❌ | Pure HTTP/OAuth layer | **Verify only** (Task 8) |
| `utils/drive_client.py` | ❌ | Pure HTTP layer | **Verify only** (Task 8) |
| `utils/charts.py` | ❌ | Pure plotly/pandas | **Verify only** (Task 8) |
| `utils/funnels.py` | ❌ | Pure pandas | **Verify only** (Task 8) |
| `utils/commands.py` | ❌ | Pure parsing | **Verify only** (Task 8) |
| `utils/sanitize.py` | ❌ | Pure string handling | **Verify only** (Task 8) |
| `utils/report_exporter.py` | ❌ | Pure pandas/plotly | **Verify only** (Task 8) |
| `utils/__init__.py` | ❌ | Empty — no re-export trap | Keep empty |

**Summary:** 4 modules decouple, 3 modules quarantine, 9 already clean. `api/` and
`tests/api/` currently import no Streamlit anywhere (verified empty grep) — this phase
must keep it that way.

## Inputs / source documents

- `../policies/session-state-inventory.md` — the 44-key replacement map; Phase 2 consumes
  the subset owned by `utils/session.clear_data()` and `utils/gemini_client._track_usage`
- `../policies/test-layer-inventory.md` — 452 utils-facing tests transfer; 290 Streamlit-layer
  rewrite/retire (Phase 2 only *keeps the 452 green*; the 290 retire in Phase 6)
- `../archive/insights-explorer-migration-ingest.md` §4.2 (reconciliation: 7/16 coupling) +
  §3.10 (Gemini behavior notes)
- master-plan §6 (Phase 2 shape) and §11 track A
- `phase-1-upload-slice.md` §7–§9 (the adapters this phase replaces; error taxonomy must not change)

## Tracks consumed

- **A** (state/session): `clear_data()`'s keys are the checklist subset; no **new**
  `st.session_state` keys may be added (freeze policy). Replacement of keys is documented
  per `session-state-inventory.md` §7 — the server `clear_dataset_state()` (Phase 1)
  already owns the destination namespace.
- **B** (API/contract): the Phase 1 upload error taxonomy (400/409/410/413/415/422) stays
  identical when `parse_uploaded_file()` → `utils/data_loader.load_file()`.
- **C** (tests): 452 utils-facing tests stay green; add import-boundary guard tests;
  the 290 Streamlit-layer tests remain green but are **not** ported in this phase.
- **D** (security): no new secrets; guard allowlist unchanged; `api/` remains Streamlit-free.
- **F** (retention/AI): Clear Data semantics unchanged — `clear_dataset_state()` already
  policy-real; `utils/session.clear_data()` remains the Streamlit-side twin until Phase 6.

## Research gate

**None required** — internal refactoring; no external platform facts. Do **not** dispatch
a research agent for Phase 2 (research-gating policy, archive §3.12).

## Non-goals (do not do in this phase)

- No React/UI work (Phase 4).
- No GA4/Drive/Gemini API endpoints (Phases 3/5) — Gemini decoupling is **infrastructure**
  only; the `/api/chat` endpoint stays out.
- No retirement of the 290 Streamlit-layer tests (Phase 6).
- No new caching framework beyond the fingerprint-keyed memo described in Task 3.
- No changes to `api/schemas.py` response shapes or the 25 MB/100 MB upload policy.
- No removal of `utils/styles.py`, `utils/error_boundary.py`, `utils/session.py` from the
  tree — they are **quarantined** (still used by Streamlit until Phase 6), not deleted.

---

## Task sequence: Preconditions + 10 implementation/acceptance tasks

### 0. Preconditions

- On `feat/react-fastapi-migration`; Phase 1 committed (`eaa6ac5`) and pushed.
- `pytest tests -q` baseline green (772 collected incl. Phase 1 contract tests).
- `python3 scripts/check_credentials.py` passes on all tracked files.

### 1. Import-boundary guard (foundation — write first, runs forever)

Add a static guard that fails CI if any shared-domain module regresses into Streamlit:

**`tests/test_utils_import_boundary.py`** (new):

```python
"""Phase 2 guard: shared utils/ modules must never import streamlit."""

import ast
from pathlib import Path

SHARED_MODULES = [
    "data_loader",
    "data_context",
    "forecasting",
    "prompt_templates",
    "gemini_client",
    "ga4_client",
    "drive_client",
    "charts",
    "funnels",
    "commands",
    "sanitize",
    "report_exporter",
]

# Streamlit-only modules that MAY import streamlit (quarantined, Task 6).
QUARANTINED = {"styles", "error_boundary", "session"}


QUARANTINED_NAMES = {"styles", "error_boundary", "session"}
QUARANTINED_PATHS = {"utils.styles", "utils.error_boundary", "utils.session"}


def _imports_streamlit(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "streamlit" for a in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "streamlit":
            return True
    return False


def _imports_quarantined(tree: ast.AST) -> bool:
    """True if the tree imports a quarantined module in any form.

    Review fix (2026-08-06): the module, not the imported symbol, is the
    boundary. ``from utils.styles import inject_global_styles`` must be caught
    even though the symbol name is not ``styles``.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            # ``import utils.styles`` — module path is the boundary.
            if any(alias.name in QUARANTINED_PATHS for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom):
            # ``from utils.styles import foo`` is ALWAYS quarantined.
            if node.module in QUARANTINED_PATHS:
                return True
            # ``from utils import styles`` is quarantined (symbol name = module).
            if node.module == "utils":
                if any(alias.name in QUARANTINED_NAMES for alias in node.names):
                    return True
    return False


def _api_and_shared_paths():
    yield from Path("api").rglob("*.py")
    for name in SHARED_MODULES:
        yield Path("utils") / f"{name}.py"


def test_no_streamlit_in_shared_utils() -> None:
    for name in SHARED_MODULES:
        path = Path("utils") / f"{name}.py"
        assert path.exists(), f"module list drift: {path}"
        tree = ast.parse(path.read_text())
        assert not _imports_streamlit(tree), f"{name}.py must not import streamlit"


def test_no_streamlit_in_api() -> None:
    for path in Path("api").rglob("*.py"):
        tree = ast.parse(path.read_text())
        assert not _imports_streamlit(tree), f"{path} must not import streamlit"


def test_no_quarantined_imports_in_api_or_shared() -> None:
    """api/** and framework-neutral utils/** must not import the quarantined trio.
    Streamlit may import them; the API boundary may not (refined 2026-08-06)."""
    for path in _api_and_shared_paths():
        tree = ast.parse(path.read_text())
        assert not _imports_quarantined(tree), (
            f"{path} must not import a STREAMLIT-ONLY module"
        )


def _is_quarantined_source(source: str) -> bool:
    return _imports_quarantined(ast.parse(source))


def test_import_forms_all_caught() -> None:
    """Every import form of a quarantined module must be caught (review fix)."""
    assert _is_quarantined_source("import utils.styles")
    assert _is_quarantined_source("from utils import styles")
    assert _is_quarantined_source("from utils.styles import inject_global_styles")
    assert _is_quarantined_source("from utils.session import initialize_session_state")
    assert _is_quarantined_source("from utils.error_boundary import render_error")
    # Sanity: legit imports are NOT flagged.
    assert not _is_quarantined_source("from utils import data_loader")
    assert not _is_quarantined_source("from utils.data_loader import load_file")
    assert not _is_quarantined_source("import streamlit as st")
    assert not _is_quarantined_source("import pandas as pd")


def test_quarantine_banners_present() -> None:
    for name in QUARANTINED:
        path = Path("utils") / f"{name}.py"
        assert "STREAMLIT-ONLY" in path.read_text(), (
            f"{name}.py missing STREAMLIT-ONLY banner (Task 6)"
        )
```

**Acceptance:** `pytest tests/test_utils_import_boundary.py -q` passes **before** any
decoupling edit (it fails on `data_loader`/`forecasting`/`prompt_templates` initially —
that is the red state that defines the phase).

**Dynamic-import bypasses are prohibited (added 2026-08-06):** static AST scanning
cannot catch `importlib.import_module("utils.styles")` or `__import__("utils.session")`.
Policy: `api/**` and shared `utils/**` modules may **not use dynamic imports at all**
(`importlib` / `__import__` forms), except through an explicit, reviewed allowlist — none
currently exists. `tests/test_utils_import_boundary.py` scans `_api_and_shared_paths()`
for the `importlib`/`__import__` call and import forms and fails on any occurrence
(implemented on the migration branch with `test_no_dynamic_imports_in_api_or_shared` +
`test_dynamic_import_forms_flagged`). `pd.eval()` / `df.eval()` are **not** dynamic imports
and are deliberately not flagged.

### 2. Decouple `utils/data_loader.py`

- Remove `import streamlit as st` (L9).
- Remove both `@st.cache_data(ttl=600, show_spinner=False)` decorators (L107, L122) —
  `validate_columns` and `get_dataset_stats` become plain functions.
- **Keep** the `_ruleset_version`/`_schema_version` hidden-parameter convention — it is
  the cache-invalidation contract; a future server cache keyed on
  `DataContext.cache_key` will use it.
- **Keep** `load_file()`'s signature `(file) -> (df, error, warning)` and its
  `MAX_FILE_SIZE_MB = 100` / `MAX_ROWS = 50_000` internal guards. The API's 25 MB
  browser cap (enforced in the route before parsing) is the outer guard; `load_file`'s
  100 MB check remains as defense-in-depth for the server-side Drive path (Phase 5).
- Behavior note for Streamlit: losing `st.cache_data` means stats/column checks
  recompute on each rerun. **Acceptable** — data is in-memory, Streamlit is frozen and
  retiring in Phase 6; do not re-add a Streamlit cache shim to shared code.

```python
# After edit — these two become:
def validate_columns(
    df: pd.DataFrame,
    _ruleset_version: str = QUALITY_RULESET_VERSION,
) -> list[str]:
    ...  # body unchanged

def get_dataset_stats(
    df: pd.DataFrame,
    _ruleset_version: str = QUALITY_RULESET_VERSION,
) -> dict[str, Any]:
    ...  # body unchanged
```

**Acceptance:** `grep -n streamlit utils/data_loader.py` → empty;
`pytest tests/test_data_loader.py tests/test_data_quality.py -q` green (38 tests).

### 3. Decouple `utils/forecasting.py`

- Remove `import streamlit as st` (L6).
- Remove `@st.cache_data(ttl=600, show_spinner=False)` (L30) from `forecast_metric`.

`forecast_metric` is the one **expensive** pure function in the shared layer, so add a
small framework-neutral fingerprint-keyed memo (new `utils/caching.py`) and apply it to
`forecast_metric` only:

```python
# utils/caching.py (new)
"""Framework-neutral, thread-safe memoization keyed on DataFrame content fingerprint.

Design rules (confirmed + refined P0 + review fix, 2026-08-06):
- Key: (fingerprint(df), rest args, sorted kwargs) — content identity, not object id.
- Value: immutable computed result only — never a mutable DataFrame reference.
- Bounded: max entries (default 32) AND an OPTIONAL byte budget (default None).
- Thread-safe: RLock guards every cache mutation (FastAPI worker threads).
- cache_clear() exposed for tests; no session-state dependency; no Streamlit import.
- byte_budget is an APPROXIMATE object-overhead guard, not a guaranteed memory
  cap: sys.getsizeof measures shallow Python object size only, not arrays,
  nested lists, Pandas objects, or model internals. Sizing is injectable so a
  domain-specific sizeof_forecast_result() can be supplied later if memory
  pressure becomes real.
"""
from __future__ import annotations

import sys
from collections import OrderedDict
from threading import RLock
from typing import Any, Callable

from utils.data_context import fingerprint_frame


def memoize_fingerprint(
    maxsize: int = 32,
    byte_budget: int | None = None,
    sizeof: Callable[[Any], int] = sys.getsizeof,
):
    """Memoize a function whose first argument is a DataFrame.

    Key = (fingerprint(df), args, sorted-kwargs); rest args must be hashable.
    Defaults (review fix 2026-08-06): maxsize=32, byte_budget=None — the LRU
    count is predictable, while an uninstrumented byte budget would create
    false confidence. Pass sizeof= when you have an accurate size estimator.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        cache: OrderedDict[tuple, Any] = OrderedDict()
        retained_bytes: dict[tuple, int] = {}
        lock = RLock()

        def _evict(count: int = 1) -> None:
            for _ in range(count):
                if not cache:
                    return
                oldest = next(iter(cache))
                cache.pop(oldest)
                retained_bytes.pop(oldest, None)

        def wrapper(df, *args, **kwargs):
            key = (fingerprint_frame(df), args, tuple(sorted(kwargs.items())))
            with lock:
                if key in cache:
                    cache.move_to_end(key)
                    return cache[key]
            result = fn(df, *args, **kwargs)  # compute outside the lock
            with lock:
                if key in cache:  # another thread won the race
                    return cache[key]
                cache[key] = result
                cache.move_to_end(key)
                if byte_budget is not None:
                    retained_bytes[key] = sizeof(result)
                if len(cache) > maxsize:
                    _evict(len(cache) - maxsize)
                if byte_budget is not None:
                    while sum(retained_bytes.values()) > byte_budget and len(cache) > 1:
                        _evict(1)
            return result

        def clear() -> None:
            with lock:
                cache.clear()
                retained_bytes.clear()

        wrapper.cache_clear = clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
```

Apply in `utils/forecasting.py`:

```python
from utils.caching import memoize_fingerprint

@memoize_fingerprint()
def forecast_metric(df: pd.DataFrame, ...) -> ForecastResult:
    ...  # body unchanged
```

**Confirmed + refined + review-fixed (P0, 2026-08-06):** keep the fingerprint memo —
bounded, **thread-safe** (`RLock`), `cache_clear()` for tests, no session-state
dependency. **Review fix:** defaults are `maxsize=32`, `byte_budget=None` (predictable
LRU count; no fake memory cap without an accurate estimator); `sizeof` is injectable;
byte budget is documented as an *approximate* object-overhead guard. Rejected
alternative: plain function + Phase 3 server cache.

**Acceptance:** `grep -n streamlit utils/forecasting.py` → empty;
`pytest tests/test_forecasting.py -q` green (31 tests); a new
`tests/test_caching.py` proves the memo returns identical results for an unchanged
frame and recomputes when `fingerprint_frame` differs.

### 4. Decouple `utils/prompt_templates.py`

- Remove `import streamlit as st` (L7).
- Remove `@st.cache_data(ttl=300, show_spinner=False)` (L38) from `build_summary_prompt`.
- Keep `_sanitize_question`, `detect_chart_request`, `build_comparison_prompt` pure as-is.
- `SUMMARY_PROMPT_SCHEMA_VERSION` remains the explicit invalidation knob — the API's
  `POST /api/v1/chat` (Phase 3) will pass it as a parameter.

**Acceptance:** `grep -n streamlit utils/prompt_templates.py` → empty;
`pytest tests/test_prompt_templates.py -q` green (61 tests).

### 5. Decouple `utils/gemini_client.py`

The only coupling is the lazy `import streamlit as st` inside `_track_usage` (L156),
which (a) accumulates `total_*_tokens` session counters, (b) bumps
`api_success_count`, and (c) attaches per-request usage to `chat_history[-1]`.
Replace the hardcoded Streamlit write with an **injectable usage sink** (dependency
injection — the API layer passes `None` or a server-side ledger later; Streamlit
passes a session-state writer, preserving identical behavior):

```python
import logging
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsageEvent:
    """Structured, safe Gemini usage event (confirmed + refined P1, 2026-08-06).

    Contains operational metadata ONLY — NEVER prompt content, raw rows, user
    messages, or model output (Gemini boundary, data-retention-policy §AI).
    Sink failures are best-effort/logged, never fatal.
    """

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model: str = ""
    request_type: str = ""   # e.g. "summary" | "chat" | "chart" (Phase 3 uses it)
    input_tokens: int = 0
    output_tokens: int = 0
    thoughts_token_count: int = 0
    cached_token_count: int = 0  # preserved for the legacy total_cached_tokens counter
    tool_use_token_count: int = 0
    total_token_count: int = 0  # provider-reported total when available (review fix)
    success: bool = True
    sanitized_error_class: str | None = None


def _emit_usage(
    response,
    model: str,
    request_type: str = "",
    success: bool = True,
    error_class: str | None = None,
    usage_sink: Callable[[UsageEvent], None] | None = None,
) -> UsageEvent | None:
    """Build a safe UsageEvent from provider metadata and hand it to the sink.

    Best-effort: a failing sink is logged and never raises — telemetry must not
    break a user request (confirmed P1).
    """
    usage = getattr(response, "usage_metadata", None)
    if usage is None and success:
        return None
    event = UsageEvent(
        model=model,
        request_type=request_type,
        input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
        output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
        thoughts_token_count=getattr(usage, "thoughts_token_count", 0) or 0,
        cached_token_count=getattr(usage, "cached_content_token_count", 0) or 0,
        tool_use_token_count=getattr(usage, "tool_use_token_count", 0) or 0,
        total_token_count=getattr(usage, "total_token_count", 0) or 0,
        success=success,
        sanitized_error_class=error_class,
    )
    # Review fix (2026-08-06): preserve provider semantics — if the provider did
    # NOT report a total, fall back to a documented sum (never silently
    # substitute a weaker number that changes the meaning of the legacy counter).
    if event.total_token_count == 0:
        event = replace(
            event,
            total_token_count=(
                event.input_tokens
                + event.output_tokens
                + event.thoughts_token_count
                + event.cached_token_count
                + event.tool_use_token_count
            ),
        )
    if usage_sink is not None:
        try:
            usage_sink(event)
        except Exception as exc:  # best-effort — telemetry never breaks a request
            # Review fix (2026-08-06): log a generic event with only the error
            # CLASS — never str(exc), which could contain prompt content or raw
            # rows from an arbitrary API ledger or Streamlit sink.
            logger.warning(
                "usage_sink_failed",
                extra={"error_class": type(exc).__name__},
            )
    return event
```

Thread the sink through the public entry points:

```python
def generate_response(
    prompt: str,
    model: str = DEFAULT_MODEL,
    request_type: str = "",
    usage_sink: Callable[[UsageEvent], None] | None = None,
) -> str:
    ...
    _emit_usage(response, model, request_type=request_type, usage_sink=usage_sink)
    ...

def generate_response_stream(
    prompt: str,
    model: str = DEFAULT_MODEL,
    request_type: str = "",
    usage_sink: Callable[[UsageEvent], None] | None = None,
) -> Iterator[str]:
    ...
```

Then move the Streamlit accumulation **out of `utils/`** into the Streamlit layer as a
sink, e.g. `utils/session.py` (quarantined, Task 6) gains:

```python
def _streamlit_usage_sink(event: UsageEvent) -> None:
    """STREAMLIT-ONLY sink — preserves pre-refactor session accounting."""
    for key, value in [
        ("total_input_tokens", event.input_tokens),
        ("total_output_tokens", event.output_tokens),
        ("total_thought_tokens", event.thoughts_token_count),
        ("total_cached_tokens", event.cached_token_count),
        ("total_tokens_used", event.total_token_count),  # provider total (review fix)
    ]:
        if key not in st.session_state:
            st.session_state[key] = 0
        st.session_state[key] += value
    if event.success:  # review fix: only successful requests count (errors may
        # emit usage events later; they must not inflate the success counter)
        if "api_success_count" not in st.session_state:
            st.session_state.api_success_count = 0
        st.session_state.api_success_count += 1
    history = st.session_state.get("chat_history", [])
    if history and "usage" not in history[-1]:
        history[-1]["usage"] = asdict(event)
```

Update Streamlit call sites (`components/chat.py`, `components/summary.py`,
`components/data_preview.py`) to pass `usage_sink=_streamlit_usage_sink` where they
call `generate_response`/`generate_response_stream`. Net behavior identical.

**Confirmed + refined + review-fixed (P1, 2026-08-06):** sink threading with a
structured **`UsageEvent`** — safe operational fields only (never prompt content, raw
rows, user messages, or model output); sink failures are **best-effort/logged** with
only the error class logged (never `str(exc)`). **Review fix:** `total_token_count` and
`tool_use_token_count` added; `total_tokens_used` uses the provider-reported total with
a documented fallback sum; `api_success_count` increments only when `event.success`.
Rejected alternatives: callers accumulate a returned dict; usage events carrying
prompt/response content.

**Acceptance:** `grep -n streamlit utils/gemini_client.py` → empty;
`pytest tests/test_gemini_client.py -q` green (14 tests); chat usage-accounting tests
(Streamlit layer) still green (5 `tests/test_chat.py`).

### 6. Quarantine Streamlit-only modules (`styles`, `error_boundary`, `session`)

Add a **STREAMLIT-ONLY** banner to the module docstring of each of the three:

```python
"""
STREAMLIT-ONLY MODULE.

This module is part of the legacy Streamlit presentation layer.
FastAPI services and framework-neutral utils must not import it.

Migration owner: Phase 6 retirement.
"""
```

Documented replacements (for the record; not implemented in Phase 2):

| Quarantined module | Destination | When |
|---|---|---|
| `utils/styles.py` | React CSS/design tokens; `test_styles.py` (68) retires | Phase 4/6 |
| `utils/error_boundary.py` | React error states; `test_error_boundary.py` (9) → React | Phase 4 |
| `utils/session.py` `clear_data()` | server `clear_dataset_state()` (Phase 1, `api/services/dataset_service.py`) — already policy-real | Phase 2 note only; keys mapped in `session-state-inventory.md` §7 |

The `session.py` `clear_data()` **stays** as-is for Streamlit (it is the twin of the
server method). Its 44-key writes are already inventoried; no new keys.

**Acceptance:** banners present (Task 1 guard test 3 passes); `api/` imports none of
the three (guard test 2 passes); Streamlit suite still green.

### 7. Replace the temporary upload adapter with `utils/data_loader.load_file()`

`api/services/dataset_service.parse_uploaded_file` (Phase 1 temp) is replaced by a
thin wrapper over the now-decoupled `load_file()`, preserving the Phase 1 error
taxonomy **exactly** (spec §8 table: 400 empty · 409 no dataset · 410 expired ·
413 too large · 415 unsupported · 422 unreadable).

```python
# api/services/dataset_service.py — replacement
import re
from io import BytesIO
from pathlib import Path

from utils.data_loader import load_file

from api.schemas import DatasetWarning


class _NamedBytesIO(BytesIO):
    """BytesIO with a .name — the minimal file-like contract load_file needs."""

    def __init__(self, data: bytes, name: str) -> None:
        super().__init__(data)
        self.name = name


class UploadError(Exception):
    """Typed upload failure; route maps to the Phase 1 HTTP status codes."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def parse_uploaded_file(
    filename: str, content: bytes,
) -> tuple[pd.DataFrame, DatasetWarning | None]:
    """Adapter over utils/data_loader.load_file() — single parser, one taxonomy.

    Returns (df, warning) where warning is a structured DatasetWarning when rows
    were truncated (confirmed P2), or None. Errors raise UploadError with the
    Phase 1 status-code mapping.
    """
    df, error, warning = load_file(_NamedBytesIO(content, filename))
    if error is not None:
        status = _error_status(error, filename)
        raise UploadError(status, error)
    structured = None
    if warning is not None:
        structured = DatasetWarning(
            code="rows_truncated",
            message=warning,
            original_row_count=_extract_original_row_count(warning),
            loaded_row_count=len(df),
        )
    return df, structured


def _extract_original_row_count(warning: str) -> int | None:
    """Best-effort parse of the loader's truncation notice; None if format changes."""
    match = re.search(r"Dataset has ([0-9,]+) rows", warning)
    return int(match.group(1).replace(",", "")) if match else None


def _error_status(error: str, filename: str) -> int:
    suffix = Path(filename).suffix.lower()
    if "Unsupported file type" in error or suffix not in {".csv", ".xlsx", ".xls"}:
        return 415
    if "empty" in error.lower():
        return 400
    if "too large" in error.lower():
        return 413
    return 422  # "We couldn't read this file…"
```

Schema change (**confirmed + refined P2**): add a **structured** warnings field to
`api/schemas.py`'s `DatasetContext` so truncation notices travel end-to-end now, not
in Phase 2b/4. Structured warnings (not free text) so the UI can render code +
counts deterministically:

```python
from typing import Literal
from pydantic import BaseModel, Field


class DatasetWarning(BaseModel):
    """Structured non-fatal data warning (confirmed + refined P2, 2026-08-06)."""

    code: Literal["rows_truncated"]
    message: str
    original_row_count: int | None = None
    loaded_row_count: int = 0


class DatasetContext(BaseModel):
    source: str
    filename: str
    row_count: int
    date_range: DateRange | None = None
    columns: list[Column] = []
    provenance: dict[str, Any] = {}
    warnings: list[DatasetWarning] = Field(default_factory=list)
```

`make_context` gains a `warnings` parameter (default `[]`) and the route passes the
adapter's warning through:

```python
# api/routes/upload.py (change)
df, warning = parse_uploaded_file(filename, content)
context = make_context(
    df, source="upload", filename=filename,
    warnings=[warning] if warning else [],
)
# context.warnings is now list[DatasetWarning]; preview/context responses serialize
# it as structured objects, and server logs record the message too (P2 refined).
```

Route changes in `api/routes/upload.py`: catch `UploadError` and raise the matching
`HTTPException` (413/415/400/422) with `detail=UploadError.detail` — the **same**
bodies the Phase 1 contract tests already assert. The 25 MB bounded-chunk read stays
in the route (outer guard); `load_file`'s 100 MB check becomes unreachable for the
browser path but stays for Drive (Phase 5).

**Acceptance:** `pytest tests/api/test_upload.py -q` green **unchanged** (the six
status-code tests 400/409/410/413/415/422 assert identical behavior through the new
adapter); `tests/test_data_loader.py` (20) green; `grep -rn parse_uploaded_file api/`
shows the single definition. **New contract test:** a >50k-row CSV upload returns a
non-413 response whose `GET /api/v1/data/context` includes a **structured
`DatasetWarning`** (code `rows_truncated`, `loaded_row_count` set) in `warnings`
(confirmed + refined P2).

### 8. Verify remaining clean modules + quality adapter

- `utils/data_context.py` — already pure; **no edits**. Confirm the 112 tests stay
  green untouched. This is the core domain object the server session will hold in
  Phase 4; do not refactor it here.
- `utils/ga4_client.py`, `utils/drive_client.py`, `utils/charts.py`, `utils/funnels.py`,
  `utils/commands.py`, `utils/sanitize.py`, `utils/report_exporter.py` — confirm zero
  streamlit imports (audit table) and leave untouched.
- `api/services/quality_service.build_quality_report` already imports
  `utils.data_loader.assess_data_quality` directly — after Task 2 that import path is
  Streamlit-free. No change needed; note in the PR.

**Acceptance:** `pytest tests/test_data_context.py tests/test_charts.py tests/test_funnels.py tests/test_commands.py tests/test_custom_metrics.py tests/test_data_quality.py -q` green (214 tests).

### 9. Test-layer actions (keep 452 green; do not port the 290)

- Re-run the **452 utils-facing tests** (test-layer-inventory §1 list) — all green.
- The **290 Streamlit-layer tests** remain green (they run against Streamlit which still
  exists) but are **not** ported in Phase 2 — retirement is a Phase 6 checklist item.
- New in this phase: `tests/test_utils_import_boundary.py` (Task 1),
  `tests/test_caching.py` (Task 3). Both are utils-facing (transfer to the API suite
  later without changes).
- Runbook (no double-run): `pytest tests -q` for full regression;
  `pytest tests/api tests/test_utils_import_boundary.py -q` for contract+boundary only.

**Acceptance:** `pytest tests -q` green (772 baseline + ~8 new boundary/caching tests);
pre-commit hooks (ruff, black, guard, detect-private-key) green on all touched files.

### 10. Exit criteria (Phase 2 gate)

- [ ] `grep -rn 'import streamlit' utils/` matches only `styles.py`, `error_boundary.py`,
      `session.py` — and all three carry `STREAMLIT-ONLY` banners.
- [ ] `grep -rn 'streamlit' api/ tests/api/` → empty.
- [ ] `tests/test_utils_import_boundary.py` green (guard runs forever, incl. CI).
- [ ] Phase 1 contract tests green against the `load_file()` adapter (Task 7) — same
      error bodies, same status codes.
- [ ] 452 utils-facing tests green; `test_data_context` (112) untouched.
- [ ] Streamlit smoke still passes (feature freeze intact; `scripts/smoke_test.sh`).
- [ ] Fingerprint memo (Task 3) covered by `tests/test_caching.py`.

## Gate table — Phase 2 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| **Phase 2 — decoupled `utils/`** | ✅ **CLOSED 2026-08-06** — commit `8c66eea` on `feat/react-fastapi-migration`. `grep -rn 'import streamlit' utils/` matches only the quarantined trio (`styles.py`, `error_boundary.py`, `session.py`) — all three carry `STREAMLIT-ONLY` banners; `grep -rn 'streamlit' api/ tests/api/` → empty; `tests/test_utils_import_boundary.py` green (incl. dynamic-import forms `importlib.import_module`/`__import__` — guard now runs forever, incl. CI); 452 utils-facing tests green (`test_data_context` 112 untouched); Phase 1 contract tests green against the `load_file()` adapter; `tests/test_caching.py` covers fingerprint memo (identity/LRU/byte-budget/reset/concurrency); Streamlit smoke passes (feature freeze intact). Evidence: **794 passed**, guard exit 0, hooks green. | Implementation agent | Recorded 2026-08-06; `specs/README.md` Phase 2 row flipped to DONE |

## Confirmed decisions (2026-08-06 product owner)

| # | Decision | Chosen | Notes |
|---|---|---|---|
| P0 | `forecast_metric` caching | **Fingerprint memo** (`utils/caching.py`) | Bounded LRU keyed on `fingerprint_frame`; **thread-safe (`RLock`)**, optional byte budget, `cache_clear()` for tests; no session-state dependency (refined) |
| P1 | Gemini usage accounting | **`usage_sink` threading + structured `UsageEvent`** | Safe operational fields only (never prompt/body content); **best-effort/logged sink failures**; Streamlit writes legacy counters, API writes a server ledger in Phase 3 (refined) |
| P2 | `load_file` truncation warning | **`DatasetContext.warnings` with structured `DatasetWarning`** | `code: "rows_truncated"` + message + loaded/original row counts; surfaced end-to-end now; new contract test required (refined) |
| Q4 | Quarantined trio (`styles`/`error_boundary`/`session`) | **Standard banner in place** | `STREAMLIT-ONLY MODULE` banner + boundary guard forbidding `api/**` and shared utils from importing the trio or streamlit (refined) |

**Authorization status (2026-08-06):** ✅ **IMPLEMENTED + CLOSED.** Owner confirmed the
four spec decisions; Tasks 1–10 were executed on `feat/react-fastapi-migration` as
commit `8c66eea` — 794 passed, guard exit 0, hooks green (see [Gate table](#gate-table--phase-2-gate)).

## Parked/absorbed content

- F3/F4 do not cover Phase 2 (F4 §6 adapter note points here) — no code to absorb.
- `session-state-inventory.md` §7 remains the state-placement checklist; Phase 2
  consumes only the `clear_data()`/`_track_usage` subsets. Remaining keys land in
  Phases 3–5 with their owning endpoints.
