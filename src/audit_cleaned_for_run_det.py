"""
audit_cleaned_for_run_det.py
============================
Audit the cleaned asset file produced by clean_html step.

Verifies that `data/processed/cleaned_assets.jsonl` has all the fields
required by `run_deterministic.py`, and reports distributions that help
spot problems before running the deterministic extraction.

Output: docs/cleaned_assets_audit.md

Run: python -m src.audit_cleaned
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from src.config import PROCESSED_DIR, DOCS_DIR


INPUT_PATH = PROCESSED_DIR / "cleaned_assets.jsonl"
REPORT_PATH = DOCS_DIR / "cleaned_assets_audit.md"

# Fields that run_deterministic.py needs. If any of these is missing,
# the deterministic extraction will silently produce wrong values.
REQUIRED_FIELDS = [
    "asset_id",
    "bank",
    "audience_label",
    "language",
    "text",
    "cleaning_status",
]

EXPECTED_LANGUAGES = {"fr", "nl", "en"}
EXPECTED_STATUSES = {"ok", "insufficient_text"}
MIN_WORDS_THRESHOLD = 50


def load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    """Load JSONL records and collect parse errors."""
    records: list[dict] = []
    errors: list[str] = []

    if not path.is_file():
        return [], [f"File does not exist: {path}"]

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_number}: invalid JSON ({exc})")
                continue
            if not isinstance(value, dict):
                errors.append(f"Line {line_number}: not a JSON object")
                continue
            records.append(value)

    return records, errors


def check_required_fields(records: list[dict]) -> dict[str, list[int]]:
    """Return, per required field, the indices of records that are missing it."""
    missing: dict[str, list[int]] = {field: [] for field in REQUIRED_FIELDS}

    for i, record in enumerate(records):
        for field in REQUIRED_FIELDS:
            if field not in record or record[field] in (None, ""):
                missing[field].append(i)

    return missing


def check_duplicates(records: list[dict], field: str) -> dict[str, int]:
    """Return duplicated non-empty values for a field, with their counts."""
    counter = Counter(
        str(r.get(field)) for r in records if r.get(field)
    )
    return {value: count for value, count in counter.items() if count > 1}


def count_distribution(records: list[dict], field: str) -> Counter:
    """Return value counts for a field (missing values counted as MISSING)."""
    return Counter(str(r.get(field) or "MISSING") for r in records)


def count_short_texts(records: list[dict]) -> list[tuple[str, int]]:
    """Return (asset_id, word_count) for records with too few words."""
    short: list[tuple[str, int]] = []
    for r in records:
        text = r.get("text") or ""
        wc = len(text.split())
        if wc < MIN_WORDS_THRESHOLD:
            short.append((r.get("asset_id", "<no id>"), wc))
    return short


def markdown_table(counter: Counter, label: str) -> list[str]:
    lines = [f"| {label} | Records |", "|---|---:|"]
    lines.extend(
        f"| {value} | {count} |" for value, count in sorted(counter.items())
    )
    return lines


def write_report(
    records: list[dict],
    parse_errors: list[str],
    missing: dict[str, list[int]],
    statuses: Counter,
    languages: Counter,
    banks: Counter,
    duplicate_ids: dict[str, int],
    short_texts: list[tuple[str, int]],
) -> None:
    total = len(records)
    total_missing = sum(len(v) for v in missing.values())
    unexpected_langs = {
        lang for lang in languages if lang not in EXPECTED_LANGUAGES
    }
    unexpected_statuses = {
        status for status in statuses if status not in EXPECTED_STATUSES
    }

    critical = total_missing + len(parse_errors) + len(duplicate_ids)
    status = "FAIL" if critical else "PASS"

    lines: list[str] = [
        "# Cleaned Assets Audit",
        "",
        f"**Input:** `{INPUT_PATH.as_posix()}`  ",
        f"**Records:** {total}  ",
        f"**Status:** **{status}**  ",
        f"**Critical findings:** {critical}",
        "",
    ]

    # --- 1. Required fields ---
    lines.append("## 1. Required fields\n")
    lines.append("| Field | Missing / Total |")
    lines.append("|---|---:|")
    for field, indices in missing.items():
        marker = " ❌" if indices else ""
        lines.append(f"| `{field}` | {len(indices)} / {total}{marker} |")

    # --- 2. Parse errors ---
    lines.append("\n## 2. JSON parsing\n")
    if parse_errors:
        lines.extend(f"- {e}" for e in parse_errors)
    else:
        lines.append("No parse errors.")

    # --- 3. Cleaning status distribution ---
    lines.append("\n## 3. Cleaning status\n")
    lines.extend(markdown_table(statuses, "cleaning_status"))
    if unexpected_statuses:
        lines.append(
            f"\n⚠️ Unexpected statuses: {', '.join(sorted(unexpected_statuses))}"
        )

    # --- 4. Language distribution ---
    lines.append("\n## 4. Language\n")
    lines.extend(markdown_table(languages, "language"))
    if unexpected_langs:
        lines.append(
            f"\n⚠️ Unexpected languages: {', '.join(sorted(unexpected_langs))}"
        )

    # --- 5. Bank distribution ---
    lines.append("\n## 5. Bank\n")
    lines.extend(markdown_table(banks, "bank"))

    # --- 6. Duplicate asset_id ---
    lines.append("\n## 6. Duplicate asset_id\n")
    if duplicate_ids:
        for value, count in sorted(duplicate_ids.items()):
            lines.append(f"- `{value}` appears {count} times.")
    else:
        lines.append("No duplicate asset_id values.")

    # --- 7. Short texts ---
    lines.append(f"\n## 7. Short texts (< {MIN_WORDS_THRESHOLD} words)\n")
    if short_texts:
        lines.append("| asset_id | word_count |")
        lines.append("|---|---:|")
        for asset_id, wc in short_texts:
            lines.append(f"| `{asset_id}` | {wc} |")
    else:
        lines.append("No short texts.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print(f"Auditing cleaned assets: {INPUT_PATH}\n")

    records, parse_errors = load_jsonl(INPUT_PATH)

    if not records:
        print("No records loaded.")
        for e in parse_errors:
            print(f"  - {e}")
        return

    print(f"Records loaded: {len(records)}")

    missing = check_required_fields(records)
    statuses = count_distribution(records, "cleaning_status")
    languages = count_distribution(records, "language")
    banks = count_distribution(records, "bank")
    duplicate_ids = check_duplicates(records, "asset_id")
    short_texts = count_short_texts(records)

    print("\nMissing required fields:")
    for field, indices in missing.items():
        print(f"  {field}: {len(indices)}/{len(records)}")

    print("\nCleaning status:")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")

    print("\nLanguage:")
    for lang, count in sorted(languages.items()):
        print(f"  {lang}: {count}")

    print("\nBank:")
    for bank, count in sorted(banks.items()):
        print(f"  {bank}: {count}")

    if duplicate_ids:
        print(f"\nDuplicate asset_id: {len(duplicate_ids)} group(s)")
    if short_texts:
        print(f"\nShort texts: {len(short_texts)} record(s)")

    write_report(
        records=records,
        parse_errors=parse_errors,
        missing=missing,
        statuses=statuses,
        languages=languages,
        banks=banks,
        duplicate_ids=duplicate_ids,
        short_texts=short_texts,
    )
    print(f"\nReport written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()