# Data Scientist's Complete Guide: ING Youth Acquisition Communication Comparator
## A Step-by-Step Manual for Learning While Building

---

### HOW TO USE THIS GUIDE
This guide is designed to be read in order, from start to finish. Each part builds on the previous one. When you encounter a term you don't know, it is explained in Part 1 (Glossary) and again in context when it first appears.

The guide follows the actual chronological workflow of the project:
- First, you understand the project and the vocabulary (Parts 0–2).
- Then, you do pre-work while waiting for data (Part 3).
- Then, you receive data and build the pipeline (Parts 4–7).
- Finally, you analyze and deliver (Parts 8–9).

Each step tells you:
- **What to do** (the action)
- **Why it matters** (the reasoning)
- **How to do it** (code or procedure)
- **How to know you're done** (the acceptance gate)

---

### PART 0: UNDERSTANDING THE PROJECT

#### 0.1 What is this project, in plain English?
ING wants to know how banks (including themselves) talk to young people (aged 18–25) when offering them a current account. They want to compare:
- **Within ING:** How ING talks to young people vs. how ING talks to adults.
- **Across banks:** How ING talks to young people vs. how KBC, Belfius, and Revolut talk to young people.

The output is a **communication comparison** — not a sales prediction. You are not measuring "which bank gets more customers." You are measuring "which bank says what, how, and where."

#### 0.2 Why is this not a sales model?
Because you have no internal data. You don't know how many people opened an account after seeing a page. You only have public web pages and ads. So the project is about **observable communication features**, not business outcomes.

#### 0.3 What is an MVP?
**MVP = Minimum Viable Product.** It means: the smallest version of the project that still delivers value. In this case, 8 days, a small sample of pages, a validated pipeline, and three recommendations. It is not a production system. It is a proof that the method works.

#### 0.4 What is a POC?
**POC = Proof of Concept.** Same idea as MVP. It proves that something is feasible. ING asked for a POC, not a production tool. So do not over-engineer.

#### 0.5 What are the final deliverables?
At the end of the project, the team will produce:
1. A one-page executive summary for ING's management.
2. A comparison table showing feature profiles across banks.
3. Three evidence-backed recommendations for ING.
4. A technical package (code, data, documentation) that proves the pipeline is reproducible.

Your role as Data Scientist is to build the technical foundation that makes all of this possible.

---

### PART 1: COMPLETE GLOSSARY OF TERMS

Read this section once. Come back to it whenever you encounter a term you don't remember. This glossary covers every technical term used in the project document and in this guide.

