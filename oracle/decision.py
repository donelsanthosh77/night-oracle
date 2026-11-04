"""Block 4: "Do we call in an extra person tonight?" as a probability, with a chosen threshold."""
import math

import numpy as np

from oracle import config


def normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def p_busy(pred: float, resid_std: float, capacity: int = config.CAPACITY) -> float:
    """P(orders > capacity) if the real number ~ Normal(pred, resid_std)."""
    if resid_std <= 0:
        return 1.0 if pred > capacity else 0.0
    return 1 - normal_cdf((capacity - pred) / resid_std)


def decide(p: float, threshold: float = config.STAFF_THRESHOLD) -> bool:
    return p >= threshold


def confusion(probs, actual_busy, threshold: float) -> dict:
    """Misses = busy night but we said no. False alarms = quiet night but we said yes."""
    said_yes = np.asarray(probs) >= threshold
    busy = np.asarray(actual_busy, bool)
    return {
        "hits": int(np.sum(said_yes & busy)),
        "misses": int(np.sum(~said_yes & busy)),
        "false_alarms": int(np.sum(said_yes & ~busy)),
        "correct_no": int(np.sum(~said_yes & ~busy)),
    }


def evaluate() -> dict:
    from oracle.cleaning import load_clean
    from oracle.model import OrdersModel, split_by_time
    train, test = split_by_time(load_clean())
    m = OrdersModel().fit(train)
    probs = [p_busy(p, m.resid_std) for p in m.predict_df(test)]
    busy = (test["orders"] > config.CAPACITY).to_numpy()
    return {t: confusion(probs, busy, t) for t in (0.2, 0.3, 0.5, 0.7)}


if __name__ == "__main__":
    for t, c in evaluate().items():
        print(f"threshold {t}: {c}")
