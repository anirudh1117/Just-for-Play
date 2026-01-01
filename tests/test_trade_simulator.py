import pytest
import pandas as pd
from datetime import datetime, timedelta

from mlapp.backtest.trade_simulator import TradeSimulator
from mlapp.testing.dummy_model import DummyModel


def generate_dummy_df():
    ts = datetime(2023, 1, 1, 9, 15)
    rows = []

    price = 100
    for _ in range(78):
        rows.append({
            "timestamp": ts,
            "open": price,
            "high": price + 1,
            "low": price - 1,
            "close": price + 0.4,
            "volume": 10000
        })
        ts += timedelta(minutes=5)
        price += 0.4

    return pd.DataFrame(rows)


def test_trade_simulator_basic():
    sim = TradeSimulator()
    sim.set_strategy_params(
        entry_rule="breakout_20",
        sl_mult=1.5,
        tp_mult=2.0,
        confidence_threshold=0.5,
        holding_time=30
    )

    df = generate_dummy_df()
    model = DummyModel(score=0.8)

    result = sim.run_day({"TEST": df}, model)

    assert result is not None
    assert not result.empty
    assert "entry_price" in result.columns
