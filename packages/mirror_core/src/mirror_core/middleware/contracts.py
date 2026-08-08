"""Middleware contracts."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from mirror_core.middleware.invocation import MiddlewareInvocation

NextMiddleware = Callable[[MiddlewareInvocation], Awaitable[Any]]


class Middleware(Protocol):
    """Protocol for middleware components."""

    async def __call__(self, invocation: MiddlewareInvocation, next: NextMiddleware) -> Any: ...
