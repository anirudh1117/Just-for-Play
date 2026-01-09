import pandas as pd

from mlapp.training.label_params import (
    TP_PCT,
    SL_PCT,
    MAX_HOLD_CANDLES
)


def generate_trade_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate binary labels for training.

    Input:
        df with columns:
        - symbol
        - ts
        - open, high, low, close

    Output:
        df with new column:
        - target_up_5m (0/1)

    Assumes df is sorted by (symbol, ts)
    """

    df = df.copy()
    df["target_up_5m"] = 0  # default loss

    grouped = df.groupby("symbol", group_keys=False)

    for symbol, g in grouped:
        g = g.sort_values("ts").reset_index()

        for i in range(len(g)):
            entry_price = g.loc[i, "close"]
            tp = entry_price * (1 + TP_PCT)
            sl = entry_price * (1 - SL_PCT)

            future = g.iloc[i + 1 : i + 1 + MAX_HOLD_CANDLES]

            hit = 0
            for _, row in future.iterrows():
                if row["high"] >= tp:
                    hit = 1
                    break
                if row["low"] <= sl:
                    hit = 0
                    break

            df.loc[g.loc[i, "index"], "target_up_5m"] = hit

    return df
