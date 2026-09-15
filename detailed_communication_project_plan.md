# ING Banking Communication Comparator: Detailed Implementation Plan

Status: proposed eight-day MVP, subject to source-access checks.

Access-planning update: 15 September 2026, based on robots.txt excerpts and sitemap information supplied by the team. These are preliminary inputs, not independently verified live bank policies or legal authorization. Re-fetch the raw files from the exact collection origins before collection.

## 1. Purpose and business outcome

Compare how ING communicates a comparable financial offer against selected traditional and challenger banks using only permitted public sources.

The business question is:

> How does ING present its offer, benefits, conditions, and next steps compared with competitors, and which observable communication practices could it improve or test?

The deliverable is a grounded communication comparison, not a sales-performance model. Internal ING data is unavailable. We cannot measure conversion, customer acquisition cost, revenue, ROI, or the causal effect of a campaign on customer behaviour.

### What the project must produce

1. A justified scope and documented source-access decisions.
2. A strict, evidence-informed communication feature dictionary.
3. A small, comparable dataset of public pages.
4. A reproducible collection and feature-extraction pipeline.
5. Validation of manual and AI-assisted annotations.
6. ING positioning, similarities, differences, and three evidence-backed recommendations.

## 2. How the three approaches fit together

| Contribution | Function | Required output |
|---|---|---|
| Irene's business and market research | Select a relevant product, audience, and competitors | Scope proposal supported by verified sources |
| Consumer psychology and marketing engineering | Explain why observable communication characteristics may matter | Hypotheses, feature definitions, scoring rules, and limitations |
| Maha's data engineering approach | Collect and structure permitted campaign assets | Source registry, raw captures, cleaned data, and repeatable extraction |
| Shared analytical work | Validate and compare the evidence | Comparison, interpretation, and recommendations |

These are suggested contributions, not assumptions about agreed team assignments. Collection and feature design must be coordinated before coding.

```text
Business question and scope
          |
          v
Academic rationale and testable communication hypotheses
          |
          v
Feature codebook and permitted-source registry
          |
          v
Collect -> Clean -> Structure -> Extract evidence
          |
          v
Human validation and agreement checks
          |
          v
Compare banks and identify communication patterns
          |
          v
ING positioning and testable recommendations
```

## 3. Scope decisions

### Primary proposed scope

Current-account communication on public Belgian bank websites. Focus on how banks explain benefits, prices, conditions, trust, convenience, and account-opening steps.

This remains a proposal until comparable, permitted pages have been identified. Do not assume current product names, prices, or account restrictions from generated market summaries without checking dated original sources.

### Proposed sample

- ING Belgium.
- KBC.
- BNP Paribas Fortis or Belfius, depending on accessibility.
- Revolut's Belgium-facing offer, if accessible and comparable.

Including a challenger is important for the coach's traditional-versus-challenger positioning question. If challenger content cannot be collected, explicitly narrow that research question rather than imply it was answered.

### Sample boundaries

- One product category and one clearly defined audience.
- Prefer adult everyday banking; do not mix minors, students, and general adult offers without stratification.
- Two or three matched page roles per bank: offer landing page, pricing/conditions page, and public opening guidance.
- One primary language shared across the selected banks; add French/Dutch replication only if time permits.
- Same viewport, browser configuration, and collection period.
- Approximately 10-15 primary communication features.
- Website communication is mandatory; media and ad-library analysis are optional.

### Access-dependent scope adjustment

Keep the business question unchanged, but select page roles only after URL-level access checks. The supplied results do not establish blanket permission or blanket exclusion for any bank. BNP Paribas Fortis campaign, image, and document restrictions may reduce comparable coverage; Belfius has numerous document and journey exclusions. Select BNP or Belfius based on approved, matched HTML pages rather than bank preference. Do not switch to blocked PDFs, APIs, browser rendering, or archives to work around a restriction.

The KBC excerpt declares KBC Brussels sitemaps. Confirm whether the robots.txt file was retrieved from KBC or KBC Brussels and register the exact entity, market, and origin. Never silently label a KBC Brussels sample as a capture of KBC's main website. Check both comparability and the destination origin's robots.txt before using cross-origin sitemap entries.

