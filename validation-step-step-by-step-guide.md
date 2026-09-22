# Validation Step — Step-by-step Guide (v2)

**Purpose of this document:** Give Irene and Alex a shared, unambiguous procedure for the validation step. Read it before starting, follow it in order, and record the outcome in `docs/validation_report.md`.

---

## 1. Why We Do This (Context)

The pipeline produces three kinds of features:
1. **Deterministic features** (`jargon_density`, `mean_sentence_length`, `word_count`) — computed by code. No interpretation. No validation needed.
2. **Interpretive textual features** (`main_benefit`, `tone`, `sentiment`, `persuasive_framing`, etc.) — produced by an LLM (Victor). These require judgment, so they can vary between annotators.
3. **Interpretive visual features** (`visual_type`, `hero_visual_type`, `human_context`, `hero_layout`, etc.) — produced by an LLM with vision capability (Victor). These also require judgment.

### Why We Cannot Just Trust the LLM
The POC must show ING that the pipeline is reproducible and unbiased. An LLM produces labels, but it does not prove them. Without an independent human check, all we can say to ING is *"we assume the LLM is correct"*. That is not defensible.

The coach asked for a pipeline that is **"structured, reproducible, unbiased"**. Validation is what turns *"the LLM produced labels"* into *"the labels are reliable enough to base conclusions on"*. Without it, the POC is a black box.

### Why We Cannot Annotate Every Screenshot Manually
A full manual annotation of all ~65 screenshots for 4+ visual features would take ~6–8 hours per annotator, plus double-labeling for Kappa. This is incompatible with the remaining POC timeline (2 days) and would compromise the validation of the textual features and the analysis step.

More importantly: **we do not need full manual annotation to prove reliability**. We need a representative sample that lets us measure agreement between the LLM and human annotators. If the LLM agrees with humans on a well-chosen sample of 10 records, we can reasonably trust the LLM on the rest.

This is standard practice in NLP and computer vision evaluation: **validate on a sample, not on the full corpus**.

The metric **Cohen's Kappa** measures agreement between two annotators, corrected for chance. It tells us whether the labels are trustworthy enough to base conclusions on.

---

## 2. When to Do This

Do it after `all_features.parquet` is fully populated with the LLM features (textual + visual).

**Steps:**
1. Wait for Victor's final `llm.parquet`.
2. Rerun `merge_features.py` to refresh `all_features.parquet`.
3. Run the validation step (this document).
4. Only after validation passes, run the analysis.

> ⚠️ **Warning:** Do NOT validate on partial data. If the LLM has only labeled 25 of 45 assets, the Kappa you compute may not represent the final feature quality.

---

## 3. What to Validate

Validate **both** the textual and the visual interpretative features. This is done in a single annotation session (same sample, same moment) to avoid double work.

### Textual Features — Recommended Trio
| Feature | Why |
| :--- | :--- |
| `main_benefit` | The most important interpretive feature — it defines the core message tone |
| `tone` | Directly relevant to the youth communication question |
| `persuasive_framing` | Captures gain/loss framing, a subtle but high-impact dimension |

### Visual Features — Recommended Trio
| Feature | Why |
| :--- | :--- |
| `visual_type` | Dominant visual type of the page (people / product / illustration / abstract) |
| `hero_visual_type` | What appears in the hero section — first impression of the page |
| `human_context` | If people are shown, in what social context (peers / family / alone) |

*If time is short:* validate 2 textual (`main_benefit`, `tone`) + 2 visual (`visual_type`, `hero_visual_type`). Four is the minimum to claim "we validated both pipelines".

---

## 4. Sample Selection

**Goal:** Pick 10 records that represent the full analysis set.

**Rules:**
* **10 records total**, used for BOTH textual and visual validation.
* **Balanced across banks:** Aim for 2 records per bank × 5 banks = 10.
* **Balanced across languages where possible:** Try for at least one `fr` and one `nl` per bank where the bank has both.
* Use only records from `analysis_set.parquet`, not the full 292.
* **Do not cherry-pick:** Include a variety of page types (hub, product, savings, etc.).

**How to pick concretely:** Sort the analysis set by `asset_id` and take a deterministic slice (e.g., every Nth record). Save the list in `data/validation/sample_ids.csv` with columns `asset_id`, `bank`, `language`.

**Deliverable:** `data/validation/sample_ids.csv` with exactly 10 rows.

---

## 5. Independent Labeling (The Core of the Process)

**The Rule:** Irene and Alex label the same 10 records independently. No discussion before, no peeking at each other's labels.

### Procedure for Each Annotator (Single Session)
For each of the 10 records:
1. Open the cleaned text (from `all_features.parquet` or `cleaned_assets.jsonl`).
2. Open the corresponding screenshot (path is in `screenshot_path`).
3. For each of the textual features (3), decide the value using the codebook definitions in `features_selection.md`. Copy the exact sentence that supports your choice.
4. For each of the visual features (3), decide the value by looking at the screenshot. Copy a short description of what you see as evidence.
5. Save your labels.

**Output Format for Each Annotator:**
* `data/validation/irene_labels.csv`
* `data/validation/alex_labels.csv`
* *Columns:* `asset_id`, `feature_name`, `value`, `evidence_text`

**Rules for Evidence:**
* *For textual features:* `evidence_text` must be an exact substring of the cleaned text.
* *For visual features:* `evidence_text` is a short description (e.g., `"young couple smiling in a café, mid-shot"`).
* If you cannot find evidence, put `value = unknown` and `evidence_text = ""`.
* If the definition is ambiguous, note it in a comment column — do not discuss with the other annotator until both have finished.

