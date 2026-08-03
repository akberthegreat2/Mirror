"""AsyncLifecycle protocol for optional component lifecycle management.

The AsyncLifecycle protocol is separate from capability contracts.
A component may implement it to receive setup() and teardown() calls,
or omit it entirely. Both are valid.

This separation follows the Interface Segregation Principle:
capability protocols describe *what* a component does, and
AsyncLifecycle describes *how it is managed*.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class AsyncLifecycle(Protocol):
    """Optional lifecycle protocol for components.

    Implement this protocol if your component needs initialization
    (e.g., opening connections, creating directories) or cleanup
    (e.g., closing connections, flushing buffers).

    Components that do not implement AsyncLifecycle are still
    fully valid. Application simply skips lifecycle calls for them.

    Both methods must be idempotent. Calling setup() or teardown()
    multiple times must be safe.
    """

    async def setup(self) -> None:
        """Initialize the component.

        Called once during Application.start().
        Must be idempotent.
        """
        ...

    async def teardown(self) -> None:
        """Clean up the component.

        Called once during Application.shutdown() or during rollback
        if startup fails. Must be idempotent.

        Implementations should avoid raising exceptions that prevent
        other components from being torn down. Any exceptions should
        be logged but not re-raised.
        """
        ...
