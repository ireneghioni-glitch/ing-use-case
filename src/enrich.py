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



def derive_role_from_url(url: str) -> str:
    u = url.lower()
    if "comparatif" in u or "compare" in u or "vergel" in u:
        return "comparison"
    if "ouvrir" in u or "open" in u or "how-to" in u:
        return "how_to"
    if "tarif" in u or "prix" in u or "kosten" in u or "fee" in u:
        return "pricing"
    if "condition" in u or "voorwaarden" in u:
        return "conditions"
    return "product_or_landing"  # default