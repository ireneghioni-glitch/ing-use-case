"""
compute_validation_kappa.py
===========================
Compute Cohen's Kappa between Irene's labels and the LLM labels
for the validation sample (main_benefit, tone, visual_type).

Reads:
  data/validation/irene_labels.csv
  data/features/all_features.parquet

Writes:
  docs/validation_report.md

Run: python -m src.compute_validation_kappa
"""

import polars as pl
from sklearn.metrics import cohen_kappa_score

from src.config import FEATURES_DIR, VALIDATION_DIR, DOCS_DIR


LABELS_PATH = VALIDATION_DIR / "irene_labels.csv"
FEATURES_PATH = FEATURES_DIR / "all_features.parquet"
REPORT_PATH = DOCS_DIR / "validation_report.md"

FEATURES = ["main_benefit", "tone", "visual_type"]
THRESHOLD = 0.60


def interpretation_band(kappa: float) -> str:
    if kappa < 0:
        return "worse than chance"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


def decision(kappa: float) -> str:
    if kappa >= THRESHOLD:
        return "keep"
    if kappa >= 0.40:
        return "revise"
    return "drop"


def main() -> None:
    irene = pl.read_csv(LABELS_PATH)
    llm = pl.read_parquet(FEATURES_PATH)

    irene_wide = irene.pivot(
        values="value",
        index="asset_id",
        columns="feature_name",
        aggregate_function="first",
    )

    llm_subset = llm.select(["asset_id"] + FEATURES)

    merged = irene_wide.join(
        llm_subset, on="asset_id", how="inner", suffix="_llm"
    )

    # --- Compute kappa per feature ---
    results: dict[str, dict] = {}
    for feature in FEATURES:
        irene_vals = merged[feature].to_list()
        llm_vals = merged[f"{feature}_llm"].to_list()

        try:
            kappa = cohen_kappa_score(irene_vals, llm_vals)
        except Exception as e:
            kappa = float("nan")
            print(f"[ERROR] {feature}: {e}")

        results[feature] = {
            "kappa": kappa,
            "band": interpretation_band(kappa),
            "decision": decision(kappa),
        }

    # --- Console output ---
    print(f"Records joined: {len(merged)}\n")
    print(f"{'Feature':<20} {'Kappa':>8}  {'Band':<20} {'Decision':<10}")
    print("-" * 65)
    for feature, r in results.items():
        print(
            f"{feature:<20} {r['kappa']:>8.3f}  "
            f"{r['band']:<20} {r['decision']:<10}"
        )

    # --- Write markdown report ---
    lines = [
        "# Validation Report",
        "",
        "## 1. Purpose",
        "",
        "Validate the LLM-produced interpretive features against an",
        "independent human annotator, using Cohen's Kappa. This is what",
        "turns \"the LLM produced labels\" into \"the labels are reliable",
        "enough to base conclusions on\".",
        "",
        "## 2. Sample",
        "",
        f"- **Records**: {len(merged)}",
        "- **Banks**: balanced across the 5 MVP banks (2 per bank)",
        "- **Languages**: fr / nl / en where available",
        "- **Source**: `data/validation/sample_ids.csv`",
        "",
        "## 3. Annotators",
        "",
        "- **Human**: Irene (single annotator)",
        "- **LLM**: Victor's extraction, stored in `data/features/llm_claude.parquet`",
        "",
        "## 4. Method",
        "",
        "- Irene labeled the 10 records **before** seeing the LLM output.",
        "- Labels: `main_benefit`, `tone`, `visual_type`.",
        f"- Metric: Cohen's Kappa (threshold for keep: {THRESHOLD}).",
        "",
        "## 5. Results",
        "",
        "| Feature | Kappa | Band | Decision |",
        "|---|---:|---|---|",
    ]
    for feature, r in results.items():
        lines.append(
            f"| `{feature}` | {r['kappa']:.3f} | {r['band']} | **{r['decision']}** |"
        )

    lines.extend([
        "",
        "## 6. Interpretation",
        "",
        "- **Kappa ≥ 0.60** → feature kept in quantitative analysis.",
        "- **0.40 ≤ Kappa < 0.60** → feature retained but flagged; consider",
        "  revising the codebook if time allows.",
        "- **Kappa < 0.40** → feature dropped from quantitative conclusions;",
        "  cited only as descriptive context.",
        "",
        "## 7. Limitations",
        "",
        "- Small sample (n = 10).",
        "- Single human annotator: no inter-human agreement check.",
        "- One record for sure (Belfius `compte-bancaire-pour-jeunes`) had a",
        "  text-extraction failure (Next.js JavaScript content), others my have this promblem. The human",
        "  annotation used the screenshot; the LLM labels for that record",
        "  may be unreliable. This is reflected in the Kappa.",
        "- Only 3 of the ~24 interpretive features were validated.",
        "",
        "## 8. Recommendations (next steps)",
        "",
        "- Two-annotator inter-human validation to strengthen the",
        "  reproducibility claim.",
        "- Extend validation to `persuasive_framing`, `hero_visual_type`,",
        "  `human_context`.",
        "- Re-run validation after any codebook revision.",
        "",
        "## 9. Raw joined table",
        "",
        "| asset_id | " + " | ".join(FEATURES) + " | " +
        " | ".join(f"{f}_llm" for f in FEATURES) + " |",
        "|" + "---|" * (1 + 2 * len(FEATURES)),
    ])
    for row in merged.iter_rows(named=True):
        cells = [row["asset_id"]]
        for f in FEATURES:
            cells.append(str(row[f]))
        for f in FEATURES:
            cells.append(str(row[f"{f}_llm"]))
        lines.append("| " + " | ".join(cells) + " |")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()