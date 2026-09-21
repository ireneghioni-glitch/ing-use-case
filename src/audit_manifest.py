"""Audit the normalized asset manifest without changing source data.

Input:
    data/processed/asset_manifest.jsonl

Output:
    docs/asset_manifest_audit.md

Run:
    python -m src.audit_manifest

This audit complements ``src.audit_jsonl``. Irene's original audit remains
unchanged and continues to describe the raw collection layer.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.config import DOCS_DIR, PROCESSED_DIR, PROJ_ROOT
from src.schema import AssetMetadata


MANIFEST_PATH = PROCESSED_DIR / "asset_manifest.jsonl"
REPORT_PATH = DOCS_DIR / "asset_manifest_audit.md"
MVP_BANKS = {"ING", "KBC", "Revolut"}
EXPECTED_LANGUAGES = {"en", "fr", "nl"}


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load JSON objects and return records plus parse errors."""
    records: list[dict[str, Any]] = []
    errors: list[str] = []

    if not path.is_file():
        return records, [f"Manifest does not exist: {path}"]

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_number}: invalid JSON ({exc})")
                continue

            if not isinstance(value, dict):
                errors.append(f"Line {line_number}: expected a JSON object")
                continue

            value["_line_number"] = line_number
            records.append(value)

    return records, errors


def validate_schema(records: list[dict[str, Any]]) -> list[str]:
    """Validate each manifest record against Irene's AssetMetadata schema."""
    errors: list[str] = []

    for record in records:
        line_number = record["_line_number"]
        payload = {
            key: value
            for key, value in record.items()
            if key != "_line_number"
        }

        try:
            AssetMetadata.model_validate(payload)
        except ValidationError as exc:
            for error in exc.errors():
                location = ".".join(str(part) for part in error["loc"])
                errors.append(
                    f"Line {line_number}, {location}: {error['msg']}"
                )

    return errors


def repeated_values(
    records: list[dict[str, Any]],
    field_name: str,
) -> dict[str, list[int]]:
    """Return repeated non-empty values and their manifest line numbers."""
    positions: dict[str, list[int]] = defaultdict(list)

    for record in records:
        value = record.get(field_name)
        if value:
            positions[str(value)].append(record["_line_number"])

    return {
        value: lines
        for value, lines in positions.items()
        if len(lines) > 1
    }


def resolve_project_path(stored_path: str) -> tuple[Path | None, str | None]:
    """Resolve a portable path and reject absolute or escaping paths."""
    path = Path(stored_path)

    if path.is_absolute():
        return None, "absolute path is not portable"

    resolved = (PROJ_ROOT / path).resolve()

    try:
        resolved.relative_to(PROJ_ROOT.resolve())
    except ValueError:
        return None, "path escapes the repository"

    return resolved, None


def audit_artifacts(
    records: list[dict[str, Any]],
) -> tuple[list[str], list[str], dict[str, str]]:
    """Check artifact paths and calculate hashes for readable HTML files."""
    critical: list[str] = []
    warnings: list[str] = []
    html_hashes: dict[str, str] = {}

    for record in records:
        line_number = record["_line_number"]
        asset_id = record.get("asset_id", "<missing asset_id>")

        raw_html_path = record.get("raw_html_path")
        if not raw_html_path:
            critical.append(f"Line {line_number} ({asset_id}): no HTML path")
        else:
            html_file, path_error = resolve_project_path(str(raw_html_path))
            if path_error:
                critical.append(
                    f"Line {line_number} ({asset_id}): HTML {path_error}"
                )
            elif html_file is None or not html_file.is_file():
                critical.append(
                    f"Line {line_number} ({asset_id}): HTML file is missing"
                )
            else:
                content = html_file.read_bytes()
                html_hashes[str(asset_id)] = hashlib.sha256(content).hexdigest()
                if not content.strip():
                    critical.append(
                        f"Line {line_number} ({asset_id}): HTML file is empty"
                    )
                elif len(content) < 500:
                    warnings.append(
                        f"Line {line_number} ({asset_id}): HTML is only "
                        f"{len(content)} bytes; it may be a blocked/error page"
                    )

        screenshot_path = record.get("screenshot_path")
        if not screenshot_path:
            warnings.append(
                f"Line {line_number} ({asset_id}): no screenshot path"
            )
            continue

        screenshot_file, path_error = resolve_project_path(str(screenshot_path))
        if path_error:
            critical.append(
                f"Line {line_number} ({asset_id}): screenshot {path_error}"
            )
        elif screenshot_file is None or not screenshot_file.is_file():
            warnings.append(
                f"Line {line_number} ({asset_id}): screenshot file is missing"
            )

    return critical, warnings, html_hashes


