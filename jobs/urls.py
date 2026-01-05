from django.urls import path
from . import views

urlpatterns = [
    # Dashboard (we also mapped it in core.urls, but here is fine for job-specific)
    path("dashboard/", views.dashboard, name="dashboard"),

    # Trigger endpoints
    path("fetch-today/", views.trigger_fetch_today, name="trigger_fetch_today"),
    path("compute-features/", views.trigger_compute_features, name="trigger_compute_features"),
    path("train-model/", views.trigger_train_model, name="trigger_train_model"),
    path("evening-predict/", views.trigger_evening_predict, name="trigger_evening_predict"),
    path("morning-confirm/", views.trigger_morning_confirm, name="trigger_morning_confirm"),
    path("instrument-sync/", views.trigger_instrument_sync, name="trigger_instrument_sync"),

    # Job detail + logs
    path("<int:job_id>/", views.job_detail, name="job_detail"),

    # Polling fallback API (if WebSocket fails)
    path("api/logs/<int:job_id>/", views.job_logs_api, name="job_logs_api"),
    path("optimize/", views.trigger_optimize_strategy, name="trigger_optimize_strategy"),
    path("historical-backfill/", views.trigger_historical_backfill, name="trigger_historical_backfill"),
    path("sync-holidays/", views.trigger_sync_holidays, name="trigger_sync_holidays"),
    path("gap-repair/", views.trigger_gap_repair, name="trigger_gap_repair"),
    path("run-morning-inference/", views.trigger_morning_inference, name="trigger_morning_inference"),
    path("run-outcome-evaluation/", views.trigger_outcome_evaluation, name="trigger_outcome_evaluation"),
    path("run-metrics-computation/", views.trigger_metrics_computation, name="trigger_metrics_computation"),

]

