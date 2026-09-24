# Validation Step — Solo Annotator Guide (v3)

**Purpose:** Practical procedure for Irene to validate three interpretive features produced by the LLM. This replaces the previous two-annotator guide — Alex is no longer available for this step.  
**Output:** `docs/validation_report.md` + three label files in `data/validation/`.

---

## 1. Why This Step Exists

The pipeline produces three kinds of features:
- **Deterministic** (`jargon_density`, `mean_sentence_length`, `word_count`) — code-computed, no validation needed.
- **Interpretive textual** (`main_benefit`, `tone`, etc.) — LLM-produced, require judgment.
- **Interpretive visual** (`visual_type`, etc.) — LLM-produced (vision), require judgment.

The POC must show ING that the pipeline is reproducible and unbiased. An LLM produces labels, but it does not prove them. Without a human check, the only statement we can make is *"we assume the LLM is correct"* — which is not defensible.

Validation converts *"the LLM produced labels"* into *"the labels are reliable enough to base conclusions on."*

### Scope of this version
This is a **single-annotator validation**: Irene compares her own independent labels against the LLM output using Cohen's Kappa.
- We lose the inter-human agreement check (Irene vs Alex) — Alex is not available.
- We keep the LLM-vs-human agreement check, which is what makes the POC defensible.
- **Limitation to document:** *"Validation was performed by a single human annotator against the LLM output. A two-annotator inter-human validation is recommended as a next step."*

---

## 2. When to Do This

`all_features.parquet` is ready when every feature column shows 45/45 non-null values in `docs/merge_report.md`.

**Steps:**
1. Confirm `all_features.parquet` is complete (check `docs/merge_report.md`).
2. Do this validation step.
3. Only after validation passes, run `analyze.py`.

> ⚠️ **Warning:** Do NOT validate on partial data. Check the merge report first.

---

## 3. What to Validate

Three features total — two textual, one visual.

| Feature | Type | Why |
| :--- | :--- | :--- |
| `main_benefit` | text | The core message of the page — the most important interpretive feature |
| `tone` | text | Directly relevant to the youth communication question |
| `visual_type` | visual | The most objective visual feature — easy to label, high informative value |

**Not validating:** `persuasive_framing`, `hero_visual_type`, `human_context`, and the rest. They remain unvalidated and must be flagged as such in the report. They can be used as descriptive context but not as the basis for quantitative conclusions.

---

## 4. Sample Selection

**Goal:** Pick 10 records that represent the full analysis set.

**Rules:**
- **10 records total**, used for both textual and visual validation.
- **Balanced across banks:** 2 records per bank × 5 banks = 10. Revolut has only 5 assets total, so it contributes 2 of them.
- **Balanced across languages where possible:** at least one `fr` and one `nl` per bank, where the bank has both.
- Use only records from `analysis_set.parquet`, not the full 292.
- **No cherry-picking.** Include a variety of page types (hub, product, savings, etc.).

### How to pick concretely
Sort the analysis set by `asset_id` and take a deterministic slice (e.g., every Nth record within each bank, alternating languages). Save the list in:
`data/validation/sample_ids.csv`  
*Columns:* `asset_id`, `bank`, `language`

**Deliverable:** `data/validation/sample_ids.csv` with exactly 10 rows.

---

## 5. Independent Labeling

You are the only annotator. The rule is simple: **label the 10 records before looking at the LLM output.** No peeking at `all_features.parquet` for these three features until your CSV is complete.

### Procedure
For each of the 10 records:
1. Open the cleaned text (from `cleaned_assets.jsonl` or `all_features.parquet`).
2. Open the corresponding screenshot (path is in `screenshot_path`).
3. For each textual feature (`main_benefit`, `tone`): decide the value using the definitions in `features_selection.md`.
4. For the visual feature (`visual_type`): decide the value by looking at the screenshot, using the same definitions.
5. Write down your label. **No evidence required** — this is the agreed simplification.

**Output:** `data/validation/irene_labels.csv`  
*Columns:* `asset_id`, `feature_name`, `value`

**Example rows:**
```text
ing__compte-jeune__fr__abc123,main_benefit,affordability
ing__compte-jeune__fr__abc123,tone,playful
ing__compte-jeune__fr__abc123,visual_type,real-people
kbc__compte-jeunes__nl__def456,main_benefit,convenience
kbc__compte-jeunes__nl__def456,tone,formal
kbc__compte-jeunes__nl__def456,visual_type,product-shot
...
```
*Total rows:* 10 records × 3 features = 30 rows.

**Rules:**
- If a definition is ambiguous for a specific record, put the value you would defend and note it mentally (or in a separate file) for the report limitations section.
- If you cannot decide, use `unknown` — but do not use `unknown` as an escape hatch. Aim to decide.
- Do not discuss with Victor or anyone else about these labels until after your CSV is complete.

**Time budget:** 45–60 minutes. Shorter than the previous version because (a) no evidence required, (b) only one visual feature, (c) no coordination with a second annotator.

---

## 6. Compute Kappa

Once `irene_labels.csv` is complete, compute Cohen's Kappa between your labels and the LLM labels, for each of the three features separately.

**Tool:** `sklearn.metrics.cohen_kappa_score`

