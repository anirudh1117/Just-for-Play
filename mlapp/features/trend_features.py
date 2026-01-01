import pandas as pd


EMA_WINDOWS = [9, 21, 50]


def build_trend_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds EMA-based trend features.
    Assumes df contains: symbol, ts, close
    """
    df = df.sort_values(["symbol", "ts"]).copy()

    for w in EMA_WINDOWS:
        df[f"ema_{w}"] = (
            df.groupby("symbol")["close"]
            .transform(lambda x: x.ewm(span=w, adjust=False).mean())
        )

    # EMA relationships
    df["ema_ratio_9_21"] = df["ema_9"] / df["ema_21"]

    # EMA slope (trend strength)
    df["ema_slope_9"] = (
        df.groupby("symbol")["ema_9"]
        .diff()
    )

    # ---- STRICT LAG ----
    lag_cols = (
        [f"ema_{w}" for w in EMA_WINDOWS] +
        ["ema_ratio_9_21", "ema_slope_9"]
    )
    df[lag_cols] = df.groupby("symbol")[lag_cols].shift(1)

    return df
