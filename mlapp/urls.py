from django.urls import path
from mlapp.views.prediction_history import (
    prediction_history_list,
    prediction_history_detail,
)
from mlapp.views.morning_predictions import (
    morning_prediction_dates,
    morning_prediction_detail,
    today_predictions,
)
from mlapp.views.backtest_views import backtest_list, backtest_detail
from mlapp.views.backtest_run_view import backtest_run_form
from mlapp.views.optimizer_views import optimizer_list, optimizer_detail
from mlapp.views.outcome_dashboard import outcome_dashboard

urlpatterns = [
    path("predictions/", prediction_history_list, name="prediction_history_list"),
    path("predictions/<str:pred_date>/", prediction_history_detail, name="prediction_history_detail"),
    path("morning-predictions/", morning_prediction_dates, name="morning_prediction_dates"),
    path("morning-predictions/<str:pred_date>/", morning_prediction_detail, name="morning_prediction_detail"),
    path("backtests/", backtest_list, name="backtest_list"),
    path("backtests/<int:run_id>/", backtest_detail, name="backtest_detail"),
    path("backtests/run/", backtest_run_form, name="backtest_run_form"),
    path("optimizer/", optimizer_list, name="optimizer_list"),
    path("optimizer/<int:opt_id>/", optimizer_detail, name="optimizer_detail"),
    path("predictions/today/", today_predictions, name="today_predictions"),
    path("outcomes/dashboard/", outcome_dashboard, name="outcome_dashboard"),
]
