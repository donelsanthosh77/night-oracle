import numpy as np
import pandas as pd
import pytest

from oracle.model import OrdersModel, baseline_predict, mae, split_by_time


def fake(n_weeks=20):
    """Known answer: orders = 50 + 10*weekday, +30 on match nights, no noise."""
    dates = pd.date_range("2026-01-05", periods=7 * n_weeks, freq="D")  # starts on a Monday
    wd = dates.weekday
    match = (np.arange(len(dates)) % 5 == 0)
    return pd.DataFrame({"date": dates, "weekday": wd, "rain": 0,
                         "event": np.where(match, "match", ""),
                         "orders": 50 + 10 * wd + 30 * match})


def test_regression_recovers_known_rule():
    m = OrdersModel().fit(fake())
    assert m.predict(4) == pytest.approx(90)            # Friday, no match
    assert m.predict(4, match=1) == pytest.approx(120)  # Friday + match
    assert m.resid_std == pytest.approx(0, abs=1e-6)


def test_model_beats_baseline_when_matches_matter():
    train, test = split_by_time(fake(), test_weeks=4)
    m = OrdersModel().fit(train)
    assert mae(test.orders, m.predict_df(test)) < mae(test.orders, baseline_predict(train, test))


def test_split_never_puts_future_in_train():
    train, test = split_by_time(fake(), test_weeks=4)
    assert train.date.max() < test.date.min()


def test_mae_known_values_and_empty():
    assert mae([1, 2, 3], [1, 2, 5]) == pytest.approx(2 / 3)
    with pytest.raises(ValueError):
        mae([], [])
