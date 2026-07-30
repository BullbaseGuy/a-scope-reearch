from __future__ import annotations

import numpy as np
import pandas as pd

FINANCIAL_KEYWORDS = ('银行', '保险', '证券', '多元金融')
RESOURCE_KEYWORDS = ('煤炭', '石油', '有色', '钢铁', '基础化工')


def route(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in frame.iterrows():
        industry = str(row.get('industry', ''))
        scores = {name: 0.0 for name in [
            'GROWTH_ACCEL', 'BOTTLENECK', 'CYCLE_REVERSAL', 'RAMP', 'TURNAROUND',
            'SPECIAL', 'POLICY_CAPEX', 'CAPITAL_RETURN', 'FINANCIAL', 'RESOURCE',
        ]}
        if any(key in industry for key in FINANCIAL_KEYWORDS):
            scores['FINANCIAL'] = 100
        elif any(key in industry for key in RESOURCE_KEYWORDS):
            scores['RESOURCE'] = 85
        revenue_yoy = float(row.get('revenue_yoy', np.nan))
        acceleration = float(row.get('revenue_acceleration', np.nan))
        profit_yoy = float(row.get('profit_yoy', np.nan))
        margin_delta = float(row.get('gross_margin_delta', np.nan))
        capex = float(row.get('capex_to_revenue', np.nan))
        contracts = float(row.get('contract_liability_to_revenue', np.nan))
        if np.isfinite(revenue_yoy):
            scores['GROWTH_ACCEL'] += max(0, min(60, revenue_yoy * 100))
        if np.isfinite(acceleration):
            scores['GROWTH_ACCEL'] += max(0, min(40, acceleration * 200))
            scores['CYCLE_REVERSAL'] += max(0, min(50, acceleration * 250))
        if np.isfinite(profit_yoy) and profit_yoy > 0.3:
            scores['GROWTH_ACCEL'] += 20
        if np.isfinite(margin_delta):
            scores['BOTTLENECK'] += max(0, min(70, margin_delta * 800))
            scores['TURNAROUND'] += max(0, min(50, margin_delta * 600))
        if np.isfinite(capex):
            scores['RAMP'] += max(0, min(50, capex * 250))
            scores['POLICY_CAPEX'] += max(0, min(35, capex * 180))
        if np.isfinite(contracts):
            scores['RAMP'] += max(0, min(50, contracts * 250))
        if float(row.get('net_cash_to_assets', 0) or 0) > 0.15:
            scores['CAPITAL_RETURN'] += 45
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        primary, primary_score = ordered[0]
        secondary, secondary_score = ordered[1]
        if primary_score <= 0:
            primary, primary_score = 'GROWTH_ACCEL', 1.0
        rows.append({
            'security_id': row['security_id'], 'primary_archetype': primary,
            'primary_archetype_score': primary_score,
            'secondary_archetype': secondary, 'secondary_archetype_score': secondary_score,
            'routing_confidence': min(100.0, max(20.0, primary_score - secondary_score + 50)),
        })
    return pd.DataFrame(rows)
