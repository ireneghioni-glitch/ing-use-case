"""
Reconcile raw campaign asset metadata.

This module converts machine-specific raw metadata into a portable,
schema-valid asset manifest.

Input:
    data/raw/campaign_asset.jsonl

Output:
    data/processed/asset_manifest.jsonl

The raw input is never modified.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic import ValidationError

from src.config import (
    ASSETS_PATH,
    PROCESSED_DIR,
    PROJ_ROOT,
    RAW_DIR,
    SCREENSHOTS_DIR,
)
from src.schema import AssetMetadata


OUTPUT_PATH = PROCESSED_DIR / "asset_manifest.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    """Load non-empty JSON objects from a JSONL file."""
    records: list[dict] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(
                    f"Line {line_number} must contain a JSON object."
                )

            records.append(record)

    return records


def canonicalize_url(url: str) -> str:
    """
    Normalize a URL for stable identification.

    The fragment is removed, scheme/domain are lowercased, and duplicate
    or trailing slashes are normalized. Query parameters are preserved.
    """
    parts = urlsplit(url.strip())

    if parts.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {url}")

    if not parts.netloc:
        raise ValueError(f"URL has no domain: {url}")

    normalized_path = re.sub(r"/+", "/", parts.path)
    normalized_path = normalized_path.rstrip("/") or "/"

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            normalized_path,
            parts.query,
            "",  # discard fragment
        )
    )


def slugify(value: str, fallback: str = "asset") -> str:
    """Convert a value into a filesystem- and ID-friendly slug."""
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    return slug or fallback


def create_asset_id(record: dict) -> str:
    """
    Create a deterministic, unique ID from bank, page, language and URL.

    The URL hash prevents French and English pages with the same final
    path component from receiving the same ID.
    """
    canonical_url = canonicalize_url(record["url"])
    parts = urlsplit(canonical_url)

    page_name = Path(parts.path).stem or "homepage"
    bank = slugify(str(record.get("bank", "unknown-bank")))
    page = slugify(page_name)
    language = slugify(str(record.get("language", "unknown")), "unknown")
    url_hash = hashlib.sha256(
        canonical_url.encode("utf-8")
    ).hexdigest()[:10]

    return f"{bank}__{page}__{language}__{url_hash}"


def get_filename(stored_path: str) -> str:
    """
    Extract a filename from either a Windows or POSIX path.

    Replacing backslashes first allows paths created on another Windows
    computer to be interpreted safely.
    """
    normalized = stored_path.replace("\\", "/")
    filename = normalized.rstrip("/").split("/")[-1]

    if not filename:
        raise ValueError(f"Could not obtain filename from: {stored_path}")

    return filename


def resolve_repo_file(
    stored_path: str,
    expected_directory: Path,
) -> Path:
    """
    Resolve an artifact inside the current repository.

    Machine-specific absolute paths are not trusted. Their filename is
    located inside the expected repository directory instead.
    """
    if not stored_path:
        raise FileNotFoundError("Stored path is empty.")

    filename = get_filename(stored_path)

    candidates: list[Path] = []

    normalized_path = Path(stored_path.replace("\\", "/"))

    # A relative path may already be correct from the project root.
    if not normalized_path.is_absolute():
        candidates.append(PROJ_ROOT / normalized_path)

    # Main portable fallback: locate by filename in the expected folder.
    candidates.append(expected_directory / filename)

    for candidate in candidates:
        if candidate.is_file():
            resolved = candidate.resolve()

            # Make sure we never resolve an artifact outside the repository.
            try:
                resolved.relative_to(PROJ_ROOT.resolve())
            except ValueError:
                continue

            return resolved

    attempted = ", ".join(str(path) for path in candidates)

    raise FileNotFoundError(
        f"Could not resolve {stored_path!r}. Tried: {attempted}"
    )


def make_project_relative(path: Path) -> str:
    """Return a portable POSIX-style path relative to the repository."""
    relative_path = path.resolve().relative_to(PROJ_ROOT.resolve())
    return relative_path.as_posix()


def reconcile_record(record: dict) -> AssetMetadata:
    """Reconcile and validate one raw asset record."""
    raw_html = resolve_repo_file(
        stored_path=record["raw_html_path"],
        expected_directory=RAW_DIR,
    )

    screenshot_path: str | None = None

    if record.get("screenshot_path"):
        screenshot = resolve_repo_file(
            stored_path=record["screenshot_path"],
            expected_directory=SCREENSHOTS_DIR,
        )
        screenshot_path = make_project_relative(screenshot)

    # Support both current and older timestamp field names.
    collected_at = record.get("collected_at") or record.get("scraped_at")

    reconciled = {
        "asset_id": create_asset_id(record),
        "bank": record.get("bank"),
        "bank_type": record.get("bank_type"),
        "channel": record.get("channel"),
        "audience_label": record.get("audience_label"),
        "audience_evidence": record.get("audience_evidence"),
        "eligibility_age_min": record.get("eligibility_age_min"),
        "eligibility_age_max": record.get("eligibility_age_max"),
        "student_requirement": record.get("student_requirement"),
        "overlap_with_18_25": record.get("overlap_with_18_25"),
        "pair_id": record.get("pair_id"),
        "url": canonicalize_url(record["url"]),
        "language": record.get("language"),
        "collected_at": collected_at,
        "raw_html_path": make_project_relative(raw_html),
        "screenshot_path": screenshot_path,
        "text": record.get("text")
    }

    return AssetMetadata.model_validate(reconciled)


def find_repeated_values(
    records: list[dict],
    field_name: str,
) -> dict[str, list[int]]:
    """Return repeated non-empty field values and their record numbers."""
    positions: dict[str, list[int]] = defaultdict(list)

    for index, record in enumerate(records, start=1):
        value = record.get(field_name)

        if value:
            positions[str(value)].append(index)

    return {
        value: indices
        for value, indices in positions.items()
        if len(indices) > 1
    }


def write_jsonl(
    records: list[AssetMetadata],
    output_path: Path,
) -> None:
    """Write validated models as JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            json_record = record.model_dump(mode="json")
            file.write(
                json.dumps(json_record, ensure_ascii=False) + "\n"
            )