**Time Budget:** 90–120 minutes per annotator, done in parallel (not sequentially). The single session covers both textual and visual labels, so there is no second pass.

---

## 6. Compute Agreement

Once both CSVs are complete, compute Cohen's Kappa for each feature separately, on the 10 shared records.

**Tool:** `sklearn.metrics.cohen_kappa_score`.

```python
from sklearn.metrics import cohen_kappa_score

# For feature "tone"
annotator_irene = ["formal", "playful", "simple", "formal", ...]  # 10 values
annotator_alex  = ["formal", "playful", "simple", "playful", ...]

kappa = cohen_kappa_score(annotator_irene, annotator_alex)
print(f"Kappa for tone: {kappa:.2f}")
```

Do this once per feature, separately for textual and visual.

### Interpretation Table
| Kappa Value | Interpretation |
| :---: | :--- |
| **< 0.00** | Worse than chance — major definition problem |
| **0.00 – 0.20** | Slight agreement |
| **0.21 – 0.40** | Fair agreement |
| **0.41 – 0.60** | Moderate agreement |
| **0.61 – 0.80** | **Substantial agreement — TARGET** |
| **0.81 – 1.00** | Almost perfect |

**Threshold:** `0.60`. Below this, the feature is not reliable for quantitative conclusions.

### Also Compute LLM vs. Human
For each feature, compute Kappa between:
* LLM labels and Irene's labels
* LLM labels and Alex's labels

This shows whether the LLM is aligned with human judgment. It is what allows us to say *"the LLM was validated against two independent human annotators"*.

---

## 7. Interpret the Results and Decide

For each validated feature, take one of three actions:

| Kappa | Decision |
| :---: | :--- |
| **≥ 0.60** | **Keep** the feature in quantitative analysis. Report it. |
| **0.40 – 0.59** | **Revise** the codebook definition (add examples, clarify edge cases), relabel the sample, recompute. |
| **< 0.40** | **Drop** the feature from quantitative conclusions. Keep it as descriptive context only, with a caveat. |

### Diagnostic Logic
* **Both humans agree well + LLM agrees well with both** → The feature is validated. ✅
* **Both humans agree well + LLM disagrees with both** → The LLM prompt needs revision. Send back to Victor. 🔁
* **Humans disagree with each other** → The codebook definition is ambiguous. Revise the codebook. 🔁
* **Everyone disagrees** → The feature is too subjective. Drop it. ❌

---

## 8. Write the Validation Report

Create `docs/validation_report.md`. It must answer:
1. **What was validated** — list the features (textual + visual).
2. **Sample** — size, banks represented, languages represented.
3. **Annotators** — Irene, Alex (and mention Victor for LLM).
4. **Method** — independent labeling, exact evidence required, Cohen's Kappa.
5. **Results** — the Kappa per feature, in a table (textual + visual).
6. **Decisions** — keep / revise / drop, per feature.
7. **Limitations** — e.g., small sample ($n=10$), French-dominant corpus, only 6 features validated.
8. **Why the LLM alone was not enough** — explain that validation was required to make the POC defensible.
9. **Why full manual annotation was not done** — explain that a representative sample of 10 was sufficient to measure LLM-vs-human agreement, given the POC timeline.
10. **Version** — codebook version used (e.g., v1.0).

### Suggested Table Format
| Feature | Type | Kappa (I vs A) | LLM vs I | LLM vs A | Decision |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `main_benefit` | text | 0.72 | 0.65 | 0.61 | **keep** |
| `tone` | text | 0.55 | 0.48 | 0.51 | **revise** |
| `persuasive_framing` | text | 0.34 | 0.28 | 0.30 | **drop** |
| `visual_type` | visual | 0.68 | 0.62 | 0.60 | **keep** |
| `hero_visual_type` | visual | 0.63 | 0.58 | 0.55 | **revise** |
| `human_context` | visual | 0.41 | 0.38 | 0.35 | **drop** |

---

## 9. What to Hand Over

At the end of this step, deliver:
* `data/validation/sample_ids.csv`
* `data/validation/irene_labels.csv`
* `data/validation/alex_labels.csv`
* `docs/validation_report.md`

These four files are what makes the POC defensible. Without them, the POC cannot claim "unbiased" or "reproducible".

---

## 10. Summary Table

| Step | What | Who | When |
| :---: | :--- | :---: | :--- |
| **1** | Wait for final `llm.parquet` (textual + visual) | Victor | As soon as ready |
| **2** | Rerun `merge_features.py` | Irene | After step 1 |
| **3** | Pick 10-record sample | Irene | 15 min |
| **4** | Label independently (textual + visual in one session) | Irene + Alex | 90–120 min each, in parallel |
| **5** | Compute Kappa for all features | Irene | 30 min |
| **6** | Decide per feature (keep / revise / drop) | Irene + Alex | 15 min |
| **7** | Write report | Irene | 30 min |
| **8** | Only then start `analyze.py` | Irene | — |

**Total wall-clock time:** ~3 hours, if Irene and Alex work in parallel on step 4.

---

## 11. Notes for the Final Report to ING

When the POC is presented to ING, the validation section should state:

> *"Interpretive features (both textual and visual) were validated against two independent human annotators on a representative sample of 10 assets (2 per bank). Cohen's Kappa was computed between the two annotators and between each annotator and the LLM output. Features with Kappa ≥ 0.60 were kept in the quantitative analysis; those below the threshold were flagged, revised, or dropped. This ensures the pipeline is reproducible and unbiased, as required."*

This is the sentence that turns the LLM from "a black box" into "a validated tool". It is what makes the POC defensible.
