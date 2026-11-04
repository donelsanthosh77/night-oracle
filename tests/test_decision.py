import pytest

from oracle.decision import confusion, decide, p_above
from oracle.staffing import staff_plan


def test_probability_known_values():
    assert p_above(20, 4, limit=20) == pytest.approx(0.5)
    assert p_above(28, 4, limit=20) == pytest.approx(0.977, abs=1e-3)  # 2 std above
    assert p_above(25, 0, limit=20) == 1.0                             # no spread


def test_threshold():
    assert decide(0.31, threshold=0.3) and not decide(0.29, threshold=0.3)


def test_confusion_counts():
    c = confusion([0.9, 0.1, 0.6, 0.2], [True, True, False, False], threshold=0.5)
    assert c == {"hits": 1, "misses": 1, "false_alarms": 1, "correct_no": 1}


# The owner's rule: 1 in service always, 1 cook per 10 guests, max 3 cooks
@pytest.mark.parametrize("guests, kitchen, total", [
    (0, 0, 1), (5, 1, 2), (10, 1, 2), (11, 2, 3), (20, 2, 3), (21, 3, 4), (30, 3, 4), (45, 3, 4)])
def test_staff_plan(guests, kitchen, total):
    p = staff_plan(guests)
    assert p["kitchen"] == kitchen and p["service"] == 1 and p["total"] == total
