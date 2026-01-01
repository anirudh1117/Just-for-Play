from django.db import models
from django.utils import timezone
from market.constants import *

# -----------------------------------------------------------------------------
# INSTRUMENT MASTER
# -----------------------------------------------------------------------------
class Instrument(models.Model):
    """
    Canonical instrument master synced from Upstox.
    instrument_key is the ONLY stable identifier.
    """

    instrument_key = models.CharField(max_length=50, unique=True)
    symbol = models.CharField(max_length=50, db_index=True)

    name = models.CharField(max_length=200, null=True, blank=True)
    exchange = models.CharField(max_length=10, default=EXCHANGE_NSE)
    instrument_type = models.CharField(max_length=10, default=INSTRUMENT_EQ)

    tick_size = models.FloatField(default=0.05)
    lot_size = models.IntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} ({self.instrument_key})"


# -----------------------------------------------------------------------------
# CANDLE DATA (TIME-SERIES)
# -----------------------------------------------------------------------------
class Candle(models.Model):
    """
    Stores OHLCV candles for each instrument.

    TIMESTAMP CONTRACT (FROZEN):
    - ts is ALWAYS stored in UTC (timezone-aware)
    - All upstream ingestion MUST normalize to UTC before save
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

    # UTC timestamp of candle open
    ts = models.DateTimeField(db_index=True)

    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()

    interval = models.CharField(max_length=10, default=INTERVAL_1MIN)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instrument", "ts", "interval"],
                name="unique_candle_per_interval",
            )
        ]
        indexes = [
            models.Index(fields=["instrument", "ts"]),
        ]

    def __str__(self):
        return f"{self.instrument.symbol} {self.ts} {self.interval}"


# -----------------------------------------------------------------------------
# UPSTOX AUTH TOKEN (FAIL-FAST DESIGN)
# -----------------------------------------------------------------------------
class UpstoxToken(models.Model):
    """
    Stores the current Upstox access token.
    Refresh tokens are intentionally NOT stored.
    """

    access_token = models.TextField()
    expires_at = models.DateTimeField()
    updated_at = models.DateTimeField(default=timezone.now)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def will_expire_soon(self, minutes=5):
        return timezone.now() >= (
            self.expires_at - timezone.timedelta(minutes=minutes)
        )

    def __str__(self):
        return f"UpstoxToken (expires {self.expires_at})"


# -----------------------------------------------------------------------------
# HISTORICAL BACKFILL STATE (PER INSTRUMENT + INTERVAL)
# -----------------------------------------------------------------------------
class HistoricalBackfillState(models.Model):
    """
    Tracks resumable backfill progress per instrument AND interval.
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    interval = models.CharField(max_length=10)

    last_fetched_date = models.DateField(null=True, blank=True)

    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)
    failed_until = models.DateTimeField(null=True, blank=True)

    total_days = models.PositiveIntegerField(default=0)
    completed_days = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    last_progress_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instrument", "interval"],
                name="unique_backfill_state_per_interval",
            )
        ]

    def __str__(self):
        return f"BackfillState({self.instrument.symbol}, {self.interval})"


# -----------------------------------------------------------------------------
# TRADING HOLIDAYS
# -----------------------------------------------------------------------------
class TradingHoliday(models.Model):
    """
    Exchange-specific trading holidays.
    """

    date = models.DateField()
    exchange = models.CharField(max_length=20, default=EXCHANGE_NSE)
    description = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "exchange"],
                name="unique_holiday_per_exchange",
            )
        ]

    def __str__(self):
        return f"{self.date} ({self.exchange})"