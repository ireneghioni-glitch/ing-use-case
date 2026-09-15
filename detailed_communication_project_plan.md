# ING Youth Acquisition Communication Comparator: Detailed Implementation Plan

Status: proposed eight-day MVP, subject to source-access checks.

Scope decision: 15 September 2026. Focus on acquisition communication for young adults aged 18-25, with general-adult offers as a comparison group. Minors are excluded from the MVP. This supersedes the earlier general-current-account and State Note scope proposals; final source selection remains subject to access and comparability checks.

Access-planning update: 15 September 2026, based on robots.txt excerpts and sitemap information supplied by the team. These are preliminary inputs, not independently verified live bank policies or legal authorization. Re-fetch the raw files from the exact collection origins before collection.

## 1. Purpose and business outcome

Compare how ING and selected traditional and challenger banks communicate everyday-banking acquisition offers to young adults aged 18-25, and how this communication differs from their general-adult offers, using only permitted public sources.

The business question is:

> How do banks adapt acquisition communication for young adults aged 18-25 compared with general-adult offers, where does ING sit relative to traditional and challenger banks, and which communication practices could ING improve or test?

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
| Irene's business and market research | Frame youth acquisition and identify comparable offers | Verified age eligibility, Belgian relevance, and candidate youth/adult page pairs |
| Alex's consumer psychology and marketing engineering | Explain why observable communication characteristics may matter | Academic rationale, hypotheses, feature definitions, scoring rules, and limitations |
| Maha's data engineering approach | Collect and structure permitted website and, if feasible, ad assets | Source registry, raw captures, cleaned data, and repeatable extraction |
| Gen-AI research and extraction contribution | Discover youth campaigns and apply the agreed codebook to approved evidence | Traceable candidate sources and evidence-backed structured labels, not invented scores |
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

### Collection and analysis architecture

```text
                  Youth acquisition scope: ages 18-25
                                |
                 Academic evidence + feature codebook
                                |
                 Source registry and access review
                      /                       \
                     v                         v
       WEBSITE TRACK: mandatory       AD TRACK: conditional
       Approved bank pages            Meta / Google ad assets
       Python HTTP or Playwright      Verified API/export or
       Youth + general-adult pairs    permitted collection method
                     |                         |
                     +------------+------------+
                                  v
                    Raw assets and provenance
                                  v
              Clean -> deduplicate -> label audience/channel
                                  v
              Rules + constrained LLM feature extraction
                                  v
                 Human validation and coverage audit
                                  v
          Within-bank youth/adult comparison + cross-bank comparison
                                  v
                  ING positioning and recommendations
```

An agent may help the team write and test a collector, but it does not grant collection permission or replace review. Python is an implementation choice, not an access method: do not assume Meta or Google permit classic website scraping. Verify supported APIs, exports, account requirements, field coverage, terms, and technical restrictions before selecting a method. No collector implementation or agent delegation is initiated by this plan update.

## 3. Scope decisions

### Agreed primary scope

Youth acquisition communication for everyday/current-account offers in Belgium, focused on young adults aged 18-25. Compare how banks present benefits, pricing, eligibility, trust, convenience, incentives, and account-opening steps to this audience versus their general-adult offers.

The audience and analytical direction are agreed; individual products, pages, campaigns, and channels remain provisional until verified. Do not assume current product names, prices, age restrictions, or account conditions from generated market summaries without checking dated original sources.

### Target sample, subject to permitted comparable coverage

- ING Belgium.
- KBC.
- BNP Paribas Fortis or Belfius, depending on accessibility.
- Revolut's Belgium-facing offer, if accessible and comparable.

Including a challenger is important for the coach's traditional-versus-challenger positioning question. If challenger content cannot be collected, explicitly narrow that research question rather than imply it was answered.

### Sample boundaries

- One product category: everyday/current-account acquisition.
- Primary analytical audience: ages 18-25 inclusive. Comparison group: general-adult acquisition offers, not a claim that all adult messaging targets people older than 25.
- Preserve each offer's actual age range and student/status requirements. Bank-defined youth ranges may differ from 18-25; record overlap and eligibility gaps rather than relabel them as identical.
- Aim for one youth-oriented landing page and one general-adult landing page per bank. Add relevant approved pricing/conditions and opening-guidance pages where available, but keep landing pages as the paired primary comparison unit.
- Approximately eight primary landing pages across four banks; supporting pages are evidence sources, not independent replications of the same offer.
- Adult student offers may be included with a student-status label. Exclude under-18 offers, parental controls, and minor-only campaign assets from the MVP.
- One primary language shared across the selected banks; add French/Dutch replication only if time permits.
- Same viewport, browser configuration, and collection period.
- Approximately 10-15 primary communication features.
- Website communication is mandatory. Test Meta/Google ad availability immediately as a conditional collection track; include ad analysis only if approved and comparable evidence is available without delaying the website MVP. News and search-interest analysis remain optional.

