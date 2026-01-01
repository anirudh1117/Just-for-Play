import pandas as pd
from datetime import datetime, timedelta, time

from jobs.utils import append_job_log
from market.models import Candle, Instrument
from mlapp.features.pipeline import build_feature_dataset
from mlapp.inference.candle_aggregator import aggregate_1m_to_5m
from mlapp.inference.model_loader import load_latest_model

from django.utils import timezone
from django.db import transaction

from market.models import Holiday
from mlapp.models import MorningInferenceRun
from models.morning_prediction import MorningPrediction



PROB_THRESHOLD = 0.65
MAX_TRADES = 5

MARKET_OPEN_TIME = time(9, 15)
INFERENCE_MINUTES = 20
LATEST_ALLOWED_TIME = time(10, 30)


def get_market_open_dt(today):
    return datetime.combine(today, MARKET_OPEN_TIME).replace(tzinfo=timezone.get_current_timezone())


def get_inference_window(today):
    start = get_market_open_dt(today)
    end = start + timedelta(minutes=INFERENCE_MINUTES)
    return start, end

def validate_inference_window(job_id):
    now = timezone.now()
    today = now.date()

    # Weekend
    if today.weekday() >= 5:
        raise Exception("Market closed (Weekend)")

    # Holiday
    if Holiday.objects.filter(date=today).exists():
        raise Exception("Market closed (Holiday)")

    market_open, window_end = get_inference_window(today)

    # Too early
    if now < window_end:
        raise Exception("Inference not allowed yet — insufficient data")

    # Too late
    latest_allowed = datetime.combine(today, LATEST_ALLOWED_TIME).replace(
        tzinfo=timezone.get_current_timezone()
    )
    if now > latest_allowed:
        raise Exception("Inference too late — window expired")

    # One run per day
    if MorningInferenceRun.objects.filter(date=today).exists():
        raise Exception("Inference already executed today")

    return market_open, window_end


def validate_candles(df_1m, expected_minutes=20):
    if df_1m.empty:
        raise Exception("No candle data found")

    counts = df_1m.groupby("symbol").size()
    valid_symbols = counts[counts >= expected_minutes - 2]

    if len(valid_symbols) < 5:
        raise Exception("Insufficient candle coverage across symbols")

    return df_1m[df_1m["symbol"].isin(valid_symbols.index)]



def run(job_id=None):
    try:
        market_open, window_end = validate_inference_window(job_id)
    except Exception as e:
        append_job_log(job_id, f"Inference blocked: {str(e)}")
        return []

    append_job_log(
        job_id,
        f"Inference window locked: {market_open.time()} → {window_end.time()}"
    )

    # --------------------------------------------------
    # 1) Load universe
    # --------------------------------------------------
    instruments = Instrument.objects.filter(
        exchange="NSE",
        instrument_type="EQ"
    )

    symbols = [i.symbol for i in instruments]

    # --------------------------------------------------
    # 2) Load last ~20 minutes of 1m candles
    # --------------------------------------------------

    qs = Candle.objects.filter(
        symbol__in=symbols,
        interval="1m",
        ts__gte=market_open,
        ts__lt=window_end
    ).values(
        "symbol", "ts", "open", "high", "low", "close", "volume"
    )

    df_1m = pd.DataFrame(list(qs))
    df_1m = validate_candles(df_1m)

    if df_1m.empty:
        append_job_log(job_id, "No 1-minute candles found. Aborting.")
        return []

    append_job_log(job_id, f"Loaded {len(df_1m)} 1m candles")

    # --------------------------------------------------
    # 3) Aggregate to 5m
    # --------------------------------------------------
    df_5m = aggregate_1m_to_5m(df_1m)
    append_job_log(job_id, f"Aggregated to {len(df_5m)} 5m candles")

    # --------------------------------------------------
    # 4) Build features (NO labels)
    # --------------------------------------------------
    df_feat = build_feature_dataset(
        df_5m,
        sl_pct=None,
        tp_pct=None,
        max_hold=None
    )

    # Remove label columns if present
    df_feat = df_feat.drop(
        columns=[c for c in df_feat.columns if c.startswith("label")],
        errors="ignore"
    )

    # --------------------------------------------------
    # 5) Load model
    # --------------------------------------------------
    model, model_version = load_latest_model()
    append_job_log(job_id, f"Loaded model: {model_version}")

    # --------------------------------------------------
    # 6) Predict probabilities
    # --------------------------------------------------
    feature_cols = [
        c for c in df_feat.columns
        if c not in ("symbol", "ts")
    ]

    df_feat["prob"] = model.predict(df_feat[feature_cols])

    # --------------------------------------------------
    # 7) Filter & rank
    # --------------------------------------------------
    picks = (
        df_feat[df_feat["prob"] >= PROB_THRESHOLD]
        .sort_values("prob", ascending=False)
        .head(MAX_TRADES)
    )

    result = []

    with transaction.atomic():
        MorningInferenceRun.objects.create(
            date=timezone.now().date(),
            model_version=model_version,
            symbols=len(result),
        )

        for rank, row in enumerate(picks.itertuples(), start=1):
            MorningPrediction.objects.create(
                date=timezone.now().date(),
                symbol=row.symbol,
                probability=row.prob,
                rank=rank,
                model_version=model_version,
            )

            result.append({
                "symbol": row.symbol,
                "probability": row.prob,
                "rank": rank,
            })


    append_job_log(job_id, f"Selected {len(result)} trade candidates")

    return result
