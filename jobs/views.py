from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse

from .models import JobStatus, JobLog
from .tasks import optimize_strategy_async, run_job
from market.constants import (
    JOB_FETCH_TODAY,
    JOB_COMPUTE_FEATURES,
    JOB_SYNC_HOLIDAYS,
    JOB_TRAIN_MODEL,
    JOB_EVENING_PREDICT,
    JOB_MORNING_CONFIRM,
    JOB_INSTRUMENT_SYNC,
    JOB_HISTORICAL_BACKFILL,
    JOB_MORNING_INFERENCE,
    JOB_OUTCOME_EVAL,
    JOB_METRICS_COMPUTE,
)



# ---------------------------------------------------------
# Helper — Create + Run Job
# ---------------------------------------------------------

def _create_and_run(job_type, func_path, func_kwargs=None):
    """
    Creates a JobStatus entry and starts Celery run_job task.
    """
    job = JobStatus.objects.create(
        job_type=job_type,
        status="PENDING",
        created_at=timezone.now()
    )

    # Launch background job
    run_job.delay(
        job_id=job.id,
        func_path=func_path,
        func_kwargs=func_kwargs or {}
    )

    return job


# ---------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------

def dashboard(request):
    """
    Main dashboard showing job buttons & recent jobs.
    """
    recent_jobs = JobStatus.objects.order_by("-created_at")[:20]

    return render(request, "dashboard.html", {
        "jobs": recent_jobs
    })


# ---------------------------------------------------------
# Trigger Job Views
# ---------------------------------------------------------

def trigger_fetch_today(request):
    job = _create_and_run(
        job_type=JOB_FETCH_TODAY,
        func_path="market.services.fetch_today.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


def trigger_compute_features(request):
    job = _create_and_run(
        job_type=JOB_COMPUTE_FEATURES,
        func_path="mlapp.features.compute_features.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


def trigger_train_model(request):
    job = _create_and_run(
        job_type=JOB_TRAIN_MODEL,
        func_path="mlapp.training.train_lgbm.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


def trigger_evening_predict(request):
    job = _create_and_run(
        job_type=JOB_EVENING_PREDICT,
        func_path="mlapp.inference.scorer.run_evening"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


def trigger_morning_confirm(request):
    job = _create_and_run(
        job_type=JOB_MORNING_CONFIRM,
        func_path="market.services.morning_stream.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


def trigger_instrument_sync(request):
    job = _create_and_run(
        job_type=JOB_INSTRUMENT_SYNC,
        func_path="market.services.instrument_loader.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


# ---------------------------------------------------------
# Job Detail + Logs
# ---------------------------------------------------------

def job_detail(request, job_id):
    job = get_object_or_404(JobStatus, id=job_id)
    logs = JobLog.objects.filter(job=job_id).order_by("timestamp")
    return render(request, "logs.html", {
        "job": job,
        "logs": logs
    })


# ---------------------------------------------------------
# API Endpoint for log polling (fallback if WS fails)
# ---------------------------------------------------------

def job_logs_api(request, job_id):
    job = get_object_or_404(JobStatus, id=job_id)
    logs = JobLog.objects.filter(job=job)
    data = [{"timestamp": str(l.timestamp), "message": l.message} for l in logs]
    return JsonResponse({"logs": data})

def trigger_run_backtest(request):
    job = _create_and_run(
        job_type="BACKTEST",
        func_path="mlapp.backtest.run_backtest.run",
        func_kwargs={}
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))

def trigger_optimize_strategy(request):
    """
    Create a job entry, start Celery optimizer.
    """
    from datetime import datetime, timedelta

    # Example: run optimization for last 1 year
    end = datetime.now().date()
    start = end - timedelta(days=365)

    symbols = ["TATAMOTORS", "TATASTEEL", "RELIANCE", "HDFCBANK"]  # temporary preset

    # Create job entry
    job = JobStatus.objects.create(
        job_type="STRATEGY_OPTIMIZATION",
        status="PENDING",
        created_at=timezone.now()
    )

    # Start background task
    optimize_strategy_async.delay(
        job_id=job.id,
        symbols=symbols,
        start_date=str(start),
        end_date=str(end),
    )

    return redirect("job_detail", job_id=job.id)


def trigger_historical_backfill(request):
    job = _create_and_run(
        job_type=JOB_HISTORICAL_BACKFILL,
        func_path="market.services.run_backfill.run",
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))

def trigger_sync_holidays(request):
    job = _create_and_run(
        job_type=JOB_SYNC_HOLIDAYS,
        func_path="market.services.holiday_loader.sync_holidays",
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))

# --------------------------------------------------
# Morning Inference
# --------------------------------------------------
def trigger_morning_inference(request):
    job = _create_and_run(
        job_type=JOB_MORNING_INFERENCE,
        func_path="mlapp.inference.morning_inference.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


# --------------------------------------------------
# Outcome Evaluation (Evening)
# --------------------------------------------------
def trigger_outcome_evaluation(request):
    job = _create_and_run(
        job_type=JOB_OUTCOME_EVAL,
        func_path="mlapp.outcomes.run_daily_outcomes.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))


# --------------------------------------------------
# Metrics Computation
# --------------------------------------------------
def trigger_metrics_computation(request):
    job = _create_and_run(
        job_type=JOB_METRICS_COMPUTE,
        func_path="mlapp.outcomes.run_daily_metrics.run"
    )
    return redirect(reverse("job_detail", kwargs={"job_id": job.id}))




