import numpy as np


def filter_symbols(df):
    """
    Filter out low-quality symbols before choosing candidates.
    """
    df = df[df["volume"] > 0]
    df = df[df["atr_norm"] < 0.05]     # avoid extremely volatile
    df = df[df["close"] > 20]          # avoid penny stocks
    return df


# -------------------------------
# Evening shortlist = 30 symbols
# -------------------------------
EVENING_SHORTLIST_COUNT = 30


def compute_entry(df):
    df["entry"] = df["vwap"]
    return df


def compute_stoploss(df):
    df["stoploss"] = df["entry"] - df["atr_14"] * 1.2
    df["stoploss"] = df["stoploss"].round(2)
    return df


def compute_target(df):
    df["target"] = df["entry"] + df["atr_14"] * 2
    df["target"] = df["target"].round(2)
    return df


def assign_confidence(df):
    df["confidence"] = (df["prob_up"] * 100).round(2)
    return df


def final_signal_processing(df, top_n=EVENING_SHORTLIST_COUNT):
    """
    Evening Signal Logic:
    - Filter low-quality symbols
    - Sort by ML probability
    - Select top 30 candidates
    """

    df = filter_symbols(df)
    if df.empty:
        return df

    # ---------------
    # TOP 30 SHORTLIST
    # ---------------
    df = df.sort_values("prob_up", ascending=False).head(top_n).copy()

    df = compute_entry(df)
    df = compute_stoploss(df)
    df = compute_target(df)
    df = assign_confidence(df)

    return df[
        [
            "symbol",
            "prob_up",
            "confidence",
            "entry",
            "target",
            "stoploss",
            "close",
            "vwap",
            "atr_14",
            "volume",
            "ts",
        ]
    ]
