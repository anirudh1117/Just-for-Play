import hashlib
from datetime import datetime
from jobs.utils import append_job_log
from market.models import Instrument
from mlapp.models.prediction_history import PredictionHistory


def snapshot_hash(df):
    """
    Creates a small hash from feature columns to track feature version.
    """
    text = "|".join(df.columns)
    return hashlib.md5(text.encode()).hexdigest()


def save_evening_shortlist(df, model_path, job_id=None):
    """
    Save evening top-30 signals into PredictionHistory table.
    """
    today = datetime.now().date()
    feature_hash = snapshot_hash(df)

    saved_count = 0

    for _, row in df.iterrows():
        try:
            inst = Instrument.objects.get(symbol=row["symbol"])

            PredictionHistory.objects.update_or_create(
                instrument=inst,
                date=today,
                defaults={
                    "prob_up": row["prob_up"],
                    "confidence": row["confidence"],
                    "entry": row["entry"],
                    "target": row["target"],
                    "stoploss": row["stoploss"],

                    "close": row["close"],
                    "vwap": row["vwap"],
                    "atr_14": row["atr_14"],
                    "volume": row["volume"],

                    "ts": row["ts"],

                    "feature_hash": feature_hash,
                    "model_version": model_path.split("/")[-1],
                }
            )

            saved_count += 1

        except Exception as e:
            append_job_log(job_id, f"Error saving {row['symbol']}: {e}")

    append_job_log(job_id, f"Saved {saved_count} prediction entries.")
    return saved_count
