from datetime import date, datetime, time, timedelta
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

import random

from market.models import Instrument, Candle, HistoricalBackfillState
from market.api.upstox_client import UpstoxClient
from market.constants import (
    INTERVAL_1MIN,
    INTERVAL_5MIN,
    MAX_BACKFILL_RETRIES,
    RETRY_COOLDOWN_MINUTES,
)
from market.services.backfill_utils import date_range, is_temporarily_blocked
from jobs.utils import append_job_log
from market.services.bhavcopy_universe import get_bhavcopy_filtered_universe
from market.services.universe_selector import get_phase1_universe


# -----------------------------------------------------------------------------
# IMPORTANT BACKFILL CONTRACT (FROZEN)
# -----------------------------------------------------------------------------
# 1. Uses Upstox v3 historical-candle API (path-based)
# 2. One trading day fetched per API call (from_date == to_date)
# 3. Auth is FAIL-FAST (401 stops symbol processing)
# 4. Candles are written idempotently (instrument, ts, interval)
# 5. Timestamps from Upstox are stored AS-IS (timezone-aware ISO strings)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Backfill one instrument + one interval
# -----------------------------------------------------------------------------
def backfill_instrument(
    inst,
    interval,
    start_date,
    end_date,
    job_id=None,
    dry_run=False,
):
    client = UpstoxClient(log_job_id=job_id)

    state, _ = HistoricalBackfillState.objects.get_or_create(
        instrument=inst,
        interval=interval,
    )

    # Skip if temporarily blocked
    if is_temporarily_blocked(state):
        append_job_log(job_id, f"[{inst.symbol}] skipped (cooldown active)")
        return

    for day in date_range(start_date, end_date):
        append_job_log(job_id, f"[{inst.symbol}] {interval} → {day}")

        try:
            # ---------------------------------------------------------
            # DRY RUN (synthetic candles)
            # ---------------------------------------------------------
            if dry_run:
                candles = generate_fake_candles(day, interval)

            # ---------------------------------------------------------
            # REAL API CALL (Upstox v3)
            # ---------------------------------------------------------
            else:
                resp = client.fetch_historical_candles(
                    instrument_key=inst.instrument_key,
                    interval=interval,
                    from_date=day,
                    to_date=day,
                )

                append_job_log(job_id, f"[{inst.symbol}] API response: {resp}")
                data = resp.get("data", {})
                candles = data.get("candles", [])
                append_job_log(job_id, f"[{inst.symbol}] {interval} → {day} fetched {len(candles)} candles")

            # ---------------------------------------------------------
            # No data (holiday / zero-trade day)
            # ---------------------------------------------------------
            if not candles:
                append_job_log(
                    job_id,
                    f"[{inst.symbol}] no data on {day} (holiday or no trades)",
                )
                state.last_fetched_date = day
                state.save(update_fields=["last_fetched_date"])
                continue

            # ---------------------------------------------------------
            # Persist candles (atomic per day)
            # ---------------------------------------------------------
            if not dry_run:
                with transaction.atomic():
                    for c in candles:
                        raw_ts = parse_datetime(c[0])
                        if raw_ts is None:
                            raise ValueError(f"Invalid timestamp: {c[0]}")
                    
                        ts_utc = raw_ts.astimezone(utc) if raw_ts.tzinfo else raw_ts.replace(tzinfo=utc)
                    
                        Candle.objects.update_or_create(
                            instrument=inst,
                            ts=ts_utc,
                            interval=interval,
                            defaults={
                                "open": c[1],
                                "high": c[2],
                                "low": c[3],
                                "close": c[4],
                                "volume": c[5],
                            },
                        )


            # ---------------------------------------------------------
            # Update progress (SUCCESS PATH)
            # ---------------------------------------------------------
            state.completed_days += 1
            state.last_progress_at = timezone.now()
            state.last_fetched_date = day
            state.retry_count = 0
            state.last_error = None
            state.failed_until = None
            state.save()

            percent = int((state.completed_days / state.total_days) * 100)
            append_job_log(
                job_id,
                f"[{inst.symbol}] progress {percent}% "
                f"({state.completed_days}/{state.total_days})",
            )

        except Exception as e:
            # ---------------------------------------------------------
            # FAILURE PATH (retry + cooldown)
            # ---------------------------------------------------------
            state.retry_count += 1
            state.last_error = str(e)

            if state.retry_count >= MAX_BACKFILL_RETRIES:
                state.failed_until = timezone.now() + timedelta(
                    minutes=RETRY_COOLDOWN_MINUTES
                )
                append_job_log(
                    job_id,
                    f"[{inst.symbol}] blocked for {RETRY_COOLDOWN_MINUTES} min "
                    f"after {state.retry_count} failures",
                )

            state.save()
            append_job_log(job_id, f"[{inst.symbol}] error: {e}")
            break  # FAIL-FAST per symbol to avoid wasting API quota


# -----------------------------------------------------------------------------
# Main job entrypoint
# -----------------------------------------------------------------------------
def run(job_id=None, dry_run=False):
    append_job_log(job_id, "Starting historical backfill job")

    today = date.today()
    instruments = get_bhavcopy_filtered_universe(job_id=job_id)

    for inst in instruments:
        for interval, years in [
            # (INTERVAL_1MIN, 1),  # intentionally disabled
            (INTERVAL_5MIN, 1),
        ]:
            state, _ = HistoricalBackfillState.objects.get_or_create(
                instrument=inst,
                interval=interval,
            )

            if state.last_fetched_date:
                start = state.last_fetched_date + timedelta(days=1)
            else:
                start = today - timedelta(days=365 * years)

            end = today - timedelta(days=1)

            if start > end:
                continue

            total_days = (end - start).days + 1
            if total_days <= 0:
                continue

            state.total_days = total_days
            state.completed_days = 0
            state.started_at = timezone.now()
            state.save()

            append_job_log(
                job_id,
                f"Backfilling {inst.symbol} [{interval}] from {start} → {end}",
            )

            if dry_run:
                append_job_log(
                    job_id,
                    "⚠️ DRY RUN MODE ENABLED — no API calls will be made",
                )

            backfill_instrument(
                inst=inst,
                interval=interval,
                start_date=start,
                end_date=end,
                job_id=job_id,
                dry_run=dry_run,
            )

    append_job_log(job_id, "Historical backfill completed")


# -----------------------------------------------------------------------------
# Synthetic candle generator (DEV ONLY)
# -----------------------------------------------------------------------------
def generate_fake_candles(day, interval):
    candles = []

    if interval == INTERVAL_1MIN:
        steps = 375
        delta = timedelta(minutes=1)
    else:
        steps = 75
        delta = timedelta(minutes=5)

    base_price = random.uniform(100, 500)
    ts = datetime.combine(day, time(9, 15))

    for _ in range(steps):
        open_ = base_price + random.uniform(-1, 1)
        high = open_ + random.uniform(0, 1)
        low = open_ - random.uniform(0, 1)
        close = random.uniform(low, high)
        volume = random.randint(1000, 50000)

        candles.append(
            {
                "timestamp": ts.isoformat(),
                "open": round(open_, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume,
            }
        )

        ts += delta
        base_price = close

    return candles
