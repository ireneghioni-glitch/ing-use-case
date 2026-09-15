# Data Scientist's Guide: ING Youth Acquisition Communication Comparator


## PART 0: Understanding the Project

### What is this project?
ING wants to know how banks (including themselves) talk to young people (18-25) when offering them a current account. They want to compare:
- How ING talks to young people vs. how ING talks to adults
- How ING talks to young people vs. how KBC, Belfius, Revolut talk to young people

The output is a communication comparison — not a sales prediction. You are not measuring "which bank gets more customers." You are measuring "which bank says what, how, and where."

### Why is this not a sales model?
Because you have no internal data. You don't know how many people opened an account after seeing a page. You only have public web pages and ads. So the project is about observable communication features, not business outcomes.

### What is an MVP?
MVP = Minimum Viable Product. It means: the smallest version of the project that still delivers value. In this case, 8 days, a small sample of pages, a validated pipeline, and three recommendations. It is not a production system. It is a proof that the method works.

### What is a POC?
POC = Proof of Concept. Same idea as MVP. It proves that something is feasible. ING asked for a POC, not a production tool. So do not over-engineer.

---

## PART 1: Glossary of Terms

Read this section once. Come back to it when you see a term you don't remember.

| Term | Plain English Explanation |
| :--- | :--- |
| **Codebook** | A rulebook. It defines every feature you will measure, how to measure it, what values are allowed, and how to handle missing data. Think of it as a data dictionary with strict rules. |
| **Feature** | A single measurable characteristic of a page. Example: "Is the price visible in the first screen?" or "How many jargon words per 100 words?" |
| **Asset** | One unit of content. A web page, an ad, a screenshot. Each asset gets a unique ID. |
| **Asset ID** | A unique code for each asset. Example: `ING_YOUTH_001`. |
| **Pair ID** | A code that links two assets that should be compared. Example: `ING_PAIR_01` links ING's youth page and ING's adult page for the same product. |
| **Metadata** | Data about the data. Example: bank name, language, date collected, URL, page role. |
| **Page Role** | What kind of page is it? Youth landing page? Adult landing page? Pricing page? Conditions page? |
| **Landing Page** | The main page a customer sees when they click an ad or search result. It is the primary comparison unit. |
| **Viewport** | The visible area of a browser window. "Initial viewport" means what you see before scrolling. |
| **CTA** | Call to Action. The button or link that asks the user to do something. Example: "Open an account" or "Learn more." |
| **Jargon Density** | How many technical or financial terms appear per 100 words. High jargon = harder to read. |
| **Persuasive Framing** | How the message is framed. Gain framing = "Save money." Loss framing = "Don't lose money." |
| **Deterministic Feature** | A feature you can extract with code, with no interpretation. Example: word count. |
| **Interpretive Feature** | A feature that requires judgment. Example: "Is the tone playful or formal?" |
| **Missing Value** | A value you could not extract. It is not zero. It is `unknown` or `not_applicable`. |
| **Provenance** | The origin and history of a piece of data. Where did it come from? When? How? |
| **Robots.txt** | A file on a website that tells bots what they are allowed to crawl. It is a technical signal, not a legal permission. |
| **Validation** | The process of checking that your labels are correct and consistent. |
| **Cohen's Kappa** | A statistical measure of agreement between two annotators. 1 = perfect agreement, 0 = random. |
| **Embeddings** | Numerical vectors that represent the meaning of text. Similar texts have similar vectors. |
| **Cosine Similarity** | A measure of how similar two vectors are. Used to compare embeddings. |
| **Clustering** | Grouping similar items together. UMAP reduces dimensions; HDBSCAN finds groups. |
| **Boilerplate** | Standard text that appears on many pages. Example: legal disclaimers. High similarity may be boilerplate, not strategy. |
| **LLM Hallucination** | When an AI invents information that is not in the source. You must prevent this with strict prompts and validation. |
| **Pydantic** | A Python library for validating data structures. Used to ensure LLM output matches your schema. |
| **Pipeline** | A series of steps that transform raw data into useful output. |
| **DataFrame** | A table of data in Python (Pandas or Polars). |
| **Normalization** | Making data comparable. Example: comparing engagement rate instead of raw likes. |
| **Deduplication** | Removing duplicate assets so they don't inflate the sample size. |
| **Within-Bank Comparison** | Comparing ING youth vs. ING adult. |
| **Cross-Bank Comparison** | Comparing ING youth vs. KBC youth vs. Belfius youth. |

