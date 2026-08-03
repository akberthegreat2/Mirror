"""Middleware chain for capability invocation.

Middleware wraps capability invocation and may alter control flow,
request, result, or exception.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

Invocation = dict[str, Any]  # typed dict with request, context, metadata
NextMiddleware = Callable[[Invocation], Awaitable[Any]]


class Middleware(Protocol):
    """Middleware protocol.

    A middleware wraps capability invocation. It receives the invocation
    and a next() callable to continue the chain.
    """

    async def __call__(self, invocation: Invocation, next: NextMiddleware) -> Any:
        """Process the invocation.

        Args:
            invocation: Contains request, context, metadata.
            next: Call the next middleware in the chain.

        Returns:
            The result of the capability invocation.
        """
        ...


class MiddlewareChain:
    """Immutable chain of middleware around a capability invocation."""

    def __init__(self, middlewares: list[Middleware]) -> None:
        self._middlewares = middlewares

    async def execute(self, invocation: Invocation, final: NextMiddleware) -> Any:
        """Execute the middleware chain.

        Args:
            invocation: The invocation context.
            final: The final capability function to call after all middleware.

        Returns:
            The result of the capability invocation.
        """
        chain = self._build_chain(final)
        return await chain(invocation)

    def _build_chain(self, final: NextMiddleware) -> NextMiddleware:
        """Build the chain from innermost to outermost."""
        chain = final
        for middleware in reversed(self._middlewares):
            current = middleware
            next_chain = chain

            # Bind current and next_chain at definition time
            async def wrapper(
                invocation: Invocation,
                m: Middleware = current,
                n: NextMiddleware = next_chain,
            ) -> Any:
                return await m(invocation, n)

            chain = wrapper
        return chain
