from datetime import datetime, timedelta
from jobs.utils import append_job_log
from mlapp.models.prediction_history import PredictionHistory
from market.models import Instrument
from mlapp.live.ws_client import UpstoxWSClient
from mlapp.live.candle_builder import CandleBuilder


class MorningCollector:
    """
    Collects 10–20 minutes of live candles for shortlisted symbols.
    """

    def __init__(self, access_token, job_id=None):
        self.access_token = access_token
        self.job_id = job_id
        self.cb = CandleBuilder(max_candles=20)

    def log(self, msg):
        append_job_log(self.job_id, msg)

    def load_shortlist(self):
        """
        Get last evening's top 30 symbols from PredictionHistory.
        """
        latest_date = (
            PredictionHistory.objects
            .values_list("date", flat=True)
            .distinct()
            .order_by("-date")
            .first()
        )

        preds = PredictionHistory.objects.filter(date=latest_date).order_by("-confidence")

        symbols = []
        instrument_keys = []

        for p in preds:
            inst = p.instrument
            symbols.append(inst.symbol)
            instrument_keys.append(inst.instrument_key)

        self.log(f"Loaded shortlist of {len(symbols)} symbols.")
        return instrument_keys

    async def collect(self, minutes=20):
        """
        Main entry: Connect WebSocket and collect live ticks.
        """
        instrument_keys = self.load_shortlist()

        ws = UpstoxWSClient(
            access_token=self.access_token,
            symbols=instrument_keys,
            candle_builder=self.cb,
            job_id=self.job_id,
        )

        await ws.run(minutes=minutes)

        self.log("Returning collected candles.")
        return self.cb.candles