def group_identical_content(
    html_hashes: dict[str, str],
) -> dict[str, list[str]]:
    """Group asset IDs whose HTML bytes are exactly identical."""
    groups: dict[str, list[str]] = defaultdict(list)

    for asset_id, digest in html_hashes.items():
        groups[digest].append(asset_id)

    return {
        digest: asset_ids
        for digest, asset_ids in groups.items()
        if len(asset_ids) > 1
    }


def counts(records: list[dict[str, Any]], field_name: str) -> Counter[str]:
    """Count printable values for a manifest field."""
    return Counter(
        str(record.get(field_name) or "MISSING")
        for record in records
    )


def markdown_table(counter: Counter[str], label: str) -> list[str]:
    """Render a two-column count table."""
    lines = [f"| {label} | Records |", "|---|---:|"]
    lines.extend(
        f"| {value} | {count} |"
        for value, count in sorted(counter.items())
    )
    return lines


def audience_by_bank_table(records: list[dict[str, Any]]) -> list[str]:
    """Render bank-level youth/adult coverage for comparison readiness."""
    coverage: dict[str, Counter[str]] = defaultdict(Counter)

    for record in records:
        bank = str(record.get("bank") or "MISSING")
        audience = str(record.get("audience_label") or "MISSING")
        coverage[bank][audience] += 1

    lines = [
        "| Bank | Youth 18-25 | General adult | Other/missing |",
        "|---|---:|---:|---:|",
    ]

    for bank, audiences in sorted(coverage.items()):
        youth = audiences.get("youth_18_25", 0)
        adult = audiences.get("general_adult", 0)
        other = sum(audiences.values()) - youth - adult
        lines.append(f"| {bank} | {youth} | {adult} | {other} |")

    return lines


def append_findings(
    lines: list[str],
    title: str,
    findings: list[str],
    empty_message: str,
) -> None:
    """Append a report section containing bullet-point findings."""
    lines.append(f"\n## {title}\n")
    if findings:
        lines.extend(f"- {finding}" for finding in findings)
    else:
        lines.append(empty_message)


