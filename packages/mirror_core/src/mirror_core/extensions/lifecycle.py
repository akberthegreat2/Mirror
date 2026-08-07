"""Extension lifecycle coordination for manifest-driven extensions.

Mirror Core owns the extension lifecycle contract. This module keeps the
runtime phases explicit so discovery, validation, configuration, activation,
deactivation, and unload semantics remain centralized in Core.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
from typing import Any

from mirror_core.exceptions import LifecycleError
from mirror_core.extensions.discovery import discover_extensions
from mirror_core.extensions.models import ExtensionManifest
from mirror_core.extensions.registry import ExtensionRegistryManager
from mirror_core.extensions.validation import validate_manifests


class ExtensionLifecycleState(str, Enum):
    """Lifecycle phases for an extension manifest."""

    DISCOVERED = "discovered"
    VALIDATED = "validated"
    CONFIGURED = "configured"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    UNLOADED = "unloaded"


@dataclass(frozen=True, slots=True)
class ExtensionLifecycleRecord:
    """Immutable snapshot of an extension's lifecycle state."""

    manifest: ExtensionManifest
    state: ExtensionLifecycleState
    configuration: Mapping[str, Any]

    @property
    def extension_id(self) -> str:
        """Return the manifest identifier used as the lifecycle key."""
        return self.manifest.extension_id

    def __post_init__(self) -> None:
        """Freeze the configuration snapshot."""
        object.__setattr__(
            self,
            "configuration",
            MappingProxyType(dict(self.configuration)),
        )


