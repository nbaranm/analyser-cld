"""Multi-agent analysis using Claude API with web search."""
from __future__ import annotations
import json
import os
from typing import Any

CLAUDE_MODEL = "claude-opus-4-5"


def _call_claude(system: str, prompt: str, visual: dict | None = None,
                 web_search: bool = False, max_tokens: int = 4096) -> dict:
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic not installed"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}

    client = anthropic.Anthropic(api_key=api_key)
    content: list = []

    if visual:
        if visual.get("mode") == "image" and visual.get("base64_data"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": visual.get("media_type", "image/jpeg"),
                    "data": visual["base64_data"],
                },
            })
        elif visual.get("mode") == "video":
            for frame in visual.get("frames", [])[:5]:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": frame.get("media_type", "image/jpeg"),
                        "data": frame["base64_data"],
                    },
                })

    content.append({"type": "text", "text": prompt})

    kwargs: dict = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": content}],
    }
    if web_search:
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    try:
        response = client.messages.create(**kwargs)
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text

        # Extract JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        return json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"error": str(e)}


SYSTEM_PROMPT = """You are a senior game industry analyst with 15+ years of experience.
Analyze games using web search to find REAL data. Return ONLY valid JSON."""


def run_full_analysis(store_url, visual_parse, genre, mono_model, platform, depth_level):
    """Main entry point. Returns complete analysis dict."""

    if store_url and store_url.strip():
        result = _analyze_store_url(store_url.strip(), genre, mono_model, platform, depth_level)
        if visual_parse and not visual_parse.get("error"):
            vision = _analyze_visual(visual_parse, genre, mono_model)
            if not vision.get("error"):
                result["vision_data"] = vision
        return result

    if visual_parse and not visual_parse.get("error"):
        return _analyze_visual_only(visual_parse, genre, mono_model)

    return {"error": "No input provided"}


