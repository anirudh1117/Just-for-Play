import pandas as pd
import numpy as np


def build_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds ATR-based volatility features.
    """
    df = df.sort_values(["symbol", "ts"]).copy()

    high = df["high"]
    low = df["low"]
    close = df.groupby("symbol")["close"].shift(1)

    tr = pd.concat([
        high - low,
        (high - close).abs(),
        (low - close).abs(),
    ], axis=1).max(axis=1)

    df["atr_14"] = (
        tr.groupby(df["symbol"])
        .rolling(14)
        .mean()
        .reset_index(level=0, drop=True)
    )

    # ---- STRICT LAG ----
    df["atr_14"] = df.groupby("symbol")["atr_14"].shift(1)

    return df
