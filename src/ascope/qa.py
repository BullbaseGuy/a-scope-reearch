from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ascope.io import read_frame, utc_now_iso, write_json


def validate_bundle(input_dir: Path, as_of_date: str, *, minimum_securities: int = 5000, minimum_market_days: int = 120) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    tables = {}
    for name in ['security_master', 'financial_quarterly', 'financial_annual', 'market_data']:
        path = input_dir / f'{name}.csv'
        if not path.exists():
            errors.append(f'missing {path.name}')
            tables[name] = pd.DataFrame()
        else:
            tables[name] = read_frame(path)
    master = tables['security_master']
    if len(master) < minimum_securities:
        errors.append(f'security_master below minimum: {len(master)} < {minimum_securities}')
    if not master.empty and master['security_id'].duplicated().any():
        errors.append('duplicate security_id')
    if not master.empty and master['code'].astype(str).str.len().ne(6).any():
        errors.append('security code lost leading zero or has invalid length')
    ids = set(master.get('security_id', []))
    for name in ['financial_quarterly', 'financial_annual', 'market_data']:
        frame = tables[name]
        if not frame.empty:
            orphan = set(frame['security_id']) - ids
            if orphan:
                errors.append(f'{name} contains orphan securities: {len(orphan)}')
    for name in ['financial_quarterly', 'financial_annual']:
        frame = tables[name]
        if not frame.empty:
            available = pd.to_datetime(frame['available_at'], errors='coerce')
            if (available > pd.Timestamp(as_of_date)).any():
                errors.append(f'{name} contains future available_at rows')
    market = tables['market_data']
    coverage = 0.0
    if not market.empty:
        days = market.groupby('security_id')['trade_date'].nunique()
        coverage = float((days >= minimum_market_days).mean())
        if coverage < 0.8:
            errors.append(f'market history coverage below 80%: {coverage:.1%}')
    st_count = int(master.get('is_st', pd.Series(dtype=bool)).astype(str).str.lower().isin({'true','1','yes'}).sum()) if not master.empty else 0
    if len(master) >= minimum_securities and st_count == 0:
        warnings.append('ST count is zero; verify ST securities were not removed from security master')
    report = {
        'status': 'PASS' if not errors else 'FAIL', 'as_of_date': as_of_date,
        'table_counts': {name: len(frame) for name, frame in tables.items()},
        'market_coverage_120d': coverage, 'st_count': st_count,
        'errors': errors, 'warnings': warnings, 'generated_at_utc': utc_now_iso(),
    }
    write_json(input_dir / 'live_bundle_validation.json', report)
    return report


def validate_output(output_dir: Path, mode: str) -> dict:
    manifest_path = output_dir / 'run_manifest.json'
    if not manifest_path.exists():
        return {'status': 'FAIL', 'errors': ['missing run_manifest.json']}
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    errors = []
    if mode == 'live' and ('FIXTURE' in str(manifest.get('mode')) or manifest.get('investment_use') == 'PROHIBITED'):
        errors.append('fixture output is prohibited in live mode')
    for name in ['screening_scores.csv', 'shortlist.csv', 'reos_bridge/ascope_to_reos_candidates.csv']:
        if not (output_dir / name).exists():
            errors.append(f'missing output {name}')
    return {'status': 'PASS' if not errors else 'FAIL', 'errors': errors, 'manifest': manifest}
