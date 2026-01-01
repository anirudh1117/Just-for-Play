import pandas as pd


class OutcomeMetricsEngine:
    """
    Computes performance metrics from TradeOutcome table.
    Read-only, deterministic.
    """

    def __init__(self, queryset):
        """
        queryset: Django queryset of TradeOutcome
        """
        self.df = pd.DataFrame(list(queryset.values(
            "date",
            "symbol",
            "R_multiple",
            "exit_reason",
            "holding_minutes",
            "created_at",
        )))

        if not self.df.empty:
            self.df["date"] = pd.to_datetime(self.df["date"])

    # --------------------------------------------------
    # Core metrics
    # --------------------------------------------------

    def trade_count(self):
        return len(self.df)

    def win_rate(self):
        if self.df.empty:
            return 0.0
        return round(
            (self.df["R_multiple"] > 0).mean() * 100, 2
        )

    def avg_win_R(self):
        wins = self.df[self.df["R_multiple"] > 0]["R_multiple"]
        return round(wins.mean(), 3) if not wins.empty else 0.0

    def avg_loss_R(self):
        losses = self.df[self.df["R_multiple"] < 0]["R_multiple"]
        return round(losses.mean(), 3) if not losses.empty else 0.0

    def expectancy(self):
        """
        EV = avg_R per trade
        """
        if self.df.empty:
            return 0.0
        return round(self.df["R_multiple"].mean(), 4)

    # --------------------------------------------------
    # Equity & drawdown
    # --------------------------------------------------

    def equity_curve(self):
        if self.df.empty:
            return []

        eq = self.df.sort_values("created_at")["R_multiple"].cumsum()
        return eq.tolist()

    def max_drawdown(self):
        if self.df.empty:
            return 0.0

        eq = self.df.sort_values("created_at")["R_multiple"].cumsum()
        peak = eq.cummax()
        drawdown = eq - peak
        return round(drawdown.min(), 3)

    # --------------------------------------------------
    # Rolling metrics
    # --------------------------------------------------

    def rolling_expectancy(self, window=20):
        if self.df.empty:
            return {}

        daily = (
            self.df.groupby("date")["R_multiple"]
            .mean()
            .rolling(window)
            .mean()
        )

        return daily.dropna().round(4).to_dict()

    # --------------------------------------------------
    # Final summary
    # --------------------------------------------------

    def summary(self):
        return {
            "trades": self.trade_count(),
            "win_rate_pct": self.win_rate(),
            "avg_win_R": self.avg_win_R(),
            "avg_loss_R": self.avg_loss_R(),
            "expectancy": self.expectancy(),
            "max_drawdown_R": self.max_drawdown(),
            "rolling_20d_ev": self.rolling_expectancy(),
        }
