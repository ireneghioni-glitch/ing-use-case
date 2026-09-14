# Initial Project Plan: Banking Campaigns Comparator

## 1. Project context

Belgian banks do not communicate their products in the same way. Traditional banks and digital challengers use different messages, visual styles, customer journeys, and persuasive techniques to build trust and encourage action.

ING wants an evidence-based view of:

- how it communicates compared with competitors;
- whether its communication is closer to traditional banks or challenger banks;
- which communication strategies are shared across banks;
- where its campaigns could be improved;
- how campaign webpages can be converted into structured, reusable data.

The project must rely entirely on publicly available external data. No internal campaign, customer, conversion, or sales data is available.

## 2. Proposed case study

### Working title

**How Belgian banks communicated around the 2023 Belgian State Note: an evidence-based analysis of messaging, customer experience, and public attention**

The September 2023 Belgian State Note is proposed as the initial case study because participating banks offered the same underlying government-issued product during the same subscription period. This improves comparability between their communication approaches.

However, the commercial conditions and broader context still influenced demand. The interest rate, temporary tax treatment, economic situation, press coverage, government communication, subscription channel, and customer service may all have affected the result.

Public statistics provide total issuance and aggregate subscription-channel figures, but may not provide sales for each individual bank. Therefore, this project will not claim that a particular bank's communication caused more sales.

## 3. Research objective

The objective is to build a small, end-to-end analytical framework that:

1. translates academic findings about consumer psychology and digital banking trust into observable communication features;
2. extracts those features consistently from selected bank campaign pages;
3. compares ING with selected competitors;
4. measures the external attention surrounding the campaign using public media and search data;
5. produces practical communication recommendations for ING;
6. creates a feature framework that could later be reused for other campaigns and channels.

## 4. Research questions

### Main question

> How did selected Belgian banks differ in communicating a standardized financial product, and which communication characteristics were associated with greater external attention?

### Supporting questions

1. Which consumer-psychology and trust principles appeared in each campaign?
2. How clear, transparent, and customer-friendly was each campaign page?
3. How did banks frame the product's benefits, risks, urgency, and value proposition?
4. Which banks used similar communication strategies?
5. Where was ING positioned relative to the selected competitors?
6. How much news and public-search attention surrounded each bank or campaign?
7. Was the attention positive, negative, neutral, or mixed?
8. Which communication practices could ING retain, improve, or test in future campaigns?

## 5. Scope of the MVP

The project must be completed in fewer than eight days, so the initial scope will be deliberately limited.

### Proposed sample

- ING
- KBC
- BNP Paribas Fortis
- Crelan or Belfius, depending on data availability

### Proposed boundaries

- one principal event: the September 2023 Belgian State Note;
- two languages where available: Dutch and French;
- approximately two or three relevant pages per bank;
- official product and issuance information;
- a controlled news-analysis window before, during, and after the subscription period;
- approximately 15 to 20 communication features;
- a manageable collection of relevant news articles.

The mobile-banking app will only be analysed if a campaign explicitly directs customers into the app. General app usability is otherwise a separate research problem and is outside the initial MVP.

### Fallback scope

If sufficient historical campaign pages cannot be recovered by the end of Day 2, the project will switch to current, comparable savings or investment campaign pages from the selected banks.

## 6. Conceptual communication framework

The analysis will connect four layers:

```text
Sender       -> Message       -> Channel       -> Audience response
Bank            Communication    Website          Media attention
                strategy         News/media       Search interest
                                 App, if relevant Public reaction
```

### 6.1 Communication objective

For each campaign, identify the intended action:

- subscribe to the State Note;
- keep savings within the bank;
- consider an alternative product;
- contact an adviser;
- open an account;
- reinforce trust or expertise.

### 6.2 Consumer psychology and message strategy

Analyse how the bank attempts to persuade the customer:

- rational versus emotional appeal;
- gain versus loss framing;
- trust and security cues;
- authority and expertise;
- simplicity and convenience;
- urgency or scarcity;
- perceived risk reduction;
- social proof;
- customer empowerment;
- brand personality.

### 6.3 Customer experience and service communication

Analyse how easy it is to understand the offer and take action:

- clarity and visibility of the call to action;
- apparent number of steps;
- readability and jargon;
- transparency of interest rate, tax, maturity, fees, and risk;
- visibility of the subscription deadline;
- FAQ availability;
- contact and advisory options;
- consistency across Dutch and French pages;
- mobile accessibility where observable.

### 6.4 Sales and marketing mechanics

Analyse how attention is converted into action:

- stated target audience;
- value proposition;
- product positioning;
- incentives and competing offers;
- CTA wording and placement;
- funnel structure;
- cross-selling opportunities;
- account or channel requirements;
- lead-capture or advisory mechanism.

### 6.5 External response

Use public data to estimate communication reach and resonance:

- number of relevant media mentions;
- number of unique media sources;
- speed of attention growth;
- duration of attention;
- Google search-interest lift;
- sentiment and emotional framing;
- dominant positive and negative themes;
- public engagement where legally and technically available.

