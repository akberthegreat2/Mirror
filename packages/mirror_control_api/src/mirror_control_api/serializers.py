"""DRF serializers for the Mirror control plane."""

from __future__ import annotations

import hashlib

from rest_framework import serializers

from mirror_control_django import models
from mirror_control_django.repository import ControlPlaneRepository


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = "__all__"


class PipelineVersionSerializer(serializers.ModelSerializer):
    definition_text = serializers.CharField(write_only=True, required=False, allow_blank=True)
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
        read_only_fields = ("definition_hash", "definition_ref", "created_at", "updated_at")

    def get_definition_preview(self, obj: models.PipelineVersion) -> str:
        payload = ControlPlaneRepository().blob_store.get_bytes(obj.definition_ref)
        return "" if payload is None else payload.decode("utf-8")

    def create(self, validated_data):
        definition_text = validated_data.pop("definition_text", "")
        if not definition_text:
            raise serializers.ValidationError({"definition_text": "A pipeline version definition is required."})
        repo = ControlPlaneRepository()
        definition_ref = repo._definition_blob_key(
            validated_data["pipeline"].project.slug,
            validated_data["pipeline"].slug,
            validated_data["version"],
        )
        validated_data["definition_ref"] = definition_ref
        instance = super().create(validated_data)
        payload = definition_text.encode("utf-8") if definition_text else b""
        if payload:
            repo.blob_store.put_bytes(instance.definition_ref, payload)
            instance.definition_hash = hashlib.sha256(payload).hexdigest()
            instance.save(update_fields=["definition_ref", "definition_hash"])
        return instance

    def update(self, instance, validated_data):
        definition_text = validated_data.pop("definition_text", None)
        instance = super().update(instance, validated_data)
        if definition_text is not None:
            payload = definition_text.encode("utf-8")
            repo = ControlPlaneRepository()
            if not instance.definition_ref:
                instance.definition_ref = repo._definition_blob_key(
                    instance.pipeline.project.slug,
                    instance.pipeline.slug,
                    instance.version,
                )
            repo.blob_store.put_bytes(instance.definition_ref, payload)
            instance.definition_hash = hashlib.sha256(payload).hexdigest()
            instance.save(update_fields=["definition_hash", "updated_at"])
        return instance


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
