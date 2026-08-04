"""Shared foundations for capability-owned provider contract suites."""

from __future__ import annotations

from typing import Any

import pytest


class BaseContract:
    """Base marker for reusable provider contract suites.

    Capability packages own concrete test methods because only the capability
    knows its request, result, and error contracts. Provider packages subclass
    those suites and explicitly set ``__test__ = True``. This base deliberately
    contains no placeholder tests: an unimplemented contract must fail during
    collection or implementation rather than appear as a skipped success.
    """

    __test__ = False
    provider_class: type[Any] | None = None

    @pytest.fixture
    def provider(self) -> Any:
        """Create the configured provider under test."""

        if self.provider_class is None:
            raise RuntimeError("provider_class must be set by the provider contract")
        return self.provider_class()
