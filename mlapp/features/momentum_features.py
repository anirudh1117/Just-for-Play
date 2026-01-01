import pandas as pd
import numpy as np


def _rsi(series: pd.Series, window: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def build_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds RSI-based momentum features.
    """
    df = df.sort_values(["symbol", "ts"]).copy()

    df["rsi_14"] = (
        df.groupby("symbol")["close"]
        .transform(lambda x: _rsi(x, 14))
    )

    # ---- STRICT LAG ----
    df["rsi_14"] = df.groupby("symbol")["rsi_14"].shift(1)

    return df