### Alternative case

The September 2023 Belgian State Note remains an alternative only if enough campaign-period pages are already recoverable from permitted sources. Aggregate issuance results cannot establish individual bank campaign performance. Historical collection should not become a dependency that consumes the MVP schedule.

### Out of scope

- Internal customer or campaign data.
- Logged-in banking journeys and in-app personalization.
- Complete app usability testing.
- Full social-media monitoring.
- Supervised sales prediction or campaign ROI estimation.
- Comprehensive market-wide product ranking.
- Production deployment and elaborate orchestration infrastructure.

## 4. Research questions and hypotheses

### Research questions

1. What benefits and customer needs does each bank emphasize?
2. How do tone, persuasive framing, and trust cues differ?
3. How prominently are price, eligibility, and conditions explained?
4. How clearly does the page communicate the next customer action?
5. Which patterns distinguish ING from its sampled competitors?
6. Which differences justify practical recommendations or future tests?

### Initial hypotheses to investigate, not assume

| Hypothesis | Observable evidence | Unsupported inference to avoid |
|---|---|---|
| Some offers require more effort to understand | Jargon density, sentence length, dispersed conditions | Customers actually find them difficult |
| Banks emphasize different trust mechanisms | Guarantees, institutional reputation, security, adviser references | One bank is objectively more trusted |
| Challenger communication emphasizes convenience | Headline themes, speed claims, digital CTAs | Challengers acquire customers more efficiently |
| Important conditions receive unequal prominence | Placement under a fixed capture protocol | Hidden conditions caused lower conversion |

The analysis may reject these hypotheses. Neutral and contradictory findings must be retained.

## 5. Step 1: Confirm the business scope

### Actions

1. Re-read the coach's brief and agree on the communication deliverable.
2. Identify the stakeholder decision the comparison should support.
3. Select one product category, audience, language, and observation period.
4. Identify candidate matched page roles for each bank.
5. Check that a traditional-versus-challenger comparison is actually possible.
6. Freeze the minimum scope before extensive collection.

### Output

`scope.md`: business question, selected banks, page roles, audience, language, inclusion/exclusion rules, and fallback.

### Acceptance gate

Every included page must support the chosen question. A product-specification comparison alone is not a communication analysis.

## 6. Step 2: Verify evidence and permitted sources

### Actions

1. Review original bank pages rather than treating NotebookLM summaries as verified facts.
2. Record each candidate URL in a source registry.
3. Inspect robots.txt, relevant sitemaps, terms, and technical access restrictions.
4. Prefer official downloads and supported APIs where useful.
5. Exclude logged-in pages, personal data, paywalled material requiring bypass, and restricted endpoints.
6. Use conservative request rates and stop on blocking or repeated errors.
7. Document uncertainties and escalate unresolved access questions before automated collection.

Robots.txt is a technical access signal, not a complete legal permission statement. Public visibility alone does not establish permission for unrestricted scraping or redistribution.

### Source-registry fields

`source_id`, `bank`, `url`, `page_role`, `language`, `market`, `checked_at`, `robots_decision`, `terms_notes`, `collection_method`, `access_decision`, `exclusion_reason`.

Use access statuses: `approved_for_project`, `excluded`, or `needs_review`.

### Team-supplied robots.txt findings

The following summary supports planning only. It is not a replacement for the full raw robots.txt rules, which must be retained and evaluated per URL.

