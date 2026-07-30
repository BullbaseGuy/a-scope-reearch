from __future__ import annotations

import pandas as pd


def assert_point_in_time(frame: pd.DataFrame, signal_column: str = 'signal_date', available_column: str = 'available_at') -> None:
    signal = pd.to_datetime(frame[signal_column], errors='coerce')
    available = pd.to_datetime(frame[available_column], errors='coerce')
    violations = frame[available > signal]
    if not violations.empty:
        raise ValueError(f'point-in-time violation rows={len(violations)}')


def walk_forward_dates(dates: pd.Series, train_years: int = 3, test_months: int = 6) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    values = pd.to_datetime(dates, errors='coerce').dropna().sort_values().unique()
    if len(values) == 0:
        return []
    start = pd.Timestamp(values[0])
    end = pd.Timestamp(values[-1])
    splits = []
    train_start = start
    while True:
        train_end = train_start + pd.DateOffset(years=train_years) - pd.Timedelta(days=1)
        test_start = train_end + pd.Timedelta(days=1)
        test_end = test_start + pd.DateOffset(months=test_months) - pd.Timedelta(days=1)
        if test_end > end:
            break
        splits.append((train_start, train_end, test_start, test_end))
        train_start += pd.DateOffset(months=test_months)
    return splits
