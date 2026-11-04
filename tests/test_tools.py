"""Block 1: the tools return what they promise (runs on the data in data/raw)."""
from oracle import tools


def test_predict_night_shape():
    r = tools.predict_night("Friday", match=True)
    assert r["weekday"] == "Friday"
    lo, hi = r["range_90"]
    assert lo <= r["expected_orders"] <= hi
    assert 0 <= r["p_busy_percent"] <= 100


def test_date_and_weekday_name_agree():
    assert tools.predict_night("2026-11-06") == {**tools.predict_night("Friday"), "day": "2026-11-06"}


def test_ask_data_answers_and_blocks():
    assert tools.ask_data("result = int(df.orders.count())")["result"] > 0
    assert tools.ask_data("import os\nresult = 1")["blocked"] is True
    assert "error" in tools.ask_data("result = df['no_such_column'].sum()")


def test_unknown_tool_and_bad_args():
    assert "error" in tools.call("rm_rf", {})
    assert "error" in tools.call("predict_night", {"day": "not-a-date"})
