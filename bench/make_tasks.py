"""Block 9: build questions about PAST nights whose answers we compute ourselves (known answers).

    python -m bench.make_tasks     # writes bench/tasks.json
"""
import json
from pathlib import Path

from oracle.cleaning import load_clean

OUT = Path(__file__).parent / "tasks.json"


def build(df) -> list[dict]:
    t = []
    last = df.iloc[-1]
    t.append({"q": f"How many guests did we have on {last.date:%Y-%m-%d}?",
              "answer": int(last.guests), "type": "number", "tol": 0})
    for month in ("2026-09", "2026-10"):
        m = df[df.date.dt.strftime("%Y-%m") == month]
        t.append({"q": f"What was the average number of guests on Fridays in {month}? Round to 1 decimal.",
                  "answer": round(float(m[m.weekday == 4].guests.mean()), 1), "type": "number", "tol": 0.5})
        t.append({"q": f"How many guests in total in {month}?",
                  "answer": int(m.guests.sum()), "type": "number", "tol": 0})
    y25 = df[df.date.dt.year == 2025]
    by_day = y25.groupby("day_name").guests.mean()
    t.append({"q": "Which day of the week had the highest average number of guests in 2025?",
              "answer": by_day.idxmax(), "type": "text"})
    t.append({"q": "Which day of the week had the lowest average number of guests in 2025?",
              "answer": by_day.idxmin(), "type": "text"})
    t.append({"q": "How many nights were completely full (30 guests) in 2025?",
              "answer": int((y25.guests == 30).sum()), "type": "number", "tol": 0})
    sun = y25[y25.weekday == 6]
    t.append({"q": "In 2025, what was the average number of guests on Sundays WITH the biryani special? Round to 1 decimal.",
              "answer": round(float(sun[sun.biryani == 1].guests.mean()), 1), "type": "number", "tol": 0.5})
    t.append({"q": "In 2025, what was the average number of guests on Sundays WITHOUT the biryani special? Round to 1 decimal.",
              "answer": round(float(sun[sun.biryani == 0].guests.mean()), 1), "type": "number", "tol": 0.5})
    t.append({"q": "How many nights before a public holiday were there in 2025?",
              "answer": int(y25.before_holiday.sum()), "type": "number", "tol": 0})
    t.append({"q": "How many nights had more than 20 guests (3 cooks needed) in 2026?",
              "answer": int((df[df.date.dt.year == 2026].guests > 20).sum()), "type": "number", "tol": 0})
    return t


if __name__ == "__main__":
    tasks = build(load_clean())
    OUT.write_text(json.dumps(tasks, indent=2))
    print(f"{len(tasks)} tasks written to {OUT}")
