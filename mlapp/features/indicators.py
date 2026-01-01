import pandas as pd
import numpy as np


# ---------------------------------------------------------
# PRICE FEATURES (already done in Step 2)
# ---------------------------------------------------------

def add_price_features(df):
    df = df.sort_values(["symbol", "ts"])

    df["ret_1m"] = df.groupby("symbol")["close"].pct_change()
    df["log_ret_1m"] = np.log(df["close"] / df.groupby("symbol")["close"].shift(1))

    df["ret_5m"] = df.groupby("symbol")["close"].pct_change(5)
    df["ret_10m"] = df.groupby("symbol")["close"].pct_change(10)
    df["ret_15m"] = df.groupby("symbol")["close"].pct_change(15)

    df["ma_5"] = df.groupby("symbol")["close"].transform(lambda x: x.rolling(5).mean())
    df["ma_10"] = df.groupby("symbol")["close"].transform(lambda x: x.rolling(10).mean())
    df["ma_20"] = df.groupby("symbol")["close"].transform(lambda x: x.rolling(20).mean())

    df["body"] = (df["close"] - df["open"]).abs()
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]

    df["body_ratio"] = df["body"] / (df["high"] - df["low"] + 1e-6)
    df["upper_wick_ratio"] = df["upper_wick"] / (df["high"] - df["low"] + 1e-6)
    df["lower_wick_ratio"] = df["lower_wick"] / (df["high"] - df["low"] + 1e-6)

    df["is_bull"] = (df["close"] > df["open"]).astype(int)
    df["is_bear"] = (df["close"] < df["open"]).astype(int)
    df["is_strong_bull"] = ((df["close"] > df["open"]) & (df["body_ratio"] > 0.6)).astype(int)
    df["is_strong_bear"] = ((df["close"] < df["open"]) & (df["body_ratio"] > 0.6)).astype(int)

    return df


# ---------------------------------------------------------
# VOLUME FEATURES (Step 3)
# ---------------------------------------------------------

def add_volume_features(df):
    df = df.sort_values(["symbol", "ts"])

    # 1. Volume % change
    df["vol_change"] = df.groupby("symbol")["volume"].pct_change()

    # 2. Rolling average volume
    df["vol_ma_20"] = df.groupby("symbol")["volume"].transform(lambda x: x.rolling(20).mean())

    # 3. Relative volume (actual vs rolling avg)
    df["vol_relative"] = df["volume"] / (df["vol_ma_20"] + 1e-6)

    # 4. Volume z-score (detect spikes)
    df["vol_z"] = df.groupby("symbol")["volume"].transform(lambda x: (x - x.mean()) / (x.std() + 1e-6))

    return df


# ---------------------------------------------------------
# VOLATILITY FEATURES (Step 3)
# ---------------------------------------------------------

def add_volatility_features(df):
    df = df.sort_values(["symbol", "ts"])

    # True Range components
    df["prev_close"] = df.groupby("symbol")["close"].shift(1)

    df["tr1"] = df["high"] - df["low"]
    df["tr2"] = (df["high"] - df["prev_close"]).abs()
    df["tr3"] = (df["low"] - df["prev_close"]).abs()

    # True Range
    df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

    # ATR (14-period)
    df["atr_14"] = df.groupby("symbol")["true_range"].transform(lambda x: x.rolling(14).mean())

    # Normalized ATR (important for intraday volatility)
    df["atr_norm"] = df["atr_14"] / (df["close"] + 1e-6)

    return df


# ---------------------------------------------------------
# VWAP FEATURES (Step 3)
# ---------------------------------------------------------

def add_vwap(df):
    df = df.sort_values(["symbol", "ts"])

    # Typical price
    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3

    # Compute cumulative values inside each day
    df["cum_tp_vol"] = df.groupby(["symbol", df["ts"].dt.date]) \
                         .apply(lambda g: (g["tp"] * g["volume"]).cumsum()) \
                         .reset_index(level=[0,1], drop=True)

    df["cum_vol"] = df.groupby(["symbol", df["ts"].dt.date])["volume"].cumsum()

    # VWAP = cumulative(tp*vol) / cumulative(vol)
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

    # -----------------------------
    # EMA indicators
    # -----------------------------

    df["ema_5"] = df.groupby("symbol")["close"].transform(lambda x: ema(x, 5))
    df["ema_10"] = df.groupby("symbol")["close"].transform(lambda x: ema(x, 10))
    df["ema_20"] = df.groupby("symbol")["close"].transform(lambda x: ema(x, 20))

    # Trend strength: close - ema
    df["close_ema_diff"] = df["close"] - df["ema_10"]

    # -----------------------------
    # RSI (14)
    # -----------------------------

    df["rsi_14"] = df.groupby("symbol")["close"].transform(lambda x: compute_rsi(x))

    # Overbought/Oversold flags
    df["rsi_overbought"] = (df["rsi_14"] > 70).astype(int)
    df["rsi_oversold"] = (df["rsi_14"] < 30).astype(int)

    # -----------------------------
    # Stochastic RSI
    # -----------------------------

    df["stoch_rsi"] = df.groupby("symbol")["rsi_14"].transform(lambda x: compute_stoch_rsi(x))
    df["stoch_rsi_k"] = df.groupby("symbol")["stoch_rsi"].transform(lambda x: x.rolling(3).mean())
    df["stoch_rsi_d"] = df.groupby("symbol")["stoch_rsi_k"].transform(lambda x: x.rolling(3).mean())

    # -----------------------------
    # MACD
    # -----------------------------

    df["ema_12"] = df.groupby("symbol")["close"].transform(lambda x: ema(x, 12))
    df["ema_26"] = df.groupby("symbol")["close"].transform(lambda x: ema(x, 26))
    df["macd"] = df["ema_12"] - df["ema_26"]
    df["macd_signal"] = df.groupby("symbol")["macd"].transform(lambda x: x.ewm(span=9, adjust=False).mean())
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # MACD signal crossover flags
    df["macd_bull_cross"] = (df["macd"] > df["macd_signal"]).astype(int)
    df["macd_bear_cross"] = (df["macd"] < df["macd_signal"]).astype(int)

    return df
