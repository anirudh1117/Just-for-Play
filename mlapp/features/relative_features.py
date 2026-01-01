import numpy as np
import pandas as pd


INDEX_SYMBOL = "NIFTY 50"   # centralize later if needed


def _compute_index_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute index-only features (5m).
    Output indexed by ts.
    """
    idx = df[df["symbol"] == INDEX_SYMBOL].copy()
    idx = idx.sort_values("ts")

    # Index return
    idx["idx_ret_1"] = np.log(idx["close"]).diff()

    # Index EMA
    idx["idx_ema_21"] = idx["close"].ewm(span=21, adjust=False).mean()

    # Index RSI
    delta = idx["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    idx["idx_rsi_14"] = 100 - (100 / (1 + rs))

    # ---- STRICT LAG ----
    lag_cols = ["idx_ret_1", "idx_ema_21", "idx_rsi_14"]
    idx[lag_cols] = idx[lag_cols].shift(1)

    return idx[["ts"] + lag_cols]

def add_relative_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Join index features to stock features and compute relative strength.
    """
    df = df.sort_values(["symbol", "ts"]).copy()

    idx_feat = _compute_index_features(df)

    # Join index features on timestamp
    df = df.merge(idx_feat, on="ts", how="left")

    # Relative features
    df["rel_ret_1"] = df["ret_1"] - df["idx_ret_1"]
    df["rel_trend_21"] = df["ema_21"] - df["idx_ema_21"]

    return df

