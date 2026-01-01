import pandas as pd
import numpy as np


class LiveFeatureEngine:
    """
    Converts the last N (≈ 10–20) 1-minute live candles into ML-ready features.
    """

    def __init__(self, candles_dict):
        self.candles_dict = candles_dict

    # -------------------------------------------
    # Helper indicators
    # -------------------------------------------
    def _ema(self, series, span):
        return series.ewm(span=span, adjust=False).mean()

    def _rsi(self, close, period=14):
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _atr(self, df, period=14):
        df["h-l"] = df["high"] - df["low"]
        df["h-pc"] = (df["high"] - df["close"].shift()).abs()
        df["l-pc"] = (df["low"] - df["close"].shift()).abs()
        tr = df[["h-l", "h-pc", "l-pc"]].max(axis=1)
        return tr.rolling(period).mean()

    def _vwap(self, df):
        typical = (df["high"] + df["low"] + df["close"]) / 3
        cum_vol = df["volume"].cumsum()
        cum_tp_vol = (typical * df["volume"]).cumsum()
        return cum_tp_vol / cum_vol

    # -------------------------------------------
    # Main Feature Computation
    # -------------------------------------------
    def compute_for_symbol(self, symbol, candles):
        df = pd.DataFrame(candles)

        if len(df) < 5:
            return None  # not enough candles yet

        # Ensure sorted
        df = df.sort_values("ts")

        # Core indicators
        df["return"] = df["close"].pct_change()

        df["ema_5"] = self._ema(df["close"], 5)
        df["ema_10"] = self._ema(df["close"], 10)
        df["ema_20"] = self._ema(df["close"], 20)

        df["rsi_14"] = self._rsi(df["close"], 14)
        df["atr_14"] = self._atr(df, 14)

        df["vwap"] = self._vwap(df)

        # Take only the latest row for ML
        last = df.iloc[-1].copy()
        last["symbol"] = symbol

        return last

    def run(self):
        """
        Returns a DataFrame with one feature row per symbol.
        """
        rows = []

        for symbol, candles in self.candles_dict.items():
            r = self.compute_for_symbol(symbol, candles)
            if r is not None:
                rows.append(r)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # Clean missing values
        df = df.dropna()

        return df
