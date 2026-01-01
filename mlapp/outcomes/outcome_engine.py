from datetime import timedelta
from dataclasses import dataclass


# ---------------------------------------------------------
# CONFIG (Phase 1 – locked)
# ---------------------------------------------------------

TP_PCT = 0.006      # +0.6%
SL_PCT = 0.004      # -0.4%
MAX_HOLD_MINUTES = 90


# ---------------------------------------------------------
# Result object (pure data)
# ---------------------------------------------------------

@dataclass
class TradeOutcomeResult:
    symbol: str
    date: str

    entry_time: object
    entry_price: float

    exit_time: object
    exit_price: float
    exit_reason: str      # TP | SL | TIMEOUT | INVALID

    holding_minutes: int
    R_multiple: float


# ---------------------------------------------------------
# Outcome Engine
# ---------------------------------------------------------

class OutcomeEngine:
    """
    Deterministic trade outcome evaluator.
    NO ML, NO randomness, NO DB writes.
    """

    def __init__(
        self,
        tp_pct=TP_PCT,
        sl_pct=SL_PCT,
        max_hold_minutes=MAX_HOLD_MINUTES,
    ):
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.max_hold_minutes = max_hold_minutes

    # -----------------------------------------------------
    # Main evaluation method
    # -----------------------------------------------------

    def evaluate(
        self,
        symbol,
        date,
        inference_end_time,
        candles_5m,
    ):
        """
        candles_5m: list of dicts sorted by ts ASC
        Each candle must contain:
        ts, open, high, low, close
        """

        # -------------------------
        # 1) Find entry candle
        # -------------------------
        entry_candle = None
        for c in candles_5m:
            if c["ts"] >= inference_end_time:
                entry_candle = c
                break

        if not entry_candle:
            return self._invalid(symbol, date)

        entry_price = entry_candle["open"]
        entry_time = entry_candle["ts"]

        tp_price = entry_price * (1 + self.tp_pct)
        sl_price = entry_price * (1 - self.sl_pct)

        # -------------------------
        # 2) Walk forward candles
        # -------------------------
        for c in candles_5m:
            if c["ts"] <= entry_time:
                continue

            holding_minutes = int(
                (c["ts"] - entry_time).total_seconds() / 60
            )

            # Timeout
            if holding_minutes >= self.max_hold_minutes:
                return self._timeout(
                    symbol, date,
                    entry_time, entry_price,
                    c["ts"], c["close"],
                    holding_minutes
                )

            # SL FIRST (conservative)
            if c["low"] <= sl_price:
                return self._sl_hit(
                    symbol, date,
                    entry_time, entry_price,
                    c["ts"], sl_price,
                    holding_minutes
                )

            # TP
            if c["high"] >= tp_price:
                return self._tp_hit(
                    symbol, date,
                    entry_time, entry_price,
                    c["ts"], tp_price,
                    holding_minutes
                )

        # -------------------------
        # 3) EOD timeout
        # -------------------------
        last_candle = candles_5m[-1]
        holding_minutes = int(
            (last_candle["ts"] - entry_time).total_seconds() / 60
        )

        return self._timeout(
            symbol, date,
            entry_time, entry_price,
            last_candle["ts"], last_candle["close"],
            holding_minutes
        )

    # -----------------------------------------------------
    # Outcome helpers
    # -----------------------------------------------------

    def _tp_hit(self, symbol, date, et, ep, xt, xp, hm):
        R = self.tp_pct / self.sl_pct
        return TradeOutcomeResult(
            symbol, date,
            et, ep,
            xt, xp,
            "TP",
            hm,
            round(R, 3)
        )

    def _sl_hit(self, symbol, date, et, ep, xt, xp, hm):
        return TradeOutcomeResult(
            symbol, date,
            et, ep,
            xt, xp,
            "SL",
            hm,
            -1.0
        )

    def _timeout(self, symbol, date, et, ep, xt, xp, hm):
        R = (xp - ep) / ep / self.sl_pct
        return TradeOutcomeResult(
            symbol, date,
            et, ep,
            xt, xp,
            "TIMEOUT",
            hm,
            round(R, 3)
        )

    def _invalid(self, symbol, date):
        return TradeOutcomeResult(
            symbol, date,
            None, None,
            None, None,
            "INVALID",
            0,
            0.0
        )
