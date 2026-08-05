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


def test_from_file_toml():
    """TOML loading must work on every Python version Mirror claims to support.

    Regression test for a bare ``import tomllib`` breaking on Python 3.10
    (tomllib is stdlib only from 3.11+) despite every pyproject.toml in the
    workspace declaring ``requires-python = ">=3.10"``.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('application_name = "testapp"\n')
        f.flush()
        s = MirrorSettings.from_file(Path(f.name))
        assert s.application_name == "testapp"
        Path(f.name).unlink()


def test_merge_deep_merges_and_preserves_secrets():
    base = MirrorSettings(
        components={"fetch": {"provider": "httpx", "enabled": True}},
        secrets={"token": "secret"},
    )
    override = MirrorSettings(components={"fetch": {"provider": "firecrawl"}})

    merged = MirrorSettings.merge(base, override)

    assert merged.components["fetch"] == {"provider": "firecrawl", "enabled": True}
    assert merged.secrets["token"].get_secret_value() == "secret"
    assert merged.model_dump()["secrets"]["token"] == "***REDACTED***"