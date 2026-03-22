"""
Multi-agent analysis pipeline using Claude Vision API.
Each agent sends a targeted prompt and returns structured JSON.
"""

from __future__ import annotations

import json
import os
from typing import Any

from app.core.constants import CLAUDE_MODEL


def _call_claude(
    system_prompt: str,
    user_prompt: str,
    visual_parse: dict[str, Any],
) -> dict[str, Any]:
    """
    Call Claude Vision API with image/video frames.
    Returns parsed JSON dict from Claude's response.
    """
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed. Run: pip install anthropic"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY environment variable not set."}

    client = anthropic.Anthropic(api_key=api_key)

    # Build content blocks
    content: list[Any] = []

    if visual_parse.get("mode") == "image":
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": visual_parse.get("media_type", "image/jpeg"),
                "data": visual_parse.get("base64_data", ""),
            },
        })
    elif visual_parse.get("mode") == "video":
        for frame in visual_parse.get("frames", [])[:8]:  # max 8 frames per call
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": frame.get("media_type", "image/jpeg"),
                    "data": frame.get("base64_data", ""),
                },
            })
            content.append({
                "type": "text",
                "text": f"[Frame at {frame.get('timestamp_s', '?')} seconds]",
            })

    content.append({"type": "text", "text": user_prompt})

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": content}],
        )
        raw_text = response.content[0].text

        # Extract JSON block
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        return json.loads(raw_text)

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw": raw_text[:500]}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Agent 1: UI/UX Agent
# ---------------------------------------------------------------------------

UI_SYSTEM = """You are a senior game UI/UX analyst.
Analyze the provided screenshot(s) and return ONLY a JSON object — no markdown, no explanation.
Focus exclusively on user interface and UX elements in game context."""

UI_USER = """Analyze this game's UI/UX and return JSON with this exact structure:
{
  "component_map": ["list of UI components visible, e.g. health bar, minimap, inventory"],
  "layout_model": {"type": "HUD|Menu|Overlay|Loading", "zones": ["top-left: health", ...]},
  "design_tokens": {"primary_color": "#hex", "font_style": "...", "theme": "..."},
  "accessibility_issues": ["list any contrast/readability problems"],
  "hud_elements": ["health bar", "stamina", "minimap", "quest tracker", ...],
  "menu_structure": ["list menu items if visible"],
  "evidence": ["list what you can clearly see in the image"]
}"""


def ui_agent(visual_parse: dict[str, Any]) -> dict[str, Any]:
    result = _call_claude(UI_SYSTEM, UI_USER, visual_parse)
    if "error" in result:
        return {
            "component_map": [], "layout_model": {"type": "unknown"},
            "design_tokens": {}, "accessibility_issues": [],
            "hud_elements": [], "menu_structure": [],
            "evidence": [], "agent_error": result["error"],
        }
    return result


# ---------------------------------------------------------------------------
# Agent 2: Gameplay Agent
# ---------------------------------------------------------------------------

GAMEPLAY_SYSTEM = """You are an expert game designer and analyst.
Analyze the provided screenshot(s) and return ONLY a JSON object."""

GAMEPLAY_USER = """Analyze this game's gameplay and mechanics. Return JSON with this exact structure:
{
  "genre": "e.g. RPG, FPS, platformer, strategy, puzzle, mobile idle",
  "core_loop": "one sentence describing the main gameplay loop",
  "mechanics": ["list of visible game mechanics"],
  "player_actions": ["actions available to player based on UI/context"],
  "progression_system": "describe XP/level/skill tree/achievement system if visible",
  "difficulty_curve": "easy/medium/hard/unknown based on visible elements",
  "target_audience": "casual/core/hardcore/all-ages",
  "evidence": ["what you can clearly see that informs these conclusions"]
}"""


def gameplay_agent(visual_parse: dict[str, Any]) -> dict[str, Any]:
    result = _call_claude(GAMEPLAY_SYSTEM, GAMEPLAY_USER, visual_parse)
    if "error" in result:
        return {
            "genre": "unknown", "core_loop": "", "mechanics": [],
            "player_actions": [], "progression_system": "",
            "difficulty_curve": "unknown", "target_audience": "unknown",
            "evidence": [], "agent_error": result["error"],
        }
    return result


# ---------------------------------------------------------------------------
# Agent 3: Visual Design Agent
# ---------------------------------------------------------------------------

VISUAL_SYSTEM = """You are a senior game artist and visual director.
Analyze the provided screenshot(s) and return ONLY a JSON object."""

VISUAL_USER = """Analyze the visual design of this game. Return JSON with this exact structure:
{
  "art_style": "e.g. pixel art, 3D realistic, cel-shaded, low-poly, hand-drawn",
  "color_palette": ["#hex1", "#hex2", "describe dominant colors if hex unknown"],
  "animation_quality": "description of animation quality if visible",
  "vfx_notes": ["list visual effects you can see"],
  "ui_consistency": "rate UI visual consistency: high/medium/low with reason",
  "lighting_style": "dynamic/static/stylized/realistic",
  "overall_polish": "description of visual polish level",
  "evidence": ["what you can see that informs these conclusions"]
}"""


