"""Create the chart for the validated visual-type analysis."""

import matplotlib.pyplot as plt
import polars as pl

from src.analysis_config import (
    BANK_ORDER,
    CATEGORY_ORDER,
    FIGURES_DIR,
    FINAL_VISUAL_DISTRIBUTION_PATH,
)


VISUAL_PROFILE_PATH = FIGURES_DIR / "final_visual_type_by_bank.png"

VISUAL_COLORS = {
    "real-people": "#FF6200",   # ING orange
    "product-shot": "#0072B2",  # blue
    "abstract": "#009E73",      # bluish green
    "none": "#B3B3B3",          # grey
}

LABEL_COLORS = {
    "real-people": "white",
    "product-shot": "white",
    "abstract": "white",
    "none": "black",
}


def load_visual_distribution() -> pl.DataFrame:
    """Load and verify the validated visual-type table."""
    if not FINAL_VISUAL_DISTRIBUTION_PATH.exists():
        raise FileNotFoundError(
            "Run `python -m src.ing_post_validation` before visualization."
        )

    distribution = pl.read_csv(FINAL_VISUAL_DISTRIBUTION_PATH)
    categories = CATEGORY_ORDER["visual_type"]
    expected_rows = len(BANK_ORDER) * len(categories)

    if distribution.height != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} rows, found {distribution.height}."
        )

    decisions = set(
        distribution.get_column("validation_decision").unique().to_list()
    )
    if decisions != {"keep"}:
        raise ValueError(
            "The visual feature has not been approved for final analysis."
        )

    percentage_totals = (
        distribution
        .group_by("bank")
        .agg(pl.col("percentage").sum().round(1).alias("total"))
    )
    if percentage_totals.filter(pl.col("total") != 100.0).height:
        raise ValueError(
            "Visual-type percentages do not total 100% for every bank."
        )

    return distribution


def create_visual_profile_chart(distribution: pl.DataFrame) -> None:
    """Create a 100% stacked visual-type chart by bank."""
    categories = CATEGORY_ORDER["visual_type"]
    percentage_lookup = {
        (row["bank"], row["category"]): float(row["percentage"])
        for row in distribution.to_dicts()
    }

    figure, axis = plt.subplots(figsize=(10, 6))
    bottoms = [0.0 for _ in BANK_ORDER]

    for category in categories:
        values = [
            percentage_lookup.get((bank, category), 0.0)
            for bank in BANK_ORDER
        ]
        bars = axis.bar(
            BANK_ORDER,
            values,
            bottom=bottoms,
            label=category,
            color=VISUAL_COLORS[category],
            edgecolor="white",
            linewidth=0.8,
        )

        for bar, value, bottom in zip(bars, values, bottoms):
            if value >= 10:
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    bottom + value / 2,
                    f"{value:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                    color=LABEL_COLORS[category],
                )

        bottoms = [
            bottom + value
            for bottom, value in zip(bottoms, values)
        ]

    axis.set_title(
        "Dominant visual types in selected youth-oriented pages",
        fontsize=14,
        pad=14,
    )
    axis.set_ylabel("Share of selected pages (%)")
    axis.set_ylim(0, 100)
    axis.grid(axis="y", linestyle="--", alpha=0.3)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.legend(
        title="Visual type",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        frameon=False,
    )

    figure.text(
        0.01,
        0.01,
        "Validated visual_type: Cohen's kappa = 0.841.",
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.06, 0.84, 1))

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(VISUAL_PROFILE_PATH, dpi=200, bbox_inches="tight")
    plt.close(figure)

    print(f"[OK] Visual profile chart created: {VISUAL_PROFILE_PATH}")


def main() -> None:
    """Create the validated final visualization."""
    distribution = load_visual_distribution()
    create_visual_profile_chart(distribution)


if __name__ == "__main__":
    main()
