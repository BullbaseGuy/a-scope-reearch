from ascope.config import load_settings


def test_satellite_account_hard_limits():
    value = load_settings()
    assert value.account['nav_cny'] == 5_000_000
    assert value.account['margin_leverage_allowed'] is False
    assert value.account['st_executable_allowed'] is False
