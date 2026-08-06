# Phase 1 — Upload Vertical Slice (executable spec)

> 🔵 **ACTIVE** (2026-08-06) — Gate 7 open. Execute on branch **`feat/react-fastapi-migration`**. Local-first, single-user, in-memory stores.
> Source of the embedded code: F4 (`phase-1-api-react-callback-tests-implementation.md` — **superseded for execution**, retained as reference). Locked decisions: master-plan §5. Step 1 (environment guard) is the **first security task** of the migration.

## Tracks consumed

- **A. State/session:** server-owned session; browser holds only the opaque HttpOnly cookie — no dataset reference, raw data, or tokens in the browser
- **B. Contract:** `/api/v1` from day one; snake_case at the boundary; typed schemas (`{ dataset }`, `{ dataset, rows }`, `{ detail }`)
- **C. Tests:** API contract tests required (`httpx`); baseline 742 pytest green
- **D. Security:** env-var guard allowlist (names only); no committed values; size/type controls
- **E. CI/CD:** pytest + health-check gates in `.github/workflows/test.yml`
- **F. Retention/AI boundary:** Clear Data semantics per `../policies/data-retention-policy.md` §5; effective retention ≤ session expiry
- **G. Research:** **no new external research required for this phase** (internal decisions only)

## Canonical API decisions (locked — do not re-litigate)

