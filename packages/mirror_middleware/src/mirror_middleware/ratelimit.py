"""Rate limiting middleware using token bucket algorithm."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any

from mirror_core.middleware import Invocation, NextMiddleware
from mirror_core.registry import MiddlewareConfig


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
        key = self._resolve_key(invocation)
        while True:
            async with self._lock:
                last_checked, tokens = self._buckets[key]
                now = time.monotonic()
                elapsed = now - last_checked
                tokens = min(self.burst, tokens + elapsed * self.rate)
                if tokens >= 1:
                    self._buckets[key] = (now, tokens - 1)
                    break
                wait_time = (1 - tokens) / self.rate
                self._buckets[key] = (now, tokens)
            await asyncio.sleep(wait_time)

        return await next_middleware(invocation)

    def _resolve_key(self, invocation: Invocation) -> str:
        if self.per_key is None:
            return "global"
        if self.per_key in invocation.context:
            return str(invocation.context[self.per_key])
        value = getattr(invocation.request, self.per_key, None)
        if value is not None:
            return str(value)
        step_value = getattr(invocation.step, self.per_key, None)
        if step_value is not None:
            return str(step_value)
        return "default"


middleware = MiddlewareConfig(
    name="ratelimit",
    factory="mirror_middleware.ratelimit:RateLimitMiddleware",
    settings_model=None,
    applies_to=None,
    after=["retry", "timeout"],
    metadata={
        "description": "Rate limit invocations using token bucket algorithm",
    },
)


def middleware_config() -> MiddlewareConfig:
    """Return the middleware descriptor for compatibility."""
    return middleware
