from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from ascope.adapters.http import get_json, session
from ascope.io import utc_now_iso, write_json

URLS = (
    'https://www.cninfo.com.cn/new/data/szse_stock.json',
    'https://www.cninfo.com.cn/new/data/bjse_stock.json',
)
REQUIRED_EXCHANGES = {'SSE', 'SZSE', 'BSE'}
REQUIRED_BOARDS = {'SSE_MAIN', 'STAR', 'SZSE_MAIN', 'CHINEXT', 'BSE'}


def is_a_share_code(code: str) -> bool:
    code = str(code).zfill(6)
    return bool(
        re.match(r'^(600|601|603|605|688|689)\d{3}$', code)
        or re.match(r'^(000|001|002|003|300|301)\d{3}$', code)
        or re.match(r'^(4|8)\d{5}$', code)
        or re.match(r'^92\d{4}$', code)
    )


def classify_exchange_board(code: str) -> tuple[str, str]:
    code = str(code).zfill(6)
    if re.match(r'^(688|689)\d{3}$', code):
        return 'SSE', 'STAR'
    if re.match(r'^(600|601|603|605)\d{3}$', code):
        return 'SSE', 'SSE_MAIN'
    if re.match(r'^(300|301)\d{3}$', code):
        return 'SZSE', 'CHINEXT'
    if re.match(r'^(000|001|002|003)\d{3}$', code):
        return 'SZSE', 'SZSE_MAIN'
    if re.match(r'^(4|8)\d{5}$', code) or re.match(r'^92\d{4}$', code):
        return 'BSE', 'BSE'
    return 'UNKNOWN', 'UNKNOWN'


def _rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    value = payload.get('stockList') or payload.get('data') or []
    return value if isinstance(value, list) else []


def normalize(item: dict[str, Any], source_url: str, as_of_date: str, retrieved_at: str) -> dict[str, Any] | None:
    code = str(item.get('code') or item.get('secCode') or '').strip().zfill(6)
    if not is_a_share_code(code):
        return None
    exchange, board = classify_exchange_board(code)
    if exchange == 'UNKNOWN':
        return None
    name = str(item.get('zwjc') or item.get('secName') or item.get('name') or item.get('zwmc') or '').strip()
    return {
        'security_id': f'{exchange}.{code}',
        'code': code,
        'name': name,
        'exchange': exchange,
        'board': board,
        'status': 'LISTED',
        'is_st': bool('ST' in name.upper()),
        'list_date': item.get('ssrq') or item.get('listDate') or None,
        'as_of_date': as_of_date,
        'source_id': 'CNINFO_BULK_DISCOVERY',
        'source_url': source_url,
        'org_id': item.get('orgId') or item.get('orgid') or '',
        'category': item.get('category') or item.get('plate') or '',
        'retrieved_at_utc': retrieved_at,
        'data_mode': 'LIVE',
    }


def validate_universe(frame: pd.DataFrame, minimum_count: int) -> dict[str, Any]:
    errors: list[str] = []
    if len(frame) < minimum_count:
        errors.append(f'incomplete universe: {len(frame)} < {minimum_count}')
    if frame['security_id'].duplicated().any():
        errors.append('duplicate security_id')
    missing_exchanges = sorted(REQUIRED_EXCHANGES - set(frame['exchange']))
    missing_boards = sorted(REQUIRED_BOARDS - set(frame['board']))
    if missing_exchanges:
        errors.append(f'missing exchanges: {missing_exchanges}')
    if missing_boards:
        errors.append(f'missing boards: {missing_boards}')
    return {
        'status': 'PASS' if not errors else 'FAIL',
        'security_count': len(frame),
        'exchange_counts': dict(Counter(frame['exchange'])),
        'board_counts': dict(Counter(frame['board'])),
        'errors': errors,
    }


def discover(output_dir: Path, as_of_date: str, minimum_count: int = 5000, payload_paths: list[Path] | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / 'raw_discovery'
    raw_dir.mkdir(exist_ok=True)
    retrieved = utc_now_iso()
    source_status = []
    merged: dict[str, dict[str, Any]] = {}
    http = session()
    http.headers.update({'Referer': 'https://www.cninfo.com.cn/'})
    sources: list[tuple[str, Any]] = []
    if payload_paths:
        import json
        for path in payload_paths:
            sources.append((str(path), json.loads(path.read_text(encoding='utf-8'))))
    else:
        for index, url in enumerate(URLS, start=1):
            try:
                payload = get_json(http, url)
                write_json(raw_dir / f'cninfo_{index}.json', payload)
                sources.append((url, payload))
            except Exception as exc:  # noqa: BLE001
                source_status.append({'url': url, 'status': 'UNAVAILABLE', 'error': str(exc)})
    for source_url, payload in sources:
        accepted = 0
        for item in _rows(payload):
            row = normalize(item, source_url, as_of_date, retrieved)
            if row is None:
                continue
            accepted += 1
            previous = merged.get(row['code'])
            if previous is None or (not previous.get('org_id') and row.get('org_id')):
                merged[row['code']] = row
        source_status.append({'url': source_url, 'status': 'PASS', 'raw_count': len(_rows(payload)), 'accepted': accepted})
    frame = pd.DataFrame([merged[code] for code in sorted(merged)])
    if frame.empty:
        frame = pd.DataFrame(columns=['security_id', 'code', 'name', 'exchange', 'board', 'status', 'is_st', 'list_date', 'as_of_date', 'source_id', 'source_url', 'org_id', 'category', 'retrieved_at_utc', 'data_mode'])
    validation = validate_universe(frame, minimum_count)
    manifest = {
        'status': 'DISCOVERY_COMPLETE_REQUIRES_MARKET_DATA' if validation['status'] == 'PASS' else 'DISCOVERY_INCOMPLETE',
        'provider': 'CNINFO_BULK',
        'expected_requests': 0 if payload_paths else len(URLS),
        'source_status': source_status,
        'validation': validation,
        'as_of_date': as_of_date,
        'generated_at_utc': retrieved,
        'investment_use': 'PROHIBITED_UNTIL_MARKET_AND_FINANCIAL_DATA_VALIDATED',
    }
    return frame, manifest
