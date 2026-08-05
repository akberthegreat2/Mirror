"""Built-in middleware for Mirror framework."""

from mirror_middleware.base import MiddlewareFactory
from mirror_middleware.logging import LoggingMiddleware
from mirror_middleware.ratelimit import RateLimitMiddleware
from mirror_middleware.retry import RetryMiddleware
from mirror_middleware.timeout import TimeoutMiddleware
from mirror_middleware.tracing import TracingMiddleware

__all__ = [
    "RetryMiddleware",
    "TimeoutMiddleware",
    "RateLimitMiddleware",
    "LoggingMiddleware",
    "TracingMiddleware",
    "MiddlewareFactory",
]

# Expose middleware configs for discovery
# Each middleware module exports a `middleware_config` variable
