"""Mirror CLI main entry point."""

import asyncio
from pathlib import Path

import typer
from mirror_core.application import Application
from mirror_core.settings import MirrorSettings
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="mirror",
    help="Mirror application framework",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to mirror.yaml configuration file",
    ),
    pipeline: Path | None = typer.Option(
        None,
        "--pipeline",
        "-p",
        help="Path to pipeline definition file (YAML)",
    ),
) -> None:
    """Run a pipeline."""
    console.print("[bold]Running pipeline...[/bold]")
    if config:
        console.print(f"Config: {config}")
    if pipeline:
        console.print(f"Pipeline: {pipeline}")
    console.print("[yellow]Not implemented yet[/yellow]")


@app.command()
def list_capabilities() -> None:
    """List all discovered capabilities."""
    table = Table(title="Discovered Capabilities")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")

    try:
        settings = MirrorSettings()
        app_obj = Application(settings=settings)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(app_obj.start())

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
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def list_providers() -> None:
    """List all discovered providers."""
    table = Table(title="Discovered Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Capability", style="green")
    table.add_column("Priority", style="yellow")

    try:
        settings = MirrorSettings()
        app_obj = Application(settings=settings)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(app_obj.start())

        for prov_key in app_obj.registry.list_providers():
            capability, name = prov_key.split(":", 1)
            try:
                config = app_obj.registry.get_provider(capability, name)
                table.add_row(name, capability, str(config.priority))
            except Exception:
                table.add_row(name, capability, "N/A")

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


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
