#from market.services.gap_detector import find_missing_days
#from market.services.historical_backfill import backfill_instrument
#from jobs.utils import append_job_log
#
#
#def repair_gaps(inst, interval, start, end, job_id=None):
#    missing_days = find_missing_days(inst, interval, start, end)
#
#    if not missing_days:
#        append_job_log(job_id, f"[{inst.symbol}] no gaps detected")
#        return
#
#    append_job_log(
#        job_id,
#        f"[{inst.symbol}] repairing {len(missing_days)} missing days"
#    )
#
#    for day in missing_days:
#        backfill_instrument(
#            inst=inst,
#            interval=interval,
#            start_date=day,
#            end_date=day,
#            job_id=job_id,
#        )

from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

from market.api.upstox_client import UpstoxClient
from market.models import Candle
from market.services.gap_detector import find_missing_days
from jobs.utils import append_job_log


def repair_gaps(inst, interval, start, end, job_id=None):
    """
    Repairs missing candle days for a given instrument and interval.

    IMPORTANT CONTRACT:
    - Does NOT touch HistoricalBackfillState
    - Uses Upstox v3 historical-candle API
    - Stores Candle.ts in UTC (timezone-aware)
    - One day fetched per API call
    """

    missing_days = find_missing_days(inst, interval, start, end)

    if not missing_days:
        append_job_log(job_id, f"[{inst.symbol}] no gaps detected")
        return

    append_job_log(
        job_id,
        f"[{inst.symbol}] repairing {len(missing_days)} missing days "
        f"for interval {interval}"
    )

    client = UpstoxClient(log_job_id=job_id)

    for day in missing_days:
        append_job_log(
            job_id,
            f"[{inst.symbol}] gap repair → {interval} → {day}"
        )

        try:
            resp = client.fetch_historical_candles(
                instrument_key=inst.instrument_key,
                interval=interval,
                from_date=day,
                to_date=day,
            )

            data = resp.get("data", {})
            candles = data.get("candles", [])
            if not candles:
                append_job_log(
                    job_id,
                    f"[{inst.symbol}] no data returned for {day} (skipping)"
                )
                continue

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

        except Exception as e:
            append_job_log(
                job_id,
                f"[{inst.symbol}] gap repair failed for {day}: {e}"
            )
            # Fail-fast for this symbol/day; continue with next day
            continue