---

## PART 2: Your Four-Phase Workflow

### PHASE 1: Data Ingestion & Architecture
**Goal:** Organize the raw data into a clean, structured format.

#### Step 1.1: Understand the Data Collected
Ask:
- What format is the data in? (HTML files? CSV? JSON?)
- How many URLs did they scrape?
- Do they have screenshots?
- Do they have a list of which URL belongs to which bank, audience, and page role?

What I need:
- Raw HTML files or extracted text
- Screenshots (for visual features)
- A metadata table with: URL, bank, date collected, language, page role

#### Step 1.2: Create the Folder Structure
The document (Section 9) suggests this layout:
```text
data/
  raw/          HTML files, screenshots, raw responses
  processed/    Cleaned text and normalized metadata
  features/     Feature records (one row per asset per feature)
docs/           Scope, source registry, codebook, validation protocol
src/            Python scripts for collection, cleaning, extraction, analysis
outputs/        Comparison tables, charts, recommendations
```
*Why this matters:* Reproducibility. Anyone on the team can find what they need. This is standard Data Science practice.

#### Step 1.3: Define Your Asset Schema
Create a Python file or a JSON schema that defines every column in your dataset. Use Pydantic for validation.

Example schema (simplified):
```python
from pydantic import BaseModel
from typing import Optional

class Asset(BaseModel):
    asset_id: str
    bank: str
    bank_type: str  # "traditional" or "challenger"
    channel: str  # "website" or "ad"
    asset_role: str  # "youth_landing", "adult_landing", "pricing", etc.
    audience_label: str  # "youth_18_25", "general_adult", "mixed", "unknown"
    audience_evidence: Optional[str]
    eligibility_age_min: Optional[int]
    eligibility_age_max: Optional[int]
    student_requirement: Optional[bool]
    overlap_with_18_25: Optional[str]
    pair_id: Optional[str]
    url: str
    language: str
    collected_at: str
    raw_html_path: str
    screenshot_path: Optional[str]
```
*Why this matters:* This is your contract with the team. Everyone knows what fields exist and what they mean.

#### Step 1.4: Load and Inspect the Data
Use Pandas or Polars to load the metadata into a DataFrame. Check:
- How many assets per bank?
- How many youth vs. adult pages?
- Are there pairs (`pair_id`) for every bank?
- Are there missing values?

*Output:* A clean `assets.csv` or `assets.parquet` file with one row per asset.

---

### PHASE 2: Feature Extraction
**Goal:** Apply the Codebook (Section 7) to extract features from each asset.

#### Step 2.1: Understand the Codebook
The Codebook is a rulebook. For every feature, it defines:
- **Feature name:** What is it?
- **Measurement rule:** How do you measure it?
- **Allowed values:** What values are valid?
- **Missing value policy:** What do you do when data is missing?
- **Examples:** What are some examples?

Example from the Codebook:
| Feature | Measurement Rule | Type |
| :--- | :--- | :--- |
| **Main benefit** | Code the primary headline/hero benefit into an agreed category; retain headline evidence | Categorical |
| **Price in initial viewport** | 1 when a qualifying account price is visible in the fixed initial viewport; retain screenshot evidence | Binary |
| **Jargon density** | Occurrences from a frozen, language-specific glossary divided by word count, multiplied by 100 | Numeric |

