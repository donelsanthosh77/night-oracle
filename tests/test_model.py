import numpy as np
import pandas as pd
import pytest

from oracle.model import GuestsModel, baseline_predict, mae, split_by_time


def fake(n_weeks=20):
    """Known answer: guests = 10 + weekday + 4 biryani + 3 start of month, rain changes nothing, no noise."""
    dates = pd.date_range("2026-01-05", periods=7 * n_weeks, freq="D")  # starts on a Monday
    wd = dates.weekday
    i = np.arange(len(dates))
    biryani = ((wd == 6) & (i % 2 == 0)).astype(int)
    som = (dates.day <= 10).astype(int)
    return pd.DataFrame({"date": dates, "weekday": wd, "rain": (i % 3 == 0).astype(int),
                         "temp_c": 20.0, "wind_kmh": 10.0, "biryani": biryani,
                         "before_holiday": 0, "start_of_month": som,
                         "guests": 10 + wd + 4 * biryani + 3 * som})


def test_regression_recovers_known_rules():
    m = GuestsModel().fit(fake())
    assert m.predict(4) == pytest.approx(14)                          # Friday
    assert m.predict(4, start_of_month=1) == pytest.approx(17)        # + start of month
    assert m.predict(6, biryani=1) == pytest.approx(20)               # biryani Sunday
    assert m.predict(4, rain=1) == pytest.approx(14)                  # rain: nothing here
    assert m.resid_std == pytest.approx(0, abs=1e-6)


def test_prediction_never_above_30_seats():
    df = fake()
    df["guests"] = df["guests"] + 25
    assert GuestsModel().fit(df).predict(6, biryani=1) <= 30


def test_model_beats_baseline_when_factors_matter():
    train, test = split_by_time(fake(), test_weeks=4)
    m = GuestsModel().fit(train)
    assert mae(test.guests, m.predict_df(test)) < mae(test.guests, baseline_predict(train, test))


def test_split_never_puts_future_in_train():
    train, test = split_by_time(fake(), test_weeks=4)
    assert train.date.max() < test.date.min()


def test_mae_known_values_and_empty():
    assert mae([1, 2, 3], [1, 2, 5]) == pytest.approx(2 / 3)
    with pytest.raises(ValueError):
        mae([], [])
