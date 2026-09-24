"""
merge_features.py
=================
Merge all feature sources into a single wide table.

Sources (all optional except analysis_set):
  - data/features/analysis_set.parquet   (deterministic, always present)
  - data/features/llm.parquet            (textual - ai assisted)
  - data/features/visual_manual.csv      (ai assisted)

Output:
  - data/features/all_features.parquet   (wide: one row per asset, one column per feature)
  - docs/merge_report.md

Run: python -m src.merge_features
"""

from pathlib import Path

import polars as pl

from src.config import FEATURES_DIR, DOCS_DIR, PROCESSED_DIR


# --- Paths ---

DETERMINISTIC_PATH = FEATURES_DIR / "analysis_set_deterministic.parquet"
LLM_PATH = FEATURES_DIR / "llm_claude.parquet"
VISUAL_PATH = FEATURES_DIR / "visual_manual.csv"
OUTPUT_PATH = FEATURES_DIR / "all_features.parquet"
REPORT_PATH = DOCS_DIR / "merge_report.md"
CLEANED_PATH = PROCESSED_DIR / "cleaned_assets.jsonl"


# --- Constants ---

METADATA_COLS = ["bank", "language", "audience_label", "scope_role", "asset_role"]


# --- Functions ---

# helper
def _to_string(df, col_name: str) -> pl.Expr:
        dtype = df.schema[col_name]
        if isinstance(dtype, pl.List):
            return pl.col(col_name).list.join("|").alias(col_name)
        if isinstance(dtype, pl.Struct):
            return pl.col(col_name).struct.json_encode().alias(col_name)
        return pl.col(col_name).cast(pl.String).alias(col_name)

def load_source(path: Path, source_name: str) -> pl.DataFrame | None:
    """
    Load a feature source. Returns None if the file does not exist.
    Prints a clear message either way.
    """
    if not path.is_file():
        print(f"[SKIP] {source_name} not found: {path}")
        return None

    if path.suffix == ".parquet":
        df = pl.read_parquet(path)
    elif path.suffix == ".csv":
        df = pl.read_csv(path)
    else:
        print(f"[WARN] Unsupported extension for {source_name}: {path}")
        return None

    print(f"[OK]   {source_name}: {len(df)} rows, {df.shape[1]} columns")
    return df

def normalize_long(df: pl.DataFrame, source_name: str) -> pl.DataFrame:
    """
    Return the source in canonical long format:
    asset_id | feature_name | value.

    Handles two input shapes:
      - long: already has asset_id, feature_name, value
      - wide: has asset_id + one column per feature (everything else)
    """
    # Case 1: already long
    if {"asset_id", "feature_name", "value"}.issubset(set(df.columns)):
        return df.select(["asset_id", "feature_name", "value"])

    # Case 2: wide — melt everything except asset_id
    if "asset_id" not in df.columns:
        raise ValueError(
            f"{source_name} has no asset_id column. "
            f"Available: {df.columns}"
        )

    # Identify feature columns: everything except asset_id and known metadata
    metadata_cols = {
        "asset_id", "bank", "bank_type", "channel",
        "audience_label", "url", "language", "collected_at",
        "pair_id", "raw_html_path", "screenshot_path", "text",
    }
    feature_cols = [c for c in df.columns if c not in metadata_cols]

    # Cast all feature columns to String before unpivoting.
    # List-type columns (e.g. support_options, trust_signals, topics) cannot
    # be cast directly; we join their elements into a "|"-separated string.

    df = df.with_columns([_to_string(df, c) for c in feature_cols])

    # Melt wide → long
    long_df = df.unpivot(
        index=["asset_id"],
        on=feature_cols,
        variable_name="feature_name",
        value_name="value",
    )

    # Drop rows with null values (feature not present for this asset)
    long_df = long_df.filter(pl.col("value").is_not_null())

    # Cast everything to string for consistency with FeatureRecord
    long_df = long_df.with_columns(pl.col("value").cast(pl.String))

    print(f"       {source_name}: melted {len(feature_cols)} wide columns → {len(long_df)} long rows")
    return long_df

