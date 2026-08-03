"""Signal bus for decoupled observability.

Signals are for announcing facts and should not control business execution.
Telemetry receiver failure must not silently fail a pipeline unless configured as critical.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Callable, Coroutine, TypeVar

from mirror_core.exceptions import MirrorError

logger = logging.getLogger(__name__)

T = TypeVar("T")
SignalHandler = Callable[..., Coroutine[Any, Any, None] | None]


class SignalBus:
    """Event bus with named signals and async/sync receiver support."""

    def __init__(self) -> None:
        self._receivers: dict[str, list[SignalHandler]] = {}
        self._signal_errors: dict[str, list[Exception]] = {}

    def subscribe(self, signal_name: str, handler: SignalHandler) -> None:
        """Subscribe a handler to a signal."""
        if signal_name not in self._receivers:
            self._receivers[signal_name] = []
        self._receivers[signal_name].append(handler)

    def unsubscribe(self, signal_name: str, handler: SignalHandler) -> None:
        """Unsubscribe a handler from a signal."""
        if signal_name in self._receivers:
            try:
                self._receivers[signal_name].remove(handler)
            except ValueError:
                pass

    async def emit(self, signal_name: str, *args: Any, **kwargs: Any) -> None:
        """Emit a signal, calling all subscribed handlers.

        Args:
            signal_name: Name of the signal (e.g., "pipeline.started").
            *args, **kwargs: Arguments passed to handlers.

        Raises:
            None. Handler exceptions are logged but not propagated unless
            the handler explicitly raises MirrorError with critical=True.
        """
        if signal_name not in self._receivers:
            return

        handlers = self._receivers[signal_name][:]

        for handler in handlers:
            try:
                result = handler(*args, **kwargs)
                if inspect.isawaitable(result):
                    await result
            except MirrorError as e:
                if e.details.get("critical", False):
                    raise
                logger.error(
                    f"Signal handler failed (non-critical): {signal_name}",
                    extra={"handler": handler.__name__, "error": str(e)},
                )
            except Exception as e:
                logger.error(
                    f"Signal handler raised unexpected exception: {signal_name}",
                    extra={"handler": handler.__name__, "error": str(e)},
                    exc_info=True,
                )

    def clear(self) -> None:
        """Clear all signal subscriptions."""
        self._receivers.clear()
        self._signal_errors.clear()