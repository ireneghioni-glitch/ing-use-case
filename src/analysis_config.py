"""Configuration for the validated final analysis."""

from src.config import DATA_DIR, FEATURES_DIR, PROJ_ROOT


ANALYSIS_DIR = DATA_DIR / "analysis"
FIGURES_DIR = PROJ_ROOT / "reports" / "figures"

ALL_FEATURES_PATH = FEATURES_DIR / "all_features.parquet"
FINAL_SOURCE_QUALITY_PATH = ANALYSIS_DIR / "final_source_quality.csv"
FINAL_VISUAL_DISTRIBUTION_PATH = (
    ANALYSIS_DIR / "final_visual_type_distribution.csv"
)

FINAL_CATEGORICAL_FEATURES = ["visual_type"]
FINAL_DETERMINISTIC_FEATURES = [
    "jargon_density",
    "mean_sentence_length",
    "word_count",
]

VALIDATION_RESULTS = {
    "visual_type": {
        "kappa": 0.841,
        "decision": "keep",
        "analysis_use": "quantitative",
    },
    "main_benefit": {
        "kappa": 0.101,
        "decision": "drop",
        "analysis_use": "descriptive_only",
    },
    "tone": {
        "kappa": -0.125,
        "decision": "drop",
        "analysis_use": "descriptive_only",
    },
}

BANK_ORDER = ["ING", "KBC", "Belfius", "N26", "Revolut"]

EXPECTED_BANK_COUNTS = {
    "ING": 10,
    "KBC": 10,
    "Belfius": 5,
    "N26": 5,
    "Revolut": 5,
}

CATEGORY_ORDER = {
    "visual_type": [
        "real-people",
        "product-shot",
        "abstract",
        "none",
    ],
}

FINAL_VALIDATION_NOTE = (
    "Final quantitative analysis uses validated visual_type. "
    "Deterministic text features are audited for source quality and excluded "
    "from cross-bank conclusions."
)
