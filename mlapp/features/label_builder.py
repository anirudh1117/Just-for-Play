import pandas as pd


def build_labels(
    df: pd.DataFrame,
    sl_pct: float = 0.005,
    tp_pct: float = 0.01,
    max_hold: int = 12,
) -> pd.DataFrame:
    """
    Adds:
      - label_raw: {-1, 0, 1}
      - label: {0, 1}
    """
    df = df.sort_values(["symbol", "ts"]).copy()
    df["label_raw"] = 0

    grouped = df.groupby("symbol")

    for symbol, g in grouped:
        g = g.reset_index()

        for i in range(len(g) - max_hold - 1):
            entry_price = g.loc[i + 1, "open"]

            sl = entry_price * (1 - sl_pct)
            tp = entry_price * (1 + tp_pct)

            outcome = 0

            for j in range(i + 1, i + 1 + max_hold):
                high = g.loc[j, "high"]
                low = g.loc[j, "low"]

                if high >= tp:
                    outcome = 1
                    break
                if low <= sl:
                    outcome = -1
                    break

            g.loc[i, "label_raw"] = outcome

        df.loc[g["index"], "label_raw"] = g["label_raw"].values

    # Binary label for ML
    df["label"] = (df["label_raw"] == 1).astype(int)

    return df
