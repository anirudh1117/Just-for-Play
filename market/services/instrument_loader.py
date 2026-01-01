import csv
import gzip
import io
import requests

from jobs.utils import append_job_log
from market.models import Instrument
from market.constants import EXCHANGE_NSE, INSTRUMENT_EQ, INSTRUMENT_INDEX


# ---------------------------------------------------------
# Upstox Instrument Master URLs
# ---------------------------------------------------------

NSE_EQ_URL = (
    "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"
)

NSE_INDEX_URL = (
    "https://assets.upstox.com/market-quote/instruments/exchange/NSE_INDEX.csv.gz"
)


# ---------------------------------------------------------
# Download & parse CSV.GZ
# ---------------------------------------------------------

def _load_csv_from_gz(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=60)

    resp.raise_for_status()

    content = resp.content

    if url.endswith(".gz"):
        with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
            text = gz.read().decode("utf-8")
    else:
        text = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# ---------------------------------------------------------
# Save instruments
# ---------------------------------------------------------

def _save_instruments(rows, instrument_type, job_id):
    count = 0

    for row in rows:
        try:
            Instrument.objects.update_or_create(
                instrument_key=row["instrument_key"],
                defaults={
                    "symbol": row["tradingsymbol"],
                    "name": row.get("name") or row.get("tradingsymbol"),
                    "exchange": EXCHANGE_NSE,
                    "instrument_type": instrument_type,
                    "tick_size": float(row.get("tick_size", 0.05)),
                    "lot_size": int(row.get("lot_size") or 1),
                },
            )
            count += 1
        except Exception as e:
            append_job_log(
                job_id,
                f"Failed saving {row.get('tradingsymbol')}: {e}",
            )

    return count


# ---------------------------------------------------------
# MAIN ENTRY POINT (Job Runner)
# ---------------------------------------------------------

def run(job_id=None):
    append_job_log(job_id, "Starting Upstox instrument sync")

    # -----------------------------
    # Load NSE EQ
    # -----------------------------
    append_job_log(job_id, "Downloading NSE_EQ instrument master")
    eq_rows = _load_csv_from_gz(NSE_EQ_URL)

    eq_count = _save_instruments(
        eq_rows,
        instrument_type=INSTRUMENT_EQ,
        job_id=job_id,
    )

    append_job_log(job_id, f"Saved {eq_count} NSE equity instruments")

    # -----------------------------
    # Load NSE INDEX
    # -----------------------------
    append_job_log(job_id, "Downloading NSE_INDEX instrument master")
    index_rows = _load_csv_from_gz(NSE_INDEX_URL)

    index_count = _save_instruments(
        index_rows,
        instrument_type=INSTRUMENT_INDEX,
        job_id=job_id,
    )

    append_job_log(job_id, f"Saved {index_count} NSE index instruments")

    total = eq_count + index_count
    append_job_log(job_id, f"Instrument sync completed. Total: {total}")

    return f"Instrument sync completed. Total instruments: {total}"
