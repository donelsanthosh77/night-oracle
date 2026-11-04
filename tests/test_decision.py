import pytest

from oracle.decision import confusion, decide, p_busy


def test_probability_known_values():
    assert p_busy(90, 10, capacity=90) == pytest.approx(0.5)
    assert p_busy(110, 10, capacity=90) == pytest.approx(0.977, abs=1e-3)  # 2 std above
    assert p_busy(100, 0, capacity=90) == 1.0                              # no spread


def test_threshold():
    assert decide(0.31, threshold=0.3) and not decide(0.29, threshold=0.3)


def test_confusion_counts():
    c = confusion([0.9, 0.1, 0.6, 0.2], [True, True, False, False], threshold=0.5)
    assert c == {"hits": 1, "misses": 1, "false_alarms": 1, "correct_no": 1}
