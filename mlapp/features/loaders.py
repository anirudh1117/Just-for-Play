import pandas as pd
from datetime import datetime, timedelta
from market.models import Candle


def load_candles_df(days):
    """
    Load last N days of candles from DB into a pandas DataFrame.
    """

    start_ts = datetime.now() - timedelta(days=days)

    qs = Candle.objects.filter(ts__gte=start_ts).select_related("instrument")

    rows = []
    for c in qs:
        rows.append({
            "instrument_id": c.instrument_id,
            "symbol": c.instrument.symbol,
            "ts": c.ts,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        })

    return pd.DataFrame(rows)
