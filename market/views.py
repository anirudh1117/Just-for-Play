import os
import httpx
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone

from market.models import HistoricalBackfillState, UpstoxToken
from market.api.tokens import get_api_base_url


from datetime import timedelta
from django.utils import timezone
import pytz

def get_upstox_expiry():
    ist = pytz.timezone("Asia/Kolkata")

    now = timezone.now()

    # Force awareness if naive
    if timezone.is_naive(now):
        now = ist.localize(now)

    now_ist = now.astimezone(ist)

    expiry_ist = now_ist.replace(
        hour=3,
        minute=30,
        second=0,
        microsecond=0
    )

    if now_ist >= expiry_ist:
        expiry_ist += timedelta(days=1)

    return expiry_ist



# ---------------------------------------------------------
# Redirect user to Upstox login page
# ---------------------------------------------------------
def upstox_login(request):
    client_id = os.getenv("UPSTOX_CLIENT_ID")
    redirect_uri = os.getenv("UPSTOX_REDIRECT_URI")

    if not client_id or not redirect_uri:
        return HttpResponse("Missing UPSTOX_CLIENT_ID or REDIRECT_URI", status=500)

    auth_url = (
        f"{get_api_base_url()}/login/authorization/dialog"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
    )

    return redirect(auth_url)


# ---------------------------------------------------------
# OAuth callback handler
# ---------------------------------------------------------
def upstox_callback(request):
    code = request.GET.get("code")

    if not code:
        return HttpResponse("Authorization failed: missing code", status=400)

    token_url = f"{get_api_base_url()}/login/authorization/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": os.getenv("UPSTOX_CLIENT_ID"),
        "client_secret": os.getenv("UPSTOX_CLIENT_SECRET"),
        "redirect_uri": os.getenv("UPSTOX_REDIRECT_URI"),
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = httpx.post(token_url, data=payload, headers=headers)

    if resp.status_code != 200:
        return HttpResponse(f"Token exchange failed: {resp.text}", status=400)

    data = resp.json()

    expires_at = get_upstox_expiry()

    UpstoxToken.objects.update_or_create(
        id=1,
        defaults={
            "access_token": data["access_token"],
            "refresh_token": "",
            "expires_at": expires_at,
        },
    )

    return redirect("/jobs/dashboard/")

def backfill_progress_api(request):
    states = HistoricalBackfillState.objects.all()
    data = []

    for s in states:
        data.append({
            "symbol": s.instrument.symbol,
            "interval": s.interval,
            "completed": s.completed_days,
            "total": s.total_days,
            "percent": int((s.completed_days / s.total_days) * 100) if s.total_days else 0,
            "last_error": s.last_error,
        })

    return JsonResponse({"progress": data})

