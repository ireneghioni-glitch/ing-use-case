"""
run_deterministic.py
====================
Run deterministic feature extraction on the cleaned asset manifest (`cleaned_asset.jsonl`).

Reads the cleaned assets produced by clean_html step and applies
the deterministic extraction functions (jargon_density, mean_sentence_length,
word_count) to each asset's cleaned text.

Output: data/features/deterministic.parquet
One row per (asset_id, feature_name).

Run: python -m src.run_deterministic
"""

import json
from pathlib import Path

import polars as pl

from src.config import PROCESSED_DIR, FEATURES_DIR
from src.schema import FeatureRecord
from src.extract_deterministic import (
    load_glossary,
    jargon_density,
    mean_sentence_length,
    word_count,
)


# --- Paths and Constants ---

INPUT_PATH = PROCESSED_DIR / "cleaned_assets.jsonl"
OUTPUT_PATH = FEATURES_DIR / "deterministic.parquet"

CODEBOOK_VERSION = "v1.0"
METHOD = "deterministic"

MVP_BANKS = {"ING", "KBC", "Belfius", "Revolut", "N26"}
BACKUP_TRAD = {"BNP Paribas Fortis"}
BACKUP_NEO = {"bunq"}
ALL_BACKUPS = BACKUP_TRAD | BACKUP_NEO


# --- Functions ---

def load_cleaned_assets(path: Path) -> list[dict]:
    """Load the cleaned assets JSONL into a list of dicts."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARN] Line {line_num}: invalid JSON — {e}")
    return records

def extract_features_for_asset(
    asset: dict,
    glossary: dict,
) -> list[FeatureRecord]:
    """
    Extract all deterministic features for one cleaned asset.

    Returns a list of FeatureRecord (one per feature).
    """
    asset_id = asset["asset_id"]
    language = asset.get("language", "fr")  # default fallback
    text = asset.get("text", "")

    # If cleaning flagged the asset as insufficient, still extract but
    # mark review_status accordingly. Downstream analysis can filter.
    review_status = "pending" if asset.get("cleaning_status") == "ok" else "flagged"

    features = []

    # 1. jargon_density
    features.append(FeatureRecord(
        asset_id=asset_id,
        feature_name="jargon_density",
        value=str(round(jargon_density(text, language, glossary), 4)),
        method=METHOD,
        codebook_version=CODEBOOK_VERSION,
        review_status=review_status,
    ))

    # 2. mean_sentence_length
    features.append(FeatureRecord(
        asset_id=asset_id,
        feature_name="mean_sentence_length",
        value=str(round(mean_sentence_length(text, language), 4)),
        method=METHOD,
        codebook_version=CODEBOOK_VERSION,
        review_status=review_status,
    ))

    # 3. word_count
    features.append(FeatureRecord(
        asset_id=asset_id,
        feature_name="word_count",
        value=str(word_count(text)),
        method=METHOD,
        codebook_version=CODEBOOK_VERSION,
        review_status=review_status,
    ))

    return features

def _scope_role(bank: str) -> str:
    """Classify a bank into mvp / backup / out_of_scope."""
    if bank in MVP_BANKS:
        return "mvp"
    if bank in ALL_BACKUPS:
        return "backup"
    return "out_of_scope"


def main() -> None:
    """Run deterministic extraction on all cleaned assets."""
    print(f"Loading cleaned assets: {INPUT_PATH}")
    assets = load_cleaned_assets(INPUT_PATH)
    print(f"Loaded {len(assets)} assets.")

    glossary = load_glossary()

    all_features: list[FeatureRecord] = []
    for i, asset in enumerate(assets, start=1):
        try:
            features = extract_features_for_asset(asset, glossary)
            all_features.extend(features)
        except Exception as e:
            asset_id = asset.get("asset_id", f"<index {i}>")
            print(f"[ERROR] Asset {asset_id}: {e}")

    print(f"Extracted {len(all_features)} feature records.")

    # Feature DataFrame
    features_df = pl.DataFrame([f.model_dump() for f in all_features])

    # Asset metadata DataFrame
    meta_rows = []
    for asset in assets:
        meta_rows.append({
            "asset_id": asset["asset_id"],
            "bank": asset.get("bank"),
            "audience_label": asset.get("audience_label"),
        })
    meta_df = pl.DataFrame(meta_rows)

    # Join
    df = features_df.join(meta_df, on="asset_id", how="left")

    # Derive scope_role (mvp / backup / out_of_scope) via Python mapping
    df = df.with_columns(
        pl.col("bank")
          .map_elements(_scope_role, return_dtype=pl.String)
          .alias("scope_role")
    )

    # Derive asset_role
    df = df.with_columns([
        pl.when(pl.col("audience_label") == "youth_18_25")
          .then(pl.lit("youth_landing"))
          .otherwise(pl.lit("out_of_scope"))
          .alias("asset_role"),
    ])

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUTPUT_PATH)
    print(f"Saved to: {OUTPUT_PATH}")

    # Summary
    print("\nFeature counts:")
    print(df.group_by("feature_name").len().sort("feature_name"))

    print("\nScope counts (unique assets):")
    print(
        df.unique(subset=["asset_id"])
          .group_by(["scope_role", "asset_role"])
          .len()
          .sort(["scope_role", "asset_role"])
    )


if __name__ == "__main__":
    main()