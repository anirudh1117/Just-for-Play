import pandas as pd

from mlapp.features.base_features import build_base_features
from mlapp.features.trend_features import build_trend_features
from mlapp.features.momentum_features import build_momentum_features
from mlapp.features.volatility_features import build_volatility_features
from mlapp.features.relative_features import add_relative_features
from mlapp.features.label_builder import build_labels


def build_feature_dataset(
    df_candles: pd.DataFrame,
    sl_pct=0.005,
    tp_pct=0.01,
    max_hold=12,
):
    """
    Input:
        df_candles: raw 5-min candle dataframe
    Output:
        ML-ready dataframe with features + labels
    """

    df = df_candles.copy()

    # ---- FEATURE PIPELINE ----
    df = build_base_features(df)
    df = build_trend_features(df)
    df = build_momentum_features(df)
    df = build_volatility_features(df)
    df = add_relative_features(df)

    # ---- LABELS ----
    df = build_labels(
        df,
        sl_pct=sl_pct,
        tp_pct=tp_pct,
        max_hold=max_hold,
    )

    # ---- CLEANUP ----
    feature_cols = [
        c for c in df.columns
        if c not in ("symbol", "ts", "label_raw")
    ]

    df = df.dropna(subset=feature_cols)
    df = df.reset_index(drop=True)

    return df
