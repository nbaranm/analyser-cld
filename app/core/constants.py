"""Project-wide constants for deterministic V2T output."""

OUTPUT_FLAG_STRUCTURAL_AMBIGUITY = "Structural ambiguity detected."
MAX_VIDEO_SECONDS = 60
MAX_IMAGE_EDGE = 1024
DEFAULT_MEDIA_TTL_HOURS = 24

SUPPORTED_MODES = {"image", "video"}
SUPPORTED_DEPTHS = {1, 2, 3}

# Anthropic model to use for vision analysis
CLAUDE_MODEL = "claude-opus-4-5"

# Game analysis categories
GAME_ANALYSIS_CATEGORIES = [
    "ui_ux",
    "gameplay_mechanics",
    "visual_design",
    "code_architecture",
    "performance",
    "monetization",
]

DEFAULT_FOLDER_TREE = """/frontend
  /components
  /pages
  /hooks
  /styles
  /utils
/backend
  /api
  /models
  /schemas
  /services
  main.py
"""

STACK_FOLDER_TREES = {
    "nextjs-fastapi": DEFAULT_FOLDER_TREE,
    "react-node": """/frontend
  /src/components
  /src/pages
  /src/hooks
  /src/styles
/backend
  /src/routes
  /src/models
  /src/services
  server.js
""",
    "unity": """/Assets
  /Scripts
    /Core
    /UI
    /Gameplay
    /Networking
  /Scenes
  /Prefabs
  /Materials
  /Audio
/Packages
ProjectSettings/
""",
    "unreal": """/Source
  /Core
  /UI
  /Gameplay
  /Characters
Content/
  /Blueprints
  /Materials
  /Meshes
  /Audio
Config/
""",
    "godot": """/scenes
  /ui
  /gameplay
  /characters
/scripts
  /core
  /ui
  /gameplay
/assets
  /sprites
  /audio
  /shaders
project.godot
""",
    "django": """/frontend
  /components
  /pages
/backend
  /project
  /apps
  manage.py
""",
    "supabase": """/frontend
  /components
  /pages
/supabase
  /functions
  /migrations
""",
    "cloudflare-workers": """/frontend
  /components
  /pages
/backend
  /workers
  wrangler.toml
""",
}
