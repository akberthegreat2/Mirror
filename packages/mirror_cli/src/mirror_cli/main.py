
"""Mirror CLI main entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mirror_core.application import Application
from mirror_core.settings import MirrorSettings
from mirror_core.workers import InlineWorker
from mirror_cli.scaffold import (
    collect_project_checks,
    create_app,
    create_project,
    format_checks,
    project_is_healthy,
)

app = typer.Typer(
    name="mirror",
    help="Mirror application framework",
    add_completion=False,
)
console = Console()


async def _list_capabilities_async() -> None:
    """List discovered capabilities without leaking application resources."""
    table = Table(title="Discovered Capabilities")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")

    async with Application(settings=MirrorSettings()) as app_obj:
        for cap in app_obj.registry.list_capabilities():
            name, version = cap.split(":", 1)
            description = "N/A"
            try:
                config = app_obj.registry.get_capability(name, version)
                description = config.metadata.get("description", "N/A")
            except Exception:
                pass
            table.add_row(name, version, description)

    console.print(table)


async def _list_providers_async() -> None:
    """List discovered providers without leaking application resources."""
    table = Table(title="Discovered Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Capability", style="green")
    table.add_column("Priority", style="yellow")

    async with Application(settings=MirrorSettings()) as app_obj:
        for prov_key in app_obj.registry.list_providers():
            capability, name = prov_key.split(":", 1)
            try:
                config = app_obj.registry.get_provider(capability, name)
                table.add_row(name, capability, str(config.priority))
            except Exception:
                table.add_row(name, capability, "N/A")

    console.print(table)


@app.command()
def startproject(
    name: str = typer.Argument(..., help="Project directory name"),
    root: Path | None = typer.Option(
        None,
        "--root",
        "-r",
        help="Parent directory for the generated project",
    ),
) -> None:
    """Create a Django-style Mirror project scaffold."""
    try:
        created = create_project(name, root=root)
    except Exception as exc:
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Created Mirror project scaffold[/green] {created}")
    console.print("Next: cd into the project and run `mirror doctor`.")


@app.command()
def startapp(
    name: str = typer.Argument(..., help="Application package name"),
    root: Path | None = typer.Option(
        None,
        "--root",
        "-r",
        help="Project root that contains apps/",
    ),
) -> None:
    """Create a reusable Mirror application scaffold inside apps/."""
    try:
        created = create_app(name, root=root)
    except Exception as exc:
        raise typer.Exit(code=1) from exc
    console.print(f"[green]Created Mirror app scaffold[/green] {created}")


@app.command()
def doctor(
    root: Path | None = typer.Option(
        None,
        "--root",
        "-r",
        help="Project root to inspect",
    ),
) -> None:
    """Inspect a generated project scaffold and report health checks."""
    checks = collect_project_checks(root=root)
    console.print(format_checks(checks))
    if not project_is_healthy(checks):
        raise typer.Exit(code=1)


@app.command()
def run(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to Mirror settings file",
    ),
    pipeline: Path | None = typer.Option(
        None,
        "--pipeline",
        "-p",
        help="Path to pipeline definition file",
    ),
) -> None:
    """Run a pipeline or start the runtime in place."""
    async def _run() -> None:
        settings = MirrorSettings.from_file(config) if config is not None else MirrorSettings()
        app_obj = Application(settings=settings)
        await app_obj.start()
        try:
            console.print("[bold]Running pipeline...[/bold]")
            if config is not None:
                console.print(f"Config: {config}")
            if pipeline is None:
                console.print("[yellow]No pipeline file supplied; runtime started successfully.[/yellow]")
                return
            pipeline_obj = _load_pipeline(pipeline)
            result = await app_obj.run_pipeline_detailed(pipeline_obj)
            console.print(f"[green]Pipeline finished[/green] {result.outcome.value}")
        finally:
            await app_obj.shutdown()

    try:
        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc



def _load_pipeline(path: Path):
    """Load a pipeline definition from JSON, TOML, or YAML."""
    from mirror_core.pipeline import Pipeline

    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("YAML pipeline files require the 'yaml' extra") from exc
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    elif path.suffix == ".toml":
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8"))
    elif path.suffix == ".json":
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise RuntimeError(f"Unsupported pipeline format: {path.suffix}")
    return Pipeline.model_validate(data)


@app.command()
def worker() -> None:
    """Start the default local worker backend for alpha development."""

    async def _run() -> None:
        backend = InlineWorker()
        await backend.start()
        await backend.stop()
        console.print("[bold]Worker backend ready[/bold] (inline)")

    try:
        asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(code=1) from exc

@app.command()
def list_capabilities() -> None:
    """List all discovered capabilities."""
    try:
        asyncio.run(_list_capabilities_async())
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


@app.command()
def list_providers() -> None:
    """List all discovered providers."""
    try:
        asyncio.run(_list_providers_async())
    except Exception as exc:
        console.print(f"[red]Error: {exc}[/red]")


@app.command()
def status() -> None:
    """Show application status."""
    console.print("[bold]Mirror Status[/bold]")
    console.print("Application: Not running")


@app.callback()
def callback() -> None:
    """Mirror CLI – application framework for web infrastructure."""
    pass


if __name__ == "__main__":
    app()
