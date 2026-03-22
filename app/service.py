"""Orchestrates the analysis pipeline."""
from __future__ import annotations
from typing import Any
from app.core.constants import STACK_FOLDER_TREES
from app.pipeline.agents import run_full_analysis
from app.pipeline.preprocess import preprocess_image, preprocess_video


def run_analysis(
    filename: str = "upload.bin",
    file_bytes: bytes = b"",
    mode: str = "image",
    depth_level: int = 2,
    stack_hint: str | None = None,
    duration_seconds: int = 0,
    generate_pdf: bool = False,
    store_url: str | None = None,
    genre: str = "Casual",
    mono_model: str = "F2P",
    platform: str = "PC",
) -> dict[str, Any]:

    visual_parse = None
    if file_bytes and len(file_bytes) > 100:
        try:
            if mode == "image":
                visual_parse = preprocess_image(filename, file_bytes)
            else:
                visual_parse = preprocess_video(filename, file_bytes, duration_seconds)
            if visual_parse and visual_parse.get("error"):
                visual_parse = None
        except Exception:
            visual_parse = None

    result = run_full_analysis(
        store_url=store_url,
        visual_parse=visual_parse,
        genre=genre,
        mono_model=mono_model,
        platform=platform,
        depth_level=depth_level,
    )

    key = (stack_hint or "nextjs-fastapi").strip().lower().replace(" + ", "-").replace(" ", "-")
    result["folder_tree"] = STACK_FOLDER_TREES.get(key, STACK_FOLDER_TREES["nextjs-fastapi"])
    result["depth_level"] = depth_level

    return result