| Decision | Value |
|---|---|
| API prefix | `/api/v1` (health stays `/healthz`) |
| Health endpoint | `GET /healthz` → `{"status":"ok"}` |
| Upload response | `{ "dataset": DatasetContext }` (201) |
| Preview response | `{ "dataset": DatasetContext, "rows": [...] }` |
| Auth/session transport | HttpOnly session cookie (`insights_session`) + `credentials: "include"` |
| API naming | snake_case at the boundary; React normalizes once in `setSourceFromApi` (Phase 4) |
| Upload policy | Browser cap **25 MB** = `MAX_BROWSER_UPLOAD_BYTES` (margin below Cloud Run's 32 MiB HTTP/1 limit); **100 MB** `MAX_INGEST_BYTES` is Drive/server-side only (Phase 5) |
| Session/data | `SessionStore`/`DatasetStore` interfaces + in-memory impls; shared ephemeral store proven only before hosted beta |
| Error shape | `{ "detail": "<message>" }` — typed, never echoing file contents or secrets |
| Dependency floors | `pandas>=2.3.3` · `pydantic>=2.12` · `fastapi` · `uvicorn` · `python-multipart` |

---

## 0. Preconditions and non-goals

**Preconditions (all closed, no re-doable work):** Gate 1 (credentials remediated), Gate 2 (branch + Streamlit freeze active), Gate 6 (retention/AI-boundary approved). Working branch `feat/react-fastapi-migration` is current with `main`. Streamlit app stays live and untouched.

**Non-goals / keep out of this PR:** React UI porting (Phase 4) · GA4 OAuth (Phase 5 — adapters **not** included here, not even as appendices) · Drive integration (Phase 5) · Gemini/chat (Phase 3) · charts/forecasting/funnels/exports · evidence/prototype panels. Do not copy GA4, Drive, Gemini, or React-callback code from F4 into this file's scope.

---

## 1. Environment guard and root `.env.example` *(first security task)*

**Rule (master-plan §11-D, 2026-08-06):** validate env var **names only** — `API_SESSION_SECRET` · `API_CORS_ORIGINS` · `FRONTEND_URL` · `MAX_BROWSER_UPLOAD_BYTES` · `MAX_INGEST_BYTES`. Validate names, expected presence in `.env.example`, and that **no committed values** exist. Never add values or permissive wildcard patterns to the allowlist.

### 1.1 `.env.example` — add a FastAPI section (root file — single-repo sibling layout)

```dotenv
# ── FastAPI migration backend (Phase 1) ─────────────────────────────────
# Names are allowlist-validated by scripts/check_credentials.py (names only).
# Real values belong in deployment secrets, never in the repo.
API_SESSION_SECRET=replace-with-a-long-random-value   # python -c "import secrets; print(secrets.token_urlsafe(48))"
API_CORS_ORIGINS=http://localhost:5173                 # Vite dev origin; same-origin deploy -> empty
FRONTEND_URL=http://localhost:5173
MAX_BROWSER_UPLOAD_BYTES=26214400                      # 25 MB = 25 * 1024 * 1024 (locked)
MAX_INGEST_BYTES=104857600                             # 100 MB = 100 * 1024 * 1024 (Drive/server-side only)
```

Placeholder convention: empty, `<angle-bracket>`, `your_xxx_here`, `replace-with-...`, or `...` — anything else is treated as a committed value.

### 1.2 `scripts/check_credentials.py` — two-part guard

**Part 1 — env-file value scan (new).** Scan env-like and deployment-config files only:

```text
.env · .env.* · *.env · docker-compose*.yml · docker-compose*.yaml · cloudbuild.yaml · .github/workflows/*.yml
```

Fail if any allowlisted name carries a non-placeholder `NAME=value` there (message: "use deployment secrets instead"). `API_SESSION_SECRET` is additionally checked inside `.env.example` itself (must be a placeholder). **Never** scan all prose for generic `NAME=value` — the migration docs intentionally contain safe constants (e.g. `MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024`); an all-text scanner creates noisy false positives and trains people to ignore guard failures.

**Part 2 — whole-repo secret-pattern scanner (existing).** Keep the AIza / AQ / ya29 shape patterns scanning the entire repository unchanged.

```python
# ── FastAPI env-var allowlist (names only) ──────────────────────────────
ALLOWLISTED_ENV_VARS = frozenset({
    "API_SESSION_SECRET", "API_CORS_ORIGINS", "FRONTEND_URL",
    "MAX_BROWSER_UPLOAD_BYTES", "MAX_INGEST_BYTES",
})
SECRET_ENV_VARS = frozenset({"API_SESSION_SECRET"})  # never committed, not even in .env.example
ENV_EXAMPLE_PATH = Path(".env.example")
ENV_ASSIGNMENT = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$")
PLACEHOLDER_VALUE = re.compile(r"^(<[^>]*>|your_[a-z0-9_]+_here|replace-with-.*|\.\.\.)$")
ENV_FILE_PARTS = {".env", ".env.*", "*.env", "docker-compose.yml",
                  "docker-compose.yaml", "cloudbuild.yaml", ".github/workflows"}
```

Checks in `main()`: (1) **presence** — every allowlisted name appears as `NAME=` in `.env.example` (always runs); (2) **secret value** — `API_SESSION_SECRET=<non-placeholder>` anywhere, including `.env.example`, fails; (3) **config value** — allowlisted names with non-placeholder values in the env-file set above fail. Update the pre-commit hook name and the CI step name to mention the allowlist (hook id `check-credentials` and the `git ls-files` CI step stay — the checks ride along).

### 1.3 Tests — extend `tests/test_credential_guard.py`

Build any `NAME=value` strings at runtime via concatenation so the guard never flags its own test file (existing file convention):

- [ ] Presence passes when all five names are documented; fails and lists a name when one is removed.
- [ ] `API_SESSION_SECRET=replace-with-a-long-random-value` passes; a real value fails.
- [ ] An env-file with `API_SESSION_SECRET=<real>` fails the value scan.
- [ ] `cloudbuild.yaml` / `.github/workflows/*.yml` with a committed value fail.
- [ ] Docs prose `MAX_BROWSER_UPLOAD_BYTES = 25 * 1024 * 1024` **does not** fail.
- [ ] Existing shape-pattern tests remain green.

### 1.4 Acceptance

- [ ] `git ls-files -z | xargs -0 python scripts/check_credentials.py` exits 0 on the clean repo.
- [ ] Removing a name from `.env.example` fails CI with a clear message.
- [ ] Committing a real value in an env-file fails pre-commit + CI.
- [ ] Full `pytest` suite green.

---

## 2. Dependency additions

Add to `requirements/base.txt` (or `requirements/api.txt`):

```txt
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
python-multipart>=0.0.9,<1
pydantic-settings>=2.0,<3
itsdangerous>=2.2,<3
httpx>=0.27,<1          # dev/contract tests
```

**Do not** add a database or Redis in Phase 1. In-memory stores only, behind interfaces.

---

## 3. API package layout

```text
insights-explorer/
  api/
    __init__.py
    main.py                # app, CORS, router includes
    config.py              # Settings (pydantic-settings) — reads the 5 allowlisted vars
    dependencies.py        # get_or_create_session, require_dataset
    schemas.py             # DateRange, Column, DatasetContext, QualityReport, errors
    stores/
      __init__.py
      session_store.py     # SessionStore protocol + InMemorySessionStore
      dataset_store.py     # DatasetStore protocol + InMemoryDatasetStore
    services/
      __init__.py
      dataset_service.py   # parse/make_context (adapts utils/data_loader.py)
      quality_service.py   # adapts utils.data_loader.assess_data_quality
    routes/
      __init__.py
      health.py
      upload.py            # /api/v1/upload, /data/context, /data/preview, /data/quality, /data/clear
  tests/
    api/                   # NEW — FastAPI contract tests (httpx)
      test_health.py
      test_upload.py
      test_data_flows.py   # context/preview/quality/clear lifecycle
      test_session.py
```

The current Streamlit UI stays alive alongside; it must not call FastAPI from inside Streamlit.

---

## 4. FastAPI application bootstrap

`api/config.py` — reads the five allowlisted vars; `api_session_secret` is required (no default), CORS defaults to the Vite dev origin:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    api_cors_origins: str = "http://localhost:5173"     # Vite dev origin; "" = same-origin deploy
    api_session_secret: str                              # REQUIRED — no default (guard-allowlisted)
    frontend_url: str = "http://localhost:5173"
    max_browser_upload_bytes: int = 25 * 1024 * 1024     # MAX_BROWSER_UPLOAD_BYTES (locked)
    max_ingest_bytes: int = 100 * 1024 * 1024            # MAX_INGEST_BYTES — Drive/server-side only

    @property
    def cors_origins(self) -> list[str]:
        return [v.strip() for v in self.api_cors_origins.split(",") if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Notes: `env_file=".env"` reads the **untracked local** `.env` (gitignored — never a committed file). Logging the session secret or echoing env values in responses is forbidden (track D).

`api/main.py` (Phase 1 — no SPA fallback yet; that is Phase 6):

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import health, upload

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
```

Create `__init__.py` for `api/`, `api/stores/`, `api/services/`, `api/routes/`.

---

## 5. Health endpoint

`api/routes/health.py`:

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

---

## 6. SessionStore / DatasetStore interfaces

Interfaces first, dev impls second (state placement, master-plan §5). `api/stores/session_store.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class AppSession:
    dataset_id: str | None = None
    ga4_credentials: dict | None = None
    oauth_state: str | None = None
    code_verifier: str | None = None          # PKCE — used Phase 5
    metadata: dict = field(default_factory=dict)


class SessionStore(Protocol):
    def create(self) -> tuple[str, AppSession]: ...
    def get(self, session_id: str) -> AppSession | None: ...
    def delete(self, session_id: str) -> None: ...
```

`api/stores/dataset_store.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from api.schemas import DatasetContext


@dataclass
class StoredDataset:
    id: str
    dataframe: pd.DataFrame
    context: DatasetContext


class DatasetStore(Protocol):
    def put(self, dataframe: pd.DataFrame, context: DatasetContext) -> StoredDataset: ...
    def get(self, dataset_id: str) -> StoredDataset | None: ...
    def remove(self, dataset_id: str) -> None: ...
```

---

## 7. In-memory local implementations

`api/stores/session_store.py` (append):

```python
class InMemorySessionStore:
    """Local dev implementation — replace with a shared ephemeral store
    (Redis/Valkey) before the hosted beta; interfaces keep routes unchanged."""

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

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


sessions = InMemorySessionStore()
```

(`RLock` / `uuid4` imports added at the top of the module.)

`api/stores/dataset_store.py` (append):

```python
class InMemoryDatasetStore:
    """Dev implementation — memory-cache semantics (eviction-tolerant; Phase 6 note)."""

    def __init__(self) -> None:
        self._items: dict[str, StoredDataset] = {}

    def put(self, dataframe: pd.DataFrame, context: DatasetContext) -> StoredDataset:
        item = StoredDataset(id=uuid4().hex, dataframe=dataframe, context=context)
        self._items[item.id] = item
        return item

    def get(self, dataset_id: str) -> StoredDataset | None:
        return self._items.get(dataset_id)

    def remove(self, dataset_id: str) -> None:
        self._items.pop(dataset_id, None)


datasets = InMemoryDatasetStore()
```

`api/dependencies.py` — cookie → session (12 h absolute expiry per the approved session policy; `__Host-` in production):

```python
from __future__ import annotations

from fastapi import Cookie, HTTPException, Response, status

from api.stores.session_store import AppSession, sessions

SESSION_COOKIE = "insights_session"


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
        secure=False,          # True behind HTTPS; Phase 6 adds the __Host- prefix
        samesite="lax",
        max_age=60 * 60 * 12,  # 12 h absolute (approved session policy)
        path="/",
    )
    return session


def require_dataset(session: AppSession | None = None) -> AppSession:
    if not session or not session.dataset_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active dataset. Upload a file or connect GA4 first.",
        )
    return session