| Bank | Supplied restrictions and discovery information | Project consequence |
|---|---|---|
| ING | `Disallow: /video`; sitemap `https://www.ing.be/sitemap-cms.xml` | Exclude matching video URLs. Discover candidate HTML offer pages through the sitemap, then check them individually. Video-dependent features remain outside the core MVP. |
| Belfius | Numerous exclusions including `/media`, `/docs/`, `/pdf/`, `/NoCMS/Doccenter`, private/logged-in journeys, complaint steps, and specific campaign/simulator paths; sitemap index `https://www.belfius.be/sitemap.xml` | Prioritize relevant retail HTML pages discovered through retail sub-sitemaps. Check conditions and support destinations separately. A retail or campaign URL is not automatically allowed. |
| BNP Paribas Fortis | `/site/`, `/images/`, `/local/`, `/promo/`, `/de/*`, `/*.pdf`, and other supplied prefixes are disallowed; `/images/favicons/` is an explicit exception; sitemap `https://www.bnpparibasfortis.be/sitemap.xml` | Exclude matching promotional, document, and image requests unless an applicable more-specific allowance resolves the match. Use approved HTML alternatives if genuinely available. Do not infer that every campaign page is blocked or that all visual evidence is available. |
| KBC / KBC Brussels, origin to confirm | `Disallow: /*/$`, `/site/*`, `/PBL/CC028/*`, `*/aemform.iframe.html`; `Allow: /campaigns/*/$`; declared sitemaps are on `www.kbcbrussels.be` | Verify the source origin and raw rules. Test trailing-slash URL matches and the more-specific campaign exception. Exclude restricted forms. Correct the apparently truncated English sitemap URL only after checking the raw source. |
| Revolut | Restricted APIs, help-centre suffixes, JSON/manifests, embedded and query patterns, specified transfer/converter paths; amount-query exceptions; sitemap `https://www.revolut.com/sitemap-index.xml` | Prefer approved Belgium-facing offer HTML without unnecessary query parameters. Evaluate the exact query and explicit allowances; do not infer access to help-centre/API endpoints or all transfer pages. |

### Raw-source verification requirements

1. Record the exact robots.txt URL, scheme, host, port if applicable, retrieval timestamp, HTTP status, crawler identity, raw content, and content hash.
2. Obtain plain server responses rather than copying browser presentation text into the parser. The supplied Belfius XML includes a `chrome-extension://` script: this is browser-injected material, not a bank sitemap entry.
3. Remove Markdown link formatting only in derived discovery lists; preserve the original input. Verify apparent truncation, non-breaking spaces, and malformed path entries against the raw file rather than silently repairing access rules.
4. Store the full rules, not only the summary table. Preserve case-sensitive path distinctions and all applicable user-agent groups and exceptions.
5. Treat unresolved or inconsistent rules as `needs_review` and do not collect the affected URLs until resolved.

### URL evaluation and collector requirements

Implement matching consistent with [RFC 9309: Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309.html), and explicitly test support for the wildcard/query patterns in the supplied files. Do not assume a parser supports all these patterns without tests.

- Evaluate rules for the declared crawler identity and exact destination origin, not a borrowed bank or subdomain policy.
- Support most-specific matching, equivalent allow/disallow precedence, `*` wildcards, and `$` end anchors. Path prefixes must not be treated as exact filenames.
- A sitemap discovers URLs; it never overrides a disallow rule or proves legal permission.
- Check candidate pages, linked documents, image/media assets, iframe targets, and redirect destinations before fetching them. Disable automatic redirect-following where it could fetch an unchecked destination.
- When using Playwright, intercept network requests before dispatch and block excluded or unresolved resources. Do not load a disallowed asset first and classify it afterwards. Record effects on rendering.
- Fetch only the resources needed for approved page evidence; exclude trackers, private forms, and unrelated requests from the collection design.
- Do not strip queries, change casing, switch hosts, or select rendering tools merely to evade restrictions. Independently discovered canonical alternatives require their own access review.
- Refresh robots.txt before each collection run; document changes and invalidate affected approvals. Under this project's conservative policy, retrieval errors, unresolved parsing, blocking, or ambiguous access mean pause and review, not assumed permission.

### Minimum access-check tests

Create tests from the verified raw rules for: ING `/video` prefix matches; BNP `/promo/`, PDF patterns and favicon exceptions; Belfius restricted document paths; KBC trailing-slash exclusions and campaign exceptions; Revolut query restrictions and amount exceptions; cross-origin redirects; and blocked browser subresources. Include allowed, blocked, and unresolved cases. Passing a test establishes parser behaviour, not legal permission.

