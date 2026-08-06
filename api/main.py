"""FastAPI application entrypoint (Phase 1 — no SPA fallback yet; Phase 6)."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.config import get_settings
from api.routes import health, upload

settings = get_settings()
app = FastAPI(title="Insights Explorer API", version="0.4.0")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Preserve dependency-set cookies (e.g. a fresh session cookie) across
    HTTPException responses — the default handler drops them."""
    headers: dict[str, str] = {}
    pending = getattr(request.state, "pending_session_cookie", None)
    if pending:
        headers["set-cookie"] = pending
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=headers
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.include_router(health.router)
app.include_router(upload.router)
