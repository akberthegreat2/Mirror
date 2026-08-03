"""Base middleware factory and utilities."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from mirror_core.middleware import Middleware

T = TypeVar("T")


class MiddlewareFactory(Protocol):
    """Protocol for middleware factories."""

    def __call__(self, **settings: Any) -> Middleware:
        """Create a middleware instance with given settings."""
        ...


def make_middleware(
    factory: MiddlewareFactory,
    settings: dict[str, Any] | None = None,
) -> Middleware:
    """Instantiate a middleware from a factory with settings."""
    settings = settings or {}
    return factory(**settings)
