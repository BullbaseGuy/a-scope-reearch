from __future__ import annotations

from pathlib import Path

import pandas as pd

from ascope.io import read_frame, utc_now_iso, write_frame, write_json

TABLES = {
    "financial_annual": {
        "required": {
            "security_id",
            "report_period",
            "available_at",
            "audit_opinion",
            "internal_control_opinion",
        },
        "key": ["security_id", "report_period", "available_at"],
    },
    "financial_quarterly": {
        "required": {
            "security_id",
            "report_period",
            "available_at",
            "revenue",
            "gross_profit",
            "deducted_net_profit",
            "operating_cash_flow",
            "accounts_receivable",
            "inventory",
            "contract_liabilities",
            "capex",
            "interest_bearing_debt",
            "total_equity",
            "total_assets",
            "cash",
        },
        "key": ["security_id", "report_period", "available_at"],
    },
}


def _files(root: Path, table: str) -> list[Path]:
    return sorted(path for path in root.rglob("*.csv") if table in path.stem.lower())


def _merge_table(
    input_dir: Path,
    table: str,
) -> tuple[pd.DataFrame, list[str], int]:
    paths = _files(input_dir, table)
    if not paths:
        raise ValueError(f"no {table} batch CSV files found under {input_dir}")
    frames = []
    for path in paths:
        frame = read_frame(path)
        missing = sorted(TABLES[table]["required"] - set(frame.columns))
        if missing:
            raise ValueError(f"{path} missing required columns: {missing}")
        frame = frame.copy()
        frame["_source_file"] = path.relative_to(input_dir).as_posix()
        frames.append(frame)
    merged = pd.concat(frames, ignore_index=True, sort=False)
    before = len(merged)
    key = TABLES[table]["key"]
    merged = (
        merged.sort_values([*key, "_source_file"])
        .drop_duplicates(key, keep="last")
        .drop(columns=["_source_file"])
        .sort_values(key)
        .reset_index(drop=True)
    )
    sources = [path.relative_to(input_dir).as_posix() for path in paths]
    return merged, sources, before


def merge_exports(input_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "status": "PASS",
        "input_dir": str(input_dir),
        "generated_at_utc": utc_now_iso(),
        "tables": {},
    }
    for table in TABLES:
        frame, sources, before = _merge_table(input_dir, table)
        output = output_dir / f"{table}.csv"
        write_frame(frame, output)
        result["tables"][table] = {
            "row_count": len(frame),
            "security_count": int(frame["security_id"].nunique()),
            "source_files": sources,
            "rows_before_dedup": before,
            "output": str(output),
        }
    write_json(output_dir / "financial_merge_manifest.json", result)
    return result
