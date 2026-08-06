# Phase 3 — Wire FastAPI to Real `utils/` + AI Analysis (executable spec)

> 🔵 **ACTIVE** — research gate run 2026-08-06 (Gemini production readiness, archive §3.12 prompt 3). Expansion in progress; open decisions marked ⚠️ **DECISION** await owner answers (recorded below as they land). **Do not begin implementation until the decision markers are resolved.**
>
> **Status flow:** STUB → (research gate) → ACTIVE → gate evidence recorded → DONE. Phase 1 ✅ and Phase 2 ✅ are complete; this is the next executable phase.

## Purpose

Add the analysis + AI endpoints that call the **decoupled** `utils/` services: chat/SSE (Gemini), summary, forecasting, funnels, charts, and export — using the **deterministic-context pattern** (domain code assembles contract/evidence/insight context; Gemini explains and prioritizes — it never calculates). Chat wire format is **locked-but-open** decision #1 (master-plan §13): **plain SSE** is the default.

Everything under `/api/v1`, snake_case at the boundary, `credentials: "include"`, server resolves session → dataset (no client-authoritative references). Metric-status policy enforced at the model boundary (provisional caveated, unavailable never numeric evidence). Gemini prompt allowlist per `migration/policies/data-retention-policy.md` §7–§8.

## Inputs / source documents

