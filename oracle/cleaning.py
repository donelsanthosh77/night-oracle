"""Block 6: turn the messy till export into a clean table, and log every decision."""
import json

import pandas as pd

from oracle import config


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

    # 2. orders stored as text with spaces
    df["orders"] = pd.to_numeric(df["orders"].astype(str).str.strip(), errors="coerce")
    n = len(df); df = df.dropna(subset=["orders"])
    step("orders_to_number", n, "empty order counts cannot be guessed, dropped")

    # 3. refund lines are not nights
    n = len(df); df = df[df["orders"] >= 0]
    step("drop_refunds", n, "negative orders are refund corrections, not a night")

    # 4. exact duplicates (the till sometimes exports a line twice)
    n = len(df); df = df.drop_duplicates()
    step("drop_duplicates", n, "same line exported twice")

    # 5. RULE NOT IN THE FILE (from the manager): a closed day is not a 0-order day
    n = len(df); df = df[df["note"].fillna("") != "closed"]
    step("drop_closed_days", n, "manager: closed days must not count as quiet nights")

    # 6. one row per date (keep the last export of that day)
    n = len(df); df = df.sort_values("date").drop_duplicates("date", keep="last")
    step("one_row_per_date", n, "two different lines for one date: keep the last export")

    df["event"] = df["event"].fillna("")
    df["weekday"] = df["date"].dt.weekday
    df["orders"] = df["orders"].astype(int)
    log["rows_out"] = len(df)
    return df.reset_index(drop=True)[["date", "weekday", "orders", "staff", "rain", "event"]], log


def load_clean() -> pd.DataFrame:
    if not config.CLEAN_SALES.exists():
        run()
    return pd.read_csv(config.CLEAN_SALES, parse_dates=["date"], keep_default_na=False)


def run():
    raw = pd.read_csv(config.RAW_SALES, dtype=str, keep_default_na=False, na_values=[])
    raw = raw.replace("", None)
    for c in ("staff", "rain"):
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    df, log = clean(raw)
    config.CLEAN_SALES.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.CLEAN_SALES, index=False)
    config.CLEANING_LOG.write_text(json.dumps(log, indent=2))
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    run()
