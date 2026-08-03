"""Rate limiting middleware using token bucket algorithm."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any

from mirror_core.middleware import Invocation, NextMiddleware


class RateLimitMiddleware:
    """Rate limit invocations using a token bucket algorithm.

    Settings:
        rate (float): Number of requests per second. Default: 10.0.
        burst (int): Maximum burst size. Default: 20.
        per_key (str | None): Key to use for rate limiting (e.g., "url", "domain").
            If None, global rate limit applies. Default: None.
    """

    def __init__(
        self,
        rate: float = 10.0,
        burst: int = 20,
        per_key: str | None = None,
    ) -> None:
        self.rate = rate
        self.burst = burst
        self.per_key = per_key
        self._buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (time.monotonic(), burst)
        )
        self._lock = asyncio.Lock()

    async def __call__(self, invocation: Invocation, next_middleware: NextMiddleware) -> Any:
        """Execute with rate limiting."""
        # Determine key
        key = str(invocation.get(self.per_key, "default")) if self.per_key is not None else "global"

        # Acquire token
        async with self._lock:
            last_checked, tokens = self._buckets[key]
            now = time.monotonic()
            elapsed = now - last_checked
            tokens = min(self.burst, tokens + elapsed * self.rate)
            if tokens < 1:
                # Wait until we have at least one token
                wait_time = (1 - tokens) / self.rate
                self._buckets[key] = (now, tokens)  # update with current time
                await asyncio.sleep(wait_time)
                # After sleep, we have one token; continue
                tokens = 1
                last_checked = time.monotonic()
            else:
                tokens -= 1
                last_checked = now
            self._buckets[key] = (last_checked, tokens)

        return await next_middleware(invocation)


def middleware_config() -> dict[str, Any]:
    """Return middleware descriptor for discovery."""
    return {
        "name": "ratelimit",
        "factory": "mirror_middleware.ratelimit:RateLimitMiddleware",
        "settings_model": None,
        "applies_to": None,
        "ordering_constraints": {"after": ["retry", "timeout"]},
        "metadata": {
            "description": "Rate limit invocations using token bucket algorithm",
        },
    }