def visual_agent(visual_parse: dict[str, Any]) -> dict[str, Any]:
    result = _call_claude(VISUAL_SYSTEM, VISUAL_USER, visual_parse)
    if "error" in result:
        return {
            "art_style": "unknown", "color_palette": [],
            "animation_quality": "", "vfx_notes": [],
            "ui_consistency": "unknown", "lighting_style": "unknown",
            "overall_polish": "", "evidence": [], "agent_error": result["error"],
        }
    return result


# ---------------------------------------------------------------------------
# Agent 4: Data/Code Architecture Agent
# ---------------------------------------------------------------------------

DATA_SYSTEM = """You are a senior backend architect specializing in game systems.
Analyze what you can infer about the technical architecture from the UI/game elements visible.
Return ONLY a JSON object."""

DATA_USER = """Based on the visible game UI and mechanics, infer the likely technical architecture.
Return JSON with this exact structure:
{
  "tables": [
    {"name": "users", "fields": ["id", "username", "level", "xp"]},
    {"name": "items", "fields": ["id", "name", "type", "rarity"]}
  ],
  "relationships": ["users has_many items", "users has_one character"],
  "sql": "CREATE TABLE users (id SERIAL PRIMARY KEY, ...);",
  "recommended_stack": "e.g. Unity + Photon + Supabase, or Godot + FastAPI + PostgreSQL",
  "detected_patterns": ["observer pattern", "entity-component system", "state machine"],
  "api_endpoints": [
    {"method": "POST", "path": "/auth/login", "purpose": "player authentication"},
    {"method": "GET", "path": "/player/inventory", "purpose": "fetch inventory"}
  ],
  "evidence": ["game elements that inform these architecture choices"]
}"""


def data_agent(visual_parse: dict[str, Any]) -> dict[str, Any]:
    result = _call_claude(DATA_SYSTEM, DATA_USER, visual_parse)
    if "error" in result:
        return {
            "tables": [], "relationships": [],
            "sql": "-- Analysis unavailable",
            "recommended_stack": "unknown",
            "detected_patterns": [], "api_endpoints": [],
            "evidence": [], "agent_error": result["error"],
        }
    return result


def api_agent(data_spec: dict[str, Any]) -> dict[str, Any]:
    """Derives OpenAPI contract from data_agent output."""
    endpoints = data_spec.get("api_endpoints", [])
    paths: dict[str, Any] = {}
    for ep in endpoints:
        path = ep.get("path", "/unknown")
        method = ep.get("method", "GET").lower()
        paths[path] = {
            method: {
                "summary": ep.get("purpose", ""),
                "responses": {"200": {"description": "Success"}},
            }
        }

    return {
        "endpoints": endpoints,
        "openapi_yaml": f"openapi: 3.0.0\ninfo:\n  title: Game API\n  version: 1.0.0\npaths: {json.dumps(paths)}",
        "crud_mapping": {},
        "evidence": data_spec.get("evidence", []),
    }


# ---------------------------------------------------------------------------
# Agent 5: Performance Agent
# ---------------------------------------------------------------------------

def perf_agent(depth_level: int) -> dict[str, Any]:
    if depth_level < 3:
        return {
            "scalability_class": "unknown",
            "optimization_notes": ["Performance analysis enabled at depth_level=3."],
            "estimated_monthly_cost": {},
            "bottlenecks": [],
        }
    return {
        "scalability_class": "medium",
        "optimization_notes": [
            "Enable pagination for leaderboard / inventory endpoints.",
            "Cache player profile reads for 60 seconds (Redis).",
            "Add database indexes on player_id, created_at for event tables.",
            "Use CDN for static game assets (sprites, audio, shaders).",
            "Implement connection pooling for multiplayer sessions.",
        ],
        "estimated_monthly_cost": {"tier": "starter", "usd": 120},
        "bottlenecks": [
            "Real-time multiplayer sync under high concurrency",
            "Leaderboard queries without proper caching",
        ],
    }


# ---------------------------------------------------------------------------
# Agent 6: Monetization Agent
# ---------------------------------------------------------------------------

MONO_SYSTEM = """You are a mobile/PC game monetization expert.
Analyze the provided screenshot(s) and return ONLY a JSON object."""

MONO_USER = """Analyze the monetization model visible in this game. Return JSON with this exact structure:
{
  "detected_model": "f2p|premium|subscription|one-time-iap|unknown",
  "iap_elements": ["list any in-app purchase elements visible: shops, currencies, battle pass, etc."],
  "market_fit_notes": ["observations about market positioning"],
  "revenue_potential": "low|medium|high with brief explanation",
  "competitor_comparison": ["similar successful games in this genre/style"],
  "evidence": ["what in the UI/gameplay suggests this monetization model"]
}"""


def monetization_agent(visual_parse: dict[str, Any]) -> dict[str, Any]:
    result = _call_claude(MONO_SYSTEM, MONO_USER, visual_parse)
    if "error" in result:
        return {
            "detected_model": "unknown", "iap_elements": [],
            "market_fit_notes": [], "revenue_potential": "unknown",
            "competitor_comparison": [],
            "evidence": [], "agent_error": result["error"],
        }
    return result
