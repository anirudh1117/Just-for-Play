# mlapp/features/compute_features.py

import os
import gc
from datetime import timedelta

import pandas as pd
from django.utils import timezone

from market.models import Candle, Instrument
from market.constants import INTERVAL_5MIN
from jobs.utils import append_job_log
from mlapp.features.feature_engine import FeatureEngine



FEATURE_DIR = "mlapp/cache/features"
LOOKBACK_DAYS = 90


def run(job_id=None):
    """
    Compute ML features instrument-by-instrument (5-minute only)
    and persist as Parquet files.

    This is memory-safe and resumable.
    """

    append_job_log(job_id, "Starting feature computation (5m, per-instrument)")

    os.makedirs(FEATURE_DIR, exist_ok=True)

    end_ts = timezone.now()
    start_ts = end_ts - timedelta(days=LOOKBACK_DAYS)

    instruments = Instrument.objects.filter(
        candle__interval=INTERVAL_5MIN
    ).distinct()

    append_job_log(
        job_id,
        f"Found {instruments.count()} instruments with 5m candles"
    )

    processed = 0
    skipped = 0

    for inst in instruments:
        try:
            qs = Candle.objects.filter(
                instrument=inst,
                interval=INTERVAL_5MIN,
                ts__gte=start_ts,
                ts__lte=end_ts,
            ).order_by("ts")

            if not qs.exists():
                skipped += 1
                continue

            # -----------------------------
            # Load candles into DataFrame
            # -----------------------------
            df = pd.DataFrame.from_records(
                qs.values(
                    "ts",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                )
            )

            if df.empty or len(df) < 50:
                skipped += 1
                continue

            df["symbol"] = inst.symbol

            # -----------------------------
            # Feature computation
            # -----------------------------
            engine = FeatureEngine(job_id=job_id)
            df = engine.run_on_df(df)


            if df.empty:
                skipped += 1
                continue

            # -----------------------------
            # Persist (per instrument)
            # -----------------------------
            out_path = os.path.join(
                FEATURE_DIR,
                f"{inst.symbol}_5m.parquet"
            )

            if "target_up_5m" not in df.columns:
                raise Exception("Label generation failed: target_up_5m missing")

            df.to_parquet(out_path, index=False)

            processed += 1

        except Exception as e:
            append_job_log(
                job_id,
                f"[{inst.symbol}] feature computation failed: {e}"
            )
            continue

        finally:
            # -----------------------------
            # Hard memory cleanup
            # -----------------------------
            del df
            gc.collect()

    append_job_log(
        job_id,
        f"Feature computation done. "
        f"Processed={processed}, Skipped={skipped}"
    )

    return f"Features written: {processed} instruments"
