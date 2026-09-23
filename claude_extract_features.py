"""
claude_extract_features.py — LLM-based feature extraction via Claude API (Haiku 4.5, Batch API)
====================================================================================================
Same job as extract_features.py (Groq version), but using Claude API — built to spend as
little as possible of a small budget:
  - Claude Haiku 4.5 only (cheapest current model)
  - Message Batches API (50% discount, results within 24h — fine since this isn't interactive)
  - Screenshots downscaled before sending (image cost scales with pixel count; a tall
    full-page screenshot can otherwise cost thousands of tokens)
  - A mandatory --estimate step using Anthropic's token-counting endpoint (no generation,
    effectively free) to get an exact cost projection BEFORE spending anything

Workflow:
    1. python claude_extract_features.py --estimate            # exact cost, no spend
    2. python claude_extract_features.py --confirm              # actually submits the batch
    3. python claude_extract_features.py --poll <batch_id>       # check status / fetch results
       (the script also polls automatically after submitting, unless --no-wait is passed)

Install:
    pip install anthropic python-dotenv pandas pyarrow pillow

Config (.env):
    ANTHROPIC_API_KEY=...
"""

import os
import io
import re
import json
import base64
import time
import hashlib
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from PIL import Image
import anthropic

load_dotenv()


def extract_json(raw: str) -> dict:
    """Claude sometimes wraps its JSON answer in markdown code fences (```json ... ```)
    even when asked not to — strip those before parsing rather than failing outright."""
    stripped = raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if match:
        stripped = match.group(1)
    return json.loads(stripped)


def get_response_text(message) -> str:
    """Find the text content block, skipping any thinking/redacted_thinking blocks
    that extended thinking can place before it — content[0] isn't reliably the
    text block once thinking is involved."""
    for block in message.content:
        if getattr(block, "type", None) == "text":
            return block.text
    raise ValueError(f"No text block found in message content: {message.content}")


def normalize_opening_guidance(record: dict) -> dict:
    """The model inconsistently returns opening_guidance.present as either a bool
    or a 'yes'/'no' string across different pages — PyArrow can't build a Parquet
    column from a mix of the two. Force it to always be the 'yes'/'no' string the
    schema specifies."""
    og = record.get("opening_guidance")
    if isinstance(og, dict) and "present" in og:
        present = og["present"]
        if isinstance(present, bool):
            og["present"] = "yes" if present else "no"
    return record

MODEL = "claude-sonnet-5"  # current-generation Sonnet — better judgment on subjective fields
MAX_TOKENS = 2048  # headroom for the ~28-field JSON response (bumped after seeing thinking eat the old 1024 budget)

# Batch API pricing (50% of standard) per model — verify against
# https://docs.claude.com/en/docs/about-claude/pricing before relying on this for budgeting.
BATCH_PRICING_PER_MTOK = {
    "claude-haiku-4-5-20251001": {"input": 0.50, "output": 2.50},
    "claude-sonnet-5": {"input": 1.50, "output": 7.50},
    "claude-opus-5": {"input": 2.50, "output": 12.50},
}

# Image cost scales with pixel count (~tokens = width*height/750). Full-page screenshots
# can be very tall — cap the total pixel count so cost per image stays predictable.
MAX_IMAGE_PIXELS = 1_000_000  # ≈ 1333 tokens/image at the (w*h)/750 formula

# Trim page text harder than the Groq version — cost control, not just context limits.
MAX_TEXT_CHARS = 4000

DEFAULT_INPUT_PATH = Path("data/processed/cleaned_assets.jsonl")
FEATURES_PATH = Path("data/features/llm_claude.parquet")  # separate file — don't mix model outputs silently
FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = FEATURES_PATH.parent / "llm_claude_checkpoint.jsonl"
ERRORS_PATH = FEATURES_PATH.parent / "llm_claude_extraction_errors.jsonl"
BATCH_ID_PATH = FEATURES_PATH.parent / "llm_claude_current_batch_id.txt"
CUSTOM_ID_MAP_PATH = FEATURES_PATH.parent / "llm_claude_custom_id_map.json"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

IDENTIFYING_FIELDS = [
    "asset_id", "bank", "bank_type", "channel",
    "audience_label", "url", "language", "collected_at", "pair_id",
]

