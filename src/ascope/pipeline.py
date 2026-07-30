from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ascope import archetypes, features, gates, scoring
from ascope.config import load_settings
from ascope.io import read_frame, utc_now_iso, write_frame, write_json


def _load_bundle(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = ['security_master.csv', 'financial_quarterly.csv', 'financial_annual.csv', 'market_data.csv']
    missing = [name for name in required if not (input_dir / name).exists()]
    if missing:
        raise ValueError(f'missing required bundle files: {missing}')
    return tuple(read_frame(input_dir / name) for name in required)  # type: ignore[return-value]


def _evidence_stage(master: pd.DataFrame, financial: pd.DataFrame) -> pd.DataFrame:
    latest = financial.sort_values(['security_id', 'report_period']).groupby('security_id', as_index=False).tail(1)
    rows = []
    for _, row in master.iterrows():
        match = latest[latest['security_id'] == row['security_id']]
        stage = 'LEAD'
        catalyst = 35.0
        if not match.empty:
            item = match.iloc[0]
            stage = 'MAPPED'
            if float(item.get('contract_liabilities', 0) or 0) > 0:
                stage, catalyst = 'CONTRACTED', 65.0
            if float(item.get('capex', 0) or 0) > 0 and stage == 'CONTRACTED':
                stage, catalyst = 'CAPACITY_READY', 72.0
            if float(item.get('revenue', 0) or 0) > 0:
                stage = max(stage, 'REVENUE_VISIBLE', key=lambda x: ['LEAD','MAPPED','QUALIFICATION','CONTRACTED','CAPACITY_READY','REVENUE_VISIBLE','ECONOMICS_PROVEN'].index(x))
        rows.append({'security_id': row['security_id'], 'evidence_stage': stage, 'catalyst_score': catalyst})
    return pd.DataFrame(rows)


def run(input_dir: Path, output_dir: Path, as_of_date: str, *, mode: str) -> dict:
    settings = load_settings()
    master, quarterly, annual, market = _load_bundle(input_dir)
    if mode == 'live':
        for name, frame in [('security_master', master), ('financial_quarterly', quarterly), ('financial_annual', annual), ('market_data', market)]:
            if 'data_mode' in frame and frame['data_mode'].astype(str).str.contains('FIXTURE').any():
                raise ValueError(f'fixture contamination in LIVE mode: {name}')
    ff = features.financial_features(quarterly, as_of_date)
    mf = features.market_features(market, as_of_date)
    merged = master.merge(ff, on='security_id', how='left').merge(mf, on='security_id', how='left')
    evidence = _evidence_stage(master, quarterly)
    merged = merged.merge(evidence, on='security_id', how='left')
    gated = gates.apply(merged, annual, settings.screening)
    assignments = archetypes.route(gated)
    scored = scoring.score(gated.merge(assignments, on='security_id', how='left'), settings.screening)
    thresholds = settings.screening['thresholds']
    eligible = scored[scored['hard_gate_status'] != 'BLOCK'].copy()
    shortlist = eligible[
        (eligible['opportunity_score'] >= float(thresholds['research_opportunity_score']))
        & (eligible['investability_score'] >= float(thresholds['research_investability_score']))
        & (eligible['data_confidence'] >= float(thresholds['research_data_confidence']))
    ].sort_values('research_priority', ascending=False)
    max_research = int(settings.screening['soft_targets']['research_queue'][1])
    shortlist = shortlist.head(max_research)
    stage_order = {'LEAD': 0, 'MAPPED': 1, 'QUALIFICATION': 2, 'CONTRACTED': 3, 'CAPACITY_READY': 4, 'REVENUE_VISIBLE': 5, 'ECONOMICS_PROVEN': 6}
    shortlist['open_p0_count'] = (
        (shortlist['data_confidence'] < 80).astype(int)
        + (shortlist['evidence_stage'].map(stage_order).fillna(0) < 2).astype(int)
        + (shortlist['median_amount_60d'] < float(settings.screening['gates']['standard_liquidity_cny'])).astype(int)
    )
    shortlist['next_data_request'] = '核验一手公告、最新财务、稀释后股本、反向估值与失效日期'
    shortlist['screening_status'] = 'RESEARCH_QUEUE'
    bridge_cols = [
        'security_id','code','name','exchange','board','industry','primary_archetype',
        'evidence_stage','opportunity_score','investability_score','research_priority',
        'replication_risk','data_confidence','hard_gate_status','hard_gate_reasons',
        'open_p0_count','next_data_request',
    ]
    bridge = shortlist[[c for c in bridge_cols if c in shortlist]].copy()
    bridge['reos_status'] = 'RESEARCH' if len(bridge) else pd.Series(dtype='object')
    output_dir.mkdir(parents=True, exist_ok=True)
    write_frame(ff, output_dir / 'financial_features.csv')
    write_frame(mf, output_dir / 'market_features.csv')
    write_frame(gated, output_dir / 'screening_input_snapshot.csv')
    write_frame(assignments, output_dir / 'archetype_assignment.csv')
    write_frame(scored, output_dir / 'screening_scores.csv')
    write_frame(shortlist, output_dir / 'shortlist.csv')
    write_frame(bridge, output_dir / 'reos_bridge' / 'ascope_to_reos_candidates.csv')
    manifest = {
        'status': 'PASS_FIXTURE_TEST_ONLY' if mode == 'fixture' else 'PASS_LIVE_SCREENING',
        'mode': 'FIXTURE_TEST_ONLY' if mode == 'fixture' else 'LIVE',
        'investment_use': 'PROHIBITED' if mode == 'fixture' else 'RESEARCH_ONLY',
        'as_of_date': as_of_date,
        'security_count': len(master),
        'eligible_count': len(eligible),
        'shortlist_count': len(shortlist),
        'generated_at_utc': utc_now_iso(),
    }
    write_json(output_dir / 'run_manifest.json', manifest)
    return manifest
