def add_time_features(df):
    df["minute_of_day"] = df["ts"].dt.hour * 60 + df["ts"].dt.minute
    return df
