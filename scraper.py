"""
Marketing Spy — Classic scraper (no LLM)
==========================================
Deterministic Playwright scraping of every URL in candidate_urls.py.
For each page: navigate (robots.txt enforced), dismiss cookie banner,
wait for real content to render, save the raw HTML and a full-page
screenshot, and emit one AssetMetadata-conformant record.

Output: campaign_asset.jsonl — one JSON record per page (validated against
AssetMetadata). Raw HTML/screenshots live under RAW_DIR/SCREENSHOTS_DIR;
this file stores only the metadata + paths, per AssetMetadata's design —
text CLEANING/extraction from raw_html_path is a separate downstream step
(the "Data Cleaning" stage), not done here anymore.

ASSUMPTION: AssetMetadata is imported from src.models — adjust the import
below if it actually lives elsewhere (e.g. src.schemas) in your project.
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from robots_checker import ROBOTS_TXT, build_checkers, is_allowed
from candidate_urls import CANDIDATE_URLS

# import centralized Paths from src/config.py
PROJ_ROOT = Path(__file__).resolve().parent.parent
if str(PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJ_ROOT))

from src.config import (
    RAW_DIR,
    SCREENSHOTS_DIR,
    ASSETS_PATH,
    LOG_DIR,
)

# ASSUMPTION: adjust this import path if AssetMetadata lives elsewhere.
from src.schema import AssetMetadata

CHECKERS = build_checkers(ROBOTS_TXT)

# ---------------------------------------------------------------------------
# Bank metadata: display name, bank_type (for AssetMetadata), and the set of
# domains each bank's URLs may legitimately come from. KBC now spans two
# domains (kbcbrussels.be + kbc.be) — a single allowed_domain string per
# bank is no longer enough, hence the list.
# ---------------------------------------------------------------------------

BANK_INFO = {
    "ing":        {"display": "ING",                "bank_type": "traditional", "domains": ["ing.be"]},
    "ing_adult":  {"display": "ING",                "bank_type": "traditional", "domains": ["ing.be"]},
    "bnp_fortis": {"display": "BNP Paribas Fortis",  "bank_type": "traditional", "domains": ["bnpparibasfortis.be"]},
    "kbc":        {"display": "KBC",                "bank_type": "traditional", "domains": ["kbcbrussels.be", "kbc.be"]},
    "belfius":    {"display": "Belfius",             "bank_type": "traditional", "domains": ["belfius.be"]},
    "revolut":    {"display": "Revolut",             "bank_type": "challenger",  "domains": ["revolut.com"]},
    "hello_bank": {"display": "Hello bank!",         "bank_type": "challenger",  "domains": ["hellobank.be"]},
    "argenta":    {"display": "Argenta",             "bank_type": "traditional", "domains": ["argenta.be"]},
    "n26":        {"display": "N26",                 "bank_type": "challenger",  "domains": ["n26.com"]},
    "beobank":    {"display": "Beobank",              "bank_type": "traditional", "domains": ["beobank.be"]},
}

# Default audience_label per bank. NOTE: several banks' candidate lists mix
# youth-specific AND general/adult comparator pages under one key (see the
# "[NAV] general ... — adult equivalent" notes in candidate_urls.py for
# hello_bank, n26, beobank, kbc). This per-bank default is an approximation,
# not a per-URL ground truth — flagged here rather than silently assumed
# accurate. Only ing_adult is reliably "general_adult" end-to-end.
DEFAULT_AUDIENCE_LABEL = {
    "ing_adult": "general_adult",
}

# Maps a URL's actual domain to the robots-checker key that has that
# domain's robots.txt loaded (see robots_checker.py's ROBOTS_TXT dict,
# still keyed by the original 5 banks). Domains not listed here have NO
# robots.txt loaded — scraping them is refused rather than guessed at.
DOMAIN_TO_ROBOTS_KEY = {
    "ing.be": "ing",
    "bnpparibasfortis.be": "bnp_fortis",
    "kbcbrussels.be": "kbc",
    "belfius.be": "belfius",
    "revolut.com": "revolut",
    "n26.com": "n26",
    # NOT YET AVAILABLE — robots.txt content needed before these can be
    # scraped: kbc.be, hellobank.be, argenta.be, n26.com, beobank.be.
    # Paste each site's robots.txt (same as done for the first 5 banks)
    # and add an entry to robots_checker.py's ROBOTS_TXT dict + here.
}

BANK_DOMAINS = {bank: info["domains"] for bank, info in BANK_INFO.items()}

# create dirs if they don't exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Aliasing to keep the rest of the code unchanged
SCREENSHOT_DIR = SCREENSHOTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"scraper_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("scraper")


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return text.strip("-")[:80]


def detect_language(url: str) -> str:
    lower = url.lower()
    for code in ("fr-be", "en-be", "nl-be"):
        if code in lower:
            return code.split("-")[0]
    for seg, lang in (("/fr/", "fr"), ("/nl/", "nl"), ("/en/", "en")):
        if seg in lower:
            return lang
    return "fr"  # default — most of this corpus is French


class BrowserSession:
    def __init__(self, bank: str, allowed_domains: list[str]):
        self.bank = bank
        self.allowed_domains = allowed_domains
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 900},
            locale="fr-BE",
        )
        self._context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self._page = self._context.new_page()

    def close(self):
        self._browser.close()
        self._pw.stop()

    def _wait_for_real_content(self, url: str):
        """
        Wait for substantial text, not just the nav bar. Uses the same
        shadow-DOM-aware deep text collector as get_text() (see there for
        why) rather than native innerText, which this site's shadow DOM
        structure prevents from reflecting real content — using innerText
        here just wasted ~20s per page always timing out despite content
        being present and readable via the JS walker.
        """
        js_condition = """
            () => {
                function collect(node) {
                    let out = '';
                    if (node.nodeType === Node.TEXT_NODE) return node.textContent;
                    if (node.shadowRoot) {
                        for (const c of node.shadowRoot.childNodes) out += collect(c);
                    }
                    if (node.childNodes) {
                        for (const c of node.childNodes) out += collect(c);
                    }
                    return out;
                }
                return collect(document.body).trim().length > 400;
            }
        """
        for attempt, timeout in enumerate([10000, 6000], start=1):
            try:
                self._page.wait_for_function(js_condition, timeout=timeout)
                return
            except Exception:
                if attempt == 1:
                    try:
                        self._page.mouse.wheel(0, 1500)
                    except Exception:
                        pass
                    continue
                logger.warning(f"Content wait timed out (both attempts) for {url}")

    def navigate(self, url: str) -> dict:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return {"ok": False, "reason": f"URL rejected (scheme check): {url}"}
        if not any(d in parsed.netloc for d in self.allowed_domains):
            return {"ok": False, "reason": f"URL rejected (domain not in {self.allowed_domains}): {url}"}

        robots_key = DOMAIN_TO_ROBOTS_KEY.get(parsed.netloc.lstrip("www."))
        if robots_key is None:
            # also try with a plain netloc match (covers "www." prefix cases)
            for domain, key in DOMAIN_TO_ROBOTS_KEY.items():
                if domain in parsed.netloc:
                    robots_key = key
                    break
        if robots_key is None:
            return {
                "ok": False,
                "reason": (
                    f"No robots.txt loaded for domain '{parsed.netloc}' — "
                    "refusing to scrape rather than guessing. Add its "
                    "robots.txt to robots_checker.py + DOMAIN_TO_ROBOTS_KEY first."
                ),
            }
        if not is_allowed(CHECKERS, robots_key, url):
            return {"ok": False, "reason": f"Disallowed by robots.txt: {url}"}

        try:
            # Reset to a blank page first — guards against SPA-style client-side
            # routing where changing the URL doesn't fully replace the previous
            # page's rendered content before we capture it (confirmed happening
            # for KBC: two different URLs produced identical screenshots).
            self._page.goto("about:blank", timeout=5000)

            self._page.goto(url, wait_until="load", timeout=20000)

            # Verify navigation actually landed on the target URL (allow for
            # trailing-slash / query-string differences); retry once if not.
            if not self._page.url.rstrip("/").endswith(urlparse(url).path.rstrip("/")):
                logger.warning(f"URL mismatch after goto ({self._page.url}) — retrying once for {url}")
                self._page.goto("about:blank", timeout=5000)
                self._page.goto(url, wait_until="load", timeout=20000)

            self._page.wait_for_timeout(1500)  # let banner scripts inject first
            self._dismiss_cookie_banner(url)
            self._wait_for_real_content(url)
            self._page.wait_for_timeout(500)

            return {"ok": True}
        except Exception as e:
            return {"ok": False, "reason": str(e)}

    def _dismiss_cookie_banner(self, url: str):
        """
        Try to close the cookie-consent banner, checking BOTH the main page
        and every iframe — several consent platforms (Cookiebot, Quantcast,
        Google Funding Choices) render their button inside an iframe, which
        a plain page.locator() call never reaches. Logs whether anything
        was actually found/clicked, for diagnosis.
        """
        selectors = [
            "#onetrust-accept-btn-handler",
            "button[aria-label*='Accepter' i]",
            "button:has-text('Accepter')",
            "button:has-text('Tout accepter')",
            "button:has-text('J\\'accepte')",
            "button:has-text('Aanvaarden')",
            "button:has-text('Alles accepteren')",
            "#didomi-notice-agree-button",
            "button[id*='cookie' i][id*='accept' i]",
            "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            "#CybotCookiebotDialogBodyButtonAccept",
            ".qc-cmp2-summary-buttons button[mode='primary']",
            "button[data-testid*='accept' i]",
            "[class*='consent' i] button[class*='accept' i]",
            # ING uses custom web components (ing-button, ing-cookie-dialog)
            # for its cookie preference dialog, likely in shadow DOM.
            # Playwright's CSS/:has-text locators pierce open shadow DOM
            # automatically (unlike XPath, which does not) — target the
            # custom element itself, not an inner <button>.
            "ing-button:has-text('Accepter')",
            "ing-button:has-text('Accepter tout')",
            "ing-button:has-text(\"J'accepte\")",
            "ing-feat-cookie-preference-be ing-button",
            "ing-form ing-button",
        ]

        frames_to_check = [self._page.main_frame] + [
            f for f in self._page.frames if f != self._page.main_frame
        ]

        # Try accessibility-tree based matching FIRST — it uses a different
        # code path than :has-text()/innerText and tends to work correctly
        # across shadow DOM even when text-content matching doesn't.
        import re as _re
        try:
            btn = self._page.get_by_role("button", name=_re.compile("accepter", _re.I)).first
            if btn.is_visible(timeout=2000):
                btn.click(timeout=1000)
                logger.info(f"Dismissed cookie banner via get_by_role(accepter) on {url}")
                self._page.wait_for_timeout(1000)
                return True
        except Exception:
            pass

        for frame in frames_to_check:
            for sel in selectors:
                try:
                    btn = frame.locator(sel).first
                    if btn.is_visible(timeout=800):
                        btn.click(timeout=800)
                        logger.info(f"Dismissed cookie banner via '{sel}' (frame: {frame.url[:60]}) on {url}")
                        self._page.wait_for_timeout(1000)
                        return True
                except Exception:
                    continue

        logger.info(f"No cookie banner matched/dismissed for {url} (may not have one, or uses an unlisted selector)")
        return False

    def get_html(self) -> str:
        """Raw HTML of the current page, saved to disk so it can be cleaned
        / re-extracted later without re-scraping (the AssetMetadata design:
        raw_html_path is the artifact, not inline text)."""
        return self._page.content()

    def screenshot(self, out_path: Path):
        self._page.screenshot(path=str(out_path), full_page=True)


def scrape_bank(bank: str, entries: list[tuple[str, str]]):
    info = BANK_INFO[bank]
    logger.info(f"=== Scraping {bank} ({info['display']}) — {len(entries)} pages ===")
    session = BrowserSession(bank=bank, allowed_domains=info["domains"])
    try:
        with ASSETS_PATH.open("a", encoding="utf-8") as out:
            for i, (url, note) in enumerate(entries, start=1):
                logger.info(f"[{i}/{len(entries)}] {url}")
                result = session.navigate(url)
                if not result["ok"]:
                    logger.warning(f"Skipped: {result['reason']}")
                    continue

                safe_name = slugify(url.rstrip("/").split("/")[-1] or "page")
                asset_id = f"{bank}__{safe_name}"

                html = session.get_html()
                raw_html_path = RAW_DIR / f"{bank}_{safe_name}.html"
                raw_html_path.write_text(html, encoding="utf-8")

                screenshot_path = SCREENSHOT_DIR / f"{bank}_{safe_name}.png"
                session.screenshot(screenshot_path)

                asset = AssetMetadata(
                    asset_id=asset_id,
                    bank=info["display"],
                    bank_type=info["bank_type"],
                    channel="website",
                    audience_label=DEFAULT_AUDIENCE_LABEL.get(bank, "youth_18_25"),
                    url=url,
                    language=detect_language(url),
                    collected_at=datetime.now(timezone.utc).isoformat(),
                    raw_html_path=str(raw_html_path),
                    screenshot_path=str(screenshot_path),
                )

                out.write(asset.model_dump_json() + "\n")
                logger.info(f"Saved {asset_id} (html: {raw_html_path.name}, screenshot: {screenshot_path.name})")
    finally:
        session.close()


if __name__ == "__main__":
    # Optional: pass bank names as CLI args to scrape only those, e.g.:
    #   python scraper.py ing
    only = set(sys.argv[1:]) or None

    for bank in BANK_INFO:
        if only and bank not in only:
            continue
        if bank == "bnp_fortis":
            logger.info("Skipping bnp_fortis — blocked by Akamai Bot Manager, collected manually.")
            continue
        entries = CANDIDATE_URLS.get(bank, [])
        if not entries:
            logger.info(f"Skipping {bank} — no URLs configured")
            continue
        scrape_bank(bank, entries)

    print(f"\nDone. Assets: {ASSETS_PATH}  Raw HTML: {RAW_DIR}/  Screenshots: {SCREENSHOT_DIR}/  Logs: {LOG_DIR}/")