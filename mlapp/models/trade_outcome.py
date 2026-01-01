from django.db import models


class TradeOutcome(models.Model):
    """
    Immutable ground truth of what happened to a predicted trade.
    One row per (date, symbol, model_version).
    """

    EXIT_CHOICES = (
        ("TP", "Target Hit"),
        ("SL", "Stop Loss Hit"),
        ("TIMEOUT", "Timeout"),
        ("INVALID", "Invalid"),
    )

    date = models.DateField()
    symbol = models.CharField(max_length=32)

    model_version = models.CharField(max_length=128)
    prediction_time = models.DateTimeField()

    entry_time = models.DateTimeField(null=True, blank=True)
    entry_price = models.FloatField(null=True, blank=True)

    exit_time = models.DateTimeField(null=True, blank=True)
    exit_price = models.FloatField(null=True, blank=True)

    exit_reason = models.CharField(
        max_length=16, choices=EXIT_CHOICES
    )

    holding_minutes = models.IntegerField(default=0)

    tp_price = models.FloatField(null=True, blank=True)
    sl_price = models.FloatField(null=True, blank=True)

    R_multiple = models.FloatField()
    pnl_pct = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("date", "symbol", "model_version")
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["symbol"]),
            models.Index(fields=["model_version"]),
        ]

    def __str__(self):
        return f"{self.date} | {self.symbol} | {self.exit_reason} | R={self.R_multiple}"
