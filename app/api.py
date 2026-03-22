"""FastAPI routes for V2T Game Analysis API."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.models import AnalysisOutput, AnalyzeQueuedResponse, AnalyzeRequest
from app.service import run_analysis
from app.tasks import run_analysis_task

router = APIRouter()

ACCEPTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ACCEPTED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


def _validate_upload(file: UploadFile, mode: str) -> None:
    ct = file.content_type or ""
    if mode == "image" and ct not in ACCEPTED_IMAGE_TYPES:
        raise HTTPException(422, f"Unsupported image type: {ct}")
    if mode == "video" and ct not in ACCEPTED_VIDEO_TYPES:
        raise HTTPException(422, f"Unsupported video type: {ct}")


@router.post("/analyze", response_model=AnalyzeQueuedResponse)
async def analyze(
    file: UploadFile = File(...),
    mode: str = Form(...),
    depth_level: int = Form(...),
    stack_hint: str | None = Form(default=None),
    project_type: str | None = Form(default=None),
    duration_seconds: int = Form(default=0),
) -> AnalyzeQueuedResponse:
    """Queue an async analysis job. Returns job_id immediately."""
    # Validate request
    AnalyzeRequest(
        mode=mode,
        depth_level=depth_level,
        stack_hint=stack_hint,
        project_type=project_type,
    )
    _validate_upload(file, mode)

    # Read file bytes
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(422, "Uploaded file is empty.")

    # Dispatch Celery task
    task = run_analysis_task.delay({
        "filename": file.filename or "upload.bin",
        "file_bytes": file_bytes,  # NOTE: Celery must serialize bytes — use base64 if needed
        "mode": mode,
        "depth_level": depth_level,
        "stack_hint": stack_hint,
        "duration_seconds": duration_seconds,
        "generate_pdf": True,
    })

    return AnalyzeQueuedResponse(job_id=task.id)


@router.post("/analyze/sync", response_model=AnalysisOutput)
async def analyze_sync(
    file: UploadFile = File(...),
    mode: str = Form(...),
    depth_level: int = Form(...),
    stack_hint: str | None = Form(default=None),
    duration_seconds: int = Form(default=0),
    return_pdf: bool = Form(default=False),
) -> JSONResponse | AnalysisOutput:
    """
    Synchronous analysis — waits for result and returns full AnalysisOutput.
    Set return_pdf=true to get the PDF file directly as a download.
    """
    AnalyzeRequest(mode=mode, depth_level=depth_level, stack_hint=stack_hint)
    _validate_upload(file, mode)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(422, "Uploaded file is empty.")

    output = run_analysis(
        filename=file.filename or "upload.bin",
        file_bytes=file_bytes,
        mode=mode,
        depth_level=depth_level,
        stack_hint=stack_hint,
        duration_seconds=duration_seconds,
        generate_pdf=True,
    )

    # Return PDF file if requested and available
    if return_pdf and output.get("report_pdf_path"):
        pdf_path = output["report_pdf_path"]
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="game_analysis_report.pdf",
        )

    return JSONResponse(content=output)


@router.get("/analyze/{job_id}/result")
async def get_job_result(job_id: str) -> JSONResponse:
    """Fetch result of an async job by job_id."""
    from celery.result import AsyncResult
    from app.tasks import celery_app

    result = AsyncResult(job_id, app=celery_app)

    if result.state == "PENDING":
        return JSONResponse({"job_id": job_id, "status": "pending"})
    elif result.state == "SUCCESS":
        return JSONResponse({"job_id": job_id, "status": "done", "result": result.result})
    elif result.state == "FAILURE":
        return JSONResponse({"job_id": job_id, "status": "failed", "error": str(result.result)})
    else:
        return JSONResponse({"job_id": job_id, "status": result.state.lower()})
