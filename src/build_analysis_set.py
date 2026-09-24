"""
build_analysis_set.py
=====================
Build the POC analysis set from the full deterministic feature file.

Reads:  data/features/deterministic.parquet  (all 292 assets, long format)
Writes: data/features/analysis_set.parquet   (~50 assets, MVP youth only)

Filtering policy:
  - Keep only scope_role == "mvp" (excludes Argenta, Beobank, BNP, bunq)
  - Keep only audience_label == "youth_18_25"
  - Cap at TARGET_YOUTH_PER_BANK per bank, stratified by language
    (round-robin between fr / nl / en to balance language coverage)

The selection is deterministic: assets are picked in sorted asset_id order
within each language, so re-running the script produces the same set.

Run: python -m src.build_analysis_set
"""

from collections import defaultdict
from pathlib import Path

import polars as pl

from src.config import FEATURES_DIR, DOCS_DIR, PROCESSED_DIR
from src.scope import MVP_BANKS, TARGET_YOUTH_PER_BANK


# --- Paths ---

INPUT_PATH = FEATURES_DIR / "deterministic.parquet"
OUTPUT_PATH = FEATURES_DIR / "analysis_set_deterministic.parquet"
REPORT_PATH = DOCS_DIR / "analysis_set_report.md"
CLEANED_PATH = PROCESSED_DIR / "cleaned_assets.jsonl"
LLM_PATH = FEATURES_DIR / "llm_claude.parquet"


# --- Functions ---

def pick_capped_by_language(
    candidates: list[dict],
    cap: int,
) -> list[str]:
    """
    Pick up to `cap` asset_ids from candidates, balancing languages.

    Candidates must be dicts with keys 'asset_id' and 'language'.
    Round-robin between languages, in sorted order, until the cap is reached
    or all languages are exhausted. Deterministic: for a given input, always
    produces the same output.
    """
    by_lang: dict[str, list[str]] = defaultdict(list)

    for c in candidates:
        by_lang[c["language"]].append(c["asset_id"])

    # Sort each language group deterministically
    for lang in by_lang:
        by_lang[lang].sort()

    picked: list[str] = []
    # Round-robin between languages
    while len(picked) < cap:
        progress = False
        for lang in sorted(by_lang.keys()):
            if by_lang[lang] and len(picked) < cap:
                picked.append(by_lang[lang].pop(0))
                progress = True
        if not progress:
            break  # all languages exhausted

    return picked

def load_unique_assets(df: pl.DataFrame) -> pl.DataFrame:
    """
    From the long-format feature DataFrame, extract one row per asset
    with the metadata columns we need for filtering.
    """
    return df.unique(subset=["asset_id"]).select([
        "asset_id",
        "bank",
        "language",
        "audience_label",
        "scope_role",
        "asset_role",
    ])

def write_report(
    total_assets: int,
    mvp_youth_assets: int,
    per_bank: dict[str, dict],
    selected_ids: list[str],
    analysis_df: pl.DataFrame,
) -> None:
    """Write a markdown report explaining the analysis set build."""
    lines = [
        "# Analysis Set Build Report",
        "",
        f"**Input:** `{INPUT_PATH.as_posix()}`  ",
        f"**Output:** `{OUTPUT_PATH.as_posix()}`  ",
        f"**Cap per bank:** {TARGET_YOUTH_PER_BANK} youth records  ",
        f"**Selection:** deterministic, stratified by language (round-robin)",
        "",
        "## 1. Funnel",
        "",
        "| Stage | Assets |",
        "|---|---:|",
        f"| Full manifest (all assets) | {total_assets} |",
        f"| MVP + youth only | {mvp_youth_assets} |",
        f"| Final analysis set | {len(selected_ids)} |",
        "",
        "## 2. Per-bank selection",
        "",
        "| Bank | Available | Picked | Language split | Health |",
        "|---|---:|---:|---|---|",
    ]

    for bank in sorted(per_bank.keys()):
        info = per_bank[bank]
        lang_split = ", ".join(
            f"{lang}: {count}" for lang, count in sorted(info["lang_split"].items())
        ) or "-"
        lines.append(
            f"| {bank} | {info['available']} | {info['picked']} | {lang_split} | {info['health']} |"
        )

    lines.extend([
        "",
        "## 3. Feature rows in output",
        "",
        "| Feature | Rows |",
        "|---|---:|",
    ])
    feature_counts = (
        analysis_df.group_by("feature_name").len().sort("feature_name")
    )
    for row in feature_counts.iter_rows(named=True):
        lines.append(f"| {row['feature_name']} | {row['len']} |")

    lines.extend([
        "",
        "## 4. Assets per bank × language in output",
        "",
        "| Bank | Language | Assets |",
        "|---|---|---:|",
    ])
    lang_counts = (
        analysis_df.unique(subset=["asset_id"])
        .group_by(["bank", "language"])
        .len()
        .sort(["bank", "language"])
    )
    for row in lang_counts.iter_rows(named=True):
        lines.append(f"| {row['bank']} | {row['language']} | {row['len']} |")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport written to: {REPORT_PATH}")

