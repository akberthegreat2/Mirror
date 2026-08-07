"""Custom exceptions for the extension system."""

from mirror_core.exceptions import (
    DiscoveryError as CoreDiscoveryError,
)
from mirror_core.exceptions import (
    MirrorError,
)
from mirror_core.exceptions import (
    RegistryError as CoreRegistryError,
)
from mirror_core.exceptions import (
    ValidationError as CoreValidationError,
)


class ExtensionError(MirrorError):
    """Base class for extension-related errors."""


class DiscoveryError(ExtensionError, CoreDiscoveryError):
    """Error during discovery of entry points."""


class ValidationError(ExtensionError, CoreValidationError):
    """Invalid extension manifest or graph."""


class RegistryError(ExtensionError, CoreRegistryError):
    """Error during registry registration or lookup."""
