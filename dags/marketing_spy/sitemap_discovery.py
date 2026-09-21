from __future__ import annotations

import requests
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

try:
    import brotli  # noqa: F401  (presence alone lets urllib3 auto-decode br)
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False


# Spoof a real browser to bypass Cloudflare/Akamai 403 blocks (Fixes Revolut)
REAL_BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 30

BROWSER_HEADERS = {
    "User-Agent": REAL_BROWSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    # Only advertise Brotli support if we can actually decode it locally.
    # Without the `brotli`/`brotlicffi` package, urllib3 can't inflate a
    # br-encoded response, and requests silently hands back the raw
    # compressed bytes as "text" -- which looks like corrupt/binary garbage
    # and gets misread as a malformed-XML error (bit us on n26.com).
    "Accept-Encoding": "gzip, deflate, br" if HAS_BROTLI else "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# One session per process so cookies/CF clearance tokens persist across
# the robots.txt -> homepage -> sitemap hops, the same way a browser tab would.
_session = requests.Session()
_session.headers.update(BROWSER_HEADERS)


def _check_brotli_response(headers) -> None:
    """
    If the server sent Content-Encoding: br but we can't decode Brotli
    locally, requests/urllib3 silently hands back raw compressed bytes as
    "text" -- which reads as binary garbage and gets misdiagnosed as a
    malformed-XML/HTML parse error further downstream. Fail loudly here
    instead, with an actionable fix, rather than letting it masquerade as
    a parse error several functions away from the real cause.
    """
    content_encoding = (headers.get("Content-Encoding") or "").lower()
    if "br" in content_encoding.split(",") and not HAS_BROTLI:
        raise RuntimeError(
            "Server responded with Content-Encoding: br (Brotli) but no Brotli "
            "decoder is installed, so the response can't be read as text. "
            "Fix: pip install brotli"
        )


def _get_via_curl_cffi(url: str) -> str:
    """
    Fallback used when plain `requests` gets a 403. requests/urllib3's TLS
    handshake (JA3 fingerprint) is trivially distinguishable from a real
    Chrome browser, which is what Cloudflare/Akamai often key on -- no
    amount of header spoofing fixes that. curl_cffi impersonates Chrome's
    actual TLS fingerprint, which is what actually gets past these WAFs.
    """
    if not HAS_CURL_CFFI:
        raise RuntimeError(
            "curl_cffi not installed. Run: pip install curl_cffi --break-system-packages"
        )
    resp = curl_requests.get(
        url,
        headers=BROWSER_HEADERS,
        timeout=TIMEOUT,
        impersonate="chrome120",
    )
    resp.raise_for_status()
    return resp.text


def get_page(url: str, referer: str | None = None, debug: bool = False) -> str:
    """
    Download a text page with desktop browser headers. Tries a plain
    requests.Session first (fast, no extra deps); if that comes back 403,
    retries with curl_cffi's TLS impersonation, which is what's actually
    needed for Cloudflare-protected sites like Revolut.

    debug=True prints the raw Content-Type/Content-Encoding/length actually
    received, so a mis-decoded response can be diagnosed from real data
    instead of guessing at what compression/format is involved.

    NOTE: for XML, prefer get_page_bytes() instead -- see its docstring for
    why (hello_bank's mis-decoded BOM bug).
    """
    headers = {}
    if referer:
        headers["Referer"] = referer

    try:
        response = _session.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        _check_brotli_response(response.headers)
        if debug:
            print(
                f"[debug] {url} -> status={response.status_code} "
                f"content-type={response.headers.get('Content-Type')!r} "
                f"content-encoding={response.headers.get('Content-Encoding')!r} "
                f"raw_bytes={len(response.content)} "
                f"apparent_encoding={response.apparent_encoding!r} "
                f"first_20_raw_bytes={response.content[:20]!r}"
            )
        return response.text
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 403:
            print(f"403 via plain requests for {url}; retrying with TLS-impersonating client...")
            return _get_via_curl_cffi(url)
        raise


def get_page_bytes(url: str, referer: str | None = None) -> bytes:
    """
    Like get_page(), but returns raw bytes instead of decoded text.

    Use this for XML. `requests` decodes response.text using the charset it
    thinks applies -- and per HTTP spec, when a server sends a Content-Type
    like "text/xml" with NO charset parameter (hello_bank does this),
    requests defaults response.encoding to ISO-8859-1, even if the actual
    bytes are UTF-8. That mis-decodes a leading UTF-8 BOM into three garbage
    characters ("ï»¿") and ElementTree then fails to parse at position 0.

    ElementTree, given raw bytes instead of a pre-decoded str, reads the XML
    declaration/BOM itself and gets the encoding right, so this sidesteps
    the whole problem rather than trying to out-guess `requests`.
    """
    headers = {}
    if referer:
        headers["Referer"] = referer

    try:
        response = _session.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        _check_brotli_response(response.headers)
        return response.content
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 403:
            print(f"403 via plain requests for {url}; retrying with TLS-impersonating client...")
            if not HAS_CURL_CFFI:
                raise RuntimeError(
                    "curl_cffi not installed. Run: pip install curl_cffi --break-system-packages"
                )
            resp = curl_requests.get(
                url, headers=BROWSER_HEADERS, timeout=TIMEOUT, impersonate="chrome120"
            )
            resp.raise_for_status()
            return resp.content
        raise


def get_sitemaps_from_robots(domain: str) -> list[str]:
    """
    Read robots.txt and find Sitemap: entries.
    If blocked by firewalls (like Revolut), gracefully drops back to standard defaults.
    """
    robots_url = urljoin(
        domain.rstrip("/") + "/",
        "robots.txt",
    )

    print(f"Reading robots.txt: {robots_url}")

    sitemap_urls = []
    try:
        # Hit the homepage first so any CF clearance cookie is set before
        # we go after robots.txt / the sitemap, mimicking real navigation.
        # Broad except here on purpose: this is a best-effort warm-up, and
        # it must never take down the caller (e.g. a missing curl_cffi
        # dependency raises RuntimeError, not RequestException).
        try:
            get_page(domain)
        except Exception as warm_up_exc:
            print(f"Homepage warm-up request failed (non-fatal): {warm_up_exc}")

        robots_text = get_page(robots_url, referer=domain)
        for line in robots_text.splitlines():
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                if sitemap_url:
                    sitemap_urls.append(sitemap_url)
    except Exception as exc:
        # Broad on purpose: this whole function is meant to be best-effort
        # with a fallback to default sitemap paths (see docstring). Plain
        # requests.RequestException isn't broad enough -- when the 403
        # fallback retries via curl_cffi and curl_cffi *also* gets blocked,
        # curl_cffi raises its own exception class, not a requests one, and
        # would otherwise escape this handler and crash the whole DAG task.
        print(f"Could not read robots.txt for {domain} due to network/firewall blocks: {exc}")

    # CRUCIAL FIX: If robots.txt is blocked or empty, force-inject known sitemap defaults
    if not sitemap_urls:
        if "revolut.com" in domain:
            print("Injecting explicit known sitemap index path for Revolut profile rules matrix.")
            sitemap_urls.append("https://www.revolut.com/sitemap-index.xml")
        else:
            sitemap_urls.append(urljoin(domain.rstrip("/") + "/", "sitemap.xml"))

    return sitemap_urls


def scrape_html_links_fallback(domain: str) -> list[str]:
    """
    Bypass strategy when sitemaps return corrupted structures or HTML content.
    Extracts navigation anchor paths directly from the website landing frame.
    """
    print(f"Executing deep HTML crawling fallback for domain target: {domain}")
    urls = []
    try:
        from bs4 import BeautifulSoup
        html_text = get_page(domain)
        soup = BeautifulSoup(html_text, 'html.parser')

        for anchor in soup.find_all('a', href=True):
            href = anchor['href'].strip()
            # Convert relative endpoints into absolute target URLs
            if href.startswith('/'):
                href = urljoin(domain, href)

            # Ensure we only track URLs belonging to the specific bank domain
            if urlparse(domain).netloc in urlparse(href).netloc and href not in urls:
                urls.append(href)
    except Exception as e:
        print(f"HTML crawler extraction fallback failed for {domain}: {e}")

    if not urls:
        print(
            f"No anchor links found in raw HTML for {domain}. "
            f"This usually means the site is a JS-rendered SPA (React/Vue/etc.) "
            f"and links don't exist in the initial HTML payload -- a plain "
            f"requests-based fetch can't help here; a headless browser "
            f"(Playwright/Selenium) would be needed to render the page first."
        )

    return urls


def parse_sitemap(sitemap_url: str) -> tuple[list[str], list[str]]:
    """
    Parse standard XML structures. Falls back to pure HTML anchor scraping
    if the endpoint serves hidden client text pages or malformed tokens.
    """
    print(f"Reading sitemap: {sitemap_url}")

    domain_root = f"{urlparse(sitemap_url).scheme}://{urlparse(sitemap_url).netloc}"
    xml_bytes = get_page_bytes(sitemap_url, referer=domain_root)

    # Decode leniently just for the heuristic text checks below (HTML/empty
    # detection). ET.fromstring() further down uses the raw bytes directly
    # and does its own correct encoding detection -- see get_page_bytes().
    xml_text = xml_bytes.decode("utf-8-sig", errors="replace")

    # Fixes Hello Bank: Check if response text is actually HTML instead of XML
    if xml_text.strip().lower().startswith("<!doc") or "<html" in xml_text.lower():
        print(f"Warning: Destination {sitemap_url} served an HTML layout string, not an XML schema.")
        fallback_urls = scrape_html_links_fallback(domain_root)
        return fallback_urls, []

    if not xml_text.strip():
        print(f"Warning: {sitemap_url} returned an empty body (likely a soft bot-block, e.g. 200 with no content).")
        fallback_urls = scrape_html_links_fallback(domain_root)
        return fallback_urls, []

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as parse_err:
        # Show what we actually got so a truly novel response shape (JSON
        # error page, WAF interstitial, gzip'd bytes read as text, etc.)
        # is visible in the logs instead of a bare parse error.
        preview = xml_text.strip()[:300].replace("\n", " ")
        print(f"XML layout token breakdown on file parse: {parse_err}. Response preview: {preview!r}")
        print("Redirecting to HTML extractor fallback.")
        fallback_urls = scrape_html_links_fallback(domain_root)
        return fallback_urls, []

    root_type = root.tag.split("}")[-1]
    urls = []
    child_sitemaps = []
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    if root_type == "urlset":
        for loc in root.findall(".//sm:url/sm:loc", namespace):
            if loc.text:
                urls.append(loc.text.strip())
    elif root_type == "sitemapindex":
        for loc in root.findall(".//sm:sitemap/sm:loc", namespace):
            if loc.text:
                child_sitemaps.append(loc.text.strip())
    else:
        print(f"Unknown sitemap token header type: {root_type}. Initializing scraping fallback loop.")
        return scrape_html_links_fallback(domain_root), []

    return urls, child_sitemaps


def discover_all_urls(sitemap_urls: list[str]) -> list[str]:
    """
    Recursively process sitemap indexes.
    """
    urls = set()
    queue = list(sitemap_urls)
    processed_sitemaps = set()

    while queue:
        sitemap_url = queue.pop(0)
        if sitemap_url in processed_sitemaps:
            continue

        processed_sitemaps.add(sitemap_url)

        try:
            found_urls, child_sitemaps = parse_sitemap(sitemap_url)
            urls.update(found_urls)
            queue.extend(child_sitemaps)
        except Exception as exc:
            print(f"Error reading {sitemap_url}: {exc}")

    return sorted(urls)


def discover_bank_urls(bank: str, domain: str) -> list[str]:
    print()
    print("=" * 60)
    print(f"Processing bank: {bank}")
    print(f"Domain: {domain}")
    print("=" * 60)

    try:
        sitemap_urls = get_sitemaps_from_robots(domain)

        print(f"Found {len(sitemap_urls)} sitemap(s)")
        for sitemap in sitemap_urls:
            print(f"  {sitemap}")

        if not sitemap_urls:
            print(f"No sitemap found for {bank}")
            return []

        urls = discover_all_urls(sitemap_urls)
        print(f"Found {len(urls)} URLs for {bank}")
        return urls
    except Exception as exc:
        # Isolate failures per bank: one site being fully blocked (WAF,
        # rate limit, outage, etc.) must not take down the whole DAG task
        # and prevent every other bank after it in the loop from running.
        print(f"Discovery failed entirely for {bank} ({domain}): {exc}")
        return []
