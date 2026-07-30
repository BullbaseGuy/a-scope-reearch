import json
import zipfile
from pathlib import Path

import pandas as pd

from ascope.bundle import package_bundle


def test_package_validated_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    pd.DataFrame([
        {"security_id": "SSE:600000", "code": "600000", "name": "Demo", "is_st": True}
    ]).to_csv(bundle / "security_master.csv", index=False)
    financial = pd.DataFrame([
        {
            "security_id": "SSE:600000",
            "report_period": "2025-12-31",
            "available_at": "2026-03-30",
        }
    ])
    financial.to_csv(bundle / "financial_quarterly.csv", index=False)
    financial.to_csv(bundle / "financial_annual.csv", index=False)
    pd.DataFrame([
        {"security_id": "SSE:600000", "trade_date": "2026-07-29", "close": 10, "amount_cny": 1000000}
    ]).to_csv(bundle / "market_data.csv", index=False)
    output = tmp_path / "ascope-live-bundle-2026-07-29.zip"
    result = package_bundle(
        bundle,
        output,
        "2026-07-29",
        minimum_securities=1,
        minimum_market_days=1,
    )
    assert result["status"] == "VALIDATED_LIVE_BUNDLE"
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        assert "live_bundle/bundle_manifest.json" in names
        manifest = json.loads(archive.read("live_bundle/bundle_manifest.json"))
        assert manifest["data_mode"] == "LIVE"
