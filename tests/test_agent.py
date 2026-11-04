"""The agent loop with a FAKE model (no llama-server needed): tool call -> answer -> guard."""
import json

from oracle import agent


def fake_model(replies):
    replies = iter(replies)
    return lambda messages, use_tools: next(replies)


def tool_call(name, args):
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": "1", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}


def test_tool_numbers_pass(monkeypatch):
    pred = agent.tools.predict_night("Friday")
    monkeypatch.setattr(agent, "chat", fake_model([
        tool_call("predict_night", {"day": "Friday"}),
        {"role": "assistant", "content": f"About {pred['expected_guests']} guests on Friday."}]))
    t = agent.ask("How busy is Friday?")
    assert t["steps"][0]["tool"] == "predict_night"
    assert t["guard_first_try"] == []
    assert str(pred["expected_guests"]) in t["answer"]


def test_invented_number_is_blocked_twice(monkeypatch):
    monkeypatch.setattr(agent, "chat", fake_model([
        {"role": "assistant", "content": "Friday will be 987 guests, trust me."},
        {"role": "assistant", "content": "OK: 987 guests."}]))
    t = agent.ask("How busy is Friday?")
    assert t["answer"].startswith("[blocked by guard")
    assert t["blocked_answer"] == "OK: 987 guests."


def test_thinking_is_stripped():
    assert agent.strip_think("<think>hmm 42</think>Done.") == "Done."
