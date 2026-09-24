"""
extract_features.py

Extract structural + visual (colour) features from saved bank webpages for
cross-bank comparison (ING Belgium use case).

EXPECTED FOLDER LAYOUT (matches your project)
-----------------------------------------------
ing-use-case/
  data/
    raw/
      argenta_10-tips-voor-jongeren-om-geld-te-sparen-html.html
      argenta_les-jeunes-html.html
      ...
      screenshots/
        argenta_10-tips-voor-jongeren-om-geld-te-sparen-html.png   <- same stem as the .html
        argenta_les-jeunes-html.png
        ...
    features/                <- output CSVs go here

Each .html file's screenshot is matched by identical filename stem
(everything before ".html" / ".png"). No URL list or live rendering is
needed for the core feature set, since you already have the screenshots.

ASSET_ID / JOIN KEY
--------------------
The real asset_id format (confirmed from your labelled features file) is:

    {bank_lower}__{safe_name}__{lang}__{sha256(url)[:10]}

e.g. "kbc__jongeren-zijn-de-influencers...__fr__6609cb7e08"

That trailing hash is sha256 of the EXACT url string used at scrape time
(scheme, "www.", trailing slash, query string all affect it) - so it is
NOT safely reconstructable from a fuzzy filename<->url match. Three ways
to get it, in order of preference:

  1) BEST: --assets_jsonl campaign_asset.jsonl (the scraper's own output).
     Read asset_id/url/bank/language straight from it, matched by exact
     filename - no guessing at all.
  2) GOOD: --assets_table your_labelled_file.xlsx (or .csv) - any file
     that already has asset_id/bank/url columns, such as your llm_claude_
     FinalFeatures.xlsx. Matched by fuzzy slug comparison SCOPED TO THE
     SAME BANK first (derived from the filename prefix), which is far
     more reliable than an unscoped fuzzy match. A match_score column and
     a low-confidence warning (<0.75) are added so you can spot-check.
  3) FALLBACK: --urls urls.txt with the *exact* URLs originally scraped,
     matched to files by filename-slug similarity, and this script
     recomputes the asset_id itself via sha256. Use only if neither of
     the above is available.

In all cases, `url` (once known) is also written out as its own column -
a plain, hash-free join key you can always fall back to.

INSTALL
-------
    pip install beautifulsoup4 requests pillow numpy pandas scikit-learn
    # only needed if you use --render_live for heading/CTA colour:
    pip install playwright
    python -m playwright install chromium

WHERE TO PUT THIS FILE
-----------------------
Put it at the project root, next to "data/":
    ing-use-case/
      extract_features.py   <- here
      data/
        raw/...

RUN (from that folder, in a terminal / VS Code terminal)
----------------------------------------------------------
Best (exact asset_id, via campaign_asset.jsonl):

    python extract_features.py --raw_dir data/raw --out data/features/features.csv --assets_jsonl data/campaign_asset.jsonl

If you don't have campaign_asset.jsonl but do have a labelled file with
asset_id/bank/url columns (e.g. llm_claude_FinalFeatures.xlsx):

    python extract_features.py --raw_dir data/raw --out data/features/features.csv --assets_table llm_claude_FinalFeatures.xlsx

Without either (still gets structural + screenshot features; asset_id only
if you also pass --urls):

    python extract_features.py --raw_dir data/raw --out data/features/features.csv

Add --download_images to also fetch every <img src> referenced in the HTML
and compute per-image colour/size stats (needs internet, slower):

    python extract_features.py --raw_dir data/raw --out data/features/features.csv --assets_table llm_claude_FinalFeatures.xlsx --download_images

Add --render_live --urls urls.txt to additionally fetch heading_colour and
CTA_colour by rendering the live pages (needs internet + Playwright browser
installed, and a urls.txt with one URL per line - the same URLs that are in
campaign_asset.jsonl / your labelled file):

    python extract_features.py --raw_dir data/raw --out data/features/features.csv --assets_table llm_claude_FinalFeatures.xlsx --render_live --urls urls.txt
"""

