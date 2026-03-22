"""Orchestrates the full analysis pipeline."""
from __future__ import annotations
from typing import Any
from app.core.constants import STACK_FOLDER_TREES
from app.pipeline.agents import run_full_analysis
from app.pipeline.preprocess import preprocess_image, preprocess_video


def _folder_tree_for(stack_hint):
    if not stack_hint:
        return STACK_FOLDER_TREES["nextjs-fastapi"]
    key = stack_hint.strip().lower().replace(" + ", "-").replace(" ", "-")
    return STACK_FOLDER_TREES.get(key, STACK_FOLDER_TREES["nextjs-fastapi"])


def run_analysis(
    filename: str,
    file_bytes: bytes,
    mode: str,
    depth_level: int,
    stack_hint=None,
    duration_seconds: int = 0,
    generate_pdf: bool = True,
    store_url=None,
    genre: str = "Casual",
    mono_model: str = "F2P",
    platform: str = "Mobile",
) -> dict[str, Any]:
    visual_parse = None
    if file_bytes and len(file_bytes) > 100:
        if mode == "image":
            visual_parse = preprocess_image(filename, file_bytes)
        else:
            visual_parse = preprocess_video(filename, file_bytes, duration_seconds)
        if visual_parse and visual_parse.get("error"):
            visual_parse = None

    result = run_full_analysis(
        store_url=store_url,
        visual_parse=visual_parse,
        genre=genre,
        mono_model=mono_model,
        platform=platform,
        depth_level=depth_level,
    )

    result["depth_level"] = depth_level
    result["folder_tree"] = _folder_tree_for(stack_hint)

    if generate_pdf:
        try:
            from app.pipeline.pdf_report import save_report
            from app.models import AnalysisOutput, UIUXAnalysis, GameplayAnalysis, VisualDesignAnalysis, CodeArchitectureAnalysis, PerformanceAnalysis, MonetizationAnalysis
            output = AnalysisOutput(
                technical_summary=str(result.get("roi", {}).get("priority_fix_roi", "Analysis complete."))[:500],
                confidence_score=int(result.get("confidence", 70)),
                assumptions=[],
                ui_ux=UIUXAnalysis(),
                gameplay=GameplayAnalysis(),
                visual_design=VisualDesignAnalysis(),
                code_architecture=CodeArchitectureAnalysis(folder_tree=result.get("folder_tree", "")),
                performance=PerformanceAnalysis(optimization_notes=[a.get("action", "") for a in result.get("action_plan", [])[:5]]),
                monetization=MonetizationAnalysis(detected_model=result.get("monetization", "unknown")),
                folder_tree=result.get("folder_tree", ""),
                optimization_notes=[a.get("action", "") for a in result.get("action_plan", [])[:5]],
            )
            pdf_path = save_report(output)
            result["report_pdf_path"] = pdf_path
        except Exception as e:
            result["pdf_error"] = str(e)

    return result
