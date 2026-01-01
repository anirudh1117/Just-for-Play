from django.shortcuts import render, get_object_or_404
from datetime import date
from mlapp.models.prediction_history import PredictionHistory


def prediction_history_list(request):
    """
    Shows list of unique dates for which predictions exist.
    """
    dates = (
        PredictionHistory.objects
        .values_list("date", flat=True)
        .distinct()
        .order_by("-date")
    )

    context = {"dates": dates}
    return render(request, "prediction_history_list.html", context)


def prediction_history_detail(request, pred_date):
    """
    Shows all predictions for a given date.
    """
    preds = PredictionHistory.objects.filter(date=pred_date).order_by("-confidence")

    context = {
        "pred_date": pred_date,
        "predictions": preds,
    }
    return render(request, "prediction_history_detail.html", context)

from django.shortcuts import render
from mlapp.models.final_pick_history import FinalPickHistory


def morning_prediction_dates(request):
    """
    List all dates for which final morning predictions exist.
    """
    dates = (
        FinalPickHistory.objects
        .values_list("date", flat=True)
        .distinct()
        .order_by("-date")
    )

    return render(request, "morning_prediction_dates.html", {"dates": dates})


def morning_prediction_detail(request, pred_date):
    """
    Show final 3 morning picks for a given date.
    """
    picks = FinalPickHistory.objects.filter(date=pred_date).order_by("-confidence")

    context = {
        "pred_date": pred_date,
        "picks": picks,
    }
    return render(request, "morning_prediction_detail.html", context)