| Term | Plain English Explanation |
| :--- | :--- |
| **Asset** | One unit of content. A web page, an ad, a screenshot. Each asset gets a unique ID. |
| **Asset ID** | A unique code for each asset. Example: `ING_YOUTH_001`. |
| **Audience Label** | A tag that says who the content is for. Values: `youth_18_25`, `adult_student`, `general_adult`, `mixed_age`, `unknown`. |
| **Boilerplate** | Standard text that appears on many pages. Example: legal disclaimers. High similarity may be boilerplate, not strategy. |
| **Codebook** | A rulebook. It defines every feature you will measure, how to measure it, what values are allowed, and how to handle missing data. Think of it as a data dictionary with strict rules. |
| **Cohen's Kappa** | A statistical measure of agreement between two annotators. 1 = perfect agreement, 0 = random. Used to validate that two people label the same data the same way. |
| **Cosine Similarity** | A measure of how similar two vectors are. Used to compare embeddings. |
| **Cross-Bank Comparison** | Comparing ING youth vs. KBC youth vs. Belfius youth. |
| **CTA** | Call to Action. The button or link that asks the user to do something. Example: "Open an account" or "Learn more." |
| **Clustering** | Grouping similar items together. UMAP reduces dimensions; HDBSCAN finds groups. |
| **DataFrame** | A table of data in Python (Pandas or Polars). |
| **Deduplication** | Removing duplicate assets so they don't inflate the sample size. |
| **Deterministic Feature** | A feature you can extract with code, with no interpretation. Example: word count. |
| **Embeddings** | Numerical vectors that represent the meaning of text. Similar texts have similar vectors. |
| **Feature** | A single measurable characteristic of a page. Example: "Is the price visible in the first screen?" or "How many jargon words per 100 words?" |
| **Feature Record** | One row in your dataset that contains the value of a single feature for a single asset. |
| **Interpretive Feature** | A feature that requires judgment. Example: "Is the tone playful or formal?" |
| **Jargon Density** | How many technical or financial terms appear per 100 words. High jargon = harder to read. |
| **Landing Page** | The main page a customer sees when they click an ad or search result. It is the primary comparison unit. |
| **LLM Hallucination** | When an AI invents information that is not in the source. You must prevent this with strict prompts and validation. |
| **Metadata** | Data about the data. Example: bank name, language, date collected, URL, page role. |
| **Missing Value** | A value you could not extract. It is not zero. It is `unknown` or `not_applicable`. |
| **Normalization** | Making data comparable. Example: comparing engagement rate instead of raw likes. |
| **Page Role** | What kind of page is it? Youth landing page? Adult landing page? Pricing page? Conditions page? |
| **Pair ID** | A code that links two assets that should be compared. Example: `ING_PAIR_01` links ING's youth page and ING's adult page for the same product. |
| **Persuasive Framing** | How the message is framed. Gain framing = "Save money." Loss framing = "Don't lose money." |
| **Pipeline** | A series of steps that transform raw data into useful output. |
| **Provenance** | The origin and history of a piece of data. Where did it come from? When? How? |
| **Pydantic** | A Python library for validating data structures. Used to ensure LLM output matches your schema. |
| **Robots.txt** | A file on a website that tells bots what they are allowed to crawl. It is a technical signal, not a legal permission. |
| **Schema** | A formal definition of the structure of your data. In Python, defined using Pydantic classes. |
| **Sentence Length** | The mean number of words per sentence in a text. A measure of readability. |
| **Validation** | The process of checking that your labels are correct and consistent. |
| **Viewport** | The visible area of a browser window. "Initial viewport" means what you see before scrolling. |
| **Within-Bank Comparison** | Comparing ING youth vs. ING adult. |

---

