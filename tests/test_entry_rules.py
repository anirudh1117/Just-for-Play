from mlapp.backtest.trade_simulator import TradeSimulator
import pandas as pd
from datetime import datetime


def generate_df():
    ts = datetime(2023,1,1,9,15)
    rows=[]
    price=100
    for _ in range(30):
        rows.append({
            "timestamp": ts,
            "open": price,
            "high": price + 1,
            "low": price - 1,
            "close": price + 0.5,
            "volume": 10000
        })
        ts += pd.Timedelta(minutes=5)
        price += 0.5
    return pd.DataFrame(rows)


def test_entry_rules():
    df = generate_df()
    sim = TradeSimulator()

    sim.entry_rule = "breakout_20"
    assert sim.get_entry_price(df) is not None

    sim.entry_rule = "ema20_cross"
    assert sim.get_entry_price(df) is not None

    sim.entry_rule = "vwap_break"
    assert sim.get_entry_price(df) is not None