import hashlib
import argparse
import difflib
import io
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def get_dominant_and_palette(img: Image.Image, k: int = 5):
    from sklearn.cluster import KMeans
    small = img.convert("RGB").resize((150, 150))
    arr = np.array(small).reshape(-1, 3)
    km = KMeans(n_clusters=k, n_init=4, random_state=0).fit(arr)
    counts = np.bincount(km.labels_)
    order = np.argsort(-counts)
    palette = [tuple(int(c) for c in km.cluster_centers_[i]) for i in order]
    return palette[0], palette


def brightness(img: Image.Image) -> float:
    return float(np.array(img.convert("L"), dtype=float).mean())


def colourfulness(img: Image.Image) -> float:
    arr = np.array(img.convert("RGB"), dtype=float)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    rg = r - g
    yb = 0.5 * (r + g) - b
    return float(
        np.sqrt(rg.std() ** 2 + yb.std() ** 2)
        + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    )


def whiteness_ratio(img: Image.Image, threshold: int = 235) -> float:
    gray = np.array(img.convert("L"))
    return float((gray >= threshold).mean())


def rgb_to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def relative_luminance(rgb) -> float:
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(rgb1, rgb2) -> float:
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    l1, l2 = max(l1, l2), min(l1, l2)
    return round((l1 + 0.05) / (l2 + 0.05), 2)


def parse_css_rgb(css_colour: str):
    if not css_colour:
        return None
    m = re.match(r"rgba?\(([\d\.\s,]+)\)", css_colour)
    if not m:
        return None
    parts = [float(x) for x in m.group(1).split(",")]
    if len(parts) < 3:
        return None
    return tuple(int(round(p)) for p in parts[:3])


def image_colour_stats(img: Image.Image) -> dict:
    dominant, palette = get_dominant_and_palette(img)
    w, h = img.size
    return {
        "width": w,
        "height": h,
        "dominant_colour": rgb_to_hex(dominant),
        "palette": [rgb_to_hex(c) for c in palette],
        "brightness": round(brightness(img), 2),
        "colourfulness": round(colourfulness(img), 2),
        "whiteness_ratio": round(whiteness_ratio(img), 3),
    }


# ---------------------------------------------------------------------------
# asset_id — two ways to get it, in order of preference
# ---------------------------------------------------------------------------
# The real format (confirmed against the labelled features file) is:
#     {bank_lower}__{safe_name}__{lang}__{sha256(url)[:10]}
# e.g. "kbc__jongeren-zijn-de-influencers...__fr__6609cb7e08"
#
# PREFERRED: load campaign_asset.jsonl (the scraper's own output) and read
# asset_id/url/bank/language straight from it, matched by exact filename.
# No guessing, no hash reconstruction needed.
#
# FALLBACK: if you don't have the jsonl but do have the exact original url
# (e.g. from urls.txt via --urls), recompute the same asset_id yourself.

BANK_KEYS = [
    "ing", "bnp_fortis", "kbc", "belfius", "revolut",
    "argenta", "n26", "beobank", "bunq",
]
# Local .html filenames use these prefixes (confirmed from your folder listing:
# "bnp_fortis_...", "argenta_...", etc). The BANK key actually embedded in the
# real asset_id is "bnp-paribas-fortis" (hyphenated) for BNP, everything else
# matches 1:1 - so alias just that one.
FILENAME_TO_ASSET_BANK = {
    "bnp_fortis": "bnp-paribas-fortis",
}


def slugify_segment(text: str) -> str:
    """Mirrors scraper.py's slugify() for a single URL path segment."""
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return text.strip("-")[:80]


def detect_language(url: str) -> str:
    """Mirrors scraper.py's detect_language() exactly."""
    lower = url.lower()
    for code in ("fr-be", "en-be", "nl-be"):
        if code in lower:
            return code.split("-")[0]
    for seg, lang in (("/fr/", "fr"), ("/nl/", "nl"), ("/en/", "en")):
        if seg in lower:
            return lang
    return "fr"


