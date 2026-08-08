"""Retry middleware with exponential backoff and jitter."""

from __future__ import annotations

import asyncio
import builtins
import random
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from mirror_core.extensions.models import MiddlewareManifest
from mirror_core.middleware.contracts import Middleware, NextMiddleware
from mirror_core.middleware.invocation import MiddlewareInvocation


class RetrySettings(BaseModel):
    """Validated settings for retry middleware."""

    model_config = ConfigDict(frozen=True)

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.1
    retryable_exception_names: tuple[str, ...] = Field(default_factory=tuple)


class MiddlewareFactory(Protocol):
    def __call__(self, **settings: Any) -> Middleware: ...


class RetryMiddleware:
    """Retry failed invocations with exponential backoff and jitter."""

    def __init__(
        self,
        settings: RetrySettings | None = None,
        /,
        **overrides: Any,
    ) -> None:
        if settings is None:
            settings = RetrySettings.model_validate(overrides)
        elif overrides:
            settings = settings.model_copy(update=overrides)
        self.settings = settings
        self.retryable_exceptions = self._resolve_retryable_exceptions(
            self.settings.retryable_exception_names
        )

    async def __call__(
        self, invocation: MiddlewareInvocation, next_middleware: NextMiddleware
    ) -> Any:
        last_exception: Exception | None = None
        attempt = 0

        while attempt < self.settings.max_attempts:
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
                if attempt >= self.settings.max_attempts:
                    raise
                delay = self.settings.base_delay * (
                    self.settings.backoff_factor ** (attempt - 1)
                )
                delay = min(delay, self.settings.max_delay)
                if self.settings.jitter > 0:
                    jitter_amount = random.uniform(
                        -self.settings.jitter * delay, self.settings.jitter * delay
                    )
                    delay = max(0.0, delay + jitter_amount)
                await asyncio.sleep(delay)

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")

    @staticmethod
    def _resolve_retryable_exceptions(
        names: tuple[str, ...],
    ) -> tuple[type[BaseException], ...] | None:
        if not names:
            return None
        resolved: list[type[BaseException]] = []
        for name in names:
            candidate = getattr(builtins, name, None)
            if isinstance(candidate, type) and issubclass(candidate, BaseException):
                resolved.append(candidate)
        return tuple(resolved) if resolved else None


middleware = MiddlewareManifest(
    name="retry",
    factory="mirror_core.middleware.builtin.retry:RetryMiddleware",
    settings_model=RetrySettings,
    applies_to=None,
    before=["timeout", "ratelimit"],
    metadata={
        "description": "Retry failed invocations with exponential backoff and jitter",
    },
)


def middleware_config() -> MiddlewareManifest:
    return middleware
