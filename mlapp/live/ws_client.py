import asyncio
import json
import websockets
from datetime import datetime, timedelta
from jobs.utils import append_job_log


UPSTOX_WS_URL = "wss://api.upstox.com/v3/feed"   # official WS endpoint


class UpstoxWSClient:
    """
    Simple async WebSocket client to receive live ticks only for shortlisted symbols.
    """

    def __init__(self, access_token, symbols, candle_builder, job_id=None):
        self.access_token = access_token
        self.symbols = symbols
        self.cb = candle_builder
        self.job_id = job_id

    def log(self, msg):
        append_job_log(self.job_id, msg)

    async def subscribe(self, ws):
        """
        Subscribe to market feed for shortlisted symbols.
        """
        subs = [{"instrument_key": s, "feed_type": "full"} for s in self.symbols]

        msg = {
            "guid": "morning_stream_1",
            "method": "sub",
            "data": subs
        }

        await ws.send(json.dumps(msg))
        self.log(f"Subscribed to {len(subs)} symbols.")

    async def run(self, minutes=20):
        """
        Run the websocket for X minutes and build candles in memory.
        """
        self.log("Starting Upstox WebSocket...")

        async with websockets.connect(
            f"{UPSTOX_WS_URL}?access_token={self.access_token}"
        ) as ws:

            await self.subscribe(ws)

            end_time = datetime.now() + timedelta(minutes=minutes)

            while datetime.now() < end_time:
                msg = await ws.recv()
                data = json.loads(msg)

                # We only care about market ticks
                if "feeds" not in data:
                    continue

                for inst_key, feed in data["feeds"].items():
                    price = feed["ltp"]
                    volume = feed["volume"]
                    ts = datetime.fromtimestamp(feed["exchange_timestamp"])

                    self.cb.add_tick(inst_key, price, volume, ts)

        self.log("WebSocket streaming completed.")
