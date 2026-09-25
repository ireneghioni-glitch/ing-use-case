"""
Shared constants for the ING Youth Acquisition Communication Comparator.
Reflects the confirmed scope (scope.md, 2026-09-21).
"""

from pathlib import Path

# --- Scope: the 5 MVP banks + their configured backups ---
MVP_BANKS = ["ING", "N26","KBC","Revolut", "Belfius" ]

BACKUP_BANKS = {
    "traditional": {"bank": "BNP Paribas Fortis", "activates_if": ["KBC", "Belfius"]},
    "digital": {"bank": "bunq", "activates_if": ["Revolut", "N26"]},
}

BANK_TYPE = {
    "ING": "traditional",
    "KBC": "traditional",
    "Belfius": "traditional",
    "Revolut": "digital challenger",
    "N26": "digital challenger",
    "BNP Paribas Fortis": "traditional",
    "bunq": "digital challenger",
    # Out-of-scope banks present in the corpus from an earlier scraping iteration.
    "Argenta": "traditional",
    "Beobank": "traditional",
}

BANK_TYPE_LABEL = {
    "traditional": "Traditional bank",
    "digital challenger": "Digital challenger",
}

SUBJECT_BANK = "ING"

# --- Coverage rule (scope.md) ---
TARGET_RECORDS_PER_BANK = 10
MIN_VIABLE_RECORDS_PER_BANK = 5
AUDIENCE_LABEL = "youth_18_25"

# --- Data sources ---
# ASSUMPTION: adjust these paths if your pipeline writes elsewhere.
DATA_DIR = Path("data")
FEATURES_PATH = DATA_DIR / "features" / "llm_claude.parquet"
DETERMINISTIC_FEATURES_PATH = DATA_DIR / "features" / "deterministic.parquet"
CLEANED_ASSETS_PATH = DATA_DIR / "processed" / "cleaned_assets.jsonl"
MANUAL_ANNOTATIONS_PATH = DATA_DIR / "features" / "visual_manual.csv"

# --- Out of scope (shown on the Scope & Methodology page so it's never ambiguous) ---
OUT_OF_SCOPE = [ 
    "Within-bank youth vs adult comparison (excluded from the MVP by team decision, 2026-09-21).",
    "Conversion, ROI, or sales impact measurement — no internal performance data available.",
    "Ad-platform analysis — this MVP covers bank websites only.",
]