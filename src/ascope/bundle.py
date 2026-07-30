from __future__ import annotations

import json
import zipfile
from pathlib import Path

from ascope.io import sha256_file, utc_now_iso, write_json
from ascope.qa import validate_bundle

REQUIRED_FILES = (
    "security_master.csv",
    "financial_quarterly.csv",
    "financial_annual.csv",
    "market_data.csv",
)


def package_bundle(
    input_dir: Path,
    output_zip: Path,
    as_of_date: str,
    *,
    minimum_securities: int = 5000,
    minimum_market_days: int = 120,
) -> dict:
    report = validate_bundle(
        input_dir,
        as_of_date,
        minimum_securities=minimum_securities,
        minimum_market_days=minimum_market_days,
    )
    if report["status"] != "PASS":
        raise ValueError(f"live bundle validation failed: {report['errors']}")
    files = [input_dir / name for name in REQUIRED_FILES]
    files.append(input_dir / "live_bundle_validation.json")
    file_hashes = {path.name: sha256_file(path) for path in files}
    manifest = {
        "schema_version": 1,
        "status": "VALIDATED_LIVE_BUNDLE",
        "data_mode": "LIVE",
        "investment_use": "RESEARCH_ONLY",
        "as_of_date": as_of_date,
        "generated_at_utc": utc_now_iso(),
        "validation": report,
        "file_sha256": file_hashes,
    }
    manifest_path = input_dir / "bundle_manifest.json"
    write_json(manifest_path, manifest)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in [*files, manifest_path]:
            archive.write(path, arcname=f"live_bundle/{path.name}")
    manifest["archive"] = str(output_zip)
    manifest["archive_sha256"] = sha256_file(output_zip)
    return manifest


def read_bundle_manifest(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("status") != "VALIDATED_LIVE_BUNDLE":
        raise ValueError("bundle manifest is not validated")
    if value.get("data_mode") != "LIVE":
        raise ValueError("bundle manifest is not LIVE")
    return value
