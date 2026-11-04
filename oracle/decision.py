"""Block 4: "Do we need the 3rd cook tonight?" (= more than 20 guests) as a probability + threshold."""
import math

import numpy as np

from oracle import config


def normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def p_above(pred: float, resid_std: float, limit: int = config.THIRD_COOK_ABOVE) -> float:
    """P(guests > limit) if the real number ~ Normal(pred, resid_std)."""
    if resid_std <= 0:
        return 1.0 if pred > limit else 0.0
    return 1 - normal_cdf((limit - pred) / resid_std)


def decide(p: float, threshold: float = config.THIRD_COOK_THRESHOLD) -> bool:
    return p >= threshold


def confusion(probs, actual, threshold: float) -> dict:
    """Misses = 3rd cook needed but we said no. False alarms = not needed but we said yes."""
    said_yes = np.asarray(probs) >= threshold
    needed = np.asarray(actual, bool)
    return {
        "hits": int(np.sum(said_yes & needed)),
        "misses": int(np.sum(~said_yes & needed)),
        "false_alarms": int(np.sum(said_yes & ~needed)),
        "correct_no": int(np.sum(~said_yes & ~needed)),
    }


def evaluate() -> dict:
    from oracle.cleaning import load_clean
    from oracle.model import GuestsModel, split_by_time
    train, test = split_by_time(load_clean())
    m = GuestsModel().fit(train)
    probs = [p_above(p, m.resid_std) for p in m.predict_df(test)]
    needed = (test["guests"] > config.THIRD_COOK_ABOVE).to_numpy()
    return {t: confusion(probs, needed, t) for t in (0.1, 0.3, 0.5, 0.7)}


if __name__ == "__main__":
    for t, c in evaluate().items():
        print(f"threshold {t}: {c}")
