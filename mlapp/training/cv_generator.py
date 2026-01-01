def generate_time_cv_splits(df, fold_size=5, step_size=5):
    """
    Rolling cross-validation generator.
    Yields: (train_df, valid_df)
    """

    df["date"] = df["ts"].dt.date
    unique_days = sorted(df["date"].unique())

    for start in range(0, len(unique_days) - fold_size, step_size):
        train_days = unique_days[:start + fold_size]
        valid_days = unique_days[start + fold_size:start + fold_size + step_size]

        train_df = df[df["date"].isin(train_days)]
        valid_df = df[df["date"].isin(valid_days)]

        yield train_df, valid_df