class ExtensionLifecycleManager:
    """Own the explicit lifecycle for manifest-based extensions.

    The manager is intentionally small: it tracks lifecycle state, delegates
    manifest validation to the existing extension validators, and delegates
    manifest storage to the extension registry manager.
    """

    _STATE_ORDER = {
        ExtensionLifecycleState.DISCOVERED: 0,
        ExtensionLifecycleState.VALIDATED: 1,
        ExtensionLifecycleState.CONFIGURED: 2,
        ExtensionLifecycleState.ACTIVATED: 3,
        ExtensionLifecycleState.DEACTIVATED: 4,
        ExtensionLifecycleState.UNLOADED: 5,
    }

    def __init__(self, registry: ExtensionRegistryManager | None = None) -> None:
        self._registry = registry or ExtensionRegistryManager()
        self._records: dict[str, ExtensionLifecycleRecord] = {}

    @property
    def registry(self) -> ExtensionRegistryManager:
        """Return the registry owned by this lifecycle manager."""
        return self._registry

    @property
    def records(self) -> tuple[ExtensionLifecycleRecord, ...]:
        """Return lifecycle records ordered by extension id for diagnostics."""
        return tuple(self._records[key] for key in sorted(self._records))

    def discover(
        self, groups: list[str] | None = None
    ) -> tuple[list[ExtensionManifest], list[tuple[str, str]]]:
        """Discover extension manifests and record them as discovered."""
        manifests, errors = discover_extensions(groups=groups)
        for manifest in manifests:
            self._set_state(manifest, ExtensionLifecycleState.DISCOVERED)
        return manifests, errors

    def validate(
        self, manifests: list[ExtensionManifest]
    ) -> tuple[list[ExtensionManifest], list[tuple[str, str]]]:
        """Validate manifests and record valid ones as validated."""
        valid, errors = validate_manifests(manifests)
        for manifest in valid:
            self._set_state(manifest, ExtensionLifecycleState.VALIDATED)
        return valid, errors

    def configure(
        self,
        manifests: list[ExtensionManifest],
        configuration: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Record extension configuration without changing ownership boundaries."""
        configuration = configuration or {}
        for manifest in manifests:
            self._ensure_transition_allowed(
                manifest, ExtensionLifecycleState.CONFIGURED
            )
            record = self._get_or_create_record(manifest)
            self._records[manifest.extension_id] = replace(
                record,
                state=ExtensionLifecycleState.CONFIGURED,
                configuration=MappingProxyType(
                    dict(configuration.get(manifest.extension_id, {}))
                ),
            )

    def activate(self, manifests: list[ExtensionManifest]) -> None:
        """Activate manifests and register them with Core's extension registry."""
        for manifest in manifests:
            record = self._get_or_create_record(manifest)
            if record.state == ExtensionLifecycleState.ACTIVATED:
                continue
            self._ensure_transition_allowed(manifest, ExtensionLifecycleState.ACTIVATED)
            self._registry.register(manifest)
            self._records[manifest.extension_id] = replace(
                record,
                state=ExtensionLifecycleState.ACTIVATED,
            )

    def deactivate(self, manifests: list[ExtensionManifest]) -> None:
        """Mark activated manifests as deactivated."""
        for manifest in manifests:
            self._ensure_transition_allowed(
                manifest, ExtensionLifecycleState.DEACTIVATED
            )
            record = self._get_or_create_record(manifest)
            self._records[manifest.extension_id] = replace(
                record,
                state=ExtensionLifecycleState.DEACTIVATED,
            )

    def unload(self, manifests: list[ExtensionManifest]) -> None:
        """Mark deactivated manifests as unloaded."""
        for manifest in manifests:
            self._ensure_transition_allowed(manifest, ExtensionLifecycleState.UNLOADED)
            record = self._get_or_create_record(manifest)
            self._records[manifest.extension_id] = replace(
                record,
                state=ExtensionLifecycleState.UNLOADED,
            )

    def get_record(self, extension_id: str) -> ExtensionLifecycleRecord:
        """Return the lifecycle record for one extension id."""
        try:
            return self._records[extension_id]
        except KeyError as exc:
            raise LifecycleError(
                f"Extension lifecycle record not found: {extension_id}"
            ) from exc

    def _set_state(
        self,
        manifest: ExtensionManifest,
        state: ExtensionLifecycleState,
    ) -> None:
        record = self._get_or_create_record(manifest)
        current_order = self._STATE_ORDER[record.state]
        next_order = self._STATE_ORDER[state]
        if next_order < current_order:
            raise LifecycleError(
                f"Invalid lifecycle transition for {manifest.extension_id!r}: "
                f"{record.state.value} -> {state.value}"
            )
        if next_order == current_order:
            return
        self._records[manifest.extension_id] = replace(record, state=state)

    def _ensure_transition_allowed(
        self,
        manifest: ExtensionManifest,
        next_state: ExtensionLifecycleState,
    ) -> None:
        record = self._records.get(manifest.extension_id)
        if record is None:
            if next_state != ExtensionLifecycleState.DISCOVERED:
                raise LifecycleError(
                    f"Extension {manifest.extension_id!r} must be discovered before "
                    f"it can transition to {next_state.value}"
                )
            return
        current_order = self._STATE_ORDER[record.state]
        next_order = self._STATE_ORDER[next_state]
        if next_order < current_order:
            raise LifecycleError(
                f"Invalid lifecycle transition for {manifest.extension_id!r}: "
                f"{record.state.value} -> {next_state.value}"
            )
        if record.state == next_state:
            return
        if next_state == ExtensionLifecycleState.CONFIGURED:
            if record.state not in {
                ExtensionLifecycleState.DISCOVERED,
                ExtensionLifecycleState.VALIDATED,
            }:
                raise LifecycleError(
                    f"Extension {manifest.extension_id!r} cannot be configured "
                    f"from {record.state.value}"
                )
        elif next_state == ExtensionLifecycleState.ACTIVATED:
            if record.state != ExtensionLifecycleState.CONFIGURED:
                raise LifecycleError(
                    f"Extension {manifest.extension_id!r} cannot be activated "
                    f"from {record.state.value}"
                )
        elif next_state == ExtensionLifecycleState.DEACTIVATED:
            if record.state != ExtensionLifecycleState.ACTIVATED:
                raise LifecycleError(
                    f"Extension {manifest.extension_id!r} cannot be deactivated "
                    f"from {record.state.value}"
                )
        elif next_state == ExtensionLifecycleState.UNLOADED:
            if record.state != ExtensionLifecycleState.DEACTIVATED:
                raise LifecycleError(
                    f"Extension {manifest.extension_id!r} cannot be unloaded "
                    f"from {record.state.value}"
                )

    def _get_or_create_record(
        self, manifest: ExtensionManifest
    ) -> ExtensionLifecycleRecord:
        record = self._records.get(manifest.extension_id)
        if record is None:
            record = ExtensionLifecycleRecord(
                manifest=manifest,
                state=ExtensionLifecycleState.DISCOVERED,
                configuration={},
            )
            self._records[manifest.extension_id] = record
        elif record.manifest.model_dump(mode="python") != manifest.model_dump(
            mode="python"
        ):
            raise LifecycleError(
                f"Conflicting manifest for extension {manifest.extension_id!r}"
            )
        return record