### Audience classification rules

Use `youth_18_25`, `adult_student`, `general_adult`, `mixed_age`, or `unknown` with evidence and actual advertised eligibility. These are analytical labels, not inferred platform targeting.

An asset can explicitly address young adults even if its product also serves a broader group. Record message audience separately from product eligibility. Do not infer age from a model's impression of photographs, slang, music, or platform alone. If the bank has no approved youth-specific page, record it as unavailable for the sampled collection, not proof that the bank has no youth strategy.

### Two comparisons, kept separate

1. **Within-bank:** compare youth-oriented and general-adult landing pages of matched role, language, channel, and capture period. This describes observable audience adaptation.
2. **Across banks:** compare youth-oriented communication between traditional banks and a challenger. General-adult pages provide context but must not substitute for missing youth assets.

“Full comparison” means consistent coverage of selected banks and agreed dimensions, not every youth campaign or every marketing channel. If some banks lack youth/adult pairs, produce a clearly labelled paired subset plus the available cross-bank youth comparison.

### Access-dependent scope adjustment

Keep the business question unchanged, but select page roles only after URL-level access checks. The supplied results do not establish blanket permission or blanket exclusion for any bank. BNP Paribas Fortis campaign, image, and document restrictions may reduce comparable coverage; Belfius has numerous document and journey exclusions. Select BNP or Belfius based on approved, matched HTML pages rather than bank preference. Do not switch to blocked PDFs, APIs, browser rendering, or archives to work around a restriction.

The KBC excerpt declares KBC Brussels sitemaps. Confirm whether the robots.txt file was retrieved from KBC or KBC Brussels and register the exact entity, market, and origin. Never silently label a KBC Brussels sample as a capture of KBC's main website. Check both comparability and the destination origin's robots.txt before using cross-origin sitemap entries.

### Scope-preserving fallback

If ad collection fails, proceed with the website-only youth/adult comparison. If a bank lacks approved matched pages, first consider another bank or a narrower adult-student subgroup while documenting lost coverage. Any material audience change requires team agreement. The State Note is now outside the active MVP; do not return to it merely because youth ad collection is difficult.

### Out of scope

- Internal customer or campaign data.
- Minors, under-18 offers, and child/parent acquisition journeys.
- Logged-in banking journeys and in-app personalization.
- Complete app usability testing.
- Full social-media monitoring.
- Supervised sales prediction or campaign ROI estimation.
- Comprehensive market-wide product ranking.
- Production deployment and elaborate orchestration infrastructure.

## 4. Research questions and hypotheses

### Research questions

1. What benefits and needs do banks explicitly emphasize for young adults?
2. How do tone, framing, trust cues, imagery, and incentives differ between youth and general-adult offers within each bank?
3. How prominently are price, age/student eligibility, promotion requirements, and conditions explained?
4. How clearly do youth assets communicate the next acquisition action?
5. Which youth communication patterns distinguish traditional banks from the sampled challenger, and where does ING sit?
6. Which evidence-backed adaptations could ING improve or test without claiming actual acquisition effects?

### Initial hypotheses to investigate, not assume

| Hypothesis | Observable evidence | Unsupported inference to avoid |
|---|---|---|
| Some offers require more effort to understand | Jargon density, sentence length, dispersed conditions | Customers actually find them difficult |
| Banks emphasize different trust mechanisms | Guarantees, institutional reputation, security, adviser references | One bank is objectively more trusted |
| Challenger communication emphasizes convenience | Headline themes, speed claims, digital CTAs | Challengers acquire customers more efficiently |
| Important conditions receive unequal prominence | Placement under a fixed capture protocol | Hidden conditions caused lower conversion |
| Youth pages emphasize affordability, independence, or convenience differently from adult pages | Evidence-backed benefit labels on matched youth/adult assets | These appeals reflect all young people's preferences |
| Acquisition incentives differ in prominence or explanation | Bonus wording, initial-viewport placement, qualifying requirements | A larger or more visible bonus creates more customers |
| Banks adapt tone and imagery for youth audiences | Defined tone/visual categories and within-bank paired evidence | Young-looking imagery proves actual ad targeting |

The analysis may reject these hypotheses. Neutral and contradictory findings must be retained.

## 5. Step 1: Confirm the business scope

### Actions

