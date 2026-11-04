"""Generate SYNTHETIC evening data from the owner's rules (the owner asked us not to use real data).

Owner's rules (told to Donel, 2026-11-04):
  - lunch + evening together are about 30 guests; the evening alone is around 20
  - the restaurant is full at 30 guests; it is never closed
  - service: always 1 person; kitchen: 1 cook per 10 guests, at most 3 (takeaway is also done by the kitchen)
  - busy: Monday, Thursday, Friday, Saturday; Wednesday depends; Tuesday quiet;
    Sunday quiet UNLESS there is a biryani special
  - the day before a public holiday is full
  - the start of the month is always busier
  - cool weather without wind: the smell of food spreads in the street -> more people;
    very cold: average; rain: average plus walk-in customers sheltering from the rain

Numbers marked ASSUMPTION are my guesses, to confirm with the owner.

The file is deliberately messy, like a real till export:
mixed date formats, numbers stored as text, typos (250 instead of 25), duplicates, empty cells.
"""
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from oracle.calendar_fr import before_holiday, start_of_month  # noqa: E402

random.seed(42)
OUT = Path(__file__).parent / "raw" / "sales.csv"
SEATS = 30
BASE = {0: 22, 1: 13, 2: 19, 3: 22, 4: 24, 5: 25, 6: 14}  # evening, Mon..Sun
BIRYANI_SUNDAY_SHARE = 0.4    # ASSUMPTION: 4 Sundays in 10 have the biryani special


def weather(d: date) -> tuple[float, float, int]:
    """Paris-like season: ~5 C in mid-January, ~22 C in mid-July. Returns temp, wind km/h, rain."""
    season = math.cos(2 * math.pi * (d.timetuple().tm_yday - 15) / 365)
    temp = round(13.5 - 8.5 * season + random.gauss(0, 3), 1)
    wind = round(abs(random.gauss(12, 8)), 1)
    rain = 1 if random.random() < 0.3 else 0
    return temp, wind, rain


def staff_needed(guests: int) -> int:
    return 1 + min(3, math.ceil(guests / 10))


def evening_guests(d: date, temp: float, wind: float, rain: int, special: int) -> int:
    wd = d.weekday()
    g = BASE[wd] * random.gauss(1.0, 0.12)
    if wd == 6 and special:
        g += 10                                 # biryani Sunday becomes busy
    if 5 <= temp < 12 and wind < 15:
        g += 4                                  # cool + calm: smell spreads (ASSUMPTION: 5-12 C, <15 km/h)
    if rain:
        g += 2                                  # walk-ins sheltering from rain
    if start_of_month(d):
        g += 3                                  # payday
    if before_holiday(d):
        g = SEATS                               # full
    return max(0, min(SEATS, round(g)))


def main():
    rows = ["date,guests,staff,rain,temp_c,wind_kmh,special,note"]
    d = date(2025, 1, 6)
    while d <= date(2026, 10, 31):
        temp, wind, rain = weather(d)
        special = 1 if d.weekday() == 6 and random.random() < BIRYANI_SUNDAY_SHARE else 0
        g = evening_guests(d, temp, wind, rain, special)
        shown = str(g)
        if random.random() < 0.015:
            shown = str(g * 10)                 # typo: 250 instead of 25
        if random.random() < 0.08:
            shown = f" {shown} "                # number stored as text
        if random.random() < 0.02:
            shown = ""                          # missing value
        ds = d.isoformat() if random.random() < 0.8 else d.strftime("%d/%m/%Y")
        sp = "biryani" if special else ""
        rows.append(f"{ds},{shown},{staff_needed(g)},{rain},{temp},{wind},{sp},")
        if random.random() < 0.02:
            rows.append(rows[-1])               # line exported twice
        d += timedelta(days=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(rows) + "\n")
    print(f"wrote {len(rows) - 1} rows to {OUT}")


if __name__ == "__main__":
    main()