### Procedure
Create `src/compute_validation_kappa.py` with this logic:
1. Load `data/validation/irene_labels.csv` and `data/features/all_features.parquet`.
2. For each of the 10 sample `asset_id`, extract:
   - Your label from `irene_labels.csv`
   - The LLM label from `all_features.parquet`
3. For each feature, compute:
   ```python
   from sklearn.metrics import cohen_kappa_score
   kappa = cohen_kappa_score(llm_values, irene_values)
   ```
4. Print a table:
   ```text
   Feature              Kappa (LLM vs Irene)
   main_benefit         0.XX
   tone                 0.XX
   visual_type          0.XX
   ```

### Interpretation Table
| Kappa | Interpretation |
| :--- | :--- |
| `< 0.00` | Worse than chance — major definition problem |
| `0.00 – 0.20` | Slight agreement |
| `0.21 – 0.40` | Fair agreement |
| `0.41 – 0.60` | Moderate agreement |
| `0.61 – 0.80` | Substantial agreement — target |
| `0.81 – 1.00` | Almost perfect |

**Threshold:** `0.60`. Below this, the feature is not reliable for quantitative conclusions.

---

## 7. Interpret the Results and Decide

For each of the three features:

| Kappa | Decision |
| :--- | :--- |
| `≥ 0.60` | Keep the feature in quantitative analysis. Report it. |
| `0.40 – 0.59` | Revise the codebook definition (clarify examples, add edge cases), relabel the 10 records, recompute. |
| `< 0.40` | Drop the feature from quantitative conclusions. Keep it as descriptive context only, with a caveat. |

### Diagnostic Logic (single-annotator version)
- **High Kappa on all three** → the LLM is aligned with human judgment. POC is defensible.
- **Low Kappa on a specific feature** → investigate why. Possible causes:
  - Codebook definition is ambiguous → revise
  - LLM misread that feature on those pages → send back to Victor for prompt revision (if time allows)
  - Feature is inherently subjective → drop
- **Low Kappa on all three** → the LLM prompt has a systematic problem. Do not run the analysis until this is resolved or the limitation is documented explicitly.

---

## 8. Write the Validation Report

Create `docs/validation_report.md`. It must answer:
- **What was validated** — `main_benefit`, `tone`, `visual_type`.
- **What was not validated** — `persuasive_framing`, `hero_visual_type`, `human_context`, and all other interpretive features. They remain LLM-only.
- **Sample** — size (10), banks represented (5 × 2), languages represented.
- **Annotator** — Irene only.
- **Method** — independent labeling (before seeing LLM output), Cohen's Kappa between LLM and human.
- **Results** — Kappa per feature, in a table.
- **Decisions** — keep / revise / drop, per feature.
- **Limitations:**
  - Small sample ($n = 10$).
  - Single human annotator (no inter-human agreement check).
  - French-dominant corpus (only 2 nl in the sample if possible, otherwise fewer).
  - Only 3 of ~24 interpretive features validated.
- **Recommendations for next steps:**
  - Two-annotator inter-human validation.
  - Extend validation to `persuasive_framing`, `hero_visual_type`, `human_context`.
  - Validate on a larger sample.
- **Version** — codebook version used (e.g., v1.0).

### Suggested Table Format
| Feature | Type | Kappa (LLM vs Irene) | Decision |
| :--- | :--- | :--- | :--- |
| `main_benefit` | text | 0.XX | keep / revise / drop |
| `tone` | text | 0.XX | keep / revise / drop |
| `visual_type` | visual | 0.XX | keep / revise / drop |

---

## 9. What to Hand Over

At the end of this step:
- `data/validation/sample_ids.csv`
- `data/validation/irene_labels.csv`
- `src/compute_validation_kappa.py`
- `docs/validation_report.md`

These four files are what makes the POC defensible on the validation axis.

---

## 10. Summary Table

| Step | What | Who | Time |
| :---: | :--- | :--- | :--- |
| **1** | Confirm `all_features.parquet` is complete (45/45 non-null) | Irene | 5 min |
| **2** | Pick 10-record sample → `sample_ids.csv` | Irene | 15 min |
| **3** | Label 10 records independently → `irene_labels.csv` | Irene | 45–60 min |
| **4** | Write `compute_validation_kappa.py` and run it | Irene | 20 min |
| **5** | Interpret Kappa, decide keep / revise / drop | Irene | 15 min |
| **6** | Write `validation_report.md` | Irene | 30 min |
| **7** | Only then start `analyze.py` | Irene | — |

*Total time:* ~2 hours.

---

## 11. Sentence for the Final Report to ING

When presenting to ING, the validation section should state:

> *"Three interpretive features (`main_benefit`, `tone`, `visual_type`) were validated against a human annotator on a representative sample of 10 assets (2 per bank). Cohen's Kappa between the LLM output and the human annotator was computed for each feature. Features with Kappa ≥ 0.60 were kept in the quantitative analysis; those below the threshold were flagged, revised, or dropped. Two-annotator inter-human validation is recommended as a next step to strengthen the reproducibility claim."*

This is the sentence that turns the LLM from "a black box" into "a validated tool," while honestly stating the single-annotator limitation.
