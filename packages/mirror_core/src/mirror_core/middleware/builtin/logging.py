"""Logging middleware for structured logging of invocations."""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel, ConfigDict

from mirror_core.extensions.models import MiddlewareManifest
from mirror_core.middleware.contracts import NextMiddleware
from mirror_core.middleware.invocation import MiddlewareInvocation

logger = logging.getLogger(__name__)


class LoggingSettings(BaseModel):
    """Validated settings for logging middleware."""

    model_config = ConfigDict(frozen=True)

    level: str = "debug"
    log_args: bool = False
    log_result: bool = False


class LoggingMiddleware:
    """Log invocation details before and after execution."""

    def __init__(self, settings: LoggingSettings | None = None, /, **overrides: Any) -> None:
        if settings is None:
            settings = LoggingSettings.model_validate(overrides)
        elif overrides:
            settings = settings.model_copy(update=overrides)
        self.settings = settings
        self.level = getattr(logging, self.settings.level.upper(), logging.DEBUG)

    async def __call__(self, invocation: MiddlewareInvocation, next_middleware: NextMiddleware) -> Any:
        start = time.monotonic()
        step_id = invocation.step.id
        capability = invocation.step.capability

        logger.log(
            self.level,
            f"Invoking capability '{capability}' step '{step_id}'",
            extra={
                "step_id": step_id,
                "capability": capability,
                "invocation_args": invocation.request.model_dump(mode="json") if self.settings.log_args else None,
            },
        )

        try:
            result = await next_middleware(invocation)
            duration = time.monotonic() - start
            logger.log(
                self.level,
                f"Capability '{capability}' step '{step_id}' succeeded in {duration:.3f}s",
                extra={
                    "step_id": step_id,
                    "capability": capability,
                    "duration": duration,
                    "result": result if self.settings.log_result else None,
                },
            )
            return result
        except Exception as exc:
            duration = time.monotonic() - start
            logger.exception(
                f"Capability '{capability}' step '{step_id}' failed after {duration:.3f}s",
                extra={
                    "step_id": step_id,
                    "capability": capability,
                    "duration": duration,
                    "error": str(exc),
                },
            )
            raise


middleware = MiddlewareManifest(
    name="logging",
    factory="mirror_core.middleware.builtin.logging:LoggingMiddleware",
    settings_model=LoggingSettings,
    applies_to=None,
    after=["retry", "timeout", "ratelimit"],
    metadata={
        "description": "Structured logging of capability invocations",
    },
)


def middleware_config() -> MiddlewareManifest:
    return middleware
