from django.db import models
from django.utils import timezone
from django.db.models import JSONField


class StrategyOptimizationResult(models.Model):
    """
    Stores the output of one optimization run.
    Includes:
    - Best strategy parameters
    - Best score
    - Metrics
    - Optional: full ranked results
    """

    created_at = models.DateTimeField(default=timezone.now)

    # Best parameters selected by optimizer
    best_params = JSONField()

    # Best performance metrics (Sharpe, win% etc.)
    best_metrics = JSONField()

    # Best score
    best_score = models.FloatField()

    # Optional: entire ranked result list (compressed JSON)
    all_results = JSONField(null=True, blank=True)

    def __str__(self):
        return f"StrategyOptimizationResult (Score {self.best_score:.4f} @ {self.created_at})"
