"""FastAPI routes."""
from __future__ import annotations
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse
from app.service import run_analysis

router = APIRouter()


@router.post("/analyze/sync")
async def analyze_sync(
    mode: str = Form(default="image"),
    depth_level: int = Form(default=2),
    file: UploadFile = File(default=None),
    store_url: str = Form(default=""),
    genre: str = Form(default="Casual"),
    mono_model: str = Form(default="F2P"),
    platform: str = Form(default="PC"),
    stack_hint: str = Form(default=""),
    duration_seconds: int = Form(default=0),
):
    file_bytes = b""
    filename = "upload.bin"
    if file and file.filename:
        file_bytes = await file.read()
        filename = file.filename

    result = run_analysis(
        filename=filename,
        file_bytes=file_bytes,
        mode=mode,
        depth_level=depth_level,
        stack_hint=stack_hint or None,
        duration_seconds=duration_seconds,
        store_url=store_url or None,
        genre=genre,
        mono_model=mono_model,
        platform=platform,
    )
    return JSONResponse(content=result)


@router.post("/analyze")
async def analyze_async(
    mode: str = Form(default="image"),
    depth_level: int = Form(default=2),
    file: UploadFile = File(default=None),
    store_url: str = Form(default=""),
    genre: str = Form(default="Casual"),
    mono_model: str = Form(default="F2P"),
):
    import uuid
    return JSONResponse({"job_id": str(uuid.uuid4()), "status": "queued"})


@router.get("/analyze/{job_id}/result")
async def get_result(job_id: str):
    return JSONResponse({"job_id": job_id, "status": "pending"})
