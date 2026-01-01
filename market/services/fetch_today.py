from datetime import datetime, date
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

from django.db import transaction

from market.models import Instrument, Candle
from market.api.upstox_client import UpstoxClient
from market.constants import EXCHANGE_NSE, INSTRUMENT_EQ, INSTRUMENT_INDEX, INTERVAL_1MIN
from jobs.utils import append_job_log
from market.services.universe_selector import get_phase1_universe



# ---------------------------------------------------------------------
# Utility: Select Universe of stocks
# Later you can add CMP filter, liquidity filter, sector filter etc.
# ---------------------------------------------------------------------

from django.db.models import Q

def get_universe():
    """
    Select EQ stocks with price between 50–200 (once we compute CMP).
    Temporarily: just load EQ + major index symbols.
    """
    eq_stocks = Instrument.objects.filter(
        instrument_type=INSTRUMENT_EQ,
        exchange=EXCHANGE_NSE
    )

    # Add indices for model context
    index_symbols = ["NIFTY 50", "BANKNIFTY", "FINNIFTY"]
    index_instruments = Instrument.objects.filter(
        name__in=index_symbols,
        instrument_type=INSTRUMENT_INDEX
    )

    return list(eq_stocks[:250]) + list(index_instruments)



# ---------------------------------------------------------------------
# Save candles for a single instrument
# ---------------------------------------------------------------------

def save_candles_for_symbol(inst, candles_data, job_id):
    """
    Saves candle list returned from Upstox into the DB.
    Each candle is stored atomically using transaction.
    """
    with transaction.atomic():
        for c in candles_data:
            try:
                raw_ts = parse_datetime(c[0])
                if raw_ts is None:
                    raise ValueError(f"Invalid timestamp: {c[0]}")

                ts_utc = raw_ts.astimezone(utc) if raw_ts.tzinfo else raw_ts.replace(tzinfo=utc)

                Candle.objects.update_or_create(
                    instrument=inst,
                    ts=ts_utc,
                    interval=INTERVAL_1MIN,
                    defaults={
                        "open": c[1],
                        "high": c[2],
                        "low": c[3],
                        "close": c[4],
                        "volume": c[5],
                    },
                )
            except Exception as e:
                append_job_log(job_id, f"Failed to save candle for {inst.symbol}: {e}")


# ---------------------------------------------------------------------
# MAIN ENTRY POINT CALLED BY JOB SYSTEM
# ---------------------------------------------------------------------

def run(job_id=None):
    """
    Fetch today's 1-minute candles for selected universe.
    This runs inside the Celery run_job() wrapper.
    """
    today = date.today()
    client = UpstoxClient(log_job_id=job_id)

    append_job_log(job_id, "Starting fetch_today pipeline...")
    append_job_log(job_id, f"Fetching 1-minute candles for {today}")

    instruments = get_phase1_universe(limit=250)
    append_job_log(job_id, f"Universe Size: {len(instruments)} instruments")

    count = 0
    last_processed_key = None 

    for inst in instruments:
        append_job_log(job_id, f"Fetching {inst.symbol} ...")
        last_processed_key = inst.instrument_key

        try:
            resp = client.fetch_historical_candles(
                instrument_key=inst.instrument_key,
                interval=INTERVAL_1MIN,
                from_date=date.today(),
                to_date=date.today(),
            )


            data = resp.get("data", {})
            candles = data.get("candles", [])
            if not candles:
                append_job_log(job_id, f"No candles for {inst.symbol}")
                continue

            save_candles_for_symbol(inst, candles, job_id)
            count += 1

        except Exception as e:
            append_job_log(job_id, f"Error fetching {inst.symbol}: {e}")
            continue

    append_job_log(job_id, f"Finished. Successfully saved data for {count} instruments.")
    append_job_log(job_id, f"Last processed symbol key: {last_processed_key}")
    return f"Saved candles for {count} instruments."
