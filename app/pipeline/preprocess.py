"""Media preprocessing — reads real file bytes, prepares for Claude Vision."""

from __future__ import annotations

import base64
import io
from typing import Any

from app.core.constants import MAX_IMAGE_EDGE, MAX_VIDEO_SECONDS


def _resize_image_bytes(image_bytes: bytes, max_edge: int = MAX_IMAGE_EDGE) -> bytes:
    """Resize image so longest edge <= max_edge. Returns JPEG bytes."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > max_edge:
            ratio = max_edge / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except ImportError:
        # Pillow not installed — return raw bytes
        return image_bytes


def preprocess_image(filename: str, file_bytes: bytes) -> dict[str, Any]:
    """
    Resize image and encode to base64 for Claude Vision API.
    Returns dict with base64 data ready for the API call.
    """
    resized = _resize_image_bytes(file_bytes)
    b64 = base64.standard_b64encode(resized).decode("utf-8")

    return {
        "mode": "image",
        "file": filename,
        "media_type": "image/jpeg",
        "base64_data": b64,
        "steps_applied": ["resize_max_1024", "jpeg_encode", "base64_encode"],
        "evidence": [],
    }


def preprocess_video(
    filename: str,
    file_bytes: bytes,
    duration_seconds: int,
) -> dict[str, Any]:
    """
    Extract frames from video at 2-second intervals, encode each to base64.
    Falls back to single thumbnail if cv2 not available.
    """
    if duration_seconds > MAX_VIDEO_SECONDS:
        return {
            "error": f"Video exceeds {MAX_VIDEO_SECONDS} seconds. Provided: {duration_seconds}s.",
            "mode": "video",
            "file": filename,
            "frames": [],
        }

    frames: list[dict[str, str]] = []

    try:
        import tempfile
        import os
        import cv2  # type: ignore

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        cap = cv2.VideoCapture(tmp_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_interval = int(fps * 2)  # every 2 seconds
        frame_idx = 0
        extracted = 0

        while cap.isOpened() and extracted < 15:  # max 15 frames
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                b64 = base64.standard_b64encode(buf.tobytes()).decode("utf-8")
                frames.append({
                    "timestamp_s": str(round(frame_idx / fps, 1)),
                    "media_type": "image/jpeg",
                    "base64_data": b64,
                })
                extracted += 1
            frame_idx += 1

        cap.release()
        os.unlink(tmp_path)

    except ImportError:
        # cv2 not available — encode entire file as fallback
        b64 = base64.standard_b64encode(file_bytes[:2 * 1024 * 1024]).decode("utf-8")
        frames.append({
            "timestamp_s": "0",
            "media_type": "video/mp4",
            "base64_data": b64,
        })

    return {
        "mode": "video",
        "file": filename,
        "frames": frames,
        "frame_count": len(frames),
        "steps_applied": ["sample_frames_2s", "jpeg_encode", "base64_encode"],
        "evidence": [],
    }
