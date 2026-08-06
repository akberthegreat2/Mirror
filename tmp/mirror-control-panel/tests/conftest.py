"""Pytest configuration for Mirror Control Panel tests."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from mirror_control_panel.models import Project
from mirror_control_panel.permissions import setup_groups

User = get_user_model()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with groups."""
    setup_groups()
    yield


@pytest.fixture
def user():
    """Create a test user."""
    user = User.objects.create_user(
        username="testuser",
        password="testpass123",
        is_staff=True,
    )
    return user


@pytest.fixture
def admin_user():
    """Create a test admin user."""
    user = User.objects.create_superuser(
        username="admin",
        password="adminpass123",
        email="admin@example.com",
    )
    return user


@pytest.fixture
def operator_user():
    """Create a test operator user."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(
        username="operator",
        password="operator123",
        is_staff=True,
    )
    group = Group.objects.get(name="Operator")
    user.groups.add(group)
    user.save()
    return user


@pytest.fixture
def viewer_user():
    """Create a test viewer user."""
    from django.contrib.auth.models import Group

    user = User.objects.create_user(
        username="viewer",
        password="viewer123",
        is_staff=True,
    )
    group = Group.objects.get(name="Viewer")
    user.groups.add(group)
    user.save()
    return user


@pytest.fixture
def project(user):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project",
        owner=user,
        created_by=user,
    )


@pytest.fixture
def admin_client(admin_user):
    """Create an authenticated admin client."""
    client = Client()
    client.force_login(admin_user)
    return client


@pytest.fixture
def user_client(user):
    """Create an authenticated user client."""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def operator_client(operator_user):
    """Create an authenticated operator client."""
    client = Client()
    client.force_login(operator_user)
    return client


@pytest.fixture
def viewer_client(viewer_user):
    """Create an authenticated viewer client."""
    client = Client()
    client.force_login(viewer_user)
    return client
