"""Tests for Mirror Control Panel admin interface."""

import pytest
from django.contrib.admin import site
from django.urls import reverse

from mirror_control_panel.admin import (
    CrawlJobAdmin,
    ProjectAdmin,
)
from mirror_control_panel.models import (
    ArchiveRecord,
    CrawlJob,
    CrawledURL,
    Project,
    Schedule,
    Worker,
)


@pytest.mark.django_db
class TestAdminRegistration:
    """Tests that models are registered with admin."""

    def test_project_registered(self):
        """Test Project is registered with admin."""
        assert site.is_registered(Project)

    def test_crawljob_registered(self):
        """Test CrawlJob is registered with admin."""
        assert site.is_registered(CrawlJob)

    def test_crawledurl_registered(self):
        """Test CrawledURL is registered with admin."""
        assert site.is_registered(CrawledURL)

    def test_archiverecord_registered(self):
        """Test ArchiveRecord is registered with admin."""
        assert site.is_registered(ArchiveRecord)

    def test_worker_registered(self):
        """Test Worker is registered with admin."""
        assert site.is_registered(Worker)

    def test_schedule_registered(self):
        """Test Schedule is registered with admin."""
        assert site.is_registered(Schedule)


@pytest.mark.django_db
class TestProjectAdmin:
    """Tests for ProjectAdmin."""

    def test_list_display(self):
        """Test list display fields."""
        admin = ProjectAdmin(Project, site)
        expected = ["name", "slug", "owner", "is_active", "created_at", "updated_at"]
        assert admin.list_display == expected

    def test_search_fields(self):
        """Test search fields."""
        admin = ProjectAdmin(Project, site)
        expected = ["name", "slug", "description", "owner__username"]
        assert admin.search_fields == expected


@pytest.mark.django_db
class TestCrawlJobAdmin:
    """Tests for CrawlJobAdmin."""

    def test_list_display(self):
        """Test list display fields."""
        admin = CrawlJobAdmin(CrawlJob, site)
        expected = [
            "id",
            "url",
            "project",
            "status_colored",
            "execution_id",
            "created_by",
            "created_at",
            "completed_at",
        ]
        assert admin.list_display == expected

    def test_actions_include_retry_and_cancel(self):
        """Test admin actions include retry and cancel."""
        admin = CrawlJobAdmin(CrawlJob, site)
        actions = [action.__name__ for action in admin.actions]
        assert "retry_crawls" in actions
        assert "cancel_crawls" in actions


@pytest.mark.django_db
class TestAdminViews:
    """Tests for admin views with permissions."""

    def test_project_list_view(self, admin_client, user, project):
        """Test project list view loads."""
        url = reverse("admin:mirror_control_panel_project_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_crawljob_list_view(self, admin_client, user, project, crawl_job):
        """Test crawl job list view loads."""
        url = reverse("admin:mirror_control_panel_crawljob_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_project_list_view_filtered_by_user(self, user_client, user, project):
        """Test user sees only their own projects."""
        # Create another user's project
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_user = User.objects.create_user(username="other", password="test")
        other_project = Project.objects.create(
            name="Other Project",
            owner=other_user,
            created_by=other_user,
        )

        url = reverse("admin:mirror_control_panel_project_changelist")
        response = user_client.get(url)
        assert response.status_code == 200

        # Should see own project
        assert "Test Project" in response.content.decode()

        # Should not see other's project
        assert "Other Project" not in response.content.decode()
