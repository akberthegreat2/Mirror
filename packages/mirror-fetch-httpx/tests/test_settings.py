"""Tests for HTTPX settings."""

from mirror_fetch_httpx.settings import HTTPXSettings


def test_defaults():
    settings = HTTPXSettings()
    assert settings.default_timeout == 30.0
    assert settings.user_agent == "Mirror/0.1"
    assert settings.follow_redirects is True
    assert settings.max_redirects == 20
    assert settings.max_response_size is None


def test_override():
    settings = HTTPXSettings(
        default_timeout=60.0,
        user_agent="Custom/1.0",
        follow_redirects=False,
        max_redirects=10,
        max_response_size=1024 * 1024,
    )
    assert settings.default_timeout == 60.0
    assert settings.user_agent == "Custom/1.0"
    assert settings.follow_redirects is False
    assert settings.max_redirects == 10
    assert settings.max_response_size == 1024 * 1024
