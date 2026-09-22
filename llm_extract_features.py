"""
extract_features.py — Step 3: LLM-based feature extraction
=============================================================
Reads campaign_asset.jsonl (produced by scraper.py + your team's preprocessing),
sends each page's text + screenshot to Groq's vision-capable model, and writes
one structured JSON record per page to campaign_feature.jsonl — matching the
fields defined in features_selection.md.

SCOPE: only the LLM-derived fields (method = "LLM (text)" / "LLM (text + vision)" /
"LLM (vision)"). Deterministic (Python/HTML) and Manual fields are NOT computed
here — those are separate, non-LLM steps.

ASSUMPTION: each asset record in campaign_asset.jsonl has a `cleaned_text_path`
field once your team's preprocessing stage has run. If that field is missing,
this script falls back to a naive HTML-tag-strip of raw_html_path — good enough
to unblock development, but your team's real cleaned text should replace it.

Install:
    pip install groq python-dotenv

Config (.env):
    GROQ_API_KEY=...
"""

import os
import re
import json
import base64
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_MODEL = "qwen/qwen3.8-27b"  # the only vision-capable model on this account's Groq access (verified via /v1/models)

# Reuse the same centralized path as scraper.py, rather than guessing a
# location — ASSETS_PATH is where scraper.py actually wrote campaign_asset.jsonl.
# ASSUMPTION: project layout unknown here — try this file's own directory and
# its parent, same as scraper.py's pattern. If this still fails, check where
# scraper.py itself sits relative to src/ and adjust the sys.path.insert below
# to match (e.g. drop one .parent if extract_features.py lives one level
# shallower/deeper than scraper.py).
_HERE = Path(__file__).resolve().parent
for _candidate in (_HERE, _HERE.parent):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

try:
    from src.config import ASSETS_PATH
except ModuleNotFoundError as e:
    print(
        "Could not import 'src.config' — this script's location relative to "
        "src/ doesn't match scraper.py's. Find src/config.py's actual path "
        "and either move this script next to scraper.py, or hardcode "
        "ASSETS_PATH = Path('<real path to campaign_asset.jsonl>') below instead."
    )
    raise e

FEATURES_PATH = ASSETS_PATH.parent / "campaign_feature.jsonl"  # same directory as campaign_asset.jsonl

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ---------------------------------------------------------------------------
# Feature schema — only LLM-derived fields from features_selection.md.
# Each entry: field -> allowed values / output description, used both to
# build the prompt and to sanity-check the response.
# ---------------------------------------------------------------------------
FEATURE_SCHEMA = {
    "value_proposition_clarity": "clear-specific | clear-vague | unclear",
    "trust_signals": "list, any of: security_badge, deposit_guarantee, testimonials, customer_numbers, none",
    "tone": "formal | persuasive | simple | playful",
    "sentiment": "positive | neutral | reassuring | urgent",
    "verbosity": "low | medium | high",
    "cta_clarity": "specific-action | vague-action | none",
    "cta_text": "free text — the main CTA button label",
    "distinctiveness": "high | medium | low",
    "visual_hierarchy_focus": "number/rate | face | product-shot | headline-text",
    "text_image_layout": "side-by-side | stacked | full-width-hero | text-only",
    "color_touch_location": "text | image | icon | none | mixed",
    "animation_level": "static | partial | fully-animated (best guess from the static screenshot)",
    "visual_type": "real-people | illustration | product-shot | abstract | none",
    "mobile_first_cues": "strong | moderate | weak",
    "topics": "list of up to 4 keywords",
    "main_benefit": "affordability | convenience | independence-control | security-support | lifestyle-rewards | other | mixed | unknown",
    "audience_explicit": "yes | no",
    "conditional_price_disclosure": "adjacent | elsewhere | not found",
    "eligibility_stated": "yes | no",
    "opening_guidance": "object: {present: yes/no, step_count: integer or null}",
    "support_options": "list of channels, e.g. chat, phone, branch, email",
    "persuasive_framing": "gain | loss | mixed | neither",
}

