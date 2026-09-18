'''
audit_jsonl.py
==============
Audit for campaign_asset.jsonl against the schema contract
(AssetMetadata) and against the project scope (banks, pairs, screenshots).

Run: python -m src.audit_jsonl
'''

import json
from pathlib import Path
from collections import Counter, defaultdict

from pydantic import ValidationError

from src.config import ASSETS_PATH, RAW_DIR, DOCS_DIR
from src.schema import AssetMetadata


# ============== Functions ==============

def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[WARN] Line {line_num}: invalid JSON — {e}")
    return records

def check_conformance(records: list[dict]) -> dict:

    # schema introspection
    required_fields = [
        name for name, field in AssetMetadata.model_fields.items()
        if field.is_required()
    ]
    missing = defaultdict(list)
    errors = []

    for i, record in enumerate(records):
        # detection of missing fields (coarse)
        for field in required_fields:
            if field not in record or record[field] in (None, ""):
                missing[field].append(i)
        # full validation with Pydantic (more detailed)
        try:
            AssetMetadata(**record)
        except ValidationError as e:
            errors.append({
                "record_index": i,
                "url": record.get("url", "<no url>"),
                "errors": e.errors()
            })
    return {
        "total_records": len(records),
        "required_fields": required_fields,
        "missing": dict(missing),
        "validation_errors": errors
    }

# check coverage by bank
def check_coverage(records: list[dict]) -> dict:
    return dict(Counter(r.get("bank", "UNKNOWN") for r in records))
# if Revolute is missing in the dict, it means it's completely missing from the scope.

def check_screenshots(records:list[dict]) -> dict:
    present, missing, no_path = 0, [], 0
    for i, r in enumerate(records):
        path_str = r.get("screenshot_path")
        if not path_str:
            no_path += 1
            continue
        path = Path(path_str)
        if not path.is_absolute():
            path = RAW_DIR / path
        if path.exists():
            present += 1
        else:
            missing.append((i, str(path)))
    return {"present": present, "missing": missing, "no_path": no_path}

# Enrichment
def check_pairs(records: list[dict]) -> dict:
    by_bank_role = defaultdict(Counter)
    for r in records:
        bank = r.get("bank", "UNKNOWN")
        role = r.get("asset_role", "UNKNOWN")
        by_bank_role[bank][role] += 1
    return {bank: dict(roles) for bank, roles in by_bank_role.items()}

def write_audit_md(
        conf: dict,
        coverage: dict,
        screenshots: dict,
        pairs: dict,
        output_path: Path
) -> None:
    '''
    Write the audit results to a markdown file.
    '''
    lines =[]

    # Header
    lines.append("# Data Audit — `campaign_asset.jsonl`\n")
    lines.append(f"**Total records:** {conf['total_records']}\n")

    # Section 1: Conformance
    lines.append("\n## 1. Conformance to schema\n")
    lines.append(f"**Required fields (from AssetMetadata):** {', '.join(conf['required_fields'])}\n")
    lines.append("\n### Missing fields\n")
    lines.append("| Field | Missing / Total |")
    lines.append("|-------|-----------------|")
    for field, indices in conf["missing"].items():
        lines.append(f"| `{field}` | {len(indices)} / {conf['total_records']} |")

    if conf["validation_errors"]:
        lines.append(f"\n### Validation errors\n")
        lines.append(f"**{len(conf['validation_errors'])} records failed Pydantic validation.**\n")
        lines.append("First 5 errors:\n")
        for err in conf["validation_errors"][:5]:
            lines.append(f"- `[record {err['record_index']}]` {err['url']}")
            for e in err["errors"][:2]:
                lines.append(f"  - `{e['loc']}`: {e['msg']}")

    # Section 2: Coverage
    lines.append("\n## 2. Coverage by bank\n")
    lines.append("| Bank | Records |")
    lines.append("|------|---------|")
    for bank, count in coverage.items():
        lines.append(f"| {bank} | {count} |")

    # Section 3: Screenshots
    lines.append("\n## 3. Screenshots\n")
    lines.append(f"- Present: **{screenshots['present']}**")
    lines.append(f"- Missing: **{len(screenshots['missing'])}**")
    lines.append(f"- No path: **{screenshots['no_path']}**\n")
    if screenshots["missing"]:
        lines.append("Missing files:\n")
        for i, path in screenshots["missing"]:
            lines.append(f"- `[record {i}]` {path}")

    # Section 4: Role coverage
    lines.append("\n## 4. Role coverage\n")
    lines.append("| Bank | Roles |")
    lines.append("|------|-------|")
    for bank, roles in pairs.items():
        roles_str = ", ".join(f"{r}: {c}" for r, c in roles.items())
        lines.append(f"| {bank} | {roles_str} |")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[OK] Markdown report saved to: {output_path}")

def main():
    print("==============================")
    print(f"Auditing: {ASSETS_PATH}")
    print("==============================\n")
    records = load_jsonl(ASSETS_PATH)
    print(f"Total records: {len(records)}\n")

    print("=== 1. Conformance to schema ===")
    conf = check_conformance(records)
    print(f"Required fields (from AssetMetadata): {conf['required_fields']}\n")
    for field, indices in conf["missing"].items():
        print(f"  {field}: missing/empty in {len(indices)}/{conf['total_records']} records")
    if conf["validation_errors"]:
        print(f"\n  Validation errors: {len(conf['validation_errors'])} records failed")
        for err in conf["validation_errors"][:3]:
            print(f"    [record {err['record_index']}] {err['url']}")
            for e in err["errors"][:2]:
                print(f"       - {e['loc']}: {e['msg']}")
    else:
        print("\n  No Pydantic validation errors.")

    print("\n=== 2. Coverage by bank ===")
    for bank, count in check_coverage(records).items():
        print(f"  {bank}: {count}")

    print("\n=== 3. Screenshots ===")
    screenshots = check_screenshots(records)
    print(f"  Present: {screenshots['present']}")
    print(f"  Missing: {len(screenshots['missing'])}")
    print(f"  No path: {screenshots['no_path']}")
    for i, path in screenshots["missing"]:
        print(f"    [record {i}] {path}")

    print("\n=== 4. Role coverage ===")
    pairs = check_pairs(records)
    for bank, roles in pairs.items():
        print(f"  {bank}: {roles}")

    # Write markdown report
    write_audit_md(
        conf=conf,
        coverage=check_coverage(records),
        screenshots=screenshots,
        pairs=pairs,
        output_path=DOCS_DIR / "data_audit.md",
    )


if __name__ == "__main__":
    main()