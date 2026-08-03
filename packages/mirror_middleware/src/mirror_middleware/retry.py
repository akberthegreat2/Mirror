"""Retry middleware with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import random
from typing import Any

from mirror_core.middleware import Invocation, NextMiddleware


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
        last_exception = None
        attempt = 0

        while attempt < self.max_attempts:
            attempt += 1
            try:
                return await next_middleware(invocation)
            except asyncio.CancelledError:
                # Do not retry cancellation
                raise
            except Exception as e:
                last_exception = e
                if self.retryable_exceptions is not None and not any(
                    isinstance(e, exc_type) for exc_type in self.retryable_exceptions
                ):
                    raise
                # Check if we should retry
                if attempt >= self.max_attempts:
                    raise
                # Calculate backoff
                delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
                delay = min(delay, self.max_delay)
                if self.jitter > 0:
                    # Add jitter: random value between -jitter*delay and +jitter*delay
                    jitter_amount = random.uniform(-self.jitter * delay, self.jitter * delay)
                    delay += jitter_amount
                    delay = max(0, delay)  # Ensure non-negative
                await asyncio.sleep(delay)

        # Should not reach here, but just in case
        if last_exception is not None:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")


def middleware_config() -> dict[str, Any]:
    """Return middleware descriptor for discovery."""
    return {
        "name": "retry",
        "factory": "mirror_middleware.retry:RetryMiddleware",
        "settings_model": None,  # No Pydantic model for now
        "applies_to": None,  # All capabilities by default
        "ordering_constraints": {"before": ["timeout", "ratelimit"]},
        "metadata": {
            "description": "Retry failed invocations with exponential backoff and jitter",
        },
    }
