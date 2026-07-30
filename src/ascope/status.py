from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

from ascope.adapters.baostock_status import fetch as fetch_baostock
from ascope.adapters.bse_status import fetch as fetch_bse
from ascope.io import read_frame, utc_now_iso, write_frame, write_json

ARCHIVE_NAME = re.compile(r"(^PT)|退市|退$|退[^A-Za-z0-9]*$", re.IGNORECASE)
ACTIVE = {"LISTED", "TRADING"}


def _archive_marker(name: object) -> bool:
    return bool(ARCHIVE_NAME.search(str(name).strip()))


def reconcile(
    identity: pd.DataFrame,
    provider: pd.DataFrame,
    as_of_date: str,
    *,
    minimum_listed_count: int = 5000,
    minimum_bse_count: int = 150,
) -> tuple[pd.DataFrame, dict]:
    required = {"security_id", "code", "name", "exchange", "board"}
    missing = sorted(required - set(identity.columns))
    if missing:
        raise ValueError(f"identity security master missing columns: {missing}")
    result = identity.copy()
    result["status"] = "REVIEW"
    result["status_reason"] = "IDENTITY_ONLY_NOT_CURRENT_STATUS"

    status_columns = [
        "security_id",
        "status",
        "current_name",
        "list_date",
        "out_date",
        "trade_status",
        "status_source",
        "status_retrieved_at_utc",
    ]
    provider = provider[status_columns].drop_duplicates("security_id", keep="last")
    provider = provider.rename(
        columns={
            "status": "provider_status",
            "list_date": "provider_list_date",
        }
    )
    result = result.merge(provider, on="security_id", how="left")
    matched = result["provider_status"].notna()
    result.loc[matched, "status"] = result.loc[matched, "provider_status"]
    result.loc[matched, "status_reason"] = "CURRENT_STATUS_PROVIDER"
    result.loc[matched & result["current_name"].notna(), "name"] = result.loc[
        matched & result["current_name"].notna(), "current_name"
    ]
    if "list_date" not in result:
        result["list_date"] = pd.NA
    result.loc[matched & result["provider_list_date"].notna(), "list_date"] = result.loc[
        matched & result["provider_list_date"].notna(), "provider_list_date"
    ]

    # Current provider membership does not override an explicit delisting/archive name.
    # This captures securities that remain visible during a delisting period, such as
    # names ending in “退”, without dropping their identity history.
    archive = result["name"].map(_archive_marker)
    result.loc[archive, "status"] = "DELISTED_OR_ARCHIVE"
    result.loc[archive, "status_reason"] = "CURRENT_OR_ARCHIVE_NAME_MARKER"

    result["is_st"] = result["name"].astype(str).str.upper().str.contains("ST", regex=False)
    result["status_as_of_date"] = as_of_date
    result["status_snapshot_type"] = "CURRENT_RECONCILIATION"
    result["status_reconciled_at_utc"] = utc_now_iso()

    listed = result["status"].isin(ACTIVE)
    listed_count = int(listed.sum())
    listed_exchanges = Counter(result.loc[listed, "exchange"])
    archive_listed = result.loc[listed, "name"].map(_archive_marker)
    errors: list[str] = []
    if listed_count < minimum_listed_count:
        errors.append(f"listed count too small: {listed_count} < {minimum_listed_count}")
    if int(listed_exchanges.get("BSE", 0)) < minimum_bse_count:
        errors.append(
            f"BSE listed count too small: {listed_exchanges.get('BSE', 0)} < {minimum_bse_count}"
        )
    if archive_listed.any():
        errors.append("archive-name securities were marked LISTED")
    manifest = {
        "status": "PASS" if not errors else "FAIL",
        "as_of_date": as_of_date,
        "identity_count": len(result),
        "provider_match_count": int(matched.sum()),
        "listed_count": listed_count,
        "listed_exchange_counts": dict(listed_exchanges),
        "status_counts": dict(Counter(result["status"])),
        "st_or_star_st_count": int((listed & result["is_st"]).sum()),
        "archive_or_delisted_count": int(
            result["status"].isin({"DELISTED", "DELISTED_OR_ARCHIVE"}).sum()
        ),
        "review_count": int(result["status"].eq("REVIEW").sum()),
        "errors": errors,
        "generated_at_utc": utc_now_iso(),
        "historical_use": "PROHIBITED_CURRENT_STATUS_SNAPSHOT_ONLY",
    }
    drop = ["provider_status", "provider_list_date", "current_name"]
    result = result.drop(columns=[column for column in drop if column in result])
    return result, manifest


def reconcile_live(
    security_master: Path,
    output_dir: Path,
    as_of_date: str,
    *,
    minimum_listed_count: int = 5000,
    minimum_bse_count: int = 150,
) -> dict:
    identity = read_frame(security_master)
    providers = [fetch_baostock(as_of_date)]
    try:
        providers.append(fetch_bse())
    except Exception as exc:  # noqa: BLE001
        bse_error = str(exc)
    else:
        bse_error = None
    provider = pd.concat(providers, ignore_index=True, sort=False)
    reconciled, manifest = reconcile(
        identity,
        provider,
        as_of_date,
        minimum_listed_count=minimum_listed_count,
        minimum_bse_count=minimum_bse_count,
    )
    manifest["provider_rows"] = len(provider)
    manifest["bse_provider_error"] = bse_error
    output_dir.mkdir(parents=True, exist_ok=True)
    write_frame(reconciled, output_dir / "security_master.csv")
    write_frame(
        reconciled.loc[reconciled["status"].isin(ACTIVE)].copy(),
        output_dir / "current_listed_securities.csv",
    )
    write_frame(
        reconciled.loc[~reconciled["status"].isin(ACTIVE)].copy(),
        output_dir / "archive_or_review_securities.csv",
    )
    write_json(output_dir / "status_reconciliation_manifest.json", manifest)
    return manifest
