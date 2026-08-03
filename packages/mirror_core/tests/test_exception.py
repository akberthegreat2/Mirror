"""Tests for core exceptions."""

from mirror_core.exceptions import (
    ConfigurationError,
    DiscoveryError,
    ExecutionError,
    LifecycleError,
    MirrorError,
    PlannerError,
    RegistryError,
    ValidationError,
)


def test_exception_hierarchy():
    """Test that all exceptions inherit from MirrorError."""
    exceptions = [
        ConfigurationError,
        LifecycleError,
        DiscoveryError,
        RegistryError,
        ValidationError,
        PlannerError,
        ExecutionError,
    ]
    for exc_cls in exceptions:
        assert issubclass(exc_cls, MirrorError)


def test_exception_chaining():
    """Test that exceptions can chain causes."""
    inner = ValueError("inner")
    outer = MirrorError("outer", cause=inner)
    assert outer.cause is inner
    assert outer.__cause__ is inner