def guess_bank_from_stem(stem: str) -> tuple[str | None, str | None, str | None]:
    """('bnp_fortis_guide-job-etudiant') -> ('bnp_fortis', 'bnp-paribas-fortis', 'guide-job-etudiant')
    Returns (filename_bank_prefix, canonical_asset_bank_key, remainder_slug).
    Longest-prefix match since some bank prefixes (bnp_fortis) contain '_'."""
    for bank in sorted(BANK_KEYS, key=len, reverse=True):
        prefix = bank + "_"
        if stem.startswith(prefix):
            remainder = stem[len(prefix):]
            canonical = FILENAME_TO_ASSET_BANK.get(bank, bank)
            return bank, canonical, remainder
    return None, None, None


def compute_asset_id(bank: str, url: str) -> str:
    """Exact reproduction of the pipeline's asset_id for a KNOWN bank + exact url.
    Only trustworthy if `url` is byte-for-byte the same string that was
    originally scraped (scheme, www., trailing slash, query string all
    change the hash). Note: the last path segment has its file extension
    (.html etc) stripped BEFORE slugifying - confirmed against real
    asset_id values, e.g. ".../generaties.html" -> "...generaties" (no
    "-html" suffix), which a plain slugify(last_segment) would produce."""
    last_segment = url.rstrip("/").split("/")[-1] or "page"
    last_segment = re.sub(r"\.[a-zA-Z0-9]{2,5}$", "", last_segment)  # strip .html/.aspx/etc
    safe_name = slugify_segment(last_segment)
    lang = detect_language(url)
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:10]
    return f"{bank.lower()}__{safe_name}__{lang}__{url_hash}"


def load_assets_jsonl(path: str) -> dict:
    """campaign_asset.jsonl -> {html_filename: record_dict}, keyed by the
    exact filename of raw_html_path, e.g. 'kbc_jongeren-...-html.html'."""
    import json
    by_filename = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            raw_html_path = rec.get("raw_html_path")
            if raw_html_path:
                by_filename[Path(raw_html_path).name] = rec
    return by_filename


def load_assets_table(path: str) -> list[dict]:
    """Load a CSV or XLSX that has (at least) asset_id, bank, url columns -
    e.g. your labelled features export. Column names are matched
    case-insensitively. Returns a list of plain dicts with lowercase keys.
    Rows missing asset_id or url are dropped (e.g. blank rows in the sheet)."""
    p = str(path).lower()
    if p.endswith((".xlsx", ".xls")):
        df = pd.read_excel(path)  # requires: pip install openpyxl
    else:
        df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "asset_id" not in df.columns or "url" not in df.columns:
        raise SystemExit(f"--assets_table file must have 'asset_id' and 'url' columns; found: {list(df.columns)}")
    df = df.dropna(subset=["asset_id", "url"])
    return df.to_dict("records")


def slug_similarity(a: str, b: str) -> float:
    norm = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def best_asset_table_match(filename_stem: str, canonical_bank: str | None, remainder_slug: str, records: list[dict], threshold: float = 0.5):
    """Match a local filename to a row in the assets table, scoped to the
    same bank first (via canonical_bank derived from the filename prefix) so
    the fuzzy comparison never accidentally matches a different bank's page.
    Falls back to comparing the whole filename stem against asset_id if the
    bank couldn't be guessed. Returns (record, score) or (None, 0.0)."""
    candidates = records
    compare_text = remainder_slug or filename_stem
    if canonical_bank:
        candidates = [r for r in records if str(r.get("asset_id", "")).split("__")[0].lower() == canonical_bank.lower()]
        if not candidates:
            candidates = records  # bank not found in table under that key - widen search rather than give up
            compare_text = filename_stem

    best_rec, best_score = None, 0.0
    for rec in candidates:
        parts = str(rec.get("asset_id", "")).split("__")
        table_safe_name = parts[1] if len(parts) > 1 else str(rec.get("asset_id", ""))
        score = slug_similarity(compare_text, table_safe_name)
        if score > best_score:
            best_rec, best_score = rec, score

    if best_rec and best_score >= threshold:
        return best_rec, best_score
    return None, best_score


