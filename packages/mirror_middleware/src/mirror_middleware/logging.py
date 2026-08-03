"""Logging middleware for structured logging of invocations."""

from __future__ import annotations

import logging
import time
from typing import Any

from mirror_core.middleware import Invocation, NextMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Log invocation details before and after execution.

    Settings:
        level (str): Log level for messages (debug, info, warning, error). Default: "debug".
        log_args (bool): Whether to log invocation arguments. Default: False.
        log_result (bool): Whether to log result (truncated). Default: False.
    """

    def __init__(
        self,
        level: str = "debug",
        log_args: bool = False,
        log_result: bool = False,
    ) -> None:
        self.level = getattr(logging, level.upper(), logging.DEBUG)
        self.log_args = log_args
        self.log_result = log_result

    async def __call__(self, invocation: Invocation, next_middleware: NextMiddleware) -> Any:
        """Execute with logging."""
        start = time.monotonic()
        step_id = invocation.get("step", {}).get("id", "unknown")
        capability = invocation.get("step", {}).get("capability", "unknown")

        # Log start
        logger.log(
            self.level,
            f"Invoking capability '{capability}' step '{step_id}'",
            extra={
                "step_id": step_id,
                "capability": capability,
                "invocation_args": invocation.get("inputs") if self.log_args else None,
            },
        )

        try:
            result = await next_middleware(invocation)
            duration = time.monotonic() - start

            # Log success
            logger.log(
                self.level,
                f"Capability '{capability}' step '{step_id}' succeeded in {duration:.3f}s",
                extra={
                    "step_id": step_id,
                    "capability": capability,
                    "duration": duration,
                    "result": result if self.log_result else None,
                },
            )
            return result

        except Exception as e:
            duration = time.monotonic() - start
            logger.error(
                f"Capability '{capability}' step '{step_id}' failed after {duration:.3f}s: {e}",
                extra={
                    "step_id": step_id,
                    "capability": capability,
                    "duration": duration,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


def middleware_config() -> dict[str, Any]:
    """Return middleware descriptor for discovery."""
    return {
        "name": "logging",
        "factory": "mirror_middleware.logging:LoggingMiddleware",
        "settings_model": None,
        "applies_to": None,
        "ordering_constraints": {"after": ["retry", "timeout", "ratelimit"]},
        "metadata": {
            "description": "Structured logging of capability invocations",
        },
    }
