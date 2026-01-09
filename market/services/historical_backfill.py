from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone

from market.models import Candle, HistoricalBackfillState
from market.api.upstox_client import UpstoxClient
from market.constants import (
    MAX_BACKFILL_RETRIES,
    RETRY_COOLDOWN_MINUTES,
)
from market.services.backfill_utils import is_temporarily_blocked
from jobs.utils import append_job_log
from calendar import monthrange
from datetime import date, timedelta

from market.utils import normalize_ts


# -------------------------------------------------------------------
# Helper: split date range into Upstox-compliant windows (≤30 days)
# -------------------------------------------------------------------
def date_windows(start: date, end: date, window_days: int = 30):
    """
    Yield (window_start, window_end) pairs where each window
    spans at most `window_days` calendar days.
    """
    cur = start
    while cur <= end:
        window_end = min(cur + timedelta(days=window_days - 1), end)
        yield cur, window_end
        cur = window_end + timedelta(days=1)


def month_windows(start: date, end: date):
    """
    Yield (window_start, window_end) pairs that NEVER cross
    calendar month boundaries.
    """

    cur = start

    while cur <= end:
        last_day_of_month = monthrange(cur.year, cur.month)[1]
        month_end = date(cur.year, cur.month, last_day_of_month)

        window_end = min(month_end, end)

        yield cur, window_end

        cur = window_end + timedelta(days=1)



# -------------------------------------------------------------------
# Backfill ONE instrument + ONE interval (window-based)
# -------------------------------------------------------------------
def backfill_instrument(
    inst,
    interval,
    start_date,
    end_date,
    job_id=None,
    dry_run=False,
):
    """
    Window-based historical backfill.

    Guarantees:
    - Uses ≤30-day API windows
    - Bulk inserts candles
    - Updates last_fetched_date per successful window
    - Treats empty windows as normal (holidays / IPOs / suspensions)
    """

    client = UpstoxClient(log_job_id=job_id)

    state, _ = HistoricalBackfillState.objects.get_or_create(
        instrument=inst,
        interval=interval,
    )

    # Respect temporary cooldown
    if is_temporarily_blocked(state):
        append_job_log(
            job_id,
            f"[{inst.symbol}] skipped (cooldown active)"
        )
        return

    # ---------------------------------------------------------------
    # Window-based backfill loop
    # ---------------------------------------------------------------
    for window_start, window_end in month_windows(start_date, end_date):
        append_job_log(
            job_id,
            f"[{inst.symbol}] {interval} → {window_start} → {window_end}"
        )

        try:
            # -------------------------------------------------------
            # Fetch candles (one API call per window)
            # -------------------------------------------------------
            if dry_run:
                candles = []
            else:
                resp = client.fetch_historical_candles(
                    instrument_key=inst.instrument_key,
                    interval=interval,
                    from_date=window_start,
                    to_date=window_end,
                )

                # Upstox v3 format:
                # {"status": "success", "data": {"candles": [[ts, o, h, l, c, v, oi], ...]}}
                candles = resp.get("data", {}).get("candles", [])

            # -------------------------------------------------------
            # Empty window is NOT an error
            # -------------------------------------------------------
            if not candles:
                append_job_log(
                    job_id,
                    f"[{inst.symbol}] no data in window "
                    f"{window_start} → {window_end}"
                )

                state.last_fetched_date = window_end
                state.last_progress_at = timezone.now()
                state.save(update_fields=["last_fetched_date", "last_progress_at"])
                continue

            # -------------------------------------------------------
            # Build Candle objects in memory
            # -------------------------------------------------------
            candle_objs = []
            for c in candles:
                candle_objs.append(
                    Candle(
                        instrument=inst,
                        ts=normalize_ts(c[0]),          # timestamp (ISO / tz-aware from Upstox)
                        open=c[1],
                        high=c[2],
                        low=c[3],
                        close=c[4],
                        volume=c[5],
                        interval=interval,
                    )
                )

            # -------------------------------------------------------
            # Bulk insert (critical for performance)
            # -------------------------------------------------------
            if not dry_run:
                with transaction.atomic():
                    Candle.objects.bulk_create(
                        candle_objs,
                        batch_size=1000,
                        ignore_conflicts=True,  # relies on unique_together
                    )

            # -------------------------------------------------------
            # Update progress (window-level semantics)
            # -------------------------------------------------------
            state.last_fetched_date = window_end
            state.retry_count = 0
            state.last_error = None
            state.failed_until = None
            state.last_progress_at = timezone.now()
            state.save(
                update_fields=[
                    "last_fetched_date",
                    "retry_count",
                    "last_error",
                    "failed_until",
                    "last_progress_at",
                ]
            )

        except Exception as e:
            # -------------------------------------------------------
            # Window-level failure handling
            # -------------------------------------------------------
            state.retry_count += 1
            state.last_error = str(e)

            append_job_log(
                job_id,
                f"[{inst.symbol}] error in window "
                f"{window_start} → {window_end}: {e}"
            )

            if state.retry_count >= MAX_BACKFILL_RETRIES:
                state.failed_until = timezone.now() + timedelta(
                    minutes=RETRY_COOLDOWN_MINUTES
                )
                append_job_log(
                    job_id,
                    f"[{inst.symbol}] blocked for "
                    f"{RETRY_COOLDOWN_MINUTES} minutes"
                )

            state.save(
                update_fields=[
                    "retry_count",
                    "last_error",
                    "failed_until",
                ]
            )

            # Stop further windows for this instrument.
            # Resume will retry this same window later.
            break
