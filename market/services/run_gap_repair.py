from datetime import date, timedelta
from market.services.bhavcopy_universe import get_bhavcopy_filtered_universe
from market.services.universe_selector import get_phase1_universe
from market.services.gap_repair import repair_gaps
from market.constants import INTERVAL_1MIN, INTERVAL_5MIN
from jobs.utils import append_job_log


def run(job_id=None):
    append_job_log(job_id, "Starting gap detection & repair")

    today = date.today()

    for inst in get_bhavcopy_filtered_universe(job_id=job_id):
        for interval in [INTERVAL_1MIN, INTERVAL_5MIN]:
            start = today - timedelta(days=365)
            end = today - timedelta(days=1)

            repair_gaps(inst, interval, start, end, job_id)

    append_job_log(job_id, "Gap repair completed")
