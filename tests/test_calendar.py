from datetime import date

from oracle.calendar_fr import before_holiday, next_date_for, start_of_month


def test_before_holiday():
    assert before_holiday(date(2026, 7, 13))       # 14 July
    assert before_holiday(date(2026, 12, 24))      # Christmas
    assert not before_holiday(date(2026, 7, 14))


def test_start_of_month():
    assert start_of_month(date(2026, 11, 1)) and start_of_month(date(2026, 11, 10))
    assert not start_of_month(date(2026, 11, 11))


def test_next_date_for_weekday():
    wed = date(2026, 11, 4)
    assert next_date_for(4, wed) == date(2026, 11, 6)   # next Friday
    assert next_date_for(2, wed) == wed                 # today is Wednesday
    assert next_date_for(1, wed) == date(2026, 11, 10)  # Tuesday next week
