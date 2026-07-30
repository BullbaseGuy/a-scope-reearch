from pathlib import Path

import pandas as pd

from ascope.financial_requests import build
from ascope.status import reconcile


def identity() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "security_id": "SSE.600000",
                "code": "600000",
                "name": "浦发银行",
                "exchange": "SSE",
                "board": "SSE_MAIN",
                "status": "REVIEW",
                "is_st": False,
            },
            {
                "security_id": "SZSE.000004",
                "code": "000004",
                "name": "国华退",
                "exchange": "SZSE",
                "board": "SZSE_MAIN",
                "status": "REVIEW",
                "is_st": False,
            },
            {
                "security_id": "BSE.920001",
                "code": "920001",
                "name": "北证示例",
                "exchange": "BSE",
                "board": "BSE",
                "status": "REVIEW",
                "is_st": False,
            },
        ]
    )


def provider() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "security_id": "SSE.600000",
                "status": "LISTED",
                "current_name": "浦发银行",
                "list_date": "1999-11-10",
                "out_date": pd.NA,
                "trade_status": "1",
                "status_source": "TEST",
                "status_retrieved_at_utc": "2026-07-30T00:00:00Z",
            },
            {
                "security_id": "BSE.920001",
                "status": "LISTED",
                "current_name": "北证示例",
                "list_date": pd.NA,
                "out_date": pd.NA,
                "trade_status": "1",
                "status_source": "TEST",
                "status_retrieved_at_utc": "2026-07-30T00:00:00Z",
            },
        ]
    )


def test_identity_does_not_imply_listed() -> None:
    result, manifest = reconcile(
        identity(), provider(), "2026-07-30", minimum_listed_count=2, minimum_bse_count=1
    )
    assert manifest["status"] == "PASS"
    status = result.set_index("security_id")["status"].to_dict()
    assert status["SSE.600000"] == "LISTED"
    assert status["BSE.920001"] == "LISTED"
    assert status["SZSE.000004"] == "DELISTED_OR_ARCHIVE"


def test_financial_manifest_excludes_archive_and_st(tmp_path: Path) -> None:
    frame, _ = reconcile(
        identity(), provider(), "2026-07-30", minimum_listed_count=2, minimum_bse_count=1
    )
    frame.loc[frame["security_id"] == "BSE.920001", "is_st"] = True
    master = tmp_path / "security_master.csv"
    frame.to_csv(master, index=False)
    output = tmp_path / "requests"
    manifest = build(master, output, "2026-07-30", batch_size=200)
    assert manifest["standard_request_count"] == 1
    assert manifest["high_risk_st_count"] == 1
    assert manifest["archive_or_review_count"] == 1
    requests = pd.read_csv(output / "financial_request_manifest.csv")
    assert requests["security_id"].tolist() == ["SSE.600000"]
