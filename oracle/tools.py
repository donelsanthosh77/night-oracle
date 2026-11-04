"""Block 1: the functions the model is allowed to call. Every number Qwen says comes from here."""
import json
from datetime import date

from oracle import config
from oracle.cleaning import load_clean
from oracle.decision import decide, p_busy
from oracle.guard import UnsafeCode, run_safe
from oracle.model import OrdersModel, interval
from oracle.rules import RuleMemory

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_model = None


def get_model() -> OrdersModel:
    global _model
    if _model is None:
        _model = OrdersModel().fit(load_clean())
    return _model


def predict_night(day: str, rain: bool = False, match: bool = False) -> dict:
    """day = 'YYYY-MM-DD' or a weekday name in English."""
    if day.capitalize() in DAYS:
        wd = DAYS.index(day.capitalize())
    else:
        wd = date.fromisoformat(day).weekday()
    m = get_model()
    pred = m.predict(wd, int(rain), int(match))
    lo, hi = interval(m, pred)
    p = p_busy(pred, m.resid_std)
    return {
        "day": day, "weekday": DAYS[wd], "rain": rain, "match": match,
        "expected_orders": round(pred), "range_90": [round(lo), round(hi)],
        "p_busy_percent": round(100 * p), "capacity": config.CAPACITY,
        "call_extra_staff": decide(p),
    }


def ask_data(code: str) -> dict:
    """Run pandas code (written by the model) on the clean sales table `df`. Must set `result`."""
    try:
        result = run_safe(code, load_clean())
    except UnsafeCode as e:
        return {"blocked": True, "reason": str(e)}
    except Exception as e:  # the model's code can be wrong: show it the error
        return {"error": f"{type(e).__name__}: {e}"}
    if hasattr(result, "to_dict"):
        result = result.to_dict()
    return {"result": json.loads(json.dumps(result, default=str))}


def save_rule(text: str) -> dict:
    return RuleMemory().add(text, source="manager")


TOOLS = {"predict_night": predict_night, "ask_data": ask_data, "save_rule": save_rule}

# Descriptions sent to the model (OpenAI tool format, understood by llama.cpp --jinja)
SCHEMAS = [
    {"type": "function", "function": {
        "name": "predict_night",
        "description": "Predict the number of orders for one night, a 90% range, "
                       "the chance it is busy and whether to call extra staff.",
        "parameters": {"type": "object", "properties": {
            "day": {"type": "string", "description": "YYYY-MM-DD or weekday name like 'Friday'"},
            "rain": {"type": "boolean"}, "match": {"type": "boolean"}},
            "required": ["day"]}}},
    {"type": "function", "function": {
        "name": "ask_data",
        "description": "Answer a question about past sales by writing pandas code. The table is `df` "
                       "with columns date (datetime), weekday (0=Mon), orders, staff, rain (0/1), "
                       "event ('match' or ''). Put the answer in a variable named `result`. No imports.",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}},
                       "required": ["code"]}}},
    {"type": "function", "function": {
        "name": "save_rule",
        "description": "Save a house rule the manager gave, so it is remembered next time.",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}},
                       "required": ["text"]}}},
]


def call(name: str, args: dict) -> dict:
    if name not in TOOLS:
        return {"error": f"unknown tool {name}"}
    try:
        return TOOLS[name](**args)
    except (TypeError, ValueError) as e:
        return {"error": f"bad arguments: {e}"}
