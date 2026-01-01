# mlapp/optimizer/strategy_params.py

from itertools import product


class StrategyParams:
    """
    Defines the parameter search space for the strategy optimizer.
    Option B: Entry Rule, SL Multiplier, TP Multiplier,
              Confidence Threshold, Holding Time.
    """

    # -------------------------
    # Parameter Grid
    # -------------------------

    ENTRY_RULES = [
        "breakout_20",
        "breakout_15",
        "ema20_cross",
        "vwap_break",
    ]

    STOPLOSS_MULT = [
        1.0,
        1.5,
        2.0,
    ]

    TARGET_MULT = [
        1.0,
        1.5,
        2.0,
    ]

    CONF_THRESH = [
        0.55,
        0.60,
        0.65,
    ]

    HOLDING_TIME = [
        15,
        30,
        45,
    ]

    # -------------------------
    # Generate all combinations
    # -------------------------

    @classmethod
    def all_combinations(cls):
        """
        Returns a list of dicts like:
        {
            "entry_rule": "breakout_20",
            "sl_mult": 1.5,
            "tp_mult": 2.0,
            "confidence": 0.60,
            "hold_time": 30
        }
        """
        combos = []

        for entry, sl, tp, conf, hold in product(
            cls.ENTRY_RULES,
            cls.STOPLOSS_MULT,
            cls.TARGET_MULT,
            cls.CONF_THRESH,
            cls.HOLDING_TIME,
        ):
            combos.append({
                "entry_rule": entry,
                "sl_mult": sl,
                "tp_mult": tp,
                "confidence": conf,
                "hold_time": hold,
            })

        return combos

    # -------------------------
    # Count total combinations
    # -------------------------

    @classmethod
    def combination_count(cls):
        return (
            len(cls.ENTRY_RULES)
            * len(cls.STOPLOSS_MULT)
            * len(cls.TARGET_MULT)
            * len(cls.CONF_THRESH)
            * len(cls.HOLDING_TIME)
        )
