from datetime import datetime, timedelta


class CandleBuilder:
    """
    Builds 1-minute candles from live ticks for each symbol.
    Stores only the last N candles in memory (typically 20).
    """

    def __init__(self, max_candles=20):
        self.max_candles = max_candles
        self.candles = {}  # {symbol: [candle_dict...]}

    def _new_candle(self, ts, price, volume):
        return {
            "ts": ts,
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": volume,
        }

    def add_tick(self, symbol, price, volume, ts):
        """
        Add a new tick into the correct 1-minute candle.
        """
        minute_ts = ts.replace(second=0, microsecond=0)

        if symbol not in self.candles:
            self.candles[symbol] = [self._new_candle(minute_ts, price, volume)]
            return

        last_candle = self.candles[symbol][-1]

        # --- NEW CANDLE NEEDED ---
        if last_candle["ts"] != minute_ts:
            new_c = self._new_candle(minute_ts, price, volume)
            self.candles[symbol].append(new_c)

            # limit size
            if len(self.candles[symbol]) > self.max_candles:
                self.candles[symbol].pop(0)

            return

        # --- UPDATE EXISTING CANDLE ---
        last_candle["close"] = price
        last_candle["volume"] += volume
        last_candle["high"] = max(last_candle["high"], price)
        last_candle["low"] = min(last_candle["low"], price)

    def get_recent_candles(self, symbol):
        return self.candles.get(symbol, [])
