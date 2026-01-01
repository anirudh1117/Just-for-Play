from django.shortcuts import render, get_object_or_404
from mlapp.models.strategy_optimization import StrategyOptimizationResult


def optimizer_list(request):
    """
    Shows all past optimization runs.
    """
    runs = StrategyOptimizationResult.objects.order_by("-created_at")
    return render(request, "optimizer_list.html", {"runs": runs})


def optimizer_detail(request, opt_id):
    """
    Detailed view of a specific optimization run.
    """
    run = get_object_or_404(StrategyOptimizationResult, id=opt_id)

    best_params = run.best_params
    best_metrics = run.best_metrics

    context = {
        "run": run,
        "best_params": best_params,
        "best_metrics": best_metrics,
        "full_results": run.all_results or [],
    }

    return render(request, "optimizer_detail.html", context)
