from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return a.astype(float) / b.astype(float).replace(0, np.nan)


def financial_features(quarterly: pd.DataFrame, as_of_date: str) -> pd.DataFrame:
    q = quarterly.copy()
    q['available_at'] = pd.to_datetime(q['available_at'], errors='coerce')
    q['report_period'] = pd.to_datetime(q['report_period'], errors='coerce')
    q = q[q['available_at'] <= pd.Timestamp(as_of_date)].sort_values(['security_id', 'report_period'])
    rows = []
    for sid, group in q.groupby('security_id'):
        group = group.tail(8).copy()
        latest = group.iloc[-1]
        prev = group.iloc[-2] if len(group) >= 2 else latest
        lag4 = group.iloc[-5] if len(group) >= 5 else group.iloc[0]
        revenue_yoy = (latest['revenue'] / lag4['revenue'] - 1) if lag4['revenue'] else np.nan
        prev_yoy = (prev['revenue'] / group.iloc[-6]['revenue'] - 1) if len(group) >= 6 and group.iloc[-6]['revenue'] else np.nan
        profit_yoy = (latest['deducted_net_profit'] / abs(lag4['deducted_net_profit']) - 1) if lag4['deducted_net_profit'] else np.nan
        gross_margin = latest['gross_profit'] / latest['revenue'] if latest['revenue'] else np.nan
        prev_gross_margin = prev['gross_profit'] / prev['revenue'] if prev['revenue'] else np.nan
        rows.append({
            'security_id': sid,
            'latest_report_period': latest['report_period'].date().isoformat(),
            'revenue_yoy': revenue_yoy,
            'revenue_acceleration': revenue_yoy - prev_yoy if pd.notna(prev_yoy) else np.nan,
            'profit_yoy': profit_yoy,
            'gross_margin': gross_margin,
            'gross_margin_delta': gross_margin - prev_gross_margin,
            'cash_conversion': latest['operating_cash_flow'] / abs(latest['deducted_net_profit']) if latest['deducted_net_profit'] else np.nan,
            'receivable_to_revenue': latest['accounts_receivable'] / latest['revenue'] if latest['revenue'] else np.nan,
            'inventory_to_revenue': latest['inventory'] / latest['revenue'] if latest['revenue'] else np.nan,
            'contract_liability_to_revenue': latest['contract_liabilities'] / latest['revenue'] if latest['revenue'] else np.nan,
            'capex_to_revenue': latest['capex'] / latest['revenue'] if latest['revenue'] else np.nan,
            'debt_to_equity': latest['interest_bearing_debt'] / latest['total_equity'] if latest['total_equity'] else np.nan,
            'net_cash_to_assets': (latest['cash'] - latest['interest_bearing_debt']) / latest['total_assets'] if latest['total_assets'] else np.nan,
            'equity': latest['total_equity'],
            'quarter_count': len(group),
        })
    return pd.DataFrame(rows)


def market_features(market: pd.DataFrame, as_of_date: str) -> pd.DataFrame:
    m = market.copy()
    m['trade_date'] = pd.to_datetime(m['trade_date'], errors='coerce')
    m = m[m['trade_date'] <= pd.Timestamp(as_of_date)].sort_values(['security_id', 'trade_date'])
    rows = []
    for sid, group in m.groupby('security_id'):
        group = group.tail(190)
        close = pd.to_numeric(group['close'], errors='coerce')
        amount = pd.to_numeric(group['amount_cny'], errors='coerce')
        returns = close.pct_change()
        momentum_120_20 = np.nan
        if len(close) >= 121:
            momentum_120_20 = close.iloc[-21] / close.iloc[-121] - 1
        drawdown = close / close.cummax() - 1
        rows.append({
            'security_id': sid,
            'last_trade_date': group.iloc[-1]['trade_date'].date().isoformat(),
            'last_close': close.iloc[-1],
            'median_amount_20d': amount.tail(20).median(),
            'median_amount_60d': amount.tail(60).median(),
            'volatility_60d': returns.tail(60).std() * np.sqrt(252),
            'max_drawdown_120d': drawdown.tail(120).min(),
            'momentum_120_20': momentum_120_20,
            'market_day_count': len(group),
        })
    return pd.DataFrame(rows)
