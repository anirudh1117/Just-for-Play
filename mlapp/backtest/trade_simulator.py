# mlapp/backtest/trade_simulator.py

import pandas as pd
from datetime import timedelta
import numpy as np


class TradeSimulator:
    """
    Simulates trades for a single day across multiple stocks.
    Now supports strategy optimization parameters:
    - entry_rule
    - sl_mult
    - tp_mult
    - confidence_threshold
    - holding_time
    """

    def __init__(self, minutes=20, strict_mode=True):
        self.minutes = minutes
        self.strict_mode = strict_mode

        # Default strategy parameters
        self.entry_rule = "breakout_20"
        self.sl_mult = 1.5
        self.tp_mult = 2.0
        self.confidence_threshold = 0.60
        self.holding_time = 30  # in minutes

    # ---------------------------------------------------------
    # Inject strategy parameters
    # ---------------------------------------------------------
    def set_strategy_params(self, entry_rule, sl_mult, tp_mult,
                            confidence_threshold, holding_time):

        self.entry_rule = entry_rule
        self.sl_mult = sl_mult
        self.tp_mult = tp_mult
        self.confidence_threshold = confidence_threshold
        self.holding_time = holding_time

    # ---------------------------------------------------------
    # Apply Entry Rules
    # ---------------------------------------------------------
    def get_entry_price(self, df):
        """
        df = full intraday candle dataframe (sorted ascending)

        Returns:
            entry_price or None
        """

        if self.entry_rule == "breakout_20":
            return self._breakout_n(df, 20)

        elif self.entry_rule == "breakout_15":
            return self._breakout_n(df, 15)

        elif self.entry_rule == "ema20_cross":
            return self._ema20_cross(df)

        elif self.entry_rule == "vwap_break":
            return self._vwap_break(df)

        return None

    # ----------------------
    # 1. 20-min / 15-min breakout
    # ----------------------
    def _breakout_n(self, df, n):
        subset = df.iloc[:n // 5]  # convert minutes → 5min candles
        if subset.empty:
            return None

        high_level = subset["high"].max()

        # Breakout detection
        breakout_rows = df[df["close"] > high_level]
        if breakout_rows.empty:
            return None

        first_break = breakout_rows.iloc[0]
        return {
            "entry_price": first_break["close"],
            "entry_time": first_break["timestamp"]
        }

    # ----------------------
    # 2. EMA20 cross
    # ----------------------
    def _ema20_cross(self, df):
        df = df.copy()
        df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()

        cond = df["close"] > df["ema20"]
        crossed = cond & (~cond.shift(1).fillna(False))

        rows = df[crossed]
        if rows.empty:
            return None

        first = rows.iloc[0]
        return {
            "entry_price": first["close"],
            "entry_time": first["timestamp"]
        }

    # ----------------------
    # 3. VWAP breakout
    # ----------------------
    def _vwap_break(self, df):
        df = df.copy()

        df["pv"] = df["close"] * df["volume"]
        df["cum_pv"] = df["pv"].cumsum()
        df["cum_vol"] = df["volume"].cumsum()

        df["vwap"] = df["cum_pv"] / df["cum_vol"]

        cond = df["close"] > df["vwap"]
        crossed = cond & (~cond.shift(1).fillna(False))

        rows = df[crossed]
        if rows.empty:
            return None

        first = rows.iloc[0]
        return {
            "entry_price": first["close"],
            "entry_time": first["timestamp"]
        }

    # ---------------------------------------------------------
    # ATR calculation
    # ---------------------------------------------------------
    def compute_atr(self, df, period=14):
        df = df.copy()
        df["hl"] = df["high"] - df["low"]
        df["hc"] = (df["high"] - df["close"].shift(1)).abs()
        df["lc"] = (df["low"] - df["close"].shift(1)).abs()

        df["tr"] = df[["hl", "hc", "lc"]].max(axis=1)
        atr = df["tr"].rolling(period).mean().iloc[-1]

        if pd.isna(atr):
            return None

        return atr

    # ---------------------------------------------------------
    # MAIN DAY SIMULATION
    # ---------------------------------------------------------
    def run_day(self, symbol_dict, model):
        """
        symbol_dict = {"TATAMOTORS": df, "RELIANCE": df2}
        model = trained LightGBM model
        """

        rows = []

        for sym, df in symbol_dict.items():
            df = df.sort_values("timestamp")

            # ----------------------------
            # 1. Predict using ML model
            # ----------------------------
            try:
                pred = model.predict(df)[0]
            except:
                continue

            # Confidence threshold
            if pred < self.confidence_threshold:
                continue

            # ----------------------------
            # 2. Determine entry rule
            # ----------------------------
            entry = self.get_entry_price(df)
            if entry is None:
                continue

            entry_price = entry["entry_price"]
            entry_time = entry["entry_time"]

            # ----------------------------
            # 3. Compute ATR for SL & TP
            # ----------------------------
            atr = self.compute_atr(df)
            if atr is None:
                continue

            sl = atr * self.sl_mult
            tp = atr * self.tp_mult

            sl_price = entry_price - sl
            tp_price = entry_price + tp

            # ----------------------------
            # 4. Holding time constraint
            # ----------------------------
            exit_cutoff = entry_time + timedelta(minutes=self.holding_time)

            # ----------------------------
            # 5. Trade simulation candle by candle
            # ----------------------------
            df_future = df[df["timestamp"] >= entry_time]

            result = 0
            exit_price = entry_price

            for _, r in df_future.iterrows():
                cur_time = r["timestamp"]
                high = r["high"]
                low = r["low"]

                # Stoploss hit
                if low <= sl_price:
                    exit_price = sl_price
                    result = -1
                    break

                # Target hit
                if high >= tp_price:
                    exit_price = tp_price
                    result = 1
                    break

                # Holding time exit
                if cur_time >= exit_cutoff:
                    exit_price = r["close"]
                    result = 1 if exit_price > entry_price else -1 if exit_price < entry_price else 0
                    break

            # ----------------------------
            # 6. Save row
            # ----------------------------
            rows.append({
                "symbol": sym,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "entry_time": entry_time,
                "exit_time": cur_time,
                "result": result,
                "atr": atr,
                "sl_mult": self.sl_mult,
                "tp_mult": self.tp_mult,
            })

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows)
