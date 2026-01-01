# mlapp/views/backtest_run_view.py

from django.shortcuts import render, redirect
from django.utils import timezone

from mlapp.forms.backtest_form import BacktestRunForm

# Import JobStatus model to create a DB job entry
from jobs.models import JobStatus

# Import the celery task (must be a @shared_task in jobs/tasks.py)
from jobs.tasks import run_backtest_async


def backtest_run_form(request):
    """
    Backtest form handler.
    Creates a JobStatus entry, launches the Celery backtest task,
    stores the Celery task_id on the JobStatus, and redirects to job detail.
    """
    if request.method == "POST":
        form = BacktestRunForm(request.POST)
        if form.is_valid():
            symbols = [s.strip() for s in form.cleaned_data["symbols"].split(",") if s.strip()]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            strict = form.cleaned_data["strict_mode"]

            # 1) Create JobStatus row (numeric id)
            job = JobStatus.objects.create(
                job_type="BACKTEST",
                status="PENDING",
                created_at=timezone.now()
            )

            # 2) Launch Celery task and persist the Celery task id (UUID)
            # Note: run_backtest_async.delay(...) returns AsyncResult; .id is the UUID string
            async_result = run_backtest_async.delay(symbols, str(start_date), str(end_date), bool(strict))

            # Save celery task id for tracking
            job.task_id = async_result.id
            job.save(update_fields=["task_id"])

            # 3) Redirect to the job detail page using numeric JobStatus.id
            return redirect("job_detail", job_id=job.id)

    else:
        form = BacktestRunForm()

    return render(request, "backtest_run_form.html", {"form": form})
