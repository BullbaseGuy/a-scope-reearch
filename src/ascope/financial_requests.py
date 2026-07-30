from __future__ import annotations

from pathlib import Path

import pandas as pd

from ascope.io import read_frame, utc_now_iso, write_frame, write_json


def build(security_master: Path, output_dir: Path, through: str, batch_size: int = 200) -> dict:
    master = read_frame(security_master)
    rows = []
    for index, row in master.reset_index(drop=True).iterrows():
        batch = index // batch_size + 1
        rows.append({
            'batch_id': f'B{batch:03d}', 'sequence': index + 1,
            'security_id': row['security_id'], 'code': row['code'], 'name': row['name'],
            'exchange': row['exchange'], 'board': row['board'], 'is_st': row.get('is_st', False),
            'request_annual_from': '2019-12-31', 'request_quarterly_from': '2022-03-31',
            'request_through': through, 'required_tables': 'financial_annual;financial_quarterly',
            'status': 'PENDING', 'output_hint': f'financial_exports/B{batch:03d}/{row["code"]}',
        })
    frame = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_frame(frame, output_dir / 'financial_request_manifest.csv')
    for batch_id, group in frame.groupby('batch_id'):
        write_frame(group, output_dir / 'financial_batches' / f'{batch_id}.csv')
    manifest = {'status': 'READY', 'security_count': len(frame), 'batch_size': batch_size, 'batch_count': int(frame['batch_id'].nunique()), 'generated_at_utc': utc_now_iso()}
    write_json(output_dir / 'financial_request_manifest.json', manifest)
    return manifest
