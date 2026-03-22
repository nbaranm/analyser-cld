"""Data models for request/response payloads."""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.core.constants import SUPPORTED_DEPTHS, SUPPORTED_MODES


class AnalyzeRequest(BaseModel):
    mode: Literal["image", "video"]
    depth_level: int = Field(ge=1, le=3)
    stack_hint: str | None = None
    project_type: str | None = None  # "game", "web", "mobile", etc.

    @model_validator(mode="after")
    def validate_supported(self) -> "AnalyzeRequest":
        if self.mode not in SUPPORTED_MODES:
            raise ValueError("Unsupported mode")
        if self.depth_level not in SUPPORTED_DEPTHS:
            raise ValueError("Unsupported depth level")
        return self


class AnalyzeQueuedResponse(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["queued"] = "queued"


# --- Game-specific analysis sections ---

class UIUXAnalysis(BaseModel):
    component_map: list[str] = []
    layout_model: dict[str, Any] = {}
    design_tokens: dict[str, Any] = {}
    accessibility_issues: list[str] = []
    hud_elements: list[str] = []
    menu_structure: list[str] = []


class GameplayAnalysis(BaseModel):
    genre: str = "unknown"
    core_loop: str = ""
    mechanics: list[str] = []
    player_actions: list[str] = []
    progression_system: str = ""
    difficulty_curve: str = ""


class VisualDesignAnalysis(BaseModel):
    art_style: str = "unknown"
    color_palette: list[str] = []
    animation_quality: str = ""
    vfx_notes: list[str] = []
    ui_consistency: str = ""


class CodeArchitectureAnalysis(BaseModel):
    detected_patterns: list[str] = []
    folder_tree: str = ""
    recommended_stack: str = ""
    code_snippets: dict[str, str] = {}
    data_models: dict[str, Any] = {}
    api_contract: dict[str, Any] = {}


class PerformanceAnalysis(BaseModel):
    scalability_class: str = "unknown"
    optimization_notes: list[str] = []
    estimated_monthly_cost: dict[str, Any] = {}
    bottlenecks: list[str] = []


class MonetizationAnalysis(BaseModel):
    detected_model: str = "unknown"  # f2p, premium, subscription, etc.
    iap_elements: list[str] = []
    market_fit_notes: list[str] = []
    revenue_potential: str = ""


class AnalysisOutput(BaseModel):
    technical_summary: str
    confidence_score: int = Field(ge=0, le=100)
    assumptions: list[str]

    # Game-specific sections
    ui_ux: UIUXAnalysis = Field(default_factory=UIUXAnalysis)
    gameplay: GameplayAnalysis = Field(default_factory=GameplayAnalysis)
    visual_design: VisualDesignAnalysis = Field(default_factory=VisualDesignAnalysis)
    code_architecture: CodeArchitectureAnalysis = Field(default_factory=CodeArchitectureAnalysis)
    performance: PerformanceAnalysis = Field(default_factory=PerformanceAnalysis)
    monetization: MonetizationAnalysis = Field(default_factory=MonetizationAnalysis)

    # Legacy flat fields (backward compat)
    data_models: dict[str, Any] = {}
    api_contract: dict[str, Any] = {}
    frontend_structure: dict[str, Any] = {}
    backend_structure: dict[str, Any] = {}
    folder_tree: str = ""
    code_snippets: dict[str, Any] = {}
    optimization_notes: list[str] = []

    # PDF report path (populated after generation)
    report_pdf_path: str | None = None
