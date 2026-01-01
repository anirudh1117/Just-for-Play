import pytest
from mlapp.optimizer.strategy_optimizer import StrategyOptimizer
from django.conf import settings


@pytest.mark.django_db
def test_optimizer_runs():
    settings.TEST_MODE = True

    opt = StrategyOptimizer(
        symbols=["TATAMOTORS"],
        start_date="2023-01-01",
        end_date="2023-01-10"
    )

    results = opt.run()

    assert len(results) == 324
    assert "score" in results[0]
    assert "params" in results[0]
