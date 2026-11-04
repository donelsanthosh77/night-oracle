import pandas as pd

from oracle.cleaning import clean


def raw(rows):
    return pd.DataFrame(rows, columns=["date", "orders", "staff", "rain", "event", "note"])


def test_two_date_formats_are_read():
    df, _ = clean(raw([["2026-01-02", "50", 3, 0, None, None],
                       ["03/01/2026", "60", 3, 0, None, None]]))
    assert list(df["date"].dt.day) == [2, 3]


def test_text_numbers_refunds_duplicates_closed():
    df, log = clean(raw([
        ["2026-01-02", " 50 ", 3, 0, None, None],   # text with spaces -> 50
        ["2026-01-02", " 50 ", 3, 0, None, None],   # duplicate
        ["2026-01-02", "-3", 3, 0, None, "refund"], # refund
        ["2026-01-05", "0", 0, 0, None, "closed"],  # closed day (manager's rule)
        ["2026-01-06", None, 3, 0, None, None],     # missing orders
    ]))
    assert df["orders"].tolist() == [50]
    removed = {s["step"]: s["rows_removed"] for s in log["steps"]}
    assert removed["drop_refunds"] == 1
    assert removed["drop_duplicates"] == 1
    assert removed["drop_closed_days"] == 1
    assert removed["orders_to_number"] == 1
    assert log["rows_in"] == 5 and log["rows_out"] == 1


def test_empty_input():
    df, log = clean(raw([]))
    assert len(df) == 0 and log["rows_out"] == 0
