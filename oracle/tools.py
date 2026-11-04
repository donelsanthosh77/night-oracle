"""Block 1: the functions the model is allowed to call. Every number Qwen says comes from here."""
import json
from datetime import date

from oracle import config
from oracle.calendar_fr import before_holiday, next_date_for, start_of_month
from oracle.cleaning import load_clean
from oracle.decision import decide, p_above
from oracle.guard import UnsafeCode, run_safe
from oracle.model import GuestsModel, interval
from oracle.rules import RuleMemory
from oracle.staffing import staff_plan

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_model = None


def get_model() -> GuestsModel:
    global _model
    if _model is None:
        _model = GuestsModel().fit(load_clean())
    return _model


WEATHER = {"normal": (15.0, 20.0), "cool_no_wind": (8.0, 5.0), "very_cold": (2.0, 10.0)}


def predict_night(day: str, rain: bool = False, weather: str = "normal",
                  biryani_special: bool = False) -> dict:
    """day = 'YYYY-MM-DD' or a weekday name in English (= the next one).
    Public holidays and the start of the month are found from the date by code, not by the model."""
    if day.capitalize() in DAYS:
        d = next_date_for(DAYS.index(day.capitalize()))
    else:
        d = date.fromisoformat(day)
    if weather not in WEATHER:
        raise ValueError(f"weather must be one of {list(WEATHER)}")
    temp, wind = WEATHER[weather]
    hol, som = before_holiday(d), start_of_month(d)
    m = get_model()
    pred = m.predict(d.weekday(), rain=int(rain), temp_c=temp, wind_kmh=wind,
                     biryani=int(biryani_special and d.weekday() == 6),
                     before_holiday=int(hol), start_of_month=int(som))
    lo, hi = interval(m, pred)
    p = p_above(pred, m.resid_std)
    reasons = [r for r, on in [("day before a public holiday", hol), ("start of the month", som),
                               ("biryani special", biryani_special and d.weekday() == 6),
                               ("cool night without wind", weather == "cool_no_wind"),
                               ("rain brings walk-ins", rain)] if on]
    return {
        "date": d.isoformat(), "weekday": DAYS[d.weekday()], "reasons": reasons,
        "expected_guests": round(pred), "range_90": [round(lo), round(hi)],
        "seats": config.SEATS,
        "staff_plan_for_expected": staff_plan(pred),
        "chance_more_than_20_guests_percent": round(100 * p),
        "call_third_cook": decide(p),
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
        "description": "Predict the number of evening guests (max 30 seats), a 90% range, the staff "
                       "plan and whether to call the 3rd cook. Holidays and start of month are automatic.",
        "parameters": {"type": "object", "properties": {
            "day": {"type": "string", "description": "YYYY-MM-DD or weekday name like 'Friday'"},
            "rain": {"type": "boolean"},
            "weather": {"type": "string", "enum": ["normal", "cool_no_wind", "very_cold"]},
            "biryani_special": {"type": "boolean", "description": "Sunday biryani special"}},
            "required": ["day"]}}},
    {"type": "function", "function": {
        "name": "ask_data",
        "description": "Answer a question about past nights by writing pandas code. The table is `df` "
                       "with columns date (datetime), weekday (0=Monday..6=Sunday), day_name "
                       "('Monday'..'Sunday'), guests, staff, rain (0/1), temp_c, wind_kmh, biryani (0/1), "
                       "before_holiday (0/1), start_of_month (0/1). "
                       "Put the answer in a variable named `result`. No imports.",
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
