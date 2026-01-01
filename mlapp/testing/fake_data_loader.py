# mlapp/testing/fake_data_loader.py

import pandas as pd
import numpy as np

class FakeBacktestDataLoader:
    """
    Generates synthetic 5-minute intraday candles for testing.
    Does NOT touch real data or Upstox data.
    """

    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)

    def _generate_day(self, day):
        ts = pd.Timestamp(day) + pd.Timedelta(hours=9, minutes=15)
        rows = []
        price = np.random.uniform(80, 200)  # random starting price

        for _ in range(78):  # 78 candles per day
            open_ = price
            high = price + np.random.uniform(0.2, 1.2)
            low = price - np.random.uniform(0.2, 1.0)
            close = np.random.uniform(low, high)
            vol = np.random.randint(5000, 15000)

            rows.append({
                "timestamp": ts,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": vol,
            })
            ts += pd.Timedelta(minutes=5)
            price = close

        return pd.DataFrame(rows)

    def run(self):
        data = {}
        dates = pd.date_range(self.start_date, self.end_date)

        for d in dates:
            df = self._generate_day(d)
            data[str(d.date())] = df

        return data
