import asyncio
from dataclasses import dataclass


@dataclass
class UsageSnapshot:
    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class UsageLedger:
    """In-memory usage ledger. Swap this for Redis or a database in a real deployment."""

    def __init__(self) -> None:
        self._rows: dict[str, UsageSnapshot] = {}
        self._lock = asyncio.Lock()

    async def record(self, username: str, prompt_tokens: int, completion_tokens: int) -> None:
        async with self._lock:
            row = self._rows.setdefault(username, UsageSnapshot())
            row.requests += 1
            row.prompt_tokens += prompt_tokens
            row.completion_tokens += completion_tokens

    async def snapshot(self, username: str) -> UsageSnapshot:
        async with self._lock:
            row = self._rows.get(username, UsageSnapshot())
            return UsageSnapshot(
                requests=row.requests,
                prompt_tokens=row.prompt_tokens,
                completion_tokens=row.completion_tokens,
            )