def write_report(
    sources_loaded: dict[str, int],
    sources_skipped: list[str],
    long_rows: int,
    wide_rows: int,
    feature_cols: list[str],
    final_df: pl.DataFrame,
) -> None:
    """Write a markdown report about the merge."""
    lines = [
        "# Merge Features Report",
        "",
        f"**Output:** `{OUTPUT_PATH.as_posix()}`  ",
        f"**Assets in wide table:** {wide_rows}  ",
        f"**Total feature rows (long):** {long_rows}  ",
        f"**Total feature columns (wide):** {len(feature_cols)}",
        "",
        "## 1. Sources loaded",
        "",
        "| Source | Rows |",
        "|---|---:|",
    ]

    for name, rows in sources_loaded.items():
        lines.append(f"| {name} | {rows} |")

    if sources_skipped:
        lines.append("")
        lines.append("**Skipped sources:** " + ", ".join(sources_skipped))

    lines.extend([
        "",
        "## 2. Feature columns in final table",
        "",
        "| Feature | Non-null values |",
        "|---|---:|",
    ])

    for col in sorted(feature_cols):
        non_null = final_df.filter(pl.col(col).is_not_null()).height
        lines.append(f"| `{col}` | {non_null} |")

    lines.extend([
        "",
        "## 3. Assets per bank",
        "",
        "| Bank | Assets |",
        "|---|---:|",
    ])
    bank_counts = (
        final_df.group_by("bank").len().sort("bank")
    )
    for row in bank_counts.iter_rows(named=True):
        lines.append(f"| {row['bank']} | {row['len']} |")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport written to: {REPORT_PATH}")

def pivot_to_wide(df_long: pl.DataFrame) -> pl.DataFrame:
    """
    Pivot a long DataFrame (asset_id, feature_name, value) to wide.
    Metadata columns are preserved separately by the caller.
    """
    wide = df_long.pivot(
        values="value",
        index="asset_id",
        columns="feature_name",
        aggregate_function="first",
    )
    return wide

def main() -> None:
    """Merge all feature sources into a wide table."""
    print("Loading sources...\n")

    det = load_source(DETERMINISTIC_PATH, "deterministic (analysis_set)")
    llm = load_source(LLM_PATH, "llm")
    vis = load_source(VISUAL_PATH, "visual_manual")

    if det is None:
        raise RuntimeError(
            f"deterministic source is required and missing: {DETERMINISTIC_PATH}"
        )

    # --- Filter every source to the analysis set's asset_ids ---
    analysis_ids = set(det["asset_id"].to_list())
    print(f"\nAnalysis set asset_ids: {len(analysis_ids)}")

    det_filtered = det.filter(pl.col("asset_id").is_in(list(analysis_ids)))

    # --- Load cleaned metadata (text + screenshot_path) for the analysis set ---
    cleaned = pl.read_ndjson(CLEANED_PATH).select([
        "asset_id", "text", "screenshot_path"
    ]).filter(pl.col("asset_id").is_in(list(analysis_ids)))
    print(f"       cleaned metadata loaded: {len(cleaned)} assets")

    sources = {
        "deterministic": normalize_long(det_filtered, "deterministic"),
    }

    if llm is not None:
        llm_filtered = llm.filter(pl.col("asset_id").is_in(list(analysis_ids)))
        dropped = llm.height - llm_filtered.height
        print(f"       llm: dropped {dropped} assets not in analysis set")
        sources["llm"] = normalize_long(llm_filtered, "llm")

    if vis is not None:
        vis_filtered = vis.filter(pl.col("asset_id").is_in(list(analysis_ids)))
        sources["visual"] = normalize_long(vis_filtered, "visual")

    # --- Concatenate in long format ---
    long_df = pl.concat(list(sources.values()), how="vertical")
    print(f"\nLong format total: {len(long_df)} rows")

    # --- Extract metadata (one row per asset) from the deterministic source ---
    meta = det.unique(subset=["asset_id"]).select(["asset_id"] + METADATA_COLS)

    # --- Pivot to wide ---
    wide = pivot_to_wide(long_df)
    print(f"Wide format: {len(wide)} assets × {wide.shape[1] - 1} features")

    # --- Join metadata onto the wide table ---
    final = wide.join(meta, on="asset_id", how="left")
    final = final.join(cleaned, on="asset_id", how="left")

    # --- Save ---
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    final.write_parquet(OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")

    # --- Identify feature columns (everything that isn't a metadata col) ---
    non_feature_cols = {"asset_id"} | set(METADATA_COLS)
    feature_cols = [c for c in final.columns if c not in non_feature_cols]

    # --- Write markdown report ---
    sources_loaded = {name: len(df) for name, df in sources.items()}
    sources_skipped = []
    if llm is None:
        sources_skipped.append("llm")
    if vis is None:
        sources_skipped.append("visual")

    write_report(
        sources_loaded=sources_loaded,
        sources_skipped=sources_skipped,
        long_rows=len(long_df),
        wide_rows=len(final),
        feature_cols=feature_cols,
        final_df=final,
    )


if __name__ == "__main__":
    main()