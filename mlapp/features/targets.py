import pandas as pd
import numpy as np


# ---------------------------------------------------------
# STEP 1: Forward Returns
# ---------------------------------------------------------

def add_forward_returns(df):
    df = df.sort_values(["symbol", "ts"])

    df["fwd_close_1m"] = df.groupby("symbol")["close"].shift(-1)
    df["fwd_close_3m"] = df.groupby("symbol")["close"].shift(-3)
    df["fwd_close_5m"] = df.groupby("symbol")["close"].shift(-5)
    df["fwd_close_10m"] = df.groupby("symbol")["close"].shift(-10)

    # Compute forward pct returns
    df["fwd_ret_1m"] = (df["fwd_close_1m"] - df["close"]) / df["close"]
    df["fwd_ret_3m"] = (df["fwd_close_3m"] - df["close"]) / df["close"]
    df["fwd_ret_5m"] = (df["fwd_close_5m"] - df["close"]) / df["close"]
    df["fwd_ret_10m"] = (df["fwd_close_10m"] - df["close"]) / df["close"]

    return df


# ---------------------------------------------------------
# STEP 2: Binary Classification Targets
# ---------------------------------------------------------

def add_binary_targets(df, threshold=0.0012):
    """
    threshold = 0.12% return = 0.0012
    """
    df["target_up_5m"] = (df["fwd_ret_5m"] > threshold).astype(int)
    df["target_up_10m"] = (df["fwd_ret_10m"] > threshold).astype(int)

    return df


# ---------------------------------------------------------
# STEP 3: ATR-based directional confidence
# ---------------------------------------------------------

def add_vol_adj_targets(df):
    """
    Volatility adjusted targets:
    If forward return > ATR fraction, label = 1
    """
    df["atr_target_5m"] = (df["fwd_ret_5m"] > df["atr_norm"] * 0.5).astype(int)
    df["atr_target_10m"] = (df["fwd_ret_10m"] > df["atr_norm"] * 0.5).astype(int)
    return df


# ---------------------------------------------------------
# STEP 4: Quality Control (Remove noisy periods)
# ---------------------------------------------------------

def clean_targets(df):
    # Remove candles with missing forward values
    df = df.dropna(subset=["fwd_ret_5m", "fwd_ret_10m"])

    # Remove first 10 minutes (too noisy)
    df = df[df["minute_of_day"] > 10]

    # Remove last 10 minutes (no future available)
    df = df[df["minute_of_day"] < 365]

    # Remove zero-volume candles
    df = df[df["volume"] > 0]

    return df
