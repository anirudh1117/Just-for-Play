import csv
import os
from datetime import date, timedelta
import time

from django.conf import settings

from market.models import Instrument
from market.constants import EXCHANGE_NSE, INSTRUMENT_EQ
from jobs.utils import append_job_log


# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
MIN_CMP = 50.0
MAX_CMP = 200.0
MIN_VOLUME = 10_000
DEFAULT_LIMIT = 500

ASSETS_DIR = os.path.join(settings.BASE_DIR, "assets")


# -------------------------------------------------------------------
# Load CSV helpers
# -------------------------------------------------------------------
def _load_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _paths(trade_date: date):
    ddmmyyyy = trade_date.strftime("%d%m%Y")
    return (
        os.path.join(ASSETS_DIR, f"pr{ddmmyyyy}.csv"),  # prices
        os.path.join(ASSETS_DIR, f"pd{ddmmyyyy}.csv"),  # series
    )


# -------------------------------------------------------------------
# PUBLIC API
# -------------------------------------------------------------------
def get_bhavcopy_filtered_universe(
    trade_date: date | None = None,
    limit: int = DEFAULT_LIMIT,
    job_id=None,
):
    """
    Correct NSE-compliant universe selector.

    Data sources:
    - pr*.csv → price & volume
    - pd*.csv → SYMBOL → SERIES

    Equity definition:
    - SERIES == 'EQ'
    """

    if trade_date is None:
        trade_date = date.today() - timedelta(days=1)

    pr_path, pd_path = _paths(trade_date)

    append_job_log(job_id, f"Loading PR bhavcopy: {os.path.basename(pr_path)}")
    pr_rows = _load_csv(pr_path)

    append_job_log(job_id, f"Loading PD bhavcopy: {os.path.basename(pd_path)}")
    pd_rows = _load_csv(pd_path)

    append_job_log(job_id, f"PR rows: {len(pr_rows)} | PD rows: {len(pd_rows)}")

    # ----------------------------------------------------------------
    # Build SYMBOL → SERIES map from PD file
    # ----------------------------------------------------------------
    symbol_series = {}
    security_series = {}

    for r in pd_rows:
        sym = r.get("SYMBOL", "").strip()
        sec = r.get("SECURITY", "").strip()
        series = r.get("SERIES", "").strip()
        if sym and series:
            symbol_series[sym] = series
            security_series[sec] = sym
    append_job_log(
        job_id,
        f"Total SYMBOLs in PD file: {len(symbol_series)}")
    # ----------------------------------------------------------------
    # Filter using PR + PD (authoritative)
    # ----------------------------------------------------------------
    eligible_symbols = set()

    for r in pr_rows:
        try:
            symbol = r.get("SECURITY", "").strip()
            #append_job_log(job_id, f"Before eligible EQ symbol: {symbol}, {symbol_series.get(symbol)}")
            #time.sleep(2)  # To avoid log flooding
            if not symbol:
                continue

            # Equity check via PD file
            sec = security_series.get(symbol)
            if symbol_series.get(sec) != "EQ":
                continue

            close_price = float(r["CLOSE_PRICE"])
            volume = int(float(r["NET_TRDQTY"]))

            #append_job_log(job_id, f"Before Price Check: {symbol}, Close Price: {close_price}, Volume: {volume}")

            if not (MIN_CMP <= close_price <= MAX_CMP):
                continue

            if volume < MIN_VOLUME:
                continue
            #time.sleep(1)
            #append_job_log(job_id, f"Eligible EQ symbol: {symbol}")

            eligible_symbols.add(sec)

        except Exception:
            continue

    append_job_log(
        job_id,
        f"Eligible EQ symbols after filters: {len(eligible_symbols)}"
    )

    if not eligible_symbols:
        append_job_log(job_id, "No eligible equities found from bhavcopy")
        return []

    # ----------------------------------------------------------------
    # Map SYMBOL → Upstox Instrument
    # ----------------------------------------------------------------
    qs = Instrument.objects.filter(
        exchange=EXCHANGE_NSE,
        instrument_type=INSTRUMENT_EQ,
        symbol__in=eligible_symbols,
    ).only("id", "symbol", "instrument_key")

    instruments = list(qs.order_by("symbol")[:limit])



    append_job_log(
        job_id,
        f"Final bhavcopy universe size (EQ only): {len(instruments)}"
    )

    return instruments
