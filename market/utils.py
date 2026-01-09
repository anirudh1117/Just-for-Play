# market/utils/time.py

from datetime import datetime
from django.utils import timezone


def normalize_ts(ts):
    """
    Normalize timestamp to:
    - timezone-aware
    - UTC
    - no microseconds
    """
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))

    if timezone.is_naive(ts):
        ts = timezone.make_aware(ts, timezone.get_current_timezone())

    ts = ts.astimezone(timezone.utc)
    return ts.replace(microsecond=0)
