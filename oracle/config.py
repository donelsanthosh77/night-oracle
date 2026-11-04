"""All settings in one place. No secrets: the model runs locally."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_SALES = ROOT / "data" / "raw" / "sales.csv"
CLEAN_SALES = ROOT / "data" / "clean" / "sales_clean.csv"
CLEANING_LOG = ROOT / "data" / "clean" / "cleaning_log.json"
RULES_FILE = ROOT / "data" / "rules.json"
TRACES = ROOT / "traces"

# Local llama.cpp server (OpenAI-compatible API)
#   llama-server -hf bartowski/Qwen_Qwen3.5-4B-GGUF:Q4_K_M --port 8080 -c 16384 --jinja
LLM_URL = "http://localhost:8080/v1/chat/completions"
LLM_MODEL = "qwen3.5-4b"

# Owner's rules (2026-11-04)
SEATS = 30              # the restaurant is full at 30 guests (evening is usually ~20)
GUESTS_PER_COOK = 10    # 1 cook for every 10 guests
MAX_COOKS = 3           # never more than 3 in the kitchen
SERVICE_STAFF = 1       # always 1 in service, even on quiet nights
COOL_MIN_C, COOL_MAX_C = 5, 12   # owner: cool + calm -> food smell spreads -> more guests (numbers: ASSUMPTION)
CALM_WIND_KMH = 15                # below this wind speed the night counts as calm (ASSUMPTION)

# Block 4: do we need the 3rd cook tonight? (= more than 20 guests)
THIRD_COOK_ABOVE = 20
THIRD_COOK_THRESHOLD = 0.30  # low on purpose: a missing cook costs more than one extra
