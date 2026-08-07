# Phase 6 — Cutover, Hosting, Retire Streamlit

> 🔵 **ACTIVE — expanded + deepened (2026-08-06) for execution after Phase 5; pending Task 0 (Cloud Run readiness probe).**
> **Phase 5 (GA4 OAuth + Drive import) is DONE** (`f032c9b` on `feat/react-fastapi-migration`) — Task 6/7/10 must migrate the *real* Phase 5 artifacts enumerated in [Post-Phase-5 reality](#post-phase-5-reality-2026-08-06--what-phase-6-must-change).
> Refined round 2 (2026-08-06): Redis lock implementation detail (single-instance lease lock, not
> Redlock), Redis failure typing (503 vs SSE), healthz/readyz, TTL-first cleanup + BackgroundTasks
> policy, and the OAuth transaction flow parked from owner guidance.
> Single-origin production deployment: the built React SPA is served **statically by the
> FastAPI container** (cookies, OAuth callbacks, CORS, SSE all same-origin), hosted on **Cloud
> Run**, with Streamlit retired after feature parity and a documented rollback path.
> **This file carries the §17 operational-readiness deferred gates** (master-plan §17).

## Purpose

Ship the Phase 4 `frontend/dist` build behind FastAPI in one container, deploy to Cloud Run,
and retire the Streamlit app. Architecture decisions recorded 2026-08-06 from owner guidance:

```text
- ONE Uvicorn worker per container while session/dataset/ledger/lock state is in-process.
  No Gunicorn; no --workers > 1. Cloud Run handles replica scaling.
- FastAPI serves frontend/dist (Vite builds static assets; FastAPI owns the server).
- Nginx only if a VPS/Kubernetes/multi-container deployment is later chosen — NOT for the
  Cloud Run single-container path. Choose ONE production SPA owner, never both.
- Session cookie: opaque server-owned ID, HttpOnly + Secure + SameSite=Lax + Path=/ + no
  Domain (__Host- prefix in production). OAuth tokens never reach the browser.
- Redis (Memorystore) is added when multi-instance scaling is enabled — sessions, locks,
  OAuth state out of process memory; datasets/exports stay in object/durable storage.
```

## Owner decisions (2026-08-06)

| Decision | Answer | Consequence for this spec |
|---|---|---|
| D4 live Google smoke | **Keep explicitly pending** — dedicated **synthetic** sandbox only (never client data); see [D4 sandbox governance](#d4-sandbox-governance-no-client-data) | Phase 5 stays closed on the no-credential wiring gate; the `E2E_REAL_GOOGLE=1` smoke becomes a **pre-hosted-beta exit gate** (Task 10), never a Phase 6 code blocker |
| Hosting target | **Cloud Run** (as planned) | Tasks 0/2/3/7/8 unchanged; Nginx (Task 9) stays the documented alternative only |
| Redis timing | **Local stays in-memory; Redis from the first hosted beta** (even a single replica) | Task 6 is executed as beta bring-up — Cloud Run instances are ephemeral (restart, revision replacement, scale-to-zero, cross-instance requests), so OAuth/session state must be durable from day one; VPC connector added with Redis, not in local-first Phase 5 |
| Production domain | **Not yet — use `<app-domain>` placeholders**; separate dev OAuth client now, separate production client at pre-beta (see [Dev vs pre-beta OAuth](#dev-vs-pre-beta-oauth-configuration)) | Redirect allowlist, Picker referrer restriction, `__Host-` cookie, and `FRONTEND_URL`/`API_CORS_ORIGINS` stay parameterized; filled at deployment time |
| Streamlit retirement | **Private rollback window ≈ 2 weeks** after parity, then archive (see [Task 10 exit criteria](#task-10--cutover-streamlit-retirement-rollback)) | Task 10 keeps the private-running Streamlit path for the window, then archives whisperer-30 with a fold-in note |

### D4 sandbox governance (no client data)

The live smoke uses a **dedicated synthetic sandbox only** — never a client property or
account just because it is easier:

```text
Dedicated Google test account
Dedicated synthetic GA4 property (synthetic/non-client traffic only)
Dedicated Drive fixture folder
Synthetic CSV/XLSX fixtures
No client identities, proprietary content, or production OAuth credentials
```

The smoke validates consent, PKCE callback/state, scope behavior, property compatibility,
pull shape, pagination contract, Picker token + selection, Drive download/import, and Clear
Data — none of which require client data. If a real client-property probe is ever necessary,
**all** of these must be in place first: client written authorization · confirmed data
classification + permitted-use scope · `client_paid` data-policy mode · dedicated production
OAuth project/client · HTTPS custom domain + exact redirect URI · token encryption at rest ·
retention/deletion + incident-response posture · no raw data or tokens in logs, fixtures,
screenshots, or test reports.

### Dev vs pre-beta OAuth configuration

```text
Development (separate dev OAuth client):
  http://localhost:5173                       (authorized JS origin)
  http://localhost:8000/api/v1/ga4/callback   (exact redirect URI)

Pre-beta (separate production OAuth client):
  https://<app-domain>                        (authorized JS origin)
  https://<app-domain>/api/v1/ga4/callback    (exact redirect URI)
  Picker API key restricted to https://<app-domain>/*
```

Google requires HTTPS for production redirect URIs and authorized JS origins (localhost is the
development exception) and **exact-match** redirect URIs — no open redirects or path
traversal. Before any external/client beta access, prepare: verified production domain · HTTPS
· public product homepage · privacy policy · terms of service · exact OAuth redirect URI ·
authorized JavaScript origin · Picker referrer allowlist · `__Host-insights_session` cookie
config (`Secure` · `HttpOnly` · `SameSite=Lax` · `Path=/` · no `Domain` attribute).

## Post-Phase-5 reality (2026-08-06) — what Phase 6 must change

Phase 5 shipped the GA4/Drive OAuth + import vertical slice (`f032c9b`). These implemented
artifacts define exactly what Phase 6 migrates — nothing below is speculative:

| Phase 5 artifact | Current state (`f032c9b`) | Phase 6 fate |
|---|---|---|
| `api/stores/oauth_store.py` (`oauth_transactions`) | In-memory TTL store with `put` (NX) / `get_and_delete` / `peek`; key `ie:oauth:state:<sha256(state)>`; 10-min TTL | **Redis swap, same interface** (Task 6) — Redis `GETDEL` (or the Lua get-and-delete fallback); `ga4.py` routes unchanged |
| `api/stores/session_store.py` sessions | In-memory; carry `ga4_credentials` / `drive_credentials` (Fernet blobs), `dataset_id`, `metadata`, `usage_ledger` | Redis session JSON (Task 6); token blobs stay server-side only, never in the browser |
| Token encryption (`ga4_service.encrypt_tokens`) | Fernet key **derived from `API_SESSION_SECRET`** (`sha256`) | Keep the derivation; **rotating `API_SESSION_SECRET` forces all users to reconnect** — document in the rotation checklist; optional hardening item: dedicated `TOKEN_ENCRYPTION_KEY` secret |
| OAuth transaction cookie `insights_oauth_txn` | `secure=False` (local HTTP) | `secure=True` behind Cloud Run via `COOKIE_SECURE=true`; same for the session cookie (Task 4) |
| OAuth redirect URI | Single allowlisted `GA4_REDIRECT_URI` | Prod value = `https://<app-domain>/api/v1/ga4/callback` — Google console allowlist must match exactly |
| Picker API key (`VITE_GOOGLE_PICKER_API_KEY`) | Frontend env var, ships in the bundle | **Baked at build time** from a CI secret (build arg) — never a runtime env var; restrict the key to the production HTTP referrer in Google Cloud console |
| GA4/Drive secrets | `GA4_CLIENT_ID` / `GA4_CLIENT_SECRET` / `GA4_PROPERTY_ID` / `GOOGLE_CLOUD_PROJECT_NUMBER` / `DRIVE_ENABLED` / `GA4_ENABLED` / `drive_download_timeout_seconds` | Secret Manager (Task 7); `*_ENABLED` stay env vars |
| CSRF / same-origin | `enforce_same_origin_unsafe` implemented (Phase 5) | Configure the production origin allowlist (`api_cors_origins`); add a CSRF token/header only if a cross-site topology appears |
| Live Google smoke | Pending D4 sandbox credentials (`E2E_REAL_GOOGLE=1`, never CI) | Run **before** the hosted beta (exit gate — not a Phase 6 code blocker) |

## Inputs / source documents

- master-plan §10 (Phase 6), §11-E (CI/CD), §12 (SPA fallback in `api/main.py`), §13 (open
  decision #4 Cloud Run), §14 (DoD), §17 (operational-readiness deferred gates)
- `../policies/dockerfile-pattern.md` (Vite build → FastAPI runtime, SPA fallback, verification)
- `../policies/branch-and-freeze-policy.md` (Streamlit freeze + lift criteria)
- `../policies/data-retention-policy.md` (hosted retention controls)
- Phase 3 spec — SSE contract, typed errors, `ai_busy`, timeouts (Task 5 of this spec serves it)
- Phase 4 spec — `frontend/dist` build, `API_BASE = "/api/v1"`, `credentials: "include"`
- Phase 5 spec — implemented GA4/Drive OAuth + import (`f032c9b`): `oauth_store.py`, session `ga4_credentials`/`drive_credentials`, `insights_oauth_txn` cookie, Picker env var, `enforce_same_origin_unsafe`

## Tracks consumed

- **C** (tests): full-parity regression + hosted smoke; container job builds only after
  backend + frontend jobs are green.
- **D** (security/credentials): credential-hygiene sweep in CI; Workload Identity Federation /
  managed identities + Secret Manager; no live credentials in the final image.
- **E** (CI/CD): unified frontend+backend gates + container job; Cloud Build + Cloud Run.
- **F** (retention/AI boundary): hosted retention controls; export metadata-only logging.
- **G** (research discipline): Cloud Run readiness probe (Task 0) before execution.

---

## Task 0 — Research gate: Cloud Run readiness probe

Run the **Cloud Run readiness** prompt (archive §3.12, prompt 4) and record results in the gate
table. Verify against current Google docs at implementation time (not memory):

```text
- Container static-file serving + SPA fallback patterns (FastAPI StaticFiles + FileResponse).
- SSE timeout / reconnect / disconnect / concurrency behavior behind Cloud Run.
- Cookie security behind Cloud Run proxy headers (--proxy-headers, forwarded allow-list).
- Request-size + HTTP/1 vs end-to-end HTTP/2: 32 MiB HTTP/1 request limit supports the 25 MB
  browser cap (HTTP/2 not selected).
- Memory/concurrency for Pandas/XLSX ingestion; health/readiness + rollout strategy.
- Cloud Build + Cloud Run config review against the Dockerfile in Task 2.
```

---

## Task 1 — Runtime architecture: one worker, one SPA owner

**Workers (owner guidance 2026-08-06):** run **one Uvicorn worker per container** until
sessions, datasets, the usage ledger, and the `ai_lock` move out of process memory. Multiple
workers would let the same cookie hit different processes — missing dataset state, split usage
counts, ineffective `ai_lock` serialization, inconsistent Clear Data. FastAPI/Uvicorn's
`--workers N` is only appropriate after Redis/Postgres hold sessions/locks and durable storage
holds datasets/artifacts. Cloud Run already scales replicas horizontally.

```bash
# Current deployment (single container):
uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1 --proxy-headers

# After sessions/locks move to Redis (multi-instance) — start at 2, measure p95 latency,
# SSE time-to-first-token, memory, error rate, session consistency before increasing:
uvicorn api.main:app --host 0.0.0.0 --port 8080 --workers 2
```

A single **async** worker handles multiple SSE streams fine — streams yield control while
awaiting provider/network I/O. The real limits are Cloud Run request concurrency, Gemini
quota, memory per active stream, the Redis lock policy, and client-disconnect handling.
**Do not set Cloud Run concurrency to 1 just because there is one worker** — that would
serialize unrelated users at the platform layer. Start at `--concurrency 10`.

**SPA owner (owner guidance 2026-08-06):** FastAPI serves `frontend/dist`. Nginx is a
deliberate later choice for VPS/K8s/multi-container only; do **not** combine both SPA
handlers (ambiguous caching, harder client-route debugging).

---

## Task 2 — Multi-stage Docker build

Build Vite once in a Node stage, install Python deps in a separate stage, copy only runtime
artifacts into a minimal runtime image.

```dockerfile
# syntax=docker/dockerfile:1
# ── Frontend dependency/build stage ─────────────────────────────────────────
FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run check && npm run build

# ── Python dependency stage ─────────────────────────────────────────────────
FROM python:3.12-slim AS python-build
WORKDIR /build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
COPY requirements/base.txt ./requirements/base.txt
RUN pip install --prefix=/install -r requirements/base.txt

# ── Minimal runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 APP_ENV=production
COPY --from=python-build /install /usr/local
COPY api ./api
COPY utils ./utils
COPY scripts ./scripts
# Vite's production artifact; FastAPI serves this directory (Task 3).
COPY --from=frontend-build /build/frontend/dist ./frontend/dist
RUN groupadd --system app && useradd --system --gid app --create-home app \
    && chown -R app:app /app
USER app
EXPOSE 8080
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --proxy-headers"]
```

> **Note on `migration/`:** copy it into the image only if runtime tests/policy validation
> need it; if it is documentation-only at runtime, omit it. The `.dockerignore` draft below
> excludes `*.md` — adjust consciously.

**`.dockerignore` (repository root):**

```gitignore
.git
.github
.env
.env.*
!.env.example
**/__pycache__
**/*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
frontend/node_modules
frontend/dist
tests
plans
*.md
```

**The final image must NOT contain:** `node_modules`, npm cache, TypeScript source maps
(unless intentional), test credentials, `.env`, the Google OAuth client secret, the Gemini API
key, or local session files.

---

## Task 3 — FastAPI serves the SPA

Register **all API routers first**, then mount assets and the client-route fallback **last** so
`/api/v1/*` never silently returns React's `index.html`.

```python
# api/main.py — Phase 6 additions (routers are already registered above)
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

DIST_DIR = Path(__file__).resolve().parents[1] / "frontend" / "dist"
ASSETS_DIR = DIST_DIR / "assets"


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception as exc:
            if getattr(exc, "status_code", None) == 404:
                return await super().get_response("index.html", scope)
            raise


if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    app.mount("/", SPAStaticFiles(directory=DIST_DIR, html=True), name="frontend")
```

Alternative explicit fallback (equivalent — choose one, keep API 404s honest):

```python
@app.get("/{client_path:path}", include_in_schema=False)
async def spa_fallback(request: Request, client_path: str):
    if client_path.startswith("api/"):
        return {"detail": "Not Found"}  # API misses stay JSON 404s
    requested = DIST_DIR / client_path
    if client_path and requested.is_file():
        return FileResponse(requested)  # favicon, manifest, robots.txt
    return FileResponse(DIST_DIR / "index.html")  # TanStack Router owns client routes
```

**Production cache policy** — Vite fingerprints assets, so cache them aggressively but never
`index.html`:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class StaticCacheHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif request.url.path == "/" or not request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

app.add_middleware(StaticCacheHeadersMiddleware)
```

---

## Task 4 — Session cookies (server-owned opaque ID)

The browser holds only an **opaque, server-issued session ID** in an `HttpOnly` cookie — never
a JWT in `localStorage`, and never provider tokens. Local dev is HTTP so `secure=False`;
production is HTTPS-only with `secure=True`. Omit `Domain` (host-only cookie, scoped to the app
host, not shared across arbitrary subdomains).

```python
# api/services/session_cookies.py
from fastapi import Response

# __Host- requires Secure=True, so local plain-HTTP dev uses a different cookie name.
# Prod:  __Host-insights_session  (browser enforces Secure + Path=/ + no Domain)
# Local: insights_session         (Secure=False)
session_cookie_name = (
    "__Host-insights_session" if settings.cookie_secure else "insights_session"
)

def set_session_cookie(response: Response, *, session_id: str, secure: bool, max_age_seconds: int) -> None:
    response.set_cookie(
        key=session_cookie_name,
        value=session_id,
        max_age=max_age_seconds,
        httponly=True,
        secure=secure,        # False for local HTTP dev only — never a production downgrade
        samesite="lax",
        path="/",
    )
```

```text
Local Vite HTTP:      insights_session        · Secure=False · HttpOnly · SameSite=Lax
Hosted HTTPS:         __Host-insights_session · Secure=True  · HttpOnly · SameSite=Lax
```

| Attribute | Local Vite dev | Hosted single-origin |
|---|---|---|
| `HttpOnly` | True | True |
| `Secure` | False (local HTTP) | True |
| `SameSite` | lax | lax |
| `Path` | `/` | `/` |
| `Domain` | omit | omit |
| Cookie prefix | — | `__Host-` preferred |
| Value | opaque random ID | opaque random ID |

**Session lifecycle:** 2 h idle / 12 h absolute (existing `api/dependencies.py` policy);
rotate the ID after login, OAuth completion, and privilege changes; delete with the same
path/security attributes used to create it. `SameSite=None; Secure` is only for a genuinely
cross-site topology (not the recommended Phase 6 design) and would require credentialed CORS +
stronger CSRF controls.

**Proxy/TLS:** with Nginx terminating HTTPS (or Cloud Run's edge), FastAPI sees internal HTTP —
keep `cookie_secure` as a **deployment setting**, never derived solely from
`request.url.scheme`. Trust forwarded headers only from the known proxy range:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8080 --proxy-headers \
  --forwarded-allow-ips="127.0.0.1"
```

**CSRF (same-origin SPA):** `enforce_same_origin_unsafe` (POST/PUT/PATCH/DELETE `Origin`
check) is **already implemented** (Phase 5) — Phase 6 configures the production public origin
(`api_cors_origins` = `https://<app-domain>`; `""` disables cross-origin API access). Add a CSRF
token/header before a hosted beta **only if** a cross-site topology appears. OAuth state/PKCE
validation stays server-side. Never put Google/Gemini/Drive/session credentials in React state,
Vite env vars, or browser storage.

**OAuth transaction cookie (Phase 5):** `insights_oauth_txn` (HttpOnly, `SameSite=Lax`, 10-min)
must follow the same local/prod split — `secure=True` in production via `COOKIE_SECURE=true`.
The OAuth redirect allowlist in Google Cloud must be the production
`https://<app-domain>/api/v1/ga4/callback` **exactly** (a second console entry is allowed for
the local dev redirect while developing against real Google, never in CI).

---

## Task 5 — SSE serving (Phase 3 contract, one worker)

The Phase 3 wire contract is named events with JSON payloads. `StreamingResponse` already
implements it; if `sse-starlette.EventSourceResponse` is adopted, preserve the identical wire
shape. Set `X-Accel-Buffering: no` for proxy environments.

**Timeout chain (aligned):**

| Layer | Value |
|---|---:|
| Queue wait | 30 s (`AI_QUEUE_WAIT_SECONDS`) |
| First token | 30 s (`AI_FIRST_TOKEN_TIMEOUT_SECONDS`) |
| Whole provider stream | 120 s (`AI_STREAM_TIMEOUT_SECONDS`) |
| Cloud Run request timeout | 180–300 s (`--timeout`; default 300, max 3600 — set above the stream deadline for cancellation/cleanup headroom) |
| Redis lock lease (Task 6) | 150+ s with safe release/renewal |

**Disconnect handling:** the chat route's terminal `done` yield is already guarded against
`CancelledError`/`GeneratorExit` teardown (Phase 3 review fix). **Heartbeats:** normal text
chunks usually provide enough activity; add a `: keepalive` comment line (or
`{"comment": "keepalive"}`) support for idle-period resilience testing.

---

## Task 6 — Redis (Memorystore): sessions, locks, OAuth state, failure handling

**Owner decision (2026-08-06): Redis is introduced at the first hosted beta — even a single
replica.** This is **not** a multi-instance-scale question: a single Cloud Run instance is
still ephemeral — it may restart, a deployment replaces the revision, scale-to-zero removes
process memory, and a later request can reach a different instance. OAuth transaction state
and active-session data would otherwise disappear. Local/Phase 6 code stays in-memory (one
worker, in-memory `SessionStore`/`DatasetStore`, no Redis); this task is beta bring-up.
Cloud Run reaches Memorystore through the **authorized VPC network** (VPC connector / direct
VPC egress) — add that connector work here, at beta, not in local-first Phase 5. Redis is the
**server-side session registry**; the browser keeps only the opaque cookie. Do NOT store raw DataFrames, previews,
prompts, model output, or access tokens as ordinary session JSON — store dataset references and
small metadata only; artifacts live in durable/encrypted storage. Redis connectivity: VPC
connector / direct VPC egress to private Memorystore; URL in Secret Manager, never in the repo
or frontend env vars.

```text
ie:session:<session-id>  = JSON session metadata (TTL = min(idle, remaining absolute))
ie:lock:ai:<session-id>  = short-lived distributed lock (unique owner token)
ie:oauth:state:<hash>    = PKCE/state transaction record (10-minute TTL)
ie:usage:<session-id>    = same lifetime as session; explicitly reset on Clear Data
```

### Lifespan-managed client (no per-request PING)

Open one pool in `lifespan`, close it at shutdown, expose it through dependency injection. Do
**not** `PING` on every request — translate actual Redis command failures into a typed
application error instead.

```python
# api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis
from redis.exceptions import RedisError

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis: Redis | None = None
    if settings.redis_url:
        redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True,
                               socket_connect_timeout=3, socket_timeout=3,
                               health_check_interval=30, max_connections=20)
        try:
            await redis.ping()
        except RedisError:
            await redis.aclose()
            if settings.redis_required:
                raise RuntimeError("Redis is required but unavailable during startup.")
            redis = None
    app.state.redis = redis
    try:
        yield
    finally:
        if redis is not None:
            await redis.aclose()

app = FastAPI(lifespan=lifespan)
```

```python
# api/errors.py
class RedisUnavailableError(Exception):
    """Redis is required for this request but is unavailable."""

class AiBusyError(Exception):
    """A same-session AI request did not acquire the lock in time."""
```

```python
# api/dependencies.py
from typing import Annotated
from fastapi import Depends, Request
from redis.asyncio import Redis
from api.errors import RedisUnavailableError

def get_redis(request: Request) -> Redis:
    redis: Redis | None = getattr(request.app.state, "redis", None)
    if redis is None:
        raise RedisUnavailableError()
    return redis

RedisDep = Annotated[Redis, Depends(get_redis)]
```

```python
# api/main.py — exception handler → typed 503
from fastapi.responses import JSONResponse
from api.errors import RedisUnavailableError

@app.exception_handler(RedisUnavailableError)
async def redis_unavailable_handler(request, exc):
    return JSONResponse(status_code=503, content={
        "detail": {"code": "session_store_unavailable",
                   "message": "Session services are temporarily unavailable.",
                   "retryable": True}})
```

Wrap Redis operations at the **service boundary** (`redis.exceptions.ConnectionError` /
`TimeoutError` → `RedisUnavailableError`) so callers never see raw driver errors.

**No in-memory fallback in hosted mode.** Never silently fall back to in-memory sessions when
Redis fails — that creates split-brain behavior (instance A serves a Redis session, instance B
a local one; the same cookie yields inconsistent auth, lock, ledger, and dataset state).

**Environment policy:**

| Environment | Redis policy | Behavior on failure |
|---|---|---|
| Local Phase 3 | Optional / disabled | Existing in-memory `AppSession` behavior |
| Local Redis integration tests | Required | Fail test startup or return typed 503 |
| Hosted beta | Required | Fail deployment startup if unavailable |
| Production multi-instance | Required | Never silently fall back to in-memory state |

### Distributed AI lock — single-instance lease lock (NOT Redlock)

Use a **single Redis instance lease lock** with an owner token for per-session AI
serialization — **not Redlock** (appendix: reference-only). Acquire **after** the queue wait
and **immediately before** the provider operation — never around request validation or prompt
assembly. The 150 s lease covers the 120 s stream plus cleanup margin and must exceed
`AI_QUEUE_WAIT_SECONDS + AI_FIRST_TOKEN_TIMEOUT_SECONDS + AI_STREAM_TIMEOUT_SECONDS + cleanup`.

```python
# api/services/redis_lock.py
from __future__ import annotations
import asyncio, logging, secrets, time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

RELEASE_LOCK_LUA = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0
"""

RENEW_LOCK_LUA = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("PEXPIRE", KEYS[1], ARGV[2])
end
return 0
"""

@asynccontextmanager
async def session_ai_lock(redis: Redis, *, session_id: str,
                          wait_seconds: float, lease_seconds: int) -> AsyncIterator[None]:
    key = f"ie:lock:ai:{session_id}"
    owner_token = secrets.token_urlsafe(32)
    deadline = time.monotonic() + wait_seconds
    acquired = False
    try:
        while time.monotonic() < deadline:
            acquired = await redis.set(key, owner_token, nx=True, px=lease_seconds * 1000)
            if acquired:
                break
            await asyncio.sleep(0.15 + secrets.randbelow(100) / 1000)  # jittered retry
        if not acquired:
            raise AiBusyError()
        yield
    finally:
        if acquired:
            try:
                await redis.eval(RELEASE_LOCK_LUA, 1, key, owner_token)
            except RedisError:
                # The lease is the safety fallback. Never mask the original exception.
                logger.warning("redis_lock_release_failed", extra={"lock_kind": "session_ai"})
```

Use it only around the provider-facing critical section:

```python
async with session_ai_lock(redis, session_id=session.id,
                           wait_seconds=settings.ai_queue_wait_seconds,
                           lease_seconds=150):
    async for chunk in ai_service.stream_chat(...):
        yield chunk
```

The compare-and-delete release is essential: a slow/stale request must not delete a newer
request's lock. Renew only while the request is alive **and** the owner token still matches
(`RENEW_LOCK_LUA`); never renew indefinitely — the application-level stream deadline stays
authoritative. Plain `EVAL` is acceptable here (release happens once per completed/failed
stream, not a hot loop); SHA script caching is an optional later optimization.

**SSE conversion rule:** once SSE headers/text have started, an HTTP 503 is impossible. Convert
mid-stream Redis failures into the existing typed SSE error contract:

```text
event: error
data: {"type":"error","code":"session_store_unavailable","retryable":true,
       "message":"Session services are temporarily unavailable."}

event: done
data: {"type":"done"}
```

### Session lifecycle — TTL is the primary cleanup system

Redis TTL handles normal expiration even if the browser closes, logout never runs, a container
is terminated mid-stream, or an OAuth callback is abandoned. Expiry is **not** a real-time
deletion guarantee — always validate `absolute_expires_at` inside the value on read.

```text
Create session:        SET ie:session:<id> JSON EX effective_ttl
Authenticated request: read record → remaining_absolute = absolute_expires_at - now
                       new_ttl = min(idle_seconds, remaining_absolute)
                       if new_ttl <= 0: delete record + SessionExpiredError
                       EXPIRE ie:session:<id> new_ttl    # never past absolute
Logout:                pipeline DEL ie:session:<id> + ie:lock:ai:<id> + ie:usage:<id>
                       delete browser cookie (same path/attributes)
Clear Data:            delete dataset-derived keys + derived state; retain OAuth connection
OAuth callback:        atomically consume the short-lived state record once
Absolute expiry:       Redis eventually removes the record; reads validate absolute_expires_at
```

### BackgroundTasks policy

FastAPI `BackgroundTasks` is for **best-effort** post-response work only. **Never** use it for:
releasing the AI lock, session revocation, OAuth state consumption, security-sensitive
deletion, TTL enforcement, or durable/large cleanup. Release the lock in the stream
generator's `finally`; handle durable cleanup with a queue, scheduled worker, Cloud Tasks, or a
periodic Cloud Run job.

Good uses: best-effort audit/usage event write · non-critical telemetry · deleting a
just-replaced temp artifact · triggering a small notification.

**Periodic orphan cleanup:** record `dataset_id / session_id / created_at / expires_at /
storage_uri / deletion_status` at artifact creation; a scheduled job (every 15–60 min) finds
`expires_at < now` with `deletion_status != deleted`, deletes the object, marks completion, and
emits an aggregate audit event. Do not depend on a web request arriving after expiry.

### Phase 5 state migration — `oauth_store` + session fields

The Phase 5 stores are already interface-shaped for this swap (`f032c9b`):

- **`oauth_transactions`** (`api/stores/oauth_store.py`): in-memory `put` (NX) /
  `get_and_delete` / `peek`. Redis implementation: `SET ie:oauth:state:<sha256(state)> JSON
  NX PX 600000` for `put`; `GETDEL` (Redis ≥ 6.2) or the parked Lua get-and-delete for
  `get_and_delete`; `GET` for `peek`. `ga4.py` routes call only these three methods — no
  route changes.
- **Session JSON** (`api/stores/session_store.py`): the in-memory `AppSession` carries
  `dataset_id`, `metadata`, `usage_ledger`, `ga4_credentials`, `drive_credentials`.
  Serialize the same fields into `ie:session:<id>`; `ga4_credentials`/`drive_credentials`
  are **already encrypted Fernet blobs** (never plaintext tokens) and travel inside the
  session JSON as opaque strings. Validate `absolute_expires_at` in the value on every read.
- **Session rotation (Phase 5 OAuth callback):** `_rotate_session` deletes the old session
  and creates a fresh one — the Redis implementation must do the same atomically
  (create new → copy `dataset_id`/`metadata`/`usage_ledger`/credentials → delete old),
  because the OAuth callback now runs on the *authenticated* path.

### Health endpoints

```text
GET /healthz  → {"status": "ok"}                     # process is alive (keep lightweight)
GET /readyz   → {"status": "ready", "redis": "ok"}  # required deps reachable; 503 if not
```

Use `/healthz` for Cloud Run liveness; `/readyz` for deployment checks and diagnostics.

---

## Task 7 — Cloud Run deployment

```bash
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/PROJECT_ID/insights-repo/insights-explorer:COMMIT_SHA

gcloud run deploy insights-explorer \
  --image us-central1-docker.pkg.dev/PROJECT_ID/insights-repo/insights-explorer:COMMIT_SHA \
  --region us-central1 \
  --port 8080 \
  --timeout 300s \
  --concurrency 10 \
  --min-instances 0 --max-instances 3 \
  --set-env-vars APP_ENV=production,COOKIE_SECURE=true,FRONTEND_URL=https://<app-domain> \
  --set-env-vars API_CORS_ORIGINS=https://<app-domain>,GA4_ENABLED=true,DRIVE_ENABLED=true \
  --set-secrets API_SESSION_SECRET=api-session-secret:latest \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-secrets GA4_CLIENT_ID=ga4-client-id:latest \
  --set-secrets GA4_CLIENT_SECRET=ga4-client-secret:latest \
  --set-secrets GA4_PROPERTY_ID=ga4-property-id:latest \
  --set-secrets GOOGLE_CLOUD_PROJECT_NUMBER=google-cloud-project-number:latest \
  --set-secrets REDIS_URL=redis-url:latest
```

**Secrets inventory (Secret Manager, one secret per row):**

| Secret | Used by | Rotation consequence |
|---|---|---|
| `api-session-secret` | Session ID signing/opaque store + **Fernet key derivation** | **Rotating it forces every user to reconnect** (GA4/Drive tokens unreadable) + invalidates live sessions — batch rotations with maintenance window |
| `gemini-api-key` | `ai_service` | None (AI becomes unavailable until updated) |
| `ga4-client-id` / `ga4-client-secret` | GA4 + Drive OAuth (shared client, D2) | Live OAuth grants stay valid; new connects use the new client |
| `ga4-property-id` | First pull | Pulls target the new property |
| `google-cloud-project-number` | Picker `setAppId` | Picker requires the matching app config |
| `redis-url` | Memorystore client (Task 6) | Sessions/locks reset — users re-authenticate |

`VITE_GOOGLE_PICKER_API_KEY` is **not** in this table: it is a public, referrer-restricted key
baked into the bundle at **build time** (CI secret → `--build-arg`), and the Google Cloud
console must restrict it to the production HTTP referrer (`https://<app-domain>/*`).

Per-container: **one Uvicorn worker**, Cloud Run handles replica scaling; every request must be
valid on any instance (no session-affinity reliance — that is an optimization at most). Raise
concurrency only after observing p95 time-to-first-token, p95 stream duration, Redis lock
contention, request memory, provider 429 rate, and client-disconnect rate.

---

## Task 8 — CI pipeline (backend → frontend → container)

```yaml
jobs:
  backend:
    steps: [checkout, install Python deps, run credential guard, run pytest, run lint/type checks]
  frontend:
    steps:
      - checkout
      - setup Node 22
      - cd frontend && npm ci
      - cd frontend && npm run check
      - cd frontend && npm run test
      - cd frontend && npm run build
  container:
    needs: [backend, frontend]
    steps:
      - checkout
      - docker build -t insights-explorer:${GIT_SHA} .
      - run container
      - curl /healthz
      - curl /
      - verify /assets/... returns 200
```

---

## Task 9 — Nginx alternative (only for VPS/K8s/multi-container)

Not needed for the Cloud Run single-container path — documented for the deliberate alternative.

```nginx
server {
    listen 80;
    server_name insights.example.com;
    root /usr/share/nginx/html;
    index index.html;

    location /assets/ {            # immutable Vite bundles
        try_files $uri =404;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    location /api/ {               # FastAPI + SSE
        proxy_pass http://fastapi:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;       # SSE chunks reach the browser as emitted
        proxy_cache off;
        proxy_read_timeout 130s;
        proxy_send_timeout 130s;
    }
    location / {                   # TanStack Router client-route fallback
        try_files $uri $uri/ /index.html;
    }
}
```

The important separation: `/api/*` → FastAPI · `/assets/*` → static immutable · everything
else → `index.html` → TanStack Router.

---

## Task 10 — Cutover, Streamlit retirement, rollback

- **Feature-parity checklist (12 items) green in the new UI**; Streamlit retired from the
  default path; whisperer-30 archived with a fold-in note.
- **Rollback:** Streamlit stays available **privately** for ≈ 2 weeks while React/FastAPI
  stabilizes (maintainers only — no new feature work, no new user onboarding, no divergent
  data model, no new public links); feature flag or separate beta URL; rollback criteria
  (failed OAuth, failed upload/preview path, data-isolation bug, persistent AI errors,
  unrecoverable session loss) route users to Streamlit or disable only the affected FastAPI
  feature — never emergency production code changes.
- **Archive exit criteria (all must be green before whisperer-30 is archived):**
  React/FastAPI regression + frontend + E2E suites remain green · D4 live smoke completed ·
  GA4 + Drive happy/error paths validated · chat stream/retry/cancel stable · Clear Data
  verified · no critical production issue for **14 consecutive days** · rollback runbook
  tested · any needed user-data/session migration documented. Only then is Streamlit
  archived with a fold-in note — two active UIs must never become permanent competing
  products.
- **Credential hygiene:** `check_credentials.py` enforced in CI; no live credentials in
  repo/history/captures; Workload Identity Federation / managed identities + Secret Manager.
- **§17 deferred gates** (product-mode decision + the five checkboxes) close or get explicitly
  scheduled before any hosted beta/public demo — never Phase-1-blocking.

## Exit criteria

- [ ] Single-origin deployment live on Cloud Run; `/healthz` + SPA route + SSE verified behind
      the proxy; `/assets/*` returns 200 with immutable cache headers.
- [ ] One Uvicorn worker per container; multi-instance only with Redis-backed sessions/locks.
- [ ] Feature parity complete; Streamlit retired; whisperer-30 archived.
- [ ] Three release gates green at the overall DoD level (master-plan §14).
- [ ] §17 deferred gates either closed or explicitly scheduled.

## Gate table — Phase 6 gate (overall migration DoD)

| Gate | Evidence | Owner | How to close |
|---|---|---|---|
| Phase 6 — cutover | Cloud Run deploy checklist green · parity list green · rollback drill documented · CI gates green | You + implementation agent | Record evidence; flip `specs/README.md` all DONE; master-plan §14 DoD complete; update repo docs (README/ARCHITECTURE/CHANGELOG/RELEASE_CHECKLIST) |
| §17 deferred gates | Product-mode decision + the five checkboxes | You (product owner) | Expand the §17 section when the hosted-beta decision is made |

## Parked/absorbed content

- **master-plan §17** operational readiness (product modes, 5 deferred checkboxes, security
  posture, out-of-scope list) — reproduced in full when this phase activates.
- `../policies/dockerfile-pattern.md` — the concrete build/runtime pattern Task 2 executes.
- **OAuth code-exchange sketch (Phase 5 detail, parked):** redirect first, then set the cookie
  on **that same `RedirectResponse` object** — never a separate response — so the session
  cookie survives the 303.

## Appendix — Redlock reference (do NOT implement for this app)

A single Redis/Memorystore endpoint is the correct scope for per-session AI serialization:
`SET key token NX PX ttl` + Lua ownership-verified release (Task 6). Redlock becomes relevant
only if ALL of these hold: you operate **≥3 independent Redis masters** that fail
independently (replicas/cluster shards are not enough); you need lock availability through a
master failure; your workload tolerates lease-based semantics; and you measure clock drift,
network latency, and acquisition timing. None apply to this app — keep the following as
reference material only.

```python
# api/services/redlock.py — REFERENCE ONLY (not a Phase 6 deliverable)
from __future__ import annotations
import asyncio, secrets, time
from dataclasses import dataclass
from redis.asyncio import Redis
from redis.exceptions import RedisError

RELEASE_LOCK_LUA = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0
"""

@dataclass(frozen=True)
class RedlockLease:
    key: str
    token: str
    validity_ms: int
    acquired_nodes: tuple[Redis, ...]

class RedlockAcquireError(Exception):
    pass

class AsyncRedlock:
    """Requires an odd number of >= 3 independent Redis masters."""
    def __init__(self, clients, *, drift_factor=0.01, drift_constant_ms=2,
                 per_node_timeout_ms=100):
        if len(clients) < 3 or len(clients) % 2 == 0:
            raise ValueError("Redlock requires an odd number of at least 3 Redis masters.")
        self.clients = clients
        self.quorum = len(clients) // 2 + 1
        self.drift_factor = drift_factor
        self.drift_constant_ms = drift_constant_ms
        self.per_node_timeout_ms = per_node_timeout_ms

    async def acquire(self, key, *, lease_ms):
        token = secrets.token_urlsafe(32)
        started_ms = time.monotonic_ns() // 1_000_000

        async def acquire_one(client):
            try:
                ok = await asyncio.wait_for(
                    client.set(key, token, nx=True, px=lease_ms),
                    timeout=self.per_node_timeout_ms / 1000)
                return client, bool(ok)
            except (RedisError, asyncio.TimeoutError):
                return client, False

        results = await asyncio.gather(*(acquire_one(c) for c in self.clients))
        acquired_nodes = tuple(c for c, ok in results if ok)
        elapsed_ms = (time.monotonic_ns() // 1_000_000) - started_ms
        validity_ms = lease_ms - elapsed_ms - int(lease_ms * self.drift_factor) - self.drift_constant_ms

        if len(acquired_nodes) >= self.quorum and validity_ms > 0:
            return RedlockLease(key, token, validity_ms, acquired_nodes)

        await self.release_partial(key=key, token=token, clients=acquired_nodes)
        raise RedlockAcquireError()

    async def release(self, lease):
        await self.release_partial(key=lease.key, token=lease.token, clients=self.clients)

    async def release_partial(self, *, key, token, clients):
        async def release_one(client):
            try:
                await client.eval(RELEASE_LOCK_LUA, 1, key, token)
            except RedisError:
                pass
        await asyncio.gather(*(release_one(c) for c in clients), return_exceptions=True)
```

Use it only with an explicit valid-lease deadline (e.g. reject leases whose validity has
shrunk below the stream deadline). Do not hold a Redlock lease across unbounded work; if exact
correctness matters more than retryable mutual exclusion (payments, irreversible writes,
exclusive migration), use a transactional database lock plus fencing/version tokens instead.
