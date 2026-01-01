from django.shortcuts import render, get_object_or_404
from mlapp.models.backtest_history import BacktestHistory


def backtest_list(request):
    """
    List all backtest runs.
    """
    runs = BacktestHistory.objects.order_by("-created_at")
    return render(request, "backtest_list.html", {"runs": runs})


def backtest_detail(request, run_id):
    """
    Detailed view of one backtest run.
    Includes metrics like Sharpe, Drawdown, Equity Curve, etc.
    """
    run = get_object_or_404(BacktestHistory, id=run_id)

    details = run.result_json  # list of {date, results}
    metrics = run.result_json  # replaced later; this will be overwritten

    # Combined result_json contains metrics already
    metrics = run.result_json if "metrics" in run.result_json else {}

    context = {
        "run": run,
        "details": run.result_json,
        "metrics": metrics,
    }

    return render(request, "backtest_detail.html", context)
