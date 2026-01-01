import pytest
from mlapp.backtest.backtest_engine import BacktestEngine
from django.conf import settings


@pytest.mark.django_db
def test_backtest_engine_runs():
    settings.TEST_MODE = True

    engine = BacktestEngine(
        symbols=["TATAMOTORS"],
        start_date="2023-01-01",
        end_date="2023-01-05"
    )

    summary = engine.run()

    assert "total_trades" in summary
    assert summary["total_trades"] >= 0
    assert "metrics" in summary
