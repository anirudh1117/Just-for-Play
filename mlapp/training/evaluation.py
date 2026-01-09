import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def evaluate_trading_performance(
    df,
    probs,
    thresholds,
    reward_pct=0.015,
    risk_pct=0.005,
):
    """
    df must contain:
      - label (0/1)
    probs:
      - model predicted probabilities
    """

    results = []

    if "target_up_5m" not in df.columns:
        raise Exception(
            "Expected column 'target_up_5m' not found in dataframe."
        )

    for th in thresholds:
        mask = probs >= th
        trades = df[mask]

        if len(trades) == 0:
            continue

        win_rate = trades["target_up_5m"].mean()
        loss_rate = 1 - win_rate

        ev = (win_rate * reward_pct) - (loss_rate * risk_pct)

        results.append({
            "threshold": th,
            "trades": len(trades),
            "win_rate": round(win_rate, 4),
            "expected_value": round(ev, 5),
        })

    return pd.DataFrame(results)
