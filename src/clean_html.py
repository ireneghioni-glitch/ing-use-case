"""Convert raw campaign HTML into cleaned, analysis-ready text.

Input:
    data/processed/asset_manifest.jsonl

Output:
    data/processed/cleaned_assets.jsonl

Run:
    python -m src.clean_html
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from src.config import PROCESSED_DIR, PROJ_ROOT


INPUT_PATH = PROCESSED_DIR / "asset_manifest.jsonl"
OUTPUT_PATH = PROCESSED_DIR / "cleaned_assets.jsonl"

CLEANING_VERSION = "1.0"
MINIMUM_WORDS = 80

REMOVED_TAGS = {
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
}

STRUCTURAL_BOILERPLATE = {
    "header",
    "nav",
    "footer",
    "aside",
}

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSON objects from a JSONL file."""

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(
                    f"Line {line_number} is not a JSON object."
                )

            records.append(record)

    return records

def resolve_project_file(stored_path: str) -> Path:
    """Resolve a project-relative file without allowing path escape."""

    path = Path(stored_path)

    if path.is_absolute():
        raise ValueError(
            f"Expected a project-relative path, received: {stored_path}"
        )

    resolved = (PROJ_ROOT / path).resolve()

    try:
        resolved.relative_to(PROJ_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(
            f"Path escapes the repository: {stored_path}"
        ) from exc

    if not resolved.is_file():
        raise FileNotFoundError(
            f"File does not exist: {resolved}"
        )

    return resolved

def is_hidden(tag: Tag) -> bool:
    """Return True for explicitly hidden HTML elements."""

    if tag.has_attr("hidden"):
        return True

    if str(tag.get("aria-hidden", "")).lower() == "true":
        return True

    style = str(tag.get("style", "")).lower().replace(" ", "")

    return (
        "display:none" in style
        or "visibility:hidden" in style
    )


def is_cookie_or_consent_element(tag: Tag) -> bool:
    """Identify common cookie and consent containers."""

    identifiers: list[str] = []

    element_id = tag.get("id")
    if element_id:
        identifiers.append(str(element_id))

    classes = tag.get("class", [])
    if isinstance(classes, list):
        identifiers.extend(str(value) for value in classes)
    elif classes:
        identifiers.append(str(classes))

    combined = " ".join(identifiers).lower()

    markers = {
        "cookie",
        "consent",
        "onetrust",
        "privacy-banner",
        "cmp-banner",
    }

    return any(marker in combined for marker in markers)

def normalize_text(raw_text: str) -> str:
    """Normalize spacing while preserving meaningful text lines."""

    raw_text = html.unescape(raw_text)
    raw_text = unicodedata.normalize("NFC", raw_text)
    raw_text = raw_text.replace("\xa0", " ")

    cleaned_lines: list[str] = []
    previous_line: str | None = None

    for raw_line in raw_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()

        if not line:
            continue

        # Remove immediately repeated lines without deleting legitimate
        # repetitions elsewhere on the page.
        if previous_line and line.casefold() == previous_line.casefold():
            continue

        cleaned_lines.append(line)
        previous_line = line

    return "\n".join(cleaned_lines)

def extract_title(soup: BeautifulSoup) -> str | None:
    """Extract the HTML document title."""

    if not soup.title:
        return None

    title = normalize_text(soup.title.get_text(" ", strip=True))
    return title or None


def extract_meta_description(
    soup: BeautifulSoup,
) -> str | None:
    """Extract the page's meta description."""

    meta = soup.find(
        "meta",
        attrs={"name": re.compile(r"^description$", re.I)},
    )

    if not meta:
        return None

    description = normalize_text(str(meta.get("content", "")))
    return description or None


def select_content_root(soup: BeautifulSoup) -> Tag:
    """
    Select the most complete page-content container.

    A main element is used only when it contains substantial content.
    Otherwise, the cleaned body is safer than selecting the first article,
    because banking pages often use multiple article/section components.
    """

    body = soup.body

    if body is None:
        raise ValueError("The HTML document has no body element.")

    primary = (
        soup.find("main")
        or soup.find(attrs={"role": "main"})
    )

    if primary is None:
        return body

    primary_word_count = len(
        primary.get_text(" ", strip=True).split()
    )
    body_word_count = len(
        body.get_text(" ", strip=True).split()
    )

    primary_is_substantial = (
        primary_word_count >= MINIMUM_WORDS
        and primary_word_count >= body_word_count * 0.5
    )

    if primary_is_substantial:
        return primary

    return body

def clean_document(raw_html: str) -> dict[str, Any]:
    """Extract useful communication text from one HTML document."""

    soup = BeautifulSoup(raw_html, "html.parser")

    title = extract_title(soup)
    meta_description = extract_meta_description(soup)

    # Remove code and non-textual elements.
    for tag_name in REMOVED_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove structural site-wide elements.
    for tag_name in STRUCTURAL_BOILERPLATE:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove cookie dialogs, consent banners and hidden elements.
    for tag in list(soup.find_all(True)):
        if tag.parent is None:
            continue

        role = str(tag.get("role", "")).lower()

        if (
            role == "dialog"
            or is_hidden(tag)
            or is_cookie_or_consent_element(tag)
        ):
            tag.decompose()

    content_root = select_content_root(soup)

    headings = [
        normalize_text(heading.get_text(" ", strip=True))
        for heading in content_root.find_all(["h1", "h2", "h3"])
    ]
    headings = [heading for heading in headings if heading]

    text = normalize_text(
        content_root.get_text(separator="\n", strip=True)
    )

    word_count = len(text.split())

    status = (
        "ok"
        if word_count >= MINIMUM_WORDS
        else "insufficient_text"
    )

    return {
        "title": title,
        "meta_description": meta_description,
        "headings": headings,
        "text": text,
        "cleaned_word_count": word_count,
        "cleaned_char_count": len(text),
        "cleaning_status": status,
    }

def clean_record(record: dict[str, Any]) -> dict[str, Any]:
    """Clean the HTML connected to one manifest record."""

    html_path = resolve_project_file(record["raw_html_path"])
    raw_bytes = html_path.read_bytes()
    raw_html = raw_bytes.decode("utf-8")

    extracted = clean_document(raw_html)

    text_hash = hashlib.sha256(
        extracted["text"].encode("utf-8")
    ).hexdigest()

    return {
        **record,
        **extracted,
        "source_html_sha256": hashlib.sha256(
            raw_bytes
        ).hexdigest(),
        "text_sha256": text_hash,
        "cleaning_version": CLEANING_VERSION,
    }

def write_jsonl(
    records: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """Write JSONL atomically to avoid incomplete output."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_path.with_suffix(".jsonl.tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    temporary_path.replace(output_path)

def main() -> None:
    """Clean every asset in the normalized manifest."""

    print(f"Loading manifest: {INPUT_PATH}")

    records = load_jsonl(INPUT_PATH)

    if not records:
        raise RuntimeError("The asset manifest is empty.")

    cleaned_records: list[dict[str, Any]] = []

    for index, record in enumerate(records, start=1):
        asset_id = record.get("asset_id", "<missing asset_id>")

        try:
            cleaned = clean_record(record)
        except Exception as exc:
            raise RuntimeError(
                f"Cleaning failed for record {index} "
                f"({asset_id}): {exc}"
            ) from exc

        cleaned_records.append(cleaned)

    write_jsonl(cleaned_records, OUTPUT_PATH)

    statuses = Counter(
        record["cleaning_status"]
        for record in cleaned_records
    )

    print(f"Records processed: {len(cleaned_records)}")

    for status, count in sorted(statuses.items()):
        print(f"{status}: {count}")

    print(f"Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()