def _analyze_store_url(url, genre, mono, platform, depth):
    prompt = f"""Search the web and analyze this game:
URL: {url}
Genre: {genre} | Monetization: {mono} | Platform: {platform}

Search for: store page, review scores, player counts, SteamSpy data, competitor games.
Use REAL data you find. Return this EXACT JSON:

{{
  "game_title": "real name",
  "platform": "{platform}",
  "monetization": "{mono}",
  "confidence": 82,
  "sections": {{
    "ui_ux": {{
      "score": 65,
      "metrics": [
        {{"label": "Store Screenshots", "value": "X screenshots found", "flag": "ok", "desc": "store page quality"}},
        {{"label": "Visual Style", "value": "description", "flag": "ok", "desc": "art style"}},
        {{"label": "UI Complexity", "value": "Low/Medium/High", "flag": "ok", "desc": "based on genre"}},
        {{"label": "Accessibility", "value": "assessment", "flag": "warn", "desc": "standard check"}},
        {{"label": "Screenshot Quality", "value": "assessment", "flag": "ok", "desc": "marketing materials"}}
      ],
      "summary": "2-3 sentences based on findings"
    }},
    "game_ux": {{
      "score": 70,
      "metrics": [
        {{"label": "Tutorial Complaints", "value": "X% mention issues", "flag": "ok", "desc": "from reviews"}},
        {{"label": "Difficulty Feedback", "value": "X% complaints", "flag": "ok", "desc": "from reviews"}},
        {{"label": "Core Loop", "value": "description from reviews", "flag": "ok", "desc": "what players do"}},
        {{"label": "FTUE Quality", "value": "assessment", "flag": "ok", "desc": "first hour experience"}},
        {{"label": "Session Length", "value": "X min typical", "flag": "ok", "desc": "genre estimate"}}
      ],
      "summary": "2-3 sentences from review analysis"
    }},
    "marketing": {{
      "score": 75,
      "metrics": [
        {{"label": "Review Score", "value": "X% positive or X/10", "flag": "ok", "desc": "actual store score"}},
        {{"label": "Review Count", "value": "X reviews", "flag": "ok", "desc": "total volume"}},
        {{"label": "Recent Sentiment", "value": "X% positive recent", "flag": "ok", "desc": "recent reviews"}},
        {{"label": "Description Quality", "value": "assessment", "flag": "ok", "desc": "USP clarity"}},
        {{"label": "Store Media", "value": "X videos/screenshots", "flag": "ok", "desc": "media count"}}
      ],
      "summary": "2-3 sentences on marketing"
    }},
    "monetization": {{
      "score": 60,
      "metrics": [
        {{"label": "Price", "value": "$X or Free", "flag": "ok", "desc": "current price"}},
        {{"label": "DLC Count", "value": "X items", "flag": "ok", "desc": "from store"}},
        {{"label": "P2W Complaints", "value": "X%", "flag": "ok", "desc": "from negative reviews"}},
        {{"label": "Price vs Genre", "value": "+/-X%", "flag": "ok", "desc": "vs similar games"}},
        {{"label": "Revenue Model", "value": "assessment", "flag": "ok", "desc": "model effectiveness"}}
      ],
      "summary": "2-3 sentences on monetization"
    }},
    "performance": {{
      "score": 65,
      "metrics": [
        {{"label": "Owner Estimate", "value": "X-Y copies", "flag": "ok", "desc": "SteamSpy estimate"}},
        {{"label": "Peak CCU", "value": "X players", "flag": "ok", "desc": "all-time peak"}},
        {{"label": "Current CCU", "value": "X players", "flag": "ok", "desc": "recent count"}},
        {{"label": "Performance Issues", "value": "X% complaints", "flag": "ok", "desc": "bug reviews"}},
        {{"label": "Update Activity", "value": "assessment", "flag": "ok", "desc": "developer cadence"}}
      ],
      "summary": "2-3 sentences on performance"
    }},
    "retention": {{
      "score": 70,
      "metrics": [
        {{"label": "Overall Sentiment", "value": "X% positive", "flag": "ok", "desc": "total reviews"}},
        {{"label": "Hours Played", "value": "X hours avg", "flag": "ok", "desc": "HowLongToBeat or reviews"}},
        {{"label": "Endgame Content", "value": "assessment", "flag": "ok", "desc": "depth from reviews"}},
        {{"label": "Replayability", "value": "Low/Medium/High", "flag": "ok", "desc": "from reviews"}},
        {{"label": "Community", "value": "assessment", "flag": "ok", "desc": "forum activity"}}
      ],
      "summary": "2-3 sentences on retention"
    }},
    "strategy": {{
      "score": 65,
      "metrics": [
        {{"label": "Top Competitor 1", "value": "Game: X score", "flag": "ok", "desc": "direct competitor"}},
        {{"label": "Top Competitor 2", "value": "Game: X score", "flag": "ok", "desc": "direct competitor"}},
        {{"label": "Top Competitor 3", "value": "Game: X score", "flag": "ok", "desc": "direct competitor"}},
        {{"label": "Genre Size", "value": "assessment", "flag": "ok", "desc": "market size"}},
        {{"label": "Differentiator", "value": "what's unique", "flag": "ok", "desc": "competitive edge"}}
      ],
      "summary": "2-3 sentences on competitive position"
    }}
  }},
  "action_plan": [
    {{"priority": 1, "issue": "REAL issue found", "action": "SPECIFIC fix with expected outcome", "impact": "high"}},
    {{"priority": 2, "issue": "REAL issue", "action": "SPECIFIC action", "impact": "high"}},
    {{"priority": 3, "issue": "REAL issue", "action": "SPECIFIC action", "impact": "medium"}},
    {{"priority": 4, "issue": "REAL issue", "action": "SPECIFIC action", "impact": "medium"}},
    {{"priority": 5, "issue": "REAL issue", "action": "SPECIFIC action", "impact": "medium"}},
    {{"priority": 6, "issue": "REAL issue", "action": "SPECIFIC action", "impact": "low"}},
    {{"priority": 7, "issue": "REAL issue", "action": "SPECIFIC action", "impact": "low"}},
    {{"priority": 8, "issue": "REAL issue", "action": "SPECIFIC action", "impact": "low"}}
  ],
  "benchmarks": [
    {{"metric": "Review Score", "you": "X", "bench": "genre avg", "diff": "+/-X", "status": "good"}},
    {{"metric": "Review Volume", "you": "X", "bench": "top 10 avg", "diff": "vs bench", "status": "good"}},
    {{"metric": "Price", "you": "$X", "bench": "genre median", "diff": "+/-X%", "status": "good"}},
    {{"metric": "Owner Est.", "you": "X-Y", "bench": "similar games", "diff": "comparison", "status": "mid"}},
    {{"metric": "CCU Peak", "you": "X", "bench": "top competitor", "diff": "comparison", "status": "mid"}}
  ],
  "roadmap": {{
    "d30": ["action 1", "action 2", "action 3", "action 4", "action 5"],
    "d60": ["action 1", "action 2", "action 3", "action 4", "action 5"],
    "d90": ["action 1", "action 2", "action 3", "action 4", "action 5"]
  }},
  "roi": {{
    "current_review_score": "X/100",
    "target_review_score": "X/100 after fixes",
    "estimated_owner_increase": "+X% with improvements",
    "priority_fix_roi": "top action and expected return"
  }}
}}"""

    result = _call_claude(SYSTEM_PROMPT, prompt, web_search=True, max_tokens=8000)
    if "error" in result:
        return _fallback_result(url, genre, mono, result["error"])
    return result