### PART 2: THE BIG PICTURE WORKFLOW

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: PRE-WORK (No data needed)                              │
│ - Define schema (Pydantic)                                      │
│ - Create glossary for jargon density                            │
│ - Write deterministic extraction functions                      │
│ - Prepare LLM prompts (with Victor)                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: DATA INGESTION (When Maha/Victor deliver data)         │
│ - Receive raw HTML, screenshots, metadata CSV                   │
│ - Validate metadata against schema                              │
│ - Create folder structure                                       │
│ - Load and inspect data                                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: TEXT CLEANING & PREPROCESSING                          │
│ - Extract main content from HTML (remove nav, footer)           │
│ - Normalize text (lowercase, remove extra spaces)               │
│ - Save cleaned text to data/processed/                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: FEATURE EXTRACTION                                     │
│ - Deterministic features (code): jargon, sentence length        │
│ - Interpretive features (LLM): main benefit, tone, framing      │
│ - Visual features (manual): imagery type, CTA visibility        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: VALIDATION                                             │
│ - Pilot annotation (2 people label same pages)                  │
│ - Calculate Cohen's Kappa                                       │
│ - Revise codebook if needed                                     │
│ - Freeze codebook                                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: ANALYSIS                                               │
│ - Primary analysis (feature profiles, within/cross-bank)        │
│ - Optional: embeddings, clustering, similarity                  │
│ - No forced prediction                                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: OUTPUT                                                 │
│ - Feature dataset (CSV)                                         │
│ - Comparison tables                                             │
│ - Visualizations                                                │
│ - Handoff to Alex for recommendations                           │
└─────────────────────────────────────────────────────────────────┘
```

---

### PART 3: PHASE 0 — PRE-WORK (No Data Needed)

This is what you do right now, while Maha and Victor are still scraping. You are building the factory before the raw materials arrive.

#### Step 3.1: Create the Folder Structure
- **What to do:** Create the project folder structure on your machine.
- **Why it matters:** Reproducibility. Anyone on the team can find what they need. This is standard Data Science practice.
- **How to do it:**
  ```bash
  mkdir -p ing_project/{data/{raw,processed,features},docs,src,outputs}
  cd ing_project
  ```
  The structure should look like this:
  ```
  ing_project/
  ├── data/
  │   ├── raw/          # HTML files, screenshots, raw responses
  │   ├── processed/    # Cleaned text and normalized metadata
  │   └── features/     # Feature records (one row per asset per feature)
  ├── docs/             # Scope, source registry, codebook, validation protocol
  ├── src/              # Python scripts for collection, cleaning, extraction, analysis
  └── outputs/          # Comparison tables, charts, recommendations
  ```
- **How to know you're done:** You can navigate to `ing_project/` and see all the folders.

#### Step 3.2: Define Your Asset Schema (with Pydantic)
- **What to do:** Create a file `src/schema.py` that defines the structure of every asset in your dataset.
- **Why it matters:** This is your contract with the team. When Maha and Victor give you the metadata CSV, Pydantic will immediately tell you if anything is missing or malformed. This prevents garbage data from entering your pipeline.
- **What is Pydantic?** Pydantic is a Python library that validates data structures. You define a class with typed fields, and Pydantic ensures that any data you pass to it matches those types. If it doesn't, Pydantic raises a clear error.
- **How to do it:**
  Create `src/schema.py`:
  ```python
  from pydantic import BaseModel
  from typing import Optional

  class AssetMetadata(BaseModel):
      asset_id: str
      bank: str
      bank_type: str  # "traditional" or "challenger"
      channel: str  # "website" or "ad"
      asset_role: str  # "youth_landing", "adult_landing", "pricing", etc.
      audience_label: str  # "youth_18_25", "general_adult", "mixed", "unknown"
      audience_evidence: Optional[str] = None
      eligibility_age_min: Optional[int] = None
      eligibility_age_max: Optional[int] = None
      student_requirement: Optional[bool] = None
      overlap_with_18_25: Optional[str] = None
      pair_id: Optional[str] = None
      url: str
      language: str
      collected_at: str
      raw_html_path: str
      screenshot_path: Optional[str] = None

  class FeatureRecord(BaseModel):
      asset_id: str
      feature_name: str
      value: str  # Can be numeric, binary, or categorical
      missing_status: Optional[str] = None  # "unknown", "not_applicable", etc.
      missing_reason: Optional[str] = None  # "robots_disallowed", etc.
      evidence_text: Optional[str] = None
      evidence_location: Optional[str] = None
      method: str  # "deterministic", "llm", "manual"
      codebook_version: str
      prompt_version: Optional[str] = None
      review_status: str  # "pending", "validated", "rejected"

  class LLMOutput(BaseModel):
      feature: str
      value: str
      evidence_text: str
      evidence_location: str
      reasoning: str
  ```
- **How to know you're done:** You can import the file without errors:
  ```python
  from src.schema import AssetMetadata, FeatureRecord, LLMOutput
  ```

#### Step 3.3: Create the Glossary for Jargon Density
- **What to do:** Create a file `data/glossary.json` containing a list of financial terms in Dutch, French, and English.
- **Why it matters:** One of the deterministic features is "Jargon Density" — how many technical terms appear per 100 words. You need a list of terms to count.
- **How to do it:**
  Create `data/glossary.json`:
  ```json
  {
    "en": [
      "interest", "rate", "fee", "commission", "IBAN", "debit card", "credit card", "overdraft", "mortgage", "loan", "savings", "current account", "transaction", "balance", "statement", "withdrawal", "deposit", "transfer", "standing order", "direct debit", "PIN", "ATM", "online banking", "mobile banking", "app", "authentication", "two-factor", "encryption", "GDPR", "terms and conditions", "eligibility", "minimum age", "student", "bonus", "promotion", "welcome offer", "cashback", "interest rate", "variable rate", "fixed rate", "APR", "EAR", "compound interest"
    ],
    "nl": [
      "rente", "tarief", "kosten", "commissie", "IBAN", "debetaart", "kredietkaart", "roodstand", "hypotheek", "lening", "spaargeld", "betaalrekening", "transactie", "saldo", "afschrift", "opname", "storting", "overschrijving", "doorlopende opdracht", "domiciliëring", "pincode", "geldautomaat", "online bankieren", "mobiel bankieren", "app", "authenticatie", "twee-factor", "encryptie", "GDPR", "algemene voorwaarden", "geschiktheid", "minimumleeftijd", "student", "bonus", "promotie", "welkomstvoordeel", "cashback", "rentevoet", "variabele rente", "vaste rente", "JKP", "effectieve rente", "samengestelde interest"
    ],
    "fr": [
      "intérêt", "taux", "frais", "commission", "IBAN", "carte de débit", "carte de crédit", "découvert", "hypothèque", "prêt", "épargne", "compte courant", "transaction", "solde", "relevé", "retrait", "dépôt", "virement", "ordre permanent", "domiciliation", "code PIN", "distributeur", "banque en ligne", "banque mobile", "application", "authentification", "deux facteurs", "chiffrement", "RGPD", "conditions générales", "éligibilité", "âge minimum", "étudiant", "bonus", "promotion", "offre de bienvenue", "cashback", "taux d'intérêt", "taux variable", "taux fixe", "TAEG", "taux effectif", "intérêt composé"
    ]
  }
  ```
- **How to know you're done:** You can load the file and count the terms:
  ```python
  import json
  with open("data/glossary.json", "r") as f:
      glossary = json.load(f)
  print(f"English terms: {len(glossary['en'])}")
  print(f"Dutch terms: {len(glossary['nl'])}")
  print(f"French terms: {len(glossary['fr'])}")
  ```

#### Step 3.4: Write Deterministic Extraction Functions
- **What to do:** Write Python functions that calculate deterministic features from text.
- **Why it matters:** These features require no interpretation. They are pure code. You can test them now, with fake text, so they are ready when real data arrives.
- **How to do it:**
  Create `src/extract_deterministic.py`:
  ```python
  import json
  import spacy

  nlp_nl = spacy.load("nl_core_news_sm")
  nlp_fr = spacy.load("fr_core_news_sm")
  nlp_en = spacy.load("en_core_web_sm")

  def load_glossary(path: str = "data/glossary.json") -> dict:
      with open(path, "r") as f:
          return json.load(f)

  def jargon_density(text: str, language: str, glossary: dict) -> float:
      words = text.lower().split()
      if not words:
          return 0.0
      terms = glossary.get(language, [])
      count = sum(1 for word in words if word in terms)
      return (count / len(words)) * 100

  def mean_sentence_length(text: str, language: str) -> float:
      if language == "nl":
          nlp = nlp_nl
      elif language == "fr":
          nlp = nlp_fr
      else:
          nlp = nlp_en

      doc = nlp(text)
      sentences = list(doc.sents)
      if not sentences:
          return 0.0
      return sum(len(sent) for sent in sentences) / len(sentences)

  def word_count(text: str) -> int:
      return len(text.split())
  ```
- **How to test it:**
  Create `src/test_deterministic.py`:
  ```python
  from src.extract_deterministic import (
      load_glossary, jargon_density, mean_sentence_length, word_count
  )

  glossary = load_glossary()
  fake_text = (
      "Open a free account in minutes. No fees for young people. "
      "Get your debit card today. Zero monthly costs. "
      "Apply online and get a 50 euro bonus."
  )

  print(f"Word count: {word_count(fake_text)}")
  print(f"Jargon density: {jargon_density(fake_text, 'en', glossary):.2f} per 100 words")
  print(f"Mean sentence length: {mean_sentence_length(fake_text, 'en'):.2f} words")
  ```
- **How to know you're done:** The test prints reasonable numbers and does not crash.

### PART 3.5: EXTENDED PHASE 0 – MOCK DATA & PRE-WORK
#### Why This Phase Exists
In the original workflow, Phase 0 was limited to defining the schema, creating a glossary, and preparing prompts. But you can do much more before Maha and Victor deliver the real data. The goal is to build the entire pipeline and test it end-to-end with fake data (mock data). When the real data arrives, you simply replace the mock files and run the same scripts. This eliminates downtime and ensures your code works before you depend on it.

#### Part A: The Mock Data Strategy
**What is mock data?**  
Mock data is artificially created data that mimics the structure and format of the real data you will receive. It allows you to develop and test your code without waiting for the actual scraped files.

**Why use it?**  
* You can build and debug your pipeline now.
* You can identify missing fields or structural issues early.
* When real data arrives, you only need to swap files, not rewrite code.

**How to create mock data:**  
1. Create a mock HTML file
  * Pick any simple web page (e.g., a news article, a blog post).
  * Save it as data/raw/ING_YOUTH_001.html.  
  * This will be used to test your HTML parser.  
2. Create a mock metadata CSV
  * Create data/raw/metadata.csv with a few rows that follow your Pydantic schema.
  * Example:
  ```csv
  asset_id,bank,bank_type,channel,asset_role,audience_label,audience_evidence,eligibility_age_min,eligibility_age_max,student_requirement,overlap_with_18_25,pair_id,url,language,collected_at,raw_html_path,screenshot_path
  ING_YOUTH_001,ING,traditional,website,youth_landing,youth_18_25,"Explicitly says 'for young people'",18,25,false,full,ING_PAIR_01,https://example.com/ing-youth,en,2026-09-15,data/raw/ING_YOUTH_001.html,data/raw/ING_YOUTH_001.png
  ING_ADULT_001,ING,traditional,website,adult_landing,general_adult,,18,99,false,none,ING_PAIR_01,https://example.com/ing-adult,en,2026-09-15,data/raw/ING_ADULT_001.html,data/raw/ING_ADULT_001.png
  Run the entire pipeline on mock data
  ```
3. Run the entire pipeline on mock data
  * Execute your scripts: ingestion → cleaning → extraction → validation.
  * Fix any bugs that appear.
  * Once it works, you are ready for real data.

#### Part B: Six Actions You Can Do Now
These are concrete tasks you can complete today, without any real data from Maha or Victor.

***1. Define Your Schema (Pydantic)***
**Action:** Write src/schema.py with the classes AssetMetadata, FeatureRecord, and LLMOutput.  
**Why:** This is your data contract. When Maha sends the metadata CSV, Pydantic will immediately tell you if any field is missing or wrong.  
**Example code:**

```python
from pydantic import BaseModel
from typing import Optional

