# AI-use log (R3)

AI tool used: Claude (claude.ai). Conversation export: `ai_log/` (files next to this one).
Model of the delivered system: Qwen3.5-4B Q4_K_M, local (llama.cpp).

---

### 2026-11-03 — Claude: project idea, repo skeleton, first runs with Qwen

- **What I decided:** the topic (a shift copilot for the restaurant where I work), fully local, and which blocks to aim for.
- **Kept as it was:** the repo structure Claude generated (cleaning, hand-written regression, decision, rules memory,
  guard, tools, MCP server, agent loop, tests).
- **Fixed by hand (what):** Windows setup — the zip created a folder inside a folder, the venv was in the wrong place,
  packages were installed in the wrong Python (`python -m pip` fixed it); git user name and email.
- **What Qwen got wrong (from my traces):**
  - said "70% busy" instead of "70% chance of being busy" (field name `p_busy_percent` misread);
  - "busiest weekday in 2025": dropped the 2025 filter and called weekday 5 "Friday" (it is Saturday);
  - invented "tomorrow (Tuesday) is a match night" — the guard only checks numbers, not facts;
  - tried `globals()` in its pandas code → blocked by my guard.
- **Prompt / pseudo-code I rewrote:** none yet; noted the weekday problem to fix next time.

---

### 2026-11-04 — Claude: owner's rules, benchmark, interface

- **What I decided:** the owner refused real data, so I asked him for his rules instead and generated the data from them;
  block 6 is not claimed. I chose to keep the two held-out failures as explained failures instead of tuning on them.
- **Owner's rules I collected:** full at 30 guests; 1 in service always, 1 cook per 10 guests (max 3); Tuesday quiet;
  Sunday quiet unless biryani special; day before a public holiday full; start of the month busier;
  cool weather without wind brings people (food smell in the street); rain brings walk-ins.
- **Kept as it was:** data generator from those rules, `stats` tool, MCP client, Streamlit interface, tests (49 pass on a fresh clone).
- **Fixed by hand (what):** zip extracted into the wrong place (old code still running); pandas warnings
  (`.dt.weekday` → `.dt.day_of_week`); trace file names in EVIDENCE.md; deleted a wrong trace
  (I typed a PowerShell command into the agent); interface changes that I had forgotten to push.
- **Prompts / tool descriptions I rewrote (which line, why):**
  - `oracle/agent.py`, SYSTEM prompt: added *"If weather or biryani are not given, call predict_night anyway with the
    defaults and say which assumption you made."* — Why: Qwen asked me for the weather instead of predicting.
    Side effect: Qwen now sometimes predicts even when I only save a rule.
  - `oracle/tools.py`, `stats` description: examples of filled parameters — Why: in v1 Qwen wrote wrong pandas code (0.53).
    Result: 1.00 on the original questions, but only 0.60 on 5 new questions → the examples were too close to the test.
  - Temperature 0.7 → 0.2 — Why: same question gave different answers between runs (std 0.13 → 0.00).
- **Benchmark:** Qwen alone 0.00; v1 0.53 ± 0.13; v2 1.00 ± 0.00; held-out 0.60 ± 0.00.
