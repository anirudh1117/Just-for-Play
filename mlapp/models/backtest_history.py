from django.db import models


class BacktestHistory(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)

    symbols = models.JSONField()
    start_date = models.DateField()
    end_date = models.DateField()

    win_rate = models.FloatField()
    total_trades = models.IntegerField()
    wins = models.IntegerField()
    losses = models.IntegerField()
    zeroes = models.IntegerField()

    result_json = models.JSONField()  # each day's results

    created_at = models.DateTimeField(auto_now_add=True)
