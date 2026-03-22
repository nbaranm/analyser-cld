"""
Orchestrates the full V2T pipeline:
preprocess → agents (parallel) → compiler → PDF report
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.core.constants import STACK_FOLDER_TREES
from app.pipeline.agents import (
    api_agent,
    data_agent,
    gameplay_agent,
    monetization_agent,
    perf_agent,
    ui_agent,
    visual_agent,
)
from app.pipeline.compiler import compile_output
from app.pipeline.pdf_report import save_report
from app.pipeline.preprocess import preprocess_image, preprocess_video


def _folder_tree_for(stack_hint: str | None) -> str:
    if not stack_hint:
        return STACK_FOLDER_TREES["nextjs-fastapi"]
    key = stack_hint.strip().lower().replace(" + ", "-").replace(" ", "-")
    return STACK_FOLDER_TREES.get(key, STACK_FOLDER_TREES["nextjs-fastapi"])


def run_analysis(
    filename: str,
    file_bytes: bytes,
    mode: str,
    depth_level: int,
    stack_hint: str | None,
    duration_seconds: int = 0,
    generate_pdf: bool = True,
) -> dict[str, Any]:
    """
    Full synchronous analysis pipeline.
    Returns dict matching AnalysisOutput schema.
    """
    assumptions: list[str] = []
    folder_tree = _folder_tree_for(stack_hint)

    # --- Step 1: Preprocess ---
    if mode == "image":
        visual_parse = preprocess_image(filename, file_bytes)
    else:
        visual_parse = preprocess_video(filename, file_bytes, duration_seconds)

    if "error" in visual_parse:
        assumptions.append(visual_parse["error"])

    # --- Step 2: Run agents ---
    # UI, gameplay, visual agents always run (depth 1+)
    ui_spec = ui_agent(visual_parse)
    gameplay_spec = gameplay_agent(visual_parse)
    visual_spec = visual_agent(visual_parse)

    db_spec: dict[str, Any] = {}
    api_spec: dict[str, Any] = {}
    mono_spec: dict[str, Any] = {
        "detected_model": "unknown", "iap_elements": [],
        "market_fit_notes": [], "revenue_potential": "unknown",
    }

    if depth_level >= 2:
        db_spec = data_agent(visual_parse)
        api_spec = api_agent(db_spec)
        mono_spec = monetization_agent(visual_parse)

    perf_spec = perf_agent(depth_level=depth_level)

    # Code agent is always local (no AI call needed)
    code_spec = _code_agent_local(depth_level=depth_level, folder_tree=folder_tree)

    # --- Step 3: Compile ---
    result = compile_output(
        ui_spec=ui_spec,
        gameplay_spec=gameplay_spec,
        visual_spec=visual_spec,
        data_spec=db_spec,
        api_spec=api_spec,
        code_spec=code_spec,
        perf_spec=perf_spec,
        mono_spec=mono_spec,
        assumptions=assumptions,
        folder_tree=folder_tree,
    )

    # --- Step 4: PDF Report ---
    if generate_pdf:
        try:
            pdf_path = save_report(result)
            result.report_pdf_path = pdf_path
        except Exception as e:
            result.assumptions.append(f"PDF generation failed: {e}")

    return result.model_dump()


def _code_agent_local(depth_level: int, folder_tree: str) -> dict[str, Any]:
    """Generate code scaffold stubs based on depth level."""
    frontend_files: dict[str, str] = {}
    backend_files: dict[str, str] = {}

    if depth_level >= 1:
        frontend_files["frontend/components/AppShell.tsx"] = (
            "export default function AppShell({ children }: { children: React.ReactNode }) {\n"
            "  return <div className='app-shell'>{children}</div>;\n"
            "}"
        )
        frontend_files["frontend/components/HUD.tsx"] = (
            "export default function HUD() {\n"
            "  return <div className='hud'><!-- HUD elements --></div>;\n"
            "}"
        )

    if depth_level >= 2:
        backend_files["backend/models/player.py"] = (
            "from pydantic import BaseModel\n\n"
            "class Player(BaseModel):\n"
            "    id: int\n"
            "    username: str\n"
            "    level: int = 1\n"
            "    xp: int = 0\n"
        )
        backend_files["backend/api/player.py"] = (
            "from fastapi import APIRouter\nrouter = APIRouter()\n\n"
            "@router.get('/player/{player_id}')\nasync def get_player(player_id: int):\n"
            "    return {'id': player_id}\n"
        )

    if depth_level >= 3:
        backend_files["backend/main.py"] = (
            "from fastapi import FastAPI\n"
            "from backend.api.player import router as player_router\n\n"
            "app = FastAPI(title='Game API')\n"
            "app.include_router(player_router, prefix='/api')\n"
        )

    return {
        "folder_tree": folder_tree,
        "frontend_files": frontend_files,
        "backend_files": backend_files,
    }
