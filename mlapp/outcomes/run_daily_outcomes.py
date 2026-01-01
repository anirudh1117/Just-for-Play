from django.utils import timezone

from jobs.utils import append_job_log
from mlapp.inference.model_loader import load_latest_model
from mlapp.outcomes.outcome_engine import OutcomeEngine
from mlapp.outcomes.persist import save_trade_outcome

from market.models import Candle
from mlapp.models import MorningInferenceRun


def run(job_id=None):
    """
    Nightly job: evaluate all morning predictions and persist outcomes.
    """

    today = timezone.now().date()
    append_job_log(job_id, f"Starting outcome evaluation for {today}")

    # Load latest model (for version only)
    _, model_version = load_latest_model()

    engine = OutcomeEngine()

    # Load today’s inference runs
    runs = MorningInferenceRun.objects.filter(date=today)
    if not runs.exists():
        append_job_log(job_id, "No morning inference runs found.")
        return "No predictions to evaluate."

    for run_obj in runs:
        prediction_time = run_obj.created_at

        for symbol in run_obj.symbol_list:  # assuming you store symbols
            qs = Candle.objects.filter(
                symbol=symbol,
                interval="5m",
                ts__date=today
            ).order_by("ts")

            candles = list(qs.values(
                "ts", "open", "high", "low", "close"
            ))

            if not candles:
                append_job_log(job_id, f"No candles for {symbol}")
                continue

            result = engine.evaluate(
                symbol=symbol,
                date=str(today),
                inference_end_time=prediction_time,
                candles_5m=candles,
            )

            save_trade_outcome(
                result=result,
                model_version=model_version,
                prediction_time=prediction_time,
            )

    append_job_log(job_id, "Outcome evaluation completed.")
    return "Trade outcomes saved."
