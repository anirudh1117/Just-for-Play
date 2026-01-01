import pandas as pd
import numpy as np


class BacktestMetrics:
    """
    Computes advanced metrics:
    equity curve, sharpe, drawdown, per-symbol stats.
    """

    def __init__(self, backtest_results):
        """
        backtest_results = {
            "details": [
                {"date": "YYYY-MM-DD", "results": [{symbol, result}, ...]},
                ...
            ]
        }
        """
        self.data = backtest_results.get("details", [])
        self.df = self._to_df()


    # ----------------------------------------------------
    # Convert input JSON → DataFrame
    # ----------------------------------------------------
    def _to_df(self):
        """
        Convert input JSON → DataFrame safely.
        Handles empty backtests (no trades).
        """
        if not self.data:
            # Return empty DF with required columns
            return pd.DataFrame(columns=["date", "symbol", "result"])
    
        rows = []
    
        for day in self.data:
            date = day["date"]
            for r in day["results"]:
                rows.append({
                    "date": date,
                    "symbol": r["symbol"],
                    "result": r["result"]
                })
    
        df = pd.DataFrame(rows)
    
        if df.empty:
            return pd.DataFrame(columns=["date", "symbol", "result"])
    
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        return df


    # ----------------------------------------------------
    # Daily PnL (sum of +1, -1, 0 per day)
    # ----------------------------------------------------
    def daily_returns(self):
        return self.df.groupby("date")["result"].sum()

    # ----------------------------------------------------
    # Equity curve
    # ----------------------------------------------------
    def equity_curve(self):
        dr = self.daily_returns()
        return dr.cumsum()

    # ----------------------------------------------------
    # Sharpe ratio
    # ----------------------------------------------------
    def sharpe_ratio(self):
        dr = self.daily_returns()
        if dr.std() == 0:
            return 0
        return dr.mean() / dr.std()

    # ----------------------------------------------------
    # Max Drawdown
    # ----------------------------------------------------
    def max_drawdown(self):
        eq = self.equity_curve()
        roll_max = eq.cummax()
        dd = roll_max - eq
        return dd.max()

    # ----------------------------------------------------
    # Per symbol performance
    # ----------------------------------------------------
    def per_symbol_stats(self):
        return (
            self.df.groupby("symbol")["result"]
            .agg(["count", "sum", "mean"])
            .rename(columns={"sum": "net", "mean": "avg"})
        )

    # ----------------------------------------------------
    # Package all metrics in one dictionary
    # ----------------------------------------------------
    def summary(self):
        return {
            "total_days": len(self.daily_returns()),
            "total_trades": len(self.df),
            "daily_returns": self.daily_returns().to_dict(),
            "equity_curve": self.equity_curve().to_dict(),
            "sharpe_ratio": round(self.sharpe_ratio(), 4),
            "max_drawdown": float(self.max_drawdown()),
            "per_symbol": self.per_symbol_stats().reset_index().to_dict(orient="records"),
        }
