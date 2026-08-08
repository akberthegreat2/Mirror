"""REST views for the Mirror control plane."""

from __future__ import annotations

from dataclasses import asdict

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from mirror_control_api.serializers import (
    ArchiveRecordSerializer,
    CheckpointSerializer,
    CrawledURLSerializer,
    DeadLetterSerializer,
    ExecutionRunSerializer,
    ExecutionStepSerializer,
    PipelineSerializer,
    PipelineVersionSerializer,
    ProjectSerializer,
    ScheduleSerializer,
    WorkerSerializer,
)
from mirror_control_django import models
from mirror_control_django.manifest import control_plane_manifest


class ManifestViewSet(viewsets.ViewSet):
    """Expose the shared interface manifest through REST."""

    def list(self, request):
        manifest = control_plane_manifest()
        return Response(
            {
                "name": manifest.name,
                "version": manifest.version,
                "entities": [asdict(entity) for entity in manifest.entities],
            }
        )


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = ProjectSerializer


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = models.Pipeline.objects.select_related("project").prefetch_related("versions")
    serializer_class = PipelineSerializer

    @action(detail=True, methods=["post"])
    def materialize(self, request, pk=None):
        pipeline = self.get_object()
        serializer = PipelineSerializer(pipeline, context=self.get_serializer_context())
        return Response(serializer.data)


class PipelineVersionViewSet(viewsets.ModelViewSet):
    queryset = models.PipelineVersion.objects.select_related("pipeline", "pipeline__project")
    serializer_class = PipelineVersionSerializer


class ExecutionRunViewSet(viewsets.ModelViewSet):
    queryset = models.ExecutionRun.objects.select_related("pipeline", "pipeline__project")
    serializer_class = ExecutionRunSerializer


class ExecutionStepViewSet(viewsets.ModelViewSet):
    queryset = models.ExecutionStep.objects.select_related("run", "run__pipeline")
    serializer_class = ExecutionStepSerializer


class WorkerViewSet(viewsets.ModelViewSet):
    queryset = models.Worker.objects.all()
    serializer_class = WorkerSerializer


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = models.Schedule.objects.select_related("pipeline", "pipeline__project")
    serializer_class = ScheduleSerializer


class CrawledURLViewSet(viewsets.ModelViewSet):
    queryset = models.CrawledURL.objects.select_related("project", "pipeline")
    serializer_class = CrawledURLSerializer


class ArchiveRecordViewSet(viewsets.ModelViewSet):
    queryset = models.ArchiveRecord.objects.select_related("pipeline")
    serializer_class = ArchiveRecordSerializer


class CheckpointViewSet(viewsets.ModelViewSet):
    queryset = models.Checkpoint.objects.all()
    serializer_class = CheckpointSerializer


class DeadLetterViewSet(viewsets.ModelViewSet):
    queryset = models.DeadLetter.objects.select_related("pipeline")
    serializer_class = DeadLetterSerializer
