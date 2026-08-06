# Phase 3 — Wire FastAPI to Real `utils/` + AI Analysis (executable spec)

> ✅ **DONE** (2026-08-06) — Gate closed. Implemented on branch **`feat/react-fastapi-migration`** (commits `bb6f564` + review-fix round `bcf4866`). Full regression **859 passed** (incl. **73 `tests/api` contract tests**), guard exit 0, hooks green. See [Gate table](#gate-table--phase-3-gate) for closure evidence.
> **Shipped:** `POST /api/v1/chat` (named-SSE events `text/usage/done/error` + optional `warning`; terminal sequences per C5; per-session `ai_lock` with bounded 30 s queue-wait → typed retryable `ai_busy`; failure `UsageEvent(success=False)` before typed error) · `POST /api/v1/analysis/summary` (Gemini, non-streaming, output capped at the reserved allowance) · `POST /api/v1/analysis/forecast` + `/analysis/funnel` (deterministic — no Gemini) · `GET /api/v1/ai/usage` (per-session ledger, counts only, reset by Clear Data). `api/services/ai_service.py`: deterministic-context assembly, identifier scrub (`identifiers_removed_for_ai` warning), metric-status caveats, two-stage token guard (chars÷4 → `countTokens` near-limit preflight → deterministic trim → typed `context_too_large`), `validate_chat_messages` (D12), `classify_provider_error` (typed codes, never raw exception text). `utils/gemini_client.py`: model hygiene (2.0/1.5 pruned; 3.5-flash/lite added), `generate_response_stream_async` (aio path, first-token + stream deadlines), `count_tokens`, `emit_usage_failure`. Settings: `GEMINI_DATA_POLICY` Literal-validated, `AI_MAX_CONTEXT_TOKENS`/`AI_RESERVED_OUTPUT_TOKENS`, timeouts + `AI_QUEUE_WAIT_SECONDS`, `has_ai`. **Task 0 probe recorded:** `google-genai` 2.14.0 — `client.models.count_tokens(*, model, contents, config) -> CountTokensResponse` (field `total_tokens`); near-limit preflight only (D11).
> **Status flow:** STUB → (research gate) → ACTIVE → gate evidence recorded → DONE. Phase 1 ✅ (`eaa6ac5`+`66c0f1d`), Phase 2 ✅ (`8c66eea`), Phase 3 ✅ (`bb6f564`+`bcf4866`) are complete on `feat/react-fastapi-migration`; Phase 4 (React port) is also DONE (`075dfa4`+`ed94679`) — next executable spec: Phase 5 (GA4/Drive), pending its Task 0 research gates.

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

Phase 2 kept `utils/gemini_client.py` framework-neutral with **sync** generators. Phase 3 adds an **async `aio` path** for FastAPI SSE (confirmed D2 — `generate_response_stream_async` via `client.aio.models.generate_content_stream`, additive to the sync generator; see Task 5).

### Verification notes (added 2026-08-06 — after owner-provided refinement review)

These are **implementation-time checks**, not blocking research gaps. The Phase 3 refinements (token guard, sliding-window history, latency observability) stayed on the internal-decision side; only the following carry unverified or secondary-evidence claims:

1. **`countTokens` exact SDK shape (verify at Task 7):** the ≥80% preflight path depends on `client.models.count_tokens(...).total_tokens`. The research gate verified `generate_content_stream` + `usage_metadata` in detail but did **not** confirm the exact `countTokens` method name/return shape in the installed `google-genai` 2.14.0. Verify locally at implementation time before wiring the near-limit preflight.
2. **`countTokens` cost semantics (corrected wording):** `countTokens` is **free but separately rate-limited**, and adds a round-trip latency + its own failure mode — it does **not** consume generation quota. Task 7 wording reflects this ("extra latency + quota use" is inaccurate and is not used).
3. **Owner-provided heuristics are design choices, not researched constraints:** the **≥80% threshold** and the **token-budgeted sliding-window algorithm** came from owner reference material (secondary, with devblogs/RAG citations) — adopted as internal design decisions, not verified external facts. Do not re-derive them from research; treat them as confirmed product decisions. The parked evidence-connector RAG reference (`plans/🔵 evidence-connector-design.md` "Deferred — Technical-Docs RAG Reference, Parts 1–2") carries owner/secondary citations (RAGAS, HNSW, milvus, etc.) and must receive **fresh research when that workstream opens** per the research-gating discipline — it is reference, not verified authority.

## Task sequence: Preconditions + 12 implementation/acceptance tasks

### 0. Preconditions and non-goals

**Preconditions:** Phases 1 ✅ + 2 ✅ on `feat/react-fastapi-migration` — **Phase 2 implementation is commit `8c66eea`** (`utils/caching.py` + `memoize_fingerprint` · `tests/test_caching.py` · `tests/test_utils_import_boundary.py` · `UsageEvent`/`usage_sink` wired into chat/summary/forecast call sites; 794 tests, guard exit 0); `GEMINI_API_KEY` present in the untracked local `.env` (placeholder only in `.env.example`); `require_dataset` dependency exists; guard allowlist includes the five Phase 1 names + the AI names below (Task 1).

**Non-goals (keep out of this phase):**
- ❌ GA4 OAuth / Drive ingestion (Phase 5).
- ❌ React UI porting (Phase 4 — F3 store wiring lives there).
- ❌ Evidence connector / research panels (prototype quarantine).
- ❌ Durable usage/audit storage (deferred — local-first in-memory stores acceptable through Phase 5; §17 guardrails are hosted-beta gates).
- ❌ Chat *history persistence* — history is client-owned (F3 store); the server is stateless for chat content and resolves only session → dataset.
- ❌ **RAG / retrieval-augmented generation and automatic conversation-summarization chains.** Phase 3 context = deterministic dataset context + structured quality/provenance/caveat rules + bounded sliding chat history + latest user question. RAG over approved aggregate evidence artifacts is a **future evidence-connector workstream**, never Phase 3 (and never retrieves person-level rows).
- ❌ **Shipping a tokenizer to the browser.** Token accounting is server-side only (`ai_service` + provider `countTokens`); the React shell never validates history tokens locally (Phase 4 note).
- ❌ **Logging prompt text / sample rows / user messages / model output** merely to debug token counts — estimates are tuned from the ledger's safe diagnostic dimensions only (Task 3).

**Task 0 — SDK `countTokens` acceptance probe (promoted from verification note 1 — run before Task 7 wires the preflight):**

1. Install the pinned `google-genai` from `requirements/base.txt` (currently 2.14.0).
2. Run a minimal `count_tokens` call with a synthetic prompt — a real call requires a valid key, so use the **local `.env` key** or a **mocked/synthetic client** in test mode (a fake key will not reach the real API).
3. Record: the **actual method name + request shape** (`client.models.count_tokens(...)` vs an alternative), the **result field** (expected `.total_tokens`), and the **failure class** when unavailable.
4. If unavailable/failing: **standard requests still work** via deterministic local trim (chars÷4); **near-limit requests fail safely** with `context_too_large` (typed, non-retryable) or a typed retryable provider error — never an untyped crash.

---

### 1. Guard allowlist + env additions

Extend `.env.example` (FastAPI section) and `scripts/check_credentials.py` **names-only** allowlist:

```dotenv
# ── FastAPI migration backend — AI (Phase 3) ─────────────────────────────
GEMINI_API_KEY=your_api_key_here          # placeholder only — real keys live in untracked .env / deployment secrets
GEMINI_MODEL=gemini-2.5-flash             # confirmed D1: env-configurable, 2.5-flash fallback; allowlist {2.5-flash, 3.5-flash, 3.5-flash-lite}
GEMINI_DATA_POLICY=local_free             # confirmed D7: local_free | client_paid | disabled — NEVER inferred from key format
AI_MAX_CONTEXT_TOKENS=24000               # corrected C4: total context budget = input allowance + reserved output (24k); effective input allowance = 24k − 4,096
AI_RESERVED_OUTPUT_TOKENS=4096            # corrected C4: reserved output; provider max_output_tokens is set to this value
AI_MAX_CONTEXT_CHARS=96000                # confirmed D11: deterministic-trim ceiling (≈ chars/4 = 24k tokens)
AI_FIRST_TOKEN_TIMEOUT_SECONDS=30         # confirmed D10: first-token deadline
AI_GENERATE_TIMEOUT_SECONDS=60            # confirmed D10: non-streaming per-request timeout
AI_STREAM_TIMEOUT_SECONDS=120             # confirmed D10: whole-stream deadline
AI_QUEUE_WAIT_SECONDS=30                  # settled C6: bounded ai_lock queue-wait ceiling (Option A)
```

Guard rules stay: **names only, no values in committed files, placeholders permitted in `.env.example`, real secrets always fail.** No `GEMINI_*` value may be committed even as a "safe default" if it is credential-shaped.

**Acceptance:** `python3 scripts/check_credentials.py` passes; guard tests cover `GEMINI_API_KEY=your_api_key_here` (pass, placeholder) and a real-key-shaped value in a committed file (fail).

---

### 2. Settings additions (`api/config.py`)

```python
class Settings(BaseSettings):
    # corrected C3: `from typing import Literal` — an invalid GEMINI_DATA_POLICY
    # value is a Pydantic validation error at startup, never silent fall-through.
    # ... existing Phase 1 fields ...

    gemini_api_key: str | None = None          # GEMINI_API_KEY — optional at startup (AI degrades)
    gemini_model: str = "gemini-2.5-flash"     # GEMINI_MODEL — confirmed D1: env-configurable, 2.5 fallback
    gemini_data_policy: Literal["local_free", "client_paid", "disabled"] = "local_free"  # GEMINI_DATA_POLICY — corrected C3: Literal-validated at startup
    ai_max_context_tokens: int = 24_000        # AI_MAX_CONTEXT_TOKENS — corrected C4: total context budget (input allowance + reserved output)
    ai_reserved_output_tokens: int = 4_096     # AI_RESERVED_OUTPUT_TOKENS — reserved output; provider max_output_tokens set to this value (C4)
    ai_max_context_chars: int = 96_000         # AI_MAX_CONTEXT_CHARS — deterministic-trim ceiling (D11)
    ai_first_token_timeout_seconds: int = 30   # AI_FIRST_TOKEN_TIMEOUT_SECONDS (D10)
    ai_generate_timeout_seconds: int = 60      # AI_GENERATE_TIMEOUT_SECONDS (D10)
    ai_stream_timeout_seconds: int = 120       # AI_STREAM_TIMEOUT_SECONDS (D10)
    ai_queue_wait_seconds: int = 30            # AI_QUEUE_WAIT_SECONDS — bounded ai_lock queue-wait ceiling (C6, settled 2026-08-06)
```

No startup validation on the key (the app must boot without AI). Add a `has_ai` property:

```python
@property
def has_ai(self) -> bool:
    return bool(self.gemini_api_key)
```

**`GEMINI_DATA_POLICY` behavior (confirmed D7 — explicit runtime policy, never inferred from the key):**

| Mode | Allowed | Behavior |
|---|---|---|
| `local_free` | Local dev + synthetic/public/personally-controlled test data only | Startup/log warning: free-tier prompts may be logged/reviewed by humans — never use client analytics data |
| `client_paid` | Hosted beta + real client analytics | Requires documented billing/project verification + paid-tier/privacy review before deployment |
| `disabled` | Nothing | AI endpoints return a clear feature-disabled response (`503` `{"detail": "AI features are disabled."}`) |

**Acceptance:** app boots with and without `GEMINI_API_KEY`; settings test asserts `has_ai` flips; each `gemini_data_policy` mode produces its documented behavior; **an invalid `GEMINI_DATA_POLICY` value fails at startup** (Pydantic validation — corrected C3); a `local_free` startup warning is logged (or, per D7 refinement, surfaced in the UI during coexistence).

---

### 3. Server-side usage ledger

Per-session in-memory ledger (local-first; durable store + budgets are §17 hosted-beta gates). **Confirmed D5: `UsageLedger` is a field on `AppSession`** — `clear_dataset_state` resets it. **Confirmed D13: Phase 3 records counts only — no per-session cap enforced (budgets stay a §17 hosted-beta gate).** Optionally log a **non-blocking warning** at a very high local threshold (e.g. 1M total tokens) — never a user-facing cap.

Shape (refined D5 — richer fields + **safe diagnostic dimensions**):

```python
@dataclass
class UsageLedger:
    """Per-session, server-owned Gemini usage (Phase 3). Cleared with Clear Data
    (clear_dataset_state resets it); never contains prompt content or raw rows."""

    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    thought_tokens: int = 0
    cached_tokens: int = 0
    tool_tokens: int = 0
    # Safe diagnostics — set by ai_service, never derived from prompt text:
    estimated_prompt_tokens: int = 0      # chars÷4 estimate before trimming
    context_trimmed: int = 0              # count of requests where trimming dropped content
    identifiers_removed: int = 0          # count of requests where scrub_identifiers dropped columns
    # Latency observability (safe — timestamps only, no content; refined 2026-08-06):
    request_started_at: datetime | None = None       # request entry
    provider_first_token_at: datetime | None = None  # first streamed chunk received
    provider_completed_at: datetime | None = None    # final chunk / response done
    by_request_type: dict[str, int] = field(default_factory=dict)  # "summary" | "chat" | ...
    by_model: dict[str, int] = field(default_factory=dict)         # per-model request counts
```

These dimensions answer the useful diagnostic questions **without logging sensitive content**: which feature uses the most tokens · are prompts frequently trimmed · which model is expensive · is free-tier quota causing failures · are retries increasing cost · does a prompt-template change increase token use.

**Latency observability (refined 2026-08-06):** from the three timestamps compute `TTFT = provider_first_token_at − request_started_at` and `TTLT = provider_completed_at − request_started_at` — observability only, letting you distinguish slow provider response vs oversized deterministic context vs expensive exact-token preflight vs long model output. **Never log prompt text, sample rows, user messages, or model output to debug token counts.**

A `usage_sink` factory binds the Phase 2 `UsageEvent` to the ledger:

```python
def ledger_sink(ledger: UsageLedger) -> UsageSink:
    def sink(event: UsageEvent) -> None:
        ledger.request_count += 1
        ledger.input_tokens += event.input_tokens
        ledger.output_tokens += event.output_tokens
        ledger.thought_tokens += event.thoughts_token_count
        ledger.cached_tokens += event.cached_token_count
        ledger.tool_tokens += event.tool_use_token_count
        ledger.total_tokens += event.total_token_count
        if event.success:
            ledger.success_count += 1
        else:
            ledger.failure_count += 1
        ledger.by_request_type[event.request_type] = (
            ledger.by_request_type.get(event.request_type, 0) + 1
        )
        ledger.by_model[event.model] = ledger.by_model.get(event.model, 0) + 1
    return sink
```

The three safe diagnostic dimensions (`estimated_prompt_tokens`, `context_trimmed`, `identifiers_removed`) are **not** provider-reported — `ai_service` records them at prompt-assembly time (before/after trimming, and whether the identifier scrub dropped columns).

**Concurrency (corrected C6 — one in-flight AI request per session):** a single
"one request = one writer" lifecycle does NOT protect two browser tabs or a
double-clicked request from mutating the same `AppSession.usage_ledger`
concurrently. Every AI route acquires a per-session lock —
`AppSession.ai_lock: asyncio.Lock = field(default_factory=asyncio.Lock)` — before
streaming and releases it in `finally`. This **serializes** AI requests per
session: a second concurrent request queues behind the first, and ledger
mutation is single-writer (deterministic counts, no lost updates). Contract
test: two concurrent chat requests against one session produce deterministic
ledger totals (C6).

**Queue-wait policy (settled 2026-08-06 — Option A, bounded queue):**
- A second AI request **queues** behind the in-flight stream while the client stays connected.
- **Cancellation while waiting releases cleanly** (`asyncio.CancelledError`) — no ledger mutation, no partial stream.
- The queue wait is **bounded by `AI_QUEUE_WAIT_SECONDS` (default 30)**; on expiry the queued request returns a typed `retryable: true` `ai_busy` SSE error — never an unbounded wait.
- Option B (immediate `429 ai_busy` + UI disabling duplicate Send/Generate controls) remains the documented alternative if a busy policy is preferred later.
- Contract test: a second request while a mocked stream is in flight either proceeds after the stream completes or times out with `ai_busy` past the ceiling; cancelling a queued request leaves the ledger untouched.

**Failure accounting (settled 2026-08-06):** the async AI path must emit a
`UsageEvent(success=False)` through the sink **before** streaming the typed
`error` SSE event — emitting usage only on successful calls leaves
`failure_count` meaningless. All `classify_provider_error` outcomes and the
typed `timeout` / `context_too_large` / `feature_disabled` errors count as
failures.

`clear_dataset_state` (Phase 1, `dataset_service.py`) must reset the ledger. **Acceptance:** contract test uploads → chat → asserts ledger counts; Clear Data resets them; no raw content ever stored.

---

### 4. Default Gemini model + model selector pruning — **confirmed D1: env-configurable, 2.5-flash fallback**

- `GEMINI_MODEL` env var (default `gemini-2.5-flash`) drives every AI route via `settings.gemini_model`.
- Selector pruned to **{`gemini-2.5-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`}**.
- **Prune `gemini-2.0-flash` (shut down 2026-06-01) and `gemini-1.5-flash` (deprecated) from `AVAILABLE_MODELS` + `MODEL_CONTEXT_LIMITS`** — locked by master-plan §7 model hygiene.

**Acceptance:** `AVAILABLE_MODELS` contains no shut-down model; `settings.gemini_model` default is `gemini-2.5-flash` and is overridable via env; every AI route reads the model from settings; unit tests mock `_get_client` (no live key).

---

### 5. Streaming implementation — **confirmed D2: async `aio` path; D3: JSON envelope**

- Add `generate_response_stream_async` to `utils/gemini_client.py` using `client.aio.models.generate_content_stream`, honoring `settings.gemini_stream_timeout_seconds`; close the aio client via a FastAPI lifespan (`await client.aio.aclose()`).
- Keep the Phase 2 sync `generate_response_stream` intact for Streamlit — the async path is additive.
- Wire format is locked: **plain SSE** — `media_type="text/event-stream"`, no AI SDK data-stream framing (decision #1; matches `ai@^7.0.48` + `toTextStreamResponse()`).

SSE event contract (**refined D3 — named SSE events with JSON payloads; no raw text + `[DONE]` protocol**):

```text
event: text
data: {"type":"text","content":"Partial answer"}

event: usage
data: {"type":"usage","input_tokens":123,"output_tokens":456,"thoughts_token_count":0,"total_token_count":579}

event: done
data: {"type":"done"}

event: error
data: {"type":"error","code":"rate_limited","retryable":true,"retry_after_seconds":3,"message":"AI capacity is temporarily limited. Try again shortly."}
```

**Typed error codes (refined D9):** `rate_limited` (retryable, may carry `retry_after_seconds`) · `quota_exhausted` (NOT retryable — known daily/spend/free-tier exhaustion; message may point to a paid deployment) · `provider_unavailable` · `timeout` (first-token/generate/stream deadlines, D10) · `context_too_large` (D11 guard, NOT retryable) · `feature_disabled` (D7 `disabled` policy). Error payloads never include raw exception text, prompt content, raw rows, or provider keys.

Phase 4 updates the F3 reader to parse the named SSE events + JSON payloads — record this in the store-drift matrix.

**Acceptance:** SSE contract test asserts ≥2 partial chunks stream before completion; disconnect cancels the async generator (`asyncio.CancelledError` propagates; Starlette handles it); usage trailer reflects the final chunk's `usage_metadata`.

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

**Refined D9 — one conditional retry, only before first streamed text:** retry at most once, only for a provider-signaled **transient/retryable** failure (`Retry-After` header, `RetryInfo`, temporary 429/500/503). Honor the provider-suggested delay when present; otherwise use a **jittered 2–5 s** backoff. **Never** retry known daily/spend/quota-exhausted failures (`quota_exhausted`), and **never** retry after any text has already streamed — emit the typed `rate_limited` error event and let the user retry manually (an automatic mid-stream retry could duplicate partial assistant text in the transcript).

Route sketch (async path):

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
    ledger = session.usage_ledger        # confirmed D5: field on AppSession
    sink = ledger_sink(ledger)

    async def event_stream():
        try:
            async for chunk in generate_response_stream_async(
                prompt,
                model=settings.gemini_model,
                request_type=payload.mode,
                usage_sink=sink,
                first_token_timeout=settings.ai_first_token_timeout_seconds,
                stream_timeout=settings.ai_stream_timeout_seconds,
            ):
                yield "event: text\n"
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        except (ValueError, RuntimeError) as exc:
            # corrected C2: classify_provider_error / TypedAiError live in
            # api/services/ai_service.py (Task 7) — NEVER raw exception text in SSE.
            err = classify_provider_error(exc)      # -> TypedAiError(code, message, retryable, ...)
            yield "event: error\n"
            yield f"data: {json.dumps(err.public_payload())}\n\n"
        finally:
            # `done` closes the transport; `error` is terminal for assistant content.
            yield "event: done\n"
            yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Terminal SSE behavior (corrected C5 — unambiguous sequences):**

```text
Successful stream:    text* → optional usage → done
Failed pre-text:      error → done
Failed after text:    text+ → error → done
Client rule: `error` is terminal for assistant content — the frontend must NOT
             append or auto-retry after an `error` event; `done` closes the transport.
```

The server emits `done` in `finally` so the transport always closes exactly once
(after either a successful stream or an error). Frontend tests (Phase 4) must
assert no assistant retry/duplicate append after `error`.

**Refined D12 — bounded chat history (two layers) with a token-budgeted sliding window:**

1. **Request validation (422):** max **20 messages** per request · max **4,000 chars** per message · max **24,000 total message chars** · roles `user`/`assistant` only · non-empty content. Reject malformed/excessive payloads with a typed `422` `{"detail": "Chat history exceeds the 20-message or 24,000-character request limit."}`. A fixed count alone can still overflow when one message contains a large pasted dataset — hence layer 2.
2. **Prompt budget (`ai_service` — token-budgeted sliding window):** even valid history is trimmed to fit `AI_MAX_CONTEXT_TOKENS − AI_RESERVED_OUTPUT_TOKENS` (the effective input allowance).

**Preserve order** (highest → lowest priority, never silently dropped):
1. System/safety instructions.
2. Metric-status policy + identifier-removal notice + provenance/caveat rules.
3. Deterministic dataset context (aggregates, quality warnings, active filters, selected metrics).
4. **Latest user message (always).**
5. Recent prior user messages (newest → oldest).
6. Recent assistant messages.
7. Optional explicit conversation summary — **only if added deliberately later** (never auto-generated in Phase 3).

**Trim order** (only after the above preserve set is fixed):
1. Remove raw/sample rows.
2. Reduce the data-sample count.
3. Drop oldest **assistant** messages.
4. Drop oldest **user** messages.
5. (Future) replace old history with a short deterministic summary — not in Phase 3.
6. **Reject with typed `context_too_large` if the minimum compliant context still exceeds the budget** — never silently discard provenance.

Sketch (in `ai_service.py`):

```python
def build_chat_context(
    *, system_messages: list[Message], deterministic_context: str,
    history: list[Message], latest_user_message: Message,
    max_input_tokens: int, reserve_output_tokens: int,
) -> list[Message]:
    budget = max_input_tokens - reserve_output_tokens
    fixed = [*system_messages, Message(role="system", content=deterministic_context), latest_user_message]
    selected = list(fixed)
    remaining = budget - estimate_tokens(selected)   # chars ÷ 4
    for message in reversed(history):                # newest → oldest until budget is reached
        cost = estimate_tokens([message])
        if cost > remaining:
            continue
        selected.insert(len(system_messages) + 1, message)
        remaining -= cost
    return selected
```

**Important implementation choices:** enforce request validation (422) separately from prompt trimming (typed `context_too_large`); never drop the newest user message; never trim provenance/identifier warnings/unavailable+provisional metric rules; **do not auto-summarize history in Phase 3** (extra request, cost, failure mode, and privacy surface); if summaries are added later, store only a structured sanitized summary — never raw conversation text.

**Reconnect safety (release gate 3):** server is stateless per request — a reconnect re-sends the same `messages` payload minus the partial assistant turn; no duplicate assistant messages are appended server-side (client owns history). Partial output is safe to discard.

**Errors:** no dataset → 409 (from `require_dataset`) · no API key → 503 with `{"detail": "AI features unavailable — configure GEMINI_API_KEY"}` (reuse `settings.has_ai`) · provider errors streamed as `type: error` events, never as raw exception text.

**Acceptance:** contract tests: 409 without dataset · 503 without key · streamed chunks with mocked `_get_client` · usage trailer reflects the final chunk's `usage_metadata`.

---

### 7. Deterministic-context assembly + prompt allowlist

New **`api/services/ai_service.py`** (confirmed D8 — separate service keeps upload concerns apart):

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

**Identifier scrub (helper in `api/services/ai_service.py` — confirmed D8 home; patterns documented in `utils/sanitize.py`):**

```python
IDENTIFIER_PATTERNS = (
    "email", "e-mail", "user_id", "userid", "name", "first_name", "last_name",
    "phone", "mobile", "address", "zip", "ip", "device_id", "session_id", "uid",
    "ssn", "dob", "birth",          # added 2026-08-06 — unambiguous PII
)

def scrub_identifiers(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return (scrubbed_df, removed_columns). Drop identifier-like columns from
    prompt-bound samples (retention §8). Best-effort: documented patterns only;
    never silently keeps PII."""
    removed = [c for c in df.columns if any(p in str(c).lower() for p in IDENTIFIER_PATTERNS)]
    return (df.drop(columns=removed) if removed else df), removed
```

**Refined D4 — drop + warning:** identifier columns are removed before prompt assembly **and** a structured `DatasetWarning` is attached to the response context naming the removed columns, e.g.:

```json
{"code": "identifiers_removed_for_ai", "message": "Potential identifier columns were removed before AI analysis.", "removed_columns": ["email", "user_id"]}
```

Extend `DatasetWarning.code` to include `identifiers_removed_for_ai` and add an optional `removed_columns: list[str] = []` field. Keep the warning in `DatasetContext`, display it in Streamlit during coexistence, and surface it in React (Phase 4). Stats-only prompts are **not** the Phase 3 mode — they remain a documented future high-sensitivity/client-data option.

**Heuristic, NOT a complete PII detector (corrected 2026-08-06):**

- The pattern list is best-effort **name-pattern matching** — a column that fails a pattern test is **not automatically safe**, and an unknown column is **not automatically removed**.
- **High-sensitivity data mode remains out of scope for Phase 3.**
- Hosted/client deployments require a **documented data-classification review before `client_paid` is enabled**.
- `ssn`, `dob`, `birth` are default patterns (added above). Business-entity columns (`customer`, `account`, `member`, `employee`, `student`) are **deliberately NOT default patterns** to avoid over-removing legitimate metric dimensions — a future high-sensitivity config may enable them.
- A generic `id` pattern is **forbidden** for the same over-removal reason.

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

**Refined D11 — two-stage guard: heuristic hard guard with deterministic trim; exact `countTokens` only near the threshold:**

Pipeline (every request): validate chat payload limits → build deterministic context → **estimate input tokens locally (chars ÷ 4)** → reserve output → trim deterministically if over → **optionally exact `countTokens` at ≥80% of budget** → send → record provider usage metadata.

1. Estimate tokens locally via **chars ÷ 4** — never a `countTokens` API call before every request (`countTokens` is free but separately rate-limited, and adds round-trip latency + its own failure mode — it does not consume generation quota; verification note 2). There is no universally accurate "tiktoken for Gemini" — Gemini uses its own tokenizer; local estimates are model-approximate. (Verify the exact `countTokens` method shape in the installed SDK at implementation time — verification note 1.)
2. Effective rule: `estimated_input_tokens <= AI_MAX_CONTEXT_TOKENS - AI_RESERVED_OUTPUT_TOKENS` (i.e. 24,000 − 4,096 = **19,904 input allowance**). **Corrected C4:** the provider's `max_output_tokens` is set explicitly to `AI_RESERVED_OUTPUT_TOKENS` so the reserved allowance is honored during generation — the total never exceeds `AI_MAX_CONTEXT_TOKENS`.
3. **Deterministic trim order:** (1) drop raw/sample rows first → (2) reduce sample-row count → (3) keep quality warnings, metric-status caveats, filters, provenance → (4) keep aggregate summaries → (5) **reject only if the deterministic minimum context still exceeds the guard**.
4. **Exact `countTokens` only in the near-limit band** (≈80–100% of budget), never on ordinary requests:
   ```python
   estimate = len(assembled_prompt) // 4
   if estimate < int(max_prompt_tokens * 0.80):
       stream_now()                          # ordinary request — no preflight, best TTFT
   elif estimate < max_prompt_tokens:
       exact = await count_tokens(assembled_prompt)   # near-limit band only
       stream_now() if exact <= max_prompt_tokens else trim_or_reject()
   else:
       trim_or_reject()                      # over budget — trim deterministically, then reject if still over
   ```
5. Count the **whole assembled request** (system instructions + deterministic context + metric caveats + chat history + samples), not just the newest user message; treat counts as **model-specific**.
6. Guard failure returns a typed non-provider error: `{"type":"error","code":"context_too_large","retryable":false,"message":"The analysis context is too large. Narrow filters or reduce the dataset scope."}`
7. After the response, record **actual provider usage** (`usage_metadata`) so estimates can be tuned — via the ledger's safe diagnostic dimensions (Task 3); never log prompt text to debug counts.

**Preserve perceived responsiveness (streaming):** build deterministic context locally → run the local heuristic immediately → begin the provider stream immediately unless near the threshold → avoid a `countTokens` preflight on ordinary requests → send the first SSE `text` event as soon as the provider emits a chunk → emit usage only at the end. Prompt size affects time-to-first-token; output length affects time-to-last-token — reserve output budget, cap output length, and stream.

**Acceptance:** unit tests assert identifier columns never appear in `prompt_df`, `removed_columns` is populated, and a `DatasetWarning` with `code: identifiers_removed_for_ai` is emitted; caveat builder covers provisional + unavailable; `build_summary_prompt` gets the scrubbed sample; heuristic guard + trim order (raw rows dropped first, caveats kept) verified; `context_too_large` error typed and non-retryable.

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

### 10. Export — **confirmed D6: DEFERRED to Phase 4**

Export endpoints are **not** part of the Phase 3 PR. `report_exporter` (`build_markdown_report` / `build_excel_report` / `build_pdf_report`) is already decoupled and deterministic; the export API + React download flow ship together in Phase 4 (with the §metadata-only retention logging rule: `{format, timestamp, row_count, opaque request/session id}` — never contents). Note the deviation from master-plan §7's task list in the gate evidence.

---

### 11. `GET /api/v1/ai/usage` (per-session ledger view)

```python
class UsageResponse(BaseModel):
    request_count: int
    success_count: int
    failure_count: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    thought_tokens: int
    cached_tokens: int
    tool_tokens: int
    estimated_prompt_tokens: int
    context_trimmed: int
    identifiers_removed: int
    avg_ttft_ms: int | None        # mean time-to-first-token across requests (observability)
    avg_ttlt_ms: int | None        # mean time-to-last-token across requests (observability)
    by_request_type: dict[str, int]
    by_model: dict[str, int]
```

Reads the per-session ledger (Task 3). Feeds the §17 AI cost guardrails later; also lets the React shell render usage stats without touching Streamlit session state. Latency aggregates (`avg_ttft_ms`/`avg_ttlt_ms`) are computed from the ledger's timestamp fields — observability only, no content. **Acceptance:** contract test asserts counts grow across requests, diagnostic dimensions update when trimming/scrubbing occurs, latency aggregates are present after a mocked stream, and Clear Data resets everything.

---

### 12. Tests, model hygiene, PR acceptance gate

**Model hygiene (locked):** prune `gemini-2.0-flash` + `gemini-1.5-flash` from `utils/gemini_client.py` `AVAILABLE_MODELS` + `MODEL_CONTEXT_LIMITS`; keep `validate_api_key`, `_classify_api_error`, sync/stream generators intact. Update `tests/test_gemini_client.py` expectations if they reference pruned models.

**Test matrix (new files under `tests/api/`):**

| Test | Asserts |
|---|---|
| `test_chat.py` | 409 no dataset · 503 no key / `feature_disabled` under `disabled` policy · mocked stream yields ≥2 partial chunks · named events (`event: text/usage/done/error`) · bounded-history 422 (20 msgs / 24k chars) · conditional 429 retry (retryable honors `Retry-After`; `quota_exhausted` never retried; no mid-stream retry) · timeout events · **terminal sequence (error→done; nothing after error — C5)** · **concurrent requests serialize on `ai_lock` — deterministic ledger (C6)** · **queue-wait: second request proceeds after the stream or times out `ai_busy` past `AI_QUEUE_WAIT_SECONDS`; queued-cancel leaves ledger untouched** |
| `test_analysis_summary.py` | summary + usage returned · 409/503 · mocked `_get_client` · timeout config honored |
| `test_analysis_forecast.py` | insufficient-data vs valid forecast · auto-detect date col |
| `test_analysis_funnel.py` | per-step aggregation · min_length=2 validation |
| `test_usage.py` | ledger counts grow (success/failure/tokens + tool_tokens by model + request type) · diagnostic dimensions update (estimated_prompt_tokens, context_trimmed, identifiers_removed) · latency aggregates present after a mocked stream (TTFT/TTLT) · Clear Data resets · no cap enforced (D13) · **provider failure emits a failure `UsageEvent` before the error event → `failure_count` increments** |
| `test_ai_context.py` | identifier scrub drops PII columns + `identifiers_removed_for_ai` warning with `removed_columns` · metric caveats for provisional/unavailable · heuristic guard + trim order (raw rows dropped first, caveats kept) · sliding-window history (newest user kept, oldest assistant dropped first) · 3-branch budget flow (stream-now < 80% · exact countTokens in 80–100% band · trim/reject over) |
| `test_settings_ai.py` | boots with/without key · `has_ai` · `GEMINI_MODEL` default + override · timeout defaults · `GEMINI_DATA_POLICY` modes (`local_free` warn, `client_paid`, `disabled` 503) · **invalid policy value → startup validation error (C3)** |

All Gemini routes mock `utils.gemini_client` client — no live key in CI.

**PR boundary (single PR):** `api/config.py` · `.env.example` guard additions · `utils/gemini_client.py` model hygiene + async stream path · `api/services/ai_service.py` · `api/routes/chat.py` + `analysis.py` + `usage.py` · `api/schemas.py` additions · `api/stores/session_store.py` (UsageLedger field) · `tests/api/*` · `tests/test_gemini_client.py` updates. **No GA4, Drive, React, evidence, export.**

**Validation:** `pytest tests -q` (full regression, expect ~794 + new) · `pytest tests/api -q` · `git ls-files -z | xargs -0 python3 scripts/check_credentials.py` (exit 0) · `pre-commit run --all-files` · manual smoke: upload fixture → chat SSE curl with live key (local `.env` only).

## Phase-integration checklist (corrected 2026-08-06 — before any Phase 3 PR merges)

- [ ] Phase 2 closure evidence linked in `specs/README.md` + master plan (implementation `8c66eea`, 794 tests, guard exit 0).
- [ ] API error taxonomy shared by chat, summary, forecast, and funnel endpoints.
- [ ] No SSE payload contains raw exception text (C2) — `classify_provider_error` only.
- [ ] `disabled` policy tested **before** Gemini client construction (D7).
- [ ] Clear Data resets dataset state, chat state, AI warnings, and `UsageLedger` (D5).
- [ ] Two concurrent requests for the same session have deterministic ledger behavior (C6).
- [ ] SDK `countTokens` probe recorded against the pinned dependency version (Task 0).
- [ ] Live local-key smoke is opt-in and cannot run in CI.

## Exit criteria (DoD)

- [ ] Chat + summary + forecast + funnel + usage endpoints live under `/api/v1`; all contract-tested (export deferred to Phase 4 per D6).
- [ ] SSE contract test asserts ≥2 partial chunks stream (release gate 3 reconnect shape documented); **named events** (`event: text/usage/done/error`) + JSON payloads + typed error codes asserted.
- [ ] Prompt allowlist + identifier scrub (drop + `identifiers_removed_for_ai` warning with `removed_columns`) enforced per data-retention-policy §7–§8 (no raw rows, no identifiers, no tokens in prompts or usage events).
- [ ] Metric-status policy enforced at the boundary (provisional caveated; unavailable never numeric evidence).
- [ ] Usage ledger on `AppSession` (request/success/failure/token + tool-token counts by model + request type, safe diagnostics `estimated_prompt_tokens`/`context_trimmed`/`identifiers_removed`, latency timestamps → TTFT/TTLT), reset by Clear Data, counts only (no cap — D13), no content stored; never log prompt text to debug counts.
- [ ] `AVAILABLE_MODELS` pruned of shut-down models; `GEMINI_MODEL` env-configurable with 2.5-flash fallback (D1).
- [ ] Async aio streaming path + three explicit timeouts (30/60/120) + conditional pre-text 429 retry + two-layer bounded chat history (D2/D9/D10/D12) tested.
- [ ] `GEMINI_DATA_POLICY` modes behave as documented (`local_free` warns; `disabled` 503s) — never inferred from key format (D7).
- [ ] Full regression + guard + hooks green; live smoke with a real local key.

## Gate table — Phase 3 gate

| Gate | Evidence | Owner | How verified |
|---|---|---|---|
| No regression | Existing Streamlit + Phase 1/2 Python behavior still works | Implementation agent | ✅ **CLOSED 2026-08-06** — `pytest tests -q` = **859 passed** (full regression incl. 73 API contract tests) |
| Contract | Chat/analysis/export/usage endpoints match schemas + error taxonomy | Implementation agent | ✅ **CLOSED 2026-08-06** — `pytest tests/api -q` green: chat SSE lifecycle (success/error/done terminal sequences, `ai_busy`, disconnect-safe terminal behavior), typed error classifier, ledger + failure accounting, summary/forecast/funnel, settings validation, `ai_service` units (`bcf4866` review round: disconnect-safe SSE terminal behavior, shared latency accumulation, deprecated status handling) |
| AI behaviour | Gemini calls use the decided model + fallback; streaming + disconnect + usage verified | Implementation agent | ✅ **CLOSED 2026-08-06** — mocked-unit streaming + usage-ledger asserted; Task 0 countTokens probe recorded against pinned `google-genai` 2.14.0 (near-limit preflight only); live-key smoke is opt-in and never runs in CI |
| Retention boundary | Prompt allowlist + identifier scrub + metric-status caveats enforced | Implementation agent | ✅ **CLOSED 2026-08-06** — deterministic context assembled server-side, identifiers removed before prompt assembly, provisional caveated / unavailable never numeric, prompt allowlist per `../policies/data-retention-policy.md` §7–§8; `test_ai_context.py` + policy cross-check green |
| Phase 3 gate | All exit criteria met | Implementation agent | ✅ **CLOSED 2026-08-06** — commits `bb6f564` + `bcf4866` on `feat/react-fastapi-migration`, 859 passed, guard exit 0, hooks green; `specs/README.md` Phase 3 row flipped to DONE |

## ✅ DECISION register — ALL CONFIRMED (2026-08-06)

| # | Decision | Confirmed choice |
|---|---|---|
| 1 | Default Gemini model | **C — env-configurable `GEMINI_MODEL`, `gemini-2.5-flash` fallback; selector {2.5-flash, 3.5-flash, 3.5-flash-lite}** |
| 2 | Streaming implementation | **B — async `aio` path (`generate_response_stream_async`), additive to the sync generator** |
| 3 | SSE event shape | **Refined A — named SSE events** (`event: text/usage/done/error`) + JSON payloads; typed error codes (`rate_limited`, `quota_exhausted`, `provider_unavailable`, `timeout`, `context_too_large`, `feature_disabled`); F3 reader updated in Phase 4 |
| 4 | Identifier severity | **Refined B — drop + structured `DatasetWarning` (`code: identifiers_removed_for_ai`, `removed_columns`); stats-only prompts kept as a future high-sensitivity option** |
| 5 | Usage ledger home | **Refined A — `UsageLedger` field on `AppSession`** (request/success/failure/token counts by model + request type); reset by Clear Data |
| 6 | ai_service home | **A — separate `api/services/ai_service.py`** |
| 7 | Export in Phase 3 | **B — deferred to Phase 4** (with the React download flow + metadata-only logging) |
| 8 | Free vs paid tier | **Refined Custom — explicit `GEMINI_DATA_POLICY` runtime policy** (`local_free` warns · `client_paid` required for hosted beta · `disabled` 503s) — **never inferred from key format** |
| 9 | 429/rate-limit retry | **Refined Custom — one conditional retry, only before first streamed text**; honors `Retry-After`/`RetryInfo`; jittered 2–5 s otherwise; never retries `quota_exhausted` or mid-stream |
| 10 | Request timeouts | **Refined A — three explicit client-side timeouts** (`AI_FIRST_TOKEN_TIMEOUT_SECONDS=30`, `AI_GENERATE_TIMEOUT_SECONDS=60`, `AI_STREAM_TIMEOUT_SECONDS=120`); cancel + typed `timeout` event |
| 11 | Prompt-size guard | **Refined Custom — two-stage guard**: heuristic chars÷4 every request; exact `countTokens` only at **≥80% of budget** or for debug; whole-assembled-request counting; model-specific tokenizers; `context_too_large` typed + non-retryable |
| 12 | Chat payload limits | **Refined A — bounded history, two layers + token-budgeted sliding window** (max 20 msgs / 4k chars each / 24k total → 422; then fixed-context + sliding-history trim preserving newest user msg, oldest assistant turns dropped first, caveats never trimmed; no auto-summarization in Phase 3) |
| 13 | Per-session AI budget | **Refined A — record counts only in Phase 3** + optional non-blocking log warning at a very high threshold; enforcement stays a §17 hosted-beta gate |