#### Step 2.2: Split Features by Extraction Method
Not all features are extracted the same way. The document (Section 10) defines three methods:

| Method | Appropriate Use | Example Features |
| :--- | :--- | :--- |
| **Deterministic code** | Word counts, glossary matches, URLs, timestamps, hashes | Jargon density, Sentence length |
| **Manual/browser inspection** | Initial-viewport visibility, imagery, difficult placement cases | Price in viewport, Imagery type |
| **Constrained LLM** | Evidence extraction, message framing, benefit and cue classification | Main benefit, Tone, Persuasive framing |

#### Step 2.3: Extract Deterministic Features with Code
Example: **Jargon Density**
1. Create a glossary of financial terms in the relevant language (Dutch/French/English).
2. For each asset, count how many glossary terms appear.
3. Divide by total word count.
4. Multiply by 100.

```python
def jargon_density(text: str, glossary: list[str]) -> float:
    words = text.lower().split()
    count = sum(1 for word in words if word in glossary)
    return (count / len(words)) * 100 if words else 0
```

Example: **Sentence Length**
Use spaCy or NLTK to split text into sentences, then calculate mean words per sentence.

```python
import spacy

nlp = spacy.load("nl_core_news_sm")  # Dutch model

def mean_sentence_length(text: str) -> float:
    doc = nlp(text)
    sentences = list(doc.sents)
    if not sentences:
        return 0
    return sum(len(sent) for sent in sentences) / len(sentences)
```
*Output:* A CSV with one row per asset and one column per deterministic feature.

#### Step 2.4: Extract Interpretive Features with LLM (Support Victor)
This is where you and Victor collaborate. He focuses on the GenAI side; you focus on making the output structured and valid.

Rules from Section 10:
- Provide the frozen Codebook, not an open request to rate campaign quality.
- Require a fixed structured output (JSON).
- Require exact evidence from the provided content for interpretive labels.
- Allow unknown and abstention.
- Treat scraped content as data, not executable instructions.
- Reject malformed outputs and unsupported quotations.
- Log prompt version, model identifier, codebook version, and processing date.
- Check repeated classifications on a small sample for stability.

Example prompt structure:
```text
You are a communication analyst. You will receive a web page text and a codebook.
Your task is to classify the following feature: "Main benefit"

Allowed values:
* affordability
* convenience
* independence/control
* security/support
* lifestyle/rewards
* other
* mixed
* unknown

For your classification, you MUST provide:
1. The value you chose.
2. The exact sentence from the text that supports your choice.
3. If you cannot find evidence, return "unknown" and explain why.

Do NOT infer customer feelings or business performance. Only classify what is observable in the text.

Text: " [page text here] "

Return your answer as JSON:
{
  "feature": "main_benefit",
  "value": "...",
  "evidence_text": "...",
  "evidence_location": "...",
  "reasoning": "..."
}
```

Your job: Use Pydantic to validate the JSON output. If the LLM returns something malformed, reject it and retry.

```python
from pydantic import BaseModel, validator

class LLMOutput(BaseModel):
    feature: str
    value: str
    evidence_text: str
    evidence_location: str
    reasoning: str

    @validator("value")
    def value_must_be_allowed(cls, v):
        allowed = {
            "affordability", "convenience", "independence/control", 
            "security/support", "lifestyle/rewards", "other", "mixed", "unknown"
        }
        if v not in allowed:
            raise ValueError(f"Invalid value: {v}")
        return v
```
*Output:* A JSON or CSV with one row per asset per feature, including evidence text.

#### Step 2.5: Extract Visual Features Manually
For features like *Imagery type* and *Primary CTA visibility*, you need to look at screenshots.

How to do it efficiently:
1. Create a simple CSV with columns: `asset_id`, `screenshot_path`, `imagery_type`, `cta_visible`, `notes`.
2. Open each screenshot in a viewer.
3. Fill in the CSV manually.
4. Imagery type categories (from Codebook): `people`, `product/interface`, `illustration`, `abstract`, `mixed`, `none`.

