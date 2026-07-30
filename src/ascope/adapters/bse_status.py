from __future__ import annotations

from typing import Any

import pandas as pd

from ascope.adapters.http import get_json, session
from ascope.io import utc_now_iso

URL = "https://82.push2.eastmoney.com/api/qt/clist/get"


def _rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    rows = data.get("diff") or []
    return rows if isinstance(rows, list) else []


def fetch(page_size: int = 100) -> pd.DataFrame:
    http = session()
    seen: dict[str, dict[str, Any]] = {}
    page = 1
    total: int | None = None
    while True:
        payload = get_json(
            http,
            URL,
            params={
                "pn": page,
                "pz": page_size,
                "po": 1,
                "np": 1,
                "fltt": 2,
                "invt": 2,
                "fid": "f12",
                "fs": "m:0+t:81+s:2048",
                "fields": "f12,f14",
            },
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict) and total is None:
            raw_total = data.get("total")
            if isinstance(raw_total, int):
                total = raw_total
        rows = _rows(payload)
        if not rows:
            break
        new_count = 0
        for row in rows:
            code = str(row.get("f12") or "").strip().zfill(6)
            name = str(row.get("f14") or "").strip()
            if not (code.startswith(("4", "8", "92")) and name):
                continue
            if code not in seen:
                new_count += 1
            seen[code] = {
                "security_id": f"BSE.{code}",
                "status": "LISTED",
                "current_name": name,
                "list_date": pd.NA,
                "out_date": pd.NA,
                "trade_status": "1",
                "status_source": "EASTMONEY_BSE_CURRENT",
                "status_retrieved_at_utc": utc_now_iso(),
            }
        if total is not None and len(seen) >= total:
            break
        if len(rows) < page_size:
            break
        if new_count == 0:
            raise RuntimeError(f"BSE pagination stalled at page {page}")
        page += 1
        if page > 10:
            raise RuntimeError("BSE status pagination exceeded safety limit")
    if not seen:
        raise RuntimeError("BSE current-status source returned no securities")
    return pd.DataFrame([seen[code] for code in sorted(seen)])
