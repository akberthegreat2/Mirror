"""Mirror middleware contracts and built-in implementations.

Middleware is part of the execution kernel. Core owns the contracts
and the built-in chain behavior, while third-party packages may still
provide compatible middleware implementations via entry points.
"""

from mirror_core.execution import CapabilityContext, ExecutionContext, ExecutionPolicy
from mirror_core.middleware.builtin import (
    LoggingMiddleware,
    LoggingSettings,
    MiddlewareFactory,
    RateLimitMiddleware,
    RateLimitSettings,
    RetryMiddleware,
    RetrySettings,
    TimeoutMiddleware,
    TimeoutSettings,
    TracingMiddleware,
    TracingSettings,
)
from mirror_core.middleware.chain import MiddlewareChain
from mirror_core.middleware.context import MiddlewareContext
from mirror_core.middleware.contracts import Middleware, NextMiddleware
from mirror_core.middleware.invocation import MiddlewareInvocation

__all__ = [
    "CapabilityContext",
    "ExecutionContext",
    "ExecutionPolicy",
    "LoggingMiddleware",
    "LoggingSettings",
    "Middleware",
    "MiddlewareChain",
    "MiddlewareContext",
    "MiddlewareFactory",
    "MiddlewareInvocation",
    "NextMiddleware",
    "RateLimitMiddleware",
    "RateLimitSettings",
    "RetryMiddleware",
    "RetrySettings",
    "TimeoutMiddleware",
    "TimeoutSettings",
    "TracingMiddleware",
    "TracingSettings",
]
