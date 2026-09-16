from pathlib import Path

# root
PROJ_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = PROJ_ROOT / "data"
DOCS_DIR = PROJ_ROOT / "docs"
OUTPUTS_DIR = PROJ_ROOT / "outputs"
LOG_DIR = PROJ_ROOT / "logs"

# data/
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
SCREENSHOTS_DIR = RAW_DIR / "screenshots"
# initial scraped data from Victor
ASSETS_PATH = RAW_DIR / "campaign_asset.jsonl"

# other files
GLOSSARY_PATH = DATA_DIR / "glossary.json"