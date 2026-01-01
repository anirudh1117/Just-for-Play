from django.db import models    


class MorningPrediction(models.Model):
    date = models.DateField()
    symbol = models.CharField(max_length=50)
    probability = models.FloatField()
    rank = models.IntegerField()
    model_version = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("date", "symbol")
        ordering = ["rank"]

    def __str__(self):
        return f"{self.date} | {self.symbol} | {self.probability:.3f}"