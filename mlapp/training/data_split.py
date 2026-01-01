import pandas as pd
from datetime import timedelta


def rolling_time_split(
    df: pd.DataFrame,
    train_days=200,
    valid_days=40,
    test_days=20,
):
    """
    Returns:
        train_df, valid_df, test_df
    """
    df = df.sort_values("ts").copy()

    last_date = df["ts"].max().normalize()

    test_start = last_date - timedelta(days=test_days)
    valid_start = test_start - timedelta(days=valid_days)
    train_start = valid_start - timedelta(days=train_days)

    train_df = df[(df["ts"] >= train_start) & (df["ts"] < valid_start)]
    valid_df = df[(df["ts"] >= valid_start) & (df["ts"] < test_start)]
    test_df  = df[df["ts"] >= test_start]

    return train_df, valid_df, test_df