### Additional registry fields

Add `origin`, `robots_url`, `robots_retrieved_at`, `robots_status`, `robots_hash`, `crawler_identity`, `matched_rule`, `sitemap_source`, `resource_type`, `redirect_chain`, `rendering_limitations`, and `reviewer`. Record linked resources as separate access decisions when required for a feature.

### Acceptance gate

There must be enough approved, comparable pages to complete a small analysis. If not, change scope before building the full pipeline.

## 7. Step 3: Build the evidence-informed codebook

### Academic approach

Review a small set of primary studies on financial communication, consumer trust, information quality, perceived risk, framing, and cognitive effort. Banking-app research may provide candidate constructs, but findings about app adoption should not automatically be transferred to campaign effectiveness.

For each construct, record the study, population, setting, measured outcome, findings, and transfer limitations. Translate the concept into an observable feature rather than inventing a psychological outcome score.

### Required definition for every feature

- Feature name and business relevance.
- Academic rationale, if applicable.
- Unit of observation.
- Exact measurement or classification rule.
- Allowed values and category boundaries.
- Required supporting evidence.
- Treatment of absence, missing data, and non-applicability.
- Examples and difficult cases.
- Extraction method and validation procedure.
- Codebook version.

### Initial operational features

| Feature | Measurement rule | Type |
|---|---|---|
| Main benefit | Code the primary headline/hero benefit into an agreed category; retain headline evidence | Categorical |
| Audience explicit | 1 when the intended customer group is explicitly identified in text; otherwise 0 after a successful complete capture | Binary |
| Price in initial viewport | 1 when a qualifying account price is visible in the fixed initial viewport; retain screenshot evidence | Binary |
| Conditional price disclosure | For a promoted conditional price, record whether the requirement appears adjacent, elsewhere, or is not found | Categorical |
| Conditions link | 1 when a clearly labelled relevant conditions link exists; record link and destination | Binary |
| Eligibility stated | 1 when relevant eligibility requirements are explicitly described; otherwise 0 after complete capture | Binary |
| Explicit reassurance cues | Count explicit security, guarantee, reputation, or support statements by predefined cue type | Counts/categories |
| Jargon density | Occurrences from a frozen, language-specific glossary divided by word count, multiplied by 100 | Numeric |
| Sentence length | Mean words per sentence in the defined main-content text | Numeric |
| CTA type | Classify visible CTAs into open account, contact, learn more, or other; retain wording | Categorical |
| Primary CTA visibility | 1 when the principal action CTA is visible in the fixed initial viewport | Binary |
| Opening guidance | Record whether public step-by-step instructions exist and the number of stated steps, not inferred private steps | Binary/count |
| Support options | Record explicitly offered contact channels; do not equate channel count with service quality | Categories |
| Persuasive framing | Classify evidence-bearing passages as gain, loss, mixed, or neither using written examples | Categorical |
| Imagery type | Classify the hero visual as people, product/interface, illustration, abstract, mixed, or none | Categorical |

Finalize exact boundaries through a pilot. Do not add features merely because an LLM can generate them.

### Missing-value rules

- `0`: feature genuinely absent after a successful inspection.
- `1`: feature present under the rule.
- `unknown`: extraction or evidence is insufficient.
- `not_applicable`: feature does not apply to this offer.

Unknown and not-applicable values must not silently become zeros. For numerical tables, retain a separate missing-status field.

### Restricted evidence is not a negative feature

Add missing reasons such as `robots_disallowed`, `access_unresolved`, `linked_document_unavailable`, `asset_blocked`, and `partial_render`.

- A conditions link visible on an approved page may be recorded as present even if its destination cannot be collected. Record the link without fetching it; leave the destination's content assessment unknown.
- Do not classify eligibility, conditions completeness, or risk information as absent when the needed evidence lies in a restricted or unavailable destination.
- If blocked assets alter the hero section, record imagery or placement as unknown where the feature cannot be judged reliably. A policy-filtered screenshot must not be represented as the unrestricted customer experience.
- Distinguish an explicit statement that help exists from inspection of its inaccessible help-centre destination.
- Do not use manual browsing, an LLM's memory, cached copies, or an archive as a substitute for excluded collection evidence under this project protocol.

