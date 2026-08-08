"""URL routing for the Mirror control-plane REST API."""

from __future__ import annotations

from rest_framework.routers import DefaultRouter

from mirror_control_api.views import (
    ArchiveRecordViewSet,
    CheckpointViewSet,
    CrawledURLViewSet,
    DeadLetterViewSet,
    ExecutionRunViewSet,
    ExecutionStepViewSet,
    ManifestViewSet,
    PipelineVersionViewSet,
    PipelineViewSet,
    ProjectViewSet,
    ScheduleViewSet,
    WorkerViewSet,
)

router = DefaultRouter()
router.register(r"manifest", ManifestViewSet, basename="mirror-control-manifest")
router.register(r"projects", ProjectViewSet)
router.register(r"pipelines", PipelineViewSet)
router.register(r"pipeline-versions", PipelineVersionViewSet)
router.register(r"runs", ExecutionRunViewSet)
router.register(r"steps", ExecutionStepViewSet)
router.register(r"workers", WorkerViewSet)
router.register(r"schedules", ScheduleViewSet)
router.register(r"crawled-urls", CrawledURLViewSet)
router.register(r"archives", ArchiveRecordViewSet)
router.register(r"checkpoints", CheckpointViewSet)
router.register(r"dead-letters", DeadLetterViewSet)

urlpatterns = router.urls
