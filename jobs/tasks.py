from celery import shared_task, current_task
from django.utils import timezone

from jobs.utils import append_job_log
from .models import JobStatus, JobLog
from mlapp.backtest.backtest_engine import BacktestEngine
from mlapp.backtest.result_writer import save_equity_curve
from mlapp.models.backtest_history import BacktestHistory
from mlapp.backtest.exporter import BacktestExporter
from mlapp.optimizer.strategy_optimizer import StrategyOptimizer



import traceback


# ---------------------------------------------------------
# Universal job wrapper
# ---------------------------------------------------------

@shared_task(bind=True)
def run_job(self, job_id, func_path, func_kwargs=None):
    """
    A universal executor that:
    - loads the JobStatus
    - updates its state (STARTED, SUCCESS, FAILED)
    - logs steps to JobLog
    - dynamically calls a function by import path
    """

    func_kwargs = func_kwargs or {}

    try:
        job = JobStatus.objects.get(id=job_id)
    except JobStatus.DoesNotExist:
        return "Job not found"

    # Mark as started
    job.status = "STARTED"
    job.started_at = timezone.now()
    job.task_id = self.request.id
    job.save()

    append_job_log(job_id, f"Job started: {job.job_type}")
    append_job_log(job_id, f"Executing: {func_path}")

    # -----------------------------------------------------
    # Dynamically import the function
    # -----------------------------------------------------
    try:
        module_path, func_name = func_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[func_name])
        func = getattr(module, func_name)
    except Exception as e:
        err = f"Failed to import function {func_path}: {e}"
        append_job_log(job_id, err)
        job.status = "FAILED"
        job.finished_at = timezone.now()
        job.message = err
        job.save()
        return err

    # -----------------------------------------------------
    # Execute the job function
    # -----------------------------------------------------
    try:
        result = func(**func_kwargs)
        append_job_log(job_id, f"Completed successfully.")
        job.status = "SUCCESS"
        job.finished_at = timezone.now()
        job.message = str(result)
        job.save()
        return result

    except Exception as e:
        err = f"Error executing {func_path}: {e}\n{traceback.format_exc()}"
        append_job_log(job_id, err)
        job.status = "FAILED"
        job.finished_at = timezone.now()
        job.message = err
        job.save()
        return err
    

@shared_task(bind=True)
def run_backtest_async(self, symbols, start_date, end_date, strict):
    append_job_log(self.request.id, "Starting backtest...")

    engine = BacktestEngine(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        strict=strict
    )

    result = engine.run()

    append_job_log(self.request.id, "Backtest simulation complete.")

    # save equity curve image
    equity = result["metrics"]["equity_curve"]
    run_id = BacktestHistory.objects.last().id
    save_equity_curve(equity, run_id)

    append_job_log(self.request.id, f"Backtest results saved as Run #{run_id}.")
    append_job_log(self.request.id, "Done.")
    
    exporter = BacktestExporter(result, run_id)
    exporter.export_daily_trades()
    exporter.export_symbol_stats()
    exporter.export_equity_curve()
    exporter.export_daily_returns()
    exporter.export_summary_json()

    append_job_log(self.request.id, "Export files created successfully.")


    return result

@shared_task(bind=True)
def optimize_strategy_async(self, job_id, symbols, start_date, end_date):
    """
    Celery task to run strategy optimizer.
    """
    append_job_log(job_id, "Starting Strategy Optimization...")

    try:
        # Initialize optimizer
        optimizer = StrategyOptimizer(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
        )

        append_job_log(job_id, f"Loaded {len(optimizer.combinations)} combinations.")

        # Run optimization
        results = optimizer.run()

        append_job_log(job_id, "Optimization Complete.")
        append_job_log(job_id, f"Best Score: {results[0]['score']:.4f}")
        append_job_log(job_id, f"Best Params: {results[0]['params']}")

    except Exception as e:
        append_job_log(job_id, f"Error: {str(e)}")
        raise

    return "OK"

