"""Block 3: rules enforced by CODE, not by the prompt.

Rule A - no invented numbers: every number in the final answer must come from a tool result
         (or from the user's own question).
Rule B - safe code only: code written by the model for "ask anything" may read the sales table,
         never touch files, the network or the system.
"""
import ast
import re

NUM = re.compile(r"\d+(?:[.,]\d+)?")  # no minus sign: "2026-11-06" gives 2026, 11, 6


def numbers_in(text: str) -> set[float]:
    return {round(float(n.replace(",", ".")), 1) for n in NUM.findall(text)}


def check_numbers(answer: str, allowed_sources: list[str], tol: float = 0.51) -> list[float]:
    """Return the numbers in `answer` that appear in none of the sources (empty list = OK).
    A small tolerance lets the model round 84.7 to 85."""
    allowed = set()
    for s in allowed_sources:
        allowed |= numbers_in(s)
    return sorted(n for n in numbers_in(answer)
                  if not any(abs(n - a) <= tol for a in allowed))


BLOCKED_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "globals",
                 "locals", "vars", "getattr", "setattr", "delattr", "breakpoint", "exit", "quit"}


class UnsafeCode(Exception):
    pass


def check_code(code: str) -> None:
    """Raise UnsafeCode if the model's code tries anything outside reading `df`."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise UnsafeCode(f"syntax error: {e}") from e
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise UnsafeCode("imports are not allowed (pd and np are already there)")
        if isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            raise UnsafeCode(f"'{node.id}' is not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise UnsafeCode(f"private attribute '{node.attr}' is not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("to_"):
            raise UnsafeCode(f"'{node.attr}' could write a file")


def run_safe(code: str, df):
    """Run checked code on a COPY of the table. The code must put its answer in `result`."""
    import numpy as np
    import pandas as pd
    check_code(code)
    env = {"__builtins__": {"len": len, "min": min, "max": max, "sum": sum, "round": round,
                            "sorted": sorted, "range": range, "abs": abs, "int": int,
                            "float": float, "str": str, "list": list, "dict": dict},
           "pd": pd, "np": np, "df": df.copy()}
    exec(code, env)  # safe enough after check_code + no builtins; see EVIDENCE.md block 3
    if "result" not in env:
        raise UnsafeCode("code must set a variable called `result`")
    return env["result"]
