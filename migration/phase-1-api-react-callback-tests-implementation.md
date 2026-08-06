# Phase 1 Implementation Packet
## FastAPI endpoints, React GA4 callback, and mock-to-API test updates

**Status:** Prepared implementation blueprint — no repository files have been changed.

This packet implements the first vertical slice only: **upload a CSV/XLSX → create a server session → receive a serialized data context → render it in React**. It also includes the GA4 OAuth callback route and the testing approach needed when `mock-ga4.ts`/`mock-braintree.ts` are removed.

> Important: keep all actual GA4, Drive, Gemini, and data-processing logic in Python. The FastAPI layer is an adapter around existing `utils/`; React is never allowed to receive provider credentials or access tokens.

---

## Canonical API Decisions (2026-08-05 — master-plan revision)

Single source of truth for implementation-facing documents. Anything below that conflicts with earlier text in this document is **superseded** (old paths are marked, not left active):

| Decision | Value |
|---|---|
| API prefix | `/api/v1` (all routes versioned) |
| Health endpoint | `GET /healthz` |
| Upload response | `{ dataset: ... }` (with `{ dataset, rows }` where specified) |
| Auth/session transport | HttpOnly secure session cookie + `credentials: "include"` |
| API naming | snake_case at the boundary |
| React mapping | `api.ts` performs snake_case → camelCase normalization — never individual components |
| Chat transport | [explicit chosen format — default: plain SSE `text/event-stream`, `data: <chunk>\n\n`] |
| Upload policy | Browser cap **25 MB** (`MAX_BROWSER_UPLOAD_BYTES` — margin below Cloud Run's 32 MiB HTTP/1 boundary); server-side/Drive **100 MB** (`MAX_INGEST_BYTES`, subject to memory/MIME/row-count/decompression safeguards) |

Superseded here: all bare `/api/...` paths (now `/api/v1/...`) and any earlier 32 MB upload default. See `master-plan.md` §4–5 and archive §4.12–4.13.

**F4-specific supersession:** §7 `max_upload_bytes = 25 MB` is retained as the browser cap (`MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024`); `MAX_INGEST_BYTES = 100 * 1024 * 1024` applies to server-side/Drive with safeguards; §1 layout gains `api/stores/` (SessionStore/DatasetStore interfaces); the in-memory session in §4 is dev-only — a **shared ephemeral OAuth/session store is proven before Phase 5**; object storage only if the signed-upload architecture is chosen (state placement, archive §4.13–4.14).

## 1. Target layout

```text
insights-explorer/
  api/
    __init__.py
    main.py
    config.py
    dependencies.py
    schemas.py
    services/
      __init__.py
      dataset_service.py
      ga4_service.py
    routes/
      __init__.py
      health.py
      upload.py
      ga4.py
  frontend/
    src/
      lib/
        api.ts
        api-types.ts
        explorer-store.tsx
      routes/
        auth/
          ga4/
            callback.tsx
      test/
        server.ts
        handlers.ts
        render.tsx
```

Keep the current Streamlit UI alive while this new vertical slice is introduced. It should call the same Python services temporarily, but should not call FastAPI from inside Streamlit.

---

## 2. Python dependencies

Add these to `requirements.txt` or a new `requirements/api.txt`:

```txt
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
python-multipart>=0.0.9,<1
pydantic-settings>=2.0,<3
itsdangerous>=2.2,<3
```

Do **not** add a database or Redis in Phase 1. Use an in-memory server-side session store only for local development and a single-instance staging deploy. Make the storage implementation swappable before production.

---

## 3. FastAPI configuration

### `api/config.py`

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_cors_origins: str = "http://localhost:5173"
    api_session_secret: str
    frontend_url: str = "http://localhost:5173"
    max_upload_bytes: int = 25 * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.api_cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Add, but do not commit, these `.env` values:

```dotenv
API_SESSION_SECRET=replace-with-a-long-random-value
API_CORS_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
MAX_UPLOAD_BYTES=26214400
```

Update `.env.example` with variable names and safe placeholders only. Continue using `scripts/check_credentials.py` and pre-commit secret checks; add the new session secret to their allowed/required configuration if necessary.

---

## 4. Session dependency

### `api/dependencies.py`

```python
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4

from fastapi import Cookie, HTTPException, Response, status

SESSION_COOKIE = "insights_session"


@dataclass
class AppSession:
    dataset_id: str | None = None
    ga4_credentials: dict | None = None
    oauth_state: str | None = None
    metadata: dict = field(default_factory=dict)


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, AppSession] = {}
        self._lock = RLock()

    def create(self) -> tuple[str, AppSession]:
        session_id = uuid4().hex
        session = AppSession()
        with self._lock:
            self._sessions[session_id] = session
        return session_id, session

    def get(self, session_id: str) -> AppSession | None:
        with self._lock:
            return self._sessions.get(session_id)


sessions = InMemorySessionStore()


def get_or_create_session(
    response: Response,
    insights_session: str | None = Cookie(default=None),
) -> AppSession:
    session = sessions.get(insights_session) if insights_session else None
    if session:
        return session

    session_id, session = sessions.create()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=False,  # Set True in production HTTPS.
        samesite="lax",
        max_age=60 * 60 * 8,
        path="/",
    )
    return session


def require_dataset(session: AppSession = None) -> AppSession:
    if not session or not session.dataset_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active dataset. Upload a file or connect GA4 first.",
        )
    return session
```

**Production replacement:** Replace `InMemorySessionStore` with a server-side store (Redis or Postgres), retain only a signed opaque session ID in the `HttpOnly` cookie, set `secure=True`, set a real cookie domain if needed, and use a narrow CORS allowlist.

---

## 5. API schemas

### `api/schemas.py`

```python
from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start: date | None = None
    end: date | None = None


class Column(BaseModel):
    name: str
    type: Literal["date", "number", "string", "boolean", "unknown"]
    nullable: bool


class DatasetContext(BaseModel):
    source: Literal["upload", "ga4", "drive"]
    filename: str
    row_count: int = Field(ge=0)
    date_range: DateRange
    columns: list[Column]
    filters: list[dict] = Field(default_factory=list)
    metrics: list[dict] = Field(default_factory=list)
    provenance: dict = Field(default_factory=dict)


class UploadResponse(BaseModel):
    dataset: DatasetContext


class GA4ConnectResponse(BaseModel):
    authorization_url: str


class APIError(BaseModel):
    detail: str
```

Use snake_case internally in FastAPI first. If the React store is already camelCase-heavy, configure Pydantic aliases at the API boundary rather than creating two parallel schemas.

---

## 6. Dataset-service adapter

### `api/services/dataset_service.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

import pandas as pd

from api.schemas import Column, DatasetContext, DateRange


@dataclass
class StoredDataset:
    id: str
    dataframe: pd.DataFrame
    context: DatasetContext


class DatasetStore:
    def __init__(self) -> None:
        self._items: dict[str, StoredDataset] = {}

    def put(self, dataframe: pd.DataFrame, context: DatasetContext) -> StoredDataset:
        item = StoredDataset(id=uuid4().hex, dataframe=dataframe, context=context)
        self._items[item.id] = item
        return item

    def get(self, dataset_id: str) -> StoredDataset | None:
        return self._items.get(dataset_id)


datasets = DatasetStore()


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    return "string"


def make_context(df: pd.DataFrame, *, source: str, filename: str) -> DatasetContext:
    date_columns = [column for column in df.columns if pd.api.types.is_datetime64_any_dtype(df[column])]
    start = end = None
    if date_columns:
        values = df[date_columns[0]].dropna()
        if not values.empty:
            start = values.min().date()
            end = values.max().date()

    return DatasetContext(
        source=source,
        filename=filename,
        row_count=len(df),
        date_range=DateRange(start=start, end=end),
        columns=[
            Column(
                name=str(column),
                type=infer_column_type(df[column]),
                nullable=bool(df[column].isna().any()),
            )
            for column in df.columns
        ],
        provenance={
            "created_at": datetime.now(timezone.utc).isoformat(),
            "transformations": [],
        },
    )


def parse_uploaded_file(filename: str, content: bytes) -> pd.DataFrame:
    """Adapter boundary.

    Replace the pandas parsing branch with the existing vetted loader in
    utils/data_loader.py once its Streamlit cache/UI coupling is extracted.
    Do not duplicate validation, supported-file, or error-taxonomy logic.
    """
    suffix = Path(filename).suffix.lower()
    with NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        if suffix == ".csv":
            return pd.read_csv(tmp.name)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(tmp.name)
    raise ValueError("Supported formats are CSV, XLSX, and XLS.")
```

**Adapter rule:** once `utils/data_loader.py` exposes a pure `load_file(path_or_bytes)` function, replace `parse_uploaded_file()` rather than maintaining two parsers. The same rule applies to `utils/data_context.py`: prefer its established filter/metric/provenance rules over this initial serializer.

---

## 7. Upload and preview routes

### `api/routes/upload.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from api.config import get_settings
from api.dependencies import AppSession, get_or_create_session
from api.schemas import DatasetContext, UploadResponse
from api.services.dataset_service import datasets, make_context, parse_uploaded_file

router = APIRouter(prefix="/api", tags=["data"])

ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    response: Response,
    file: UploadFile = File(...),
    session: AppSession = Depends(get_or_create_session),
) -> UploadResponse:
    settings = get_settings()
    filename = file.filename or "upload"
    suffix = f".{filename.rsplit('.', 1)[-1].lower()}" if "." in filename else ""
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload a CSV, XLSX, or XLS file.")

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit.")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        dataframe = parse_uploaded_file(filename, content)
        context = make_context(dataframe, source="upload", filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Log exception metadata server-side; never echo file contents or secrets.
        raise HTTPException(status_code=422, detail="Unable to parse this file.") from exc

    stored = datasets.put(dataframe, context)
    session.dataset_id = stored.id
    return UploadResponse(dataset=stored.context)


@router.get("/data/context", response_model=DatasetContext)
def get_data_context(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> DatasetContext:
    if not session.dataset_id:
        raise HTTPException(status_code=409, detail="No active dataset.")
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")
    return dataset.context


@router.get("/data/preview")
def get_data_preview(
    response: Response,
    limit: int = 10,
    session: AppSession = Depends(get_or_create_session),
) -> dict:
    if not session.dataset_id:
        raise HTTPException(status_code=409, detail="No active dataset.")
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")

    safe_limit = min(max(limit, 1), 100)
    frame = dataset.dataframe.head(safe_limit).where(dataset.dataframe.notna(), None)
    return {
        "dataset": dataset.context.model_dump(mode="json"),
        "rows": frame.to_dict(orient="records"),
    }
```

### `api/routes/health.py`

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

---

## 8. GA4 OAuth endpoints

### `api/services/ga4_service.py`

```python
from __future__ import annotations

import secrets
from urllib.parse import urlencode

from api.config import get_settings


def begin_oauth() -> tuple[str, str]:
    """Adapter boundary for utils/ga4_client.py.

    Replace URL construction with the existing GA4 OAuth client as soon as it
    exposes a framework-neutral authorization-url function.
    """
    settings = get_settings()
    state = secrets.token_urlsafe(32)
    callback_url = f"{settings.frontend_url.rstrip('/')}/auth/ga4/callback"

    # Placeholder: use only the provider library already used by ga4_client.py.
    # Do not hand-roll token exchange or duplicate the project's OAuth scopes.
    params = {
        "client_id": "READ_FROM_EXISTING_GA4_CONFIG",
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/analytics.readonly",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return state, "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def exchange_code(code: str) -> dict:
    """Call the existing ga4_client token-exchange implementation here.

    Do not put client secrets in React, query strings, error messages, or logs.
    """
    raise NotImplementedError("Wire this adapter to utils.ga4_client.")
```

### `api/routes/ga4.py`

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse

from api.config import get_settings
from api.dependencies import AppSession, get_or_create_session
from api.schemas import GA4ConnectResponse
from api.services.ga4_service import begin_oauth, exchange_code

router = APIRouter(prefix="/api/v1/ga4", tags=["GA4"])


@router.post("/connect", response_model=GA4ConnectResponse)
def connect_ga4(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> GA4ConnectResponse:
    state, authorization_url = begin_oauth()
    session.oauth_state = state
    return GA4ConnectResponse(authorization_url=authorization_url)


@router.get("/callback")
def ga4_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    response: Response = None,
    session: AppSession = Depends(get_or_create_session),
):
    settings = get_settings()
    callback = f"{settings.frontend_url.rstrip('/')}/auth/ga4/callback"

    if error:
        # User cancelled at Google — canonical status (2026-08-06)
        return RedirectResponse(f"{callback}?status=cancelled")
    if not code or not state or not secrets.compare_digest(state, session.oauth_state or ""):
        return RedirectResponse(f"{callback}?status=error&reason=invalid_state")

    try:
        session.ga4_credentials = exchange_code(code)
        session.oauth_state = None
        return RedirectResponse(f"{callback}?status=success")
    except Exception:
        # Record sanitized diagnostic server-side.
        return RedirectResponse(f"{callback}?status=error&reason=token_exchange_failed")
```

**Correction before implementation:** The OAuth `redirect_uri` must point to the **FastAPI callback** (`https://api.example.com/api/v1/ga4/callback`), not React. Google redirects to FastAPI; FastAPI validates `state`, exchanges the code, sets server session state, and then redirects the browser to React at `/auth/ga4/callback?status=success`. Replace the placeholder callback URL in `begin_oauth()` accordingly.

---

## 9. FastAPI application entry point

### `api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import ga4, health, upload

settings = get_settings()
app = FastAPI(title="Insights Explorer API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(ga4.router)
```

Add `api/routes/__init__.py` and `api/services/__init__.py` as empty files.

Run locally:

```bash
uvicorn api.main:app --reload --port 8000
```

Expected checks:

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

---

## 10. React API client

### `frontend/src/lib/api-types.ts`

```ts
export type SourceKind = "upload" | "ga4" | "drive";

export interface DateRange {
  start: string | null;
  end: string | null;
}

export interface Column {
  name: string;
  type: "date" | "number" | "string" | "boolean" | "unknown";
  nullable: boolean;
}

export interface DataContext {
  source: SourceKind;
  filename: string;
  row_count: number;
  date_range: DateRange;
  columns: Column[];
  filters: Record<string, unknown>[];
  metrics: Record<string, unknown>[];
  provenance: Record<string, unknown>;
}

export interface UploadResponse {
  dataset: DataContext;
}

export interface DataPreviewResponse {
  dataset: DataContext;
  rows: Record<string, unknown>[];
}

export interface ApiError {
  detail: string;
}
```

### `frontend/src/lib/api.ts`

```ts
import type { DataContext, DataPreviewResponse, UploadResponse } from "./api-types";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api";

async function assertOk(response: Response): Promise<Response> {
  if (response.ok) return response;
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  throw new Error(body?.detail ?? `Request failed (${response.status})`);
}

export async function uploadDataset(file: File): Promise<DataContext> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await assertOk(
    await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
      credentials: "include",
    }),
  );
  const payload = (await response.json()) as UploadResponse;
  return payload.dataset;
}

export async function fetchPreview(): Promise<DataPreviewResponse> {
  const response = await assertOk(
    await fetch(`${API_BASE}/data/preview`, { credentials: "include" }),
  );
  return response.json() as Promise<DataPreviewResponse>;
}

export async function beginGa4OAuth(): Promise<void> {
  const response = await assertOk(
    await fetch(`${API_BASE}/ga4/connect`, {
      method: "POST",
      credentials: "include",
    }),
  );
  const { authorization_url } = (await response.json()) as { authorization_url: string };
  window.location.assign(authorization_url);
}
```

Always send `credentials: "include"`; otherwise the browser will not return the session cookie needed to correlate upload, OAuth, and analysis requests.

---

## 11. React OAuth callback route

Create the route matching the TanStack file-routing convention already used by the app.

### `frontend/src/routes/auth/ga4/callback.tsx`

```tsx
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AlertCircle, CheckCircle2, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { fetchPreview } from "@/lib/api";
import { useExplorer } from "@/lib/explorer-store";

export const Route = createFileRoute("/auth/ga4/callback")({
  component: Ga4CallbackPage,
});

type CallbackState = "loading" | "success" | "error";

// Canonical callback statuses (2026-08-06): status=success · status=cancelled (no reason) ·
// status=error&reason=<safe_code> (invalid_state | token_exchange_failed | ...).
// "provider_denied" / "invalid_oauth_state" are superseded spellings.

function readableReason(reason: string | undefined): string {
  switch (reason) {
    case "cancelled":
      return "Google authorization was cancelled. No data was connected.";
    case "invalid_state":
      return "The authorization session expired or could not be verified. Please try again.";
    case "token_exchange_failed":
      return "Google authorization completed, but Insights Explorer could not establish a GA4 session.";
    default:
      return "We could not connect Google Analytics. Please try again.";
  }
}

function Ga4CallbackPage() {
  const navigate = useNavigate();
  const { setSourceFromApi, setLoadState, setError } = useExplorer();
  const search = new URLSearchParams(window.location.search);
  const status = search.get("status");
  const reason = search.get("reason") ?? undefined;
  const [state, setState] = useState<CallbackState>(status === "success" ? "loading" : "error");

  useEffect(() => {
    if (status !== "success") {
      setError(readableReason(reason));
      setLoadState("error");
      return;
    }

    let cancelled = false;
    async function finishConnection() {
      try {
        setLoadState("loading");
        const preview = await fetchPreview();
        if (cancelled) return;
        setSourceFromApi(preview.dataset);
        setLoadState("ready");
        setState("success");
        window.setTimeout(() => navigate({ to: "/" }), 700);
      } catch (error) {
        if (cancelled) return;
        const message = error instanceof Error ? error.message : "Unable to load the GA4 dataset.";
        setError(message);
        setLoadState("error");
        setState("error");
      }
    }
    void finishConnection();
    return () => {
      cancelled = true;
    };
  }, [navigate, reason, setError, setLoadState, setSourceFromApi, status]);

  const isSuccess = state === "success";
  const isLoading = state === "loading";

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <section className="w-full max-w-md rounded-md border border-border bg-card p-6" aria-live="polite">
        {isLoading ? <LoaderCircle className="mb-4 size-6 animate-spin text-primary" aria-hidden /> : null}
        {isSuccess ? <CheckCircle2 className="mb-4 size-6 text-emerald-500" aria-hidden /> : null}
        {state === "error" ? <AlertCircle className="mb-4 size-6 text-destructive" aria-hidden /> : null}
        <h1 className="text-lg font-semibold">
          {isLoading ? "Connecting Google Analytics…" : isSuccess ? "Google Analytics connected" : "Connection unsuccessful"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {isLoading
            ? "Loading your selected analytics data."
            : isSuccess
              ? "Returning you to Insights Explorer."
              : readableReason(reason)}
        </p>
        {state === "error" ? (
          <button className="mt-5 rounded-sm bg-primary px-3 py-2 text-sm text-primary-foreground" onClick={() => navigate({ to: "/" })}>
            Return to explorer
          </button>
        ) : null}
      </section>
    </main>
  );
}
```

### Required store addition

The route requires a non-UI setter so it does not recreate upload logic:

```ts
setSourceFromApi: (dataset: DataContext) => void;
```

Its implementation should normalize Python snake_case fields at **one** boundary, then set existing store state. Do not scatter `row_count` → `rowCount` conversions across components.

---

## 12. Test updates: replace mock-module tests

### Testing principle

Do not replace `mock-ga4.ts` with a production fixture that components import. Instead:

- **Unit tests:** Mock the network boundary with MSW.
- **Store tests:** Test loading, ready, error, and streaming behavior against MSW responses.
- **Component tests:** Render real provider + MSW; assert user-visible state.
- **E2E:** Use Playwright against FastAPI staging/local test mode for upload and OAuth error/success paths.

This keeps test data out of production code and prevents components from knowing whether data is mock or live.

### Add dependencies in `frontend/package.json`

```json
{
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.6.1",
    "jsdom": "^25.0.0",
    "msw": "^2.4.0",
    "vitest": "^2.1.0"
  },
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

### `frontend/src/test/handlers.ts`

```ts
import { http, HttpResponse } from "msw";
import { API_BASE } from "@/lib/api";

export const uploadedDataset = {
  source: "upload",
  filename: "analytics.csv",
  row_count: 3,
  date_range: { start: "2026-01-01", end: "2026-01-03" },
  columns: [
    { name: "date", type: "date", nullable: false },
    { name: "sessions", type: "number", nullable: false },
  ],
  filters: [],
  metrics: [],
  provenance: { created_at: "2026-08-05T00:00:00Z", transformations: [] },
};

export const handlers = [
  http.post(`${API_BASE}/upload`, async () => HttpResponse.json({ dataset: uploadedDataset }, { status: 201 })),
  http.get(`${API_BASE}/data/preview`, () =>
    HttpResponse.json({
      dataset: uploadedDataset,
      rows: [
        { date: "2026-01-01", sessions: 30 },
        { date: "2026-01-02", sessions: 50 },
      ],
    }),
  ),
  http.post(`${API_BASE}/ga4/connect`, () =>
    HttpResponse.json({ authorization_url: "https://accounts.google.com/test-oauth" }),
  ),
];
```

### `frontend/src/test/server.ts`

```ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

### `frontend/src/test/setup.ts`

```ts
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Upload/store behavior test

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ExplorerProvider, useExplorer } from "@/lib/explorer-store";