1. Re-read the coach's brief and agree on the communication deliverable.
2. Identify the stakeholder decision the comparison should support.
3. Operationalize the agreed 18-25 scope, general-adult comparison, primary language, and shared observation period.
4. Identify youth/general-adult landing-page pairs and supporting evidence for each bank; preserve actual eligibility boundaries.
5. Check that a traditional-versus-challenger comparison is actually possible.
6. Freeze the minimum scope before extensive collection.

### Output

`scope.md`: business question, selected banks, page roles, audience, language, inclusion/exclusion rules, and fallback.

### Acceptance gate

Every included page must support the chosen question. A product-specification comparison alone is not a communication analysis.

### Immediate instructions for collection tests already underway

1. Tag existing candidate assets by bank, Belgium relevance, channel, audience evidence, actual age eligibility, language, page role, and access status.
2. Prioritize one approved youth landing page and one approved general-adult landing page per bank before expanding page counts.
3. Keep uncertain, mixed-age, and under-18 discoveries outside the main analytical dataset until reviewed; retain candidate metadata where permitted.
4. Test Meta and Google separately for accessible advertiser identities, Belgian relevance, dates, creative fields, age-targeting metadata if actually provided, and collection permissions.
5. Report each test as available, unavailable, or needs review, with the method and evidence. A visible library page is not proof of API/scraper access.
6. Freeze the usable source set by the end of Day 2. Do not wait for perfect ad coverage to begin the website analysis.

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

### Meta and Google advertising access gate

Treat ad platforms as separate sources with their own access review; bank robots.txt does not cover ad-library collection. Prefer supported APIs or exports when available and approved. Do not assume API access to every commercial ad, exact targeting data, reach, clicks, spend, or conversion.

Record platform, advertiser identity, asset/library ID, retrieval method, dates, market evidence, creative text/media availability, and targeting/metric fields actually supplied. Unknown fields remain unknown. Do not use private Ads Manager access or circumvent authentication, rate limits, CAPTCHA, or platform controls. No performance inference should be derived from unavailable fields.

Website screenshots and ad creatives have different contexts and lengths: compare within channel first. Linking an ad to a landing page requires an explicit destination or campaign match; unlinked assets remain separate.

## 7. Step 3: Build the evidence-informed codebook

### Academic approach

Review a small set of primary studies on financial communication, consumer trust, information quality, perceived risk, framing, and cognitive effort. Banking-app research may provide candidate constructs, but findings about app adoption should not automatically be transferred to campaign effectiveness.

For each construct, record the study, population, setting, measured outcome, findings, and transfer limitations. Translate the concept into an observable feature rather than inventing a psychological outcome score.

Prioritize studies relevant to young adults, financial communication, financial literacy, acquisition friction, and benefit/price framing where available. Distinguish evidence from the target population from broader adult or non-Belgian findings. Do not assume that all 18-25-year-olds share financial knowledge, motivations, or preferences. Academic research informs feature selection; it does not establish the observed campaigns' customer impact.

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

### Youth-specific refinements

Keep the main feature set near 10-15 by integrating these refinements into existing features rather than endlessly adding scores:

- **Audience and eligibility:** store explicit audience wording, advertised age minimum/maximum, student requirement, and overlap with 18-25. Unknown eligibility is not universal eligibility.
- **Main benefit:** finalize categories such as affordability, convenience, independence/control, security/support, and lifestyle/rewards through the pilot; permit other/mixed labels with evidence.
- **Acquisition incentive:** record explicitly advertised bonus/perk, placement, and disclosed qualifying conditions. Separate actual product price from promotional messaging.
- **Tone:** use anchored categories with examples, such as formal/informational, conversational, and playful; allow mixed/unknown. Do not score “youth appeal” from intuition.
- **Imagery:** record observable scene and imagery type, not inferred age, ethnicity, personality, or financial status of depicted people.
- **Guidance:** distinguish public opening instructions from verified transaction steps. No logged-in or simulated account opening is required.

Apply the same definitions to youth and general-adult assets. Channel-specific visibility or text-length features need separately documented rules.

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

8. Match youth/adult page pairs within bank before pooling results. A general-adult page may also be available to 18-25 customers; do not describe the comparison as young versus old unless age targeting is explicit.
9. Keep actual bank eligibility ranges, student status, promotion dates, and market localization visible. A youth product for ages 18-24 is not identical to one for ages 18-25.
10. Do not pool ad and website counts or infer ad audiences from platform choice. Compare corresponding channels and roles separately.

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

### Asset metadata for the updated scope

Add `asset_id`, `bank_type`, `channel`, `asset_role`, `audience_label`, `audience_evidence`, `eligibility_age_min`, `eligibility_age_max`, `student_requirement`, `overlap_with_18_25`, `pair_id`, `campaign_id_if_verified`, `advertiser_id_if_available`, and `market_evidence`.

