from django.utils import timezone
from datetime import time, datetime, timedelta

from jobs.utils import append_job_log


# ---------------------------------------------------------
# Helper: fixed Upstox expiry (3:30 AM IST)
# ---------------------------------------------------------
def compute_upstox_expiry():
    now = timezone.now()
    today = now.date()

    expiry_time = time(3, 30)
    expiry_dt = datetime.combine(today, expiry_time).replace(
        tzinfo=timezone.get_current_timezone()
    )

    if now >= expiry_dt:
        expiry_dt += timedelta(days=1)

    return expiry_dt


# ---------------------------------------------------------
# Get latest stored token
# ---------------------------------------------------------
def get_token():
    from market.models import UpstoxToken
    return UpstoxToken.objects.order_by("-updated_at").first()


# ---------------------------------------------------------
# Save token (called ONLY from OAuth callback)
# ---------------------------------------------------------
def save_token(access_token):
    from market.models import UpstoxToken

    expires_at = compute_upstox_expiry()

    token, _ = UpstoxToken.objects.update_or_create(
        id=1,   # enforce singleton
        defaults={
            "access_token": access_token,
            "expires_at": expires_at,
            "updated_at": timezone.now(),
        },
    )

    return token


# ---------------------------------------------------------
# Get valid access token
# ---------------------------------------------------------
def get_valid_access_token(log_job_id=None):
    token = get_token()

    if not token:
        raise Exception("Upstox not connected. Please login first.")

    if token.is_expired():
        msg = "Upstox access token expired. Please login again."
        append_job_log(log_job_id, msg)
        raise Exception(msg)

    return token.access_token
