from datetime import date, timedelta
from calendar import monthrange

from django.db import transaction
from django.utils import timezone

from market.models import Candle
from market.api.upstox_client import UpstoxClient
from market.services.gap_detector import find_missing_days
from jobs.utils import append_job_log
from market.utils import normalize_ts


# ---------------------------------------------------------
# Helper: group sorted dates into contiguous ranges
# ---------------------------------------------------------
def _group_into_ranges(days: list[date]) -> list[tuple[date, date]]:
    """
    Convert list of dates into contiguous (start, end) ranges.
    """
    if not days:
        return []

    days = sorted(days)
    ranges = []

    start = prev = days[0]

    for d in days[1:]:
        if d == prev + timedelta(days=1):
            prev = d
            continue

        ranges.append((start, prev))
        start = prev = d

    ranges.append((start, prev))
    return ranges


# ---------------------------------------------------------
# Helper: split a range so it never crosses month boundary
# ---------------------------------------------------------
def _split_by_month(start: date, end: date) -> list[tuple[date, date]]:
    """
    Split a (start, end) range into month-safe subranges.
    """
    ranges = []
    cur = start

    while cur <= end:
        last_day = monthrange(cur.year, cur.month)[1]
        month_end = date(cur.year, cur.month, last_day)

        window_end = min(month_end, end)
        ranges.append((cur, window_end))

        cur = window_end + timedelta(days=1)

    return ranges


# ---------------------------------------------------------
# GAP REPAIR (range-based, bulk)
# ---------------------------------------------------------
def repair_gaps(inst, interval, start, end, job_id=None):
    """
    Repair missing trading-day gaps using:
    - contiguous ranges
    - month-safe windows
    - bulk inserts
    """

    missing_days = find_missing_days(inst, interval, start, end)

    if not missing_days:
        append_job_log(job_id, f"[{inst.symbol}] no gaps detected")
        return

    append_job_log(
        job_id,
        f"[{inst.symbol}] repairing {len(missing_days)} missing trading days"
    )

    client = UpstoxClient(log_job_id=job_id)

    # Step 1: contiguous ranges
    ranges = _group_into_ranges(missing_days)

    for range_start, range_end in ranges:

        # Step 2: split by calendar month
        month_safe_ranges = _split_by_month(range_start, range_end)

        for window_start, window_end in month_safe_ranges:
            append_job_log(
                job_id,
                f"[{inst.symbol}] gap fetch {interval} "
                f"{window_start} → {window_end}"
            )

            try:
                resp = client.fetch_historical_candles(
                    instrument_key=inst.instrument_key,
                    interval=interval,
                    from_date=window_start,
                    to_date=window_end,
                )

                candles = resp.get("data", {}).get("candles", [])

                if not candles:
                    continue

                candle_objs = []
                for c in candles:
                    candle_objs.append(
                        Candle(
                            instrument=inst,
                            ts=normalize_ts(c[0]),
                            open=c[1],
                            high=c[2],
                            low=c[3],
                            close=c[4],
                            volume=c[5],
                            interval=interval,
                        )
                    )

                with transaction.atomic():
                    Candle.objects.bulk_create(
                        candle_objs,
                        batch_size=1000,
                        ignore_conflicts=True,
                    )

            except Exception as e:
                append_job_log(
                    job_id,
                    f"[{inst.symbol}] gap repair error "
                    f"{window_start} → {window_end}: {e}"
                )
                # continue with next range, do NOT stop entire job
                continue
