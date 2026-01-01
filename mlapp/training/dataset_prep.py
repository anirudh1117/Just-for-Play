import pandas as pd


def clean_dataset(df):
    """
    Remove non-feature columns and prepare dataset for ML.
    """
    drop_cols = [
        "open", "high", "low",
        "body", "upper_wick", "lower_wick",
        "tr1", "tr2", "tr3",
        "prev_close", "tp",
        "cum_tp_vol", "cum_vol",
        "fwd_close_1m", "fwd_close_3m", "fwd_close_5m", "fwd_close_10m",
    ]

    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    return df


def split_by_date(df, train_days=80, valid_days=10, test_days=1):
    """
    Time-based split (NO leakage). Splits by unique dates.
    """
    df["date"] = df["ts"].dt.date
    unique_days = sorted(df["date"].unique())

    train_cut = unique_days[:train_days]
    valid_cut = unique_days[train_days:train_days + valid_days]
    test_cut = unique_days[train_days + valid_days:train_days + valid_days + test_days]

    df_train = df[df["date"].isin(train_cut)]
    df_valid = df[df["date"].isin(valid_cut)]
    df_test = df[df["date"].isin(test_cut)]

    return df_train, df_valid, df_test
