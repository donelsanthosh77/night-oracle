"""Block 6: turn the messy till export into a clean table, and log every decision."""
import json

import pandas as pd

from oracle import config
from oracle.calendar_fr import before_holiday

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log = {"rows_in": len(raw), "steps": []}
    df = raw.copy()

    def step(name, before, why):
        log["steps"].append({"step": name, "rows_removed": before - len(df), "why": why})

    # 1. dates come in two formats (ISO and dd/mm/yyyy)
    iso = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    fr = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["date"] = iso.fillna(fr)
    n = len(df); df = df.dropna(subset=["date"])
    step("parse_dates", n, "two date formats in the export; unreadable dates dropped")

    # 2. guests stored as text with spaces
    df["guests"] = pd.to_numeric(df["guests"].astype(str).str.strip(), errors="coerce")
    n = len(df); df = df.dropna(subset=["guests"])
    step("guests_to_number", n, "empty guest counts cannot be guessed, dropped")

    # 3. exact duplicates (the till sometimes exports a line twice)
    n = len(df); df = df.drop_duplicates()
    step("drop_duplicates", n, "same line exported twice")

    # 4. RULE NOT IN THE FILE (from the owner): the restaurant is full at 30 guests,
    #    so more than 30 is a typing error (e.g. 250 for 25), not a busy night.
    n = len(df); df = df[(df["guests"] >= 0) & (df["guests"] <= config.SEATS)]
    step("drop_impossible_counts", n,
         f"owner: full at {config.SEATS} guests, so larger numbers are typos")

    # 5. one row per date (keep the last export of that day)
    n = len(df); df = df.sort_values("date").drop_duplicates("date", keep="last")
    step("one_row_per_date", n, "two different lines for one date: keep the last export")

    df["weekday"] = df["date"].dt.weekday
    df["biryani"] = (df["special"].fillna("") == "biryani").astype(int)
    df["before_holiday"] = df["date"].map(lambda d: int(before_holiday(d.date())))
    df["start_of_month"] = (df["date"].dt.day <= 10).astype(int)
    df["day_name"] = df["weekday"].map(lambda i: DAYS[i])  # names, so the model can't mix up 5 and Friday
    df["guests"] = df["guests"].astype(int)
    log["rows_out"] = len(df)
    cols = ["date", "weekday", "day_name", "guests", "staff", "rain", "temp_c", "wind_kmh",
            "biryani", "before_holiday", "start_of_month"]
    return df.reset_index(drop=True)[cols], log


def load_clean() -> pd.DataFrame:
    if not config.CLEAN_SALES.exists():
        run()
    return pd.read_csv(config.CLEAN_SALES, parse_dates=["date"])


def run():
    raw = pd.read_csv(config.RAW_SALES, dtype=str, keep_default_na=False, na_values=[])
    raw = raw.replace("", None)
    for c in ("staff", "rain", "temp_c", "wind_kmh"):
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    df, log = clean(raw)
    config.CLEAN_SALES.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.CLEAN_SALES, index=False)
    config.CLEANING_LOG.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    run()
