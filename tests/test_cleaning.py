import pandas as pd

from oracle.cleaning import clean

COLS = ["date", "guests", "staff", "rain", "temp_c", "wind_kmh", "special", "note"]


def raw(rows):
    return pd.DataFrame(rows, columns=COLS)


def row(d, g, special=None):
    return [d, g, 3, 0, 8.0, 5.0, special, None]


def test_two_date_formats_are_read():
    df, _ = clean(raw([row("2026-01-02", "20"), row("03/01/2026", "25")]))
    assert list(df["date"].dt.day) == [2, 3]
    assert list(df["day_name"]) == ["Friday", "Saturday"]


def test_text_numbers_typos_duplicates_missing():
    df, log = clean(raw([
        row("2026-01-02", " 20 "),   # text with spaces -> 20
        row("2026-01-02", " 20 "),   # duplicate
        row("2026-01-03", "250"),    # typo: owner says max 30
        row("2026-01-06", None),     # missing guests
    ]))
    assert df["guests"].tolist() == [20]
    removed = {s["step"]: s["rows_removed"] for s in log["steps"]}
    assert removed["drop_duplicates"] == 1
    assert removed["drop_impossible_counts"] == 1
    assert removed["guests_to_number"] == 1
    assert log["rows_in"] == 4 and log["rows_out"] == 1


def test_calendar_columns():
    df, _ = clean(raw([row("2026-11-10", "30"), row("2026-11-15", "24", "biryani")]))
    assert df["before_holiday"].tolist() == [1, 0]   # 11 November is a holiday
    assert df["start_of_month"].tolist() == [1, 0]
    assert df["biryani"].tolist() == [0, 1]
    assert df["guests"].tolist() == [30, 24]          # full restaurant is kept


def test_empty_input():
    df, log = clean(raw([]))
    assert len(df) == 0 and log["rows_out"] == 0
