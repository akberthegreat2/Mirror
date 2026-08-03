"""Application composition root with transactional lifecycle.

Application owns discovery, registry, settings, signals, middleware,
and execution engine. Startup is transactional: if any component fails,
all previously initialized components are shut down in reverse order.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from mirror_core.discovery import discover, DiscoveryResult, DiscoverySource
from mirror_core.exceptions import ApplicationError, LifecycleError
from mirror_core.executor import Executor
from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.middleware import MiddlewareChain
from mirror_core.registry import Registry
from mirror_core.settings import MirrorSettings
from mirror_core.signals import SignalBus
from mirror_core.resource import ResourceEnvelope

logger = logging.getLogger(__name__)


class Application:
    """Composition root for Mirror.

    Owns discovery, registry, settings, signals, middleware,
    and execution engine.

    Startup is transactional: if any component fails to initialize,
    all previously initialized components are torn down in reverse order.
    """

    def __init__(
        self,
        settings: Optional[MirrorSettings] = None,
        discovery_source: Optional[DiscoverySource] = None,
    ) -> None:
        self.settings = settings or MirrorSettings()
        self._discovery_source = discovery_source
        self._discovery_result: Optional[DiscoveryResult] = None
        self._registry = Registry()
        self._signal_bus = SignalBus()
        self._executor: Optional[Executor] = None
        self._components: dict[str, Any] = {}  # name → component instance
        self._initialized: list[str] = []  # order of initialization
        self._started = False
        self._shutdown_complete = False

    async def start(self) -> None:
        """Start the application transactionally.

        Discovers extensions, resolves configured providers, and initializes them.
        If any component fails, all previously initialized components are torn down.
        """
        if self._started:
            return

        try:
            # 1. Discover extensions
            self._discovery_result = discover(source=self._discovery_source)
            if self._discovery_result.has_errors():
                raise ApplicationError(
                    f"Discovery errors: {self._discovery_result.errors}"
                )

            # 2. Register descriptors
            self._register_descriptors()

            # 3. Resolve and initialize components
            await self._initialize_components()

            # 4. Initialize executor
            self._executor = Executor(
                max_concurrency=10,  # TODO: from settings
                signal_bus=self._signal_bus,
            )

            await self._emit("application.started")
            self._started = True

        except Exception as e:
            await self._rollback_startup(e)
            raise

    def _register_descriptors(self) -> None:
        """Register all discovered descriptors."""
        if not self._discovery_result:
            raise ApplicationError("Discovery result is empty")

        for cap in self._discovery_result.capabilities:
            self._registry.register_capability(cap)

        for prov in self._discovery_result.providers:
            self._registry.register_provider(prov)

        for mw in self._discovery_result.middleware:
            self._registry.register_middleware(mw)

        for iface in self._discovery_result.interfaces:
            self._registry.register_interface(iface)

    async def _initialize_components(self) -> None:
        """Initialize all components from settings."""
        for cap_name, config in self.settings.components.items():
            provider_name = config.get("provider")
            if not provider_name:
                raise ApplicationError(f"No provider selected for {cap_name}")

            # Get provider descriptor
            provider_config = self._registry.get_provider(cap_name, provider_name)

            # Import factory
            import importlib
            module_path, _, class_name = provider_config.factory.rpartition(":")
            module = importlib.import_module(module_path)
            factory = getattr(module, class_name)

            # Instantiate with settings
            settings_cls = provider_config.settings_model
            if isinstance(settings_cls, str):
                # Import settings model
                mod_path, _, cls_name = settings_cls.rpartition(":")
                mod = importlib.import_module(mod_path)
                settings_cls = getattr(mod, cls_name)

            provider_settings = settings_cls.model_validate(
                self.settings.component_settings.get(cap_name, {}).get(provider_name, {})
            )

            instance = factory(provider_settings)

            # Initialize lifecycle
            if isinstance(instance, AsyncLifecycle):
                await instance.setup()

            self._components[cap_name] = instance
            self._initialized.append(cap_name)
            logger.info(f"Initialized component: {cap_name} (provider: {provider_name})")

    async def _rollback_startup(self, original_exception: Exception) -> None:
        """Rollback initialized components in reverse order."""
        if not self._initialized:
            return

        logger.warning(f"Rolling back startup after failure: {original_exception}")

        for cap_name in reversed(self._initialized):
            instance = self._components.get(cap_name)
            if instance and isinstance(instance, AsyncLifecycle):
                try:
                    await instance.teardown()
                except Exception as e:
                    logger.error(f"Error during rollback teardown of {cap_name}: {e}")
            self._components.pop(cap_name, None)

        self._initialized.clear()

    async def shutdown(self) -> None:
        """Shut down the application gracefully.

        Shutdown reverses initialization order. Idempotent.
        """
        if self._shutdown_complete:
            return

        await self._emit("application.shutting_down")

        # Shutdown executor
        if self._executor:
            self._executor.cancel()

        # Reverse order teardown
        for cap_name in reversed(self._initialized):
            instance = self._components.get(cap_name)
            if instance and isinstance(instance, AsyncLifecycle):
                try:
                    await instance.teardown()
                except Exception as e:
                    logger.error(f"Error during teardown of {cap_name}: {e}")
            self._components.pop(cap_name, None)

        self._initialized.clear()
        self._started = False
        self._shutdown_complete = True

        await self._emit("application.shutdown")
        logger.info("Application shutdown complete")

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        """Emit a signal if bus is available."""
        await self._signal_bus.emit(signal, **kwargs)

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def signal_bus(self) -> SignalBus:
        return self._signal_bus

    @property
    def executor(self) -> Optional[Executor]:
        return self._executor

    @property
    def started(self) -> bool:
        return self._started