from django.db import models
from market.models import Instrument


class PredictionHistory(models.Model):
    """
    Stores the evening shortlist (top 30 candidates) to be used for next-day final picks.
    """

    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    date = models.DateField()                       # EOD date for which shortlist was generated
    prob_up = models.FloatField()                   # model probability
    confidence = models.FloatField()                # prob_up * 100
    entry = models.FloatField()
    target = models.FloatField()
    stoploss = models.FloatField()

    close = models.FloatField()
    vwap = models.FloatField()
    atr_14 = models.FloatField()
    volume = models.BigIntegerField()

    ts = models.DateTimeField()                     # timestamp of latest candle

    feature_hash = models.CharField(max_length=64)  # to track feature snapshot version
    model_version = models.CharField(max_length=50) # model filename

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["instrument"]),
        ]

    def __str__(self):
        return f"{self.date} - {self.instrument.symbol} ({self.confidence}%)"
