"""Block 5: the manager's rules, kept in a file so they survive a restart."""
import json
from datetime import date
from pathlib import Path

from oracle import config


class RuleMemory:
    def __init__(self, path: Path = config.RULES_FILE):
        self.path = Path(path)
        self.rules = json.loads(self.path.read_text()) if self.path.exists() else []

    def add(self, text: str, source: str = "manager") -> dict:
        text = text.strip()
        if not text:
            raise ValueError("empty rule")
        if any(r["text"].lower() == text.lower() for r in self.rules):
            return next(r for r in self.rules if r["text"].lower() == text.lower())
        rule = {"text": text, "source": source, "added": date.today().isoformat()}
        self.rules.append(rule)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.rules, indent=2, ensure_ascii=False))
        return rule

    def as_prompt(self) -> str:
        """What is injected into the system prompt. Its size is the memory's cost in tokens."""
        if not self.rules:
            return "No house rules saved yet."
        return "House rules from the restaurant:\n" + "\n".join(
            f"- {r['text']} (from {r['source']})" for r in self.rules)

    def approx_tokens(self) -> int:
        return len(self.as_prompt()) // 4  # rough rule of thumb: ~4 characters per token