class AssetMetadata(BaseModel):
    asset_id: str
    bank: str
    bank_type: str  # "traditional" or "challenger"
    channel: str  # "website" or "ad"
    asset_role: str  # "youth_landing", "adult_landing", etc.
    audience_label: str  # "youth_18_25", "general_adult", etc.
    audience_evidence: Optional[str] = None
    eligibility_age_min: Optional[int] = None
    eligibility_age_max: Optional[int] = None
    student_requirement: Optional[bool] = None
    overlap_with_18_25: Optional[str] = None
    pair_id: Optional[str] = None
    url: str
    language: str
    collected_at: str
    raw_html_path: str
    screenshot_path: Optional[str] = None

class FeatureRecord(BaseModel):
    asset_id: str
    feature_name: str
    value: str
    missing_status: Optional[str] = None
    missing_reason: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_location: Optional[str] = None
    method: str
    codebook_version: str
    prompt_version: Optional[str] = None
    review_status: str

class LLMOutput(BaseModel):
    feature: str
    value: str
    evidence_text: str
    evidence_location: str
    reasoning: str
```
**Test:** Import the file with from src.schema import AssetMetadata and ensure no errors.

***2. Create the Glossary for Jargon Density***
**Action:** Create data/glossary.json with 50–100 financial terms in English, Dutch, and French.
**Why:** Jargon density is a deterministic feature. You need a list of terms to count. This is tedious but necessary work you can do now.
**Example structure:**

```json
{
  "en": ["interest", "rate", "fee", "commission", "IBAN", "debit card", ...],
  "nl": ["rente", "tarief", "kosten", "commissie", "IBAN", "debetaart", ...],
  "fr": ["intérêt", "taux", "frais", "commission", "IBAN", "carte de débit", ...]
}
```
**Test:** Load the file and print the number of terms.

***3. Write Deterministic Extraction Functions***
**Action:** Write Python functions to calculate sentence_length and jargon_density.
**Why:** These are pure code. You can test them with fake text now. When real HTML arrives, you just pass the cleaned text.
**Example code (`src/extract_deterministic.py`):**

```python
import json
import spacy

