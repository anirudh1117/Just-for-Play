from datetime import datetime
from market.api.upstox_client import UpstoxClient
from market.models import TradingHoliday
from jobs.utils import append_job_log


#def sync_holidays(job_id=None):
#    """
#    Fetch NSE holidays from Upstox and persist them.
#    This should be run once per year or on demand.
#    """
#    client = UpstoxClient(log_job_id=job_id)
#
#    append_job_log(job_id, "Fetching NSE holidays from Upstox")
#
#    # Upstox returns holidays for current year
#    resp = client._get("/market/holidays")
#    holidays = resp.get("data", [])
#
#    saved = 0
#    for h in holidays:
#        TradingHoliday.objects.update_or_create(
#            date=datetime.strptime(h["date"], "%Y-%m-%d").date(),
#            defaults={
#                "exchange": "NSE",
#                "description": h.get("description", ""),
#            },
#        )
#        saved += 1
#
#    append_job_log(job_id, f"Saved {saved} NSE holidays")
#    return saved

def sync_holidays(job_id=None):
    """
    NSE holidays must be loaded from an official static source.
    Upstox v3 does NOT guarantee a holidays API.
    """
    append_job_log(
        job_id,
        "Holiday sync disabled: load holidays manually from NSE circulars"
    )
    return 0