Use `pair_id` to connect matched youth/adult pages, not to assert causality. Use stable asset IDs to distinguish multiple ads, language variants, and supporting pages. Track shared content and duplicate creatives so repeated assets do not inflate sample size.

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

1. Audit coverage by bank, audience, page role, language, channel, exclusions, actual eligibility, and missing values.
2. Compare raw feature profiles across matched youth/adult landing-page pairs within each bank.
3. Compare youth profiles across banks, including traditional versus challenger patterns, while acknowledging the small sample.
4. Compare benefit themes, tone, trust cues, incentives, framing, conditions prominence, and next-step clarity.
5. Inspect differences between headline promises and detailed conditions without treating product advantages as communication effectiveness.
6. Identify ING's youth adaptations, distinctive practices, and similarities to sampled competitors.
7. Support each finding with evidence, capture dates, eligible denominators, and any unmatched-page limitations.

For numeric paired features, report `youth value - general-adult value` with the raw values. For binary features, show presence/absence transitions; for categorical features, show category changes with evidence. Do not combine these into an arbitrary audience-adaptation score. If ads are usable, provide a separate creative comparison rather than claiming acquisition performance.

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

The ad creative track is tested during initial source discovery and may support communication analysis in Step 8. It is not necessary to wait for this optional attention extension. Ad visibility or available reach metadata does not prove clicks, successful acquisition, or positive audience response.

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

State whether a recommendation concerns ING's youth/adult adaptation, a cross-bank youth difference, or a specific channel. Avoid framing an academic generalization as a proven preference of Belgian young adults.

### Example, not a finding

> Observation: qualifying conditions are separated from a promoted price on a sampled page. Comparison: matched competitor pages display the requirement beside the price. Rationale: proximity may reduce interpretation effort. Recommendation: test an adjacent price-and-condition summary. Future test: measure comprehension or conversion in an authorized experiment. Limitation: public-page analysis does not establish a conversion effect.

Avoid language such as “ING is more trusted,” “this campaign failed,” or “this feature increases sales” without the necessary outcome evidence.

## 15. Eight-day schedule and decision gates

| Day | Activities | Output/gate |
|---|---|---|
| 1 | Confirm ages 18-25 scope, youth/adult pairs, academic research questions; website and Meta/Google access tests | Candidate paired sample and separate channel feasibility reports |
| 2 | Academic rationale, codebook, eligibility mapping, pilot comparability checks | Freeze usable banks/channels and feature definitions; website-only fallback if ads fail |
| 3 | Collect paired website assets and approved ad creatives if feasible; screenshots, metadata, exclusions | Traceable audience-labelled campaign assets |
| 4 | Cleaning, deterministic extraction, pilot labels, codebook refinement | Processed data and frozen annotation rules |
| 5 | Constrained LLM extraction and human review | Validated feature records |
| 6 | Within-bank youth/adult and cross-bank youth comparisons, coverage audit, optional similarity analysis | Evidence-backed audience-adaptation and ING-positioning findings |
| 7 | Youth communication recommendations and stakeholder narrative; optional attention only if time remains | Business conclusions, test ideas, and limitations |
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
| Youth eligibility differs across banks | Preserve actual age/student rules; show overlap and gaps rather than invent uniform eligibility |
| General-adult pages are mistaken for older-only targeting | Label broader audience correctly and separate message audience from eligibility |
| Youth is inferred from pictures or slang | Require explicit audience evidence; retain mixed/unknown labels |
| Missing youth/adult pairs prevent fair adaptation claims | Analyse the paired subset and report cross-bank youth coverage separately |
| Meta/Google access or fields are unavailable | Day 2 access gate; website-only MVP without blocked scraping or invented metrics |
| Multiple supporting pages or duplicate ads inflate sample size | Use primary landing-page pairs, stable IDs, and duplicate/content tracking |
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
- Within-bank youth/general-adult adaptation table and cross-bank youth comparison.
- Traditional/challenger patterns with explicit sample and coverage limits.
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
- [ ] The active scope is youth acquisition for ages 18-25; minors are excluded.
- [ ] Actual advertised age eligibility and student requirements are documented separately from message audience.
- [ ] Youth/adult pair availability and traditional/challenger coverage are disclosed.
- [ ] Meta/Google methods and available fields passed source-specific access review, or the ad track was omitted.
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

> We combine Irene's youth-acquisition scope, Alex's evidence-informed behavioural framework, and Maha's collection architecture to compare permitted public banking communication for ages 18-25. Matched general-adult pages reveal observable within-bank adaptations, while cross-bank youth assets position ING relative to traditional and challenger banks. Strict feature definitions, provenance, and human validation support practical communication recommendations without claiming internal acquisition performance or causal customer effects.
