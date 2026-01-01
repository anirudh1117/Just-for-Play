from django.db import models
from django.utils import timezone

from market.constants import (
    JOB_FETCH_TODAY,
    JOB_COMPUTE_FEATURES,
    JOB_HISTORICAL_BACKFILL,
    JOB_METRICS_COMPUTE,
    JOB_MORNING_INFERENCE,
    JOB_OUTCOME_EVAL,
    JOB_SYNC_HOLIDAYS,
    JOB_TRAIN_MODEL,
    JOB_EVENING_PREDICT,
    JOB_MORNING_CONFIRM,
    JOB_INSTRUMENT_SYNC
)



class JobStatus(models.Model):
    """
    Represents a background job (Celery task) initiated from UI.
    Tracks status, start/end time, and result.
    """
    JOB_TYPES = [
    (JOB_FETCH_TODAY, "Fetch Today's Market Data"),
    (JOB_COMPUTE_FEATURES, "Compute Features"),
    (JOB_TRAIN_MODEL, "Train ML Model"),
    (JOB_EVENING_PREDICT, "Evening Prediction"),
    (JOB_MORNING_CONFIRM, "Morning Confirmation"),
    (JOB_INSTRUMENT_SYNC, "Sync Instruments"),
    (JOB_HISTORICAL_BACKFILL, "Historical Data Backfill"),
    (JOB_SYNC_HOLIDAYS, "Sync NSE Holidays"),
    (JOB_MORNING_INFERENCE, "Morning Inference"),
    (JOB_OUTCOME_EVAL, "Outcome Evaluation"),
    (JOB_METRICS_COMPUTE, "Metrics Computation"),


]


    job_type = models.CharField(max_length=50, choices=JOB_TYPES)
    task_id = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=[
            ("PENDING", "Pending"),
            ("STARTED", "Started"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed"),
        ],
    )

    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Optional result message
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.job_type} ({self.status})"


class JobLog(models.Model):
    """
    Log lines for a job, used for real-time UI streaming.
    """
    job = models.ForeignKey(JobStatus, on_delete=models.CASCADE, related_name="logs")
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()

    def __str__(self):
        return f"[{self.timestamp}] {self.message}"
