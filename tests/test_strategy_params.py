from mlapp.optimizer.strategy_params import StrategyParams


def test_strategy_combinations_count():
    combos = StrategyParams.all_combinations()
    assert len(combos) == 324
