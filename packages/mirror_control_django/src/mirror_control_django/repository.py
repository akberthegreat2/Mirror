"""Repository helpers for the Mirror control plane."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.db.models import Max
from mirror_core.pipeline import Pipeline as CorePipeline
from mirror_core.storage import FileSystemBlobStore

from mirror_control_django import models
from mirror_control_django.manifest import CONTROL_PLANE_MANIFEST

DEFAULT_BLOB_ENV = "MIRROR_CONTROL_BLOB_ROOT"
DEFAULT_BLOB_DIR = ".mirror/control-plane/blobs"
MANAGED_PIPELINE_ORIGIN = "managed"


@dataclass(frozen=True, slots=True)
class PipelineArtifact:
    """Metadata for one materialized pipeline version."""

    project_slug: str
    pipeline_slug: str
    version: int
    definition_ref: str
    definition_hash: str
    origin: str
    read_only: bool


def default_blob_root() -> Path:
    """Return the configured blob store root for control-plane documents."""

    value = os.environ.get(DEFAULT_BLOB_ENV)
    return Path(value) if value else Path(DEFAULT_BLOB_DIR)


def default_blob_store() -> FileSystemBlobStore:
    """Build the default filesystem blob store."""

    return FileSystemBlobStore(default_blob_root())


def serialize_pipeline_definition(pipeline: CorePipeline) -> bytes:
    """Serialize a core pipeline into canonical JSON bytes."""

    payload = pipeline.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, indent=2).encode("utf-8")


def deserialize_pipeline_definition(raw: bytes) -> CorePipeline:
    """Deserialize canonical JSON bytes back into a core pipeline."""

    return CorePipeline.model_validate_json(raw)


def content_hash(payload: bytes) -> str:
    """Return a stable digest for a pipeline definition blob."""

    return hashlib.sha256(payload).hexdigest()


class ControlPlaneRepository:
    """High-level repository for pipeline documents and control-plane objects."""

    def __init__(self, blob_store: FileSystemBlobStore | None = None) -> None:
        self.blob_store = blob_store or default_blob_store()

    def ensure_project(
        self,
        *,
        slug: str,
        name: str | None = None,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> models.Project:
        project, _ = models.Project.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name or slug.replace("-", " ").title(),
                "description": description,
                "metadata": metadata or {},
            },
        )
        if name is not None and project.name != name:
            project.name = name
        if description and project.description != description:
            project.description = description
        if metadata is not None:
            project.metadata = metadata
        project.save()
        return project

    def get_or_create_pipeline(
        self,
        *,
        project_slug: str,
        pipeline_slug: str,
        name: str | None = None,
        origin: str = MANAGED_PIPELINE_ORIGIN,
        read_only: bool = False,
        source_ref: str = "",
        source_hash_value: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> models.Pipeline:
        project = self.ensure_project(slug=project_slug)
        pipeline, created = models.Pipeline.objects.get_or_create(
            project=project,
            slug=pipeline_slug,
            defaults={
                "name": name or pipeline_slug.replace("-", " ").title(),
                "origin": origin,
                "is_read_only": read_only,
                "source_ref": source_ref,
                "source_hash": source_hash_value,
                "metadata": metadata or {},
            },
        )
        if not created:
            if name is not None:
                pipeline.name = name
            pipeline.origin = origin
            pipeline.is_read_only = read_only
            pipeline.source_ref = source_ref
            pipeline.source_hash = source_hash_value
            if metadata is not None:
                pipeline.metadata = metadata
            pipeline.save()
        return pipeline

    def register_code_pipeline(
        self,
        *,
        project_slug: str,
        pipeline_slug: str,
        pipeline: CorePipeline,
        source_ref: str,
        source_hash_value: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[models.Pipeline, models.PipelineVersion]:
        """Materialize a code pipeline as a read-only versioned document."""

        raw = serialize_pipeline_definition(pipeline)
        blob_key = self._definition_blob_key(project_slug, pipeline_slug, 1)
        self.blob_store.put_bytes(blob_key, raw)
        artifact = self.get_or_create_pipeline(
            project_slug=project_slug,
            pipeline_slug=pipeline_slug,
            name=pipeline.id,
            origin="code",
            read_only=True,
            source_ref=source_ref,
            source_hash_value=source_hash_value,
            metadata=metadata,
        )
        version = models.PipelineVersion.objects.create(
            pipeline=artifact,
            version=1,
            definition_ref=blob_key,
            definition_hash=content_hash(raw),
            definition_format="json",
            notes="Code-defined pipeline materialized as read-only blob",
            metadata=metadata or {},
        )
        artifact.definition_ref = version.definition_ref
        artifact.current_version_number = version.version
        artifact.current_version_hash = version.definition_hash
        artifact.save()
        return artifact, version

    def materialize_pipeline(
        self,
        *,
        project_slug: str,
        pipeline_slug: str,
        pipeline: CorePipeline,
        metadata: dict[str, Any] | None = None,
        notes: str = "",
    ) -> tuple[models.Pipeline, models.PipelineVersion]:
        """Create or update a managed pipeline artifact from a core pipeline."""

        raw = serialize_pipeline_definition(pipeline)
        digest = content_hash(raw)
        managed = self.get_or_create_pipeline(
            project_slug=project_slug,
            pipeline_slug=pipeline_slug,
            name=pipeline.id,
            origin=MANAGED_PIPELINE_ORIGIN,
            read_only=False,
            metadata=metadata,
        )
        next_version = (
            managed.versions.aggregate(Max("version"))["version__max"] or 0
        ) + 1
        blob_key = self._definition_blob_key(project_slug, pipeline_slug, next_version)
        self.blob_store.put_bytes(blob_key, raw)
        version = models.PipelineVersion.objects.create(
            pipeline=managed,
            version=next_version,
            definition_ref=blob_key,
            definition_hash=digest,
            definition_format="json",
            notes=notes,
            metadata=metadata or {},
        )
        managed.definition_ref = version.definition_ref
        managed.current_version_number = version.version
        managed.current_version_hash = digest
        managed.is_read_only = False
        managed.save()
        return managed, version

    def materialize_definition(
        self,
        *,
        project_slug: str,
        pipeline_slug: str,
        definition: bytes,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
        notes: str = "",
    ) -> tuple[models.Pipeline, models.PipelineVersion]:
        """Validate and store a new immutable managed pipeline version."""

        pipeline = deserialize_pipeline_definition(definition)
        managed = self.get_or_create_pipeline(
            project_slug=project_slug,
            pipeline_slug=pipeline_slug,
            name=name or pipeline.id,
            origin=MANAGED_PIPELINE_ORIGIN,
            read_only=False,
            metadata=metadata,
        )
        next_version = (
            managed.versions.aggregate(Max("version"))["version__max"] or 0
        ) + 1
        blob_key = self._definition_blob_key(project_slug, pipeline_slug, next_version)
        self.blob_store.put_bytes(blob_key, definition)
        digest = content_hash(definition)
        version = models.PipelineVersion.objects.create(
            pipeline=managed,
            version=next_version,
            definition_ref=blob_key,
            definition_hash=digest,
            definition_format="json",
            notes=notes,
            metadata=metadata or {},
        )
        managed.definition_ref = blob_key
        managed.current_version_number = next_version
        managed.current_version_hash = digest
        managed.save(
            update_fields=[
                "definition_ref",
                "current_version_number",
                "current_version_hash",
                "updated_at",
            ]
        )
        return managed, version

    def load_pipeline_definition(self, version: models.PipelineVersion) -> CorePipeline:
        """Load a pipeline definition from its blob reference."""

        payload = self.blob_store.get_bytes(version.definition_ref)
        if payload is None:
            raise FileNotFoundError(version.definition_ref)
        return deserialize_pipeline_definition(payload)

    def pipeline_document(self, pipeline: models.Pipeline) -> dict[str, Any]:
        """Return a JSON-serialisable document for dashboards and APIs."""

        version = (
            pipeline.versions.filter(version=pipeline.current_version_number).first()
            or pipeline.versions.order_by("-version").first()
        )
        return {
            "project": pipeline.project.slug,
            "slug": pipeline.slug,
            "name": pipeline.name,
            "origin": pipeline.origin,
            "read_only": pipeline.is_read_only,
            "source_ref": pipeline.source_ref,
            "source_hash": pipeline.source_hash,
            "definition_ref": pipeline.definition_ref,
            "current_version": pipeline.current_version_number,
            "current_version_hash": pipeline.current_version_hash,
            "metadata": pipeline.metadata,
            "version": None if version is None else self.version_document(version),
        }

    def version_document(self, version: models.PipelineVersion) -> dict[str, Any]:
        """Return a JSON-serialisable document for a pipeline version."""

        payload = self.blob_store.get_bytes(version.definition_ref)
        preview = payload.decode("utf-8") if payload is not None else ""
        return {
            "pipeline": version.pipeline.slug,
            "version": version.version,
            "definition_ref": version.definition_ref,
            "definition_hash": version.definition_hash,
            "definition_format": version.definition_format,
            "notes": version.notes,
            "metadata": version.metadata,
            "definition_preview": preview,
        }

    def _definition_blob_key(
        self, project_slug: str, pipeline_slug: str, version: int
    ) -> str:
        return f"pipelines/{project_slug}/{pipeline_slug}/v{version}.json"


__all__ = [
    "CONTROL_PLANE_MANIFEST",
    "MANAGED_PIPELINE_ORIGIN",
    "ControlPlaneRepository",
    "PipelineArtifact",
    "content_hash",
    "default_blob_root",
    "default_blob_store",
    "deserialize_pipeline_definition",
    "serialize_pipeline_definition",
]
