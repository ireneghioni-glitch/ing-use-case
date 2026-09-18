Integrated feature set for the ING Youth Acquisition Communication Comparator.

| Feature | Method | Possible values / output | What it measures |
|---------|--------|--------------------------|------------------|
| value_proposition_clarity | LLM (text) | clear-specific / clear-vague / unclear | Whether the core benefit is stated concretely (with a number, rate, or timeframe) vs vaguely |
| trust_signals | LLM (text + vision) | list: security_badge / deposit_guarantee / testimonials / customer_numbers / none | Presence of credibility/reassurance cues specific to financial products |
| tone | LLM (text + vision) | formal / persuasive / simple / playful | Overall register of language |
| sentiment | LLM (text + vision) | positive / neutral / reassuring / urgent | Emotional framing of the message |
| verbosity | LLM (text + vision) | low / medium / high | Density of text on the page |
| cta_clarity | LLM (text) | specific-action / vague-action / none | Whether the CTA states one clear next step vs a generic "learn more" |
| cta_text | LLM (text + vision) | free text | Main call-to-action button label |
| distinctiveness | LLM (vision + text) | high / medium / low | Whether the page uses ownable visual/verbal assets vs generic category conventions |
| visual_hierarchy_focus | LLM (vision) | number/rate / face / product-shot / headline-text | What the eye is drawn to first |
| text_image_layout | LLM (vision) | side-by-side / stacked / full-width-hero / text-only | Text/image arrangement |
| color_touch_location | LLM (vision) | text / image / icon / none / mixed | Where the brand color shows up |
| animation_level | LLM (vision) | static / partial / fully-animated | Degree of visual animation |
| visual_type | LLM (vision) | real-people / illustration / product-shot / abstract / none | Dominant visual type |
| mobile_first_cues | LLM (vision) | strong / moderate / weak | Vertical flow, large touch targets — proxy for digital-native design maturity |
| topics | LLM (text) | list of keywords (max 4) | Themes covered |
| word_count | Deterministic (Python) | integer | Exact page text length |
| cta_count | Deterministic (HTML parsing) | integer | Number of call-to-action elements |
| dominant_color | Deterministic (k-means on screenshot) | RGB/hex value | Most prevalent color on the page |
| main_benefit | LLM (text) | affordability / convenience / independence-control / security-support / lifestyle-rewards / other / mixed / unknown | The core benefit category of the message |
| audience_explicit | LLM (text) | yes / no | Whether the intended audience is explicitly named (young people, students, under 25) |
| price_in_initial_viewport | Manual / Vision | yes / no | Whether the price (or monthly fee) is visible without scrolling |
| conditional_price_disclosure | LLM (text) | adjacent / elsewhere / not found | Whether the promotional price requires conditions and where they are stated |
| conditions_link | Deterministic (HTML parsing) | yes / no | Presence of a clear link to terms and conditions |
| eligibility_stated | LLM (text) | yes / no | Whether age or student status requirements are stated |
| opening_guidance | LLM (text) | yes / no + count | Whether step-by-step instructions for opening the account are provided |
| support_options | LLM (text) | list of channels (chat, phone, branch, etc.) | Contact channels offered |
| persuasive_framing | LLM (text) | gain / loss / mixed / neither | Gain vs loss framing (e.g., "save" vs "don't lose") |
| jargon_density | Deterministic (Python) | float (terms per 100 words) | Density of financial terms |
| sentence_length | Deterministic (Python) | float (words per sentence) | Average sentence length (readability) |
| primary_cta_visibility | Manual / Vision | yes / no | Whether the main CTA is visible in the initial viewport |