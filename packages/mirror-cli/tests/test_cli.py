"""Tests for CLI commands."""

from mirror_cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_list_capabilities():
    result = runner.invoke(app, ["list-capabilities"])
    assert result.exit_code == 0


def test_list_providers():
    result = runner.invoke(app, ["list-providers"])
    assert result.exit_code == 0


def test_status():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0


def test_run_no_args():
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "Running pipeline" in result.output
