"""Tests for Mirror Control Panel permissions."""

import pytest
from django.contrib.auth.models import Group

from mirror_control_panel.models import CrawlJob, Project
from mirror_control_panel.permissions import (
    setup_groups,
    user_can_cancel_crawl,
    user_can_retry_crawl,
    user_can_view_project,
    user_can_manage_project,
)


@pytest.mark.django_db
class TestPermissions:
    """Tests for permission system."""

    def test_setup_groups_creates_groups(self):
        """Test that setup_groups creates the expected groups."""
        setup_groups()

        assert Group.objects.filter(name="Viewer").exists()
        assert Group.objects.filter(name="Operator").exists()
        assert Group.objects.filter(name="Admin").exists()

    def test_viewer_has_read_permissions(self, viewer_user):
        """Test that Viewer group has read permissions."""
        setup_groups()

        # Check view permissions
        assert viewer_user.has_perm("mirror_control_panel.view_project")
        assert viewer_user.has_perm("mirror_control_panel.view_crawljob")
        assert viewer_user.has_perm("mirror_control_panel.view_crawledurl")
        assert viewer_user.has_perm("mirror_control_panel.view_archiverecord")
        assert viewer_user.has_perm("mirror_control_panel.view_worker")
        assert viewer_user.has_perm("mirror_control_panel.view_schedule")
        assert viewer_user.has_perm("mirror_control_panel.view_audit_logs")

        # Check no write permissions
        assert not viewer_user.has_perm("mirror_control_panel.add_crawljob")
        assert not viewer_user.has_perm("mirror_control_panel.change_crawljob")
        assert not viewer_user.has_perm("mirror_control_panel.retry_crawl")
        assert not viewer_user.has_perm("mirror_control_panel.cancel_crawl")

    def test_operator_has_action_permissions(self, operator_user):
        """Test that Operator group has action permissions."""
        setup_groups()

        # Check action permissions
        assert operator_user.has_perm("mirror_control_panel.add_crawljob")
        assert operator_user.has_perm("mirror_control_panel.change_crawljob")
        assert operator_user.has_perm("mirror_control_panel.retry_crawl")
        assert operator_user.has_perm("mirror_control_panel.cancel_crawl")
        assert operator_user.has_perm("mirror_control_panel.add_schedule")
        assert operator_user.has_perm("mirror_control_panel.change_schedule")

        # Check no admin permissions
        assert not operator_user.has_perm("mirror_control_panel.delete_any_project")
        assert not operator_user.has_perm("mirror_control_panel.force_worker_offline")

    def test_admin_has_all_permissions(self, admin_user):
        """Test that Admin group has all permissions."""
        setup_groups()

        # Check admin permissions
        assert admin_user.has_perm("mirror_control_panel.delete_any_project")
        assert admin_user.has_perm("mirror_control_panel.force_worker_offline")
        assert admin_user.has_perm("mirror_control_panel.view_all_projects")
        assert admin_user.has_perm("mirror_control_panel.view_all_crawls")

    def test_user_can_retry_crawl_own_project(self, user, project):
        """Test user can retry crawl in their own project."""
        setup_groups()

        # Add user to Operator group
        operator_group = Group.objects.get(name="Operator")
        user.groups.add(operator_group)

        crawl = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        crawl.mark_completed(success=False)

        assert user_can_retry_crawl(user, crawl) is True

    def test_user_can_retry_crawl_other_project(self, user, operator_user):
        """Test user cannot retry crawl in someone else's project."""
        setup_groups()

        # Add user to Operator group
        operator_group = Group.objects.get(name="Operator")
        user.groups.add(operator_group)

        # Create project owned by operator_user
        project = Project.objects.create(
            name="Other Project",
            owner=operator_user,
            created_by=operator_user,
        )
        crawl = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=operator_user,
        )
        crawl.mark_completed(success=False)

        # User should not be able to retry
        assert user_can_retry_crawl(user, crawl) is False

    def test_superuser_can_retry_any_crawl(self, admin_user, operator_user):
        """Test superuser can retry any crawl."""
        setup_groups()

        project = Project.objects.create(
            name="Other Project",
            owner=operator_user,
            created_by=operator_user,
        )
        crawl = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=operator_user,
        )
        crawl.mark_completed(success=False)

        assert user_can_retry_crawl(admin_user, crawl) is True

    def test_user_can_cancel_crawl_own_project(self, user, project):
        """Test user can cancel crawl in their own project."""
        setup_groups()

        operator_group = Group.objects.get(name="Operator")
        user.groups.add(operator_group)

        crawl = CrawlJob.objects.create(
            project=project,
            url="https://example.com",
            created_by=user,
        )
        crawl.mark_started()

        assert user_can_cancel_crawl(user, crawl) is True

    def test_user_can_view_project_own(self, user, project):
        """Test user can view their own project."""
        assert user_can_view_project(user, project) is True

    def test_user_can_view_project_other(self, user, operator_user):
        """Test user cannot view someone else's project."""
        project = Project.objects.create(
            name="Other Project",
            owner=operator_user,
            created_by=operator_user,
        )
        assert user_can_view_project(user, project) is False

    def test_user_can_manage_project_own(self, user, project):
        """Test user can manage their own project."""
        assert user_can_manage_project(user, project) is True

    def test_user_can_manage_project_other(self, user, operator_user):
        """Test user cannot manage someone else's project."""
        project = Project.objects.create(
            name="Other Project",
            owner=operator_user,
            created_by=operator_user,
        )
        assert user_can_manage_project(user, project) is False
