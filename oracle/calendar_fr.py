"""French public holidays + the calendar facts the owner says matter."""
from datetime import date, timedelta

HOLIDAYS = {date(*d) for d in [
    (2025, 1, 1), (2025, 4, 21), (2025, 5, 1), (2025, 5, 8), (2025, 5, 29), (2025, 6, 9),
    (2025, 7, 14), (2025, 8, 15), (2025, 11, 1), (2025, 11, 11), (2025, 12, 25),
    (2026, 1, 1), (2026, 4, 6), (2026, 5, 1), (2026, 5, 8), (2026, 5, 14), (2026, 5, 25),
    (2026, 7, 14), (2026, 8, 15), (2026, 11, 1), (2026, 11, 11), (2026, 12, 25),
]}


def before_holiday(d: date) -> bool:
    """Owner: the day before a public holiday is full."""
    return d + timedelta(days=1) in HOLIDAYS


def start_of_month(d: date) -> bool:
    """Owner: the start of the month is always busier (we take days 1-10)."""
    return d.day <= 10


def next_date_for(weekday: int, today: date | None = None) -> date:
    """'Friday' -> the next Friday (today counts if it is Friday)."""
    today = today or date.today()
    return today + timedelta(days=(weekday - today.weekday()) % 7)
