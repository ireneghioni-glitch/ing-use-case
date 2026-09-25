"""Create the validated final analysis tables."""

import polars as pl

from src.analysis_config import (
    ALL_FEATURES_PATH,
    BANK_ORDER,
    CATEGORY_ORDER,
    EXPECTED_BANK_COUNTS,
    FINAL_CATEGORICAL_FEATURES,
    FINAL_DETERMINISTIC_FEATURES,
    FINAL_SOURCE_QUALITY_PATH,
    FINAL_VALIDATION_NOTE,
    FINAL_VISUAL_DISTRIBUTION_PATH,
    VALIDATION_RESULTS,
)


EXPECTED_ASSET_COUNT = sum(EXPECTED_BANK_COUNTS.values())
EXTREME_WORD_COUNT = 10_000
VISUAL_FEATURE = "visual_type"


def load_final_features() -> pl.DataFrame:
    """Load and validate the final feature dataset."""
    if not ALL_FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Final feature dataset not found: {ALL_FEATURES_PATH}"
        )

    features = pl.read_parquet(ALL_FEATURES_PATH)

    if features.height != EXPECTED_ASSET_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ASSET_COUNT} assets, found {features.height}."
        )

    unique_assets = features.get_column("asset_id").n_unique()
    if unique_assets != EXPECTED_ASSET_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_ASSET_COUNT} unique asset IDs, "
            f"found {unique_assets}."
        )

    required = [
        "asset_id",
        "bank",
        "language",
        "text",
        *FINAL_CATEGORICAL_FEATURES,
        *FINAL_DETERMINISTIC_FEATURES,
    ]
    missing = [column for column in required if column not in features.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    observed_counts = {
        row["bank"]: row["len"]
        for row in features.group_by("bank").len().to_dicts()
    }
    if observed_counts != EXPECTED_BANK_COUNTS:
        raise ValueError(
            "Bank coverage does not match the approved analysis scope: "
            f"{observed_counts}"
        )

    expected_categories = set(CATEGORY_ORDER[VISUAL_FEATURE])
    observed_categories = set(
        features.get_column(VISUAL_FEATURE).unique().to_list()
    )
    unexpected_categories = observed_categories - expected_categories
    if unexpected_categories:
        raise ValueError(
            "Unexpected visual_type categories: "
            + ", ".join(sorted(unexpected_categories))
        )

    return features.with_columns(
        pl.col(feature).cast(pl.Float64, strict=False).alias(feature)
        for feature in FINAL_DETERMINISTIC_FEATURES
    )


def build_source_quality_audit(features: pl.DataFrame) -> pl.DataFrame:
    """Flag records unsuitable for deterministic text analysis."""
    text = pl.col("text").fill_null("")

    return (
        features
        .with_columns(
            text.str.contains("window.ING", literal=True).alias("has_ing_script"),
            text.str.contains("self.__next_f.push", literal=True).alias(
                "has_nextjs_script"
            ),
            (pl.col("word_count") > EXTREME_WORD_COUNT).alias(
                "extreme_word_count"
            ),
            pl.any_horizontal(
                [
                    pl.col(feature).is_null()
                    for feature in FINAL_DETERMINISTIC_FEATURES
                ]
            ).alias("numeric_conversion_error"),
        )
        .with_columns(
            pl.when(pl.col("numeric_conversion_error"))
            .then(pl.lit("invalid_numeric"))
            .when(pl.col("has_ing_script") | pl.col("has_nextjs_script"))
            .then(pl.lit("contaminated_text"))
            .when(pl.col("extreme_word_count"))
            .then(pl.lit("review_extreme_length"))
            .otherwise(pl.lit("eligible"))
            .alias("quality_status")
        )
        .with_columns(
            (pl.col("quality_status") == "eligible").alias(
                "eligible_for_deterministic_analysis"
            )
        )
        .select(
            "asset_id",
            "bank",
            "language",
            "word_count",
            "mean_sentence_length",
            "jargon_density",
            "has_ing_script",
            "has_nextjs_script",
            "extreme_word_count",
            "numeric_conversion_error",
            "quality_status",
            "eligible_for_deterministic_analysis",
        )
        .sort("bank", "quality_status", "asset_id")
    )


def build_visual_type_distribution(features: pl.DataFrame) -> pl.DataFrame:
    """Calculate the validated visual-type distribution by bank."""
    categories = CATEGORY_ORDER[VISUAL_FEATURE]
    complete_grid = pl.DataFrame(
        [
            {"bank": bank, "category": category}
            for bank in BANK_ORDER
            for category in categories
        ]
    )
    bank_totals = features.group_by("bank").len().rename({"len": "bank_total"})
    category_counts = (
        features
        .group_by("bank", VISUAL_FEATURE)
        .len()
        .rename({VISUAL_FEATURE: "category", "len": "asset_count"})
    )
    validation = VALIDATION_RESULTS[VISUAL_FEATURE]

    return (
        complete_grid
        .join(category_counts, on=["bank", "category"], how="left")
        .join(bank_totals, on="bank", how="left")
        .with_columns(pl.col("asset_count").fill_null(0).cast(pl.Int64))
        .with_columns(
            (pl.col("asset_count") / pl.col("bank_total") * 100)
            .round(1)
            .alias("percentage"),
            pl.lit(VISUAL_FEATURE).alias("feature"),
            pl.lit(validation["kappa"]).alias("kappa"),
            pl.lit(validation["decision"]).alias("validation_decision"),
            pl.lit(FINAL_VALIDATION_NOTE).alias("analysis_note"),
        )
        .select(
            "feature",
            "bank",
            "category",
            "asset_count",
            "bank_total",
            "percentage",
            "kappa",
            "validation_decision",
            "analysis_note",
        )
        .sort("bank", "category")
    )


def main() -> None:
    """Generate the final quality and visual-distribution tables."""
    features = load_final_features()
    quality_audit = build_source_quality_audit(features)
    visual_distribution = build_visual_type_distribution(features)

    FINAL_SOURCE_QUALITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    quality_audit.write_csv(FINAL_SOURCE_QUALITY_PATH)
    visual_distribution.write_csv(FINAL_VISUAL_DISTRIBUTION_PATH)

    quality_summary = (
        quality_audit
        .group_by("bank", "quality_status")
        .len()
        .sort("bank", "quality_status")
    )
    print("[OK] Post-validation tables created.")
    print(f"Source quality:      {FINAL_SOURCE_QUALITY_PATH}")
    print(f"Visual distribution: {FINAL_VISUAL_DISTRIBUTION_PATH}")
    print("\nQuality status by bank:")
    for row in quality_summary.to_dicts():
        print(f"- {row['bank']}: {row['quality_status']} = {row['len']}")


if __name__ == "__main__":
    main()