function TestHarness() {
  const { loadData, loadState, source, error } = useExplorer();
  return (
    <>
      <input
        aria-label="Upload data"
        type="file"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0];
          if (file) void loadData(file, "upload");
        }}
      />
      <output data-testid="status">{loadState}</output>
      <output data-testid="filename">{source?.filename ?? ""}</output>
      <output data-testid="error">{error ?? ""}</output>
    </>
  );
}

describe("ExplorerProvider", () => {
  it("uploads a file and exposes the server dataset to consumers", async () => {
    const user = userEvent.setup();
    render(
      <ExplorerProvider>
        <TestHarness />
      </ExplorerProvider>,
    );

    await user.upload(
      screen.getByLabelText("Upload data"),
      new File(["date,sessions\n2026-01-01,30"], "analytics.csv", { type: "text/csv" }),
    );

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("ready"));
    expect(screen.getByTestId("filename")).toHaveTextContent("analytics.csv");
    expect(screen.getByTestId("error")).toHaveTextContent("");
  });
});
```

### Error-state test

```tsx
import { http, HttpResponse } from "msw";
import { server } from "@/test/server";
import { API_BASE } from "@/lib/api";

it("surfaces upload errors instead of silently retaining mock data", async () => {
  server.use(
    http.post(`${API_BASE}/upload`, () => HttpResponse.json({ detail: "Uploaded file is empty." }, { status: 400 })),
  );

  // Render the same harness, upload an empty file, then assert:
  // loadState === "error" and error includes "Uploaded file is empty."
});
```

### OAuth callback tests

Test three cases by setting the route search string and mocking `GET /data/preview`:

1. `?status=success`: calls preview, writes dataset to store, navigates home.
2. `?status=cancelled`: shows cancellation explanation and return button.
3. `?status=success` + preview failure: shows API error and does not navigate.

### Delete/update tests that do this

```ts
vi.mock("@/lib/mock-ga4", () => ({ defaultSource: ... }));
```

Replace with MSW response overrides. Delete `mock-ga4.ts` and `mock-braintree.ts` only after all direct imports are removed; during the transition, move test fixtures into `src/test/fixtures/`, not `src/lib/`.

---

## 13. Definition of done for this slice

- [ ] `GET /healthz` returns `{"status":"ok"}`.
- [ ] React upload sends multipart data to FastAPI with credentials included.
- [ ] FastAPI returns a validated dataset context and persists it in the current server session.
- [ ] React store transitions `idle → loading → ready`; failed upload transitions to `error` with a visible message.
- [ ] Existing UI components consume the existing `useExplorer()` API; they do not import mock data.
- [ ] `mock-ga4.ts` and `mock-braintree.ts` have no production imports.
- [ ] OAuth callback validates state server-side, performs token exchange server-side, and never exposes a provider token to React.
- [ ] Unit/component tests use MSW; no test depends on live GA4, Drive, Gemini, or Lovable.
- [ ] `pytest`, React unit tests, TypeScript build, and the existing smoke-test suite pass before the next endpoint family is added.

---

## Do not do in Phase 1

- Do not implement Drive Picker, Gemini chat streaming, forecasting, funnels, or exports yet.
- Do not move secrets into `VITE_*` variables; Vite exposes these to the browser.
- Do not redirect Google OAuth directly to React.
- Do not deploy FastAPI and React on separate production origins unless there is a clear need; same-origin deployment avoids fragile cross-site cookie behavior.
- Do not delete Streamlit or archive the Lovable repo until feature parity and regression coverage exist.
---

## Research Addendum (2026-08-05)

Source-backed notes — full citations in `insights-explorer-migration-ingest.md` Part 3:

1. **PKCE.** RFC 9700 / OAuth 2.1 recommend PKCE for all client types, including confidential web apps. Add an S256 `code_verifier` / `code_challenge` to `begin_oauth()` and exchange it in `exchange_code()`. Keep the existing `state` + `compare_digest` validation (correct per Google's guidance).
2. **redirect_uri.** Google requires an exact string match against the configured URI — keep `callback_url` construction consistent between `config.py` (`FRONTEND_URL`) and the OAuth adapter.
3. **Drive Picker (Phase 5 forward).** `POST /api/v1/drive/picker-token` should return the token **and** the project number (`setAppId`); the project number may require enabling the Cloud Resource Manager API. The developer API key should be HTTP-referrer restricted.
4. **GA4 funnel nuance.** The Data API has `runFunnelReport` (Funnel quota category) — template funnels may be implementable without event-level export; user-level analyses remain blocked. Revisit the roadmap's funnel rows at implementation time.
5. **Session cookie.** `secure=False` is flagged for production — set `secure=True` behind HTTPS; consider a `__Host-` cookie prefix on the production origin.
6. **SSE wire format.** Decide plain SSE (`text/event-stream`, `data: ...\n\n`) vs the Vercel AI SDK data-stream up front, and make the React reader (F3 §6) match.
---

## Reconciliation Addendum (2026-08-05)

Cross-checked against the plan doc, the store prompt, and the repo (full ledger: `insights-explorer-migration-ingest.md` Part 4). This packet's choices are confirmed as **canonical** where the other docs conflict:

1. **`GET /healthz` is canonical.** The plan doc and draft GitHub issue say `GET /health` — apply `/healthz` when creating issues and the smoke script.
2. **Response shapes are canonical:** `UploadResponse { dataset }`, `DataPreviewResponse { dataset, rows }`, `GA4ConnectResponse { authorization_url }`. The plan's bare/camelCase forms and the store prompt's `authUrl` reads are superseded.
3. **`GET /api/v1/data/context`** is an addition beyond the plan's endpoint table — keep it; it's the clean session-restore endpoint for the store.
4. **Casing rule stands:** snake_case at the API boundary, camelCase in store state, normalized once in `setSourceFromApi`. Pydantic aliases only if the store insists on camelCase at the wire.
5. **OAuth design stands:** Google → FastAPI callback → React with `status`/`reason` only. The `begin_oauth()` placeholder callback URL still points at React (`frontend_url` + `/auth/ga4/callback`); the inline "Correction before implementation" note already overrides it — make the FastAPI callback URL (`/api/v1/ga4/callback`) the value used in code.
6. **Repo facts confirmed:** 8,461 LOC, 742 unit + 32 smoke tests, 7/16 utils Streamlit coupling, `ga4-measurement-contract.md` exists.
7. **Deferred work confirmed out of scope** per §13 ("Do not do in Phase 1"): Drive, Gemini streaming, forecasting, funnels, exports.
---

## Batch 3 Addendum (2026-08-05)

> Source: PASTE 11 of the ingest archive (§1.13 synthesis, §2.15 verbatim, §4.6 verification). Refines the Phase 1 implementation packet.

1. **Server-owned session model (adopt explicitly).** The packet's in-memory session placeholder becomes the documented model: the browser holds only an opaque `HttpOnly` secure cookie; the server owns the dataset reference, OAuth credentials, filter/metric/chat state. Implement the storage abstraction now — name the interface (in-memory for dev; Redis/Postgres-compatible for deployed multi-instance) rather than committing to the bare dict.
2. **API versioning.** Prefix routes as `/api/v1/...` (health may stay `/healthz`). This lets the evidence connector and future breaking changes evolve without a v2 scramble.
3. **Typed client contract.** Python domain models stay canonical and FastAPI serializes at the boundary (already the design). Add: generate or validate the React client against the OpenAPI schema so `api-types.ts` never drifts from the server.
4. **Test-by-behavior mapping.** Map the packet's test strategy onto the four-layer matrix — Python unit · FastAPI contract · React unit/component · Playwright E2E. MSW for frontend tests; mock modules become test fixtures only.
5. **Pre-copy security gate (Phase 0 of this packet, before any code copy).** The whisperer-30 `.env` is **verified tracked** (62 B, commit `9059739`, no `.env.example`, no gitignore rule) — inspect history, rotate/revoke any real credentials, remove from index, add a safe `.env.example` before the React app enters this repo.
6. **Phase 1 scope confirmed.** Upload CSV → validate → server session → React preview/quality → clear-data → regression tests, exactly as the packet's "Do not do in Phase 1" boundary implies. GA4 → Drive → AI streaming → advanced analysis come later, in order.
---

## Research Fold-In Cross-Check Addendum (2026-08-05)

Cross-checks the 7 research corrections from the plan's Research Fold-In Log against **this implementation packet** (source: `insights-explorer-migration-ingest.md` Part 3 §3.8). Two real drift items were found and are fixed here; the rest confirm existing notes.

1. **PKCE is missing from the §8 code sketch (correction 1).** The Research Addendum item 1 states the requirement, but `begin_oauth()` builds params without `code_challenge`. Update the sketch: generate an S256 `code_verifier`/`code_challenge` before building params, add `"code_challenge": challenge, "code_challenge_method": "S256"`, store `code_verifier` on the session (`AppSession.code_verifier: str | None`, §4), and send it in `exchange_code()`. Keep the existing `state` + `secrets.compare_digest` validation.
2. **Callback route should use typed search params (correction 6).** §11's `callback.tsx` reads `new URLSearchParams(window.location.search)`. Replace with TanStack Router typed search params: a `validateSearch` schema for `status`/`reason`, read via `Route.useSearch()`. On validation failure the router sets `error.routerCode === "VALIDATE_SEARCH"` and renders the route's `errorComponent` — use that as the invalid-state path instead of manual string parsing. Live-verified: `@tanstack/react-router@1.170.20` (archive §3.6).
3. **MSW setup is live-verified — keep as-is (no change).** §12's `setup.ts` already sets `onUnhandledRequest: "error"` explicitly. That is correct and now source-backed: `msw@2.15.0`'s default is `"warn"` — not `"bypass"` as an earlier research pass claimed — so the explicit `"error"` is a deliberate choice. Do not remove it.
4. **Picker project number (correction 2).** Phase 5 forward — this packet's Phase 1 scope defers Drive (see "Do not do in Phase 1"). Recorded so the Phase 5 packet returns `{ token, appId }` from `POST /api/v1/drive/picker-token` (see the F3 cross-check addendum item 1).
5. **Single-origin hosting (correction 5).** §13's same-origin rule and Research Addendum item 5 already align; the concrete multi-stage Dockerfile pattern is in `migration/dockerfile-pattern.md`.
6. **No Phase 1 code change for corrections 3, 4, 7.** Chat wire format (3), funnel nuance (4), and GA4 pull pagination/throttling (7) all live in later phases; the plan amendments (Phases 1/3/5) carry the decisions. Funnel note: scope template funnels only when `GET /api/v1/analysis/funnel` is implemented.
---

## Round 2 Research Addendum (2026-08-05)

> Source: archive §3.9 (live-verified round-2 research).

1. **GA4 client names (for the §8 adapter boundary).** Python package `google-analytics-data` → `from google.analytics.data_v1beta import BetaAnalyticsDataClient`; core methods `run_report`, `batch_run_reports`, `run_funnel_report`. Use these when wiring `utils/ga4_client.py` (and the Phase-5 `POST /api/v1/ga4/pull` adapter) instead of inventing new names.
2. **GA4 pagination + quotas (live numbers for the Phase-5-forward pull).** `limit`/`offset` paging; default limit 10,000, max 250,000 rows/request; **Core Concurrent Requests Per Property = 10** (Standard) / 50 (360); token budgets 200k/day + 40k/hr per property; 120 thresholded-requests/hr cap; `returnPropertyQuota: true` for observability; `runFunnelReport` consumes a separate **Funnel** quota. *(§3.9 items 1–2, 6.)*
3. **Gemini SDK.** Use `google-genai` — `client.models.generate_content_stream(...)` for `/api/v1/chat` and summary; map `thoughts_token_count` into the server usage ledger. *(§3.9 item 4.)*
4. **AI SDK pin.** The whisperer frontend pins `ai@^7.0.48` — the Phase 1 wire-format decision (plain SSE vs SDK data-stream) must be validated against the v7 API surface. *(§3.9 item 3.)*
---

## Round 3 Research Addendum (2026-08-05)

> Source: archive §3.10 (live-verified round-3 research).

1. **MSW streaming test pattern (§3.10 item 4).** Add a chat handler returning `HttpResponse` with a `ReadableStream` body and `Content-Type: text/event-stream` (+ `Cache-Control: no-cache`). Node/undici may buffer unless the client consumes via `getReader()`; **jsdom has no real `EventSource`** — test the store's fetch+getReader path, not `EventSource`.
2. **Python 3.14 floors (§3.10 item 6).** `python:3.14-slim` is valid for the Phase 6 Dockerfile; **raise the repo's `pandas>=2.0.0` floor to `>=2.3.3`** (first cp314-wheel release) for reproducible builds; keep `pydantic>=2.12` (v1 is not 3.14-compatible); `google-analytics-data` (0.23.0) and `google-genai` support 3.14.
3. **GA4 client naming confirmed.** `google-analytics-data` → `BetaAnalyticsDataClient`; methods `run_report`, `batch_run_reports`, `run_funnel_report`; pagination `limit`/`offset` (default 10k, max 250k); Core concurrent = 10/property (50 for 360). *(§3.10 + round-2.)*
4. **`__Host-` cookie verified (§3.10 item 8).** FastAPI `Response.set_cookie` supports `__Host-` directly: `secure=True`, `path="/"`, and **omit `domain`** (required by the prefix spec).
---

## Reconciliation Addendum 2 (2026-08-05) — size policy + measurement-contract mapping

> Source: archive §4.11 (internal reconciliation batch). Apply at Phase 1 implementation.

1. **Single ingestion size policy.** Replace the standalone `max_upload_bytes = 25 MB` default with a shared **`MAX_INGEST_BYTES = 100 MB`** — matching `utils/drive_client.py:48` (`MAX_DRIVE_IMPORT_BYTES`) — env-overridable, applied to both `POST /api/v1/upload` and the Phase-5 `POST /api/v1/drive/download` (Drive downloads happen server-side, so their byte budget applies to parsed content, not the request body). Note platform caps when choosing hosts: Vercel functions ≈4.5 MB body (blocked — archive §3.11); Cloud Run configurable to ~128 MB. The current Streamlit upload path has no explicit guard — this constant becomes the canonical limit. **Superseded 2026-08-06:** the locked policy splits this — **browser uploads cap at 25 MB** (`MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024`), while the **100 MB `MAX_INGEST_BYTES` applies to Drive/server-side ingestion only** (subject to metadata/streaming/MIME/decompression/row/column/temp-file limits). See the Canonical API Decisions block above and `master-plan.md` §4–5.
2. **GA4 measurement-contract mapping.** F4's `DatasetContext` is a transport descriptor; `plans/ga4-measurement-contract.md` defines computed metrics (5 rows). Wire the mapping at Phase 5: `POST /api/v1/ga4/pull` returns a `DatasetContext` whose `metrics` entries carry contract provenance (`{"contract_row": "daily_reach", "validation_status": "provisional"}`), and add a future `GET /api/v1/ga4/metrics` (contract rows + status) per the contract's Next-steps item 4 (`ReportContract` objects). Rows 3–5 stay `unavailable` until event-level GA4 access exists (aggregate-only; funnel nuance per archive §3.4).
