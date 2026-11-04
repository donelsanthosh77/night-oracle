# EVIDENCE

> Data is **synthetic**, generated from the restaurant owner's rules (the owner did not want real
> sales data used; see README). Numbers below come from `python -m oracle.model` / `oracle.decision`
> on that data. TODO items must be filled from the local Qwen3.5-4B runs.

## Block 1 — Your own tool
- **What:** `predict_night`, `ask_data`, `save_rule`, called by Qwen through the loop in `oracle/agent.py`.
- **Files:** `oracle/tools.py`, `oracle/agent.py`, `tests/test_tools.py`, `tests/test_agent.py`
- **Trace of a real call:** TODO `traces/<file>.json` ("How busy is next Sunday with the biryani special?")
- **Reproduce:** `python -m oracle.agent`

## Block 2 — Your own MCP server
- **What:** the same three tools served over MCP (stdio), listed and called by an MCP client; TODO also called from Pi.
- **Files:** `oracle/mcp_server.py`, `bench/mcp_demo.py`, `traces/mcp_call.json`
- **Reproduce:** `python -m bench.mcp_demo`

## Block 3 — A rule enforced in code
- **Rule A:** the final answer may contain no number that is not in a tool result or the question (`guard.check_numbers`); one retry, then the answer is blocked.
- **Rule B:** code written by the model (`ask_data`) cannot import, open files, call eval/exec/globals, reach private attributes or write files. Checked on the syntax tree, run on a copy, without builtins.
- **Attack tests (blocked):** `tests/test_guard.py` (6 attacks), `tests/test_agent.py::test_invented_number_is_blocked_twice`
- **Real model blocked:** TODO trace where Qwen tried `globals()` (2026-11-03).
- **Reproduce:** `python -m pytest tests/test_guard.py -v`

## Block 4 — A decision model
- **What:** "do we need the 3rd cook?" = P(guests > 20), from the regression and its error spread (normal model). Threshold **0.30**, low on purpose: a missing cook on a busy night costs more than one extra person.
- **Results on 81 unseen nights:** threshold 0.3 → 59 hits, 0 misses, 4 false alarms, 18 correct no; threshold 0.5 → 3 misses, 2 false alarms.
- **Files:** `oracle/decision.py`, `oracle/staffing.py`, `tests/test_decision.py` · **Reproduce:** `python -m oracle.decision`

## Block 5 — Memory
- **What:** house rules saved to `data/rules.json`, injected in the system prompt at every start.
- **Restart test:** `tests/test_rules.py::test_rule_survives_restart` + live: rule saved, agent restarted, "What house rules do you know?" answered correctly (TODO trace file).
- **Cost:** `RuleMemory().approx_tokens()` tokens per request. TODO: report for N rules.

## Block 6 — Messy data, decisions written
- **Not claimed:** the owner asked me not to use real data, and block 6 requires real data.
- The cleaning code and log still exist (`oracle/cleaning.py`, `data/clean/cleaning_log.json`); the rule "more than 30 guests is a typo" comes from the owner.

## Block 7 — A model learned from data
- **What:** linear regression by least squares: weekday, rain, cool-and-calm night, biryani Sunday, day before a public holiday, start of month. Trained before the last 12 weeks, tested on the last 12 weeks.
- **Baseline:** average guests of the same weekday.
- **Metric:** MAE model 1.71 vs baseline 2.67 guests.
- **Learned effects (guests):** Tuesday −9.0, Sunday −7.9, biryani +10.0, day before holiday +7.8, cool & calm +3.3, start of month +2.7, rain +1.9 — the model finds the owner's rules back from the data.
- **Known limit:** the owner says the day before a holiday is *full*; a linear model only *adds* guests, so on a quiet Tuesday it predicts ~23, not 30.
- **Files:** `oracle/model.py`, `tests/test_model.py` · **Reproduce:** `python -m oracle.model`

## Block 8 — Numbers with uncertainty
- **What:** 90% prediction interval (prediction ± 1.645 × residual std, clipped to 0–30 seats). Coverage on unseen weeks: 0.889.
- **What the data cannot conclude:** it is synthetic, generated from the owner's rules (some thresholds are my assumptions), so the model can only find those rules back; it says nothing about the real restaurant until it is checked on real nights.

## Block 9 — A measured comparison
- **What:** 12 + 5 held-out questions about past nights with answers computed by code (`bench/tasks.json`); 3 runs each.
- **v1 (2026-11-04, temperature 0.7, Qwen writes pandas code):** Qwen alone **0.00 ± 0.00**, Qwen + tools **0.53 ± 0.13** (`bench/results.json`).
  Qwen alone either refused ("I don't have access…") or invented: 48 and 45 guests (the restaurant has 30 seats), US holidays instead of French ones.
- **v2 (temperature 0.2, new `stats` tool: Qwen only fills parameters, code computes):** Qwen + tools **1.00 ± 0.00** on the 12 original questions (`bench/results_v2.json`).
- **v3 — held-out check:** the `stats` description contains examples close to the original questions, so 5 NEW questions were added after v2 (rainy Saturdays, busiest night of a month, biryani Sundays count, quietest night, Tuesdays at start of month). TODO: original vs held-out mean ± std (`bench/results_v3.json`).
- **One failure explained from its trace:** TODO (from results_v2.json). Also, 2026-11-03: asked the busiest weekday in 2025, Qwen dropped the 2025 filter and translated `weekday` 5 as "Friday" (it is Saturday) → fixed with the `day_name` column.
- **Reproduce:** `python -m bench.make_tasks && python -m bench.run_bench --runs 3 --tools-only --out bench/results_v3.json`
