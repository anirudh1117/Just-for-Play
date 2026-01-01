from mlapp.backtest.metrics import BacktestMetrics


def test_metrics():
    summary = {
        "details": [
            {"date": "2023-01-01", "results": []}
        ],
        "total_trades": 10,
        "wins": 5,
        "losses": 3,
        "zeroes": 2,
        "win_rate": 50,
    }

    metrics = BacktestMetrics(summary).summary()
    assert "sharpe_ratio" in metrics
