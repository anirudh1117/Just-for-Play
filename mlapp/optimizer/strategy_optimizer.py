# mlapp/optimizer/strategy_optimizer.py

from jobs.utils import clean_json
from mlapp.optimizer.strategy_params import StrategyParams
from mlapp.backtest.backtest_engine import BacktestEngine
from mlapp.backtest.metrics import BacktestMetrics

from mlapp.models.strategy_optimization import StrategyOptimizationResult



class StrategyOptimizer:
    """
    Core engine for running multiple strategy variations (Option B).
    This skeleton defines the architecture. Real logic will be added in later steps.
    """

    def __init__(self, symbols, start_date, end_date):
        """
        symbols: list of stock symbols to test
        start_date, end_date: backtest period
        """
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date

        # All combinations (300+)
        self.combinations = StrategyParams.all_combinations()

    # ---------------------------------------------------------
    # SCORE FUNCTION (placeholder for Step 4)
    # ---------------------------------------------------------
    def compute_score(self, metrics):
        """
        metrics = {
            "sharpe_ratio": float,
            "max_drawdown": float,
            "per_symbol": [...],
            "daily_returns": {...},
            ...
        }

        This converts all metrics into a single numeric score.
        """

        # Extract needed fields
        sharpe = metrics.get("sharpe_ratio", 0)
        drawdown = metrics.get("max_drawdown", 0)
        daily_ret = metrics.get("daily_returns", {})

        if not daily_ret:
            return 0.0

        # Win rate calculation
        total_trades = sum([abs(v) > 0 for v in metrics["daily_returns"].values()])
        wins = sum([1 for v in metrics["daily_returns"].values() if v > 0])
        if total_trades == 0:
            win_rate = 0
        else:
            win_rate = wins / total_trades

        # Expectancy = avg return per trade
        expectancy = (
            sum(metrics["daily_returns"].values()) / total_trades
            if total_trades > 0 else 0
        )

        # Normalize metrics (avoid division by zero)
        norm_win = win_rate
        norm_sharpe = sharpe / 3 if sharpe < 3 else 1.0  # cap
        norm_exp = expectancy
        norm_dd = min(drawdown / 10, 1.0)  # normalize 0–10R range

        # Weighted score
        score = (
            0.30 * norm_win +
            0.40 * norm_sharpe +
            0.20 * norm_exp -
            0.10 * norm_dd
        )

        return score

    # ---------------------------------------------------------
    # RUN BACKTEST FOR ONE STRATEGY (Step 3)
    # ---------------------------------------------------------
    def evaluate_strategy(self, params):
        """
        Runs a full backtest for a single strategy config.
        params = {
            "entry_rule": ...,
            "sl_mult": ...,
            "tp_mult": ...,
            "confidence": ...,
            "hold_time": ...
        }
        """

        # 1. Run backtest with parameters
        engine = BacktestEngine(
            symbols=self.symbols,
            start_date=self.start_date,
            end_date=self.end_date,
            minutes=params["hold_time"],   # using holding time here
            strict=True,                   # fixed (still OK for now)
        )

        # Pass strategy parameters to backtest engine
        # We will extend BacktestEngine to accept `params` soon.
        backtest_result = engine.run(params=params)

        # 2. Compute metrics
        metrics = BacktestMetrics(backtest_result).summary()

        # 3. Prepare return object
        result = {
            "params": params,
            "metrics": metrics,
            "score": 0.0,  # Step 4 will compute this
        }

        return result

    # ---------------------------------------------------------
    # MAIN OPTIMIZATION LOOP (framework only)
    # ---------------------------------------------------------
    def run(self):
        """
        Run full optimization:
        - loop over all strategy combinations
        - evaluate each strategy
        - compute score
        - collect sorted results
        """

        results = []
        total_combos = len(self.combinations)

        print(f"Starting Strategy Optimization across {total_combos} combinations.")

        for idx, params in enumerate(self.combinations, start=1):

            print(f"Evaluating strategy {idx}/{total_combos}: {params}")

            try:
                # 1. Run backtest + metrics
                result = self.evaluate_strategy(params)

                # 2. Score the strategy
                result["score"] = self.compute_score(result["metrics"])

                results.append(result)

            except Exception as e:
                # Safety: even if one combo fails, optimizer must continue
                print(f"⚠️ Strategy failed for params {params}: {str(e)}")
                continue

        # ---------------------------------------------------------
        # Sort all strategies by score (descending)
        # ---------------------------------------------------------
        results.sort(key=lambda x: x["score"], reverse=True)
        best = results[0]

        # ---------------------------------------------------------
        # Persist best result
        # ---------------------------------------------------------
        StrategyOptimizationResult.objects.create(
            best_params=clean_json(best["params"]),
            best_metrics=clean_json(best["metrics"]),
            best_score=best["score"],
            all_results=clean_json(results),
        )

        print("Optimization completed and saved to database.")

        return results