FEATURE_SCHEMA = {
    "value_proposition_clarity": "clear-specific | clear-vague | unclear",
    "trust_signals": "JSON array (always a list, even with one item), values from: security_badge, deposit_guarantee, testimonials, customer_numbers, none",
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
    "price_in_initial_viewport": "yes | no — based on Image 1 (the initial viewport crop)",
    "primary_cta_visibility": "yes | no — based on Image 1 (the initial viewport crop)",
}

SYSTEM_PROMPT = """You are a marketing analyst extracting structured features from bank \
marketing web pages for a competitive comparison study. You are given the page's text \
content and a screenshot. Analyze both and return ONLY a valid JSON object matching the \
exact field names and allowed values given. Output raw JSON only: no prose, no markdown \
code fences (no ```json), no explanation before or after — your entire response must be \
parseable by json.loads() as-is."""


# ASSUMPTION: matches the viewport height your scraper used when capturing full-page
# screenshots (scraper.py's BrowserSession context: viewport={"height": 900}). Adjust
# if your scraper's viewport differs — this is what defines "visible without scrolling".
VIEWPORT_HEIGHT = 900
VIEWPORT_CROP_MAX_PIXELS = 400_000  # smaller cap — this crop only needs to show the top of the page


def resize_screenshot_b64(screenshot_path: str) -> tuple[str, str]:
    """Downscale the image so pixel count stays under MAX_IMAGE_PIXELS, keeping cost
    predictable regardless of how tall the original full-page screenshot is.
    Returns (base64_data, media_type)."""
    img = Image.open(screenshot_path).convert("RGB")
    w, h = img.size
    pixels = w * h
    if pixels > MAX_IMAGE_PIXELS:
        scale = (MAX_IMAGE_PIXELS / pixels) ** 0.5
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)  # jpeg: smaller payload, cost unaffected (pixel-based)
    return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"


def viewport_crop_b64(screenshot_path: str) -> tuple[str, str]:
    """Crop just the top VIEWPORT_HEIGHT px of the original full-page screenshot —
    i.e. what a visitor actually sees before scrolling. Needed for
    price_in_initial_viewport / primary_cta_visibility, which the full downscaled
    page image can't answer (it flattens the whole page, losing 'above the fold')."""
    img = Image.open(screenshot_path).convert("RGB")
    w, h = img.size
    crop_h = min(VIEWPORT_HEIGHT, h)
    img = img.crop((0, 0, w, crop_h))

    pixels = w * crop_h
    if pixels > VIEWPORT_CROP_MAX_PIXELS:
        scale = (VIEWPORT_CROP_MAX_PIXELS / pixels) ** 0.5
        img = img.resize((max(1, int(w * scale)), max(1, int(crop_h * scale))), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"


def load_page_text(asset: dict) -> str:
    if asset.get("text"):
        return asset["text"]
    cleaned_path = asset.get("cleaned_text_path")
    if cleaned_path and Path(cleaned_path).exists():
        return Path(cleaned_path).read_text(encoding="utf-8")
    return ""  # no naive HTML fallback here — this script assumes the cleaned dataset


def build_user_prompt(page_text: str, asset: dict) -> str:
    schema_block = json.dumps(FEATURE_SCHEMA, indent=2, ensure_ascii=False)
    trimmed_text = page_text[:MAX_TEXT_CHARS]
    return f"""Bank: {asset['bank']} ({asset['bank_type']})
URL: {asset['url']}
Language: {asset['language']}

### Page text
{trimmed_text}

### Fields to extract (JSON schema — field: allowed values)
{schema_block}

Return a single JSON object with exactly these keys, values matching the allowed
formats above. You are given two images: Image 1 is the initial viewport (what's
visible before scrolling — use this specifically for price_in_initial_viewport and
primary_cta_visibility), Image 2 is the full page (use this for the other visual
fields). If something can't be determined from the text or images, use your best
judgment rather than leaving it null, except for cta_text and topics which can be
an empty string / empty list if genuinely absent.
"""


def build_request_params(asset: dict) -> dict:
    page_text = load_page_text(asset)
    full_page_b64, full_media_type = resize_screenshot_b64(asset["screenshot_path"])
    viewport_b64, viewport_media_type = viewport_crop_b64(asset["screenshot_path"])
    user_prompt = build_user_prompt(page_text, asset)

    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "thinking": {"type": "disabled"},  # not needed for extraction, and was silently eating max_tokens
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "text", "text": "Image 1 — the initial viewport (what's visible before scrolling):"},
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": viewport_media_type, "data": viewport_b64},
                    },
                    {"type": "text", "text": "Image 2 — the full page:"},
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": full_media_type, "data": full_page_b64},
                    },
                ],
            }
        ],
    }