nlp_nl = spacy.load("nl_core_news_sm")
nlp_fr = spacy.load("fr_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

def load_glossary(path="data/glossary.json"):
    with open(path, "r") as f:
        return json.load(f)

def jargon_density(text, language, glossary):
    words = text.lower().split()
    if not words:
        return 0.0
    terms = glossary.get(language, [])
    count = sum(1 for w in words if w in terms)
    return (count / len(words)) * 100

def mean_sentence_length(text, language):
    nlp = {"nl": nlp_nl, "fr": nlp_fr, "en": nlp_en}[language]
    doc = nlp(text)
    sents = list(doc.sents)
    if not sents:
        return 0.0
    return sum(len(s) for s in sents) / len(sents)
```
**Test:** Use a fake text like:

```python
fake_text = "Open a free account. No fees. Get a bonus."
print(jargon_density(fake_text, "en", load_glossary()))
print(mean_sentence_length(fake_text, "en"))
```

***4. Write the HTML Parser***
**Action:** Write extract_main_content(html_path) using BeautifulSoup to remove navigation, footer, and scripts.
**Why:** This is the most common bottleneck when real HTML arrives. Test it on a mock HTML file.
**Example code (`src/clean_html.py`):**

```python
from bs4 import BeautifulSoup
import re

def extract_main_content(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text
```
**Test:** Create a simple HTML file with <nav>, <footer>, and main content, then run the parser.

***5. Prepare the LLM Prompt (with Victor)***
**Action:** Write the prompt for classifying main_benefit (and later tone, persuasive_framing).
**Why:** The LLM must return structured JSON with evidence. Test it with a fake text.
**Example prompt (`src/prompts.py`):**

```python
MAIN_BENEFIT_PROMPT = """
You are a communication analyst. Classify the main benefit of the following text.

Allowed values:
- affordability
- convenience
- independence/control
- security/support
- lifestyle/rewards
- other
- mixed
- unknown

You MUST provide the exact sentence that supports your choice. If you cannot find evidence, return "unknown".

Text:
\"\"\"
{text}
\"\"\"

Return JSON:
{{
  "feature": "main_benefit",
  "value": "...",
  "evidence_text": "...",
  "evidence_location": "...",
  "reasoning": "..."
}}
"""
```
**Test:** Ask Victor to run it through an LLM with:
```text
Open an under-30 account, zero fees, €50 bonus.
```
Check that the JSON is valid and the value is from the allowed list.

***6. Create the Orchestration Script (`main.py`)***
**Action:** Write src/main.py that calls the pipeline steps in order.
**Why:** This is your "one button" to run everything. When real data arrives, you just replace files and run this script.
**Example skeleton:**
```python
import polars as pl
from src.schema import AssetMetadata
from src.clean_html import extract_main_content
from src.extract_deterministic import load_glossary, jargon_density, mean_sentence_length

def run_ingestion():
    df = pl.read_csv("data/raw/metadata.csv")
    # validate with Pydantic, save to data/processed/assets.parquet
    pass

def run_cleaning():
    # for each asset, extract main content and save to data/processed/{asset_id}.txt
    pass

def run_extraction():
    # compute deterministic features, call LLM, manual labels
    pass

def run_validation():
    # compute Cohen's kappa, revise codebook
    pass

if __name__ == "__main__":
    run_ingestion()
    run_cleaning()
    run_extraction()
    run_validation()
    print("Pipeline completed.")
```
**Test:** Run python src/main.py on your mock data. Fix any errors.

***What Happens When Real Data Arrives***
1. Replace data/raw/metadata.csv and HTML files with the real ones.
2. Run python src/main.py.
3. The pipeline will validate, clean, extract, and produce outputs/feature_dataset.csv.
4. You then proceed to Phase 4 (Validation) and Phase 5 (Analysis).

By doing this pre-work, you turn a waiting period into productive preparation. You will be ready to execute immediately when Maha and Victor deliver.

#### Step 3.6: Prepare the LLM Prompt (with Victor)
- **What to do:** Write the prompt that will be used to classify interpretive features (Main Benefit, Tone, Persuasive Framing).
- **Why it matters:** The LLM must return structured JSON with evidence. If the prompt is vague, the LLM will hallucinate or return malformed output. You and Victor need to design this prompt together.
- **How to do it:**
  Create `src/prompts.py`:
  ```python
  MAIN_BENEFIT_PROMPT = """
  You are a communication analyst. You will receive a web page text and a codebook.

  Your task is to classify the following feature: "Main Benefit"

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

  Text: """{text}"""

  Return your answer as JSON:
  {{
    "feature": "main_benefit",
    "value": "...",
    "evidence_text": "...",
    "evidence_location": "...",
    "reasoning": "..."
  }}
  """
  ```
- **How to know you're done:** The LLM returns valid JSON that Pydantic can validate without errors.

---

### PART 4: PHASE 1 — DATA INGESTION (When Data Arrives)

#### Step 4.1: Receive and Inspect the Data
- **What to do:** Ask Maha and Victor for raw HTML files, screenshots, and a metadata CSV.
- **Why it matters:** You cannot build a pipeline without knowing the shape of the data.
- **How to do it:** Load the metadata CSV and inspect it using Pandas/Polars.

#### Step 4.2: Validate Metadata Against Schema
- **What to do:** Use Pydantic to validate every row of the metadata CSV.
- **Why it matters:** Catching errors in metadata early prevents hours of debugging later.
- **How to do it:**
  ```python
  from src.schema import AssetMetadata
  from pydantic import ValidationError

  valid_assets = []
  invalid_assets = []

  for _, row in df.iterrows():
      try:
          asset = AssetMetadata(**row.to_dict())
          valid_assets.append(asset)
      except ValidationError as e:
          invalid_assets.append((row["asset_id"], e))

  print(f"Valid assets: {len(valid_assets)}, Invalid assets: {len(invalid_assets)}")
  ```

#### Step 4.3: Load and Save the Clean Asset Table
- **What to do:** Save validated assets as `data/processed/assets.parquet`.

---

### PART 5: PHASE 2 — TEXT CLEANING & PREPROCESSING

#### Step 5.1: Extract Main Content from HTML
- **What to do:** For each HTML file, extract the main content and remove script, style, nav, footer, header, and aside tags using BeautifulSoup.

#### Step 5.2: Save Cleaned Text
- **What to do:** Save cleaned text for each asset to `data/processed/{asset_id}.txt`.

---

### PART 6: PHASE 3 — FEATURE EXTRACTION

#### Step 6.1: Extract Deterministic Features
- **What to do:** Compute jargon density, sentence length, and word count for each asset and save to `data/features/deterministic.parquet`.

#### Step 6.2: Extract Interpretive Features with LLM
- **What to do:** Send cleaned text to the LLM with structured prompts, validate responses with Pydantic (`LLMOutput`), and save to `data/features/llm.parquet`.

#### Step 6.3: Extract Visual Features Manually
- **What to do:** Inspect screenshots and fill in `data/features/visual_manual.csv` with `imagery_type` (`people`, `product/interface`, `illustration`, `abstract`, `mixed`, `none`) and `primary_cta_visible`.

---

### PART 7: PHASE 4 — VALIDATION

#### Step 7.1: Pilot Annotation
- **What to do:** Select 6 representative pages (2 ING, 2 KBC, 2 Belfius). Two annotators independently label the same interpretive features.

#### Step 7.2: Calculate Agreement
- **What to do:** Compute Cohen's Kappa using `scikit-learn`:
  ```python
  from sklearn.metrics import cohen_kappa_score
  kappa = cohen_kappa_score(annotator1, annotator2)
  ```
  - **Target:** Aim for Cohen's Kappa >= 0.60 for interpretive features.

#### Step 7.3: Revise and Freeze the Codebook
- **What to do:** If agreement is low, clarify ambiguous feature definitions, update `docs/codebook.md`, version it (e.g., `v1.1`), and freeze it.

#### Step 7.4: Handle Missing Values Correctly
- **Critical rule:** `unknown` and `not_applicable` values must NOT be converted to zero.
- **Log missing reasons:** `robots_disallowed`, `access_unresolved`, `linked_document_unavailable`, `asset_blocked`, `partial_render`.

---

### PART 8: PHASE 5 — ANALYSIS

#### Step 8.1: Primary Analysis
- **What to do:** Compare feature profiles across banks and audience groups.
  - Within-bank: ING Youth vs. ING Adult.
  - Cross-bank: ING Youth vs. KBC / Belfius / Revolut Youth.
  - Traditional vs. Challenger patterns.

#### Step 8.2: Optional Embeddings & Clustering
- **What to do:** Use `SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")` to generate text embeddings, calculate cosine similarity matrices, and run UMAP + HDBSCAN clustering to discover semantic themes.

#### Step 8.3: No Forced Prediction
- **What to do:** Do not attempt sales or conversion predictions due to small sample size and lack of internal performance metrics.

---

### PART 9: PHASE 6 — OUTPUT

#### Step 9.1: Build the Feature Dataset
- **What to do:** Consolidate feature records into wide format and export to `outputs/feature_dataset.csv`.

#### Step 9.2: Create Comparison Tables
- **What to do:** Generate within-bank and cross-bank comparative matrices in Markdown and CSV.

#### Step 9.3: Handoff
- **What to do:** Deliver feature datasets, comparison tables, and analytical findings to Alex for final recommendation drafting.

---

### PART 10: TOOL STACK SUMMARY

| Phase | Tool | Why |
| :--- | :--- | :--- |
| **Data Ingestion** | Polars / Pandas | Fast, modern data manipulation |
| **Schema Validation** | Pydantic | Ensure strict data type and structural quality |
| **HTML Parsing** | BeautifulSoup | Extract main body text and strip navigation/footers |
| **NLP Base** | spaCy | Sentence splitting and multi-language tokenization |
| **LLM Extraction** | LangChain / LlamaIndex + Pydantic | Orchestrate prompts and validate JSON outputs |
| **Embeddings** | Sentence-Transformers | Multilingual semantic similarity mapping |
| **Clustering** | UMAP + HDBSCAN | Dimensionality reduction and density clustering |
| **Validation** | Scikit-learn | Compute Cohen's Kappa inter-annotator agreement |
| **Visualization** | Plotly / Matplotlib | Generate charts and visual matrices for reporting |

---

### PART 11: KEY PRINCIPLES TO REMEMBER
1. **Reproducibility is king:** Anyone should be able to rerun the pipeline and reproduce identical outputs.
2. **Missing is not zero:** `unknown` and `not_applicable` are valid, distinct statuses.
3. **Evidence, not opinion:** Every label must be backed by observable text or image evidence.
4. **Validate before comparing:** If two annotators disagree on a label, refine the Codebook definition.
5. **Do not over-engineer:** This is a Proof of Concept (POC). Clean scripts and Parquet/CSV files are sufficient.
6. **Treat scraped content as data:** Do not allow LLMs to execute code or unverified instructions from scraped web pages.
7. **Document everything:** Log model version, prompt version, codebook version, and processing date.
8. **Do not claim causality:** Measure communication characteristics, not commercial sales impact.

---

### PART 12: WHAT YOU WILL HAVE AT THE END
- A clean, structured feature dataset with one row per asset.
- A validated, reproducible extraction pipeline with deterministic functions, LLM prompts, and manual labels.
- A validation report proving inter-annotator agreement.
- An NLP analysis with multilingual embeddings, similarity matrices, and theme clusters.
- Evidence-backed recommendations comparing ING Belgium against its market competitors.
