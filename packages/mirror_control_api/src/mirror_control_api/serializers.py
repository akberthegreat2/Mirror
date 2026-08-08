"""DRF serializers for the Mirror control plane."""

from __future__ import annotations

from mirror_control_django import models
from mirror_control_django.repository import ControlPlaneRepository
from rest_framework import serializers


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = "__all__"


class PipelineVersionSerializer(serializers.ModelSerializer):
    definition_text = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    definition_preview = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.PipelineVersion
        fields = (
            "id",
            "pipeline",
            "version",
            "definition_ref",
            "definition_hash",
            "definition_format",
            "notes",
            "metadata",
            "created_at",
            "updated_at",
            "definition_text",
            "definition_preview",
        )
        read_only_fields = (
            "version",
            "definition_hash",
            "definition_ref",
            "definition_format",
            "created_at",
            "updated_at",
        )

    def get_definition_preview(self, obj: models.PipelineVersion) -> str:
        payload = ControlPlaneRepository().blob_store.get_bytes(obj.definition_ref)
        return "" if payload is None else payload.decode("utf-8")

    def create(self, validated_data):
        definition_text = validated_data.pop("definition_text", "")
        if not definition_text:
            raise serializers.ValidationError(
                {"definition_text": "A pipeline version definition is required."}
            )
        pipeline = validated_data["pipeline"]
        if pipeline.is_read_only:
            raise serializers.ValidationError(
                {
                    "pipeline": "Code-defined pipelines are read-only; materialize a managed pipeline first."
                }
            )
        repo = ControlPlaneRepository()
        payload = definition_text.encode("utf-8")
        try:
            from mirror_control_django.repository import deserialize_pipeline_definition

            deserialize_pipeline_definition(payload)
        except Exception as exc:
            raise serializers.ValidationError({"definition_text": str(exc)}) from exc
        _, instance = repo.materialize_definition(
            project_slug=pipeline.project.slug,
            pipeline_slug=pipeline.slug,
            definition=payload,
            metadata=validated_data.get("metadata") or {},
            notes=validated_data.get("notes", ""),
        )
        return instance

    def update(self, instance, validated_data):
        raise serializers.ValidationError(
            "Pipeline versions are immutable; create a new version instead."
        )


class PipelineSerializer(serializers.ModelSerializer):
    versions = PipelineVersionSerializer(many=True, read_only=True)

    class Meta:
        model = models.Pipeline
        fields = "__all__"


class ExecutionRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExecutionRun
        fields = "__all__"


class ExecutionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExecutionStep
        fields = "__all__"


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Worker
        fields = "__all__"


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Schedule
        fields = "__all__"


class CrawledURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CrawledURL
        fields = "__all__"


class ArchiveRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArchiveRecord
        fields = "__all__"


class CheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Checkpoint
        fields = "__all__"


class DeadLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeadLetter
        fields = "__all__"