SYSTEM_PROMPT = """You are a marketing analyst extracting structured features from bank \
marketing web pages for a competitive comparison study. You are given the page's text \
content and a screenshot. Analyze both and return ONLY a valid JSON object matching the \
exact field names and allowed values given — no prose, no markdown fences, no explanation."""


def naive_html_to_text(html: str) -> str:
    """Fallback text extraction if cleaned_text_path isn't available yet.
    NOT a substitute for real preprocessing — strips tags/scripts only."""
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_page_text(asset: dict) -> str:
    cleaned_path = asset.get("cleaned_text_path")
    if cleaned_path and Path(cleaned_path).exists():
        return Path(cleaned_path).read_text(encoding="utf-8")
    # Fallback — flagged, not silent
    html = Path(asset["raw_html_path"]).read_text(encoding="utf-8")
    return naive_html_to_text(html)


def encode_screenshot(screenshot_path: str) -> str:
    data = Path(screenshot_path).read_bytes()
    return base64.b64encode(data).decode("utf-8")


def build_user_prompt(page_text: str, asset: dict) -> str:
    schema_block = json.dumps(FEATURE_SCHEMA, indent=2, ensure_ascii=False)
    # Truncate very long pages to keep the request light — adjust if needed
    trimmed_text = page_text[:6000]
    return f"""Bank: {asset['bank']} ({asset['bank_type']})
URL: {asset['url']}
Language: {asset['language']}

### Page text
{trimmed_text}

### Fields to extract (JSON schema — field: allowed values)
{schema_block}

Return a single JSON object with exactly these keys, values matching the allowed
formats above. If something can't be determined from the text or image, use your
best judgment rather than leaving it null, except for cta_text and topics which can
be an empty string / empty list if genuinely absent.
"""


def extract_features_for_asset(asset: dict) -> dict:
    page_text = load_page_text(asset)
    image_b64 = encode_screenshot(asset["screenshot_path"])
    user_prompt = build_user_prompt(page_text, asset)

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            },
        ],
        temperature=0.1,  # low — this is extraction, not creative writing
        response_format={"type": "json_object"},
    )

    raw = completion.choices[0].message.content
    try:
        features = json.loads(raw)
    except json.JSONDecodeError:
        return {"asset_id": asset["asset_id"], "error": "invalid_json", "raw_response": raw}

    missing = set(FEATURE_SCHEMA) - set(features)
    if missing:
        features["_missing_fields"] = sorted(missing)

    return {"asset_id": asset["asset_id"], "url": asset["url"], "bank": asset["bank"], **features}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract LLM-based features from campaign_asset.jsonl")
    parser.add_argument("--limit", type=int, default=None,
                         help="Only process the first N assets (use this for testing before a full run)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Print results to the console instead of writing to campaign_feature.jsonl")
    args = parser.parse_args()

    if not ASSETS_PATH.exists():
        print(f"'{ASSETS_PATH}' not found — check the path (see ASSUMPTION at the top of this file).")
        return

    with ASSETS_PATH.open(encoding="utf-8") as f:
        lines = f.readlines()

    if args.limit:
        lines = lines[:args.limit]

    print(f"Processing {len(lines)} asset(s){' (dry run — nothing written)' if args.dry_run else ''}...\n")

    out_file = None if args.dry_run else FEATURES_PATH.open("a", encoding="utf-8")

    try:
        for i, line in enumerate(lines, start=1):
            asset = json.loads(line)
            print(f"[{i}/{len(lines)}] {asset['asset_id']}")
            try:
                result = extract_features_for_asset(asset)
            except Exception as e:
                result = {"asset_id": asset["asset_id"], "error": str(e)}

            if args.dry_run:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                print("-" * 60)
            else:
                out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
    finally:
        if out_file:
            out_file.close()

    if not args.dry_run:
        print(f"\nDone. Features written to {FEATURES_PATH}")
    else:
        print("\nDry run complete — nothing was written. Re-run without --dry-run once the output looks right.")


if __name__ == "__main__":
    main()