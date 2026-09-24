"""
annotate_validation.py
======================
Interactive CLI to label the 10-record validation sample.

Reads:  data/validation/sample_ids.csv
        data/features/all_features.parquet
Writes: data/validation/irene_labels.csv (appends after each record)

Opens each screenshot in the system image viewer, prints the text,
and prompts for the 3 values. Resumable: skips records already labeled.

Run: python -m src.annotate_validation
"""

import os
import sys
from pathlib import Path

import polars as pl

from src.config import FEATURES_DIR, DATA_DIR, SCREENSHOTS_DIR, VALIDATION_DIR, PROJ_ROOT


SAMPLE_PATH = VALIDATION_DIR / "sample_ids.csv"
LABELS_PATH = VALIDATION_DIR / "irene_labels.csv"
PARQUET_PATH = FEATURES_DIR / "all_features.parquet"

FEATURES = {
    "main_benefit": [
        "affordability", "convenience", "independence-control",
        "security-support", "lifestyle-rewards", "other", "mixed", "unknown",
    ],
    "tone": ["formal", "persuasive", "simple", "playful"],
    "visual_type": ["real-people", "illustration", "product-shot", "abstract", "none"],
}


def load_done_ids() -> set[str]:
    """Return asset_ids already present in irene_labels.csv."""
    if not LABELS_PATH.is_file():
        return set()
    done = set()
    with LABELS_PATH.open("r", encoding="utf-8") as f:
        next(f, None)  # skip header
        for line in f:
            line = line.strip()
            if line:
                done.add(line.split(",")[0])
    return done


def ensure_labels_file() -> None:
    """Create the labels file with a header if it does not exist."""
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LABELS_PATH.is_file():
        LABELS_PATH.write_text("asset_id,feature_name,value\n", encoding="utf-8")


def append_rows(asset_id: str, values: dict[str, str]) -> None:
    with LABELS_PATH.open("a", encoding="utf-8") as f:
        for feature, value in values.items():
            f.write(f"{asset_id},{feature},{value}\n")


def prompt_value(feature: str, allowed: list[str]) -> str:
    """Ask the user for a value, validating against the allowed list."""
    allowed_str = " / ".join(allowed)
    while True:
        choice = input(f"  {feature} [{allowed_str}]: ").strip().lower()
        if choice in allowed:
            return choice
        print(f"    ✗ Invalid. Choose one of: {allowed_str}")


def open_screenshot(path: str) -> None:
    """Open the screenshot with the OS default viewer."""
    p = Path(path)
    if not p.is_absolute():
        p = PROJ_ROOT / p
    if p.is_file():
        os.startfile(str(p))  # Windows only
    else:
        print(f"    ⚠ Screenshot not found: {p}")


def main() -> None:
    ensure_labels_file()

    if not SAMPLE_PATH.is_file():
        print(f"Sample file not found: {SAMPLE_PATH}")
        sys.exit(1)

    sample = pl.read_csv(SAMPLE_PATH)
    full = pl.read_parquet(PARQUET_PATH)

    done = load_done_ids()
    todo = sample.filter(~pl.col("asset_id").is_in(list(done)))

    print(f"Total in sample: {len(sample)}")
    print(f"Already labeled: {len(done)}")
    print(f"Remaining: {len(todo)}\n")

    if len(todo) == 0:
        print("Nothing to do. All records are labeled.")
        return

    for i, row in enumerate(todo.iter_rows(named=True), start=1):
        asset_id = row["asset_id"]
        bank = row["bank"]

        match = full.filter(pl.col("asset_id") == asset_id)
        if match.is_empty():
            print(f"[{i}] {asset_id} — NOT FOUND in all_features.parquet. Skipping.")
            continue

        record = match.row(0, named=True)
        text = (record.get("text") or "")[:1500]
        screenshot = record.get("screenshot_path") or ""

        print("=" * 80)
        print(f"[{i}/{len(todo)}] {bank}  —  {asset_id}")
        print("=" * 80)
        print(f"\nText (truncated to 1500 chars):\n{text}\n")
        print(f"Screenshot: {screenshot}")
        open_screenshot(screenshot)
        print()

        values = {}
        for feature, allowed in FEATURES.items():
            values[feature] = prompt_value(feature, allowed)

        append_rows(asset_id, values)
        print(f"  ✓ Saved. Progress: {len(done) + i}/{len(sample)}\n")

    print("\nDone. All labels written to:")
    print(f"  {LABELS_PATH}")


if __name__ == "__main__":
    main()