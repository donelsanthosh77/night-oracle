"""The agent loop: Qwen (local) <-> our tools, with the number guard on every final answer.

    python -m oracle.agent                 # chat
    python -m oracle.agent --no-tools      # the model alone (for the comparison in block 9)
"""
import argparse
import json
import re
import time
from datetime import date

import requests

from oracle import config, tools
from oracle.guard import check_numbers
from oracle.rules import RuleMemory

SYSTEM = """You are Night Oracle, the shift assistant of a small restaurant (30 seats).
Today is {today} ({weekday}).
Never compute or guess numbers yourself: call predict_night for tonight/future nights,
ask_data for questions about past sales, save_rule when the user gives a house rule.
Answer in 2-4 short sentences, using only numbers returned by the tools.
{rules}"""

SYSTEM_NO_TOOLS = "You are the shift assistant of a small restaurant. Today is {today}. Answer briefly."


def chat(messages: list, use_tools: bool) -> dict:
    body = {"model": config.LLM_MODEL, "messages": messages, "temperature": 0.7,
            "chat_template_kwargs": {"enable_thinking": False}}
    if use_tools:
        body["tools"] = tools.SCHEMAS
    r = requests.post(config.LLM_URL, json=body, timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


def strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()


def ask(question: str, use_tools: bool = True, max_steps: int = 6, guard: bool = True) -> dict:
    """One question -> one answer. Returns the answer and the full trace (saved to traces/)."""
    today = date.today()
    if use_tools:
        system = SYSTEM.format(today=today.isoformat(), weekday=today.strftime("%A"),
                               rules=RuleMemory().as_prompt())
    else:
        system = SYSTEM_NO_TOOLS.format(today=today.isoformat())
    messages = [{"role": "system", "content": system}, {"role": "user", "content": question}]
    tool_outputs, trace = [], {"question": question, "use_tools": use_tools, "steps": []}

    answer = None
    for _ in range(max_steps):
        msg = chat(messages, use_tools)
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            answer = strip_think(msg.get("content", ""))
            break
        for c in calls:
            args = json.loads(c["function"]["arguments"] or "{}")
            out = tools.call(c["function"]["name"], args)
            trace["steps"].append({"tool": c["function"]["name"], "args": args, "result": out})
            tool_outputs.append(json.dumps(out))
            messages.append({"role": "tool", "tool_call_id": c.get("id", ""),
                             "content": json.dumps(out)})
    if answer is None:
        answer = "I could not finish (too many tool calls)."

    # Block 3, rule A: code checks the numbers, the prompt alone is not trusted.
    if use_tools and guard:
        bad = check_numbers(answer, tool_outputs + [question, system])
        trace["guard_first_try"] = bad
        if bad:
            messages.append({"role": "user", "content":
                             f"These numbers are not from any tool: {bad}. "
                             "Rewrite the answer using only tool numbers, or call a tool."})
            answer = strip_think(chat(messages, use_tools=False).get("content", ""))
            bad = check_numbers(answer, tool_outputs + [question, system])
            if bad:
                trace["blocked_answer"] = answer
                answer = f"[blocked by guard: unsupported numbers {bad}] Please ask again."
    trace["answer"] = answer
    config.TRACES.mkdir(exist_ok=True)
    (config.TRACES / f"{time.strftime('%Y%m%d-%H%M%S')}-{int(time.time()*1000) % 1000:03d}.json"
     ).write_text(json.dumps(trace, indent=2, ensure_ascii=False))
    return trace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-tools", action="store_true")
    a = ap.parse_args()
    print("Night Oracle - type a question (empty line to quit)")
    while (q := input("> ").strip()):
        t = ask(q, use_tools=not a.no_tools)
        for s in t["steps"]:
            print(f"  [tool] {s['tool']}({s['args']}) -> {json.dumps(s['result'])[:200]}")
        print(t["answer"])


if __name__ == "__main__":
    main()
