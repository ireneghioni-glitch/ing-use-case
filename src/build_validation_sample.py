from pathlib import Path
import polars as pl 

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "features"
    / "analysis_set_deterministic.parquet"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "sample_ids.csv"
)

SAMPLE_SIZE_PER_BANK = 2 
PREFERRED_LANGUAGES = ("en", "fr")

def select_for_bank(bank_assets: pl.DataFrame) -> list[dict]:
    """
    Select two assets while preferrring different languages.
    """

    selected: list[dict] = []
    selected_ids: set[str] = set()

    for language in PREFERRED_LANGUAGES:
        if len(selected) >= SAMPLE_SIZE_PER_BANK:
            break

        candidates = (
            bank_assets
            .filter(pl.col("language") == language)
            .sort("asset_id")
         )

        if candidates.height > 0:
            record = candidates.row(0, named=True)
            selected.append(record)
            selected_ids.add(record["asset_id"])

    # Defensive fallback if fewer than two languages are available.
    if len(selected) < SAMPLE_SIZE_PER_BANK:
        remaining = (
            bank_assets
            .filter(~pl.col("asset_id").is_in(selected_ids))
            .sort("asset_id")
        )

        for record in remaining.iter_rows(named=True):
            if len(selected) >= SAMPLE_SIZE_PER_BANK:
                break
            selected.append(record)

    return selected


def main() -> None:
    features = pl.read_parquet(INPUT_PATH)

    # analysis_set.parquet is long format: three deterministic-feature
    # rows exist for each asset. Keep one metadata row per asset.
    assets = (
        features
        .select(["asset_id", "bank", "language"])
        .unique(subset=["asset_id"])
        .sort(["bank", "language", "asset_id"])
    )

    sample: list[dict] = []

    for bank in sorted(assets["bank"].unique().to_list()):
        bank_assets = assets.filter(pl.col("bank") == bank)
        selected = select_for_bank(bank_assets)

        if len(selected) != SAMPLE_SIZE_PER_BANK:
            raise ValueError(
                f"{bank}: expected 2 selected assets, "
                f"received {len(selected)}"
            )

        sample.extend(selected)

    sample_df = (
        pl.DataFrame(sample)
        .select(["asset_id", "bank", "language"])
        .sort(["bank", "language", "asset_id"])
    )

    if sample_df.height != 10:
        raise ValueError(
            f"Expected exactly 10 records, found {sample_df.height}"
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample_df.write_csv(OUTPUT_PATH)

    print(sample_df)
    print(f"\nSample written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()