### Acceptance gate

Two people should be able to apply the definitions to the same page and explain their labels using observable evidence.

## 8. Step 4: Define comparability and normalization

Normalization is not a substitute for feature validity. Scaling arbitrary model scores does not make them meaningful.

### Collection controls

1. Compare matched page roles separately.
2. Use the same language or analyse language groups separately.
3. Fix viewport dimensions, zoom, device class, and browser settings.
4. Record cookie-banner handling and resulting viewport state.
5. Capture within a short shared period and retain timestamps.
6. Use the same main-content inclusion rules; exclude navigation and footer consistently.
7. Record product differences so communication differences are not confused with different offers.

### Numerical rules

- Report jargon per 100 words, not only raw counts.
- Report counts alongside the denominator and inspected content length.
- Use binary and categorical features directly when appropriate.
- Keep missingness visible in all summaries.
- If scaling is used for visualization, state the formula and retain raw values.
- Avoid a combined campaign-quality or challenger score without justified weights and sensitivity analysis.

With a small sample, show feature profiles rather than implying statistically representative bank rankings.

### Fair comparison under unequal access

Produce a bank-by-page-role and bank-by-feature coverage table. Compare only adequately observed matched evidence, and report the eligible denominator for each summary. Do not impute unknowns as zeros, penalize banks for robots restrictions, or infer inferior transparency/service from unavailable pages. If a core feature is unavailable for a bank, narrow the comparison or change the matched sample rather than construct an apparently complete ranking. Explain selection bias: accessible pages may not represent every campaign or the complete customer journey.

## 9. Step 5: Collect and preserve campaign assets

### Collection process

1. Read the approved URL list.
2. Capture permitted HTML with a simple HTTP client where sufficient.
3. Use browser rendering only when necessary and permitted.
4. Record response status, redirect destination, timestamp, and content hash.
5. Save rendered screenshots for visibility and imagery features.
6. Separate main content from navigation, banners, and footer.
7. Preserve raw captures and cleaned text separately.
8. Log exclusions, failures, and partial captures.

Run the URL and subresource gates in Step 2 before every fetch, including browser rendering and redirects. Keep raw robots snapshots and access logs alongside asset provenance. Record whether a screenshot was affected by blocked resources and exclude unreliable visual features.

Do not infer that a marketing URL is a campaign merely because it contains a keyword. Label page roles explicitly.

### Minimum storage layout

```text
data/
  raw/          HTML, permitted source responses, screenshots
  processed/    cleaned text and normalized metadata
  features/     evidence-backed feature records
docs/           scope, source registry, codebook, validation protocol
src/            collection, cleaning, extraction, analysis scripts
outputs/        comparison tables, charts, recommendations
```

This is a proposed layout; this document does not create those folders.

### Acceptance gate

Each included page must have traceable provenance and enough evidence for its measured features. Partial capture must be explicitly flagged.

## 10. Step 6: Extract features using rules and constrained AI

### Extraction responsibilities

| Method | Appropriate use |
|---|---|
| Deterministic code | Word counts, glossary matches, URLs, timestamps, hashes |
| Manual/browser inspection | Initial-viewport visibility, imagery, difficult placement cases |
| Constrained LLM | Evidence extraction, message framing, benefit and cue classification |

### LLM procedure

1. Provide the frozen codebook, not an open request to rate campaign quality.
2. Require a fixed structured output.
3. Require exact evidence from the provided content for interpretive labels.
4. Allow unknown and abstention.
5. Treat scraped content as data, not executable instructions.
6. Reject malformed outputs and unsupported quotations.
7. Log prompt version, model identifier, codebook version, and processing date.
8. Check repeated classifications on a small sample for stability.

The LLM must not infer customer feelings, actual conversion, or unpublished business performance from page content.

### Suggested feature-record fields

