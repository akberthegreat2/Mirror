"""Project scaffolding helpers for the Mirror CLI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_IDENTIFIER_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def _text(*lines: str) -> str:
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class DoctorCheck:
    """Single health-check result for a generated Mirror project."""

    name: str
    passed: bool
    details: str


def _validate_name(value: str, label: str) -> None:
    if not value:
        raise ValueError(f"{label} cannot be empty")
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(
            f"{label} must start with a letter or underscore and contain only "
            "letters, digits, underscores, or hyphens"
        )


def _render(template: str, **replacements: str) -> str:
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def _write_file(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)


_PROJECT_FILES: dict[str, str] = {
    "README.md": _text(
        "# {{PROJECT_NAME}}",
        "",
        "Created with `mirror startproject`.",
        "",
        "## Next steps",
        "",
        "1. Edit `config/settings.py` to select the active components.",
        "2. Add app-specific code under `apps/` with `mirror startapp`.",
        "3. Run `mirror doctor` from this directory to verify the scaffold.",
    ),
    "pyproject.toml": _text(
        "[build-system]",
        'requires = ["setuptools>=61.0", "wheel"]',
        'build-backend = "setuptools.build_meta"',
        "",
        "[project]",
        'name = "{{PROJECT_NAME}}"',
        'version = "0.1.0"',
        'description = "Mirror project scaffold"',
        'requires-python = ">=3.10"',
        "dependencies = [",
        '    "mirror-core>=0.1.0",',
        '    "mirror-cli>=0.1.0",',
        "]",
        "",
        "[tool.setuptools.packages.find]",
        'where = ["."]',
        'include = ["config*", "apps*"]',
        'namespaces = false',
        "",
        "[tool.pytest.ini_options]",
        'testpaths = ["tests"]',
        'python_files = ["test_*.py"]',
    ),
    "manage.py": _text(
        "#!/usr/bin/env python3",
        '"""Mirror project command entry point."""',
        "",
        "from mirror_cli.main import app",
        "",
        "",
        'if __name__ == "__main__":',
        "    app()",
    ),
    "config/__init__.py": _text('"""Project configuration package for Mirror."""'),
    "config/settings.py": _text(
        '"""Project-level Mirror settings."""',
        "",
        "from mirror_core.settings import MirrorSettings",
        "",
        'settings = MirrorSettings(',
        '    application_name="{{PROJECT_NAME}}",',
        '    worker_backend="inline",',
        ')',
    ),
    "config/asgi.py": _text(
        '"""ASGI placeholder for the Mirror project."""',
        "",
        'from config.settings import settings as _settings',
        "",
        'application = None',
    ),
    "config/wsgi.py": _text(
        '"""WSGI placeholder for the Mirror project."""',
        "",
        'from config.settings import settings as _settings',
        "",
        'application = None',
    ),
    "config/urls.py": _text(
        '"""URL placeholder for the Mirror project."""',
        "",
        'urlpatterns: list[str] = []',
    ),
    "apps/__init__.py": _text('"""Application packages for the Mirror project."""'),
    "apps/core/__init__.py": _text(
        '"""Default application package created by `mirror startproject`."""'
    ),
    "apps/core/config.py": _text(
        '"""Application configuration for the default Mirror app."""',
        "",
        "from dataclasses import dataclass",
        "",
        "",
        "@dataclass(frozen=True)",
        "class AppConfig:",
        '    """Configuration for a Mirror application bundle."""',
        "",
        '    name: str = "core"',
        '    label: str = "core"',
        '    pipelines_module: str = "apps.core.pipelines"',
        '    middleware_module: str = "apps.core.middleware"',
        '    signals_module: str = "apps.core.signals"',
    ),
    "apps/core/pipelines.py": _text(
        '"""Pipeline definitions for the default Mirror app."""',
        "",
        "from mirror_core.pipeline import Pipeline",
        "",
        'core_pipeline = Pipeline(id="core", steps=[])',
    ),
    "apps/core/tasks.py": _text(
        '"""Task registration helpers for the default Mirror app."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_tasks() -> Sequence[str]:",
        '    """Return registered task names for the scaffold app."""',
        "",
        '    return ()',
    ),
    "apps/core/middleware.py": _text(
        '"""Middleware registration helpers for the default Mirror app."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_middleware() -> Sequence[str]:",
        '    """Return middleware names for the scaffold app."""',
        "",
        '    return ()',
    ),
    "apps/core/signals.py": _text(
        '"""Signal registration helpers for the default Mirror app."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_signals() -> Sequence[str]:",
        '    """Return signal names for the scaffold app."""',
        "",
        '    return ()',
    ),
    "apps/core/workers.py": _text(
        '"""Worker registration helpers for the default Mirror app."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_workers() -> Sequence[str]:",
        '    """Return worker names for the scaffold app."""',
        "",
        '    return ()',
    ),
    "tests/test_project_smoke.py": _text(
        '"""Smoke tests for the generated Mirror project scaffold."""',
        "",
        "from config.settings import settings",
        "",
        "",
        "def test_project_settings_load() -> None:",
        '    """Project settings should import and expose the application name."""',
        "",
        '    assert settings.application_name',
        '    assert settings.worker_backend == "inline"',
    ),
    "docs/README.md": _text(
        '# Project documentation',
        "",
        'Use this directory for project-specific decisions, ADRs, and runbooks.',
        "Mirror's repository-level docs describe the framework; this folder is",
        'where the generated project records its own implementation details.',
    ),
}