- master-plan §7 (Phase 3), §11-B/F, §13 (open decisions #1, #7), §14 (release gate 3 — chat reconnect)
- `utils/gemini_client.py` (Phase 2: `UsageEvent`, `usage_sink`, sync + stream generators) · `utils/prompt_templates.py` (`build_summary_prompt`, `build_chat_prompt`, `detect_chart_request`) · `utils/data_loader.py` (`get_dataset_stats`, `smart_sample`) · `utils/forecasting.py` (`forecast_metric`, `build_forecast_summary`) · `utils/funnels.py` (`build_funnel_data`) · `utils/charts.py` (`generate_chart`) · `utils/report_exporter.py` (`build_markdown_report`, `build_excel_report`, `build_pdf_report`) · `utils/commands.py` (`resolve_command`, `get_command_pills`) · `utils/sanitize.py`
- `api/` Phase 1 surface: `main.py` · `dependencies.py` (signed-cookie session, `require_dataset`) · `schemas.py` · `stores/session_store.py` (AppSession.metadata) · `stores/dataset_store.py` · `services/dataset_service.py` (`clear_dataset_state`) · `services/quality_service.py`
- `plans/ga4-measurement-contract.md` — metric-status consumption policy (validated / provisional / unavailable)
- `migration/policies/data-retention-policy.md` §7 (Gemini prompt allowlist), §8 (identifier removal/aggregation)
- archive §3.5 (SSE wire format), §3.9–3.10 (google-genai, ai@^7.0.48, streaming tests, model hygiene)
- **F3's chat content is NOT absorbed here** — F3 is the frontend store wiring; it parks in `phase-4-react-port.md`. This phase owns the backend chat/summary endpoints.

## Tracks consumed

- **A** (state/session): analysis state is server-owned; chat context resolved from the signed-cookie session.
- **B** (API/contract): `/api/v1` chat + analysis schemas; metric-status policy enforced at the model boundary.
- **C** (tests): chat/analysis contract tests; SSE test asserts partial chunks stream; usage-ledger assertions.
- **D** (security): `GEMINI_API_KEY` env handling (never committed); placeholder guard stays for secrets.
- **F** (retention/AI boundary): Gemini prompt allowlist per data-retention-policy §7; identifiers scrubbed per §8.
- **G** (research discipline): Gemini readiness gate run 2026-08-06 — results recorded below.

## Research gate — RESULTS (run 2026-08-06, archive §3.12 prompt 3)

Dispatched to the web + docs research agents. Findings below are **official-source-derived**; model lifecycle facts are re-verified at implementation time (policy: external research never overrides canonical internal contracts without a reconciliation step).

### Model landscape (August 2026)

| Model | Role | Notes |
|---|---|---|
| `gemini-3.5-flash` | **Recommended workhorse** for analytics explanation; built-in reasoning (default medium thinking) | $1.50/1M input, $9.00/1M output incl. thinking tokens; 1M-token context; batch API −50% |
| `gemini-3.1-pro-preview` / `gemini-2.5-pro` | Deep reasoning (multi-table joins, modeling) | Higher cost/latency |
| `gemini-3.5-flash-lite` / `gemini-3.1-flash-lite` | Cost-sensitive, high-throughput routine formatting | Cheapest |
| `gemini-2.5-flash` | **Current code default** — still available as of the gate | 1M context; master-plan §7 says keep as default |

**Deprecations:** Gemini 2.0 family shut down 2026-06-01 · 3.1 Flash-Lite preview shut down 2026-05-25 · 2.5 Flash Image shutdown 2026-10-02 (image variant only — the text `2.5-flash` remains). **`utils/gemini_client.py` still lists `gemini-2.0-flash` and `gemini-1.5-flash` in `AVAILABLE_MODELS` — prune (master-plan §7 model hygiene, task below).**

### Privacy — free vs paid tier (client data!)

- **Free tier (AI Studio key, no billing):** prompts/responses **are logged and may be reviewed by humans** — **NOT acceptable for client analytics data**. Do not ship the hosted beta with a free-tier key.
- **Paid tier (Cloud project + billing):** Google does **not** use prompts/responses to train or improve products; DPA applies; abuse logs retained ~55 days (configurable down to 7). Required posture for client data.

### SDK facts (`google-genai`, current)

- Package: `google-genai` (pinned `>=1.0.0`; installed 2.14.0). Legacy `google-generativeai` is NOT used.
- Async client: `client.aio.models.generate_content_stream(...)`; sync: `client.models.generate_content_stream(...)`.
- Multi-turn history: `contents=[{"role": "user"|"model", "parts": [{"text": ...}]}, ...]`.
- Usage metadata: on the **final chunk** — `usage_metadata.prompt_token_count`, `candidates_token_count`, `thoughts_token_count`, `cached_content_token_count`, `tool_use_token_count`, `total_token_count`.
- Disconnect: Starlette cancels the async generator on client disconnect → `asyncio.CancelledError`; aio client closed via `await client.aio.aclose()`.
- Env var: `GEMINI_API_KEY` (if both `GEMINI_API_KEY` and `GOOGLE_API_KEY` set, `GOOGLE_API_KEY` wins).
- Context limits: 1M-token input for 2.5-flash / 3.x flash; countTokens guard exists (`MODEL_CONTEXT_LIMITS`).

### Reconciliation note

Phase 2 kept `utils/gemini_client.py` framework-neutral with **sync** generators. Phase 3 can wrap the sync stream inside `StreamingResponse` (acceptable for local-first; blocks the event loop per chunk) **or** add an async `aio` path (production-shaped, Cloud Run-ready). ⚠️ **DECISION — see Task 5.**

## Task sequence: Preconditions + 12 implementation/acceptance tasks

### 0. Preconditions and non-goals

**Preconditions:** Phases 1 ✅ + 2 ✅ on `feat/react-fastapi-migration`; `GEMINI_API_KEY` present in the untracked local `.env` (placeholder only in `.env.example`); `require_dataset` dependency exists; guard allowlist includes the five Phase 1 names.

**Non-goals (keep out of this phase):**
- ❌ GA4 OAuth / Drive ingestion (Phase 5).
- ❌ React UI porting (Phase 4 — F3 store wiring lives there).
- ❌ Evidence connector / research panels (prototype quarantine).
- ❌ Durable usage/audit storage (deferred — local-first in-memory stores acceptable through Phase 5; §17 guardrails are hosted-beta gates).
- ❌ Chat *history persistence* — history is client-owned (F3 store); the server is stateless for chat content and resolves only session → dataset.

---

### 1. Guard allowlist + env additions

Extend `.env.example` (FastAPI section) and `scripts/check_credentials.py` **names-only** allowlist:

```dotenv
# ── FastAPI migration backend — AI (Phase 3) ─────────────────────────────
GEMINI_API_KEY=your_api_key_here          # placeholder only — real keys live in untracked .env / deployment secrets
GEMINI_MODEL=gemini-3.5-flash             # ⚠️ DECISION — see Task 4 (default model)
AI_MAX_CONTEXT_TOKENS=200000              # prompt-budget guard (see Task 3)
```

Guard rules stay: **names only, no values in committed files, placeholders permitted in `.env.example`, real secrets always fail.** No `GEMINI_*` value may be committed even as a "safe default" if it is credential-shaped.

**Acceptance:** `python3 scripts/check_credentials.py` passes; guard tests cover `GEMINI_API_KEY=your_api_key_here` (pass, placeholder) and a real-key-shaped value in a committed file (fail).

---

### 2. Settings additions (`api/config.py`)

```python
class Settings(BaseSettings):
    # ... existing Phase 1 fields ...

    gemini_api_key: str | None = None          # GEMINI_API_KEY — optional at startup (AI degrades)
    gemini_model: str = "gemini-3.5-flash"     # GEMINI_MODEL — ⚠️ DECISION default (Task 4)
    ai_max_context_tokens: int = 200_000       # AI_MAX_CONTEXT_TOKENS — prompt-budget guard (Task 3)
```

No startup validation on the key (the app must boot without AI). Add a `has_ai` property:

```python
@property
def has_ai(self) -> bool:
    return bool(self.gemini_api_key)
```

**Acceptance:** app boots with and without `GEMINI_API_KEY`; settings test asserts `has_ai` flips.

---

### 3. Server-side usage ledger

Per-session in-memory ledger (local-first; durable store + budgets are §17 hosted-beta gates). ⚠️ **DECISION — add `UsageLedger` as a field on `AppSession` (recommended) vs a separate `api/stores/usage_store.py` keyed by session id.**

Recommended shape (either home):

```python
@dataclass
class UsageLedger:
    """Per-session, server-owned Gemini usage (Phase 3). Cleared with Clear Data
    (clear_dataset_state resets it); never contains prompt content or raw rows."""

    request_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    thoughts_token_count: int = 0
    cached_token_count: int = 0
    total_token_count: int = 0
    success_count: int = 0
    error_count: int = 0
    by_request_type: dict[str, int] = field(default_factory=dict)  # "summary" | "chat" | ...
```

A `usage_sink` factory binds the Phase 2 `UsageEvent` to the ledger:

```python
def ledger_sink(ledger: UsageLedger) -> UsageSink:
    def sink(event: UsageEvent) -> None:
        ledger.request_count += 1
        ledger.input_tokens += event.input_tokens
        ledger.output_tokens += event.output_tokens
        ledger.thoughts_token_count += event.thoughts_token_count
        ledger.cached_token_count += event.cached_token_count
        ledger.total_token_count += event.total_token_count
        if event.success:
            ledger.success_count += 1
        else:
            ledger.error_count += 1
        ledger.by_request_type[event.request_type] = (
            ledger.by_request_type.get(event.request_type, 0) + 1
        )
    return sink
```

Thread-safety: `UsageLedger` mutation happens inside the request lifecycle (one request = one writer) — document the invariant; add an `RLock` only if a future phase shares the ledger across streams.

`clear_dataset_state` (Phase 1, `dataset_service.py`) must reset the ledger. **Acceptance:** contract test uploads → chat → asserts ledger counts; Clear Data resets them; no raw content ever stored.

---

### 4. ⚠️ DECISION — default Gemini model + model selector pruning

Options:

| Option | Effect |
|---|---|
| **A. Keep `gemini-2.5-flash` default** (master-plan §7 current text) | Zero behaviour change; matches existing tests + Streamlit; prune only 2.0/1.5 from `AVAILABLE_MODELS` |
| **B. Adopt `gemini-3.5-flash` default** (research-recommended workhorse) | Current-gen reasoning; update `DEFAULT_MODEL` + `AVAILABLE_MODELS` + `MODEL_CONTEXT_LIMITS`; re-run gemini unit tests with mocked responses (no live-key dependency) |
| **C. Env-configurable, 2.5-flash fallback** | `GEMINI_MODEL` env with 2.5-flash default; selector pruned to {2.5-flash, 3.5-flash, 3.5-flash-lite} |

Regardless: **prune `gemini-2.0-flash` (shut down) and `gemini-1.5-flash` (deprecated) from `AVAILABLE_MODELS` + `MODEL_CONTEXT_LIMITS`** — locked by master-plan §7 model hygiene.

**Acceptance (any option):** `AVAILABLE_MODELS` contains no shut-down model; default model constant is used by every AI route; unit tests mock `_get_client` (no live key).

---

### 5. ⚠️ DECISION — streaming implementation

| Option | Shape | Trade-off |
|---|---|---|
| **A. Wrap the Phase 2 sync generator** | `StreamingResponse(sync_gen(), media_type="text/event-stream")`; run chunk iteration via `anyio.to_thread` per chunk | Reuses tested framework-neutral `generate_response_stream`; per-chunk thread hop; fine local-first |
| **B. Add an async `aio` path** | New `generate_response_stream_async` in `utils/gemini_client.py` using `client.aio.models.generate_content_stream`; `await client.aio.aclose()` on lifespan shutdown | Cloud Run-ready; clean `CancelledError` handling; adds a second code path to a Phase-2-tested module |
| **C. Hybrid** | Keep sync utils; API route wraps with `run_in_threadpool` for the whole stream, buffering 1–2 chunks | Simpler than A per-chunk; slightly higher latency |

**Recommended: B if Cloud Run concurrency matters soon; A if Phase 3 must stay minimal.** Wire format is locked: **plain SSE** — `data: <chunk>\n\n`, `media_type="text/event-stream"`, no AI SDK data-stream framing (decision #1; matches `ai@^7.0.48` + `toTextStreamResponse()` + the captured F3 reader).

SSE event contract (⚠️ **DECISION — trailer shape**):

```text
data: {"type":"text","content":"..."}\n\n        # per chunk
data: {"type":"usage","input_tokens":N,...}\n\n  # final chunk: ledger/usage trailer (optional)
data: {"type":"done"}\n\n                        # stream end
```

or plain text chunks + a final `[DONE]` line. **Recommended: JSON envelope** (survives commas in prose; F3 reader updated in Phase 4 to parse it — record in the store-drift matrix).

**Acceptance:** SSE contract test asserts ≥2 partial chunks stream before completion; disconnect cancels the generator (test with a cancelled TestClient stream where feasible).

---

### 6. `POST /api/v1/chat` — SSE streaming endpoint

New `api/routes/chat.py`. Request carries only message/mode data (server resolves everything else):

```python
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    mode: Literal["chat", "summary"] = "chat"

class ChatError(BaseModel):
    detail: str
```

Route (option A sketch — adjust per Task 5 decision):

```python
router = APIRouter(prefix="/api/v1", tags=["ai"])

@router.post("/chat")
async def chat(
    payload: ChatRequest,
    session: AppSession = Depends(require_dataset),
) -> StreamingResponse:
    dataset = datasets.get(session.dataset_id)
    df = dataset.dataframe                      # server-owned, read-only by convention
    ctx = dataset.context
    # Deterministic context assembly (Task 7) — never raw rows/identifiers.
    context = build_deterministic_context(df, ctx, session)
    prompt = build_chat_prompt(
        user_question=payload.messages[-1].content,
        df=context.prompt_df,                   # identifier-scrubbed sample only
        stats=context.stats,
        conversation_history=[
            {"role": m.role, "content": m.content} for m in payload.messages[:-1]
        ],
    )
    ledger = session.usage  # or usage_store.get(session.id) per Task 3 decision
    sink = ledger_sink(ledger)

    def event_stream():
        try:
            for chunk in generate_response_stream(
                prompt,
                model=settings.gemini_model,
                request_type=payload.mode,
                usage_sink=sink,
            ):
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
        except RuntimeError as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Reconnect safety (release gate 3):** server is stateless per request — a reconnect re-sends the same `messages` payload minus the partial assistant turn; no duplicate assistant messages are appended server-side (client owns history). Partial output is safe to discard.

**Errors:** no dataset → 409 (from `require_dataset`) · no API key → 503 with `{"detail": "AI features unavailable — configure GEMINI_API_KEY"}` (reuse `settings.has_ai`) · provider errors streamed as `type: error` events, never as raw exception text.

**Acceptance:** contract tests: 409 without dataset · 503 without key · streamed chunks with mocked `_get_client` · usage trailer reflects the final chunk's `usage_metadata`.

---

### 7. Deterministic-context assembly + prompt allowlist

New `api/services/ai_service.py` (or extend `dataset_service` — ⚠️ **DECISION on home; recommended: separate `ai_service.py` to keep upload concerns separate**):

```python
@dataclass(frozen=True)
class DeterministicContext:
    prompt_df: pd.DataFrame   # identifier-scrubbed sample — NEVER the full raw frame
    stats: dict[str, Any]     # from get_dataset_stats()
    quality: QualityReport | None
    metric_caveats: list[str]  # provisional/unavailable caveats from the measurement contract

def build_deterministic_context(
    df: pd.DataFrame,
    ctx: DatasetContext,
    session: AppSession,
) -> DeterministicContext:
    stats = get_dataset_stats(df)
    quality = build_quality_report(df)              # reuse Phase 1 service
    prompt_df = scrub_identifiers(smart_sample(df, max_rows=5))  # §8: identifiers removed
    caveats = metric_status_caveats(ctx)            # provisional caveated; unavailable never numeric
    return DeterministicContext(prompt_df, stats, quality, caveats)
```

**Identifier scrub (`utils/sanitize.py` extension or `ai_service` helper — ⚠️ DECISION):**

```python
IDENTIFIER_PATTERNS = (
    "email", "user", "user_id", "uid", "client_id", "device_id",
    "phone", "name", "customer", "member", "account",
)

def scrub_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Drop identifier-like columns from prompt-bound samples (retention §8).
    Best-effort: documented patterns only; never silently keeps PII."""
    drop = [c for c in df.columns if any(p in str(c).lower() for p in IDENTIFIER_PATTERNS)]
    return df.drop(columns=drop) if drop else df
```

⚠️ **DECISION — severity:** (a) **hard drop** (recommended — §8 says "removed or aggregated before any AI call") vs (b) drop + record a `DatasetWarning` vs (c) stats-only prompts with no raw sample rows at all (most conservative; `build_summary_prompt` would need a stats-only variant).

**Metric-status caveats** — enforce the canonical policy at the boundary:

```python
def metric_status_caveats(ctx: DatasetContext) -> list[str]:
    caveats = []
    for m in ctx.metrics:                       # metrics are server-owned (empty until Phase 4 sync)
        status = m.get("status", "validated")
        if status == "provisional":
            caveats.append(f"{m.get('id', m.get('name', '?'))} is provisional — directional only")
        elif status == "unavailable":
            caveats.append(f"{m.get('id', m.get('name', '?'))} is unavailable — blocked capability only")
    return caveats
```

Caveats are appended to the prompt (provisional → directional label; unavailable → never numeric evidence). `ctx.metrics` is empty in Phase 3 (no mutation endpoints yet) — the hook is in place for Phase 4/5.

**Acceptance:** unit tests assert identifier columns never appear in `prompt_df`; caveat builder covers provisional + unavailable; `build_summary_prompt` gets the scrubbed sample.

---

### 8. `POST /api/v1/analysis/summary`

Same deterministic-context flow, non-streaming:

```python
class SummaryRequest(BaseModel):
    mode: Literal["summary"] = "summary"

class SummaryResponse(BaseModel):
    summary: str
    model: str
    usage: UsageSummary

class UsageSummary(BaseModel):
    input_tokens: int
    output_tokens: int
    thoughts_token_count: int
    total_token_count: int
```

Route: `generate_response(build_summary_prompt(context.prompt_df, context.stats, quality_report=context.quality), model=..., request_type="summary", usage_sink=sink)`; 503 without key; 409 without dataset; `RuntimeError`/`ValueError` → typed 5xx with generic detail.

**Acceptance:** contract test with mocked `_get_client` returns summary + usage; 409/503 paths tested.

---

### 9. `POST /api/v1/analysis/forecast` + `POST /api/v1/analysis/funnel` (deterministic — no Gemini)

```python
class ForecastRequest(BaseModel):
    date_col: str | None = None    # auto-detect via find_date_column when omitted
    metric_col: str                # e.g. "sessions"
    periods: int = Field(default=30, ge=1, le=365)

class ForecastResponse(BaseModel):
    metric_col: str
    periods: int
    summary: str                   # build_forecast_summary(result)
    forecast_points: list[dict]    # [{date, value, lower, upper}]
    insufficient_data: bool = False

class FunnelRequest(BaseModel):
    page_col: str | None = None    # auto-detect via find_column(candidates) when omitted
    metric_col: str
    steps: list[str] = Field(min_length=2)

class FunnelResponse(BaseModel):
    steps: list[str]
    values: list[float]
```

Both are **server-side deterministic** calls (`forecast_metric`, `build_funnel_data`) on the stored frame — Gemini is never asked to calculate. Funnel scope: **page-pattern aggregation only** (`build_funnel_data`) — GA4 `runFunnelReport` template funnels are Phase 5 (re-verify the ROADMAP funnel rows at implementation, master-plan §7 + archive §3.4).

**Acceptance:** contract tests with a small fixture CSV: forecast returns `insufficient_data=true` for <3 points and a valid forecast otherwise; funnel aggregates per step; auto-detect column resolution tested.

---

### 10. `POST /api/v1/export` (markdown/excel/pdf)

```python
class ExportRequest(BaseModel):
    format: Literal["markdown", "excel", "pdf"] = "markdown"

class ExportResponse(BaseModel):
    format: str
    filename: str
    size_bytes: int
    download_url: str   # Phase 6 serves static; Phase 3 returns the artifact inline (see below)
```

Phase 3 behavior: build via `report_exporter` (`build_markdown_report` / `build_excel_report` / `build_pdf_report`) and return `Response(content=..., media_type=...)` with `Content-Disposition: attachment`. **Retention §metadata:** log `{format, timestamp, row_count, opaque request/session id}` only — never contents (30-day metadata rule; no logging table needed yet — in-memory last-export record on the session, cleared by Clear Data).

⚠️ **DECISION — export in Phase 3 vs Phase 4:** master-plan §7 lists export in the wire-real-utils task, but the Phase 1 boundary kept exports out. Options: (a) include now (parity with Streamlit) or (b) defer to Phase 4 with the React download flow. **Recommended: include** — `report_exporter` is already decoupled and deterministic; the frontend wiring is what belongs to Phase 4.

**Acceptance:** export contract test returns a non-empty artifact per format with correct media type; metadata record contains no content.

---

### 11. `GET /api/v1/ai/usage` (per-session ledger view)

```python
class UsageResponse(BaseModel):
    request_count: int
    input_tokens: int
    output_tokens: int
    thoughts_token_count: int
    total_token_count: int
    success_count: int
    error_count: int
    by_request_type: dict[str, int]
```

Reads the per-session ledger (Task 3). Feeds the §17 AI cost guardrails later; also lets the React shell render usage stats without touching Streamlit session state. **Acceptance:** contract test asserts counts grow across requests and reset on Clear Data.

---

### 12. Tests, model hygiene, PR acceptance gate

**Model hygiene (locked):** prune `gemini-2.0-flash` + `gemini-1.5-flash` from `utils/gemini_client.py` `AVAILABLE_MODELS` + `MODEL_CONTEXT_LIMITS`; keep `validate_api_key`, `_classify_api_error`, sync/stream generators intact. Update `tests/test_gemini_client.py` expectations if they reference pruned models.

**Test matrix (new files under `tests/api/`):**

| Test | Asserts |
|---|---|
| `test_chat.py` | 409 no dataset · 503 no key · mocked stream yields ≥2 partial chunks · usage trailer · error event shape |
| `test_analysis_summary.py` | summary + usage returned · 409/503 · mocked `_get_client` |
| `test_analysis_forecast.py` | insufficient-data vs valid forecast · auto-detect date col |
| `test_analysis_funnel.py` | per-step aggregation · min_length=2 validation |
| `test_export.py` | markdown/excel/pdf artifacts + media types · metadata contains no content |
| `test_usage.py` | ledger counts grow · Clear Data resets · by_request_type |
| `test_ai_context.py` | identifier scrub drops PII columns · metric caveats for provisional/unavailable |
| `test_settings_ai.py` | boots with/without key · `has_ai` · `GEMINI_MODEL` default |

All Gemini routes mock `utils.gemini_client._get_client` — no live key in CI.

**PR boundary (single PR):** `api/config.py` · `.env.example` guard additions · `utils/gemini_client.py` model hygiene · `api/services/ai_service.py` · `api/routes/chat.py` + `analysis.py` + `export.py` + `usage.py` · `api/schemas.py` additions · `api/stores/session_store.py` (or `usage_store.py`) · `tests/api/*` · `tests/test_gemini_client.py` updates. **No GA4, Drive, React, evidence.**

**Validation:** `pytest tests -q` (full regression, expect ~794 + new) · `pytest tests/api -q` · `git ls-files -z | xargs -0 python3 scripts/check_credentials.py` (exit 0) · `pre-commit run --all-files` · manual smoke: upload fixture → chat SSE curl with live key (local `.env` only).

## Exit criteria (DoD)

- [ ] Chat + analysis + export + usage endpoints live under `/api/v1`; all contract-tested.
- [ ] SSE contract test asserts partial chunks stream (release gate 3 reconnect shape documented).
- [ ] Prompt allowlist + identifier scrub enforced per data-retention-policy §7–§8 (no raw rows, no identifiers, no tokens in prompts or usage events).
- [ ] Metric-status policy enforced at the boundary (provisional caveated; unavailable never numeric evidence).
- [ ] Usage ledger per session, reset by Clear Data, no content stored.
- [ ] `AVAILABLE_MODELS` pruned of shut-down models; default model decision recorded.
- [ ] Full regression + guard + hooks green; live smoke with a real local key.

## Gate table — Phase 3 gate

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| No regression | Existing Streamlit + Phase 1/2 Python behavior still works | Implementation agent | `pytest tests -q` baseline green |
| Contract | Chat/analysis/export/usage endpoints match schemas + error taxonomy | Implementation agent | `pytest tests/api -q` (httpx contract tests) |
| AI behaviour | Gemini calls use the decided model + fallback; streaming + disconnect + usage verified | Implementation agent | mocked-unit + live-key smoke (local `.env`), usage ledger asserted |
| Retention boundary | Prompt allowlist + identifier scrub + metric-status caveats enforced | Implementation agent | `test_ai_context.py` + policy cross-check |
| Phase 3 gate | All exit criteria met | Implementation agent | Record evidence; flip `specs/README.md`; open Phase 4 after the React 19 verification gate |

## ⚠️ DECISION register (asked to owner 2026-08-06)

| # | Decision | Options | Status |
|---|---|---|---|
| 1 | Default Gemini model | A: keep 2.5-flash · B: adopt 3.5-flash · C: env-config, 2.5 fallback | ⏳ pending |
| 2 | Streaming implementation | A: wrap sync gen · B: async aio path · C: hybrid | ⏳ pending |
| 3 | SSE trailer shape | JSON envelope vs plain chunks + [DONE] | ⏳ pending |
| 4 | Identifier severity | a: hard drop · b: drop + warning · c: stats-only prompts | ⏳ pending |
| 5 | Usage ledger home | AppSession field vs separate usage_store | ⏳ pending |
| 6 | ai_service home | separate `api/services/ai_service.py` vs extend dataset_service | ⏳ pending |
| 7 | Export in Phase 3 | include now (recommended) vs defer to Phase 4 | ⏳ pending |
| 8 | Free vs paid tier enforcement | document-only vs startup warning vs hard block | ⏳ pending |
