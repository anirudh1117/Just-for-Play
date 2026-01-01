from django.db import models
from market.models import Instrument


class FinalPickHistory(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    date = models.DateField()
    
    prob_up_live = models.FloatField()
    confidence = models.FloatField()

    entry = models.FloatField()
    target = models.FloatField()
    stoploss = models.FloatField()

    close = models.FloatField()
    vwap = models.FloatField()
    atr_14 = models.FloatField()
    volume = models.BigIntegerField()

    ts = models.DateTimeField()

    model_version = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
