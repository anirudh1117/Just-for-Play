from django.db import models


class MorningInferenceRun(models.Model):
    date = models.DateField(unique=True)
    model_version = models.CharField(max_length=255)
    symbols = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
