# Night Oracle — a local shift copilot that cannot lie with numbers

A small AI system for a restaurant shift: it predicts how busy tonight will be, says whether to call in an extra person, answers questions about past sales, and remembers the manager's house rules.
The language model (**Qwen3.5-4B, Q4_K_M, local llama.cpp**) is not trusted: it never computes a number itself, every figure comes from my code, and a guard **in code** blocks any number that did not come from a tool.

Everything runs locally: no API key, no internet after setup.

## 1. Install

```bash
git clone <this repo> && cd night-oracle
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Start the model (separate terminal)

```bash
llama-server -m Qwen3.5-4B-Q4_K_M.gguf --port 8080 -c 16384 --jinja
```

## 3. Run

```bash
python -m oracle.cleaning          # clean the raw export -> data/clean/ + cleaning log
python -m pytest -q                # all tests (no model needed)
python -m oracle.agent             # chat: "How busy is Friday?", "Manager says: match nights +30%"
```

Evidence for each building block (and the command that reproduces it): see [EVIDENCE.md](EVIDENCE.md).

## Layout

| Path | What |
|---|---|
| `oracle/cleaning.py` | messy export → clean table + log (block 6) |
| `oracle/model.py` | hand-written least-squares regression, baseline, interval (blocks 7, 8) |
| `oracle/decision.py` | "extra staff?" probability, threshold, confusion counts (block 4) |
| `oracle/rules.py` | house rules memory in `data/rules.json` (block 5) |
| `oracle/guard.py` | number guard + safe-code checker (block 3) |
| `oracle/tools.py` | tools the model calls (block 1) |
| `oracle/mcp_server.py` | same tools over MCP (block 2) |
| `oracle/agent.py` | the loop: Qwen ↔ tools ↔ guard, traces saved in `traces/` |
| `bench/` | known-answer tasks, model alone vs with tools (block 9) |
| `ai_log/` | AI-use log (R3) |

## Data

`data/raw/sales.csv` — **TODO: replace the generated placeholder with the real anonymised export** (no customer names, payment data or staff names). Used with the manager's permission.
