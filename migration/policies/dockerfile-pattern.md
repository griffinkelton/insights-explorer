# Dockerfile Pattern — Single-Origin FastAPI + React (Phase 6 deliverable sketch)

**Date:** 2026-08-05
**Purpose:** concrete deliverable sketch for the Phase 6 hosting amendment (research correction 5): bundle the built React SPA into the FastAPI container so the product serves from **one origin**. Same-origin serving is what keeps the session-cookie / OAuth-callback / CORS / SSE model simple (Batch 3 + Research Addendum item 1).

> Applies to: Railway, Render (Docker-based Web Service — **not** the default split Static Site + Web Service), Fly.io. Streamlit Community Cloud cannot run this stack at all.

---

## 1. The pattern (two stages)

```dockerfile
# ---------- Stage 1: build the React frontend ----------
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend

# Dependencies first (layer caching)
COPY frontend/package.json frontend/bun.lock ./
# Bun is the whisperer-30 package manager; CI must support it.
# If npm is chosen instead (see plan "npm vs bun" decision), swap:
#   COPY frontend/package.json frontend/package-lock.json ./
#   RUN npm ci
RUN bun install --frozen-lockfile

COPY frontend/ ./
# VITE_API_BASE must be relative ("/api") so the SPA talks to the same origin.
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN bun run build

# ---------- Stage 2: Python API + static assets ----------
FROM python:3.14-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps FastAPI/uvicorn need (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY utils/ ./utils/
# Existing Streamlit assets needed only until cutover; drop this line after Phase 6.
COPY app.py ./

# The built SPA is served statically by FastAPI (no separate web server).
COPY --from=frontend-build /app/frontend/dist ./static

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4).status==200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**CI support for the frontend build stage:** GitHub Actions uses `oven-sh/setup-bun@v2` (auto-detects the `packageManager` field in `package.json`); Cloud Build installs bun via the official install script. So the npm-vs-bun choice (plan Phase 4) is unconstrained by CI. *(archive §3.9 item 5.)*

**Python 3.14 dependency floors (round-3, §3.10 item 6):** keep `pandas>=2.3.3` (first cp314-wheel release) and `pydantic>=2.12` (v1 is not 3.14-compatible) in `requirements`; `python:3.14-slim` itself is valid.

## 2. FastAPI side — serve the SPA at `/`

```python
# api/main.py — after the API routers are included
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Mount /assets (Vite output) first so hashed assets don't hit the SPA fallback
app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """Serve index.html for any non-API path (client-side routing)."""
    candidate = STATIC_DIR / full_path
    if full_path and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")
```

Rules that keep this correct:
- **API routes are registered before the SPA fallback**, and the fallback must never shadow `/api/*`, `/healthz`, or `/api/ga4/callback`. A guard `if full_path.startswith("api"): raise HTTPException(404)` is a cheap safety net.
- The **OAuth `redirect_uri` stays same-origin** (`https://<host>/api/ga4/callback`) — no cross-origin cookie or CORS concerns by construction.
- **No CORS needed in production** when everything is same-origin; keep the `api_cors_origins` allowlist for local dev (`http://localhost:5173`) only.
- **Session cookie:** set `secure=True` behind HTTPS; consider a `__Host-` prefix (Research Addendum item 5). `samesite="lax"` is correct for the OAuth redirect round-trip.

## 3. Why not the Render split (Static Site + Web Service)

Two origins ⇒ the browser must send `credentials: "include"` cross-origin, which requires: (a) a permissive CORS allowlist, (b) `SameSite=None; Secure` cookies, (c) consistent OAuth redirect configuration across two hostnames, and (d) SSE/CORS interplay on `/api/chat`. All of that disappears with one origin. Render can still host this — use a **Docker-based Web Service** running this image, not the Static Site + Web Service pair.

## 4. Deploy notes per platform

| Platform | How this image runs | Gotchas |
|---|---|---|
| Railway | Single service, Dockerfile at repo root | Set `VITE_API_BASE=/api`; attach the env vars from `.env.example` |
| Render | Web Service → Docker | Ignore the "Static Site" preset; one service, one origin |
| Fly.io | `fly deploy` with Dockerfile | Add `internal_port = 8000`; healthcheck already in image |
| GCP (Cloud Run) | docker build → Artifact Registry → `gcloud run deploy` (canonical shape: cloud.google.com/build/docs/deploying-builds/deploy-cloud-run) | Bind `$PORT` (8080); raise the request timeout for SSE (default 300s, max 3600s) or heartbeat; session affinity is best-effort — design chat reconnects; enable HTTP/2 (`h2c`); set the OAuth redirect to the explicit public HTTPS URL (Cloud Run proxies `X-Forwarded-Proto`). Round-3 verified (archive §3.10 item 3) |
| Vercel | Frontend-only option — **rejected** | SPA hosts fine, but the API cannot run on serverless functions (≈4.5 MB body cap vs the 100 MB ingestion policy; function duration vs SSE; stateless sessions). Split origins would break the single-origin cookie/OAuth model (archive §3.11) |

## 5. Verification checklist (Phase 6 DoD)

- [ ] `docker build` succeeds with `VITE_API_BASE=/api`.
- [ ] `GET /healthz` returns `{"status":"ok"}` inside the container.
- [ ] `GET /` returns the React app; a deep route (e.g. `/learn`) returns the SPA, not 404.
- [ ] `/api/*` never falls through to `index.html` (test with an unknown API path → 404).
- [ ] OAuth round-trip completes on the production origin with `secure=True` cookies.
- [ ] Chat SSE streams from the same origin (`/api/chat`).

---

*Sketch only — refine during Phase 6. Related: plan Phase 6 amendment + Research Fold-In Log item 5; archive §3.1.*