```

---

## 8. Upload endpoint, 25 MB cap

`api/services/dataset_service.py` — parsing is an **adapter boundary** to `utils/data_loader.py` (do not duplicate its validation/error taxonomy):

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from api.schemas import Column, DatasetContext, DateRange


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    return "string"


def make_context(df: pd.DataFrame, *, source: str, filename: str) -> DatasetContext:
    date_columns = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
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
            Column(name=str(c), type=infer_column_type(df[c]), nullable=bool(df[c].isna().any()))
            for c in df.columns
        ],
        provenance={"created_at": datetime.now(timezone.utc).isoformat(), "transformations": []},
    )


def parse_uploaded_file(filename: str, content: bytes) -> pd.DataFrame:
    """Adapter boundary — replace with utils/data_loader.load_file() once its
    Streamlit cache/UI coupling is extracted (Phase 2). No duplicate parsers."""
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

`api/routes/upload.py` (upload endpoint; the data endpoints live in §9–§10):

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from api.config import get_settings
from api.dependencies import AppSession, get_or_create_session
from api.schemas import UploadResponse
from api.services.dataset_service import datasets, make_context, parse_uploaded_file

router = APIRouter(prefix="/api/v1", tags=["data"])

ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
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
    if len(content) > settings.max_browser_upload_bytes:          # 25 MB locked cap
        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the 25 MB browser limit. Use a Drive import or a smaller file.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        dataframe = parse_uploaded_file(filename, content)
        context = make_context(dataframe, source="upload", filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # Log sanitized metadata server-side; never echo file contents or secrets.
        raise HTTPException(status_code=422, detail="Unable to parse this file.") from exc

    stored = datasets.put(dataframe, context)
    session.dataset_id = stored.id
    return UploadResponse(dataset=stored.context)
```

