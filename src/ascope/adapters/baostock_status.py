from __future__ import annotations

from typing import Any

import pandas as pd

from ascope.io import utc_now_iso


def _security_id(code: str) -> str | None:
    value = str(code).strip().lower()
    if value.startswith("sh."):
        return f"SSE.{value.split('.', 1)[1].zfill(6)}"
    if value.startswith("sz."):
        return f"SZSE.{value.split('.', 1)[1].zfill(6)}"
    if value.startswith("bj."):
        return f"BSE.{value.split('.', 1)[1].zfill(6)}"
    return None


def _result_frame(result: Any) -> pd.DataFrame:
    if getattr(result, "error_code", "1") != "0":
        raise RuntimeError(
            f"BaoStock query failed: {getattr(result, 'error_msg', 'unknown error')}"
        )
    rows: list[list[str]] = []
    while result.next():
        rows.append(result.get_row_data())
    return pd.DataFrame(rows, columns=result.fields)


def fetch(as_of_date: str) -> pd.DataFrame:
    import baostock as bs

    login = bs.login()
    if getattr(login, "error_code", "1") != "0":
        raise RuntimeError(
            f"BaoStock login failed: {getattr(login, 'error_msg', 'unknown error')}"
        )
    try:
        basics = _result_frame(bs.query_stock_basic())
        try:
            trading = _result_frame(bs.query_all_stock(day=as_of_date))
        except Exception:  # noqa: BLE001
            trading = pd.DataFrame(columns=["code", "tradeStatus", "code_name"])
    finally:
        bs.logout()

    if basics.empty:
        raise RuntimeError("BaoStock returned no security basics")
    basics = basics.copy()
    basics["security_id"] = basics["code"].map(_security_id)
    basics = basics.loc[
        basics["security_id"].notna() & basics["type"].astype(str).eq("1")
    ].copy()
    basics["status"] = basics["status"].astype(str).map(
        {"1": "LISTED", "0": "DELISTED"}
    ).fillna("REVIEW")
    basics["current_name"] = basics["code_name"].astype(str).str.strip()
    basics["list_date"] = basics["ipoDate"].replace("", pd.NA)
    basics["out_date"] = basics["outDate"].replace("", pd.NA)
    basics["status_source"] = "BAOSTOCK_BASIC"
    basics["status_retrieved_at_utc"] = utc_now_iso()

    if not trading.empty and "code" in trading:
        trading = trading.copy()
        trading["security_id"] = trading["code"].map(_security_id)
        trading = trading.loc[trading["security_id"].notna()].copy()
        trading = trading[["security_id", "tradeStatus"]].drop_duplicates(
            "security_id", keep="last"
        )
        trading = trading.rename(columns={"tradeStatus": "trade_status"})
        basics = basics.merge(trading, on="security_id", how="left")
    else:
        basics["trade_status"] = pd.NA

    return basics[
        [
            "security_id",
            "status",
            "current_name",
            "list_date",
            "out_date",
            "trade_status",
            "status_source",
            "status_retrieved_at_utc",
        ]
    ].drop_duplicates("security_id", keep="last")
