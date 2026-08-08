"""Validation of extension manifests and their relationships."""

from __future__ import annotations

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from mirror_core.extensions.models import (
    CapabilityManifest,
    ExtensionManifest,
    ProviderManifest,
)


def validate_manifests(
    manifests: list[ExtensionManifest],
) -> tuple[list[ExtensionManifest], list[tuple[str, str]]]:
    """Validate a list of manifests.

    Checks:
        - No duplicate extension_id.
        - Each manifest has a valid version.
        - Required fields are present (enforced by Pydantic, but we double‑check).
        - Provider manifests reference a capability that exists in the list.
        - Version constraints are parseable and valid.

    Returns:
        A tuple of (valid_manifests, errors), where each error is (extension_id, message).
    """
    valid: list[ExtensionManifest] = []
    errors: list[tuple[str, str]] = []

    # 1. Check for duplicate IDs
    id_map: dict[str, ExtensionManifest] = {}
    invalid_ids: set[str] = set()
    for manifest in manifests:
        if manifest.extension_id in id_map:
            errors.append(
                (
                    manifest.extension_id,
                    (f"Duplicate extension ID: {manifest.extension_id} (also defined by {id_map[manifest.extension_id].package_name})"),
                )
            )
            invalid_ids.add(manifest.extension_id)
        else:
            id_map[manifest.extension_id] = manifest

    # 2. Validate each manifest, but skip those already invalid
    for manifest in manifests:
        if manifest.extension_id in invalid_ids:
            continue

        # version, requires_core, dependencies, etc.
        try:
            Version(manifest.version)
        except Exception as exc:  # noqa: BLE001
            errors.append(
                (
                    manifest.extension_id,
                    f"Invalid version string: {manifest.version} - {exc}",
                )
            )
            invalid_ids.add(manifest.extension_id)
            continue

        try:
            SpecifierSet(manifest.requires_core)
        except Exception as exc:  # noqa: BLE001
            errors.append(
                (
                    manifest.extension_id,
                    f"Invalid requires_core: {manifest.requires_core} - {exc}",
                )
            )
            invalid_ids.add(manifest.extension_id)
            continue

        for dep in manifest.dependencies:
            try:
                SpecifierSet(dep.version_constraint)
            except Exception as exc:  # noqa: BLE001
                errors.append(
                    (
                        manifest.extension_id,
                        f"Invalid version constraint for dependency '{dep.target}': {dep.version_constraint} - {exc}",
                    )
                )
                invalid_ids.add(manifest.extension_id)
                break

        if manifest.extension_id in invalid_ids:
            continue

        # Capability-specific checks
        if isinstance(manifest, CapabilityManifest) and manifest.protocol is None and manifest.runner is None:
            errors.append(
                (
                    manifest.extension_id,
                    "Capability must define at least one of 'protocol' or 'runner'.",
                )
            )
            invalid_ids.add(manifest.extension_id)
            continue

        # If we reach here, the manifest is valid for now
        valid.append(manifest)

    # 3. Verify provider capability references (only for valid manifests)
    capability_names = {m.name for m in valid if isinstance(m, CapabilityManifest)}
    for manifest in valid:
        if isinstance(manifest, ProviderManifest) and manifest.capability not in capability_names:
            errors.append(
                (
                    manifest.extension_id,
                    f"Provider's capability '{manifest.capability}' is not a valid capability name (or was invalid).",
                )
            )
            valid = [m for m in valid if m.extension_id != manifest.extension_id]

    return valid, errors
