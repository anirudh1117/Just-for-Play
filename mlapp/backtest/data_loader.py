import pandas as pd
from datetime import timedelta
from market.models import Candle
from django.db.models import Q


class BacktestDataLoader:
    """
    Loads historical 1-min candles from DB and groups them by day.
    """

    def __init__(self, symbol, start_date, end_date):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date

    def load_candles(self):
        """
        Loads candles for the given symbol & date range.
        """
        qs = (
            Candle.objects
            .filter(
                symbol=self.symbol,
                ts__date__gte=self.start_date,
                ts__date__lte=self.end_date,
                interval="1min"
            )
            .order_by("ts")
            .values("ts", "open", "high", "low", "close", "volume")
        )

        df = pd.DataFrame(list(qs))
        if df.empty:
            return {}

        # Add date column
        df["date"] = df["ts"].dt.date
        return df

    def group_by_day(self, df):
        """
        Convert DF of all candles → dict of daily candles.
        """
        grouped = {}

        for day in sorted(df["date"].unique()):
            day_df = df[df["date"] == day].copy()
            grouped[str(day)] = day_df

        return grouped

    def run(self):
        """
        Final entrypoint:
        Load → group → return dictionary of daily DF.
        """
        df = self.load_candles()
        if isinstance(df, dict):  # empty
            return {}

        return self.group_by_day(df)
