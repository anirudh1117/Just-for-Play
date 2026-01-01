from django.shortcuts import render
from mlapp.models import TradeOutcome
from mlapp.outcomes.metrics_engine import OutcomeMetricsEngine


def outcome_dashboard(request):
    qs = TradeOutcome.objects.all().order_by("-created_at")

    engine = OutcomeMetricsEngine(qs)
    summary = engine.summary()

    recent_trades = qs[:50]

    context = {
        "summary": summary,
        "recent_trades": recent_trades,
    }

    return render(request, "mlapp/outcomes/dashboard.html", context)
