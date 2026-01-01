from datetime import date, timedelta
from django.utils import timezone

from market.models import HistoricalBackfillState
from market.constants import INTERVAL_5MIN
from market.services.bhavcopy_universe import get_bhavcopy_filtered_universe
from market.services.historical_backfill import backfill_instrument
from jobs.utils import append_job_log


def run(job_id=None):
    append_job_log(job_id, "Starting historical backfill job")

    instruments = get_bhavcopy_filtered_universe(job_id=job_id)

    for inst in instruments[:10]:
        append_job_log(job_id, f"Selected EQ: {inst.symbol} {inst.instrument_key}")

    today = date.today()

    for inst in instruments:
        for interval, years in [
            #(INTERVAL_1MIN, 1),
            (INTERVAL_5MIN, 1),
        ]:
            state, _ = HistoricalBackfillState.objects.get_or_create(
                instrument=inst,
                interval=interval,
            )

            end = today - timedelta(days=1)

            if state and state.last_fetched_date:
                start = state.last_fetched_date + timedelta(days=1)
            else:
                start = today - timedelta(days=365 * years)

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
                f"Backfilling {inst.symbol} [{interval}] from {start} → {end}"
            )

            backfill_instrument(
                inst=inst,
                interval=interval,
                start_date=start,
                end_date=end,
                job_id=job_id,
            )

    append_job_log(job_id, "Historical backfill completed")
