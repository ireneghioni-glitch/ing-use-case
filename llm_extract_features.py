"""
extract_features.py — Step 3: LLM-based feature extraction
=============================================================
Reads your team's cleaned dataset (default: data/processed/cleaned_assets.jsonl,
with the `text` field already extracted), sends each page's text + screenshot
to Groq's vision-capable model, and writes one structured record per page to
data/features/llm.parquet — matching the fields defined in features_selection.md.

SCOPE: only the LLM-derived fields (method = "LLM (text)" / "LLM (text + vision)" /
"LLM (vision)"). Deterministic (Python/HTML) and Manual fields are NOT computed
here — those are separate, non-LLM steps.

Use --input to point at a different file (e.g. the raw scraper output if the
cleaned dataset isn't ready yet — falls back to a naive HTML-tag-strip in that
case, see load_page_text()).

Install:
    pip install groq python-dotenv pandas pyarrow

Config (.env):
    GROQ_API_KEY=...
"""

import os
import re
import json
import base64
import sys
import time
from pathlib import Path

import pandas as pd
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
    from src.config import ASSETS_PATH  # kept for reference / --input fallback location
except ModuleNotFoundError:
    ASSETS_PATH = None  # not fatal anymore — the default input is cleaned_assets.jsonl below

# ASSUMPTION: this is where your team's cleaned/preprocessed dataset lives
# (with the `text` field already extracted — cleaned_assets.jsonl). Adjust
# this path if you move the file elsewhere, or override with --input.
DEFAULT_INPUT_PATH = Path("data/processed/cleaned_assets.jsonl")

# ASSUMPTION: output path — adjust if your team's FeatureRecord schema
# expects a different location. Mirrors the "data/features/llm.parquet"
# path from the task description.
FEATURES_PATH = DEFAULT_INPUT_PATH.parent.parent / "features" / "llm.parquet"
FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)

# Checkpoint: every successful extraction is appended here immediately, so a
# run that's stopped (rate limit, Ctrl+C, crash) can resume without redoing
# work already paid for. The final parquet is (re)built from this file.
CHECKPOINT_PATH = FEATURES_PATH.parent / "llm_features_checkpoint.jsonl"

# Failed extractions go here too (not mixed into the parquet — inconsistent schema)
ERRORS_PATH = FEATURES_PATH.parent / "llm_extraction_errors.jsonl"

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# Identifying columns carried over from AssetMetadata, so this output can be
# joined with the manual-annotation set (Step 2) and with campaign_asset
# itself on asset_id. ASSUMPTION: field names match AssetMetadata's — adjust
# if your team's FeatureRecord schema names these differently.
IDENTIFYING_FIELDS = [
    "asset_id", "bank", "bank_type", "channel",
    "audience_label", "url", "language", "collected_at", "pair_id",
]

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
    # Priority 1: the team's own extracted text (cleaned_assets.jsonl's `text` field)
    if asset.get("text"):
        return asset["text"]
    # Priority 2: a separate cleaned_text_path field, if that's how your team ships it
    cleaned_path = asset.get("cleaned_text_path")
    if cleaned_path and Path(cleaned_path).exists():
        return Path(cleaned_path).read_text(encoding="utf-8")
    # Fallback — naive HTML strip, flagged, not a substitute for real preprocessing
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


DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_BACKOFF_SECONDS = 5  # doubles each retry: 5, 10, 20 (~35s worst case per call)

MAX_RETRIES = DEFAULT_MAX_RETRIES
BASE_BACKOFF_SECONDS = DEFAULT_BASE_BACKOFF_SECONDS


