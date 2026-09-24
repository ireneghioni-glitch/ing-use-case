# Validation Report

## 1. Purpose

Validate the LLM-produced interpretive features against an
independent human annotator, using Cohen's Kappa. This is what
turns "the LLM produced labels" into "the labels are reliable
enough to base conclusions on".

## 2. Sample

- **Records**: 10
- **Banks**: balanced across the 5 MVP banks (2 per bank)
- **Languages**: fr / nl / en where available
- **Source**: `data/validation/sample_ids.csv`

## 3. Annotators

- **Human**: Irene (single annotator)
- **LLM**: Victor's extraction, stored in `data/features/llm_claude.parquet`

## 4. Method

- Irene labeled the 10 records **before** seeing the LLM output.
- Labels: `main_benefit`, `tone`, `visual_type`.
- Metric: Cohen's Kappa (threshold for keep: 0.6).

## 5. Results

| Feature | Kappa | Band | Decision |
|---|---:|---|---|
| `main_benefit` | 0.101 | slight | **drop** |
| `tone` | -0.125 | worse than chance | **drop** |
| `visual_type` | 0.841 | almost perfect | **keep** |

### Diagnostic — why the Kappas are low

The low Kappa on `main_benefit` and `tone` is **not random disagreement**.
It is probably a systematic bias in the LLM output:

- `main_benefit`: the LLM returned `independence-control` in 7 of 10 records.
  The human annotator used 4 different categories. It seems the LLM is collapsing
  the feature space onto one label.
- `tone`: the LLM returned `formal` or `persuasive` in 7 of 10 records.
  The human annotator used `playful` 4 times. The LLM could probably not recognize
  the youthful and friendly register on these pages.

By contrast, `visual_type` shows almost perfect agreement (0.841). The
pipeline works correctly on the visual track; the text track needs a
prompt revision.

**Action for the next iteration:** review the LLM prompt for `main_benefit`
and `tone`, add explicit definitions and few-shot examples of each
category, and re-run the validation on the same 10 records.

## 6. Interpretation

- **Kappa ≥ 0.60** → feature kept in quantitative analysis.
- **0.40 ≤ Kappa < 0.60** → feature retained but flagged; consider
  revising the codebook if time allows.
- **Kappa < 0.40** → feature dropped from quantitative conclusions;
  cited only as descriptive context.

## 7. Limitations

- Small sample (n = 10).
- Single human annotator: no inter-human agreement check.
- One record for sure (Belfius `compte-bancaire-pour-jeunes`) had a
  text-extraction failure (Next.js JavaScript content), others my have this promblem. The human
  annotation used the screenshot; the LLM labels for that record
  may be unreliable. This is reflected in the Kappa.
- Only 3 of the ~24 interpretive features were validated.

## 8. Recommendations (next steps)

- Two-annotator inter-human validation to strengthen the
  reproducibility claim.
- Extend validation to `persuasive_framing`, `hero_visual_type`,
  `human_context`.
- Re-run validation after any codebook revision.

## 9. Raw joined table

| asset_id | main_benefit | tone | visual_type | main_benefit_llm | tone_llm | visual_type_llm |
|---|---|---|---|---|---|---|
| ing__automatic-savings-account-youth__en__be6bdee298 | mixed | simple | real-people | independence-control | formal | real-people |
| ing__app-ing-banking-jeunes-apprendre-gerer-son-budget__fr__8b9dc331d4 | convenience | formal | real-people | independence-control | simple | real-people |
| kbc__18-ans__fr__6a644fdf4c | convenience | playful | real-people | convenience | formal | real-people |
| kbc__credit-card-students__en__427c316df1 | mixed | formal | product-shot | independence-control | formal | product-shot |
| belfius__compte-bancaire-pour-jeunes__fr__5ca90c8257 | mixed | simple | real-people | independence-control | persuasive | real-people |
| belfius__betaalrekening-voor-jongeren__nl__2db666014e | mixed | simple | real-people | independence-control | persuasive | real-people |
| revolut__getting-started-with-instant-access-savings__en__bb34b97d35 | other | playful | none | security-support | formal | none |
| revolut__revolut-junior__fr__88ba5a908e | other | playful | none | independence-control | simple | none |
| n26__bank-account__en__daae456c5e | independence-control | simple | product-shot | independence-control | persuasive | product-shot |
| n26__how-to-open-a-bank-account-in-belgium__fr__a3d02b35c6 | other | playful | none | convenience | simple | product-shot |