---

## 9. Dataset context / preview / quality endpoints

`api/routes/upload.py` (append — the data endpoints share the same router):

```python
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


@router.get("/data/preview", response_model=DataPreviewResponse)
def get_data_preview(
    response: Response,
    limit: int = 10,
    session: AppSession = Depends(get_or_create_session),
) -> DataPreviewResponse:
    if not session.dataset_id:
        raise HTTPException(status_code=409, detail="No active dataset.")
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")

    safe_limit = min(max(limit, 1), 100)
    frame = dataset.dataframe.head(safe_limit).where(dataset.dataframe.notna(), None)
    return DataPreviewResponse(
        dataset=dataset.context,
        rows=frame.to_dict(orient="records"),
    )


@router.get("/data/quality", response_model=QualityReport)
def get_data_quality(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> QualityReport:
    if not session.dataset_id:
        raise HTTPException(status_code=409, detail="No active dataset.")
    dataset = datasets.get(session.dataset_id)
    if not dataset:
        raise HTTPException(status_code=410, detail="Dataset session has expired.")
    return build_quality_report(dataset.dataframe)
```

`api/services/quality_service.py` — adapt the existing A–F scorecard (`utils/data_loader.assess_data_quality`, already exercised by `tests/test_data_quality.py`):

```python
from __future__ import annotations

import pandas as pd

from api.schemas import QualityReport


def build_quality_report(df: pd.DataFrame, missing_cols: list[str] | None = None) -> QualityReport:
    """Adapt utils.data_loader.assess_data_quality / DataQualityReport.
    The initial endpoint calls it directly; Phase 2 removes any Streamlit coupling."""
    from utils.data_loader import assess_data_quality  # direct until Phase 2 decoupling

    report = assess_data_quality(df, missing_cols)
    return QualityReport(
        grade=report.grade,
        completeness_pct=report.completeness_pct,
        duplicate_pct=report.duplicate_pct,
        duplicate_count=report.duplicate_count,
        outlier_count=report.outlier_count,
        date_range_days=report.date_range_days,
        date_gaps=report.date_gaps,
        column_count=report.column_count,
        missing_columns=report.missing_columns,
        warnings=report.warnings,
    )
```

