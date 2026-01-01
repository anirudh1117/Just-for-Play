import pandas as pd
import os
import json


class BacktestExporter:

    def __init__(self, summary, run_id):
        self.summary = summary
        self.run_id = run_id
        self.base_dir = f"mlapp/static/backtest_exports/{run_id}"
        os.makedirs(self.base_dir, exist_ok=True)

    # ----------------------------------------------------
    # Export daily results (expanded trades)
    # ----------------------------------------------------
    def export_daily_trades(self):
        rows = []
        for day in self.summary["details"]:
            date = day["date"]
            for r in day["results"]:
                rows.append({
                    "date": date,
                    "symbol": r["symbol"],
                    "entry": r["entry"],
                    "target": r["target"],
                    "stoploss": r["stoploss"],
                    "result": r["result"],
                })

        df = pd.DataFrame(rows)
        df.to_csv(f"{self.base_dir}/daily_trades.csv", index=False)
        return f"/static/backtest_exports/{self.run_id}/daily_trades.csv"

    # ----------------------------------------------------
    # Export per-symbol stats
    # ----------------------------------------------------
    def export_symbol_stats(self):
        df = pd.DataFrame(self.summary["metrics"]["per_symbol"])
        df.to_csv(f"{self.base_dir}/per_symbol_stats.csv", index=False)
        return f"/static/backtest_exports/{self.run_id}/per_symbol_stats.csv"

    # ----------------------------------------------------
    # Export equity curve
    # ----------------------------------------------------
    def export_equity_curve(self):
        eq = self.summary["metrics"]["equity_curve"]
        df = pd.DataFrame(list(eq.items()), columns=["date", "equity"])
        df.to_csv(f"{self.base_dir}/equity_curve.csv", index=False)
        return f"/static/backtest_exports/{self.run_id}/equity_curve.csv"

    # ----------------------------------------------------
    # Export daily returns
    # ----------------------------------------------------
    def export_daily_returns(self):
        dr = self.summary["metrics"]["daily_returns"]
        df = pd.DataFrame(list(dr.items()), columns=["date", "return"])
        df.to_csv(f"{self.base_dir}/daily_returns.csv", index=False)
        return f"/static/backtest_exports/{self.run_id}/daily_returns.csv"

    # ----------------------------------------------------
    # Export full summary as JSON
    # ----------------------------------------------------
    def export_summary_json(self):
        path = f"{self.base_dir}/summary.json"
        with open(path, "w") as f:
            json.dump(self.summary, f, indent=4)
        return f"/static/backtest_exports/{self.run_id}/summary.json"
