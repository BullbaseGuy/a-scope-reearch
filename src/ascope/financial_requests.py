from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from ascope.io import read_frame, utc_now_iso, write_frame, write_json

ACTIVE_STATUSES = {"LISTED", "TRADING"}


def _flag(frame: pd.DataFrame, name: str, default: bool = False) -> pd.Series:
    if name not in frame:
        return pd.Series(default, index=frame.index, dtype=bool)
    value = frame[name]
    if value.dtype == bool:
        return value.fillna(default)
    return value.astype(str).str.lower().isin({"1", "true", "yes", "y"})


def build(security_master: Path, output_dir: Path, through: str, batch_size: int = 200) -> dict:
    frame = read_frame(security_master).copy()
    required = {"security_id", "code", "name", "exchange", "status", "is_st"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"security master is not status-reconciled; missing {missing}")
    active = frame["status"].astype(str).isin(ACTIVE_STATUSES)
    is_st = _flag(frame, "is_st")
    standard = frame.loc[active & ~is_st].copy()
    high_risk = frame.loc[active & is_st].copy()
    archive_review = frame.loc[~active].copy()
    if standard.empty:
        raise ValueError("no standard active non-ST securities available for financial requests")

    output_dir.mkdir(parents=True, exist_ok=True)
    batch_dir = output_dir / "financial_batches"
    batch_dir.mkdir(exist_ok=True)
    request_rows = []
    batch_count = math.ceil(len(standard) / batch_size)
    for batch_no in range(batch_count):
        start = batch_no * batch_size
        part = standard.iloc[start : start + batch_size].copy()
        batch_id = f"B{batch_no + 1:03d}"
        part["batch_id"] = batch_id
        part["request_annual_from"] = "2019-12-31"
        part["request_quarterly_from"] = "2022-03-31"
        part["request_through"] = through
        part["required_available_at"] = True
        part["request_status"] = "PENDING"
        columns = [
            "batch_id",
            "security_id",
            "code",
            "name",
            "exchange",
            "request_annual_from",
            "request_quarterly_from",
            "request_through",
            "required_available_at",
            "request_status",
        ]
        write_frame(part[columns], batch_dir / f"{batch_id}.csv")
        request_rows.extend(part[columns].to_dict("records"))

    requests = pd.DataFrame(request_rows)
    write_frame(requests, output_dir / "financial_request_manifest.csv")
    write_frame(high_risk, output_dir / "high_risk_st_manifest.csv")
    write_frame(archive_review, output_dir / "archive_or_review_manifest.csv")
    manifest = {
        "status": "READY",
        "through": through,
        "batch_size": batch_size,
        "batch_count": batch_count,
        "identity_count": len(frame),
        "standard_request_count": len(standard),
        "high_risk_st_count": len(high_risk),
        "archive_or_review_count": len(archive_review),
        "generated_at_utc": utc_now_iso(),
        "selection_rule": "status in LISTED/TRADING and is_st=false",
    }
    write_json(output_dir / "financial_request_manifest.json", manifest)
    return manifest
