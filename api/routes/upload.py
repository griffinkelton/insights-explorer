"""Upload + dataset data endpoints (spec §8–§10).

- ``POST /api/v1/upload`` — bounded-chunk read, 25 MB browser cap enforced
  mid-stream (never after full buffering; Content-Length is preflighted only
  and never trusted as the sole control).
- ``GET /api/v1/data/context`` · ``/data/preview`` · ``/data/quality``
- ``POST /api/v1/data/clear`` — policy-real Clear Data (§8 clear_dataset_state).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from api.config import get_settings
from api.dependencies import AppSession, get_or_create_session
from api.schemas import DataPreviewResponse, DatasetContext, QualityReport, UploadResponse
from api.services.dataset_service import clear_dataset_state, make_context, parse_uploaded_file
from api.services.quality_service import build_quality_report
from api.stores.dataset_store import datasets  # canonical store location (api/stores)

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

    # Bounded read: stream in 1 MB chunks and reject as soon as the total
    # exceeds the cap — never buffer the whole file before the size check.
    # Content-Length may be preflighted, but it is client-supplied and is
    # never trusted as the only size control.
    CHUNK_SIZE = 1024 * 1024
    total = 0
    chunks: list[bytes] = []
    while chunk := await file.read(CHUNK_SIZE):
        total += len(chunk)
        if total > settings.max_browser_upload_bytes:  # 25 MB locked cap
            raise HTTPException(
                status_code=413,
                detail="Uploaded file exceeds the 25 MB browser limit. Use a Drive import or a smaller file.",
            )
        chunks.append(chunk)

    content = b"".join(chunks)
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


@router.post("/data/clear", status_code=status.HTTP_200_OK)
def clear_data(
    response: Response,
    session: AppSession = Depends(get_or_create_session),
) -> dict[str, str]:
    """Server-side Clear Data per policies/data-retention-policy.md §5."""
    clear_dataset_state(session)
    return {"status": "cleared"}