def load_assets(input_path: Path, bank: str | None, limit: int | None,
                 include_insufficient: bool, resume: bool) -> list[dict]:
    with input_path.open(encoding="utf-8") as f:
        assets = [json.loads(l) for l in f]

    if not include_insufficient:
        before = len(assets)
        assets = [a for a in assets if a.get("cleaning_status") != "insufficient_text"]
        skipped = before - len(assets)
        if skipped:
            print(f"Skipped {skipped} asset(s) with cleaning_status='insufficient_text'.")

    if bank:
        assets = [a for a in assets if a.get("bank", "").lower() == bank.lower()]

    if resume and CHECKPOINT_PATH.exists():
        done = set()
        with CHECKPOINT_PATH.open(encoding="utf-8") as cf:
            for line in cf:
                try:
                    done.add(json.loads(line)["asset_id"])
                except (json.JSONDecodeError, KeyError):
                    continue
        before = len(assets)
        assets = [a for a in assets if a["asset_id"] not in done]
        if done:
            print(f"Resuming: {before - len(assets)} asset(s) already done, skipped.")

    if limit:
        assets = assets[:limit]

    return assets


# --- Pricing note: BATCH_PRICING_PER_MTOK above is used by estimate() to project cost
# for whichever MODEL is currently set. Verify against the official pricing page. ---


def estimate(assets: list[dict]):
    print(f"Counting exact input tokens for {len(assets)} asset(s) via the (free) count_tokens endpoint...\n")
    total_input_tokens = 0
    failed = []

    for i, asset in enumerate(assets, start=1):
        try:
            params = build_request_params(asset)
            count = client.messages.count_tokens(
                model=params["model"],
                system=params["system"],
                messages=params["messages"],
            )
            total_input_tokens += count.input_tokens
            if i % 25 == 0 or i == len(assets):
                print(f"  [{i}/{len(assets)}] running total: {total_input_tokens} input tokens")
        except Exception as e:
            failed.append((asset["asset_id"], str(e)))

    # Output tokens aren't counted by count_tokens (nothing is generated) — estimate
    # from the schema size: ~28 fields, short values → roughly 400 tokens is a safe upper bound.
    estimated_output_tokens = 400 * len(assets)

    pricing = BATCH_PRICING_PER_MTOK.get(MODEL, BATCH_PRICING_PER_MTOK["claude-sonnet-5"])
    input_cost = total_input_tokens / 1_000_000 * pricing["input"]
    output_cost = estimated_output_tokens / 1_000_000 * pricing["output"]
    total_cost = input_cost + output_cost

    print(f"\n=== Estimate (Batch API, {MODEL}) ===")
    print(f"Assets: {len(assets)}  |  Failed to count: {len(failed)}")
    print(f"Total input tokens: {total_input_tokens:,}")
    print(f"Estimated output tokens: {estimated_output_tokens:,} (assumed ~400/asset)")
    print(f"Estimated cost: ${total_cost:.3f}  (input: ${input_cost:.3f}, output: ${output_cost:.3f})")
    if failed:
        print(f"\n{len(failed)} asset(s) failed token counting — check them before running for real:")
        for asset_id, err in failed[:5]:
            print(f"  - {asset_id}: {err}")
    print(f"\nIf this looks right, run again with --confirm to actually submit the batch.")


def short_custom_id(asset_id: str) -> str:
    """Batch API caps custom_id at 64 chars — some asset_ids (with language + hash
    suffix) exceed that, so use a short deterministic hash instead and keep a
    mapping back to the real asset_id for poll_and_collect to resolve."""
    return hashlib.sha1(asset_id.encode("utf-8")).hexdigest()  # 40 chars, well under the limit


