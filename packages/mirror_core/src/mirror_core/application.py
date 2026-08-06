"""Mirror application composition root and transactional lifecycle."""

from __future__ import annotations

import logging
import types
from contextlib import AsyncExitStack
from typing import Any, cast
from typing_extensions import Self  # <-- added

from mirror_core.components import ComponentManager
from mirror_core.discovery import DiscoveryResult, DiscoverySource, discover
from mirror_core.exceptions import ApplicationError
from mirror_core.executor import ExecutionResult, Executor
from mirror_core.lifecycle import AsyncLifecycle
from mirror_core.middleware import Middleware, MiddlewareChain
from mirror_core.pipeline import Pipeline
from mirror_core.planner import Planner
from mirror_core.registry import MiddlewareConfig, Registry
from mirror_core.resource import ResourceEnvelope
from mirror_core.settings import MirrorSettings
from mirror_core.signals import SignalBus

logger = logging.getLogger(__name__)


class Application:
    """Own and compose one isolated Mirror runtime."""

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
        self._component_manager = ComponentManager(self._registry, self.settings)
        self._lifecycle_stack: AsyncExitStack | None = None
        self._started = False

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
        """Discover, validate, instantiate, and start the application atomically."""
        if self._started:
            return
        self._reset_runtime_state()
        stack = AsyncExitStack()
        await stack.__aenter__()
        try:
            self._discovery_result = discover(source=self._discovery_source)
            if self._discovery_result.has_errors():
                raise ApplicationError(
                    "Extension discovery failed",
                    details={"errors": self._discovery_result.errors},
                )
            if self._discovery_result.has_duplicates():
                raise ApplicationError(
                    "Duplicate extension descriptors discovered",
                    details={"duplicates": self._discovery_result.duplicates},
                )
            self._register_descriptors()
            self._registry.freeze()
            middleware_chains = await self._build_middleware_chains(stack)
            await self._component_manager.initialize(stack)
            self._executor = Executor(
                components=self._component_manager.instances,
                max_concurrency=self.settings.max_concurrency,
                signal_bus=self._signal_bus,
                middleware_chains=middleware_chains,
            )
            self._lifecycle_stack = stack.pop_all()
            self._started = True
            await self._emit("application.started", application=self)
        except Exception:
            await stack.aclose()
            self._reset_runtime_state()
            raise

    async def run_pipeline(
        self,
        pipeline: Pipeline,
        *,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, ResourceEnvelope]:
        """Compile and execute a pipeline using explicit runtime inputs."""
        result = await self.run_pipeline_detailed(pipeline, inputs=inputs)
        return result.results

    async def run_pipeline_detailed(
        self,
        pipeline: Pipeline,
        *,
        inputs: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Compile and execute a pipeline and return its terminal run state."""
        if not self._started or self._executor is None:
            raise ApplicationError(
                "Application must be started before running pipelines"
            )
        defaults = {
            capability: str(config["provider"])
            for capability, config in self.settings.components.items()
            if "provider" in config
        }
        plan = Planner(self._registry, default_providers=defaults).plan(pipeline)
        if self._lifecycle_stack is None:
            raise ApplicationError("Application lifecycle stack is unavailable")
        for compiled in plan.steps.values():
            await self._component_manager.ensure_provider(
                compiled.capability.name,
                compiled.provider.name,
                self._lifecycle_stack,
            )
        return await self._executor.execute_run(plan, inputs=inputs or {})

    async def shutdown(self) -> None:
        """Cancel active runs and release every owned resource once."""
        if not self._started and self._lifecycle_stack is None:
            return
        await self._emit("application.shutting_down", application=self)
        if self._executor is not None:
            self._executor.cancel()
        stack, self._lifecycle_stack = self._lifecycle_stack, None
        if stack is not None:
            await stack.aclose()
        self._started = False
        self._executor = None
        self._component_manager.clear()
        await self._emit("application.shutdown", application=self)

    def _register_descriptors(self) -> None:
        result = self._discovery_result
        if result is None:
            raise ApplicationError("Discovery result is unavailable")
        for capability in result.capabilities:
            self._registry.register_capability(capability)
        for provider in result.providers:
            self._registry.register_provider(provider)
        for middleware in result.middleware:
            self._registry.register_middleware(middleware)
        for interface in result.interfaces:
            self._registry.register_interface(interface)

    async def _build_middleware_chains(
        self, stack: AsyncExitStack
    ) -> dict[str, MiddlewareChain]:
        capability_names = list(self.settings.components)
        requested_names = set(self.settings.global_middleware)
        for capability in capability_names:
            requested_names.update(self.settings.middleware.get(capability, []))

        if not requested_names or not capability_names:
            return {}

        configs = {
            name: self._registry.get_middleware(name) for name in requested_names
        }
        instances: dict[str, Middleware] = {}
        for name in self._order_middleware(list(configs.values())):
            config = configs[name.name]
            factory = ComponentManager.import_symbol(config.factory)
            settings_model = ComponentManager.resolve_settings_model(
                config.settings_model
            )
            raw_settings = self.settings.middleware_settings.get(config.name, {})
            instance = factory(settings_model.model_validate(raw_settings))
            if isinstance(instance, AsyncLifecycle):
                stack.push_async_callback(instance.teardown)
                await instance.setup()
            instances[config.name] = cast(Middleware, instance)

        middleware_chains: dict[str, MiddlewareChain] = {}
        for capability in capability_names:
            names = list(
                dict.fromkeys(
                    self.settings.global_middleware
                    + self.settings.middleware.get(capability, [])
                )
            )
            ordered_configs = [configs[name] for name in names if name in configs]
            ordered = self._order_middleware(ordered_configs)
            chain_instances = []
            for config in ordered:
                if (
                    config.applies_to is not None
                    and capability not in config.applies_to
                ):
                    raise ApplicationError(
                        f"Middleware {config.name!r} does not apply to capability {capability!r}"
                    )
                chain_instances.append(instances[config.name])
            if chain_instances:
                middleware_chains[capability] = MiddlewareChain(chain_instances)
        return middleware_chains

    @staticmethod
    def _order_middleware(configs: list[MiddlewareConfig]) -> list[MiddlewareConfig]:
        """Topologically order middleware, using priority as a stable tie-breaker."""
        by_name = {config.name: config for config in configs}
        dependencies = {config.name: set() for config in configs}
        for config in configs:
            for target in config.after:
                if target in by_name:
                    dependencies[config.name].add(target)
            for target in config.before:
                if target in by_name:
                    dependencies[target].add(config.name)
        ordered: list[MiddlewareConfig] = []
        remaining = set(by_name)
        while remaining:
            ready = [
                name
                for name in remaining
                if not dependencies[name].intersection(remaining)
            ]
            if not ready:
                raise ApplicationError(
                    "Middleware ordering constraints contain a cycle"
                )
            ready.sort(key=lambda name: (-by_name[name].priority, name))
            for name in ready:
                ordered.append(by_name[name])
                remaining.remove(name)
        return ordered

    def _reset_runtime_state(self) -> None:
        self._registry = Registry()
        self._signal_bus = SignalBus()
        self._executor = None
        self._component_manager = ComponentManager(self._registry, self.settings)
        self._discovery_result = None
        self._started = False

    async def _emit(self, signal: str, **kwargs: Any) -> None:
        await self._signal_bus.emit(signal, **kwargs)

    @property
    def component_manager(self) -> ComponentManager:
        """Return the provider lifecycle owner for this runtime."""
        return self._component_manager

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