def main() -> None:
    """Run reconciliation for the complete raw asset dataset."""
    print(f"Loading raw assets from: {ASSETS_PATH}")

    raw_records = load_jsonl(ASSETS_PATH)

    if not raw_records:
        raise RuntimeError("The raw asset file contains no records.")

    print(f"Loaded {len(raw_records)} raw records.")

    duplicate_source_ids = find_repeated_values(
        raw_records,
        "asset_id",
    )
    duplicate_urls = find_repeated_values(
        raw_records,
        "url",
    )
    shared_html_paths = find_repeated_values(
        raw_records,
        "raw_html_path",
    )

    if duplicate_source_ids:
        print("\n[WARN] Duplicate source asset IDs:")
        for value, indices in duplicate_source_ids.items():
            print(f"  {value}: records {indices}")

    if duplicate_urls:
        print("\n[WARN] Duplicate source URLs:")
        for value, indices in duplicate_urls.items():
            print(f"  {value}: records {indices}")

    if shared_html_paths:
        print("\n[WARN] Shared raw HTML paths:")
        for value, indices in shared_html_paths.items():
            print(f"  {value}: records {indices}")

    reconciled_records: list[AssetMetadata] = []
    errors: list[str] = []

    for record_number, raw_record in enumerate(
        raw_records,
        start=1,
    ):
        try:
            reconciled = reconcile_record(raw_record)
            reconciled_records.append(reconciled)

        except (
            KeyError,
            ValueError,
            FileNotFoundError,
            ValidationError,
        ) as exc:
            url = raw_record.get("url", "<no URL>")
            errors.append(
                f"Record {record_number} ({url}): {exc}"
            )

    if errors:
        print("\n[ERROR] Reconciliation failed:")
        for error in errors:
            print(f"  - {error}")

        raise SystemExit(
            f"\nNo output written. {len(errors)} record(s) failed."
        )

    output_ids = [
        record.asset_id
        for record in reconciled_records
    ]

    duplicate_output_ids = [
        asset_id
        for asset_id, count in Counter(output_ids).items()
        if count > 1
    ]

    if duplicate_output_ids:
        raise RuntimeError(
            "Generated duplicate asset IDs: "
            + ", ".join(duplicate_output_ids)
        )

    write_jsonl(
        records=reconciled_records,
        output_path=OUTPUT_PATH,
    )

    print(f"\n[OK] Reconciled {len(reconciled_records)} records.")
    print(f"[OK] All generated asset IDs are unique.")
    print(f"[OK] Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()