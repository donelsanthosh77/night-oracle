"""Block 1: the tools return what they promise (runs on the data in data/raw)."""
from oracle import tools


def test_predict_night_shape():
    r = tools.predict_night("2026-11-07", weather="cool_no_wind")
    assert r["weekday"] == "Saturday"
    assert "cool night without wind" in r["reasons"]
    lo, hi = r["range_90"]
    assert 0 <= lo <= r["expected_guests"] <= hi <= 30
    assert 0 <= r["chance_more_than_20_guests_percent"] <= 100
    assert r["staff_plan_for_expected"]["service"] == 1


def test_owner_rules_show_in_predictions():
    sat = tools.predict_night("2026-11-21")["expected_guests"]
    assert tools.predict_night("2026-11-17")["expected_guests"] < sat           # Tuesday quiet
    plain_sun = tools.predict_night("2026-11-22")["expected_guests"]
    assert plain_sun < sat                                                      # Sunday quiet...
    assert tools.predict_night("2026-11-22", biryani_special=True)["expected_guests"] > plain_sun
    eve = tools.predict_night("2026-11-10")                                     # eve of 11 November (Tuesday)
    normal_tue = tools.predict_night("2026-11-24")                              # plain Tuesday
    assert "day before a public holiday" in eve["reasons"]
    assert eve["expected_guests"] > normal_tue["expected_guests"] + 5
    # known limit: a linear model ADDS guests, so it does not reach "always full" (30) on a quiet day


def test_weekday_name_gives_a_date():
    r = tools.predict_night("Friday")
    assert r["weekday"] == "Friday" and len(r["date"]) == 10


def test_bad_weather_value():
    assert "error" in tools.call("predict_night", {"day": "Friday", "weather": "sunny"})


def test_ask_data_answers_and_blocks():
    assert tools.ask_data("result = int(df.guests.count())")["result"] > 0
    assert tools.ask_data("result = df.groupby('day_name').guests.mean().idxmax()")["result"] in tools.DAYS
    assert tools.ask_data("import os\nresult = 1")["blocked"] is True
    assert "error" in tools.ask_data("result = df['no_such_column'].sum()")


def test_unknown_tool_and_bad_args():
    assert "error" in tools.call("rm_rf", {})
    assert "error" in tools.call("predict_night", {"day": "not-a-date"})
