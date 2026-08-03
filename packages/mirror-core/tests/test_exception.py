"""Tests for exception hierarchy."""

from mirror_core.exceptions import (
    ConfigurationError,
    DescriptorError,
    DiscoveryError,
    LifecycleError,
    MirrorError,
    PipelineError,
    ResourceError,
)


def test_exception_chaining():
    inner = ValueError("inner")
    outer = MirrorError("outer", cause=inner)
    assert outer.cause is inner
    assert outer.__cause__ is inner


def test_exception_metadata():
    err = MirrorError("test", metadata={"key": "value"})
    assert err.metadata["key"] == "value"


def test_specific_exceptions():
    # Ensure all subclasses exist and can be instantiated
    assert ConfigurationError("config")
    assert DiscoveryError("discovery")
    assert DescriptorError("descriptor")
    assert LifecycleError("lifecycle")
    assert PipelineError("pipeline")
    assert ResourceError("resource")
