import pandas as pd

from ascope.gates import apply


def test_st_is_blocked():
    frame = pd.DataFrame([{'security_id':'SZSE.000001','is_st':True,'status':'LISTED','equity':1,'median_amount_60d':1e8,'market_day_count':190,'debt_to_equity':0.2}])
    annual = pd.DataFrame([{'security_id':'SZSE.000001','report_period':'2025-12-31','audit_opinion':'STANDARD_UNQUALIFIED','internal_control_opinion':'PASS'}])
    out = apply(frame, annual, {'gates':{'minimum_median_amount_60d_cny':3e6}})
    assert out.iloc[0]['hard_gate_status'] == 'BLOCK'
