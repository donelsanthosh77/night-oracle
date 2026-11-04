"""Block 7: a linear regression written by hand (least squares), against a simple baseline.
Block 8: a prediction interval from the model's errors on unseen weeks.
"""
import numpy as np
import pandas as pd


def features(weekday: int, rain: int, match: int) -> np.ndarray:
    """1 (intercept) + one-hot weekday (Tue..Sun, Monday is the reference) + rain + match + rainy Sunday."""
    x = [1.0] + [1.0 if weekday == d else 0.0 for d in range(1, 7)]
    x += [float(rain), float(match), float(rain and weekday == 6)]
    return np.array(x)


def design(df: pd.DataFrame) -> np.ndarray:
    return np.array([features(r.weekday, r.rain, r.event == "match") for r in df.itertuples()])


class OrdersModel:
    def fit(self, df: pd.DataFrame) -> "OrdersModel":
        X, y = design(df), df["orders"].to_numpy(float)
        # least squares: w = argmin ||Xw - y||^2
        self.w, *_ = np.linalg.lstsq(X, y, rcond=None)
        self.resid_std = float(np.std(y - X @ self.w, ddof=X.shape[1]))
        return self

    def predict(self, weekday: int, rain: int = 0, match: int = 0) -> float:
        return float(features(weekday, rain, match) @ self.w)

    def predict_df(self, df: pd.DataFrame) -> np.ndarray:
        return design(df) @ self.w


def baseline_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """'Same as usual for this weekday': mean of the training nights with the same weekday."""
    means = train.groupby("weekday")["orders"].mean()
    return test["weekday"].map(means).fillna(train["orders"].mean()).to_numpy()


def split_by_time(df: pd.DataFrame, test_weeks: int = 12):
    """Test on the LAST weeks: the model never sees the future."""
    cut = df["date"].max() - pd.Timedelta(weeks=test_weeks)
    return df[df["date"] <= cut], df[df["date"] > cut]


def mae(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    if len(y_true) == 0:
        raise ValueError("mae of an empty list")
    return float(np.mean(np.abs(y_true - y_pred)))


def interval(model: OrdersModel, pred: float, z: float = 1.645) -> tuple[float, float]:
    """~90% prediction interval, assuming errors are roughly normal (check it: see EVIDENCE.md)."""
    return pred - z * model.resid_std, pred + z * model.resid_std


def evaluate() -> dict:
    from oracle.cleaning import load_clean
    df = load_clean()
    train, test = split_by_time(df)
    m = OrdersModel().fit(train)
    pred = m.predict_df(test)
    lo, hi = pred - 1.645 * m.resid_std, pred + 1.645 * m.resid_std
    y = test["orders"].to_numpy()
    return {
        "train_nights": len(train), "test_nights": len(test),
        "mae_model": round(mae(y, pred), 2),
        "mae_baseline": round(mae(y, baseline_predict(train, test)), 2),
        "interval_coverage_90": round(float(np.mean((y >= lo) & (y <= hi))), 3),
    }


if __name__ == "__main__":
    print(evaluate())
