# Night Oracle — a local shift copilot that cannot lie with numbers

A small AI system for a 30-seat restaurant: it predicts how many guests will come this evening, gives the staff plan (1 in service + 1 cook per 10 guests, max 3), says whether to call the 3rd cook, answers questions about past sales, and remembers the manager's house rules.
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
python -m oracle.agent             # chat: "How busy is Sunday with the biryani special?", "Owner says: Tuesday is quiet"
```

### Web interface (optional, not a block)

```bash
streamlit run app.py               # opens http://localhost:8501
```

Shows the whole chain live: question → Qwen → harness → MCP server → tool → guard → answer, with the
arguments Qwen chose and the result our code computed. Switches: tools on/off, through MCP or direct, guard on/off.
Same from the terminal: `python -m oracle.agent --mcp`.

Evidence for each building block (and the command that reproduces it): see [EVIDENCE.md](EVIDENCE.md).

## Layout

| Path | What |
|---|---|
| `oracle/cleaning.py` | messy export → clean table + log (block 6) |
| `oracle/model.py` | hand-written least-squares regression, baseline, interval (blocks 7, 8) |
| `oracle/staffing.py` | the owner's staffing rule in code |
| `oracle/decision.py` | "3rd cook?" probability, threshold, confusion counts (block 4) |
| `oracle/rules.py` | house rules memory in `data/rules.json` (block 5) |
| `oracle/guard.py` | number guard + safe-code checker (block 3) |
| `oracle/tools.py` | tools the model calls (block 1) |
| `oracle/mcp_server.py` | same tools over MCP (block 2) |
| `oracle/mcp_client.py` | lets our harness call the tools through MCP |
| `app.py` | Streamlit interface (not a block) |
| `oracle/agent.py` | the loop: Qwen ↔ tools ↔ guard, traces saved in `traces/` |
| `bench/` | known-answer tasks, model alone vs with tools (block 9) |
| `ai_log/` | AI-use log (R3) |

## Data

`data/raw/sales.csv` is **synthetic**: the restaurant owner asked me not to use real sales data, so `data/make_sample_data.py` generates it **from the owner's rules** (told to me on 2026-11-04):

- lunch + evening are about 30 guests; the evening alone is around 20; full at 30; never closed
- 1 person in service always; in the kitchen 1 cook per 10 guests, at most 3 (takeaway is done by the kitchen too)
- busy: Monday, Thursday, Friday, Saturday; Wednesday depends; Tuesday quiet; Sunday quiet unless there is a biryani special
- the day before a public holiday is full; the start of the month is busier
- cool weather without wind brings people (the smell of food spreads in the street); very cold: average; rain: walk-in customers

Thresholds the owner did not give (cool = 5–12 °C, calm = wind under 15 km/h, 4 Sundays in 10 with biryani) are marked ASSUMPTION in the code.

Regenerate it with `python data/make_sample_data.py`.