---

## 10. Clear Data endpoint

`api/routes/upload.py` (append) — server-side Clear Data, retention-policy §5 semantics: deletes the dataset + preview rows + quality/analysis cache + chat context + export temp files. Does **not** clear OAuth connection or theme preference:

```python
@router.post("/data/clear", status_code=status.HTTP_200_OK)
def clear_data(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> dict[str, str]:
    """Server-side Clear Data per policies/data-retention-policy.md §5."""
    if session.dataset_id:
        datasets.remove(session.dataset_id)
        session.dataset_id = None
    return {"status": "cleared"}
```

---

## 11. Error taxonomy and response schemas

`api/schemas.py` — F4 §5 plus the quality report (fields mirror `utils.data_loader.DataQualityReport`):

```python
from __future__ import annotations

from datetime import date
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


class DataPreviewResponse(BaseModel):
    dataset: DatasetContext
    rows: list[dict]


class QualityReport(BaseModel):
    grade: Literal["A", "B", "C", "D", "E", "F"]
    completeness_pct: float
    duplicate_pct: float
    duplicate_count: int
    outlier_count: int
    date_range_days: int | None
    date_gaps: int
    column_count: int
    missing_columns: list[str]
    warnings: list[str]


class APIError(BaseModel):
    detail: str
```

Error taxonomy (all errors are `{ "detail": ... }`, `APIError`):

| Code | Condition | Message |
|---|---|---|
| 400 | Empty upload | `Uploaded file is empty.` |
| 409 | No active dataset | `No active dataset.` / `No active dataset. Upload a file or connect GA4 first.` |
| 410 | Dataset session expired | `Dataset session has expired.` |
| 413 | Over 25 MB browser cap | `Uploaded file exceeds the 25 MB browser limit. Use a Drive import or a smaller file.` |
| 415 | Unsupported suffix | `Upload a CSV, XLSX, or XLS file.` |
| 422 | Parse failure (ValueError) | the ValueError message |
| 422 | Parse failure (other) | `Unable to parse this file.` (sanitized — log metadata server-side, never file contents) |

---

## 12. Contract tests (`tests/api/`)

Use `httpx` + FastAPI's `TestClient`/`ASGITransport`:

- [ ] `GET /healthz` → 200 `{"status":"ok"}`.
- [ ] Upload CSV → 201 with `{dataset}`; context fields correct (row_count, columns, date_range).
- [ ] Upload XLSX → 201. `.txt`/bad suffix → 415. Empty file → 400.
- [ ] **25 MB boundary:** just over `MAX_BROWSER_UPLOAD_BYTES` → 413 with the exact rejection message.
- [ ] `context`/`preview`/`quality` before upload → 409.
- [ ] `preview?limit=0` clamps to 1; `limit=1000` clamps to 100.
- [ ] `quality` returns the A–F report with all fields.
- [ ] **Clear Data lifecycle:** upload → context → quality → clear → context → 409; dataset removed from the store.
- [ ] Session cookie set (`insights_session`, httponly) and correlates across requests.
- [ ] Guard tests from §1 pass (`tests/test_credential_guard.py`).

