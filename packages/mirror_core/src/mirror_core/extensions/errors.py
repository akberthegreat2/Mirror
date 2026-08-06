"""Custom exceptions for the extension system."""

from mirror_core.exceptions import MirrorError


class ExtensionError(MirrorError):
    """Base class for extension‑related errors."""


class DiscoveryError(ExtensionError):
    """Error during discovery of entry points."""


class ValidationError(ExtensionError):
    """Invalid extension manifest or graph."""


class RegistryError(ExtensionError):
    """Error during registry registration or lookup."""
