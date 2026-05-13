# --------------------------------------------------------------------
# Purpose: Define all paths used in the project.
# Best practice: Single responsibility. This file only manages paths.
# ---------------------------------------------------------------------

from pathlib import Path

BASE_PATH = Path(__file__).parents[1]
ASSETS_PATH = BASE_PATH / "assets"
IMAGE_PATH = ASSETS_PATH / "image"
STYLES_PATH = ASSETS_PATH / "style"
MARKDOWN_PATH = ASSETS_PATH / "markdown"
DATA_PATH = (ASSETS_PATH / "data") 
COMPONENTS_PATH = BASE_PATH / "components"
