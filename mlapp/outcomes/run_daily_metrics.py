from django.utils import timezone

from jobs.utils import append_job_log
from mlapp.models import TradeOutcome
from mlapp.outcomes.metrics_engine import OutcomeMetricsEngine


def run(job_id=None):
    today = timezone.now().date()
    append_job_log(job_id, "Computing outcome metrics...")

    qs = TradeOutcome.objects.filter(date__lte=today)
    engine = OutcomeMetricsEngine(qs)

    summary = engine.summary()

    append_job_log(job_id, f"Trades: {summary['trades']}")
    append_job_log(job_id, f"Win rate: {summary['win_rate_pct']}%")
    append_job_log(job_id, f"Expectancy: {summary['expectancy']}")
    append_job_log(job_id, f"Max DD (R): {summary['max_drawdown_R']}")

    return summary
