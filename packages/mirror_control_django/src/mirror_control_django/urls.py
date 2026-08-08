"""URL configuration for the Mirror control plane dashboard."""

from __future__ import annotations

from django.urls import path

from mirror_control_django.views import DashboardView

app_name = "mirror_control_django"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
]