These indicators measure **external attention and resonance**, not sales, revenue, conversion, or campaign ROI.

## 7. Evidence-based feature framework

Academic research on technology adoption, consumer trust, information quality, perceived risk, ease of use, privacy, reputation, and customer support will be used to define the codebook.

| Academic construct | Observable campaign features |
|---|---|
| Trust | Guarantees, reputation, expertise, and institutional cues |
| Perceived security | Security, protection, and risk explanations |
| Information quality | Completeness, clarity, consistency, and accuracy |
| Ease of use | Plain language, simple navigation, and clear steps |
| Perceived usefulness | Concrete customer benefits and use cases |
| Transparency | Rate, tax, maturity, fees, eligibility, and conditions |
| Customer support | Adviser, chat, telephone, branch, and FAQ options |
| Social influence | Testimonials, popularity claims, and social proof |
| Cognitive effort | Word count, sentence length, jargon, and content density |
| Urgency | Deadlines, scarcity language, and time-sensitive CTAs |

Features can be stored as:

- binary values: present or absent;
- ordinal values: low, medium, or high;
- numeric values: word count, CTA count, or readability score;
- categorical values: dominant frame, audience, tone, or CTA type;
- textual values: headline, value proposition, and extracted evidence;
- visual values: imagery type, colour prominence, and CTA contrast.

Every AI-generated label should retain supporting text or page evidence so that the result remains auditable.

## 8. Data to collect

### 8.1 Owned communication

For each selected bank:

- campaign or product landing page;
- related press release;
- FAQ or help page;
- subscription instructions;
- accessible archived version from the campaign period;
- page title, headings, body text, CTA text, links, and publication date;
- language and capture timestamp;
- screenshots or selected visual characteristics.

### 8.2 Earned-media and attention data

- relevant news articles;
- article title, publication, URL, date, and language;
- campaign and bank entities mentioned;
- media sentiment and framing;
- Google Trends data for selected campaign and bank queries;
- official Belgian Debt Agency issuance results;
- public engagement signals where collection is permitted.

### 8.3 Candidate sources

- Belgian Debt Agency;
- public bank websites;
- bank sitemaps and permitted web archives;
- GDELT;
- Media Cloud;
- Google Trends;
- publicly accessible Belgian news sources.

All sources must be evaluated for access conditions, reliability, language coverage, and reproducibility.

## 9. Proposed data model

### Campaign-page table

One row represents one bank, campaign page, language, and capture date.

Suggested fields:

- `campaign_id`
- `bank`
- `bank_type`
- `page_url`
- `page_type`
- `language`
- `publication_date`
- `capture_date`
- `headline`
- `body_text`
- `target_audience`
- `communication_objective`
- `value_proposition`
- `dominant_frame`
- `tone`
- `trust_score`
- `transparency_score`
- `ease_of_use_score`
- `urgency_score`
- `customer_support_score`
- `cta_type`
- `cta_count`
- `word_count`
- `visual_features`
- `extraction_evidence`

### Media-mention table

One row represents one unique media item.

Suggested fields:

- `mention_id`
- `campaign_id`
- `source`
- `url`
- `publication_date`
- `language`
- `title`
- `clean_text`
- `banks_mentioned`
- `relevance_label`
- `sentiment`
- `sentiment_target`
- `dominant_topic`
- `media_type`
- `duplicate_group`
- `engagement_metrics`

## 10. Data-engineering pipeline

```text
Academic literature
        |
        v
Feature codebook
        |
        v
Source, robots.txt, sitemap, and access validation
        |
        v
Campaign pages + news + Trends + official statistics
        |
        v
Raw HTML, JSON, CSV, metadata, and screenshots
        |
        v
Text extraction, cleaning, language detection, and deduplication
        |
        v
Rule-based + LLM/NLP feature extraction
        |
        v
Human validation sample
        |
        v
Similarity, clustering, attention, and sentiment analysis
        |
        v
ING positioning, conclusions, and recommendations
```

### Storage layers

- `raw`: unmodified permitted source material and API responses;
- `processed`: cleaned text, normalized fields, and deduplicated records;
- `features`: structured campaign and media features;
- `outputs`: charts, comparison tables, and presentation material.

Important metadata should include the source URL, collection timestamp, language, response status, content hash, extraction method, and access decision.

## 11. Analysis methods

### Descriptive analysis

- feature frequencies by bank;
- communication scorecards;
- page-structure comparison;
- message-frame comparison;
- media volume over time;
- search-interest trends;
- sentiment and theme distributions.

### NLP and generative AI

- page and article relevance classification;
- communication-feature extraction into a fixed JSON schema;
- message-frame classification;
- multilingual sentiment and aspect analysis;
- topic and theme summarisation;
- named-entity recognition;
- duplicate detection.

### Embeddings and exploratory data science

- multilingual text embeddings;
- cosine similarity between campaign pages;
- campaign similarity matrix;
- hierarchical clustering;
- exploratory topic grouping;
- comparison of communication scores with attention indicators.

### Human validation

