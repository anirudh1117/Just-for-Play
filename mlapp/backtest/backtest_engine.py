from datetime import datetime
import pickle
import os
import pandas as pd

from mlapp.backtest.trade_simulator import TradeSimulator
from mlapp.backtest.data_loader import BacktestDataLoader
from mlapp.models.backtest_history import BacktestHistory
from mlapp.backtest.metrics import BacktestMetrics
from mlapp.backtest.result_writer import save_equity_curve

from django.conf import settings

from mlapp.testing.dummy_model import DummyModel
from mlapp.testing.fake_data_loader import FakeBacktestDataLoader


class BacktestEngine:
    """
    Runs a full multi-day, multi-stock backtest.
    Now supports Strategy Optimization parameters.
    """

    def __init__(self, symbols, start_date, end_date, minutes=20, strict=True):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.minutes = minutes
        self.strict = strict

        # Trade simulator will later be updated to accept params
        self.simulator = TradeSimulator(minutes=minutes, strict_mode=strict)

        # Params injected from optimizer
        self.strategy_params = {}

    # ------------------------------------------------------
    # Load latest LGBM model
    # ------------------------------------------------------
    def load_model(self, model_dir="mlapp/models_store"):
        files = [f for f in os.listdir(model_dir) if f.endswith(".pkl")]
        if not files:
            raise Exception("No trained model found")

        files.sort()
        latest = files[-1]
        path = os.path.join(model_dir, latest)

        with open(path, "rb") as f:
            model = pickle.load(f)

        return model, latest

    # ------------------------------------------------------
    # Load data for backtest window
    # ------------------------------------------------------
    def load_all_data(self):
        """
        Returns:
        {
            '2023-10-05': {'TATASTEEL': df, 'HDFCBANK': df, ...},
            '2023-10-06': {...}
        }
        """
        merged = {}

        for sym in self.symbols:
            if settings.TEST_MODE:
                # use synthetic data, does NOT affect real NSE data
                loader = FakeBacktestDataLoader(sym, self.start_date, self.end_date)
                daywise = loader.run()
            else:
                # use REAL historical data from DB or API
                loader = BacktestDataLoader(sym, self.start_date, self.end_date)
                daywise = loader.run()

            for day, df in daywise.items():
                if day not in merged:
                    merged[day] = {}
                merged[day][sym] = df

        return merged

    # ------------------------------------------------------
    # RUN BACKTEST WITH STRATEGY PARAMETERS
    # ------------------------------------------------------
    def run(self, params=None):
        """
        params is optional, used by strategy optimizer:

        params = {
            "entry_rule": "breakout_20",
            "sl_mult": 1.5,
            "tp_mult": 2.0,
            "confidence": 0.60,
            "hold_time": 30,
        }
        """
        # inject strategy params
        self.strategy_params = params or {}

        # Load model & data
        if settings.TEST_MODE:
            model = DummyModel(score=0.8)
        else:
            model, model_version = self.load_model()

        day_data = self.load_all_data()

        results = []
        wins = losses = zeroes = 0

        # --------------------------
        # Extract strategy params
        # --------------------------
        entry_rule = self.strategy_params.get("entry_rule", "breakout_20")
        sl_mult = self.strategy_params.get("sl_mult", 1.5)
        tp_mult = self.strategy_params.get("tp_mult", 2.0)
        confidence_threshold = self.strategy_params.get("confidence", 0.60)
        holding_time = self.strategy_params.get("hold_time", self.minutes)

        # Pass strategy configuration to simulator
        self.simulator.set_strategy_params(
            entry_rule=entry_rule,
            sl_mult=sl_mult,
            tp_mult=tp_mult,
            confidence_threshold=confidence_threshold,
            holding_time=holding_time,
        )

        # ---------------------------------------------------
        # Backtest day-by-day
        # ---------------------------------------------------
        for day, symbol_dict in sorted(day_data.items()):
            # Highly incomplete day
            if len(symbol_dict) < 3:
                continue

            df_res = self.simulator.run_day(symbol_dict, model)

            if df_res is None or df_res.empty:
                continue

            # collect result for this day
            results.append({
                "date": day,
                "results": df_res.to_dict(orient="records")
            })

            # aggregate statistics
            for _, row in df_res.iterrows():
                if row["result"] == 1:
                    wins += 1
                elif row["result"] == -1:
                    losses += 1
                else:
                    zeroes += 1

        # -------------------------
        # Summary for Metrics Engine
        # -------------------------
        total = wins + losses + zeroes
        win_rate = (wins / total * 100) if total > 0 else 0

        summary = {
            "symbols": self.symbols,
            "start": self.start_date,
            "end": self.end_date,
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "zeroes": zeroes,
            "win_rate": win_rate,
            "details": results,
            "strategy_params": self.strategy_params,
        }

        # -------------------------
        # Save backtest history
        # -------------------------
        if not settings.TEST_MODE:
            history = BacktestHistory.objects.create(
                symbols=self.symbols,
                start_date=self.start_date,
                end_date=self.end_date,
                win_rate=win_rate,
                total_trades=total,
                wins=wins,
                losses=losses,
                zeroes=zeroes,
                result_json=results,
                strategy_params=self.strategy_params,
            )
        else:
            history = None

        # -------------------------
        # Compute metrics
        # -------------------------
        metrics = BacktestMetrics(summary).summary()
        summary["metrics"] = metrics

        # Save equity curve
        eq = summary["metrics"]["equity_curve"]

        if history is not None:
            save_equity_curve(eq, run_id=history.id)

            # Attach backtest id in summary
            summary["backtest_id"] = history.id

        return summary
