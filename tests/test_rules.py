"""Block 5: restart test - a rule saved by one session is there in the next one."""
import pytest

from oracle.rules import RuleMemory


def test_rule_survives_restart(tmp_path):
    path = tmp_path / "rules.json"
    RuleMemory(path).add("Match nights: +30% delivery")
    after_restart = RuleMemory(path)  # a brand-new object = a restart
    assert "Match nights: +30% delivery" in after_restart.as_prompt()
    assert after_restart.approx_tokens() > 0


def test_duplicates_and_empty(tmp_path):
    m = RuleMemory(tmp_path / "r.json")
    m.add("Rainy Sundays are dead")
    m.add("rainy sundays are dead")
    assert len(m.rules) == 1
    with pytest.raises(ValueError):
        m.add("   ")


def test_no_rules_yet(tmp_path):
    assert RuleMemory(tmp_path / "none.json").as_prompt() == "No house rules saved yet."