# ---------------------------------------------------------------------------
# Structural features - from the saved .html file
# ---------------------------------------------------------------------------

CTA_SELECTOR = (
    "a.btn, a.button, a[class*='cta'], a[class*='btn'], "
    "button, input[type='submit'], input[type='button']"
)
CTA_KEYWORDS_NL = ["ontdek", "open", "simuleer", "aanvragen", "meer weten", "bereken"]
CTA_KEYWORDS_FR = ["découvrir", "ouvrir", "simuler", "demander", "en savoir plus", "calculer"]


def structural_features(html_path: Path) -> dict:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    imgs = soup.find_all("img")
    ctas = soup.select(CTA_SELECTOR)
    headings = {f"h{i}_count": len(soup.find_all(f"h{i}")) for i in range(1, 7)}
    text = soup.get_text(separator=" ", strip=True)
    cta_texts = " ".join(c.get_text(strip=True).lower() for c in ctas)
    viewport = soup.find("meta", attrs={"name": "viewport"})

    img_srcs = [
        (img.get("src") or img.get("data-src"))
        for img in imgs
        if img.get("src") or img.get("data-src")
    ]

    guessed_bank_prefix, guessed_canonical_bank, guessed_remainder = guess_bank_from_stem(html_path.stem)

    return {
        "stem": html_path.stem,
        "file": html_path.name,
        # placeholders - overwritten in main() from campaign_asset.jsonl /
        # assets_table when available; these guessed values are only a
        # filename-based fallback used to scope/seed the matching
        "bank": guessed_canonical_bank,
        "safe_name": guessed_remainder,
        "asset_id": None,
        "url": None,
        "language": None,
        "image_count": len(imgs),
        "cta_count": len(ctas),
        "cta_keyword_hits": sum(kw in cta_texts for kw in CTA_KEYWORDS_NL + CTA_KEYWORDS_FR),
        "word_count": len(text.split()),
        "link_count": len(soup.find_all("a")),
        "has_viewport_meta": bool(viewport),
        "img_srcs": img_srcs,
        **headings,
    }


