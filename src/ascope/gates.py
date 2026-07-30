from __future__ import annotations

import numpy as np
import pandas as pd

BAD_AUDIT = {'DISCLAIMER', 'ADVERSE', '无法表示意见', '否定意见'}


def apply(frame: pd.DataFrame, annual: pd.DataFrame, settings: dict) -> pd.DataFrame:
    result = frame.copy()
    latest_annual = annual.sort_values(['security_id', 'report_period']).groupby('security_id', as_index=False).tail(1)
    annual_cols = [c for c in ['security_id', 'audit_opinion', 'internal_control_opinion'] if c in latest_annual]
    if annual_cols:
        result = result.merge(latest_annual[annual_cols], on='security_id', how='left')
    minimum = float(settings['gates']['minimum_median_amount_60d_cny'])
    reasons = []
    statuses = []
    for _, row in result.iterrows():
        block = []
        review = []
        if bool(row.get('is_st', False)):
            block.append('ST_OR_STAR_ST')
        if str(row.get('status', 'LISTED')) not in {'LISTED', 'TRADING'}:
            block.append('NOT_LISTED_OR_TRADING')
        if float(row.get('equity', np.nan)) < 0:
            block.append('NEGATIVE_EQUITY')
        if str(row.get('audit_opinion', '')) in BAD_AUDIT:
            block.append('BAD_AUDIT_OPINION')
        amount = float(row.get('median_amount_60d', np.nan))
        if not np.isfinite(amount) or amount < minimum:
            block.append('INSUFFICIENT_LIQUIDITY')
        if int(row.get('market_day_count', 0)) < 120:
            review.append('SHORT_TRADING_HISTORY')
        if float(row.get('debt_to_equity', 0) or 0) > 1.5:
            review.append('HIGH_LEVERAGE')
        if block:
            statuses.append('BLOCK')
            reasons.append(';'.join(block + review))
        elif review:
            statuses.append('HIGH_RISK')
            reasons.append(';'.join(review))
        else:
            statuses.append('PASS')
            reasons.append('')
    result['hard_gate_status'] = statuses
    result['hard_gate_reasons'] = reasons
    return result