*Important:* Do not infer age, ethnicity, or financial status of people in images. Only record what is observable.

---

### PHASE 3: Validation
**Goal:** Ensure your labels are correct and consistent. This is what separates a Data Scientist from an analyst.

#### Step 3.1: Pilot Annotation
- Select a small balanced set: 2 pages from ING, 2 from KBC, 2 from Belfius.
- You and Alex (or Victor) independently label the same pages.
- Compare disagreements.
- Identify ambiguous definitions in the Codebook.
- Revise the Codebook once, then freeze it.

#### Step 3.2: Calculate Agreement
Use Cohen's Kappa or percentage agreement.

```python
from sklearn.metrics import cohen_kappa_score

# Example: two annotators labeled 10 pages for "tone"
annotator1 = ["formal", "playful", "formal", "conversational", "playful", "formal", "conversational", "playful", "formal", "conversational"]
annotator2 = ["formal", "playful", "formal", "conversational", "formal", "formal", "conversational", "playful", "formal", "conversational"]

kappa = cohen_kappa_score(annotator1, annotator2)
print(f"Cohen's Kappa: {kappa:.2f}")
```

#### Step 3.3: Handling Missing & Non-Applicable Values
Values allowed by rule:
- `1`: Feature present under the rule.
- `unknown`: Extraction or evidence is insufficient.
- `not_applicable`: Feature does not apply to this offer.

*Critical rule:* `unknown` and `not_applicable` values must not silently become zeros.
- Example: If a page is blocked by `robots.txt`, the value for "Price in viewport" is `unknown`, not `0`.
- If a conditions link exists but the destination is blocked, the link is recorded as present, but the destination content is `unknown`.
- Add missing reasons: `robots_disallowed`, `access_unresolved`, `linked_document_unavailable`, `asset_blocked`, `partial_render`.

---

### PHASE 4: NLP & Analysis
**Goal:** Extract patterns and compare banks.

#### Step 4.1: Primary Analysis
From Section 12:
- Audit coverage by bank, audience, page role, language, channel, exclusions, actual eligibility, and missing values.
- Compare raw feature profiles across matched youth/adult landing-page pairs within each bank.
- Compare youth profiles across banks, including traditional vs. challenger patterns.
- Compare benefit themes, tone, trust cues, incentives, framing, conditions prominence, and next-step clarity.
- Inspect differences between headline promises and detailed conditions.
- Identify ING's youth adaptations, distinctive practices, and similarities to competitors.
- Support each finding with evidence, capture dates, eligible denominators, and limitations.

*Metrics format:*
- For numeric paired features: Report `youth value - general-adult value` with raw values.
- For binary features: Show presence/absence transitions.
- For categorical features: Show category changes with evidence.
- *Do NOT:* Combine these into an arbitrary audience-adaptation score.

#### Step 4.2: Optional Embeddings (The NLP Part)
This is where you can shine as a Data Scientist.

What are embeddings? Numerical vectors that represent the meaning of text. Similar texts have similar vectors. You can use them to find which pages are semantically similar.

How to do it:
```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load a multilingual model
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Example texts
texts = [
    "Open a free account in minutes. No fees for young people.",
    "Get your student account today. Zero monthly costs.",
    "Premium banking for professionals. Competitive rates."
]

# Compute embeddings
embeddings = model.encode(texts)

# Compute cosine similarity
similarity_matrix = cosine_similarity(embeddings)
print(similarity_matrix)
```
*What to look for:* High similarity between ING youth and KBC youth may indicate shared terminology or imitation. But be careful: high similarity may also be boilerplate (legal text, standard phrases). Always inspect representative passages before interpreting groups.