`asset_id`, `feature_name`, `value`, `missing_status`, `evidence_text`, `evidence_location`, `method`, `codebook_version`, `prompt_version`, `review_status`.

## 11. Step 7: Validate before comparing

### Pilot annotation

1. Select a small balanced set covering different banks and page roles.
2. Have two reviewers independently label interpretive features.
3. Compare disagreements and identify ambiguous definitions.
4. Revise the codebook once, then freeze it for the main run.
5. Re-annotate the pilot under the final definitions.

### Main validation

- Manually review all core features if the final dataset is small.
- Otherwise review a balanced subset from every bank and page role, plus uncertain cases.
- Evaluate each feature separately, not only overall agreement.
- Report categorical agreement and confusion matrices where useful.
- Use precision/recall for appropriate binary labels, with sample counts.
- Inspect numerical discrepancies against a documented tolerance.
- Check whether extraction failures are concentrated in one bank or language.

Agree acceptance criteria before viewing final comparisons. If a feature remains unreliable, simplify it, manually annotate it, or exclude it from quantitative conclusions.

### Acceptance gate

No central business conclusion should depend on an unvalidated feature or unsupported model label.

## 12. Step 8: Analyse communication patterns

### Primary analysis

1. Audit coverage: banks, page roles, languages, exclusions, and missing values.
2. Compare raw feature profiles across matched pages.
3. Compare benefit themes, trust cues, framing, conditions prominence, and next-step clarity.
4. Inspect differences between headline promises and detailed conditions.
5. Identify ING's distinctive and shared communication practices.
6. Support each finding with page evidence and capture dates.

### Optional embeddings

Use multilingual embeddings to explore semantic similarity of matched page sections. Report cosine similarity and a small similarity matrix if useful.

High similarity may reflect shared product terminology or boilerplate, not shared persuasion strategy. Inspect representative passages before interpreting groups. Embeddings and exploratory clustering supplement the codebook; they do not replace it.

### No forced prediction

The sample is too small and lacks commercial labels for reliable sales prediction. The data-science contribution is reusable measurement, validated extraction, and comparison. Predictive modelling is a future extension, not an MVP requirement.

## 13. Step 9: Optional external-attention extension

Only begin after the core communication dataset and comparison are complete.

### Possible sources and indicators

- Permitted news sources or accessible news APIs: relevant articles and unique publications.
- Google Trends: relative search interest, not absolute demand.
- Ad libraries: creative assets and explicitly available metadata, subject to verified access.

### Rules

1. Define campaign-specific bank/product queries and a shared time window.
2. Distinguish campaign coverage from unrelated bank news.
3. Deduplicate syndicated and near-identical stories.
4. Separate owned press releases, sponsored content, and independent coverage where identifiable.
5. Report source coverage and retrieval limitations.
6. Keep volume and sentiment separate.
7. Never treat generic CPM/CTR benchmarks as these campaigns' measured performance.

If mentions are sparse or cannot be attributed to the campaign, omit the extension. Do not manufacture an attention index from incomparable sources.

## 14. Step 10: Convert findings into business recommendations

Every recommendation should follow this template:

1. **Observation:** what is visible in the sampled ING pages?
2. **Comparison:** how do matched competitor pages differ?
3. **Rationale:** why might the difference matter according to relevant evidence?
4. **Action:** what communication change could ING consider?
5. **Future test:** what behavioural evidence would confirm its value?
6. **Limitation:** what has not been established?

### Example, not a finding

> Observation: qualifying conditions are separated from a promoted price on a sampled page. Comparison: matched competitor pages display the requirement beside the price. Rationale: proximity may reduce interpretation effort. Recommendation: test an adjacent price-and-condition summary. Future test: measure comprehension or conversion in an authorized experiment. Limitation: public-page analysis does not establish a conversion effect.

Avoid language such as “ING is more trusted,” “this campaign failed,” or “this feature increases sales” without the necessary outcome evidence.

## 15. Eight-day schedule and decision gates

