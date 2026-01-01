import matplotlib.pyplot as plt
import os


def save_equity_curve(equity_dict, run_id):
    """
    Saves equity curve plot to static folder.
    """
    dates = list(equity_dict.keys())
    values = list(equity_dict.values())

    plt.figure(figsize=(10, 5))
    plt.plot(dates, values)
    plt.title("Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("PnL Units")

    path = f"mlapp/static/backtest_equity/equity_{run_id}.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)

    plt.savefig(path, dpi=150)
    plt.close()