def submit_batch(assets: list[dict]) -> str:
    requests = []
    skipped = []
    custom_id_map = {}
    for asset in assets:
        try:
            params = build_request_params(asset)
            cid = short_custom_id(asset["asset_id"])
            custom_id_map[cid] = asset["asset_id"]
            requests.append({"custom_id": cid, "params": params})
        except Exception as e:
            skipped.append({"asset_id": asset["asset_id"], "_error": f"build_request failed: {e}"})

    if skipped:
        with ERRORS_PATH.open("a", encoding="utf-8") as ef:
            for s in skipped:
                ef.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"{len(skipped)} asset(s) failed to build a request (logged to {ERRORS_PATH}), skipped.")

    if not requests:
        print("Nothing to submit.")
        return None

    # Persist the custom_id -> asset_id mapping, merging with any prior batches'
    # mappings rather than overwriting (so old batches can still be polled/resolved).
    existing_map = {}
    if CUSTOM_ID_MAP_PATH.exists():
        existing_map = json.loads(CUSTOM_ID_MAP_PATH.read_text(encoding="utf-8"))
    existing_map.update(custom_id_map)
    CUSTOM_ID_MAP_PATH.write_text(json.dumps(existing_map, ensure_ascii=False), encoding="utf-8")

    batch = client.messages.batches.create(requests=requests)
    BATCH_ID_PATH.write_text(batch.id)
    print(f"Batch submitted: {batch.id}  ({len(requests)} request(s))")
    print(f"Batch id saved to {BATCH_ID_PATH} — you can close this terminal and check back later with:")
    print(f"  python claude_extract_features.py --poll {batch.id}")
    return batch.id


def load_identifying_lookup(input_path: Path) -> dict:
    """asset_id -> identifying fields, reloaded from the input file so poll_and_collect
    can enrich batch results the same way the Groq script does — batch results only
    carry custom_id + the model's output, not the original asset's metadata."""
    lookup = {}
    with input_path.open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            lookup[d["asset_id"]] = {k: d.get(k) for k in IDENTIFYING_FIELDS}
    return lookup


def poll_and_collect(batch_id: str, wait: bool = True, input_path: Path = DEFAULT_INPUT_PATH):
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        print(f"Status: {batch.processing_status}  "
              f"(succeeded={batch.request_counts.succeeded}, "
              f"errored={batch.request_counts.errored}, "
              f"processing={batch.request_counts.processing})")
        if batch.processing_status == "ended":
            break
        if not wait:
            print("Still processing — re-run with --poll to check again later.")
            return
        time.sleep(30)

    successes, errors = [], []
    identifying = load_identifying_lookup(input_path)
    custom_id_map = {}
    if CUSTOM_ID_MAP_PATH.exists():
        custom_id_map = json.loads(CUSTOM_ID_MAP_PATH.read_text(encoding="utf-8"))

    with CHECKPOINT_PATH.open("a", encoding="utf-8") as ckpt:
        for result in client.messages.batches.results(batch_id):
            asset_id = custom_id_map.get(result.custom_id, result.custom_id)  # fall back to raw id if unmapped
            if result.result.type == "succeeded":
                try:
                    raw = get_response_text(result.result.message)
                except ValueError as e:
                    errors.append({"asset_id": asset_id, "_error": str(e)})
                    continue
                try:
                    features = extract_json(raw)
                except json.JSONDecodeError:
                    errors.append({"asset_id": asset_id, "_error": "invalid_json", "_raw_response": raw})
                    continue
                record = normalize_opening_guidance({**identifying.get(asset_id, {"asset_id": asset_id}), **features})
                successes.append(record)
                ckpt.write(json.dumps(record, ensure_ascii=False) + "\n")
            else:
                errors.append({"asset_id": asset_id, "_error": str(result.result)})

    if errors:
        with ERRORS_PATH.open("a", encoding="utf-8") as ef:
            for e in errors:
                ef.write(json.dumps(e, ensure_ascii=False) + "\n")

    # Consolidate checkpoint -> parquet
    if CHECKPOINT_PATH.exists():
        records = []
        with CHECKPOINT_PATH.open(encoding="utf-8") as cf:
            for line in cf:
                try:
                    records.append(normalize_opening_guidance(json.loads(line)))
                except json.JSONDecodeError:
                    continue
        if records:
            df = pd.DataFrame(records).drop_duplicates(subset="asset_id", keep="last")
            df.to_parquet(FEATURES_PATH, index=False)
            print(f"\n{len(df)} record(s) written to {FEATURES_PATH}.")

    print(f"{len(successes)} succeeded, {len(errors)} errored this batch.")
    if errors:
        print(f"Errors logged to {ERRORS_PATH}.")


