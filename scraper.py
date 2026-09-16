"""
Marketing Spy — Classic scraper (no LLM)
==========================================
Deterministic Playwright scraping of every URL in candidate_urls.py.
For each page: navigate (robots.txt enforced), dismiss cookie banner,
wait for real content to render, extract text (main doc + iframes),
save a full-page screenshot.

Output: campaign_asset.jsonl — one JSON record per page, raw/unstructured.
This is the "campaign_asset" table from the original architecture —
kept separate from feature extraction so extraction prompts can be
re-run later without re-scraping.
"""

import json
import logging
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

CHECKERS = build_checkers(ROBOTS_TXT)

BANK_DOMAINS = {
    "ing": "ing.be",
    "ing_adult": "ing.be",  # ING's general/adult equivalents, for the
                             # within-ING youth-vs-adult comparison
    # bnp_fortis intentionally excluded — blocked by Akamai Bot Manager
    # (confirmed via AK-Ref-Id in the served "maintenance" page). Collected
    # manually instead, see manual_collection_template.py.
    "kbc": "kbcbrussels.be",
    "belfius": "belfius.be",
    "revolut": "revolut.com",
}

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


class BrowserSession:
    def __init__(self, bank: str, allowed_domain: str):
        self.bank = bank
        self.allowed_domain = allowed_domain
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
        if parsed.scheme not in ("http", "https") or self.allowed_domain not in parsed.netloc:
            return {"ok": False, "reason": f"URL rejected (scheme/domain check): {url}"}
        # ing_adult shares ing.be's robots.txt — no separate entry needed.
        robots_bank = "ing" if self.bank == "ing_adult" else self.bank
        if not is_allowed(CHECKERS, robots_bank, url):
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

    def get_text(self) -> str:
        """
        Deep text extraction that manually walks the DOM + open shadow
        roots via JS and concatenates raw textContent. Needed because
        Playwright's inner_text()/native innerText do not reliably surface
        text rendered inside open shadow roots on this site (confirmed via
        diagnostic — shadow roots are open and JS-walkable, but innerText
        still returns empty).
        """
        chunks = []
        for frame in [self._page.main_frame] + [
            f for f in self._page.frames if f != self._page.main_frame
        ]:
            try:
                t = frame.evaluate("""
                    () => {
                        function collect(node) {
                            let out = '';
                            if (node.nodeType === Node.TEXT_NODE) {
                                return node.textContent + ' ';
                            }
                            if (node.shadowRoot) {
                                for (const child of node.shadowRoot.childNodes) {
                                    out += collect(child);
                                }
                            }
                            if (node.childNodes) {
                                for (const child of node.childNodes) {
                                    out += collect(child);
                                }
                            }
                            return out;
                        }
                        return collect(document.body).replace(/\\s+/g, ' ').trim();
                    }
                """)
                if t and t.strip():
                    chunks.append(t)
            except Exception:
                continue
        return "\n".join(chunks)

    def screenshot(self, out_path: Path):
        self._page.screenshot(path=str(out_path), full_page=True)


def scrape_bank(bank: str, domain: str, entries: list[tuple[str, str]]):
    logger.info(f"=== Scraping {bank} — {len(entries)} pages ===")
    session = BrowserSession(bank=bank, allowed_domain=domain)
    try:
        with ASSETS_PATH.open("a", encoding="utf-8") as out:
            for i, (url, note) in enumerate(entries, start=1):
                logger.info(f"[{i}/{len(entries)}] {url}")
                result = session.navigate(url)
                if not result["ok"]:
                    logger.warning(f"Skipped: {result['reason']}")
                    continue

                text = session.get_text()
                safe_name = url.rstrip("/").split("/")[-1][:60] or "page"
                screenshot_path = SCREENSHOT_DIR / f"{bank}_{safe_name}.png"
                session.screenshot(screenshot_path)

                record = {
                    "bank": bank,
                    "url": url,
                    "note": note,
                    "text": text,
                    "screenshot_path": str(screenshot_path),
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                logger.info(f"Saved ({len(text)} chars text, screenshot: {screenshot_path.name})")
    finally:
        session.close()


if __name__ == "__main__":
    import sys

    # Optional: pass bank names as CLI args to scrape only those, e.g.:
    #   python scraper.py ing
    only = set(sys.argv[1:]) or None

    for bank, domain in BANK_DOMAINS.items():
        if only and bank not in only:
            continue
        entries = CANDIDATE_URLS.get(bank, [])
        if not entries:
            logger.info(f"Skipping {bank} — no URLs configured")
            continue
        scrape_bank(bank, domain, entries)

    print(f"\nDone. Assets: {ASSETS_PATH}  Screenshots: {SCREENSHOT_DIR}/  Logs: {LOG_DIR}/")