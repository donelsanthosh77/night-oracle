"""All settings in one place. No secrets: the model runs locally."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_SALES = ROOT / "data" / "raw" / "sales.csv"
CLEAN_SALES = ROOT / "data" / "clean" / "sales_clean.csv"
CLEANING_LOG = ROOT / "data" / "clean" / "cleaning_log.json"
RULES_FILE = ROOT / "data" / "rules.json"
TRACES = ROOT / "traces"

# Local llama.cpp server (OpenAI-compatible API)
#   llama-server -m Qwen3.5-4B-Q4_K_M.gguf --port 8080 -c 16384 --jinja
LLM_URL = "http://localhost:8080/v1/chat/completions"
LLM_MODEL = "qwen3.5-4b"

# Block 4: when do we call in an extra person?
CAPACITY = 90          # orders the normal team handles (ask the manager!)
STAFF_THRESHOLD = 0.30 # low on purpose: being understaffed costs more than one extra person