Test file note: no full-length credential-shaped strings in test sources (runtime concatenation convention).

---

## 13. Minimal frontend/MSW verification (conditional)

Only if a React shell exists in the repo when Phase 1 lands — otherwise **defer entirely to Phase 4** (master-plan §5: "MSW test setup in the frontend *if* the React shell exists yet"). If a shell exists:

- [ ] MSW handlers for `POST /upload` + `GET /data/preview` (pattern from F4 §12 — parked for Phase 4) with `onUnhandledRequest: "error"`.
- [ ] One store test: upload transitions `idle → loading → ready`; failure → `error` with the visible message.
- [ ] No production component imports mock data.

Do not scaffold a React app in Phase 1 if none exists.

---

## 14. PR acceptance gate

### Runbook

```bash
# from repo root (branch: feat/react-fastapi-migration)
pip install -r requirements/base.txt
cp .env.example .env        # fill API_SESSION_SECRET (generated value — never committed)
uvicorn api.main:app --reload --port 8000

curl http://localhost:8000/healthz            # {"status":"ok"}
curl -F "file=@sample.csv" http://localhost:8000/api/v1/upload -c cookies.txt
curl -b cookies.txt http://localhost:8000/api/v1/data/context
curl -b cookies.txt http://localhost:8000/api/v1/data/preview
curl -b cookies.txt http://localhost:8000/api/v1/data/quality
curl -b cookies.txt -X POST http://localhost:8000/api/v1/data/clear
pytest tests/ tests/api/ -q                    # full regression + contract tests
```

### Exit criteria (DoD for this phase)

- [ ] App runs on `:8000`; `/healthz` passes.
- [ ] **upload → context → preview → quality → clear** works end-to-end via `httpx` contract tests (Clear Data semantics per `../policies/data-retention-policy.md` §5).
- [ ] **25 MB browser cap enforced** with a boundary test and the exact rejection message; the 100 MB `MAX_INGEST_BYTES` is a Phase 5 Drive/server-side concern only.
- [ ] Guard allowlist (§1): five names present in `.env.example`; no committed values; CI + pre-commit enforce it.
- [ ] Baseline **742 pytest green** (no regression); `pytest tests/api/` green.
- [ ] No GA4/Drive/Gemini/chat/export/React code in the PR (non-goals honored).

### Gate table

| Gate | Evidence | Owner | How verified |
|---|---|---|---|
| **Gate 7 — vertical slice works** | `pytest tests/api/` green · `/healthz` curl passes · upload→clear lifecycle verified · 25 MB boundary test green · baseline suite green | Implementation agent | Record evidence in this file + master-plan §5; flip `phase-1-upload-slice.md` to DONE and Phase 2 to ACTIVE in `specs/README.md` |
| Release gate 1 — no regression | 452 utils-facing tests stay green | Agent + reviewer | `pytest` baseline before merge |
| Release gate 2 — contract | Endpoint/schema/error behavior matches this spec | Agent | `pytest tests/api/` + OpenAPI schema dump review |
| Release gate 3 — user flow | Upload → preview → clear works (MSW/Playwright where the shell exists) | Agent | Contract tests now; Playwright joins with the React shell (Phase 4) |

## Source documents

- F4 `phase-1-api-react-callback-tests-implementation.md` (embedded — **superseded for execution**)
- master-plan §5 (authorization, locked decisions) + §11-D (guard rule) + §14 (release gates)
- `../policies/data-retention-policy.md` §2/§5 (retention, Clear Data semantics)
- `../policies/env-rotation-checklist.md` Phase E (allowlist task checkbox)
- archive §4.2 (canonical shapes) · §3.5 (wire format) · §3.9–3.10 (pins) · §4.11–4.14 (size policy, state placement)

*Spec created 2026-08-06 (product-owner interview + reviewer answer-set); 14-step task order per reviewer recommendation. Planning-only — no migration product code written yet.*
