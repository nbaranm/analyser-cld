"""Celery task definitions for asynchronous V2T jobs."""

import base64

from celery import Celery

from app.service import run_analysis

celery_app = Celery(
    "v2t",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,  # 1 hour
)


@celery_app.task(name="v2t.run_analysis", bind=True, max_retries=2)
def run_analysis_task(self, payload: dict) -> dict:
    """
    Async Celery task for V2T analysis.
    file_bytes is base64-encoded in payload for JSON serialization.
    """
    try:
        raw_bytes = payload.get("file_bytes")
        if isinstance(raw_bytes, str):
            # Decode from base64 if sent as string
            file_bytes = base64.b64decode(raw_bytes)
        elif isinstance(raw_bytes, bytes):
            file_bytes = raw_bytes
        else:
            file_bytes = b""

        return run_analysis(
            filename=payload.get("filename", "upload.bin"),
            file_bytes=file_bytes,
            mode=payload["mode"],
            depth_level=payload["depth_level"],
            stack_hint=payload.get("stack_hint"),
            duration_seconds=payload.get("duration_seconds", 0),
            generate_pdf=payload.get("generate_pdf", True),
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
