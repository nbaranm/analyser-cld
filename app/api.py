"""FastAPI routes for GDA Game Analysis API."""
from __future__ import annotations
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from app.service import run_analysis

router = APIRouter()

ACCEPTED_IMAGE = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ACCEPTED_VIDEO = {"video/mp4", "video/webm", "video/quicktime"}


@router.post("/analyze/sync")
async def analyze_sync(
    mode: str = Form(...),
    depth_level: int = Form(...),
    file: UploadFile = File(None),
    store_url: str = Form(default=""),
    genre: str = Form(default="Casual"),
    mono_model: str = Form(default="F2P"),
    platform: str = Form(default="Mobile"),
    stack_hint: str = Form(default=""),
    duration_seconds: int = Form(default=0),
    return_pdf: bool = Form(default=False),
):
    if not store_url and not file:
        raise HTTPException(422, "Provide store_url or upload a file")

    file_bytes = b""
    filename = "upload.bin"

    if file:
        ct = file.content_type or ""
        if mode == "image" and ct not in ACCEPTED_IMAGE:
            raise HTTPException(422, f"Unsupported image type: {ct}")
        if mode == "video" and ct not in ACCEPTED_VIDEO:
            raise HTTPException(422, f"Unsupported video type: {ct}")
        file_bytes = await file.read()
        filename = file.filename or "upload.bin"

    output = run_analysis(
        filename=filename,
        file_bytes=file_bytes,
        mode=mode,
        depth_level=depth_level,
        stack_hint=stack_hint or None,
        duration_seconds=duration_seconds,
        generate_pdf=True,
        store_url=store_url or None,
        genre=genre,
        mono_model=mono_model,
        platform=platform,
    )

    if return_pdf and output.get("report_pdf_path"):
        return FileResponse(output["report_pdf_path"], media_type="application/pdf", filename="gda_report.pdf")

    return JSONResponse(content=output)


@router.post("/analyze")
async def analyze_async(
    mode: str = Form(...),
    depth_level: int = Form(...),
    file: UploadFile = File(None),
    store_url: str = Form(default=""),
    genre: str = Form(default="Casual"),
    mono_model: str = Form(default="F2P"),
    platform: str = Form(default="Mobile"),
    duration_seconds: int = Form(default=0),
):
    import uuid
    from app.tasks import run_analysis_task
    file_bytes = b""
    filename = "upload.bin"
    if file:
        file_bytes = await file.read()
        filename = file.filename or "upload.bin"
    import base64
    task = run_analysis_task.delay({
        "filename": filename,
        "file_bytes": base64.b64encode(file_bytes).decode() if file_bytes else "",
        "mode": mode,
        "depth_level": depth_level,
        "store_url": store_url,
        "genre": genre,
        "mono_model": mono_model,
        "platform": platform,
        "generate_pdf": True,
    })
    return JSONResponse({"job_id": task.id, "status": "queued"})


@router.get("/analyze/{job_id}/result")
async def get_result(job_id: str):
    from celery.result import AsyncResult
    from app.tasks import celery_app
    result = AsyncResult(job_id, app=celery_app)
    if result.state == "PENDING":
        return JSONResponse({"job_id": job_id, "status": "pending"})
    elif result.state == "SUCCESS":
        return JSONResponse({"job_id": job_id, "status": "done", "result": result.result})
    elif result.state == "FAILURE":
        return JSONResponse({"job_id": job_id, "status": "failed", "error": str(result.result)})
    return JSONResponse({"job_id": job_id, "status": result.state.lower()})
