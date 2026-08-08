"""Django dashboard smoke tests."""

from __future__ import annotations

from django.test import RequestFactory

from mirror_control_django.views import DashboardView


def test_dashboard_smoke() -> None:
    request = RequestFactory().get("/")
    response = DashboardView.as_view()(request)
    assert response.status_code == 200
    body = response.render().content
    assert b"Mirror Control Plane" in body
