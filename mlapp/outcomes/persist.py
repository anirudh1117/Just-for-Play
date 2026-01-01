from mlapp.models import TradeOutcome


def save_trade_outcome(result, model_version, prediction_time):
    """
    Persist TradeOutcomeResult (from OutcomeEngine).
    Append-only: create or ignore if already exists.
    """

    if result.exit_reason == "INVALID":
        return None

    obj, _ = TradeOutcome.objects.get_or_create(
        date=result.date,
        symbol=result.symbol,
        model_version=model_version,
        defaults={
            "prediction_time": prediction_time,

            "entry_time": result.entry_time,
            "entry_price": result.entry_price,

            "exit_time": result.exit_time,
            "exit_price": result.exit_price,
            "exit_reason": result.exit_reason,

            "holding_minutes": result.holding_minutes,

            "tp_price": (
                result.entry_price * (1 + 0.006)
                if result.entry_price else None
            ),
            "sl_price": (
                result.entry_price * (1 - 0.004)
                if result.entry_price else None
            ),

            "R_multiple": result.R_multiple,
            "pnl_pct": (
                (result.exit_price - result.entry_price)
                / result.entry_price * 100
                if result.entry_price and result.exit_price else 0.0
            ),
        }
    )

    return obj
