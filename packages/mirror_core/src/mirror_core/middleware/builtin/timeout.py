"""Timeout middleware for enforcing timeouts on invocations."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, ConfigDict

from mirror_core.extensions.models import MiddlewareManifest
from mirror_core.middleware.contracts import NextMiddleware
from mirror_core.middleware.invocation import MiddlewareInvocation


class TimeoutSettings(BaseModel):
    """Validated settings for timeout middleware."""

    model_config = ConfigDict(frozen=True)

    timeout: float = 30.0


class TimeoutMiddleware:
    """Enforce a timeout on capability invocation."""

    def __init__(self, settings: TimeoutSettings | None = None, /, **overrides: Any) -> None:
        if settings is None:
            settings = TimeoutSettings.model_validate(overrides)
        elif overrides:
            settings = settings.model_copy(update=overrides)
        self.settings = settings

    async def __call__(self, invocation: MiddlewareInvocation, next_middleware: NextMiddleware) -> Any:
        try:
            return await asyncio.wait_for(next_middleware(invocation), timeout=self.settings.timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Invocation timed out after {self.settings.timeout} seconds") from None


middleware = MiddlewareManifest(
    name="timeout",
    factory="mirror_core.middleware.builtin.timeout:TimeoutMiddleware",
    settings_model=TimeoutSettings,
    applies_to=None,
    after=["retry"],
    before=["ratelimit"],
    metadata={
        "description": "Enforce a timeout on capability invocations",
    },
)


def middleware_config() -> MiddlewareManifest:
    return middleware