def _call_groq_with_retry(**kwargs):
    """Wraps client.chat.completions.create with retry + exponential backoff
    on rate-limit (429) errors. Kept short on purpose: if the account is
    truly rate/quota-limited (not just a transient per-minute spike), a long
    wait here just delays the inevitable — the circuit breaker in main()
    handles that case by stopping the run instead."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            status = getattr(e, "status_code", None)
            is_rate_limit = status == 429 or "429" in str(e) or "rate_limit" in str(e).lower()
            if not is_rate_limit or attempt == MAX_RETRIES:
                raise
            wait = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
            print(f"    Rate limited — waiting {wait}s before retry {attempt}/{MAX_RETRIES}...")
            time.sleep(wait)


def extract_features_for_asset(asset: dict) -> dict:
    page_text = load_page_text(asset)
    image_b64 = encode_screenshot(asset["screenshot_path"])
    user_prompt = build_user_prompt(page_text, asset)

    completion = _call_groq_with_retry(
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
    identifying = {k: asset.get(k) for k in IDENTIFYING_FIELDS}

    try:
        features = json.loads(raw)
    except json.JSONDecodeError:
        return {**identifying, "_error": "invalid_json", "_raw_response": raw}

    missing = set(FEATURE_SCHEMA) - set(features)
    if missing:
        features["_missing_fields"] = sorted(missing)

    return {**identifying, **features}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract LLM-based features from the cleaned dataset")
    parser.add_argument("--limit", type=int, default=None,
                         help="Only process the first N assets (use this for testing before a full run)")
    parser.add_argument("--bank", type=str, default=None,
                         help="Only process assets from this bank (matches the 'bank' field, e.g. 'N26', 'KBC')")
    parser.add_argument("--input", type=str, default=None,
                         help=f"Path to the input jsonl file (default: {DEFAULT_INPUT_PATH})")
    parser.add_argument("--include-insufficient", action="store_true",
                         help="Also process assets with cleaning_status == 'insufficient_text' (skipped by default)")
    parser.add_argument("--sleep", type=float, default=2.0,
                         help="Seconds to wait between each API call, as a preventive rate-limit measure (default: 2.0)")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                         help=f"Retries per call on a 429 before giving up on that asset (default: {DEFAULT_MAX_RETRIES})")
    parser.add_argument("--base-backoff", type=float, default=DEFAULT_BASE_BACKOFF_SECONDS,
                         help=f"Base backoff in seconds, doubles each retry (default: {DEFAULT_BASE_BACKOFF_SECONDS})")
    parser.add_argument("--max-consecutive-failures", type=int, default=3,
                         help="Stop the whole run after this many consecutive rate-limit failures — "
                              "signals a quota/daily limit rather than a transient spike (default: 3)")
    parser.add_argument("--no-resume", action="store_true",
                         help="Ignore the checkpoint file and reprocess everything, even assets already done")
    parser.add_argument("--dry-run", action="store_true",
                         help="Print results to the console instead of writing to the checkpoint/parquet files")
    args = parser.parse_args()

    global MAX_RETRIES, BASE_BACKOFF_SECONDS
    MAX_RETRIES = args.max_retries
    BASE_BACKOFF_SECONDS = args.base_backoff

    input_path = Path(args.input) if args.input else DEFAULT_INPUT_PATH
    if not input_path.exists():
        print(f"'{input_path}' not found — check the path, or pass --input <path> to point at the right file.")
        return

    with input_path.open(encoding="utf-8") as f:
        lines = f.readlines()

    if not args.include_insufficient:
        kept = []
        skipped = 0
        for l in lines:
            d = json.loads(l)
            if d.get("cleaning_status") == "insufficient_text":
                skipped += 1
                continue
            kept.append(l)
        lines = kept
        if skipped:
            print(f"Skipped {skipped} asset(s) with cleaning_status='insufficient_text' "
                  f"(use --include-insufficient to process them anyway).\n")

    if args.bank:
        lines = [l for l in lines if json.loads(l).get("bank", "").lower() == args.bank.lower()]
        if not lines:
            print(f"No assets found for bank='{args.bank}'. Check the exact 'bank' field value in the input file.")
            return

    # --- Resume: skip asset_ids already completed in a previous run ---
    already_done = set()
    if not args.dry_run and not args.no_resume and CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open(encoding="utf-8") as cf:
            for cline in cf:
                try:
                    already_done.add(json.loads(cline)["asset_id"])
                except (json.JSONDecodeError, KeyError):
                    continue
        if already_done:
            before = len(lines)
            lines = [l for l in lines if json.loads(l)["asset_id"] not in already_done]
            print(f"Resuming: {before - len(lines)} asset(s) already in the checkpoint, skipped "
                  f"(use --no-resume to reprocess everything).\n")

    if args.limit:
        lines = lines[:args.limit]

    if not lines:
        print("Nothing left to process.")
        return

    print(f"Processing {len(lines)} asset(s){' (dry run — nothing written)' if args.dry_run else ''}...\n")

    errors = []
    consecutive_failures = 0
    checkpoint_file = None if args.dry_run else CHECKPOINT_PATH.open("a", encoding="utf-8")

    try:
        for i, line in enumerate(lines, start=1):
            asset = json.loads(line)
            print(f"[{i}/{len(lines)}] {asset['asset_id']}")
            try:
                result = extract_features_for_asset(asset)
            except Exception as e:
                result = {"asset_id": asset["asset_id"], "_error": str(e)}

            if args.dry_run:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                print("-" * 60)
                if args.sleep and i < len(lines):
                    time.sleep(args.sleep)
                continue

            if "_error" in result:
                errors.append(result)
                with ERRORS_PATH.open("a", encoding="utf-8") as ef:
                    ef.write(json.dumps(result, ensure_ascii=False) + "\n")

                is_rate_limit = "429" in str(result["_error"]) or "rate_limit" in str(result["_error"]).lower()
                consecutive_failures = consecutive_failures + 1 if is_rate_limit else 0

                if consecutive_failures >= args.max_consecutive_failures:
                    print(
                        f"\nStopping: {consecutive_failures} consecutive rate-limit failures — "
                        f"this looks like a quota/daily limit, not a transient spike. "
                        f"Progress so far is saved in {CHECKPOINT_PATH}. "
                        f"Re-run the same command once the limit resets — already-completed "
                        f"assets will be skipped automatically."
                    )
                    break
            else:
                consecutive_failures = 0
                checkpoint_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                checkpoint_file.flush()

            if args.sleep and i < len(lines):
                time.sleep(args.sleep)
    finally:
        if checkpoint_file:
            checkpoint_file.close()

    if args.dry_run:
        print("\nDry run complete — nothing was written. Re-run without --dry-run once the output looks right.")
        return

    # --- Consolidate the checkpoint into the final parquet ---
    if CHECKPOINT_PATH.exists():
        records = []
        with CHECKPOINT_PATH.open(encoding="utf-8") as cf:
            for cline in cf:
                try:
                    records.append(json.loads(cline))
                except json.JSONDecodeError:
                    continue
        if records:
            df = pd.DataFrame(records).drop_duplicates(subset="asset_id", keep="last")
            df.to_parquet(FEATURES_PATH, index=False)
            print(f"\n{len(df)} record(s) written to {FEATURES_PATH}.")

    if errors:
        print(f"{len(errors)} error(s) this run, logged to {ERRORS_PATH}.")
        print(f"{len(errors)} error(s) logged to {ERRORS_PATH} — check and re-run those asset_ids separately.")


if __name__ == "__main__":
    main()