# --- Error page detection ---

ERROR_PATTERNS = (
    "page not found",
    "pagina niet gevonden",
    "pagina niet beschikbaar",
    "page non trouvée",
    "page introuvable",
    "seite nicht gefunden",
    "404 not found",
    "404 error",
    "error 404",
    "404 - page",
    "404 page",
)

MIN_WORDS_FOR_HEALTHY = 100


def load_healthy_ids(cleaned_path: Path) -> set[str]:
    df = pl.read_ndjson(cleaned_path).select(["asset_id", "text"])
    healthy: set[str] = set()

    for row in df.iter_rows(named=True):
        text = (row["text"] or "").lower()
        word_count = len(text.split())

        # Too short → unhealthy
        if word_count < MIN_WORDS_FOR_HEALTHY:
            continue

        # Specific error signature → unhealthy, regardless of length.
        # A 404 page can have many words (header, nav, footer), but its
        # body still contains an explicit "page not found" signature.
        if any(p in text for p in ERROR_PATTERNS):
            continue

        healthy.add(row["asset_id"])

    return healthy

def load_unhealthy_from_llm(llm_path: Path) -> set[str]:
    """
    Return asset_ids whose LLM topics field flags them as error pages.
    The LLM (vision) detected errors that the text-extraction missed.
    """
    if not llm_path.is_file():
        return set()

    df = pl.read_parquet(llm_path).select(["asset_id", "topics"])
    unhealthy: set[str] = set()

    bad_keywords = ("page not found", "error", "404", "pagina niet gevonden",
                    "page non trouvée", "not found")

    for row in df.iter_rows(named=True):
        topics = str(row["topics"] or "").lower()
        if any(k in topics for k in bad_keywords):
            unhealthy.add(row["asset_id"])

    return unhealthy

def main() -> None:
    """Build the analysis set and save it."""
    print(f"Loading: {INPUT_PATH}")
    df = pl.read_parquet(INPUT_PATH)
    print(f"Loaded {len(df)} feature rows.")

    assets = load_unique_assets(df)
    print(f"Unique assets: {len(assets)}")

    # Filter to MVP + youth only
    healthy_ids = load_healthy_ids(CLEANED_PATH)
    unhealthy_from_llm = load_unhealthy_from_llm(LLM_PATH)
    print(f"Unhealthy per LLM topics: {len(unhealthy_from_llm)}")
    print(f"Healthy records (after error filter): {len(healthy_ids)}")

    mvp_youth = assets.filter(
        (pl.col("scope_role") == "mvp")
        & (pl.col("audience_label") == "youth_18_25")
        & (pl.col("asset_id").is_in(list(healthy_ids)))
        & (~pl.col("asset_id").is_in(list(unhealthy_from_llm)))
    )
    print(f"MVP youth assets: {len(mvp_youth)}")

    # --- Cap per bank, stratified by language ---
    selected_ids: list[str] = []
    per_bank: dict[str, dict] = {}


    for bank in sorted(MVP_BANKS):
        bank_rows = mvp_youth.filter(pl.col("bank") == bank)
        candidates = bank_rows.select(["asset_id", "language"]).to_dicts()

        picked = pick_capped_by_language(candidates, cap=TARGET_YOUTH_PER_BANK)
        selected_ids.extend(picked)

        # Language split of what was actually picked (for the report)
        picked_rows = bank_rows.filter(pl.col("asset_id").is_in(picked))
        lang_split = picked_rows.group_by("language").len().to_dicts()
        lang_split_dict = {r["language"]: r["len"] for r in lang_split}

        health = (
            "healthy" if len(picked) >= 5
            else "weak" if len(picked) >= 3
            else "unhealthy"
        )

        per_bank[bank] = {
            "available": len(bank_rows),
            "picked": len(picked),
            "lang_split": lang_split_dict,
            "health": health,
        }

        print(f"  {bank}: {len(bank_rows)} available → picked {len(picked)} [{health}]")

    print(f"\nTotal selected assets: {len(selected_ids)}")

    # --- Filter the full long-format DataFrame to the selected assets ---
    analysis_df = df.filter(pl.col("asset_id").is_in(selected_ids))

    # --- Save ---
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    analysis_df.write_parquet(OUTPUT_PATH)
    print(f"Saved to: {OUTPUT_PATH}")

    # --- Summary to console ---
    print("\nFeature counts in analysis set:")
    print(analysis_df.group_by("feature_name").len().sort("feature_name"))

    # --- Write markdown report ---
    write_report(
        total_assets=len(assets),
        mvp_youth_assets=len(mvp_youth),
        per_bank=per_bank,
        selected_ids=selected_ids,
        analysis_df=analysis_df,
    ) 


if __name__ == "__main__":
    main()