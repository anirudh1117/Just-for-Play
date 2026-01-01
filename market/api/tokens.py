import os
from django.conf import settings


def get_upstox_headers():
    """
    Returns headers required for Upstox V2 Open API calls.
    Uses ACCESS_TOKEN from .env
    """
    access_token = os.environ.get("UPSTOX_ACCESS_TOKEN")

    if not access_token:
        raise Exception(
            "UPSTOX_ACCESS_TOKEN missing. Set it in your .env file."
        )

    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def get_api_base_url():
    """
    Upstox official BASE URL for OPEN API REST.
    """
    return "https://api.upstox.com/v2"
