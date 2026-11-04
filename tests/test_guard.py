"""Block 3: tests that TRY TO BREAK the rules and must be blocked."""
import pandas as pd
import pytest

from oracle.guard import UnsafeCode, check_numbers, run_safe

DF = pd.DataFrame({"weekday": [4, 4, 5], "orders": [80, 100, 120]})


# Rule A: no invented numbers
def test_invented_number_is_caught():
    tool = '{"expected_orders": 85, "range_90": [70, 100]}'
    assert check_numbers("Expect about 120 orders tonight.", [tool]) == [120.0]


def test_numbers_from_tools_pass_with_rounding():
    tool = '{"expected_orders": 84.7, "p_busy_percent": 72}'
    assert check_numbers("Around 85 orders, 72% chance it is busy.", [tool]) == []


def test_numbers_from_the_question_are_allowed():
    assert check_numbers("On 2026-11-06 we expect 85.", ["Friday 2026-11-06?", "85"]) == []


# Rule B: model-written code may only read the table
@pytest.mark.parametrize("attack", [
    "import os\nresult = os.listdir('.')",
    "result = open('data/rules.json').read()",
    "result = __import__('os').system('rm -rf /')",
    "result = df.__class__.__subclasses__()",
    "df.to_csv('/tmp/stolen.csv'); result = 1",
    "result = eval('1+1')",
])
def test_attacks_are_blocked(attack):
    with pytest.raises(UnsafeCode):
        run_safe(attack, DF)


def test_normal_code_works_and_does_not_change_data():
    code = "df['orders'] = 0\nresult = 1"
    run_safe(code, DF)
    assert DF["orders"].tolist() == [80, 100, 120]  # it worked on a copy
    assert run_safe("result = df[df.weekday == 4].orders.mean()", DF) == 90


def test_code_without_result_is_refused():
    with pytest.raises(UnsafeCode):
        run_safe("x = 1", DF)
