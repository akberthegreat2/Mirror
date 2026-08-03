"""Tests for settings."""

import tempfile
from pathlib import Path

from mirror_core.settings import MirrorSettings


def test_defaults():
    s = MirrorSettings()
    assert s.application_name == "mirror"
    assert s.debug is False


def test_environment_override(monkeypatch):
    monkeypatch.setenv("MIRROR_APPLICATION_NAME", "myapp")
    s = MirrorSettings()
    assert s.application_name == "myapp"


def test_secret_redaction():
    s = MirrorSettings(secrets={"api_key": "secret"})
    dumped = s.model_dump()
    assert dumped["secrets"]["api_key"] == "***REDACTED***"


def test_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("application_name: testapp\n")
        f.flush()
        s = MirrorSettings.from_file(Path(f.name))
        assert s.application_name == "testapp"
        Path(f.name).unlink()
