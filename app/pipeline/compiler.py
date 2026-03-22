"""Spec compiler — merges all agent outputs into final AnalysisOutput."""

from __future__ import annotations

from typing import Any

from app.core.constants import OUTPUT_FLAG_STRUCTURAL_AMBIGUITY
from app.models import (
    AnalysisOutput,
    CodeArchitectureAnalysis,
    GameplayAnalysis,
    MonetizationAnalysis,
    PerformanceAnalysis,
    UIUXAnalysis,
    VisualDesignAnalysis,
)


def _calculate_confidence(
    assumptions: list[str],
    agent_errors: int,
    evidence_count: int,
) -> int:
    base = 95
    penalty = len(assumptions) * 5       # each assumption -5
    error_penalty = agent_errors * 15    # each agent failure -15
    weak_evidence = 15 if evidence_count == 0 else 0
    score = max(0, min(100, base - penalty - error_penalty - weak_evidence))
    return score


def _count_agent_errors(*specs: dict[str, Any]) -> int:
    return sum(1 for s in specs if "agent_error" in s)


def _collect_evidence(*specs: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    for spec in specs:
        evidence.extend(spec.get("evidence", []))
    return list(set(evidence))


def compile_output(
    ui_spec: dict[str, Any],
    gameplay_spec: dict[str, Any],
    visual_spec: dict[str, Any],
    data_spec: dict[str, Any],
    api_spec: dict[str, Any],
    code_spec: dict[str, Any],
    perf_spec: dict[str, Any],
    mono_spec: dict[str, Any],
    assumptions: list[str],
    folder_tree: str,
) -> AnalysisOutput:

    agent_errors = _count_agent_errors(
        ui_spec, gameplay_spec, visual_spec, data_spec, mono_spec
    )
    evidence = _collect_evidence(
        ui_spec, gameplay_spec, visual_spec, data_spec, mono_spec
    )
    confidence = _calculate_confidence(assumptions, agent_errors, len(evidence))

    if confidence < 60 and OUTPUT_FLAG_STRUCTURAL_AMBIGUITY not in assumptions:
        assumptions.append(OUTPUT_FLAG_STRUCTURAL_AMBIGUITY)

    # Build genre-aware technical summary
    genre = gameplay_spec.get("genre", "unknown")
    art_style = visual_spec.get("art_style", "unknown")
    rec_stack = data_spec.get("recommended_stack", "unknown")
    mono_model = mono_spec.get("detected_model", "unknown")

    summary = (
        f"Game genre: {genre}. "
        f"Art style: {art_style}. "
        f"Recommended stack: {rec_stack}. "
        f"Monetization: {mono_model}. "
        f"Analysis confidence: {confidence}/100."
    )

    return AnalysisOutput(
        technical_summary=summary,
        confidence_score=confidence,
        assumptions=assumptions,

        ui_ux=UIUXAnalysis(
            component_map=ui_spec.get("component_map", []),
            layout_model=ui_spec.get("layout_model", {}),
            design_tokens=ui_spec.get("design_tokens", {}),
            accessibility_issues=ui_spec.get("accessibility_issues", []),
            hud_elements=ui_spec.get("hud_elements", []),
            menu_structure=ui_spec.get("menu_structure", []),
        ),

        gameplay=GameplayAnalysis(
            genre=gameplay_spec.get("genre", "unknown"),
            core_loop=gameplay_spec.get("core_loop", ""),
            mechanics=gameplay_spec.get("mechanics", []),
            player_actions=gameplay_spec.get("player_actions", []),
            progression_system=gameplay_spec.get("progression_system", ""),
            difficulty_curve=gameplay_spec.get("difficulty_curve", ""),
        ),

        visual_design=VisualDesignAnalysis(
            art_style=visual_spec.get("art_style", "unknown"),
            color_palette=visual_spec.get("color_palette", []),
            animation_quality=visual_spec.get("animation_quality", ""),
            vfx_notes=visual_spec.get("vfx_notes", []),
            ui_consistency=visual_spec.get("ui_consistency", ""),
        ),

        code_architecture=CodeArchitectureAnalysis(
            detected_patterns=data_spec.get("detected_patterns", []),
            folder_tree=folder_tree,
            recommended_stack=data_spec.get("recommended_stack", ""),
            code_snippets=code_spec.get("frontend_files", {}),
            data_models={
                "tables": data_spec.get("tables", []),
                "relationships": data_spec.get("relationships", []),
                "sql": data_spec.get("sql", ""),
            },
            api_contract=api_spec,
        ),

        performance=PerformanceAnalysis(
            scalability_class=perf_spec.get("scalability_class", "unknown"),
            optimization_notes=perf_spec.get("optimization_notes", []),
            estimated_monthly_cost=perf_spec.get("estimated_monthly_cost", {}),
            bottlenecks=perf_spec.get("bottlenecks", []),
        ),

        monetization=MonetizationAnalysis(
            detected_model=mono_spec.get("detected_model", "unknown"),
            iap_elements=mono_spec.get("iap_elements", []),
            market_fit_notes=mono_spec.get("market_fit_notes", []),
            revenue_potential=mono_spec.get("revenue_potential", ""),
        ),

        # Flat legacy fields
        data_models={"tables": data_spec.get("tables", [])},
        api_contract=api_spec,
        frontend_structure={
            "component_map": ui_spec.get("component_map", []),
            "layout_model": ui_spec.get("layout_model", {}),
        },
        backend_structure={
            "recommended_stack": data_spec.get("recommended_stack", ""),
            "scalability_class": perf_spec.get("scalability_class", ""),
        },
        folder_tree=folder_tree,
        code_snippets=code_spec,
        optimization_notes=perf_spec.get("optimization_notes", []),
    )
