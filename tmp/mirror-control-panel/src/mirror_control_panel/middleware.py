"""Django middleware for Mirror Control Panel."""

from django.http import HttpRequest, HttpResponse

from mirror_control_panel.models import AuditLog


class AuditMiddleware:
    """Middleware to log all requests that modify data.

    Logs:
    - POST, PUT, PATCH, DELETE requests
    - Login/logout actions
    - User and IP information
    """

    def __init__(self, get_response: callable) -> None:
        """Initialize middleware.

        Args:
            get_response: Django view callable
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and log modifications.

        Args:
            request: Django HttpRequest

        Returns:
            Django HttpResponse
        """
        # Skip logging for static files, admin CSS/JS, etc.
        if self._should_skip_logging(request):
            return self.get_response(request)

        # Process request
        response = self.get_response(request)

        # Log modifications
        if self._should_log_request(request, response):
            self._log_request(request, response)

        return response

    def _should_skip_logging(self, request: HttpRequest) -> bool:
        """Check if request should skip audit logging.

        Args:
            request: Django HttpRequest

        Returns:
            True if logging should be skipped
        """
        path = request.path
        skip_prefixes = [
            "/static/",
            "/media/",
            "/favicon.ico",
            "/robots.txt",
        ]
        return any(path.startswith(prefix) for prefix in skip_prefixes)

    def _should_log_request(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Check if request should be logged.

        Args:
            request: Django HttpRequest
            response: Django HttpResponse

        Returns:
            True if request should be logged
        """
        # Log all modifying requests
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True

        # Log login/logout
        if request.path == "/admin/login/" and request.method == "POST":
            return True
        if request.path == "/admin/logout/" and request.method in ["POST", "GET"]:
            return True

        return False

    def _log_request(self, request: HttpRequest, response: HttpResponse) -> None:
        """Log the request to audit log.

        Args:
            request: Django HttpRequest
            response: Django HttpResponse
        """
        if not request.user.is_authenticated:
            return

        # Determine action
        action = self._determine_action(request)

        # Determine resource type and ID
        resource_type = self._determine_resource_type(request)
        resource_id = self._determine_resource_id(request)

        # Skip if no resource determined
        if not resource_type:
            return

        AuditLog.objects.create(
            user=request.user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id or "unknown",
            changes={},
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "query_params": dict(request.GET),
            },
        )

    def _determine_action(self, request: HttpRequest) -> str:
        """Determine audit action from request.

        Args:
            request: Django HttpRequest

        Returns:
            Audit action string
        """
        # Check for login/logout
        if request.path == "/admin/login/" and request.method == "POST":
            return AuditLog.Action.LOGIN
        if request.path == "/admin/logout/":
            return AuditLog.Action.LOGOUT

        # Check for retry/cancel actions (custom URLs)
        if "/retry/" in request.path:
            return AuditLog.Action.RETRY
        if "/cancel/" in request.path:
            return AuditLog.Action.CANCEL

        # Map HTTP methods
        method_to_action = {
            "POST": AuditLog.Action.CREATE,
            "PUT": AuditLog.Action.UPDATE,
            "PATCH": AuditLog.Action.UPDATE,
            "DELETE": AuditLog.Action.DELETE,
        }
        return method_to_action.get(request.method, AuditLog.Action.UPDATE)

    def _determine_resource_type(self, request: HttpRequest) -> str:
        """Determine resource type from request.

        Args:
            request: Django HttpRequest

        Returns:
            Resource type string
        """
        path = request.path

        # Admin paths
        if "crawljob" in path:
            return "CrawlJob"
        if "project" in path:
            return "Project"
        if "schedule" in path:
            return "Schedule"
        if "worker" in path:
            return "Worker"
        if "crawledurl" in path:
            return "CrawledURL"
        if "archiverecord" in path:
            return "ArchiveRecord"

        return ""

    def _determine_resource_id(self, request: HttpRequest) -> str:
        """Determine resource ID from request.

        Args:
            request: Django HttpRequest

        Returns:
            Resource ID string
        """
        path = request.path

        # Extract ID from path patterns
        import re

        match = re.search(r"/(\d+)/", path)
        if match:
            return match.group(1)

        return ""

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP from request.

        Args:
            request: Django HttpRequest

        Returns:
            Client IP address
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip or "0.0.0.0"
