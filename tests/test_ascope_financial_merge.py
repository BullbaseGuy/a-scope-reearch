from pathlib import Path

import pandas as pd

from ascope.financial_merge import merge_exports


def _quarterly() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "security_id": "SSE:600000",
            "report_period": "2025-12-31",
            "available_at": "2026-03-30",
            "revenue": 100,
            "gross_profit": 30,
            "deducted_net_profit": 10,
            "operating_cash_flow": 12,
            "accounts_receivable": 8,
            "inventory": 5,
            "contract_liabilities": 2,
            "capex": 4,
            "interest_bearing_debt": 20,
            "total_equity": 50,
            "total_assets": 100,
            "cash": 15,
        }
    ])


def _annual() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "security_id": "SSE:600000",
            "report_period": "2025-12-31",
            "available_at": "2026-03-30",
            "audit_opinion": "UNQUALIFIED",
            "internal_control_opinion": "UNQUALIFIED",
        }
    ])


def test_merge_exports_deduplicates_batches(tmp_path: Path) -> None:
    for batch in ("B001", "B002"):
        folder = tmp_path / batch
        folder.mkdir()
        _quarterly().to_csv(folder / "financial_quarterly.csv", index=False)
        _annual().to_csv(folder / "financial_annual.csv", index=False)
    output = tmp_path / "merged"
    result = merge_exports(tmp_path, output)
    assert result["status"] == "PASS"
    assert len(pd.read_csv(output / "financial_quarterly.csv")) == 1
    assert len(pd.read_csv(output / "financial_annual.csv")) == 1
