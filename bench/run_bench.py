"""Block 9: Qwen alone vs Qwen + tools, every task, 3 runs each. Needs llama-server running.

    python -m bench.run_bench --runs 3
"""
import argparse
import json
import re
import statistics
from pathlib import Path

from oracle.agent import ask
from oracle.guard import numbers_in

TASKS = Path(__file__).parent / "tasks.json"
OUT = Path(__file__).parent / "results.json"


def score(task: dict, answer: str) -> bool:
    if task["type"] == "text":
        return re.search(rf"\b{task['answer']}\b", answer, re.I) is not None
    return any(abs(n - task["answer"]) <= task["tol"] for n in numbers_in(answer))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()
    tasks = json.loads(TASKS.read_text())
    results = {}
    for mode, use_tools in (("model_alone", False), ("with_tools", True)):
        accs, rows = [], []
        for run in range(a.runs):
            ok = 0
            for i, t in enumerate(tasks):
                tr = ask(t["q"], use_tools=use_tools)
                good = score(t, tr["answer"])
                ok += good
                rows.append({"run": run, "task": i, "correct": good, "answer": tr["answer"]})
                print(f"{mode} run{run} task{i}: {'OK ' if good else 'BAD'} {tr['answer'][:80]!r}")
            accs.append(ok / len(tasks))
        results[mode] = {"accuracy_per_run": accs, "mean": statistics.mean(accs),
                         "std": statistics.stdev(accs) if len(accs) > 1 else 0.0, "rows": rows}
    OUT.write_text(json.dumps(results, indent=2))
    for m, r in results.items():
        print(f"{m}: mean {r['mean']:.2f}  std {r['std']:.2f}")


if __name__ == "__main__":
    main()
