import time
import threading
from collections import deque
from datetime import datetime, timedelta


# ---------------------------------------------------------
# Rate Limit Constants (can adjust later)
# ---------------------------------------------------------
MAX_REQUESTS_PER_MINUTE = 80       # safe limit (Upstox allows more, but leave buffer)
BACKOFF_BASE_SECONDS = 1           # exponential backoff: 1 → 2 → 4 → 8
MAX_BACKOFF_SECONDS = 32           # cap backoff


# ---------------------------------------------------------
# Thread-safe rate limiter using sliding window
# ---------------------------------------------------------
class RateLimiter:
    """
    Thread-safe sliding window rate limiter.
    Tracks timestamps of requests in last 60 seconds.
    """

    def __init__(self, max_requests=MAX_REQUESTS_PER_MINUTE):
        self.max_requests = max_requests
        self.lock = threading.Lock()
        self.timestamps = deque()   # stores timestamps of recent requests

    def acquire(self):
        """
        Blocks until a request can be made without violating rate limits.
        """
        while True:
            with self.lock:
                now = datetime.utcnow()
                window_start = now - timedelta(seconds=60)

                # Remove timestamps older than 60s
                while self.timestamps and self.timestamps[0] < window_start:
                    self.timestamps.popleft()

                if len(self.timestamps) < self.max_requests:
                    # Safe to proceed
                    self.timestamps.append(now)
                    return

            # If rate limit reached, sleep a little before retrying
            time.sleep(0.2)


rate_limiter = RateLimiter()
