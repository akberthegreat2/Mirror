"""Application composition root with transactional lifecycle."""

from __future__ import annotations

import importlib
import logging
import types
from typing import Any

from pydantic import BaseModel

from mirror_core.discovery import DiscoveryResult, DiscoverySource, discover
from mirror_core.exceptions import ApplicationError, ExecutionError
from mirror_core.executor import Executor
from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.middleware import MiddlewareChain
from mirror_core.pipeline import Pipeline, Step
from mirror_core.planner import Planner
from mirror_core.registry import Registry
from mirror_core.resource import ProducerRef, ResourceEnvelope
from mirror_core.settings import MirrorSettings
from mirror_core.signals import SignalBus

logger = logging.getLogger(__name__)


class EmptySettings(BaseModel):
    """Default empty settings model for providers that don't define one."""

    pass


class Application:
    """Composition root for Mirror.

    Supports both async context manager and explicit start/shutdown.
    Startup is transactional: if any component fails, all previously
    initialized components are shut down in reverse order.
    """

    def __init__(
        self,
        settings: MirrorSettings | None = None,
        discovery_source: DiscoverySource | None = None,
    ) -> None:
        self.settings = settings or MirrorSettings()
        self._discovery_source = discovery_source
        self._discovery_result: DiscoveryResult | None = None
        self._registry = Registry()
        self._signal_bus = SignalBus()
        self._executor: Executor | None = None
        self._components: dict[str, Any] = {}
        self._initialized: list[str] = []
        self._started = False
        self._shutdown_complete = False
        self._producer_ref: ProducerRef | None = None

    async def __aenter__(self) -> Application:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self.shutdown()

    async def start(self) -> None:
        """Start the application transactionally."""
        if self._started:
            return

        try:
            self._discovery_result = discover(source=self._discovery_source)
            if self._discovery_result.has_errors():
                raise ApplicationError(f"Discovery errors: {self._discovery_result.errors}")

            self._register_descriptors()

            # Build middleware chain from discovered middleware configs
            middleware_chain = self._build_middleware_chain()

            # Initialize components
            await self._initialize_components()

            # Set producer reference for executor
            self._producer_ref = ProducerRef(
                capability="application",
                capability_version="0.1.0",
                provider="core",
                provider_version="0.1.0",
                config_fingerprint=self.settings.model_dump_json(),
            )

            self._executor = Executor(
                registry=self._registry,
                components=self._components,
                max_concurrency=10,  # TODO: from settings
                signal_bus=self._signal_bus,
                middleware_chain=middleware_chain,
            )
            self._executor.set_producer(self._producer_ref)

            await self._emit("application.started")
            self._started = True

        except Exception as e:
            await self._rollback_startup(e)
            raise

    async def run_pipeline(self, pipeline: Pipeline) -> dict[str, ResourceEnvelope]:
        """Run a pipeline end-to-end.

        Args:
            pipeline: The pipeline definition to execute.

        Returns:
            dict[str, ResourceEnvelope]: Results for each step.
        """
        if not self._started:
            raise ApplicationError("Application must be started before running pipelines")
        if self._executor is None:
            raise ApplicationError("Executor not initialized")

        planner = Planner(self._registry)
        plan = planner.plan(pipeline)

        # Define a runner that routes to the correct capability runner
        # This is a placeholder; we need a registry of capability runners
        # or we can use the step's runner from the capability config
        async def step_runner(step: Step, inputs: dict[str, Any]) -> Any:
            # Look up the capability config
            cap_config = self._registry.get_capability(step.capability, "1.0")
            if cap_config.runner is None:
                raise ExecutionError(f"No runner defined for capability '{step.capability}'")
            # Import the runner function
            module_path, _, func_name = cap_config.runner.rpartition(":")
            module = importlib.import_module(module_path)
            runner_func = getattr(module, func_name)
            # The runner expects (provider, request, ...) – we need to construct request from inputs
            provider = self._components.get(step.capability)
            if provider is None:
                raise ExecutionError(f"No provider initialized for '{step.capability}'")
            # Build request from inputs using the request_model
            request_model = cap_config.request_model
            if request_model is None:
                raise ExecutionError(f"No request_model for '{step.capability}'")
            request = request_model.model_validate(inputs)
            return await runner_func(provider, request, signal_bus=self.signal_bus, step_id=step.id)

        return await self._executor.execute(plan, step_runner)

    async def shutdown(self) -> None:
        """Shut down the application gracefully."""
        if self._shutdown_complete:
            return

        await self._emit("application.shutting_down")

        if self._executor:
            self._executor.cancel()

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

    def _register_descriptors(self) -> None:
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

    def _build_middleware_chain(self) -> MiddlewareChain | None:
        """Build middleware chain from registry and settings."""
        # Get global middleware list
        global_middleware_names = self.settings.global_middleware
        if not global_middleware_names:
            return None

        middlewares = []
        for name in global_middleware_names:
            config = self._registry.get_middleware(name)
            # Import factory
            import importlib

            module_path, _, class_name = config.factory.rpartition(":")
            module = importlib.import_module(module_path)
            factory = getattr(module, class_name)
            # Instantiate with settings (if any)
            settings_cls = config.settings_model
            if settings_cls:
                if isinstance(settings_cls, str):
                    mod_path, _, cls_name = settings_cls.rpartition(":")
                    mod = importlib.import_module(mod_path)
                    settings_cls = getattr(mod, cls_name)
                # Get settings from component_settings or defaults
                # For now, use empty dict
                instance = factory()
            else:
                instance = factory()
            middlewares.append(instance)

        return MiddlewareChain(middlewares)

    async def _initialize_components(self) -> None:
        for cap_name, config in self.settings.components.items():
            provider_name = config.get("provider")
            if not provider_name:
                raise ApplicationError(f"No provider selected for {cap_name}")

            provider_config = self._registry.get_provider(cap_name, provider_name)

            # Import factory
            module_path, _, class_name = provider_config.factory.rpartition(":")
            module = importlib.import_module(module_path)
            factory = getattr(module, class_name)

            # Resolve settings model (with fallback)
            settings_cls = provider_config.settings_model

            if isinstance(settings_cls, str):
                # Import settings model from string path
                mod_path, _, cls_name = settings_cls.rpartition(":")
                mod = importlib.import_module(mod_path)
                settings_cls = getattr(mod, cls_name)

            # Ensure we have a concrete model class
            if settings_cls is None:
                settings_cls = EmptySettings
            elif not (isinstance(settings_cls, type) and issubclass(settings_cls, BaseModel)):
                # Fallback if something unexpected
                settings_cls = EmptySettings

            # Now settings_cls is guaranteed to be a subclass of BaseModel
            provider_settings = settings_cls.model_validate(
                self.settings.component_settings.get(cap_name, {}).get(provider_name, {})
            )

            instance = factory(provider_settings)

            if isinstance(instance, AsyncLifecycle):
                await instance.setup()

            self._components[cap_name] = instance
            self._initialized.append(cap_name)
            logger.info(f"Initialized component: {cap_name} (provider: {provider_name})")

    async def _rollback_startup(self, original_exception: Exception) -> None:
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

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        await self._signal_bus.emit(signal, **kwargs)

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def signal_bus(self) -> SignalBus:
        return self._signal_bus

    @property
    def executor(self) -> Executor | None:
        return self._executor

    @property
    def started(self) -> bool:
        return self._started
