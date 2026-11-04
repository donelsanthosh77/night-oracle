"""Block 9: build questions about PAST sales whose answers we compute ourselves (known answers).

    python -m bench.make_tasks     # writes bench/tasks.json
"""
import json
from pathlib import Path

from oracle.cleaning import load_clean

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
OUT = Path(__file__).parent / "tasks.json"


def build(df) -> list[dict]:
    t = []
    last = df.iloc[-1]
    t.append({"q": f"How many orders did we have on {last.date:%Y-%m-%d}?",
              "answer": int(last.orders), "type": "number", "tol": 0})
    for month in ("2026-09", "2026-10"):
        m = df[df.date.dt.strftime("%Y-%m") == month]
        t.append({"q": f"What was the average number of orders on Fridays in {month}? Round to 1 decimal.",
                  "answer": round(float(m[m.weekday == 4].orders.mean()), 1), "type": "number", "tol": 0.5})
        t.append({"q": f"How many orders in total in {month}?",
                  "answer": int(m.orders.sum()), "type": "number", "tol": 0})
    y25 = df[df.date.dt.year == 2025]
    t.append({"q": "Which weekday had the highest average orders in 2025?",
              "answer": DAYS[int(y25.groupby("weekday").orders.mean().idxmax())], "type": "text"})
    t.append({"q": "How many match nights were there in 2025?",
              "answer": int((y25.event == "match").sum()), "type": "number", "tol": 0})
    t.append({"q": "What was the busiest single night in 2025 (number of orders)?",
              "answer": int(y25.orders.max()), "type": "number", "tol": 0})
    t.append({"q": "On rainy Sundays in 2025, what was the average number of orders? Round to 1 decimal.",
              "answer": round(float(y25[(y25.weekday == 6) & (y25.rain == 1)].orders.mean()), 1),
              "type": "number", "tol": 0.5})
    t.append({"q": "How many nights had more than 90 orders in 2026?",
              "answer": int((df[df.date.dt.year == 2026].orders > 90).sum()), "type": "number", "tol": 0})
    t.append({"q": "Which weekday had the lowest average orders in 2026?",
              "answer": DAYS[int(df[df.date.dt.year == 2026].groupby("weekday").orders.mean().idxmin())],
              "type": "text"})
    return t


if __name__ == "__main__":
    tasks = build(load_clean())
    OUT.write_text(json.dumps(tasks, indent=2))
    print(f"{len(tasks)} tasks written to {OUT}")
