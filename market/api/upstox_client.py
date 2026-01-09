import httpx
import time
from datetime import date

from jobs.utils import append_job_log
from market.api.token_manager import get_valid_access_token
from market.api.rate_limiter import (
    rate_limiter,
    BACKOFF_BASE_SECONDS,
    MAX_BACKOFF_SECONDS,
)


class UpstoxClient:
    """
    Upstox REST client aligned STRICTLY to Upstox API v3.

    Design principles (locked):
    - Fail-fast on auth (NO silent refresh)
    - Explicit rate limiting
    - Deterministic retries for transient failures only
    - Path-based v3 endpoints (no query-based v2 legacy)
    """

    BASE_URL = "https://api.upstox.com/v3"

    def __init__(self, log_job_id=None):
        self.log_job_id = log_job_id

    # ------------------------------------------------------------------
    # Headers (DB-backed token, fail-fast)
    # ------------------------------------------------------------------
    def _get_headers(self):
        token = get_valid_access_token(self.log_job_id)
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Core request wrapper with retry discipline
    # ------------------------------------------------------------------
    def _request_with_retry(self, method: str, path: str, *, params=None):
        backoff = BACKOFF_BASE_SECONDS

        while True:
            try:
                rate_limiter.acquire()

                url = f"{self.BASE_URL}{path}"
                headers = self._get_headers()

                with httpx.Client(timeout=20) as client:
                    if method == "GET":
                        resp = client.get(url, headers=headers, params=params)
                    else:
                        raise ValueError("Only GET supported for v3 market data")

                # ----------------------------
                # Success
                # ----------------------------
                if resp.status_code == 200:
                    return resp.json()

                # ----------------------------
                # Auth failure → FAIL FAST
                # ----------------------------
                if resp.status_code == 401:
                    msg = (
                        "Upstox auth failed (401). "
                        "Token expired or invalid. Manual re-login required."
                    )
                    append_job_log(self.log_job_id, msg)
                    raise RuntimeError(msg)

                # ----------------------------
                # Rate limiting (defensive)
                # ----------------------------
                if resp.status_code == 429:
                    append_job_log(
                        self.log_job_id,
                        f"429 rate limit hit. Sleeping {backoff}s",
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                    continue

                # ----------------------------
                # Transient server errors
                # ----------------------------
                if 500 <= resp.status_code < 600:
                    append_job_log(
                        self.log_job_id,
                        f"Upstox {resp.status_code} server error. Retrying in {backoff}s",
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                    continue

                # ----------------------------
                # Other client errors → FAIL
                # ----------------------------
                raise RuntimeError(
                    f"Upstox API error {resp.status_code}: {resp.text}"
                )

            except httpx.RequestError as e:
                append_job_log(self.log_job_id, f"Network error: {e}")
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)

    # ------------------------------------------------------------------
    # Public GET wrapper
    # ------------------------------------------------------------------
    def _get(self, path: str, *, params=None):
        append_job_log(self.log_job_id, f"Calling: {path} with params: {params}")
        return self._request_with_retry("GET", path, params=params)

    # ------------------------------------------------------------------
    # v3 Market Data APIs
    # ------------------------------------------------------------------
    def fetch_historical_candles(
        self,
        instrument_key: str,
        interval: str,
        from_date: date,
        to_date: date,
    ):
        """
        Fetch historical intraday candles from Upstox v3.

        Logical rules:
        - from_date <= to_date
        - (to_date - from_date).days <= 30

        Transport rule (Upstox):
        - URL order = {to_date}/{from_date}
        """

        # -------- validation (fail fast) --------
        if from_date > to_date:
            raise ValueError(
                f"Invalid date range: from_date {from_date} > to_date {to_date}"
            )

        if (to_date - from_date).days > 30:
            raise ValueError(
                f"Date window too large for Upstox v3: "
                f"{from_date} → {to_date}"
            )

        # -------- Upstox v3 URL (NOTE ORDER) --------
        path = (
            f"/historical-candle/"
            f"{instrument_key}/minutes/{interval}/"
            f"{to_date}/{from_date}"
        )

        return self._get(path)
    
    def fetch_today_candles(
        self,
        instrument_key: str,
        interval: str
    ):
        """
        Fetch Today's intraday candles from Upstox v3.

        Logical rules:
        - from_date <= to_date
        - (to_date - from_date).days <= 30

        Transport rule (Upstox):
        - URL order = {to_date}/{from_date}
        """
       
        path = (
            f"/historical-candle/intraday/"
            f"{instrument_key}/minutes/{interval}/"
        )

        return self._get(path)

    def fetch_ltp(self, instrument_key: str):
        """
        Fetch last traded price (v3).
        NOTE: Used only for verification / monitoring, not model features.
        """
        path = f"/market-quote/ltp/{instrument_key}"
        return self._get(path)
