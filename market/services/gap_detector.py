from datetime import timedelta

from django.db.models.functions import TruncDate
from django.db.models import DateField
from django.db.models import Q

from market.models import Candle
from market.services.trading_calendar import is_trading_day


def find_missing_days(instrument, interval, start, end):
    """
    Returns list of dates where trading was expected but no candles exist.

    Assumptions (FROZEN):
    - Candle.ts is stored in UTC (timezone-aware)
    - Trading calendar decides whether a day is tradable
    """

    # Collect distinct trading dates that already have candles
    existing_dates = set(
        Candle.objects.filter(
            instrument=instrument,
            interval=interval,
            ts__date__range=(start, end),
        )
        .annotate(day=TruncDate("ts", output_field=DateField()))
        .values_list("day", flat=True)
        .distinct()
    )

    missing_days = []

    cur = start
    while cur <= end:
        if is_trading_day(cur) and cur not in existing_dates:
            missing_days.append(cur)
        cur += timedelta(days=1)

    return missing_days
