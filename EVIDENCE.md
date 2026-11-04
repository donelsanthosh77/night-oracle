# EVIDENCE

> **Model:** Qwen3.5-4B, Q4_K_M, llama.cpp on my laptop (`-c 16384`).
> **Data:** synthetic, generated from the restaurant owner's rules (the owner did not want real sales data
> used; see README). Model numbers come from `python -m oracle.model` / `python -m oracle.decision`.
> Traces are in `traces/` (one JSON per question: question, tool calls with arguments and results, guard, answer).

**Blocks claimed: 1, 2, 3, 5, 9.** Spares (built and shown): 4, 7, 8. Block 6 is not claimed (needs real data).

## Block 1 — Your own tool
- **What:** `predict_night`, `stats`, `ask_data`, `save_rule`, written by me, called by Qwen through the loop in `oracle/agent.py`.
- **Trace of a real call:** `traces/20261104-091035-031.json` — "How busy is next Sunday with the biryani special?" →
  Qwen called `predict_night({"day": "2026-11-08", "biryani_special": true})` → 27 guests (23–30), 3 cooks + 1 in service.
- **Files:** `oracle/tools.py`, `oracle/agent.py`, `tests/test_tools.py`, `tests/test_agent.py`
- **Reproduce:** `python -m oracle.agent`

## Block 2 — Your own MCP server
- **What:** the four tools served over MCP (stdio) by `oracle/mcp_server.py`. My harness calls them through MCP
  (`oracle/mcp_client.py`) when started with `--mcp` (or the "Call tools through MCP" switch in the app).
- **Trace of a real call by my harness through MCP:** `traces/20261104-114851-697.json` (`"via": "mcp"`) —
  same question as block 1, same result (27 guests, 23–30).
- **Also:** `traces/mcp_call.json` (server started, tools listed, one call) · `tests/test_agent.py::test_same_answer_through_mcp`
  (a call through MCP gives exactly the same result as a direct call).
- **Reproduce:** `python -m oracle.agent --mcp` · `python -m bench.mcp_demo`

## Block 3 — A rule enforced in code
- **Rule A, no invented numbers:** every number in the final answer must appear in a tool result or the question
  (`guard.check_numbers`). One retry, then the answer is blocked.
- **Rule B, safe code only:** code written by the model (`ask_data`) cannot import, open files, call eval/exec/globals,
  reach private attributes or write files. Checked on the syntax tree before running, run on a copy of the table, without builtins.
- **Rule C, no runaway loop:** at most 6 tool steps per question (`max_steps` in `oracle/agent.py`).
- **Tests that try to break the rules (all blocked):** `tests/test_guard.py` (6 code attacks, invented numbers),
  `tests/test_agent.py::test_invented_number_is_blocked_twice`.
- **Real model blocked:** `traces/20261103-132605-815.json` — Qwen tried `globals()` in `ask_data` → `"'globals' is not allowed"`.
  Rule C stopped Qwen in the benchmark: `traces/20261104-105921-674.json` (see block 9).
- **Reproduce:** `python -m pytest tests/test_guard.py tests/test_agent.py -v`

## Block 5 — Memory
- **What:** house rules saved by `save_rule` to `data/rules.json`; at every start they are put in the system prompt.
- **Restart test (live, 2026-11-04):** two owner's rules saved through MCP
  (`traces/20261104-115729-285.json`, `traces/20261104-115942-251.json`), app restarted, then
  "What house rules do you know?" → both rules, **no tool call needed** (`traces/20261104-120139-422.json`).
- **Automated restart test:** `tests/test_rules.py::test_rule_survives_restart`.
- **Cost:** the rules text is added to every request. 2 rules = **~32 tokens** per request
  (`RuleMemory().approx_tokens()`, ~4 characters per token; also shown in the app sidebar). It grows with every rule:
  with ~100 rules it would take ~1,600 tokens of the 16,384-token context.
- **Reproduce:** `python -m pytest tests/test_rules.py -v` · in the app: save a rule, restart, ask.

