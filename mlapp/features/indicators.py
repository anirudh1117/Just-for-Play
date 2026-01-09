import pandas as pd
import numpy as np


# ---------------------------------------------------------
# PRICE FEATURES (already done in Step 2)
# ---------------------------------------------------------

def add_price_features(df):
    df = df.sort_values(["symbol", "ts"])
    g = df.groupby("symbol")

    close_s = g["close"].shift(1)
    open_s  = g["open"].shift(1)
    high_s  = g["high"].shift(1)
    low_s   = g["low"].shift(1)

    df["ret_1m"] = close_s.pct_change()
    df["log_ret_1m"] = np.log(close_s / close_s.shift(1))

    df["ret_5m"]  = close_s.pct_change(5)
    df["ret_10m"] = close_s.pct_change(10)
    df["ret_15m"] = close_s.pct_change(15)

    df["ma_5"]  = close_s.rolling(5).mean()
    df["ma_10"] = close_s.rolling(10).mean()
    df["ma_20"] = close_s.rolling(20).mean()

    body = (close_s - open_s).abs()
    range_ = (high_s - low_s) + 1e-6

    df["body_ratio"] = body / range_
    df["upper_wick_ratio"] = (high_s - close_s) / range_
    df["lower_wick_ratio"] = (close_s - low_s) / range_

    df["is_bull"] = (close_s > open_s).astype(int)
    df["is_bear"] = (close_s < open_s).astype(int)

    return df



# ---------------------------------------------------------
# VOLUME FEATURES (Step 3)
# ---------------------------------------------------------

def add_volume_features(df):
    df = df.sort_values(["symbol", "ts"])
    g = df.groupby("symbol")

    vol_s = g["volume"].shift(1)

    df["vol_change"] = vol_s.pct_change()
    df["vol_ma_20"] = vol_s.rolling(20).mean()
    df["vol_relative"] = vol_s / (df["vol_ma_20"] + 1e-6)

    # rolling z-score ONLY (no global mean)
    df["vol_z"] = (
        (vol_s - vol_s.rolling(50).mean()) /
        (vol_s.rolling(50).std() + 1e-6)
    )

    return df



# ---------------------------------------------------------
# VOLATILITY FEATURES (Step 3)
# ---------------------------------------------------------

def add_volatility_features(df):
    df = df.sort_values(["symbol", "ts"])
    g = df.groupby("symbol")

    high_s = g["high"].shift(1)
    low_s  = g["low"].shift(1)
    close_s = g["close"].shift(1)

    prev_close = close_s.shift(1)

    tr1 = high_s - low_s
    tr2 = (high_s - prev_close).abs()
    tr3 = (low_s - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    df["atr_14"] = true_range.rolling(14).mean()
    df["atr_norm"] = df["atr_14"] / (close_s + 1e-6)

    return df



# ---------------------------------------------------------
# VWAP FEATURES (Step 3)
# ---------------------------------------------------------

def add_vwap(df):
    df = df.sort_values(["symbol", "ts"])
    g = df.groupby(["symbol", df["ts"].dt.date])

    tp = (df["high"] + df["low"] + df["close"]) / 3
    tp_s = tp.groupby(df["symbol"]).shift(1)
    vol_s = df.groupby("symbol")["volume"].shift(1)

    df["cum_tp_vol"] = (tp_s * vol_s).groupby([df["symbol"], df["ts"].dt.date]).cumsum()
    df["cum_vol"] = vol_s.groupby([df["symbol"], df["ts"].dt.date]).cumsum()

    df["vwap"] = df["cum_tp_vol"] / (df["cum_vol"] + 1e-6)

    return df


# ---------------------------------------------------------
# MOMENTUM INDICATORS (Step 4)
# ---------------------------------------------------------

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()

    rs = avg_gain / (avg_loss + 1e-6)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_stoch_rsi(rsi_series, period=14):
    min_rsi = rsi_series.rolling(period).min()
    max_rsi = rsi_series.rolling(period).max()
    stoch_rsi = (rsi_series - min_rsi) / (max_rsi - min_rsi + 1e-6)
    return stoch_rsi


def add_momentum_features(df):
    df = df.sort_values(["symbol", "ts"])
    g = df.groupby("symbol")

    close_s = g["close"].shift(1)

    df["ema_5"]  = close_s.ewm(span=5, adjust=False).mean()
    df["ema_10"] = close_s.ewm(span=10, adjust=False).mean()
    df["ema_20"] = close_s.ewm(span=20, adjust=False).mean()

    df["close_ema_diff"] = close_s - df["ema_10"]

    # ✅ RSI (fixed)
    df["rsi_14"] = g["close"].transform(
        lambda x: compute_rsi(x.shift(1))
    )

    df["rsi_overbought"] = (df["rsi_14"] > 70).astype(int)
    df["rsi_oversold"] = (df["rsi_14"] < 30).astype(int)

    df["stoch_rsi"] = g["rsi_14"].transform(compute_stoch_rsi)

    df["ema_12"] = close_s.ewm(span=12, adjust=False).mean()
    df["ema_26"] = close_s.ewm(span=26, adjust=False).mean()

    df["macd"] = df["ema_12"] - df["ema_26"]
    df["macd_signal"] = g["macd"].shift(1).ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    return df

