"""Retry middleware with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from mirror_core.middleware import Invocation, NextMiddleware
from mirror_core.registry import MiddlewareConfig


class RetryMiddleware:
    """Retry failed invocations with exponential backoff and jitter.

    Settings:
        max_attempts (int): Maximum number of attempts (including first). Default: 3.
        base_delay (float): Base delay in seconds. Default: 1.0.
        max_delay (float): Maximum delay in seconds. Default: 30.0.
        backoff_factor (float): Multiplier for exponential backoff. Default: 2.0.
        jitter (float): Random jitter factor (0.0 = no jitter, 1.0 = full jitter). Default: 0.1.
        retryable_exceptions (list[type]): Exception types that should trigger retry.
            If None, any exception is retried (except CancelledError). Default: None.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: float = 0.1,
        retryable_exceptions: list[type] | None = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    async def __call__(self, invocation: Invocation, next_middleware: NextMiddleware) -> Any:
        """Execute with retry logic."""
        last_exception: Exception | None = None
        attempt = 0

        while attempt < self.max_attempts:
            attempt += 1
            try:
                return await next_middleware(invocation)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_exception = exc
                if self.retryable_exceptions is not None and not any(
                    isinstance(exc, exc_type) for exc_type in self.retryable_exceptions
                ):
                    raise
                if attempt >= self.max_attempts:
                    raise
                delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
                delay = min(delay, self.max_delay)
                if self.jitter > 0:
                    jitter_amount = random.uniform(-self.jitter * delay, self.jitter * delay)
                    delay = max(0.0, delay + jitter_amount)
                await asyncio.sleep(delay)

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")


middleware = MiddlewareConfig(
    name="retry",
    factory="mirror_middleware.retry:RetryMiddleware",
    settings_model=None,
    applies_to=None,
    before=["timeout", "ratelimit"],
    metadata={
        "description": "Retry failed invocations with exponential backoff and jitter",
    },
)


def middleware_config() -> MiddlewareConfig:
    """Return the middleware descriptor for compatibility."""
    return middleware