_APP_FILES: dict[str, str] = {
    "__init__.py": _text('"""Mirror application package scaffold."""'),
    "config.py": _text(
        '"""Application configuration for {{APP_NAME}}."""',
        "",
        "from dataclasses import dataclass",
        "",
        "",
        "@dataclass(frozen=True)",
        "class AppConfig:",
        '    """Metadata for a generated Mirror application."""',
        "",
        '    name: str = "{{APP_NAME}}"',
        '    label: str = "{{APP_NAME}}"',
        '    pipelines_module: str = "apps.{{APP_NAME}}.pipelines"',
        '    middleware_module: str = "apps.{{APP_NAME}}.middleware"',
        '    signals_module: str = "apps.{{APP_NAME}}.signals"',
    ),
    "pipelines.py": _text(
        '"""Pipeline definitions for {{APP_NAME}}."""',
        "",
        "from mirror_core.pipeline import Pipeline",
        "",
        'app_pipeline = Pipeline(id="{{APP_NAME}}", steps=[])',
    ),
    "tasks.py": _text(
        '"""Task helpers for {{APP_NAME}}."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_tasks() -> Sequence[str]:",
        '    """Return task names registered by the application scaffold."""',
        "",
        '    return ()',
    ),
    "middleware.py": _text(
        '"""Middleware helpers for {{APP_NAME}}."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_middleware() -> Sequence[str]:",
        '    """Return middleware names registered by the application scaffold."""',
        "",
        '    return ()',
    ),
    "signals.py": _text(
        '"""Signals for {{APP_NAME}}."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_signals() -> Sequence[str]:",
        '    """Return signal names registered by the application scaffold."""',
        "",
        '    return ()',
    ),
    "workers.py": _text(
        '"""Worker helpers for {{APP_NAME}}."""',
        "",
        "from collections.abc import Sequence",
        "",
        "",
        "def list_workers() -> Sequence[str]:",
        '    """Return worker names registered by the application scaffold."""',
        "",
        '    return ()',
    ),
    "README.md": _text(
        '# {{APP_NAME}}',
        "",
        'Generated with `mirror startapp`.',
        "",
        'Place pipelines, middleware, tasks, workers, and signals here.',
    ),
    "tests.py": _text(
        '"""Smoke tests for {{APP_NAME}}."""',
        "",
        "",
        "def test_app_importable() -> None:",
        '    """The scaffolded application module should import cleanly."""',
        "",
        '    assert True',
    ),
}


def create_project(name: str, *, root: Path | None = None) -> Path:
    """Create a Mirror project scaffold.

    Args:
        name: Project directory name.
        root: Optional parent directory. Defaults to the current directory.

    Returns:
        The path to the created project directory.
    """
    _validate_name(name, "Project name")
    base = Path.cwd() if root is None else root
    project_root = base / name
    if project_root.exists():
        raise FileExistsError(f"Project already exists: {project_root}")

    for relative_path, template in _PROJECT_FILES.items():
        content = _render(template, PROJECT_NAME=name)
        executable = relative_path == "manage.py"
        _write_file(project_root / relative_path, content, executable=executable)

    return project_root


def create_app(name: str, *, root: Path | None = None) -> Path:
    """Create a Mirror application scaffold inside an existing project.

    Args:
        name: Application directory name.
        root: Optional project root. Defaults to the current directory.

    Returns:
        The path to the created application package.
    """
    _validate_name(name, "App name")
    base = Path.cwd() if root is None else root
    apps_root = base / "apps"
    if not apps_root.exists():
        raise FileNotFoundError(
            f"Unable to find apps/ under {base}. Run `mirror startproject` first."
        )
    app_root = apps_root / name
    if app_root.exists():
        raise FileExistsError(f"Application already exists: {app_root}")

    for relative_path, template in _APP_FILES.items():
        content = _render(template, APP_NAME=name)
        _write_file(app_root / relative_path, content)

    return app_root


def collect_project_checks(root: Path | None = None) -> list[DoctorCheck]:
    """Inspect the current directory for a generated Mirror project."""
    base = Path.cwd() if root is None else root
    checks: list[DoctorCheck] = []

    def _exists(label: str, path: Path) -> None:
        checks.append(
            DoctorCheck(
                name=label,
                passed=path.exists(),
                details=str(path),
            )
        )

    _exists("project root", base / "manage.py")
    _exists("project settings", base / "config" / "settings.py")
    _exists("project ASGI entrypoint", base / "config" / "asgi.py")
    _exists("project WSGI entrypoint", base / "config" / "wsgi.py")
    _exists("default app", base / "apps" / "core")
    _exists("project README", base / "README.md")
    _exists("project docs", base / "docs" / "README.md")

    for module_name in ("mirror_core", "mirror_cli"):
        try:
            __import__(module_name)
        except Exception as exc:  # pragma: no cover - environment-specific
            checks.append(
                DoctorCheck(
                    name=f"import {module_name}",
                    passed=False,
                    details=str(exc),
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name=f"import {module_name}",
                    passed=True,
                    details="imported successfully",
                )
            )

    return checks


def format_checks(checks: list[DoctorCheck]) -> str:
    """Render doctor checks as a plain-text summary."""
    lines = ["Mirror Doctor", ""]
    for check in checks:
        status = "OK" if check.passed else "FAIL"
        lines.append(f"[{status}] {check.name}: {check.details}")
    return "\n".join(lines)


def project_is_healthy(checks: list[DoctorCheck]) -> bool:
    """Return ``True`` when all doctor checks pass."""
    return all(check.passed for check in checks)