def _analyze_visual(visual, genre, mono):
    prompt = f"""Analyze these game screenshots. Genre: {genre} | Monetization: {mono}
Return ONLY this JSON based on what you see:
{{
  "ui_clarity": "Low/Medium/High",
  "hud_elements": ["list visible"],
  "core_loop": "one sentence",
  "polish": "Low/Medium/High",
  "issues": ["specific issues"],
  "action_items": ["fix 1", "fix 2", "fix 3"]
}}"""
    return _call_claude("You are a game UI analyst. Return ONLY JSON.", prompt, visual=visual, max_tokens=2000)


def _analyze_visual_only(visual, genre, mono):
    vision = _analyze_visual(visual, genre, mono)
    q2s = lambda q: {"High": 80, "Medium": 60, "Low": 35}.get(str(q), 50)
    score = q2s(vision.get("polish", "Medium"))
    actions = [{"priority": i+1, "issue": "Visual finding", "action": a, "impact": "medium"}
               for i, a in enumerate(vision.get("action_items", []))]
    return {
        "game_title": "Game (Visual Analysis)",
        "platform": "Unknown",
        "monetization": mono,
        "confidence": 55,
        "sections": {
            "ui_ux": {"score": q2s(vision.get("ui_clarity", "Medium")),
                      "metrics": [{"label": "UI Clarity", "value": vision.get("ui_clarity", "?"), "flag": "ok", "desc": "from screenshot"},
                                  {"label": "HUD Elements", "value": str(len(vision.get("hud_elements", []))), "flag": "ok", "desc": str(vision.get("hud_elements", []))}],
                      "summary": "Visual analysis only. Add store URL for full report."},
            "game_ux": {"score": score, "metrics": [{"label": "Core Loop", "value": vision.get("core_loop", "?"), "flag": "ok", "desc": "inferred"}], "summary": ""},
            "marketing": {"score": 50, "metrics": [], "summary": "Add store URL for marketing data."},
            "monetization": {"score": 50, "metrics": [], "summary": "Add store URL for monetization data."},
            "performance": {"score": 50, "metrics": [], "summary": "Add store URL for performance data."},
            "retention": {"score": 50, "metrics": [], "summary": "Add store URL for retention data."},
            "strategy": {"score": 50, "metrics": [], "summary": "Add store URL for competitive analysis."},
        },
        "action_plan": actions,
        "benchmarks": [],
        "roadmap": {"d30": ["Add store URL for full analysis"], "d60": [], "d90": []},
        "roi": {"current_review_score": "N/A", "target_review_score": "N/A",
                "estimated_owner_increase": "N/A", "priority_fix_roi": "Add store URL for ROI analysis"},
    }


def _fallback_result(url, genre, mono, error):
    return {
        "game_title": url,
        "platform": "Unknown",
        "monetization": mono,
        "confidence": 20,
        "error_detail": error,
        "sections": {k: {"score": 50, "metrics": [], "summary": f"Analysis failed: {error}"}
                     for k in ["ui_ux", "game_ux", "marketing", "monetization", "performance", "retention", "strategy"]},
        "action_plan": [],
        "benchmarks": [],
        "roadmap": {"d30": [], "d60": [], "d90": []},
        "roi": {"current_review_score": "N/A", "target_review_score": "N/A",
                "estimated_owner_increase": "N/A", "priority_fix_roi": "N/A"},
    }


# Legacy compatibility
def ui_agent(v): return {}
def gameplay_agent(v): return {}
def visual_agent(v): return {}
def data_agent(v): return {}
def api_agent(v): return {}
def perf_agent(d): return {}
def monetization_agent(v): return {}
