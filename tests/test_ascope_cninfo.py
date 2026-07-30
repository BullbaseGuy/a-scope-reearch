from ascope.adapters.cninfo import classify_exchange_board, is_a_share_code, normalize


def test_code_classification():
    assert classify_exchange_board('688001') == ('SSE','STAR')
    assert classify_exchange_board('300001') == ('SZSE','CHINEXT')
    assert classify_exchange_board('920001') == ('BSE','BSE')
    assert not is_a_share_code('900901')


def test_normalize_cninfo_item():
    row = normalize({'code':'000001','zwjc':'平安银行','orgId':'gssz0000001'}, 'fixture', '2026-07-29', '2026-07-30T00:00:00Z')
    assert row and row['security_id'] == 'SZSE.000001'