| Day | Activities | Output/gate |
|---|---|---|
| 1 | Business question, scope, candidate pages, access checks | Approved small scope and fallback |
| 2 | Academic rationale, codebook, pilot comparability checks | Freeze features; resolve source feasibility |
| 3 | Raw collection, screenshots, metadata, exclusions | Traceable campaign assets |
| 4 | Cleaning, deterministic extraction, pilot labels, codebook refinement | Processed data and frozen annotation rules |
| 5 | Constrained LLM extraction and human review | Validated feature records |
| 6 | Comparison, coverage audit, optional similarity analysis | Evidence-backed findings |
| 7 | Recommendations and stakeholder narrative; optional attention only if time remains | Business conclusions and limitations |
| 8 | Final quality checks, documentation, presentation | Complete reproducible MVP |

If fewer than eight working days are available, cut optional features, second-language replication, embeddings, and media analysis before cutting validation or provenance.

## 16. Risks and responses

| Risk | Response |
|---|---|
| Generated market statements are inaccurate | Verify original dated sources and record evidence |
| No comparable permitted pages | Change bank/sample or product before collection |
| Unequal bank restrictions distort scores | Report coverage and eligible denominators; never score restricted evidence as absence |
| KBC/KBC Brussels origin is misidentified | Verify source and destination origins; label the sampled entity and market explicitly |
| Browser loads blocked assets or redirect destinations | Pre-request filtering, checked redirects, and partial-render flags |
| Copied robots/sitemap text contains formatting artifacts | Verify raw server files and preserve snapshots; review ambiguous rules |
| Product differences confound communication | Record offer characteristics and compare matched page roles |
| Subjective labels resemble arbitrary scores | Operational codebook, evidence, pilot agreement, and validation |
| Missing values become zeros | Explicit missing-status fields and coverage reporting |
| LLM outputs vary | Frozen prompt/schema, stability checks, manual review |
| Screenshot visibility varies | Fixed viewport and documented banner handling |
| Reviews measure service rather than campaigns | Exclude from the core campaign comparison |
| No internal outcomes | Restrict claims to observable communication |
| Overengineering consumes the deadline | Use simple scripts and CSV/JSON or an existing database |
| Recommendations favour ING in advance | Retain contradictory findings and apply identical rules |

## 17. Final deliverables and quality checklist

### Business package

- One-page executive summary.
- Small bank comparison table or feature-profile chart.
- ING positioning with representative evidence.
- Three prioritized communication recommendations.
- Explicit distinction between observation, interpretation, and future testing.

### Technical package

- Scope and source registry.
- Versioned feature dictionary and academic evidence notes.
- Raw-source provenance and processed datasets.
- Collection/extraction scripts and rerun instructions.
- Validation results and exclusions.
- Limitations and extension options.

### Completion checklist

- [ ] Scope answers the coach's communication question.
- [ ] All included sources have a documented access decision.
- [ ] Bank-specific rules were verified from raw robots.txt on the exact collection origins.
- [ ] Parser tests cover wildcards, anchors, exceptions, queries, redirects, and browser resources.
- [ ] KBC versus KBC Brussels identity and source origin are resolved.
- [ ] Restricted evidence has explicit missing reasons and is not scored as zero.
- [ ] Coverage differences and policy-filtered rendering limitations are disclosed.
- [ ] Page roles, audience, language, and capture settings are comparable.
- [ ] Every feature has an explicit rule and missing-value policy.
- [ ] Core labels have been checked against human evidence.
- [ ] Normalization formulas and denominators are documented.
- [ ] No unexplained quality or challenger score is presented as objective truth.
- [ ] Findings refer to the sampled pages, not all customers or all campaigns.
- [ ] Recommendations follow from observations and include testable next steps.
- [ ] No sales, ROI, or causal-effect claim exceeds the available evidence.
- [ ] The pipeline can be rerun and its outputs traced to sources.

## 18. Final project statement

> We combine business scoping, behavioural theory, and data engineering to build a reproducible comparison of permitted public banking communication. Strict feature definitions and human validation turn public webpages into auditable evidence. The resulting analysis positions ING relative to selected competitors and identifies communication improvements worth testing, without claiming access to internal performance or customer behaviour.
