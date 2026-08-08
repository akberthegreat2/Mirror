"""Dashboard views for Mirror control plane."""

from __future__ import annotations

from django.views.generic import TemplateView

from mirror_control_django import models
from mirror_control_django.manifest import control_plane_manifest


class DashboardView(TemplateView):
    """Simple control-plane dashboard summary page."""

    template_name = "mirror_control_django/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            manifest=control_plane_manifest(),
            projects=models.Project.objects.count(),
            pipelines=models.Pipeline.objects.count(),
            runs=models.ExecutionRun.objects.count(),
            workers=models.Worker.objects.count(),
            dead_letters=models.DeadLetter.objects.count(),
        )
        return context
