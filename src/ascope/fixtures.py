from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ascope.io import utc_now_iso, write_frame, write_json


def generate(output_dir: Path, as_of_date: str = '2026-07-29', count: int = 120, seed: int = 20260729) -> dict:
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    codes = []
    for i in range(count):
        if i % 5 == 0:
            code, exchange, board = f'688{i:03d}', 'SSE', 'STAR'
        elif i % 5 == 1:
            code, exchange, board = f'600{i:03d}', 'SSE', 'SSE_MAIN'
        elif i % 5 == 2:
            code, exchange, board = f'300{i:03d}', 'SZSE', 'CHINEXT'
        elif i % 5 == 3:
            code, exchange, board = f'000{i:03d}', 'SZSE', 'SZSE_MAIN'
        else:
            code, exchange, board = f'920{i:03d}', 'BSE', 'BSE'
        codes.append((code, exchange, board))
    industries = ['软件', '电子', '机械设备', '银行', '有色金属', '医药生物', '电力设备']
    master_rows = []
    for i, (code, exchange, board) in enumerate(codes):
        master_rows.append({
            'security_id': f'{exchange}.{code}', 'code': code,
            'name': ('ST测试' if i in {7, 44} else f'测试公司{i:03d}'),
            'exchange': exchange, 'board': board, 'status': 'LISTED',
            'is_st': i in {7, 44}, 'list_date': f'{2010 + i % 15}-01-01',
            'as_of_date': as_of_date, 'industry': industries[i % len(industries)],
            'source_id': 'FIXTURE_GENERATOR', 'source_url': '',
            'retrieved_at_utc': utc_now_iso(), 'data_mode': 'FIXTURE_TEST_ONLY',
        })
    master = pd.DataFrame(master_rows)
    quarter_rows = []
    periods = pd.period_range('2024Q3', periods=8, freq='Q')
    for i, row in master.iterrows():
        base = rng.uniform(3e8, 5e9)
        growth = rng.uniform(-0.15, 0.45)
        margin = rng.uniform(0.15, 0.55)
        for q, period in enumerate(periods):
            revenue = base * ((1 + growth / 4) ** q) * rng.uniform(0.94, 1.06)
            gross = revenue * np.clip(margin + q * rng.uniform(-0.005, 0.012), 0.05, 0.8)
            profit = gross * rng.uniform(0.08, 0.35) - rng.uniform(0, 5e7)
            ocf = profit * rng.uniform(0.55, 1.35)
            quarter_rows.append({
                'security_id': row.security_id,
                'report_period': period.end_time.date().isoformat(),
                'published_at': (period.end_time + pd.Timedelta(days=35 + i % 25)).date().isoformat(),
                'available_at': (period.end_time + pd.Timedelta(days=35 + i % 25)).date().isoformat(),
                'revenue': revenue, 'gross_profit': gross, 'net_profit_parent': profit,
                'deducted_net_profit': profit * rng.uniform(0.85, 1.0),
                'operating_cash_flow': ocf, 'capex': revenue * rng.uniform(0.02, 0.18),
                'total_assets': base * rng.uniform(1.2, 3.0),
                'total_equity': base * rng.uniform(0.5, 1.5),
                'cash': base * rng.uniform(0.05, 0.45),
                'interest_bearing_debt': base * rng.uniform(0.0, 0.8),
                'accounts_receivable': revenue * rng.uniform(0.08, 0.35),
                'inventory': revenue * rng.uniform(0.05, 0.32),
                'contract_liabilities': revenue * rng.uniform(0.01, 0.25),
                'goodwill': base * rng.uniform(0, 0.2),
                'diluted_share_count': rng.uniform(1e8, 2e9),
                'source_id': 'FIXTURE_GENERATOR', 'source_url': '',
                'data_mode': 'FIXTURE_TEST_ONLY',
            })
    quarterly = pd.DataFrame(quarter_rows)
    annual = quarterly.groupby('security_id', as_index=False).tail(1).copy()
    annual['audit_opinion'] = 'STANDARD_UNQUALIFIED'
    annual['internal_control_opinion'] = 'PASS'
    annual.loc[annual.index[:1], 'audit_opinion'] = 'DISCLAIMER'
    dates = pd.bdate_range(end=as_of_date, periods=190)
    market_rows = []
    for i, row in master.iterrows():
        returns = rng.normal(0.0005 + (i % 9) * 0.00008, 0.018 + (i % 7) * 0.002, len(dates))
        close = rng.uniform(5, 80) * np.exp(np.cumsum(returns))
        amount = rng.lognormal(mean=np.log(2e7 + (i % 12) * 6e6), sigma=0.5, size=len(dates))
        if i in {9, 71}:
            amount *= 0.03
        for date, price, ret, value in zip(dates, close, returns, amount, strict=True):
            market_rows.append({
                'security_id': row.security_id, 'trade_date': date.date().isoformat(),
                'open': price * (1 - ret / 2), 'high': price * 1.02, 'low': price * 0.98,
                'close': price, 'prev_close': price / (1 + ret), 'pct_change': ret * 100,
                'volume': value / max(price, 0.1), 'amount_cny': value,
                'turnover_rate': rng.uniform(0.2, 8), 'market_cap_cny': price * rng.uniform(2e8, 3e9),
                'float_market_cap_cny': price * rng.uniform(1e8, 2e9),
                'available_at': date.date().isoformat(), 'source_id': 'FIXTURE_GENERATOR',
                'source_url': '', 'data_mode': 'FIXTURE_TEST_ONLY',
            })
    market = pd.DataFrame(market_rows)
    write_frame(master, output_dir / 'security_master.csv')
    write_frame(quarterly, output_dir / 'financial_quarterly.csv')
    write_frame(annual, output_dir / 'financial_annual.csv')
    write_frame(market, output_dir / 'market_data.csv')
    manifest = {
        'status': 'PASS_FIXTURE_GENERATED', 'mode': 'FIXTURE_TEST_ONLY',
        'investment_use': 'PROHIBITED', 'security_count': len(master),
        'as_of_date': as_of_date, 'seed': seed, 'generated_at_utc': utc_now_iso(),
    }
    write_json(output_dir / 'fixture_manifest.json', manifest)
    return manifest
