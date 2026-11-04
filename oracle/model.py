"""Block 7: a linear regression written by hand (least squares), against a simple baseline.
Block 8: a prediction interval from the model's errors on unseen weeks.
"""
import numpy as np
import pandas as pd

from oracle import config


NAMES = ["monday_base", "tue", "wed", "thu", "fri", "sat", "sun",
         "rain", "cool_calm", "biryani", "before_holiday", "start_of_month"]


def cool_calm(temp_c: float, wind_kmh: float) -> bool:
    """Owner: cool and no wind -> the smell of food spreads in the street."""
    return config.COOL_MIN_C <= temp_c < config.COOL_MAX_C and wind_kmh < config.CALM_WIND_KMH


def features(weekday: int, rain=0, temp_c=15.0, wind_kmh=10.0, biryani=0,
             before_holiday=0, start_of_month=0) -> np.ndarray:
    """1 (intercept) + one-hot weekday (Tue..Sun; Monday is the reference) + the owner's factors."""
    x = [1.0] + [1.0 if weekday == d else 0.0 for d in range(1, 7)]
    x += [float(rain), float(cool_calm(temp_c, wind_kmh)), float(biryani),
          float(before_holiday), float(start_of_month)]
    return np.array(x)


def design(df: pd.DataFrame) -> np.ndarray:
    return np.array([features(r.weekday, r.rain, r.temp_c, r.wind_kmh, r.biryani,
                              r.before_holiday, r.start_of_month) for r in df.itertuples()])


def clip(x):
    """Never predict fewer than 0 or more than the 30 seats."""
    return np.clip(x, 0, config.SEATS)


class GuestsModel:
    def fit(self, df: pd.DataFrame) -> "GuestsModel":
        X, y = design(df), df["guests"].to_numpy(float)
        # least squares: w = argmin ||Xw - y||^2
        self.w, *_ = np.linalg.lstsq(X, y, rcond=None)
        self.resid_std = float(np.std(y - X @ self.w, ddof=X.shape[1]))
        return self

    def predict(self, weekday: int, **factors) -> float:
        return float(clip(features(weekday, **factors) @ self.w))

    def predict_df(self, df: pd.DataFrame) -> np.ndarray:
        return clip(design(df) @ self.w)

    def effects(self) -> dict:
        """Readable coefficients: how many guests each factor adds."""
        return {n: round(float(v), 1) for n, v in zip(NAMES, self.w)}


def baseline_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """'Same as usual for this weekday': mean of the training nights with the same weekday."""
    means = train.groupby("weekday")["guests"].mean()
    return test["weekday"].map(means).fillna(train["guests"].mean()).to_numpy()


def split_by_time(df: pd.DataFrame, test_weeks: int = 12):
    """Test on the LAST weeks: the model never sees the future."""
    cut = df["date"].max() - pd.Timedelta(weeks=test_weeks)
    return df[df["date"] <= cut], df[df["date"] > cut]


def mae(y_true, y_pred) -> float:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    if len(y_true) == 0:
        raise ValueError("mae of an empty list")
    return float(np.mean(np.abs(y_true - y_pred)))


def interval(model: GuestsModel, pred: float, z: float = 1.645) -> tuple[float, float]:
    """~90% prediction interval, assuming errors are roughly normal, clipped to 0..30 seats."""
    lo, hi = clip(pred - z * model.resid_std), clip(pred + z * model.resid_std)
    return float(lo), float(hi)


def evaluate() -> dict:
    from oracle.cleaning import load_clean
    df = load_clean()
    train, test = split_by_time(df)
    m = GuestsModel().fit(train)
    pred = m.predict_df(test)
    lo, hi = clip(pred - 1.645 * m.resid_std), clip(pred + 1.645 * m.resid_std)
    y = test["guests"].to_numpy()
    return {
        "train_nights": len(train), "test_nights": len(test),
        "mae_model": round(mae(y, pred), 2),
        "mae_baseline": round(mae(y, baseline_predict(train, test)), 2),
        "interval_coverage_90": round(float(np.mean((y >= lo) & (y <= hi))), 3),
        "effects_in_guests": m.effects(),
    }


if __name__ == "__main__":
    print(evaluate())
