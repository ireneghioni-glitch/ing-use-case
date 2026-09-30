"""Reproduce the historical pre-validation communication tables.

The outputs from this module document what the LLM labels initially
suggested. Validation later rejected ``tone`` and ``main_benefit`` for
quantitative analysis, so these tables are hypotheses rather than findings.
"""

import polars as pl

from src.analysis_config import (
    ALL_FEATURES_PATH,
    BANK_ORDER,
    EXPECTED_BANK_COUNTS,
    PRELIMINARY_ANALYSIS_FEATURES,
    PRELIMINARY_ANALYSIS_NOTE,
    PRELIMINARY_BANK_COVERAGE_PATH,
    PRELIMINARY_CATEGORY_ORDER,
    PRELIMINARY_COMPARISON_GROUPS,
    PRELIMINARY_CONSISTENCY_PATH,
    PRELIMINARY_DISTRIBUTIONS_PATH,
    PRELIMINARY_ING_GAP_PATH,
)

STATUS = "rejected_after_validation"


def load_and_validate() -> pl.DataFrame:
    """Load the feature table and enforce the agreed 35-asset scope."""
    if not ALL_FEATURES_PATH.exists():
        raise FileNotFoundError(f"Feature dataset not found: {ALL_FEATURES_PATH}")

    data = pl.read_parquet(ALL_FEATURES_PATH)
    required = {
        "asset_id",
        "bank",
        "language",
        *PRELIMINARY_ANALYSIS_FEATURES,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    duplicate_count = data.select(pl.col("asset_id").is_duplicated().sum()).item()
    if duplicate_count:
        raise ValueError(f"Duplicate asset IDs found: {duplicate_count}")

    observed_counts = {
        row["bank"]: row["len"] for row in data.group_by("bank").len().to_dicts()
    }
    if observed_counts != EXPECTED_BANK_COUNTS:
        raise ValueError(
            "Dataset does not match the agreed analysis scope.\n"
            f"Expected: {EXPECTED_BANK_COUNTS}\nObserved: {observed_counts}"
        )

    for feature in PRELIMINARY_ANALYSIS_FEATURES:
        if data.get_column(feature).null_count():
            raise ValueError(f"Null labels found in {feature}.")
        observed = set(data.get_column(feature).unique().to_list())
        allowed = set(PRELIMINARY_CATEGORY_ORDER[feature])
        unexpected = sorted(observed - allowed)
        if unexpected:
            raise ValueError(f"Unexpected {feature} categories: {unexpected}")

    return data


def build_coverage(data: pl.DataFrame) -> pl.DataFrame:
    """Summarize asset and language coverage by bank."""
    return (
        data.group_by("bank")
        .agg(
            pl.len().alias("asset_count"),
            pl.col("language").unique().sort().alias("recorded_languages"),
        )
        .with_columns(
            (pl.col("asset_count") / pl.col("asset_count").sum() * 100)
            .round(1)
            .alias("dataset_percentage"),
            pl.col("recorded_languages").list.join(", "),
        )
        .sort(pl.col("bank").replace_strict(BANK_ORDER, list(range(len(BANK_ORDER)))))
    )


def build_distributions(data: pl.DataFrame) -> pl.DataFrame:
    """Calculate within-bank label counts and percentages."""
    tables = []
    for feature in PRELIMINARY_ANALYSIS_FEATURES:
        table = (
            data.group_by("bank", feature)
            .agg(pl.len().alias("asset_count"))
            .with_columns(
                pl.col("asset_count").sum().over("bank").alias("bank_total")
            )
            .with_columns(
                (pl.col("asset_count") / pl.col("bank_total") * 100)
                .round(1)
                .alias("percentage"),
                pl.lit(feature).alias("feature"),
                pl.lit(STATUS).alias("validation_status"),
                pl.lit(PRELIMINARY_ANALYSIS_NOTE).alias("analysis_note"),
            )
            .rename({feature: "category"})
            .select(
                "feature",
                "bank",
                "category",
                "asset_count",
                "bank_total",
                "percentage",
                "validation_status",
                "analysis_note",
            )
        )
        tables.append(table)

    return pl.concat(tables).sort("feature", "bank", "category")


def build_ing_gaps(distributions: pl.DataFrame) -> pl.DataFrame:
    """Compare ING with equal-bank competitor-group percentages."""
    lookup = {
        (row["feature"], row["bank"], row["category"]): row["percentage"]
        for row in distributions.to_dicts()
    }
    rows = []

    for feature in PRELIMINARY_ANALYSIS_FEATURES:
        observed = set(
            distributions.filter(pl.col("feature") == feature)
            .get_column("category")
            .to_list()
        )
        categories = [
            category
            for category in PRELIMINARY_CATEGORY_ORDER[feature]
            if category in observed
        ]
        for category in categories:
            ing_percentage = float(lookup.get((feature, "ING", category), 0.0))
            for group_name, banks in PRELIMINARY_COMPARISON_GROUPS.items():
                group_percentage = sum(
                    float(lookup.get((feature, bank, category), 0.0))
                    for bank in banks
                ) / len(banks)
                rows.append(
                    {
                        "feature": feature,
                        "category": category,
                        "comparison_group": group_name,
                        "ing_percentage": round(ing_percentage, 1),
                        "group_mean_percentage": round(group_percentage, 1),
                        "percentage_point_gap": round(
                            ing_percentage - group_percentage, 1
                        ),
                        "validation_status": STATUS,
                        "analysis_note": PRELIMINARY_ANALYSIS_NOTE,
                    }
                )

    return pl.DataFrame(rows).sort("feature", "category", "comparison_group")


def build_consistency(distributions: pl.DataFrame) -> pl.DataFrame:
    """Identify each bank's most frequent labels while preserving ties."""
    dominant = distributions.with_columns(
        pl.col("asset_count").max().over("feature", "bank").alias("dominant_count")
    ).filter(pl.col("asset_count") == pl.col("dominant_count"))

    return (
        dominant.group_by(
            "feature",
            "bank",
            "bank_total",
            "dominant_count",
            "validation_status",
            "analysis_note",
        )
        .agg(pl.col("category").sort().alias("dominant_categories"))
        .with_columns(
            (pl.col("dominant_count") / pl.col("bank_total") * 100)
            .round(1)
            .alias("dominance_percentage"),
            (pl.col("dominant_categories").list.len() > 1).alias("is_tie"),
            pl.col("dominant_categories").list.join(" | "),
        )
        .select(
            "feature",
            "bank",
            "dominant_categories",
            "dominant_count",
            "bank_total",
            "dominance_percentage",
            "is_tie",
            "validation_status",
            "analysis_note",
        )
        .sort("feature", "bank")
    )


def main() -> None:
    """Generate the four reproducible preliminary-analysis tables."""
    data = load_and_validate()
    outputs = {
        PRELIMINARY_BANK_COVERAGE_PATH: build_coverage(data),
        PRELIMINARY_DISTRIBUTIONS_PATH: build_distributions(data),
    }
    outputs[PRELIMINARY_ING_GAP_PATH] = build_ing_gaps(
        outputs[PRELIMINARY_DISTRIBUTIONS_PATH]
    )
    outputs[PRELIMINARY_CONSISTENCY_PATH] = build_consistency(
        outputs[PRELIMINARY_DISTRIBUTIONS_PATH]
    )

    for path, table in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        table.write_csv(path)
        print(f"[OK] {path.name}: {table.height} rows")

    print(PRELIMINARY_ANALYSIS_NOTE)


if __name__ == "__main__":
    main()
