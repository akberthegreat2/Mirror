"""Provider component construction, validation, lookup, and lifecycle ownership."""

from __future__ import annotations

import importlib
from contextlib import AsyncExitStack
from typing import Any

from pydantic import BaseModel

from mirror_core.exceptions import ApplicationError
from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.registry import Registry
from mirror_core.settings import MirrorSettings


class EmptySettings(BaseModel):
    """Settings model used when a provider declares no configuration."""


class ComponentManager:
    """Own provider instances selected for one Application runtime."""

    def __init__(self, registry: Registry, settings: MirrorSettings) -> None:
        self._registry = registry
        self._settings = settings
        self._instances: dict[tuple[str, str], Any] = {}

    @property
    def instances(self) -> dict[tuple[str, str], Any]:
        """Return the mutable runtime mapping consumed by the executor."""
        return self._instances

    async def initialize(self, stack: AsyncExitStack) -> None:
        """Construct and start all configured providers transactionally."""
        for capability_name, selection in self._settings.components.items():
            provider_name = selection.get("provider")
            if not isinstance(provider_name, str) or not provider_name:
                raise ApplicationError(f"No provider selected for {capability_name!r}")
            capability = self._registry.resolve_capability(capability_name)
            provider = self._registry.resolve_provider(capability, provider_name)
            factory = self.import_symbol(provider.factory)
            settings_model = self.resolve_settings_model(provider.settings_model)
            raw_settings = self._settings.component_settings.get(capability_name, {}).get(
                provider_name, {}
            )
            instance = factory(settings_model.model_validate(raw_settings))
            if capability.protocol is not None and not isinstance(instance, capability.protocol):
                raise ApplicationError(
                    f"Provider {provider.name!r} does not implement capability "
                    f"protocol {capability.name!r}"
                )
            if isinstance(instance, AsyncLifecycle):
                stack.push_async_callback(instance.teardown)
                await instance.setup()
            self._instances[(capability_name, provider_name)] = instance

    def get(self, capability: str, provider: str) -> Any:
        """Return one initialized provider instance."""
        try:
            return self._instances[(capability, provider)]
        except KeyError as exc:
            raise ApplicationError(
                f"Provider {provider!r} is not initialized for capability {capability!r}"
            ) from exc

    def clear(self) -> None:
        """Forget instances after their lifecycle stack has been closed."""
        self._instances.clear()

    @staticmethod
    def import_symbol(path: str) -> Any:
        """Import a descriptor symbol from a ``module:symbol`` path."""
        module_name, separator, symbol_name = path.rpartition(":")
        if not separator:
            raise ApplicationError(f"Invalid import path: {path!r}")
        try:
            return getattr(importlib.import_module(module_name), symbol_name)
        except (ImportError, AttributeError) as exc:
            raise ApplicationError(f"Unable to import {path!r}", cause=exc) from exc

    @classmethod
    def resolve_settings_model(
        cls, value: type[BaseModel] | str | None
    ) -> type[BaseModel]:
        """Resolve and validate an optional Pydantic settings model."""
        if value is None:
            return EmptySettings
        resolved = cls.import_symbol(value) if isinstance(value, str) else value
        if not isinstance(resolved, type) or not issubclass(resolved, BaseModel):
            raise ApplicationError("Component settings model must be a Pydantic model")
        return resolved
