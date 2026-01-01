import numpy as np
import pandas as pd
from mlapp.features.config import FEATURE_VERSION, RETURN_WINDOWS


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    # ts must be datetime
    minutes = df["ts"].dt.hour * 60 + df["ts"].dt.minute
    df["minute_sin"] = np.sin(2 * np.pi * minutes / (6.5 * 60))
    df["minute_cos"] = np.cos(2 * np.pi * minutes / (6.5 * 60))
    df["day_of_week"] = df["ts"].dt.weekday
    return df


def build_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input df columns (required):
    ['symbol','ts','open','high','low','close','volume']

    Output:
    Adds base features with STRICT lag (T-1).
    """
    df = df.sort_values(["symbol", "ts"]).copy()

    # ---------- Candle structure ----------
    df["candle_body"] = (df["close"] - df["open"]) / df["close"].replace(0, np.nan)
    df["candle_range"] = (df["high"] - df["low"]) / df["close"].replace(0, np.nan)

    # ---------- Returns (LOG RETURNS) ----------
    for w in RETURN_WINDOWS:
        df[f"ret_{w}"] = (
            np.log(df["close"])
            .groupby(df["symbol"])
            .diff(w)
        )

    # ---------- STRICT LAG (prevent leakage) ----------
    feature_cols = (
        ["candle_body", "candle_range"] +
        [f"ret_{w}" for w in RETURN_WINDOWS]
    )

    df[feature_cols] = df.groupby("symbol")[feature_cols].shift(1)

    # ---------- Time features ----------
    df = _add_time_features(df)

    # ---------- Metadata ----------
    df["feature_version"] = FEATURE_VERSION

    return df
