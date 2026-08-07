"""Rate limiting middleware using token bucket algorithm."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict

from mirror_core.extensions.models import MiddlewareManifest
from mirror_core.middleware.contracts import NextMiddleware
from mirror_core.middleware.invocation import MiddlewareInvocation


class RateLimitSettings(BaseModel):
    """Validated settings for rate limiting middleware."""

    model_config = ConfigDict(frozen=True)

    rate: float = 10.0
    burst: int = 20
    per_key: str | None = None


class RateLimitMiddleware:
    """Rate limit invocations using a token bucket algorithm."""

    def __init__(
        self, settings: RateLimitSettings | None = None, /, **overrides: Any
    ) -> None:
        if settings is None:
            settings = RateLimitSettings.model_validate(overrides)
        elif overrides:
            settings = settings.model_copy(update=overrides)
        self.settings = settings
        self._buckets: dict[str, tuple[float, float]] = defaultdict(
            lambda: (time.monotonic(), self.settings.burst)
        )
        self._lock = asyncio.Lock()

    async def __call__(
        self, invocation: MiddlewareInvocation, next_middleware: NextMiddleware
    ) -> Any:
        key = self._resolve_key(invocation)
        while True:
            async with self._lock:
                last_checked, tokens = self._buckets[key]
                now = time.monotonic()
                elapsed = now - last_checked
                tokens = min(self.settings.burst, tokens + elapsed * self.settings.rate)
                if tokens >= 1:
                    self._buckets[key] = (now, tokens - 1)
                    break
                wait_time = (1 - tokens) / self.settings.rate
                self._buckets[key] = (now, tokens)
            await asyncio.sleep(wait_time)

        return await next_middleware(invocation)

    def _resolve_key(self, invocation: MiddlewareInvocation) -> str:
        if self.settings.per_key is None:
            return "global"
        if self.settings.per_key in invocation.context:
            return str(invocation.context[self.settings.per_key])
        value = getattr(invocation.request, self.settings.per_key, None)
        if value is not None:
            return str(value)
        step_value = getattr(invocation.step, self.settings.per_key, None)
        if step_value is not None:
            return str(step_value)
        return "default"


middleware = MiddlewareManifest(
    name="ratelimit",
    factory="mirror_core.middleware.builtin.ratelimit:RateLimitMiddleware",
    settings_model=RateLimitSettings,
    applies_to=None,
    after=["retry", "timeout"],
    metadata={
        "description": "Rate limit invocations using token bucket algorithm",
    },
)


def middleware_config() -> MiddlewareManifest:
    return middleware
