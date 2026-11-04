# EVIDENCE

> Numbers below marked TODO must be filled in from the **real** data and the **local Qwen3.5-4B** runs.
> The current numbers come from the placeholder data and are only there to show the format.

## Block 1 — Your own tool
- **What:** `predict_night`, `ask_data`, `save_rule`, called by Qwen through the loop in `oracle/agent.py`.
- **Files:** `oracle/tools.py`, `oracle/agent.py`, `tests/test_tools.py`, `tests/test_agent.py`
- **Trace of a real call:** TODO `traces/<file>.json` (ask "How busy is Friday?" in `python -m oracle.agent`)
- **Reproduce:** `python -m oracle.agent`

## Block 2 — Your own MCP server
- **What:** the same three tools served over MCP (stdio), listed and called by an MCP client; TODO also called from Pi.
- **Files:** `oracle/mcp_server.py`, `bench/mcp_demo.py`, `traces/mcp_call.json`
- **Reproduce:** `python -m bench.mcp_demo`

## Block 3 — A rule enforced in code
- **Rule A:** the final answer may contain no number that is not in a tool result or the question. Checked in `guard.check_numbers`; the model gets one retry, then the answer is blocked.
- **Rule B:** code written by the model (`ask_data`) cannot import, open files, call eval/exec, reach private attributes or write files (`to_csv`...). Checked on the syntax tree before running, on a copy of the table, without builtins.
- **Attack tests (blocked):** `tests/test_guard.py` (6 attacks), `tests/test_agent.py::test_invented_number_is_blocked_twice`
- **Reproduce:** `python -m pytest tests/test_guard.py -v`

## Block 4 — A decision model
- **What:** P(orders > capacity of 90) from the regression and its error spread (normal model). Threshold **0.30**, chosen low because a miss (understaffed busy night) costs more than a false alarm (one extra person).
- **Results on 75 unseen nights (placeholder data):** threshold 0.3 → 20 hits, 0 misses, 4 false alarms, 51 correct no; threshold 0.7 → 9 misses. TODO real data.
- **Files:** `oracle/decision.py`, `tests/test_decision.py` · **Reproduce:** `python -m oracle.decision`

## Block 5 — Memory
- **What:** house rules saved to `data/rules.json`, injected in the system prompt at every start.
- **Restart test:** `tests/test_rules.py::test_rule_survives_restart`. TODO: live demo (save a rule, quit, restart, ask).
- **Cost:** `RuleMemory().approx_tokens()` tokens per request. TODO: report for N rules.

## Block 6 — Messy data, decisions written
- **Data:** TODO real export from the restaurant (anonymised, with permission).
- **Cleaning log:** `data/clean/cleaning_log.json` (dates in 2 formats, text numbers, missing values, refunds, duplicates).
- **Rule not in the file:** "closed days must not count as quiet nights" — **from the manager**, TODO name/role and date.
- **Reproduce:** `python -m oracle.cleaning`

## Block 7 — A model learned from data
- **What:** linear regression by least squares (weekday, rain, match, rainy Sunday), trained on everything before the last 12 weeks, tested on the last 12 weeks.
- **Baseline:** average orders of the same weekday.
- **Metric (placeholder):** MAE model 6.43 vs baseline 7.03 orders. TODO real data.
- **Files:** `oracle/model.py`, `tests/test_model.py` · **Reproduce:** `python -m oracle.model`

## Block 8 — Numbers with uncertainty
- **What:** 90% prediction interval (prediction ± 1.645 × residual std). Coverage on unseen weeks: 0.867 (placeholder).
- **What the data cannot conclude:** TODO, e.g. "it cannot say how a new menu or a price change would affect orders: none happened in the data."

## Block 9 — A measured comparison
- **What:** 11 questions about past sales with answers computed by code (`bench/tasks.json`); Qwen alone vs Qwen + tools; 3 runs each.
- **Results:** TODO mean ± std from `bench/results.json`.
- **One failure explained from its trace:** TODO.
- **Reproduce:** `python -m bench.make_tasks && python -m bench.run_bench --runs 3`
