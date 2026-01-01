from market.models import TradingHoliday


def is_weekend(d):
    return d.weekday() >= 5


def is_holiday(d):
    TradingHoliday.objects.filter(date=d, exchange="NSE").exists()


def is_trading_day(d):
    if is_weekend(d):
        return False
    if is_holiday(d):
        return False
    return True