def per_image_features(src: str, base_url: str | None = None) -> dict:
    """Download an <img src> referenced in the html and compute colour/size stats."""
    try:
        if src.startswith("http"):
            resp = requests.get(src, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            data = resp.content
        elif base_url:
            resp = requests.get(urljoin(base_url, src), timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            data = resp.content
        else:
            return {"src": src, "error": "no base_url to resolve relative src"}
        img = Image.open(io.BytesIO(data))
        stats = image_colour_stats(img)
        size_bytes = len(data)
        stats.update({
            "src": src,
            "size_bytes": size_bytes,
            "pixels_per_byte": round((stats["width"] * stats["height"]) / size_bytes, 4) if size_bytes else None,
        })
        return stats
    except Exception as e:
        return {"src": src, "error": str(e)}


# ---------------------------------------------------------------------------
# Screenshot-based page-level colour features (uses your existing PNGs)
# ---------------------------------------------------------------------------

def screenshot_features(png_path: Path) -> dict:
    img = Image.open(png_path)
    stats = image_colour_stats(img)
    return {
        "page_width": stats["width"],
        "page_height": stats["height"],
        "page_dominant_colour": stats["dominant_colour"],
        "page_palette": stats["palette"],
        "page_brightness": stats["brightness"],
        "page_colourfulness": stats["colourfulness"],
        "page_whiteness_ratio": stats["whiteness_ratio"],
    }


# ---------------------------------------------------------------------------
# Optional: live render for heading_colour / CTA_colour (needs Playwright + URL)
# ---------------------------------------------------------------------------

def render_colour_features(url: str) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=45000)

        heading_colour_css = page.evaluate(
            """() => {
                const h = document.querySelector('h1, h2');
                return h ? getComputedStyle(h).color : null;
            }"""
        )
        cta_style = page.evaluate(
            f"""() => {{
                const btn = document.querySelector("{CTA_SELECTOR}");
                if (!btn) return null;
                const s = getComputedStyle(btn);
                return {{bg: s.backgroundColor, color: s.color}};
            }}"""
        )
        body_bg_css = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
        browser.close()

    heading_rgb = parse_css_rgb(heading_colour_css)
    body_rgb = parse_css_rgb(body_bg_css) or (255, 255, 255)

    return {
        "heading_colour": heading_colour_css,
        "heading_colour_hex": rgb_to_hex(heading_rgb) if heading_rgb else None,
        "cta_bg_colour": cta_style["bg"] if cta_style else None,
        "cta_text_colour": cta_style["color"] if cta_style else None,
        "heading_body_contrast": contrast_ratio(heading_rgb, body_rgb) if heading_rgb else None,
    }


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://(www\.)?", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def best_url_match(filename_stem: str, urls: list[str]) -> str | None:
    fslug = slugify(filename_stem)
    scores = [(difflib.SequenceMatcher(None, fslug, slugify(u)).ratio(), u) for u in urls]
    scores.sort(reverse=True)
    return scores[0][1] if scores and scores[0][0] > 0.35 else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw_dir", required=True, help="Folder containing the .html files, e.g. data/raw")
    ap.add_argument("--screenshots_subdir", default="screenshots", help="Subfolder of raw_dir with matching .png files")
    ap.add_argument("--out", default="data/features/features.csv")
    ap.add_argument("--download_images", action="store_true", help="Also fetch each <img src> in the html for per-image colour stats (needs internet)")
    ap.add_argument("--render_live", action="store_true", help="Also render live URL for heading_colour/CTA_colour (needs Playwright + --urls)")
    ap.add_argument("--urls", default=None, help="Text file, one URL per line - fallback source for url/asset_id and used by --render_live")
    ap.add_argument("--assets_jsonl", default=None, help="Path to campaign_asset.jsonl (scraper's own output) - BEST source: exact asset_id/url/bank/language, joined by exact filename")
    ap.add_argument("--assets_table", default=None, help="Path to a CSV or XLSX with asset_id/bank/url columns (e.g. your labelled features export) - GOOD source when you don't have campaign_asset.jsonl. Joined by bank-scoped fuzzy filename match")
    ap.add_argument("--match_threshold", type=float, default=0.5, help="Minimum fuzzy-match score (0-1) to accept an --assets_table match, default 0.5")
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    shots_dir = raw_dir / args.screenshots_subdir
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    assets_by_filename = {}
    if args.assets_jsonl:
        assets_by_filename = load_assets_jsonl(args.assets_jsonl)
        print(f"Loaded {len(assets_by_filename)} records from {args.assets_jsonl}")

    assets_table = []
    if args.assets_table:
        assets_table = load_assets_table(args.assets_table)
        print(f"Loaded {len(assets_table)} records from {args.assets_table}")

    urls = []
    if args.urls:
        with open(args.urls, encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    if args.render_live and not urls:
        raise SystemExit("--render_live requires --urls path/to/urls.txt")

    rows = []
    img_rows = []
    unmatched = []
    low_confidence = []

    html_files = sorted(raw_dir.glob("*.html"))
    print(f"Found {len(html_files)} html files in {raw_dir}")

    for fp in html_files:
        row = structural_features(fp)
        _, canonical_bank, remainder_slug = guess_bank_from_stem(fp.stem)

        png_path = shots_dir / f"{fp.stem}.png"
        if png_path.exists():
            try:
                row.update(screenshot_features(png_path))
                row["screenshot_matched"] = True
            except Exception as e:
                row["screenshot_error"] = str(e)
                row["screenshot_matched"] = False
        else:
            row["screenshot_matched"] = False
            print(f"  [!] no matching screenshot for {fp.name} (expected {png_path.name})")

        # --- asset_id / url / bank / language, in priority order ---
        # 1) campaign_asset.jsonl, exact filename match (best)
        # 2) assets_table (e.g. your labelled xlsx/csv), bank-scoped fuzzy match on the slug
        # 3) urls.txt, fuzzy match + recompute the real hash-based asset_id ourselves
        # 4) unmatched
        rec = assets_by_filename.get(fp.name)
        if rec:
            row["asset_id"] = rec.get("asset_id")
            row["url"] = rec.get("url")
            row["bank"] = rec.get("bank")
            row["language"] = rec.get("language")
            row["audience_label"] = rec.get("audience_label")
            row["id_source"] = "assets_jsonl"
        elif assets_table:
            match, score = best_asset_table_match(fp.stem, canonical_bank, remainder_slug, assets_table, threshold=args.match_threshold)
            row["match_score"] = round(score, 3)
            if match:
                row["asset_id"] = match.get("asset_id")
                row["url"] = match.get("url")
                row["bank"] = match.get("bank", canonical_bank)
                row["language"] = match.get("language")
                row["id_source"] = "assets_table_fuzzy_match"
                if score < 0.75:
                    low_confidence.append((fp.name, row["asset_id"], score))
            elif urls and canonical_bank:
                url = best_url_match(fp.stem, urls)
                if url:
                    row["url"] = url
                    row["asset_id"] = compute_asset_id(canonical_bank, url)
                    row["language"] = detect_language(url)
                    row["id_source"] = "urls_txt_fuzzy_match"
                else:
                    unmatched.append(fp.name)
                    row["id_source"] = "unmatched"
            else:
                unmatched.append(fp.name)
                row["id_source"] = "unmatched"
        elif urls and canonical_bank:
            # best-effort: fuzzy-match a url by filename slug, then recompute the
            # real asset_id from it. Only as good as the fuzzy match - spot check.
            url = best_url_match(fp.stem, urls)
            if url:
                row["url"] = url
                row["asset_id"] = compute_asset_id(canonical_bank, url)
                row["language"] = detect_language(url)
                row["id_source"] = "urls_txt_fuzzy_match"
            else:
                unmatched.append(fp.name)
                row["id_source"] = "unmatched"
        else:
            unmatched.append(fp.name)
            row["id_source"] = "unmatched"

        if args.render_live and row.get("url"):
            try:
                print(f"  Rendering {row['url']} for heading/CTA colour ...")
                row.update(render_colour_features(row["url"]))
            except Exception as e:
                row["render_error"] = str(e)

        if args.download_images:
            for src in row["img_srcs"]:
                img_rows.append({
                    "stem": fp.stem,
                    "asset_id": row.get("asset_id"),
                    "url": row.get("url"),
                    **per_image_features(src, row.get("url")),
                })

        rows.append(row)

    if low_confidence:
        print(f"\n[?] {len(low_confidence)} file(s) matched via --assets_table but with a low confidence score (<0.75) - spot check these:")
        for name, asset_id, score in low_confidence:
            print(f"    - {name}  ->  {asset_id}  (score {score:.2f})")

    if unmatched:
        print(f"\n[!] {len(unmatched)} file(s) could not be linked to an asset_id/url:")
        for name in unmatched:
            print(f"    - {name}")
        print("    Pass --assets_jsonl campaign_asset.jsonl (best) or --assets_table your_labelled_file.xlsx to fix this.\n")

    df = pd.DataFrame(rows)
    id_cols = ["asset_id", "bank", "url", "language", "id_source", "match_score"]
    front = [c for c in id_cols if c in df.columns]
    df = df[front + [c for c in df.columns if c not in front]]
    df.to_csv(out_path, index=False)
    print(f"\nWrote {out_path} ({len(df)} rows)")

    if args.download_images:
        img_out = out_path.with_name(out_path.stem + "_images.csv")
        img_df = pd.DataFrame(img_rows)
        img_front = [c for c in ["asset_id", "url", "src"] if c in img_df.columns]
        img_df = img_df[img_front + [c for c in img_df.columns if c not in img_front]]
        img_df.to_csv(img_out, index=False)
        print(f"Wrote {img_out} ({len(img_rows)} rows)")


if __name__ == "__main__":
    main()