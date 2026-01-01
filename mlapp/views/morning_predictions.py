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


from django.utils import timezone
from mlapp.models.morning_prediction import MorningPrediction


def today_predictions(request):
    today = timezone.now().date()
    preds = MorningPrediction.objects.filter(date=today)
    return render(request, "mlapp/today_predictions.html", {
        "predictions": preds,
        "date": today
    })

