from __future__ import annotations

import numpy as np
import pandas as pd


def percentile(series: pd.Series, *, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce')
    if values.notna().sum() <= 1:
        return pd.Series(50.0, index=series.index)
    ranks = values.rank(pct=True, method='average') * 100
    if not higher_is_better:
        ranks = 100 - ranks
    return ranks.fillna(25.0)


def score(frame: pd.DataFrame, settings: dict) -> pd.DataFrame:
    value = frame.copy()
    value['change_strength'] = (
        percentile(value['revenue_acceleration']) * 0.35
        + percentile(value['profit_yoy']) * 0.25
        + percentile(value['gross_margin_delta']) * 0.25
        + percentile(value['momentum_120_20']) * 0.15
    )
    evidence_map = {'LEAD': 20, 'MAPPED': 40, 'QUALIFICATION': 55, 'CONTRACTED': 70, 'CAPACITY_READY': 80, 'REVENUE_VISIBLE': 90, 'ECONOMICS_PROVEN': 100, 'INVALIDATED': 0}
    value['evidence_maturity'] = value.get('evidence_stage', pd.Series('MAPPED', index=value.index)).map(evidence_map).fillna(20)
    value['expectation_gap'] = percentile(value['revenue_acceleration']) * 0.6 + percentile(value['momentum_120_20'], higher_is_better=False) * 0.4
    value['catalyst_clarity'] = value.get('catalyst_score', pd.Series(45.0, index=value.index)).fillna(45.0)
    value['valuation_odds'] = (
        percentile(value['net_cash_to_assets']) * 0.35
        + percentile(value['debt_to_equity'], higher_is_better=False) * 0.35
        + percentile(value['max_drawdown_120d'], higher_is_better=False) * 0.30
    )
    value['financial_quality'] = (
        percentile(value['cash_conversion'].clip(-5, 5)) * 0.35
        + percentile(value['gross_margin_delta']) * 0.25
        + percentile(value['debt_to_equity'], higher_is_better=False) * 0.25
        + percentile(value['receivable_to_revenue'], higher_is_better=False) * 0.15
    )
    value['risk_resilience'] = (
        percentile(value['volatility_60d'], higher_is_better=False) * 0.35
        + percentile(value['max_drawdown_120d'], higher_is_better=False) * 0.35
        + percentile(value['debt_to_equity'], higher_is_better=False) * 0.30
    )
    value['liquidity_execution'] = percentile(value['median_amount_60d'])
    value['portfolio_fit'] = 65.0
    required = ['revenue_yoy', 'revenue_acceleration', 'profit_yoy', 'gross_margin_delta', 'cash_conversion', 'median_amount_60d', 'volatility_60d', 'momentum_120_20']
    value['data_confidence'] = value[required].notna().mean(axis=1) * 100
    ow = settings['score_weights']['opportunity']
    iw = settings['score_weights']['investability']
    value['opportunity_score'] = sum(value[key] * float(weight) for key, weight in ow.items())
    value['investability_score'] = sum(value[key] * float(weight) for key, weight in iw.items())
    confidence = (value['data_confidence'] / 100).clip(0.25, 1.0)
    archetype = (value['primary_archetype_score'] / 100).clip(0.35, 1.0)
    value['research_priority'] = np.sqrt(value['opportunity_score'] * value['investability_score']) * confidence * archetype
    value.loc[value['hard_gate_status'] == 'BLOCK', 'research_priority'] = 0
    value['replication_risk'] = 100 - value['risk_resilience'] * 0.45 - value['liquidity_execution'] * 0.25 - value['data_confidence'] * 0.30
    return value
