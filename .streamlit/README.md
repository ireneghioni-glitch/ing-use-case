# ING Youth Acquisition Communication Comparator

Streamlit app for the business-facing walkthrough of the project.

## Run

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Pages

- **Home.py** — Scope & Methodology (the 5 MVP banks, coverage rule, out-of-scope items)
- **1_ING_Positioning.py** — ING vs the other 4 MVP banks on key indicators
- **2_Visual_Comparator.py** — side-by-side screenshots + key features for 2–3 chosen banks
- **3_Traditional_vs_Digital_Challenger.py** — aggregate feature patterns by bank type
- **4_Why_It_Matters.py** — live RAG retrieval, sourced justification for observed patterns
- **5_Recommendations.py** — final recommendations, each tied to an observation + its source

## Data

By default the app looks for:
- `data/features/llm_claude.parquet` — the feature-extraction output
- `data/processed/cleaned_assets.jsonl` — cleaned text + screenshot paths
- `data/features/visual_manual.csv` — the manual visual annotation set

If any of these are missing, the app falls back to a small generated demo
dataset (clearly flagged with a warning banner) so every page still renders.
Adjust the paths in `utils/config.py` if your pipeline writes elsewhere.

## RAG (Why It Matters page)

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set
`SUPABASE_DB_URL` to enable live retrieval. Without it, the page shows a
clear notice instead of erroring.
