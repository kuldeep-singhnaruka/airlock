import asyncio
import time
from collections import defaultdict


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> None:
        now = time.monotonic()
        async with self._lock:
            recent = [stamp for stamp in self._hits[key] if now - stamp < self.window_seconds]
            if len(recent) >= self.limit:
                self._hits[key] = recent
                raise RateLimitExceeded(self.window_seconds)
            recent.append(now)
            self._hits[key] = recent