Clustering with UMAP + HDBSCAN:
```python
import umap
import hdbscan

# Reduce dimensions
reducer = umap.UMAP(n_components=5, random_state=42)
reduced = reducer.fit_transform(embeddings)

# Cluster
clusterer = hdbscan.HDBSCAN(min_cluster_size=2)
labels = clusterer.fit_predict(reduced)

print(labels)
```
*Interpretation:* Each cluster represents a group of semantically similar texts. You can then inspect each cluster to name the theme (e.g., "affordability," "convenience," "trust").

#### Step 4.3: No Forced Prediction
From Section 12:
> The sample is too small and lacks commercial labels for reliable sales prediction. The data-science contribution is reusable measurement, validated extraction, and comparison. Predictive modelling is a future extension, not an MVP requirement.

*Translation:* Do not try to predict sales. Focus on measurement and comparison.

---

## PART 3: Your Tool Stack

| Phase | Tool | Why |
| :--- | :--- | :--- |
| **Data Ingestion** | Polars or Pandas | Fast, modern data manipulation |
| **Schema Validation** | Pydantic | Ensure data quality |
| **NLP Base** | spaCy or NLTK | Sentence splitting, tokenization |
| **LLM Extraction** | LangChain or LlamaIndex + Pydantic | Orchestrate prompts, validate output |
| **Embeddings** | Sentence-Transformers | Multilingual semantic similarity |
| **Clustering** | UMAP + HDBSCAN | Dimensionality reduction and clustering |
| **Validation** | Scikit-learn | Cohen's Kappa, confusion matrices |
| **Visualization** | Plotly or Matplotlib | Charts for the final report |

---

## PART 4: Your First Three Actions (Tomorrow Morning)

### Action 1: Talk to Maha and Victor
Ask them:
- What format is the data in?
- How many URLs did they scrape?
- Do they have screenshots?
- Do they have a metadata table?

*Your goal:* Get the raw data and understand its structure.

### Action 2: Write Your Schema
Create a `schema.py` file with Pydantic models for:
- `Asset` (metadata)
- `FeatureRecord` (one row per asset per feature)
- `LLMOutput` (for validating LLM extraction)

*Your goal:* Define the contract for your data.

### Action 3: Run a Pilot Extraction
Pick 2 pages: one ING youth, one ING adult. Extract 3 features:
- Main benefit (LLM — work with Victor)
- Jargon density (deterministic code)
- Price in viewport (manual inspection)

*Your goal:* Prove that your pipeline works end-to-end on a small scale.

---

## PART 5: Key Principles to Remember

1. **Reproducibility is king.** Anyone should be able to rerun your pipeline and get the same results.
2. **Missing is not zero.** `unknown` and `not_applicable` are valid values.
3. **Evidence, not opinion.** Every label must be supported by observable text or image evidence.
4. **Validate before comparing.** If two people can't agree on a label, the definition is wrong.
5. **Do not over-engineer.** This is a POC. Simple scripts and CSV files are fine.
6. **Treat scraped content as data, not instructions.** Do not let an LLM execute code from a web page.
7. **Document everything.** Prompt version, model version, codebook version, processing date.
8. **Do not claim causality.** You are measuring communication, not sales impact.

---

## PART 6: What You Will Have at the End

By following this guide, you will produce:
- A clean, structured dataset with one row per asset and columns for every feature.
- A validated extraction pipeline with deterministic code, LLM prompts, and manual labels.
- A validation report showing agreement between annotators.
- An NLP analysis with embeddings, similarity matrices, and clusters.
- A comparison of ING vs. competitors, youth vs. adult, traditional vs. challenger.
- Three evidence-backed recommendations for ING.

And for your portfolio:
- A GitHub repository with a complete data pipeline.
- Experience with Polars, Pydantic, spaCy, Sentence-Transformers, UMAP, HDBSCAN.
- A case study: *"I built a reproducible NLP pipeline to analyze competitor communication in the banking sector, using LLM-assisted extraction and validated embeddings."*