def write_report(
    records: list[dict[str, Any]],
    parse_errors: list[str],
    schema_errors: list[str],
    critical: list[str],
    warnings: list[str],
    duplicate_ids: dict[str, list[int]],
    duplicate_urls: dict[str, list[int]],
    shared_html_paths: dict[str, list[int]],
    identical_content: dict[str, list[str]],
) -> None:
    """Write a human-readable audit report for the team."""
    total_critical = len(parse_errors) + len(schema_errors) + len(critical)
    status = "FAIL" if total_critical else "PASS WITH WARNINGS" if warnings else "PASS"

    lines = [
        "# Processed Asset Manifest Audit",
        "",
        f"**Input:** `{MANIFEST_PATH.relative_to(PROJ_ROOT).as_posix()}`  ",
        f"**Records:** {len(records)}  ",
        f"**Status:** **{status}**  ",
        f"**Critical findings:** {total_critical}  ",
        f"**Warnings:** {len(warnings)}",
        "\n## Coverage by bank\n",
        *markdown_table(counts(records, "bank"), "Bank"),
        "\n## Coverage by language\n",
        *markdown_table(counts(records, "language"), "Language"),
        "\n## Coverage by audience\n",
        *markdown_table(counts(records, "audience_label"), "Audience"),
        "\n## Audience coverage by bank\n",
        *audience_by_bank_table(records),
    ]

    mvp_counts = Counter(
        str(record.get("bank"))
        for record in records
        if record.get("bank") in MVP_BANKS
    )
    lines.extend(["\n## Recommended MVP scope\n", *markdown_table(mvp_counts, "Bank")])

    append_findings(lines, "JSON parsing", parse_errors, "No JSON parsing errors.")
    append_findings(lines, "Schema conformance", schema_errors, "All records conform to `AssetMetadata`.")
    append_findings(lines, "Critical artifact problems", critical, "No critical artifact problems.")

    duplicate_findings = [
        f"Duplicate asset ID `{value}` on lines {line_numbers}."
        for value, line_numbers in duplicate_ids.items()
    ]
    duplicate_findings.extend(
        f"Duplicate URL `{value}` on lines {line_numbers}."
        for value, line_numbers in duplicate_urls.items()
    )
    duplicate_findings.extend(
        f"Shared HTML path `{value}` on lines {line_numbers}."
        for value, line_numbers in shared_html_paths.items()
    )
    duplicate_findings.extend(
        "Identical HTML content for assets: " + ", ".join(asset_ids) + "."
        for asset_ids in identical_content.values()
    )
    append_findings(
        lines,
        "Duplicates and shared content",
        duplicate_findings,
        "No duplicated identifiers, URLs, paths or HTML content.",
    )

    append_findings(lines, "Warnings", warnings, "No warnings.")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Run the processed-manifest audit and write its report."""
    print(f"Auditing normalized manifest: {MANIFEST_PATH}")

    records, parse_errors = load_jsonl(MANIFEST_PATH)
    schema_errors = validate_schema(records)

    duplicate_ids = repeated_values(records, "asset_id")
    duplicate_urls = repeated_values(records, "url")
    shared_html_paths = repeated_values(records, "raw_html_path")

    artifact_critical, warnings, html_hashes = audit_artifacts(records)
    identical_content = group_identical_content(html_hashes)

    unexpected_languages = sorted(
        {
            str(record.get("language"))
            for record in records
            if record.get("language") not in EXPECTED_LANGUAGES
        }
    )
    if unexpected_languages:
        warnings.append(
            "Unexpected language values: " + ", ".join(unexpected_languages)
        )

    if duplicate_urls:
        warnings.append(f"Duplicate canonical URLs: {len(duplicate_urls)} group(s)")
    if shared_html_paths:
        warnings.append(f"Shared HTML paths: {len(shared_html_paths)} group(s)")
    if identical_content:
        warnings.append(
            f"Identical HTML content: {len(identical_content)} group(s)"
        )

    for bank in sorted(MVP_BANKS):
        bank_audiences = {
            record.get("audience_label")
            for record in records
            if record.get("bank") == bank
        }
        missing_audiences = {
            "youth_18_25",
            "general_adult",
        } - bank_audiences
        if missing_audiences:
            warnings.append(
                f"MVP bank {bank} has no "
                + ", ".join(sorted(missing_audiences))
                + " assets; within-bank youth/adult comparison is incomplete"
            )

    critical = list(artifact_critical)
    if duplicate_ids:
        critical.append(f"Duplicate asset IDs: {len(duplicate_ids)} group(s)")

    write_report(
        records=records,
        parse_errors=parse_errors,
        schema_errors=schema_errors,
        critical=critical,
        warnings=warnings,
        duplicate_ids=duplicate_ids,
        duplicate_urls=duplicate_urls,
        shared_html_paths=shared_html_paths,
        identical_content=identical_content,
    )

    total_critical = len(parse_errors) + len(schema_errors) + len(critical)

    print(f"Records audited: {len(records)}")
    print(f"Critical findings: {total_critical}")
    print(f"Warnings: {len(warnings)}")
    print(f"Report written to: {REPORT_PATH}")

    if total_critical:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
