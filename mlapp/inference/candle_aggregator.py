import pandas as pd


def aggregate_1m_to_5m(df_1m: pd.DataFrame) -> pd.DataFrame:
    """
    Convert 1-minute candles to 5-minute candles.
    Assumes columns:
      symbol, ts, open, high, low, close, volume
    """

    df = df_1m.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values(["symbol", "ts"])

    df.set_index("ts", inplace=True)

    agg = (
        df.groupby("symbol")
        .resample("5T")
        .agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        })
        .dropna()
        .reset_index()
    )

    return agg