A manually annotated sample should be compared with AI-generated labels. Disagreements will be reviewed, and prompts or rules will be adjusted once before final extraction.

## 12. Measurement strategy

### External Communication Attention Index

An exploratory composite indicator may combine:

```text
Attention Index =
    normalized media volume
  + mention velocity
  + source diversity
  + search-interest lift
  + public engagement, when available
```

The components should first be reported individually. A combined score should only be created if its weighting is transparent and justified.

### Sentiment remains separate

| Attention | Sentiment | Interpretation |
|---|---|---|
| High | Positive | Broad positive resonance |
| High | Negative | Controversy or reputational risk |
| Low | Positive | Positive but limited reach |
| Low | Neutral | Limited observable external resonance |

### Possible baseline

Where data permits:

```text
Campaign attention lift =
attention during the campaign / normal attention for that bank
```

This helps reduce bias caused by differences in bank size and normal media visibility.

## 13. Prediction and machine-learning position

The MVP will not promise a reliable supervised prediction model. Four banks and a small number of campaign pages do not provide enough observations to predict sales or campaign success.

The appropriate data-science contribution is:

- automated and reusable feature extraction;
- campaign similarity analysis;
- exploratory clustering;
- descriptive associations between communication and attention;
- a framework that can later scale to a larger dataset.

The project will not claim to:

- predict sales by bank;
- prove that communication caused State Note purchases;
- determine campaign ROI;
- infer customer conversion without internal data;
- equate high media volume with positive success.

## 14. Legal and ethical approach

Only publicly available information will be collected.

Before collection:

1. inspect each site's `robots.txt`;
2. inspect relevant sitemaps;
3. review terms or access restrictions where applicable;
4. prefer official APIs or downloadable data;
5. avoid personal data;
6. avoid bypassing authentication, paywalls, rate limits, or technical restrictions;
7. apply conservative request rates;
8. document what was considered acceptable and why.

Article URLs and metadata can be retained even when full article content cannot legally or technically be stored.

## 15. Eight-day delivery plan

| Day | Work | Expected output |
|---|---|---|
| 1 | Confirm scope, banks, questions, success proxies, and legal protocol | Project charter and source list |
| 2 | Review academic evidence and create the communication codebook | Feature dictionary and annotation guide |
| 3 | Collect campaign pages and official issuance statistics | Raw campaign dataset |
| 4 | Collect news coverage and search-interest data | External-attention dataset |
| 5 | Clean, normalize, deduplicate, and run NLP/LLM extraction | Processed data and feature tables |
| 6 | Validate labels and calculate similarity, attention, and sentiment results | Analysis tables and charts |
| 7 | Interpret ING's position and formulate recommendations | Findings, limitations, and recommendations |
| 8 | Finalize the business presentation and technical documentation | Presentation and reproducible MVP |

## 16. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Bank-level sales are unavailable | Treat official sales as event context and use attention as the observable outcome |
| Historical campaign pages are unavailable | Use permitted archives or switch to current comparable product pages |
| Product economics dominate demand | Document interest rate, tax, timing, and market conditions as confounders |
| News duplicates inflate volume | Deduplicate using URLs, normalized headlines, hashes, and embedding similarity |
| Larger banks naturally receive more attention | Compare campaign-period attention with each bank's baseline |
| Dutch and French communication differ | Analyse languages separately before producing combined conclusions |
| LLM labels are inconsistent | Use a fixed schema, low-variance prompts, stored evidence, and human validation |
| Sentiment misses financial nuance | Use aspect labels such as trust, return, risk, transparency, and fairness |
| Sample size is too small for ML | Use descriptive analysis, embeddings, and clustering instead of predictive claims |
| Scraping is restricted | Prefer APIs and permitted pages; document exclusions and never bypass restrictions |
| Eight-day deadline causes excessive scope | Freeze the MVP after Day 1 and apply the Day 2 fallback decision |

## 17. Expected deliverables

### Business audience

- clear comparison of selected banks;
- explanation of ING's relative position;
- communication strengths and gaps;
- evidence-based improvement opportunities;
- concise explanation of what external attention does and does not mean.

### Data audience

- documented source and legal-access decisions;
- campaign feature dictionary;
- reproducible collection and processing pipeline;
- structured campaign and media datasets;
- validation approach;
- similarity, sentiment, and attention analysis;
- limitations and possible extensions.

## 18. Definition of success for the MVP

The MVP is successful if it delivers:

1. a coherent comparison based on a clearly justified limited scope;
2. an auditable feature framework grounded in academic evidence;
3. a reproducible pipeline using permitted external data;
4. a defensible view of ING's communication position;
5. practical recommendations that do not overstate causality;
6. a foundation that can later extend to social media, app banners, or larger automated studies.

## 19. Immediate decisions required

Before implementation begins, confirm:

1. the final four banks;
2. whether the September 2023 State Note is the definitive case;
3. the exact campaign observation window;
4. whether both Dutch and French pages are mandatory;
5. which public media sources are accessible within the project environment;
6. the required presentation format and assessment criteria.

