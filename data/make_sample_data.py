"""Generate a FAKE sales file so the project runs before the real export arrives.

PLACEHOLDER ONLY. Block 6 needs real data: replace data/raw/sales.csv with the
real (anonymised) export from the restaurant, then delete this script.

The fake file is deliberately messy, like a real till export:
mixed date formats, numbers stored as text, duplicates, refunds, empty cells.
"""
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent / "raw" / "sales.csv"

BASE = {0: 45, 1: 50, 2: 55, 3: 65, 4: 95, 5: 105, 6: 70}  # Mon..Sun


def main():
    rows = ["date,orders,staff,rain,event,note"]
    d = date(2025, 1, 6)
    while d <= date(2026, 10, 31):
        wd = d.weekday()
        rain = 1 if random.random() < 0.3 else 0
        event = "match" if wd in (1, 2, 5, 6) and random.random() < 0.12 else ""
        orders = BASE[wd] * random.gauss(1.0, 0.12)
        if event:
            orders *= 1.3  # the manager's "match night" rule
        if rain and wd == 6:
            orders *= 0.7  # "rainy Sundays are dead"
        orders = max(0, round(orders))
        staff = 3 if orders < 80 else 4
        note = ""

        if wd == 0 and random.random() < 0.5:  # closed some Mondays
            orders, staff, note = 0, 0, "closed"
        ds = d.isoformat() if random.random() < 0.8 else d.strftime("%d/%m/%Y")
        o = str(orders) if random.random() < 0.9 else f" {orders} "
        if random.random() < 0.02:
            o = ""  # missing value
        rows.append(f"{ds},{o},{staff},{rain},{event},{note}")
        if random.random() < 0.02:
            rows.append(rows[-1])  # duplicate line
        if random.random() < 0.01:
            rows.append(f"{ds},-3,{staff},{rain},{event},refund")
        d += timedelta(days=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(rows) + "\n")
    print(f"wrote {len(rows) - 1} rows to {OUT}")


if __name__ == "__main__":
    main()
