from datetime import date, timedelta
from django.utils import timezone


def date_range(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def is_temporarily_blocked(state):
    if not state or not state.failed_until:
        return False
    return timezone.now() < state.failed_until

def compute_eta(state):
    if not state.started_at or state.completed_days == 0:
        return None

    elapsed = (timezone.now() - state.started_at).total_seconds()
    avg_per_day = elapsed / state.completed_days
    remaining = max(state.total_days - state.completed_days, 0)

    return int(avg_per_day * remaining)