def test_live(assets: list[dict]):
    """Direct (non-batch) call — slightly pricier per-token (no batch discount) but
    returns immediately, useful for a quick sanity check on 1-2 pages before committing
    to a batch run."""
    pricing = BATCH_PRICING_PER_MTOK.get(MODEL, BATCH_PRICING_PER_MTOK["claude-sonnet-5"])
    standard_input = pricing["input"] * 2  # batch is 50% of standard
    standard_output = pricing["output"] * 2

    for asset in assets:
        print(f"--- {asset['asset_id']} ---")
        params = build_request_params(asset)
        message = client.messages.create(**params)
        raw = get_response_text(message)
        try:
            features = extract_json(raw)
            print(json.dumps({"asset_id": asset["asset_id"], **features}, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(f"Invalid JSON returned:\n{raw}")

        cost = (message.usage.input_tokens / 1_000_000 * standard_input
                + message.usage.output_tokens / 1_000_000 * standard_output)
        print(f"[{message.usage.input_tokens} input + {message.usage.output_tokens} output tokens, "
              f"${cost:.4f} at standard (non-batch) pricing]\n")


def main():
    import argparse

    global MODEL

    parser = argparse.ArgumentParser(description="Extract LLM-based features via Claude API (Batch, Haiku 4.5)")
    parser.add_argument("--input", type=str, default=None, help=f"Input jsonl (default: {DEFAULT_INPUT_PATH})")
    parser.add_argument("--bank", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--include-insufficient", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--model", type=str, default=None,
                         help=f"Override the model (default: {MODEL}). "
                              f"Known options with pricing: {', '.join(BATCH_PRICING_PER_MTOK)}")
    parser.add_argument("--test-live", action="store_true",
                         help="Direct (non-batch) call for a quick sanity check — returns immediately, "
                              "small cost at standard (non-discounted) pricing. Combine with --limit 1.")
    parser.add_argument("--estimate", action="store_true",
                         help="Only compute the exact cost (via count_tokens) — no batch is submitted, nothing is spent")
    parser.add_argument("--confirm", action="store_true",
                         help="Actually submit the batch (required — running with neither --estimate nor --confirm does nothing)")
    parser.add_argument("--no-wait", action="store_true",
                         help="Submit the batch and exit immediately instead of polling until it's done")
    parser.add_argument("--poll", type=str, default=None, nargs="?", const="__last__", metavar="BATCH_ID",
                         help="Check status / fetch results of a submitted batch. Pass the batch id, "
                              "or omit it to use the last one saved by this script.")
    args = parser.parse_args()

    if args.model:
        MODEL = args.model

    if args.poll:
        batch_id = args.poll
        if batch_id == "__last__":
            if not BATCH_ID_PATH.exists():
                print("No saved batch id found — pass one explicitly: --poll <batch_id>")
                return
            batch_id = BATCH_ID_PATH.read_text().strip()
        poll_input_path = Path(args.input) if args.input else DEFAULT_INPUT_PATH
        poll_and_collect(batch_id, wait=not args.no_wait, input_path=poll_input_path)
        return

    input_path = Path(args.input) if args.input else DEFAULT_INPUT_PATH
    if not input_path.exists():
        print(f"'{input_path}' not found.")
        return

    assets = load_assets(
        input_path, args.bank, args.limit, args.include_insufficient,
        resume=not args.no_resume,
    )
    if not assets:
        print("Nothing to process.")
        return

    if args.test_live:
        test_live(assets)
        return

    if args.estimate:
        estimate(assets)
        return

    if not args.confirm:
        print("This does nothing by default — pass --estimate to see the projected cost "
              "(free, no generation), or --confirm to actually submit the batch.")
        return

    batch_id = submit_batch(assets)
    if batch_id and not args.no_wait:
        poll_and_collect(batch_id, wait=True, input_path=input_path)


if __name__ == "__main__":
    main()