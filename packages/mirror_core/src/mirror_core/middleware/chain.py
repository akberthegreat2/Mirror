"""Middleware chain execution."""

from __future__ import annotations

from typing import Any

from mirror_core.middleware.contracts import Middleware, NextMiddleware
from mirror_core.middleware.invocation import MiddlewareInvocation


class MiddlewareChain:
    """Immutable chain of middleware around a capability invocation."""

    def __init__(self, middlewares: list[Middleware]) -> None:
        self._middlewares = tuple(middlewares)

    async def execute(
        self,
        invocation: MiddlewareInvocation,
        final: NextMiddleware,
    ) -> Any:
        """Execute the middleware chain."""
        chain = self._build_chain(final)
        return await chain(invocation)

    def _build_chain(self, final: NextMiddleware) -> NextMiddleware:
        chain = final
        for middleware in reversed(self._middlewares):
            current = middleware
            next_chain = chain

            async def wrapper(
                invocation: MiddlewareInvocation,
                m: Middleware = current,
                n: NextMiddleware = next_chain,
            ) -> Any:
                return await m(invocation, n)

            chain = wrapper
        return chain