## Block 9 — A measured comparison
- **What:** 17 questions about past nights with answers computed by code (`bench/tasks.json`: 12 original + 5 held-out);
  my system (Qwen + tools) against Qwen alone; 3 runs each.

| Version | Questions | Qwen alone | Qwen + tools | File |
|---|---|---|---|---|
| v1 — Qwen writes pandas code, temperature 0.7 | 12 | 0.00 ± 0.00 | 0.53 ± 0.13 | `bench/results.json` |
| v2 — `stats` tool (Qwen fills parameters, code computes), temperature 0.2 | 12 | — | 1.00 ± 0.00 | `bench/results_v2.json` |
| v3 — v2 + 5 held-out questions written after v2 | 5 new | — | 0.60 ± 0.00 | `bench/results_v3.json` |

(mean ± standard deviation of the accuracy over 3 runs)

- **Qwen alone** either refused ("I don't have access…") or invented: 48 and 45 guests in a 30-seat restaurant, US holidays instead of French ones.
- **Why v3:** the `stats` description contains examples close to the 12 original questions, so the 100% could be "learning the test".
  On 5 new questions Qwen gets 3/5, always the same 3.
- **Failures explained from their traces:**
  - `traces/20261104-105726-811.json` (rainy Saturdays 2025): Qwen added `month: 1`, which the question never asked → 27.0 instead of 27.7.
    The guard cannot catch it: the number does come from a tool, but the tool was asked the wrong question.
  - `traces/20261104-105921-674.json` (biryani Sundays 2026): Qwen counted month by month instead of one call with `year: 2026`,
    hit the 6-step limit → "I could not finish". The limit (rule C) stopped a runaway loop.
  - `traces/20261103-120855-184.json` (v1, busiest weekday 2025): Qwen dropped the 2025 filter and called `weekday` 5 "Friday"
    (it is Saturday) → fixed by adding a `day_name` column to the table.
- **Reproduce:** `python -m bench.make_tasks && python -m bench.run_bench --runs 3 --out bench/results_v3.json` (needs llama-server)

---

## Spare blocks (built and shown, not needed for the five)

### Block 4 — A decision model
- **What:** "do we need the 3rd cook tonight?" = P(guests > 20), from the regression and its error spread (normal model).
  Threshold **0.30**, low on purpose: a missing cook on a busy night costs more than one extra person.
- **On 81 unseen nights:** threshold 0.3 → 59 hits, 0 misses, 4 false alarms, 18 correct no; threshold 0.5 → 3 misses, 2 false alarms.
- **Files:** `oracle/decision.py`, `oracle/staffing.py`, `tests/test_decision.py` · **Reproduce:** `python -m oracle.decision`

### Block 7 — A model learned from data
- **What:** linear regression by least squares, written by hand (weekday, rain, cool-and-calm night, biryani Sunday,
  day before a public holiday, start of month). Trained before the last 12 weeks, tested on the last 12 weeks.
- **Baseline:** average guests of the same weekday. **Metric:** MAE model **1.71** vs baseline **2.67** guests.
- **Learned effects (guests):** biryani +10.0, day before holiday +7.8, cool & calm +3.3, start of month +2.7, rain +1.9,
  Tuesday −9.0, Sunday −7.9 — the model finds the owner's rules back from the data.
- **Known limit:** the owner says the day before a holiday is *full*; a linear model only *adds* guests, so on a quiet Tuesday it predicts ~23, not 30.
- **Files:** `oracle/model.py`, `tests/test_model.py` · **Reproduce:** `python -m oracle.model`

### Block 8 — Numbers with uncertainty
- **What:** 90% prediction interval (prediction ± 1.645 × residual std, clipped to 0–30 seats). Coverage on unseen weeks: 0.889.
- **What the data cannot conclude:** the data is synthetic, generated from the owner's rules (some thresholds are my
  assumptions), so the model can only find those rules back; it says nothing about the real restaurant until it is checked on real nights.

### Block 6 — Not claimed
- The owner asked me not to use real sales data, and block 6 requires real data. The cleaning code and log still exist
  (`oracle/cleaning.py`, `data/clean/cleaning_log.json`); the rule "more than 30 guests is a typo" comes from the owner.
