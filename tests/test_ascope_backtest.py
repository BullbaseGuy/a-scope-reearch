import pandas as pd
import pytest

from ascope.backtest import assert_point_in_time, walk_forward_dates


def test_point_in_time_guard():
    frame = pd.DataFrame({'signal_date':['2026-01-01'], 'available_at':['2026-01-02']})
    with pytest.raises(ValueError):
        assert_point_in_time(frame)


def test_walk_forward_splits():
    dates = pd.Series(pd.date_range('2018-01-01','2025-12-31',freq='ME'))
    assert walk_forward_dates(dates)
