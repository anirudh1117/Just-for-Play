from datetime import datetime
from jobs.utils import append_job_log
from market.models import Instrument
from mlapp.models.final_pick_history import FinalPickHistory


def save_final_picks(df, model_path, job_id=None):
    today = datetime.now().date()
    saved = 0

    for _, row in df.iterrows():
        inst = Instrument.objects.get(symbol=row["symbol"])

        FinalPickHistory.objects.create(
            instrument=inst,
            date=today,

            prob_up_live=row["prob_up_live"],
            confidence=row["confidence"],
            entry=row["entry"],
            target=row["target"],
            stoploss=row["stoploss"],

            close=row["close"],
            vwap=row["vwap"],
            atr_14=row["atr_14"],
            volume=row["volume"],

            ts=row["ts"],
            model_version=model_path.split("/")[-1],
        )

        saved += 1

    append_job_log(job_id, f"Saved final morning picks: {saved}")
    return saved
